"""
TEST-023: Clear Navigation Button
Tests the CLEAR button functionality for navigation input fields using Playwright MCP.

Requirements:
- Test actual CLEAR button click interaction
- Verify CLEAR button exists and is clickable
- Test that CLEAR button resets all navigation input fields
- Verify latitude field clears to empty
- Verify longitude field clears to empty  
- Verify altitude field resets to default (10m)
- Test that CLEAR button removes validation error messages
- Ensure no navigation commands are sent when clearing
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestClearNavButton:
    """Test CLEAR navigation button functionality with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5023)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5023,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5023"
        for _ in range(10):  # Try for 10 seconds
            try:
                response = requests.get(base_url, timeout=1)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        
        yield base_url

    @pytest.mark.asyncio
    async def test_clear_button_basic_functionality(self, webgcs_server):
        """Test CLEAR button basic clearing functionality."""
        record_agent_usage('navigation-testing-agent', 100, 90)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS interface
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for navigation controls to load
                await page.wait_for_selector('#nav-lat', timeout=10000)
                await page.wait_for_selector('#nav-lon', timeout=10000)
                await page.wait_for_selector('#nav-alt', timeout=10000)
                await page.wait_for_selector('#clear-btn', timeout=10000)
                
                # Get input elements and clear button
                lat_input = page.locator('#nav-lat')
                lon_input = page.locator('#nav-lon')
                alt_input = page.locator('#nav-alt')
                clear_btn = page.locator('#clear-btn')
                
                # Verify elements are visible
                assert await lat_input.is_visible(), "Latitude input field should be visible"
                assert await lon_input.is_visible(), "Longitude input field should be visible" 
                assert await alt_input.is_visible(), "Altitude input field should be visible"
                assert await clear_btn.is_visible(), "CLEAR button should be visible"
                
                # Fill in some test coordinates
                await lat_input.fill('37.774900')
                await lon_input.fill('-122.419400')
                await alt_input.fill('75.5')
                
                # Verify values were set
                assert await lat_input.input_value() == '37.774900', "Latitude should be filled"
                assert await lon_input.input_value() == '-122.419400', "Longitude should be filled"
                assert await alt_input.input_value() == '75.5', "Altitude should be filled"
                
                # Click CLEAR button
                await clear_btn.click()
                await page.wait_for_timeout(500)  # Wait for clearing to complete
                
                # Verify fields are cleared
                lat_value = await lat_input.input_value()
                lon_value = await lon_input.input_value()
                alt_value = await alt_input.input_value()
                
                assert lat_value == '', f"Latitude should be empty after clear, got '{lat_value}'"
                assert lon_value == '', f"Longitude should be empty after clear, got '{lon_value}'"
                assert alt_value == '10', f"Altitude should reset to default '10' after clear, got '{alt_value}'"
                
                print("✅ CLEAR button basic functionality working correctly")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_clear_button_removes_validation_errors(self, webgcs_server):
        """Test CLEAR button removes validation error messages."""
        record_agent_usage('navigation-testing-agent', 90, 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#nav-lat', timeout=10000)
                
                # Fill invalid coordinates to trigger validation error
                await page.locator('#nav-lat').fill('95.0')  # Invalid latitude
                await page.locator('#nav-lon').fill('-122.4')
                await page.locator('#nav-alt').fill('50')
                
                # Try to GO TO with invalid coordinates (should trigger error)
                await page.locator('#goto-btn').click()
                await page.wait_for_timeout(500)
                
                # Verify error message appears
                error_message = page.locator('.nav-error')
                assert await error_message.is_visible(), "Validation error should be visible"
                
                error_text = await error_message.text_content()
                assert 'Latitude must be between -90 and 90' in error_text, f"Expected latitude validation error, got: {error_text}"
                
                # Click CLEAR button
                await page.locator('#clear-btn').click()
                await page.wait_for_timeout(500)
                
                # Verify error message is removed
                assert not await error_message.is_visible(), "Validation error should be removed after clear"
                
                # Verify fields are cleared
                assert await page.locator('#nav-lat').input_value() == '', "Latitude should be empty"
                assert await page.locator('#nav-lon').input_value() == '', "Longitude should be empty"
                assert await page.locator('#nav-alt').input_value() == '10', "Altitude should reset to default"
                
                print("✅ CLEAR button removes validation errors correctly")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_clear_button_no_command_sent(self, webgcs_server):
        """Test CLEAR button does not send any navigation commands."""
        record_agent_usage('navigation-testing-agent', 80, 75)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#nav-lat', timeout=10000)
                
                # Set up SocketIO command capture
                await page.add_init_script("""
                    window.capturedCommands = [];
                    const originalEmit = io.Socket.prototype.emit;
                    io.Socket.prototype.emit = function(event, data) {
                        if (event === 'send_command') {
                            window.capturedCommands.push(data);
                        }
                        return originalEmit.call(this, event, data);
                    };
                """)
                
                # Fill some coordinates
                await page.locator('#nav-lat').fill('37.7749')
                await page.locator('#nav-lon').fill('-122.4194')
                await page.locator('#nav-alt').fill('100')
                
                # Clear commands array before testing
                await page.evaluate('window.capturedCommands = []')
                
                # Click CLEAR button
                await page.locator('#clear-btn').click()
                await page.wait_for_timeout(1000)
                
                # Verify no commands were sent
                captured_commands = await page.evaluate('window.capturedCommands')
                assert len(captured_commands) == 0, f"CLEAR button should not send commands, but {len(captured_commands)} were captured"
                
                # Verify fields are cleared
                assert await page.locator('#nav-lat').input_value() == '', "Latitude should be empty"
                assert await page.locator('#nav-lon').input_value() == '', "Longitude should be empty" 
                assert await page.locator('#nav-alt').input_value() == '10', "Altitude should reset to default"
                
                print("✅ CLEAR button does not send navigation commands")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_clear_button_multiple_clears(self, webgcs_server):
        """Test CLEAR button works correctly with multiple clear operations."""
        record_agent_usage('navigation-testing-agent', 70, 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#nav-lat', timeout=10000)
                
                clear_btn = page.locator('#clear-btn')
                
                # Test multiple clear operations in sequence
                for i in range(3):
                    # Fill different coordinates each time
                    test_coords = [
                        ('45.0', '90.0', '25'),
                        ('-30.5', '-60.25', '150'),
                        ('0.0', '0.0', '75')
                    ]
                    
                    lat, lon, alt = test_coords[i]
                    
                    await page.locator('#nav-lat').fill(lat)
                    await page.locator('#nav-lon').fill(lon)
                    await page.locator('#nav-alt').fill(alt)
                    
                    # Verify values were set (accounting for precision formatting)
                    lat_value = await page.locator('#nav-lat').input_value()
                    lon_value = await page.locator('#nav-lon').input_value()
                    alt_value = await page.locator('#nav-alt').input_value()
                    
                    # Check that values match expected precision (lat/lon get 6 decimals, alt gets 1)
                    assert float(lat_value) == float(lat), f"Expected lat {lat}, got {lat_value}"
                    assert float(lon_value) == float(lon), f"Expected lon {lon}, got {lon_value}"  
                    assert float(alt_value) == float(alt), f"Expected alt {alt}, got {alt_value}"
                    
                    # Clear the values
                    await clear_btn.click()
                    await page.wait_for_timeout(300)
                    
                    # Verify cleared state
                    assert await page.locator('#nav-lat').input_value() == '', f"Latitude should be empty on clear {i+1}"
                    assert await page.locator('#nav-lon').input_value() == '', f"Longitude should be empty on clear {i+1}"
                    assert await page.locator('#nav-alt').input_value() == '10', f"Altitude should be '10' on clear {i+1}"
                
                print("✅ Multiple CLEAR operations work correctly")
                
            finally:
                await browser.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
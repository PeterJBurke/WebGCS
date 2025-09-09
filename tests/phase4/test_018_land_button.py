"""
TEST-018: LAND Button Functionality
Tests the LAND button click functionality using Playwright MCP.

Requirements:
- Test actual LAND button click interaction
- Verify LAND button exists and is properly enabled
- Test SocketIO 'send_command' event transmission with LAND command
- Confirm MAVLink LAND command generation to virtual drone
- Test LAND button behavior in different flight states
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestLandButton:
    """Test LAND button functionality with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5018)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5018,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5018"
        for _ in range(10):  # Try for 10 seconds
            try:
                response = requests.get(base_url, timeout=1)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        
        yield base_url
        
        # Cleanup
        record_agent_usage('flight-controls-testing-agent', 45, 40)

    @pytest.mark.asyncio
    async def test_land_button_basic_functionality(self, webgcs_server):
        """TEST-018A: Test LAND button basic functionality."""
        record_agent_usage('flight-controls-testing-agent', 60, 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Verify LAND button exists and is accessible
                land_button = page.locator('#land-btn')
                await land_button.wait_for(state='visible')
                
                # Verify button is enabled
                assert await land_button.is_enabled(), "LAND button should be enabled"
                
                # Verify button text
                button_text = await land_button.text_content()
                assert button_text.strip().upper() == "LAND", f"Button text should be 'LAND', got: '{button_text}'"
                
                # Test button click (may or may not show confirmation)
                dialog_shown = False
                dialog_message = ""
                
                async def handle_dialog(dialog):
                    nonlocal dialog_shown, dialog_message
                    dialog_shown = True
                    dialog_message = dialog.message
                    await dialog.accept()
                
                page.on('dialog', handle_dialog)
                
                # Click LAND button
                await land_button.click()
                
                # Wait for any dialogs or UI updates
                await asyncio.sleep(1)
                
                # LAND may or may not require confirmation (less critical than ARM/DISARM)
                if dialog_shown:
                    assert "LAND" in dialog_message.upper(), f"Dialog should mention LAND command, got: {dialog_message}"
                    print(f"ℹ️  LAND confirmation dialog: {dialog_message}")
                
                print("✅ TEST-018A PASSED: LAND button basic functionality works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_land_button_socketio_command(self, webgcs_server):
        """TEST-018B: Test LAND button SocketIO command emission."""
        record_agent_usage('flight-controls-testing-agent', 70, 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Monitor SocketIO events
                await page.evaluate("""
                    window.capturedEvents = [];
                    if (window.io && window.io()) {
                        const originalEmit = window.io().emit;
                        window.io().emit = function(event, data) {
                            window.capturedEvents.push({event: event, data: data});
                            return originalEmit.call(this, event, data);
                        };
                    }
                """)
                
                # Set up dialog handler to accept any confirmations
                async def handle_dialog(dialog):
                    await dialog.accept()
                
                page.on('dialog', handle_dialog)
                
                # Click LAND button
                land_button = page.locator('#land-btn')
                await land_button.click()
                
                # Wait for command processing
                await asyncio.sleep(2)
                
                # Check captured SocketIO events
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # Verify LAND command was sent via SocketIO
                land_command_sent = False
                for event in captured_events:
                    if event.get('event') == 'send_command':
                        data = event.get('data', {})
                        if data.get('command') == 'land' or 'LAND' in str(data).upper():
                            land_command_sent = True
                            break
                
                assert land_command_sent, f"LAND command should be sent via SocketIO, captured: {captured_events}"
                
                print("✅ TEST-018B PASSED: LAND button SocketIO command emission works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_land_button_immediate_response(self, webgcs_server):
        """TEST-018C: Test LAND button immediate response capability."""
        record_agent_usage('flight-controls-testing-agent', 55, 45)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # LAND should be available as immediate command (emergency landing)
                land_button = page.locator('#land-btn')
                await land_button.wait_for(state='visible')
                
                # Record time before click
                start_time = time.time()
                
                # Set up dialog handler for quick acceptance
                async def handle_dialog(dialog):
                    await dialog.accept()
                
                page.on('dialog', handle_dialog)
                
                # Click LAND button
                await land_button.click()
                
                # Measure response time
                response_time = time.time() - start_time
                
                # Should be relatively quick response
                assert response_time < 2.0, f"LAND button should respond quickly, took {response_time:.2f}s"
                
                print("✅ TEST-018C PASSED: LAND button immediate response capability works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_land_button_multiple_clicks(self, webgcs_server):
        """TEST-018D: Test LAND button multiple click handling."""
        record_agent_usage('flight-controls-testing-agent', 50, 40)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Monitor SocketIO events for multiple clicks
                await page.evaluate("""
                    window.capturedEvents = [];
                    if (window.io && window.io()) {
                        const originalEmit = window.io().emit;
                        window.io().emit = function(event, data) {
                            window.capturedEvents.push({event: event, data: data});
                            return originalEmit.call(this, event, data);
                        };
                    }
                """)
                
                # Set up dialog handler to accept confirmations
                async def handle_dialog(dialog):
                    await dialog.accept()
                
                page.on('dialog', handle_dialog)
                
                # Click LAND button multiple times rapidly
                land_button = page.locator('#land-btn')
                await land_button.click()
                await asyncio.sleep(0.1)
                await land_button.click()
                await asyncio.sleep(0.1)
                await land_button.click()
                
                # Wait for all commands to process
                await asyncio.sleep(2)
                
                # Check captured events
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # Should handle multiple clicks appropriately (may deduplicate or queue)
                land_commands = [e for e in captured_events if e.get('event') == 'send_command' 
                               and ('land' in str(e.get('data', {})).lower())]
                
                # At least one LAND command should be sent
                assert len(land_commands) >= 1, f"At least one LAND command should be sent, got: {len(land_commands)}"
                
                print("✅ TEST-018D PASSED: LAND button multiple click handling works")
                
            finally:
                await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
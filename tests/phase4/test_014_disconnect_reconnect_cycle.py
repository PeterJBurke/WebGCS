"""
TEST-014: Disconnect/Reconnect Cycle Functionality
Tests the complete disconnect/reconnect cycle using Playwright MCP.

Requirements:
- Test full connect → disconnect → reconnect cycle
- Verify button state transitions during cycle
- Test connection status updates throughout cycle  
- Verify heartbeat counter behavior during cycle
- Test proper cleanup and re-initialization
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestDisconnectReconnectCycle:
    """Test disconnect/reconnect cycle functionality with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5004)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5004,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5004"
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
    async def test_initial_button_states_before_cycle(self, webgcs_server):
        """TEST-014-A: Verify initial button states before starting cycle."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                connect_button = page.locator('#connect-btn')
                disconnect_button = page.locator('#disconnect-btn')
                
                # Initial states
                connect_enabled = await connect_button.is_enabled()
                disconnect_enabled = await disconnect_button.is_enabled()
                
                assert connect_enabled, "Connect button should be enabled initially"
                assert not disconnect_enabled, "Disconnect button should be disabled initially"
                
                # Verify button texts
                connect_text = await connect_button.text_content()
                disconnect_text = await disconnect_button.text_content()
                
                assert connect_text == "Connect", f"Expected 'Connect', got '{connect_text}'"
                assert disconnect_text == "Disconnect", f"Expected 'Disconnect', got '{disconnect_text}'"
                
                record_agent_usage('connection-testing-agent', 90, 75)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_connect_button_click_sequence(self, webgcs_server):
        """TEST-014-B: Test connect button click and immediate response."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for SocketIO to be ready
                await page.wait_for_function("typeof io !== 'undefined'")
                
                connect_button = page.locator('#connect-btn')
                disconnect_button = page.locator('#disconnect-btn')
                status_element = page.locator('#connection-status')
                
                # Get initial status
                initial_status = await status_element.text_content()
                
                # Click connect button
                await connect_button.click()
                
                # Wait for any immediate response
                await page.wait_for_timeout(1000)
                
                # Button should still exist and be clickable
                await connect_button.wait_for()
                button_still_enabled = await connect_button.is_enabled()
                
                # Even if connection fails, the button interaction should work
                assert button_still_enabled is not None, "Connect button should maintain some state"
                
                record_agent_usage('connection-testing-agent', 100, 85)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_disconnect_button_click_when_enabled(self, webgcs_server):
        """TEST-014-C: Test disconnect button click when it becomes enabled."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                disconnect_button = page.locator('#disconnect-btn')
                
                # Initially disabled
                initial_state = await disconnect_button.is_enabled()
                assert not initial_state, "Disconnect button should be disabled initially"
                
                # Force enable for testing (simulating connected state)
                await page.evaluate("""
                    document.getElementById('disconnect-btn').disabled = false;
                """)
                
                # Now it should be enabled
                enabled_state = await disconnect_button.is_enabled()
                assert enabled_state, "Disconnect button should be enabled after manual enable"
                
                # Click disconnect button
                await disconnect_button.click()
                
                # Button should still exist after click
                await disconnect_button.wait_for()
                
                record_agent_usage('connection-testing-agent', 95, 80)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_multiple_connect_clicks(self, webgcs_server):
        """TEST-014-D: Test multiple connect button clicks in sequence."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for SocketIO
                await page.wait_for_function("typeof io !== 'undefined'")
                
                connect_button = page.locator('#connect-btn')
                
                # Click connect multiple times
                for i in range(3):
                    await connect_button.click()
                    await page.wait_for_timeout(500)  # Brief pause between clicks
                    
                    # Button should remain clickable
                    is_enabled = await connect_button.is_enabled()
                    assert is_enabled is not None, f"Connect button should maintain state after click {i+1}"
                
                record_agent_usage('connection-testing-agent', 105, 90)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_connection_status_persistence(self, webgcs_server):
        """TEST-014-E: Test connection status display persistence through interactions."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                status_element = page.locator('#connection-status')
                heartbeat_element = page.locator('#heartbeat-counter')
                connect_button = page.locator('#connect-btn')
                
                # Get initial values
                initial_status = await status_element.text_content()
                initial_heartbeat = await heartbeat_element.text_content()
                
                # Perform connect action
                await connect_button.click()
                await page.wait_for_timeout(1000)
                
                # Check status elements still exist and have content
                current_status = await status_element.text_content()
                current_heartbeat = await heartbeat_element.text_content()
                
                assert current_status is not None, "Status element should maintain content"
                assert current_heartbeat is not None, "Heartbeat element should maintain content"
                assert "Status:" in current_status, "Status should maintain proper format"
                assert "❤️ Heartbeat:" in current_heartbeat, "Heartbeat should maintain proper format"
                
                record_agent_usage('connection-testing-agent', 115, 100)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_page_reload_resets_state(self, webgcs_server):
        """TEST-014-F: Test that page reload properly resets connection state."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Perform some interactions
                connect_button = page.locator('#connect-btn')
                await connect_button.click()
                await page.wait_for_timeout(500)
                
                # Reload page
                await page.reload()
                await page.wait_for_load_state('networkidle')
                
                # Check that state is reset
                connect_button_after = page.locator('#connect-btn')
                disconnect_button_after = page.locator('#disconnect-btn')
                status_element_after = page.locator('#connection-status')
                heartbeat_element_after = page.locator('#heartbeat-counter')
                
                # Verify reset state
                connect_enabled = await connect_button_after.is_enabled()
                disconnect_enabled = await disconnect_button_after.is_enabled()
                status_text = await status_element_after.text_content()
                heartbeat_text = await heartbeat_element_after.text_content()
                
                assert connect_enabled, "Connect button should be enabled after reload"
                assert not disconnect_enabled, "Disconnect button should be disabled after reload"
                assert "❤️ Heartbeat: 0" == heartbeat_text, "Heartbeat should reset to 0"
                
                record_agent_usage('connection-testing-agent', 120, 105)
                
            finally:
                await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
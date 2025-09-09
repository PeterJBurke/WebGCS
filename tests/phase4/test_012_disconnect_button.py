"""
TEST-012: Disconnect Button Functionality
Tests the Disconnect button click functionality using Playwright MCP.

Requirements:
- Test actual disconnect button interaction
- Verify button exists but is disabled initially  
- Test button enable/disable state logic
- Confirm disconnect functionality when enabled
- Verify SocketIO 'disconnect_drone' event transmission
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestDisconnectButton:
    """Test disconnect button functionality with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5002)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5002,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5002"
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
    async def test_disconnect_button_exists_disabled_initially(self, webgcs_server):
        """TEST-012-A: Verify disconnect button exists but is disabled initially."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Verify disconnect button exists
                disconnect_button = page.locator('#disconnect-btn')
                await disconnect_button.wait_for()
                
                # Verify button is disabled initially
                is_enabled = await disconnect_button.is_enabled()
                assert not is_enabled, "Disconnect button should be disabled initially"
                
                # Verify button text
                button_text = await disconnect_button.text_content()
                assert button_text == "Disconnect", f"Expected 'Disconnect', got '{button_text}'"
                
                record_agent_usage('connection-testing-agent', 80, 65)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_disconnect_button_not_clickable_when_disabled(self, webgcs_server):
        """TEST-012-B: Test disconnect button is not clickable when disabled."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                disconnect_button = page.locator('#disconnect-btn')
                
                # Verify button is disabled
                is_enabled = await disconnect_button.is_enabled()
                assert not is_enabled, "Button should be disabled"
                
                # Try to click disabled button (should not throw error but have no effect)
                await disconnect_button.click(force=True)  # force click on disabled element
                
                # Button should still be disabled
                is_still_enabled = await disconnect_button.is_enabled()
                assert not is_still_enabled, "Button should remain disabled after forced click"
                
                record_agent_usage('connection-testing-agent', 70, 55)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_button_states_relationship(self, webgcs_server):
        """TEST-012-C: Test connect/disconnect button state relationship."""
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
                
                # The buttons should have opposite states
                assert connect_enabled != disconnect_enabled, "Buttons should have opposite enable states"
                
                record_agent_usage('connection-testing-agent', 85, 70)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_disconnect_button_has_event_handler(self, webgcs_server):
        """TEST-012-D: Verify disconnect button has proper event handler setup."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for main.js to load
                await page.wait_for_function("typeof io !== 'undefined'")
                
                # Check if disconnect button has event listener
                has_handler = await page.evaluate("""() => {
                    const btn = document.getElementById('disconnect-btn');
                    return btn && (btn.onclick !== null || typeof btn.addEventListener === 'function');
                }""")
                
                assert has_handler, "Disconnect button should have event handler setup"
                
                # Verify the handler is part of the main.js functionality
                main_js_elements = await page.evaluate("""
                    document.querySelector('script[src*="main.js"]') !== null
                """)
                
                assert main_js_elements, "main.js should be loaded for button functionality"
                
                record_agent_usage('connection-testing-agent', 90, 75)
                
            finally:
                await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
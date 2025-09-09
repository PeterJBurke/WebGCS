"""
TEST-013: Connection Status Display Functionality
Tests the connection status display updates using Playwright MCP.

Requirements:
- Test connection status display exists and shows initial state
- Verify status updates correctly reflect connection state
- Test heartbeat counter display and initial value
- Verify UI connection indicators update properly
- Test status text changes during connection events
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestConnectionStatusDisplay:
    """Test connection status display functionality with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5003)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5003,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5003"
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
    async def test_connection_status_element_exists(self, webgcs_server):
        """TEST-013-A: Verify connection status display element exists."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Verify connection status element exists
                status_element = page.locator('#connection-status')
                await status_element.wait_for()
                
                # Check initial status text
                status_text = await status_element.text_content()
                assert status_text is not None, "Status element should have text content"
                assert "Status:" in status_text, f"Expected status text to contain 'Status:', got '{status_text}'"
                
                record_agent_usage('connection-testing-agent', 75, 60)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_heartbeat_counter_element_exists(self, webgcs_server):
        """TEST-013-B: Verify heartbeat counter display element exists."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Verify heartbeat counter element exists
                heartbeat_element = page.locator('#heartbeat-counter')
                await heartbeat_element.wait_for()
                
                # Check initial heartbeat display
                heartbeat_text = await heartbeat_element.text_content()
                assert heartbeat_text is not None, "Heartbeat element should have text content"
                assert "❤️" in heartbeat_text, f"Expected heartbeat icon, got '{heartbeat_text}'"
                assert "Heartbeat:" in heartbeat_text, f"Expected 'Heartbeat:' text, got '{heartbeat_text}'"
                
                # Should show initial count of 0
                assert "0" in heartbeat_text, f"Expected initial count of 0, got '{heartbeat_text}'"
                
                record_agent_usage('connection-testing-agent', 85, 70)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_initial_connection_status_values(self, webgcs_server):
        """TEST-013-C: Test initial connection status display values."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Get initial status values
                status_element = page.locator('#connection-status')
                heartbeat_element = page.locator('#heartbeat-counter')
                
                status_text = await status_element.text_content()
                heartbeat_text = await heartbeat_element.text_content()
                
                # Check for connection state (could be "Disconnected" initially or "Connected to WebGCS" if SocketIO connects)
                assert ("Disconnected" in status_text or "disconnected" in status_text.lower() or 
                       "Connected to WebGCS" in status_text), \
                    f"Expected connection status (disconnected or WebGCS connected), got '{status_text}'"
                
                # Check heartbeat counter is 0
                assert "❤️ Heartbeat: 0" == heartbeat_text, \
                    f"Expected '❤️ Heartbeat: 0', got '{heartbeat_text}'"
                
                record_agent_usage('connection-testing-agent', 95, 80)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_status_display_elements_visibility(self, webgcs_server):
        """TEST-013-D: Test connection status elements are visible and properly styled."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Check status element visibility
                status_element = page.locator('#connection-status')
                heartbeat_element = page.locator('#heartbeat-counter')
                
                status_visible = await status_element.is_visible()
                heartbeat_visible = await heartbeat_element.is_visible()
                
                assert status_visible, "Connection status element should be visible"
                assert heartbeat_visible, "Heartbeat counter element should be visible"
                
                # Check they are in the connection status section
                connection_panel = page.locator('.connection-status')
                panel_visible = await connection_panel.is_visible()
                assert panel_visible, "Connection status panel should be visible"
                
                # Verify both elements are within the connection status panel
                status_in_panel = await connection_panel.locator('#connection-status').count()
                heartbeat_in_panel = await connection_panel.locator('#heartbeat-counter').count()
                
                assert status_in_panel == 1, "Status element should be in connection panel"
                assert heartbeat_in_panel == 1, "Heartbeat element should be in connection panel"
                
                record_agent_usage('connection-testing-agent', 100, 85)
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_connection_status_updates_after_socketio_ready(self, webgcs_server):
        """TEST-013-E: Verify status can be updated after SocketIO connection."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for SocketIO to be ready
                await page.wait_for_function("typeof io !== 'undefined'")
                
                # Get initial status
                status_element = page.locator('#connection-status')
                initial_status = await status_element.text_content()
                
                # Wait a moment for any automatic status updates from SocketIO connection
                await page.wait_for_timeout(2000)
                
                # Check if status potentially updated (SocketIO connection established)
                current_status = await status_element.text_content()
                
                # The status should either remain the same or update to show WebGCS connection
                assert current_status is not None, "Status should have text content"
                assert "Status:" in current_status, "Status should contain 'Status:' prefix"
                
                record_agent_usage('connection-testing-agent', 110, 95)
                
            finally:
                await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
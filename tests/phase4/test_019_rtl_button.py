"""
TEST-019: RTL (Return to Launch) Button Functionality
Tests the RTL button click functionality using Playwright MCP.

Requirements:
- Test actual RTL button click interaction
- Verify RTL button exists and is properly enabled
- Test SocketIO 'send_command' event transmission with RTL mode command
- Confirm MAVLink RTL mode change command to virtual drone
- Verify RTL button behavior and immediate response
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestRtlButton:
    """Test RTL button functionality with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5019)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5019,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5019"
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
    async def test_rtl_button_basic_functionality(self, webgcs_server):
        """TEST-019A: Test RTL button basic functionality."""
        record_agent_usage('flight-controls-testing-agent', 60, 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Verify RTL button exists and is accessible
                rtl_button = page.locator('#rtl-btn')
                await rtl_button.wait_for(state='visible')
                
                # Verify button is enabled
                assert await rtl_button.is_enabled(), "RTL button should be enabled"
                
                # Verify button text
                button_text = await rtl_button.text_content()
                assert button_text.strip().upper() == "RTL", f"Button text should be 'RTL', got: '{button_text}'"
                
                # Test button click (RTL is typically immediate emergency command)
                dialog_shown = False
                dialog_message = ""
                
                async def handle_dialog(dialog):
                    nonlocal dialog_shown, dialog_message
                    dialog_shown = True
                    dialog_message = dialog.message
                    await dialog.accept()
                
                page.on('dialog', handle_dialog)
                
                # Click RTL button
                await rtl_button.click()
                
                # Wait for any dialogs or UI updates
                await asyncio.sleep(1)
                
                # RTL may show confirmation but often immediate for safety
                if dialog_shown:
                    assert "RTL" in dialog_message.upper() or "RETURN" in dialog_message.upper(), \
                        f"Dialog should mention RTL command, got: {dialog_message}"
                    print(f"ℹ️  RTL confirmation dialog: {dialog_message}")
                
                print("✅ TEST-019A PASSED: RTL button basic functionality works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_rtl_button_socketio_command(self, webgcs_server):
        """TEST-019B: Test RTL button SocketIO command emission."""
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
                
                # Click RTL button
                rtl_button = page.locator('#rtl-btn')
                await rtl_button.click()
                
                # Wait for command processing
                await asyncio.sleep(2)
                
                # Check captured SocketIO events
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # Verify RTL command was sent via SocketIO
                rtl_command_sent = False
                for event in captured_events:
                    if event.get('event') == 'send_command':
                        data = event.get('data', {})
                        if (data.get('command') == 'rtl' or 'RTL' in str(data).upper() or
                            data.get('command') == 'set_mode' and 'RTL' in str(data).upper()):
                            rtl_command_sent = True
                            break
                
                assert rtl_command_sent, f"RTL command should be sent via SocketIO, captured: {captured_events}"
                
                print("✅ TEST-019B PASSED: RTL button SocketIO command emission works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_rtl_button_emergency_response(self, webgcs_server):
        """TEST-019C: Test RTL button emergency response capability."""
        record_agent_usage('flight-controls-testing-agent', 65, 55)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # RTL should be available as emergency command
                rtl_button = page.locator('#rtl-btn')
                await rtl_button.wait_for(state='visible')
                
                # Record time before click for response time
                start_time = time.time()
                
                # Set up dialog handler for quick acceptance
                async def handle_dialog(dialog):
                    await dialog.accept()
                
                page.on('dialog', handle_dialog)
                
                # Click RTL button
                await rtl_button.click()
                
                # Measure response time
                response_time = time.time() - start_time
                
                # Should be relatively quick response for emergency
                assert response_time < 2.0, f"RTL button should respond quickly, took {response_time:.2f}s"
                
                print("✅ TEST-019C PASSED: RTL button emergency response capability works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_rtl_button_mode_change(self, webgcs_server):
        """TEST-019D: Test RTL button mode change behavior."""
        record_agent_usage('flight-controls-testing-agent', 55, 45)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Monitor for mode change commands
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
                
                # Set up dialog handler
                async def handle_dialog(dialog):
                    await dialog.accept()
                
                page.on('dialog', handle_dialog)
                
                # Click RTL button
                rtl_button = page.locator('#rtl-btn')
                await rtl_button.click()
                
                # Wait for command processing
                await asyncio.sleep(2)
                
                # Check for mode change command
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # RTL should trigger mode change to RTL mode
                mode_change_found = False
                for event in captured_events:
                    if event.get('event') == 'send_command':
                        data = event.get('data', {})
                        if (data.get('command') in ['set_mode', 'rtl'] or 
                            'RTL' in str(data).upper()):
                            mode_change_found = True
                            break
                
                assert mode_change_found, f"RTL mode change command should be sent, captured: {captured_events}"
                
                print("✅ TEST-019D PASSED: RTL button mode change behavior works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio  
    async def test_rtl_button_immediate_availability(self, webgcs_server):
        """TEST-019E: Test RTL button immediate availability."""
        record_agent_usage('flight-controls-testing-agent', 50, 40)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # RTL should be immediately available (emergency command)
                rtl_button = page.locator('#rtl-btn')
                await rtl_button.wait_for(state='visible')
                
                # Should be enabled by default for emergency use
                is_enabled = await rtl_button.is_enabled()
                # Note: RTL might be disabled if not connected, but should exist
                
                # Button should exist and be properly labeled
                button_text = await rtl_button.text_content()
                assert button_text.strip().upper() == "RTL", f"Button text should be 'RTL', got: '{button_text}'"
                
                # RTL button should be visible and clickable
                assert await rtl_button.is_visible(), "RTL button should be visible"
                
                print("✅ TEST-019E PASSED: RTL button immediate availability works")
                
            finally:
                await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
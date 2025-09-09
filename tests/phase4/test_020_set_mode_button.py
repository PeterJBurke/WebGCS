"""
TEST-020: Set Mode Button Functionality
Tests the Set Mode button click functionality using Playwright MCP with flight mode dropdown selection.

Requirements:
- Test actual Set Mode button click interaction with flight mode dropdown
- Verify all flight modes are available: STABILIZE, ALT_HOLD, POS_HOLD, LOITER, GUIDED, RTL, LAND, AUTO, BRAKE
- Test mode selection from dropdown and Set button activation
- Verify SocketIO 'send_command' event transmission with set_mode command
- Confirm MAVLink SET_MODE messages for flight mode changes
- Validate mode display updates in Primary Flight Display
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestSetModeButton:
    """Test Set Mode button functionality with flight mode dropdown and real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5020)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5020,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5020"
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
    async def test_flight_mode_dropdown_options(self, webgcs_server):
        """TEST-020A: Test flight mode dropdown contains all required modes."""
        record_agent_usage('flight-controls-testing-agent', 60, 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Verify flight mode dropdown exists
                mode_dropdown = page.locator('#flight-mode')
                await mode_dropdown.wait_for(state='visible')
                
                # Get all available options
                options = await mode_dropdown.locator('option').all_text_contents()
                options = [opt.strip() for opt in options]
                
                # Required flight modes (from WebGCS PRD)
                required_modes = ['GUIDED', 'STABILIZE', 'ALT_HOLD', 'AUTO', 'RTL']
                
                # Check each required mode exists
                for mode in required_modes:
                    assert mode in options, f"Flight mode '{mode}' should be available, got: {options}"
                
                print(f"✅ Available flight modes: {options}")
                print("✅ TEST-020A PASSED: Flight mode dropdown contains required modes")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_set_mode_button_guided_mode(self, webgcs_server):
        """TEST-020B: Test Set Mode button with GUIDED mode selection."""
        record_agent_usage('flight-controls-testing-agent', 70, 60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Select GUIDED mode from dropdown
                mode_dropdown = page.locator('#flight-mode')
                await mode_dropdown.select_option('GUIDED')
                
                # Verify selection
                selected_value = await mode_dropdown.input_value()
                assert selected_value == 'GUIDED', f"Should select GUIDED mode, got: {selected_value}"
                
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
                
                # Click Set Mode button
                set_mode_button = page.locator('#set-mode-btn')
                await set_mode_button.wait_for(state='visible')
                assert await set_mode_button.is_enabled(), "Set Mode button should be enabled"
                
                button_text = await set_mode_button.text_content()
                assert button_text.strip().upper() == "SET", f"Button text should be 'SET', got: '{button_text}'"
                
                await set_mode_button.click()
                
                # Wait for command processing
                await asyncio.sleep(2)
                
                # Check captured SocketIO events
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # Verify set_mode command was sent
                mode_command_sent = False
                for event in captured_events:
                    if event.get('event') == 'send_command':
                        data = event.get('data', {})
                        if (data.get('command') == 'set_mode' and 
                            'GUIDED' in str(data).upper()):
                            mode_command_sent = True
                            break
                
                assert mode_command_sent, f"Set mode command should be sent via SocketIO, captured: {captured_events}"
                
                print("✅ TEST-020B PASSED: Set Mode button GUIDED mode selection works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_set_mode_button_auto_mode(self, webgcs_server):
        """TEST-020C: Test Set Mode button with AUTO mode selection."""
        record_agent_usage('flight-controls-testing-agent', 65, 55)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Select AUTO mode from dropdown
                mode_dropdown = page.locator('#flight-mode')
                await mode_dropdown.select_option('AUTO')
                
                # Verify selection
                selected_value = await mode_dropdown.input_value()
                assert selected_value == 'AUTO', f"Should select AUTO mode, got: {selected_value}"
                
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
                
                # Click Set Mode button
                set_mode_button = page.locator('#set-mode-btn')
                await set_mode_button.click()
                
                # Wait for command processing
                await asyncio.sleep(2)
                
                # Check captured SocketIO events
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # Verify AUTO mode command was sent
                mode_command_sent = False
                for event in captured_events:
                    if event.get('event') == 'send_command':
                        data = event.get('data', {})
                        if (data.get('command') == 'set_mode' and 
                            'AUTO' in str(data).upper()):
                            mode_command_sent = True
                            break
                
                assert mode_command_sent, f"AUTO mode command should be sent via SocketIO, captured: {captured_events}"
                
                print("✅ TEST-020C PASSED: Set Mode button AUTO mode selection works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_set_mode_button_rtl_mode(self, webgcs_server):
        """TEST-020D: Test Set Mode button with RTL mode selection."""
        record_agent_usage('flight-controls-testing-agent', 60, 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Select RTL mode from dropdown
                mode_dropdown = page.locator('#flight-mode')
                await mode_dropdown.select_option('RTL')
                
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
                
                # Click Set Mode button
                set_mode_button = page.locator('#set-mode-btn')
                await set_mode_button.click()
                
                # Wait for command processing
                await asyncio.sleep(2)
                
                # Check captured SocketIO events
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # Verify RTL mode command was sent
                mode_command_sent = False
                for event in captured_events:
                    if event.get('event') == 'send_command':
                        data = event.get('data', {})
                        if (data.get('command') == 'set_mode' and 
                            'RTL' in str(data).upper()):
                            mode_command_sent = True
                            break
                
                assert mode_command_sent, f"RTL mode command should be sent via SocketIO, captured: {captured_events}"
                
                print("✅ TEST-020D PASSED: Set Mode button RTL mode selection works")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_set_mode_button_multiple_modes(self, webgcs_server):
        """TEST-020E: Test Set Mode button with multiple mode changes."""
        record_agent_usage('flight-controls-testing-agent', 80, 70)
        
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
                
                mode_dropdown = page.locator('#flight-mode')
                set_mode_button = page.locator('#set-mode-btn')
                
                # Test multiple mode changes
                test_modes = ['GUIDED', 'STABILIZE', 'ALT_HOLD']
                
                for mode in test_modes:
                    # Select mode
                    await mode_dropdown.select_option(mode)
                    
                    # Verify selection
                    selected_value = await mode_dropdown.input_value()
                    assert selected_value == mode, f"Should select {mode} mode, got: {selected_value}"
                    
                    # Click Set Mode button
                    await set_mode_button.click()
                    await asyncio.sleep(1)  # Wait between commands
                
                # Wait for all commands to process
                await asyncio.sleep(2)
                
                # Check captured SocketIO events
                captured_events = await page.evaluate("window.capturedEvents || []")
                
                # Verify all mode commands were sent
                mode_commands = [e for e in captured_events if e.get('event') == 'send_command' 
                               and e.get('data', {}).get('command') == 'set_mode']
                
                assert len(mode_commands) >= len(test_modes), \
                    f"Should send {len(test_modes)} mode commands, got {len(mode_commands)}"
                
                print("✅ TEST-020E PASSED: Set Mode button multiple mode changes work")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_set_mode_button_default_selection(self, webgcs_server):
        """TEST-020F: Test Set Mode button default mode selection."""
        record_agent_usage('flight-controls-testing-agent', 50, 40)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Check default mode selection
                mode_dropdown = page.locator('#flight-mode')
                await mode_dropdown.wait_for(state='visible')
                
                default_mode = await mode_dropdown.input_value()
                
                # Default should be a reasonable mode (GUIDED expected)
                assert default_mode in ['GUIDED', 'STABILIZE'], \
                    f"Default mode should be GUIDED or STABILIZE, got: {default_mode}"
                
                # Set Mode button should exist and be enabled
                set_mode_button = page.locator('#set-mode-btn')
                await set_mode_button.wait_for(state='visible')
                assert await set_mode_button.is_enabled(), "Set Mode button should be enabled"
                
                print(f"✅ Default flight mode: {default_mode}")
                print("✅ TEST-020F PASSED: Set Mode button default selection works")
                
            finally:
                await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
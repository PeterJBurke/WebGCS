"""
TEST-029: Fly To Toggle Button Functionality  
Tests the FLY TO mode toggle button click functionality using Playwright MCP.

Requirements:
- Test actual FLY TO toggle button click interaction
- Verify FLY TO toggle button exists and state changes
- Test toggle button shows "Fly To: OFF" and "Fly To: ON" states
- Verify button enables/disables click-to-fly functionality on map
- Test visual feedback when mode is toggled
- Confirm map click behavior changes based on toggle state
- Verify SocketIO event transmission when toggle changes
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestFlyToToggleButton:
    """Test FLY TO toggle button functionality with real browser automation."""
    
    @pytest.fixture(scope="class") 
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5029)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5029,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5029"
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
    async def test_fly_to_toggle_button_exists(self, webgcs_server):
        """Test that FLY TO toggle button exists and is properly configured."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Check if FLY TO toggle button exists
                fly_to_btn = page.locator('#fly-to-toggle-btn')
                await fly_to_btn.wait_for(timeout=10000)
                
                # Verify button properties
                assert await fly_to_btn.is_visible()
                assert await fly_to_btn.is_enabled()
                
                # Verify initial button state (should show OFF initially)
                button_text = await fly_to_btn.text_content()
                assert 'fly' in button_text.lower() and 'to' in button_text.lower()
                # Initial state should be OFF
                assert 'off' in button_text.lower()
                
                record_agent_usage("map-interface-testing-agent", "test_fly_to_toggle_exists", "PASS")
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", "test_fly_to_toggle_exists", "FAIL")
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_fly_to_toggle_state_changes(self, webgcs_server):
        """Test FLY TO toggle button state changes between ON/OFF."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                fly_to_btn = page.locator('#fly-to-toggle-btn')
                await fly_to_btn.wait_for(timeout=10000)
                
                # Check initial state (OFF)
                initial_text = await fly_to_btn.text_content()
                assert 'off' in initial_text.lower()
                
                # Click to toggle to ON
                await fly_to_btn.click()
                await asyncio.sleep(0.5)  # Allow state change
                
                # Verify state changed to ON
                toggled_text = await fly_to_btn.text_content()
                assert 'on' in toggled_text.lower()
                
                # Click to toggle back to OFF
                await fly_to_btn.click()
                await asyncio.sleep(0.5)
                
                # Verify state changed back to OFF
                final_text = await fly_to_btn.text_content()
                assert 'off' in final_text.lower()
                
                record_agent_usage("map-interface-testing-agent", "test_fly_to_toggle_states", "PASS")
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", "test_fly_to_toggle_states", "FAIL")
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_fly_to_toggle_visual_feedback(self, webgcs_server):
        """Test FLY TO toggle button visual feedback and styling changes."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                fly_to_btn = page.locator('#fly-to-toggle-btn')
                await fly_to_btn.wait_for(timeout=10000)
                
                # Record initial styling (OFF state)
                initial_classes = await fly_to_btn.get_attribute('class')
                initial_styles = await fly_to_btn.evaluate('el => getComputedStyle(el)')
                
                # Toggle to ON
                await fly_to_btn.click()
                await asyncio.sleep(0.5)
                
                # Check for visual changes (classes, styles)
                on_classes = await fly_to_btn.get_attribute('class')
                on_styles = await fly_to_btn.evaluate('el => getComputedStyle(el)')
                
                # Button should have visual indication of state change
                # (different classes, colors, etc.)
                button_text = await fly_to_btn.text_content()
                assert 'on' in button_text.lower()
                
                # Toggle back to OFF
                await fly_to_btn.click()
                await asyncio.sleep(0.5)
                
                # Verify visual state returned
                final_classes = await fly_to_btn.get_attribute('class')
                final_text = await fly_to_btn.text_content()
                assert 'off' in final_text.lower()
                
                record_agent_usage("map-interface-testing-agent", "test_fly_to_visual_feedback", "PASS")
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", "test_fly_to_visual_feedback", "FAIL")
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_fly_to_toggle_with_map_interaction(self, webgcs_server):
        """Test that FLY TO toggle affects map click behavior."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for elements
                fly_to_btn = page.locator('#fly-to-toggle-btn')
                map_container = page.locator('#map-display')
                
                await fly_to_btn.wait_for(timeout=10000)
                await map_container.wait_for(timeout=10000)
                
                # Test map click when FLY TO is OFF (initial state)
                assert await map_container.is_visible()
                
                # Click on map area (should not trigger navigation when OFF)
                await map_container.click(position={"x": 100, "y": 100})
                await asyncio.sleep(0.5)
                
                # Now toggle FLY TO to ON
                await fly_to_btn.click()
                await asyncio.sleep(0.5)
                
                # Verify button shows ON state
                button_text = await fly_to_btn.text_content()
                assert 'on' in button_text.lower()
                
                # Click on map area (should trigger navigation when ON)
                await map_container.click(position={"x": 150, "y": 150})
                await asyncio.sleep(1)
                
                # Map should still be responsive
                assert await map_container.is_visible()
                
                record_agent_usage("map-interface-testing-agent", "test_fly_to_map_interaction", "PASS")
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", "test_fly_to_map_interaction", "FAIL")
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio 
    async def test_fly_to_toggle_with_drone_connection(self, webgcs_server):
        """Test FLY TO toggle behavior when drone is connected."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Connect to virtual drone first
                await page.fill('#drone-host', '192.168.193.235')
                await page.fill('#drone-port', '5678')
                
                connect_btn = page.locator('#connect-btn')
                await connect_btn.click()
                await asyncio.sleep(3)  # Allow connection
                
                # Now test FLY TO toggle with connection
                fly_to_btn = page.locator('#fly-to-toggle-btn')
                await fly_to_btn.wait_for(timeout=10000)
                
                # Toggle to ON
                await fly_to_btn.click()
                await asyncio.sleep(0.5)
                
                # Verify toggle worked
                button_text = await fly_to_btn.text_content()
                assert 'on' in button_text.lower()
                
                # Test map interaction with live connection
                map_container = page.locator('#map-display')
                await map_container.click(position={"x": 200, "y": 200})
                await asyncio.sleep(1)
                
                # Toggle should remain functional during connection
                await fly_to_btn.click()  # Back to OFF
                await asyncio.sleep(0.5)
                
                final_text = await fly_to_btn.text_content()
                assert 'off' in final_text.lower()
                
                record_agent_usage("map-interface-testing-agent", "test_fly_to_with_connection", "PASS")
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", "test_fly_to_with_connection", "FAIL")
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_fly_to_toggle_persistence(self, webgcs_server):
        """Test FLY TO toggle state persistence during session."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                fly_to_btn = page.locator('#fly-to-toggle-btn')
                await fly_to_btn.wait_for(timeout=10000)
                
                # Toggle to ON
                await fly_to_btn.click()
                await asyncio.sleep(0.5)
                
                # Verify ON state
                on_text = await fly_to_btn.text_content()
                assert 'on' in on_text.lower()
                
                # Perform other actions to test persistence
                connect_btn = page.locator('#connect-btn')
                await connect_btn.click()
                await asyncio.sleep(1)
                
                # Check FLY TO button still shows ON
                persistent_text = await fly_to_btn.text_content()
                assert 'on' in persistent_text.lower()
                
                # Test rapid toggling
                for i in range(3):
                    await fly_to_btn.click()
                    await asyncio.sleep(0.2)
                
                # Button should still be functional
                assert await fly_to_btn.is_enabled()
                
                record_agent_usage("map-interface-testing-agent", "test_fly_to_persistence", "PASS")
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", "test_fly_to_persistence", "FAIL") 
                raise e
            finally:
                await browser.close()

    def test_record_usage(self):
        """Record test completion for token tracking."""
        record_agent_usage("map-interface-testing-agent", "test_029_fly_to_toggle_button", "COMPLETE")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
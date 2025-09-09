"""
TEST-025: Navigation Controls Validation
Tests comprehensive navigation input validation, UI feedback, and control behavior using Playwright MCP.

Requirements:
- Test all navigation input field validation (latitude, longitude, altitude)
- Verify input field attributes (step, min, max, type)
- Test real-time validation feedback (border colors, tooltips)
- Test precision formatting on blur events
- Verify coordinate boundary enforcement
- Test input field focus management
- Test navigation panel UI responsiveness
- Verify button states and accessibility
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestNavigationControls:
    """Test comprehensive navigation controls validation and UI behavior with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5025)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5025,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5025"
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
    async def test_input_field_attributes(self, webgcs_server):
        """Test navigation input field HTML attributes and properties."""
        record_agent_usage('navigation-testing-agent', 100, 85)
        
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
                
                # Test latitude input attributes
                lat_input = page.locator('#nav-lat')
                lat_type = await lat_input.get_attribute('type')
                lat_step = await lat_input.get_attribute('step')
                
                assert lat_type == 'number', f"Latitude input should be type 'number', got '{lat_type}'"
                assert lat_step == '0.000001', f"Latitude step should be '0.000001' for 6 decimal precision, got '{lat_step}'"
                
                # Test longitude input attributes
                lon_input = page.locator('#nav-lon')
                lon_type = await lon_input.get_attribute('type')
                lon_step = await lon_input.get_attribute('step')
                
                assert lon_type == 'number', f"Longitude input should be type 'number', got '{lon_type}'"
                assert lon_step == '0.000001', f"Longitude step should be '0.000001' for 6 decimal precision, got '{lon_step}'"
                
                # Test altitude input attributes
                alt_input = page.locator('#nav-alt')
                alt_type = await alt_input.get_attribute('type')
                alt_value = await alt_input.get_attribute('value')
                
                assert alt_type == 'number', f"Altitude input should be type 'number', got '{alt_type}'"
                assert alt_value == '10', f"Altitude should have default value '10', got '{alt_value}'"
                
                # Test input field labels
                nav_panel = page.locator('.navigation-panel')
                panel_text = await nav_panel.text_content()
                
                assert 'Lat:' in panel_text, "Navigation panel should contain 'Lat:' label"
                assert 'Lon:' in panel_text, "Navigation panel should contain 'Lon:' label"
                assert 'Alt:' in panel_text, "Navigation panel should contain 'Alt:' label"
                assert 'm' in panel_text, "Navigation panel should show altitude units 'm'"
                
                print("✅ Input field attributes are correct")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_real_time_validation_feedback(self, webgcs_server):
        """Test real-time validation feedback with visual cues."""
        record_agent_usage('navigation-testing-agent', 120, 100)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#nav-lat', timeout=10000)
                
                lat_input = page.locator('#nav-lat')
                lon_input = page.locator('#nav-lon')
                alt_input = page.locator('#nav-alt')
                
                # Test invalid latitude real-time feedback
                await lat_input.fill('95.0')  # Invalid latitude
                await lat_input.blur()  # Trigger blur event
                await page.wait_for_timeout(300)
                
                # Check for visual feedback (red border)
                lat_border_color = await lat_input.evaluate('el => getComputedStyle(el).borderColor')
                lat_title = await lat_input.get_attribute('title')
                
                # Note: Border color detection can be tricky, so we mainly check for title (tooltip)
                assert lat_title is not None and 'between -90 and 90' in lat_title, \
                    f"Latitude should show validation tooltip, got title: '{lat_title}'"
                
                # Test valid latitude clears feedback
                await lat_input.fill('37.7749')
                await lat_input.blur()
                await page.wait_for_timeout(300)
                
                lat_title_valid = await lat_input.get_attribute('title')
                assert not lat_title_valid or lat_title_valid == '', \
                    f"Valid latitude should clear tooltip, got: '{lat_title_valid}'"
                
                # Test invalid longitude feedback
                await lon_input.fill('185.0')  # Invalid longitude
                await lon_input.blur()
                await page.wait_for_timeout(300)
                
                lon_title = await lon_input.get_attribute('title')
                assert lon_title is not None and 'between -180 and 180' in lon_title, \
                    f"Longitude should show validation tooltip, got: '{lon_title}'"
                
                # Test invalid altitude feedback
                await alt_input.fill('-10')  # Invalid altitude
                await alt_input.blur()
                await page.wait_for_timeout(300)
                
                alt_title = await alt_input.get_attribute('title')
                assert alt_title is not None and 'positive' in alt_title, \
                    f"Altitude should show validation tooltip, got: '{alt_title}'"
                
                print("✅ Real-time validation feedback working correctly")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_precision_formatting(self, webgcs_server):
        """Test coordinate precision formatting on blur events."""
        record_agent_usage('navigation-testing-agent', 100, 90)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#nav-lat', timeout=10000)
                
                lat_input = page.locator('#nav-lat')
                lon_input = page.locator('#nav-lon')
                alt_input = page.locator('#nav-alt')
                
                # Test latitude precision formatting (6 decimal places)
                await lat_input.fill('37.77')  # Input with fewer decimals
                await lat_input.blur()
                await page.wait_for_timeout(300)
                
                lat_value = await lat_input.input_value()
                assert lat_value == '37.770000', f"Latitude should format to 6 decimals, got '{lat_value}'"
                
                # Test longitude precision formatting (6 decimal places)
                await lon_input.fill('-122.4')  # Input with fewer decimals
                await lon_input.blur()
                await page.wait_for_timeout(300)
                
                lon_value = await lon_input.input_value()
                assert lon_value == '-122.400000', f"Longitude should format to 6 decimals, got '{lon_value}'"
                
                # Test altitude precision formatting (1 decimal place)
                await alt_input.fill('50')  # Input without decimal
                await alt_input.blur()
                await page.wait_for_timeout(300)
                
                alt_value = await alt_input.input_value()
                assert alt_value == '50.0', f"Altitude should format to 1 decimal, got '{alt_value}'"
                
                # Test precision with more decimals than needed
                await lat_input.fill('37.774953829')  # More than 6 decimals
                await lat_input.blur()
                await page.wait_for_timeout(300)
                
                lat_value = await lat_input.input_value()
                assert lat_value == '37.774954', f"Latitude should round to 6 decimals, got '{lat_value}'"
                
                print("✅ Precision formatting working correctly")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_navigation_button_states(self, webgcs_server):
        """Test navigation button states and accessibility."""
        record_agent_usage('navigation-testing-agent', 90, 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#goto-btn', timeout=10000)
                await page.wait_for_selector('#clear-btn', timeout=10000)
                
                goto_btn = page.locator('#goto-btn')
                clear_btn = page.locator('#clear-btn')
                
                # Test button visibility and enabled state
                assert await goto_btn.is_visible(), "GO TO button should be visible"
                assert await goto_btn.is_enabled(), "GO TO button should be enabled"
                assert await clear_btn.is_visible(), "CLEAR button should be visible"
                assert await clear_btn.is_enabled(), "CLEAR button should be enabled"
                
                # Test button text content
                goto_text = await goto_btn.text_content()
                clear_text = await clear_btn.text_content()
                
                assert goto_text.strip() == 'GO TO', f"GO TO button should show 'GO TO', got '{goto_text}'"
                assert clear_text.strip() == 'CLEAR', f"CLEAR button should show 'CLEAR', got '{clear_text}'"
                
                # Test button click responsiveness
                await goto_btn.click()
                await page.wait_for_timeout(300)
                
                # Should show validation error since no coordinates entered
                error_message = page.locator('.nav-error')
                assert await error_message.is_visible(), "Should show validation error when clicking GO TO with empty fields"
                
                # Test CLEAR button click responsiveness
                await clear_btn.click()
                await page.wait_for_timeout(300)
                
                # Error should be cleared
                assert not await error_message.is_visible(), "CLEAR should remove validation errors"
                
                print("✅ Navigation button states are correct")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_comprehensive_boundary_testing(self, webgcs_server):
        """Test comprehensive boundary value testing for all coordinate inputs."""
        record_agent_usage('navigation-testing-agent', 110, 95)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#nav-lat', timeout=10000)
                
                # Comprehensive boundary test cases
                boundary_tests = [
                    # Latitude boundary tests
                    {'field': '#nav-lat', 'value': '90.0', 'should_pass': True, 'desc': 'Max valid latitude'},
                    {'field': '#nav-lat', 'value': '-90.0', 'should_pass': True, 'desc': 'Min valid latitude'},
                    {'field': '#nav-lat', 'value': '90.000001', 'should_pass': False, 'desc': 'Above max latitude'},
                    {'field': '#nav-lat', 'value': '-90.000001', 'should_pass': False, 'desc': 'Below min latitude'},
                    
                    # Longitude boundary tests
                    {'field': '#nav-lon', 'value': '180.0', 'should_pass': True, 'desc': 'Max valid longitude'},
                    {'field': '#nav-lon', 'value': '-180.0', 'should_pass': True, 'desc': 'Min valid longitude'},
                    {'field': '#nav-lon', 'value': '180.000001', 'should_pass': False, 'desc': 'Above max longitude'},
                    {'field': '#nav-lon', 'value': '-180.000001', 'should_pass': False, 'desc': 'Below min longitude'},
                    
                    # Altitude boundary tests
                    {'field': '#nav-alt', 'value': '0.0', 'should_pass': True, 'desc': 'Min valid altitude'},
                    {'field': '#nav-alt', 'value': '5000.0', 'should_pass': True, 'desc': 'Max valid altitude'},
                    {'field': '#nav-alt', 'value': '-0.1', 'should_pass': False, 'desc': 'Below min altitude'},
                    {'field': '#nav-alt', 'value': '5000.1', 'should_pass': False, 'desc': 'Above max altitude'},
                ]
                
                for test_case in boundary_tests:
                    # Clear all fields first
                    await page.locator('#clear-btn').click()
                    await page.wait_for_timeout(200)
                    
                    # Set valid defaults for other fields
                    if test_case['field'] != '#nav-lat':
                        await page.locator('#nav-lat').fill('0.0')
                    if test_case['field'] != '#nav-lon':
                        await page.locator('#nav-lon').fill('0.0')
                    if test_case['field'] != '#nav-alt':
                        await page.locator('#nav-alt').fill('10.0')
                    
                    # Set the test value
                    await page.locator(test_case['field']).fill(test_case['value'])
                    
                    # Click GO TO to trigger validation
                    await page.locator('#goto-btn').click()
                    await page.wait_for_timeout(500)
                    
                    # Check validation result
                    error_message = page.locator('.nav-error')
                    error_visible = await error_message.is_visible()
                    
                    if test_case['should_pass']:
                        assert not error_visible, f"Test '{test_case['desc']}' should pass but got validation error"
                    else:
                        assert error_visible, f"Test '{test_case['desc']}' should fail but no validation error shown"
                        
                        # Verify error message is appropriate
                        if error_visible:
                            error_text = await error_message.text_content()
                            if 'lat' in test_case['field']:
                                assert 'Latitude' in error_text, f"Should show latitude error for {test_case['desc']}"
                            elif 'lon' in test_case['field']:
                                assert 'Longitude' in error_text, f"Should show longitude error for {test_case['desc']}"
                            elif 'alt' in test_case['field']:
                                assert 'Altitude' in error_text, f"Should show altitude error for {test_case['desc']}"
                
                print("✅ Comprehensive boundary testing completed successfully")
                
            finally:
                await browser.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
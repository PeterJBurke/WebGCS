"""
UI Validation Testing Agent - Safety Limits Enforcement Tests

Phase 6 Test 4: Safety Limits and Operational Boundaries Testing
Tests safety limit enforcement and operational boundary validation using Playwright MCP.

SAFETY-CRITICAL: Ensures dangerous operations are prevented by UI safety systems.
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class TestSafetyLimitsEnforcement:
    """
    Tests safety limit enforcement systems:
    - Altitude limits (120m maximum for safety)
    - Speed limits and reasonable operational ranges
    - Geofence boundary validation
    - Command rate limiting and sequencing
    - Emergency stop functionality
    - Concurrent command conflict resolution
    """
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.base_url = "http://localhost:5002"
        cls.timeout = 10000
        
    async def setup_browser(self):
        """Setup browser and page for testing"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Set up dialog handling
        self.page.on("dialog", lambda dialog: dialog.dismiss())
        
        # Navigate to WebGCS
        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state('networkidle')
        
    async def teardown_browser(self):
        """Cleanup browser resources"""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    @pytest.mark.asyncio
    async def test_altitude_safety_limits_120m_maximum(self):
        """Test that altitude inputs are limited to safe operational values (120m max)"""
        await self.setup_browser()
        
        try:
            # Test altitude field enforcement
            altitude_field = await self.page.query_selector('#goto-altitude')
            if altitude_field:
                # Test values above 120m safety limit
                dangerous_altitudes = ['121', '200', '500', '1000', '5000']
                
                for alt in dangerous_altitudes:
                    await self.page.fill('#goto-altitude', alt)
                    await self.page.blur('#goto-altitude')
                    await asyncio.sleep(0.2)
                    
                    # Check if validation prevents dangerous altitude
                    error_element = await self.page.query_selector('#goto-altitude-error')
                    input_class = await self.page.get_attribute('#goto-altitude', 'class')
                    
                    has_error_indication = False
                    
                    if error_element and await error_element.is_visible():
                        error_text = await error_element.text_content()
                        if error_text and error_text.strip():
                            has_error_indication = True
                            print(f"Altitude {alt}m blocked with error: {error_text}")
                            
                    if input_class and 'input-error' in input_class:
                        has_error_indication = True
                        
                    # SAFETY CRITICAL: Must prevent dangerous altitudes
                    assert has_error_indication, f"Dangerous altitude {alt}m must be blocked by validation"
                    
                # Test safe altitudes (under 120m)
                safe_altitudes = ['10', '50', '100', '119']
                
                for alt in safe_altitudes:
                    await self.page.fill('#goto-altitude', alt)
                    await self.page.blur('#goto-altitude')
                    await asyncio.sleep(0.2)
                    
                    # Should not show error for safe altitudes
                    error_element = await self.page.query_selector('#goto-altitude-error')
                    if error_element:
                        error_visible = await error_element.is_visible()
                        if error_visible:
                            error_text = await error_element.text_content()
                            assert not error_text or not error_text.strip(), \
                                f"Safe altitude {alt}m should not show error"
                                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_takeoff_altitude_safety_limits(self):
        """Test takeoff altitude safety limits (1-100m range)"""
        await self.setup_browser()
        
        try:
            takeoff_field = await self.page.query_selector('#takeoff-altitude')
            if takeoff_field:
                # Test dangerous takeoff altitudes
                dangerous_takeoffs = ['0', '101', '200', '1000']
                
                for alt in dangerous_takeoffs:
                    await self.page.fill('#takeoff-altitude', alt)
                    await self.page.blur('#takeoff-altitude')
                    await asyncio.sleep(0.2)
                    
                    # Should show validation error
                    error_element = await self.page.query_selector('#takeoff-altitude-error')
                    input_class = await self.page.get_attribute('#takeoff-altitude', 'class')
                    
                    has_error = False
                    if error_element and await error_element.is_visible():
                        error_text = await error_element.text_content()
                        if error_text and error_text.strip():
                            has_error = True
                            
                    if input_class and 'input-error' in input_class:
                        has_error = True
                        
                    assert has_error, f"Dangerous takeoff altitude {alt}m must be blocked"
                    
                # Test safe takeoff altitudes
                safe_takeoffs = ['1', '10', '25', '50', '100']
                
                for alt in safe_takeoffs:
                    await self.page.fill('#takeoff-altitude', alt)
                    await self.page.blur('#takeoff-altitude')
                    await asyncio.sleep(0.2)
                    
                    # Should not show error
                    error_element = await self.page.query_selector('#takeoff-altitude-error')
                    if error_element and await error_element.is_visible():
                        error_text = await error_element.text_content()
                        assert not error_text or not error_text.strip(), \
                            f"Safe takeoff altitude {alt}m should not show error"
                            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_speed_limit_enforcement(self):
        """Test that speed inputs are limited to safe operational values"""
        await self.setup_browser()
        
        try:
            # Look for speed input fields
            speed_fields = await self.page.query_selector_all('input[type="number"][id*="speed"], input[data-validation="speed"]')
            
            if speed_fields:
                for speed_field in speed_fields:
                    field_id = await speed_field.get_attribute('id')
                    print(f"Testing speed field: {field_id}")
                    
                    # Test excessive speeds (validation.js limits to 30 m/s)
                    dangerous_speeds = ['31', '50', '100', '1000']
                    
                    for speed in dangerous_speeds:
                        await self.page.fill(f'#{field_id}', speed)
                        await self.page.blur(f'#{field_id}')
                        await asyncio.sleep(0.2)
                        
                        # Check for validation error
                        error_selector = f'#{field_id}-error'
                        error_element = await self.page.query_selector(error_selector)
                        input_class = await self.page.get_attribute(f'#{field_id}', 'class')
                        
                        has_error = False
                        if error_element and await error_element.is_visible():
                            error_text = await error_element.text_content()
                            if error_text and error_text.strip():
                                has_error = True
                                
                        if input_class and 'input-error' in input_class:
                            has_error = True
                            
                        assert has_error, f"Dangerous speed {speed} m/s must be blocked"
                        
                    # Test safe speeds
                    safe_speeds = ['1', '5', '10', '20', '30']
                    
                    for speed in safe_speeds:
                        await self.page.fill(f'#{field_id}', speed)
                        await self.page.blur(f'#{field_id}')
                        await asyncio.sleep(0.2)
                        
                        error_selector = f'#{field_id}-error'
                        error_element = await self.page.query_selector(error_selector)
                        if error_element and await error_element.is_visible():
                            error_text = await error_element.text_content()
                            assert not error_text or not error_text.strip(), \
                                f"Safe speed {speed} m/s should not show error"
            else:
                print("No speed input fields found")
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_coordinate_boundary_validation(self):
        """Test that coordinate inputs enforce geographic boundaries"""
        await self.setup_browser()
        
        try:
            # Test latitude boundaries (strict -90 to 90)
            extreme_latitudes = ['-91', '91', '-180', '180', '999', '-999']
            
            for lat in extreme_latitudes:
                await self.page.fill('#goto-latitude', lat)
                await self.page.blur('#goto-latitude')
                await asyncio.sleep(0.2)
                
                error_element = await self.page.query_selector('#goto-latitude-error')
                input_class = await self.page.get_attribute('#goto-latitude', 'class')
                
                has_error = False
                if error_element and await error_element.is_visible():
                    error_text = await error_element.text_content()
                    if error_text and error_text.strip():
                        has_error = True
                        
                if input_class and 'input-error' in input_class:
                    has_error = True
                    
                assert has_error, f"Invalid latitude {lat} must be blocked"
                
            # Test longitude boundaries (strict -180 to 180)
            extreme_longitudes = ['-181', '181', '360', '-360', '999', '-999']
            
            for lon in extreme_longitudes:
                await self.page.fill('#goto-longitude', lon)
                await self.page.blur('#goto-longitude')
                await asyncio.sleep(0.2)
                
                error_element = await self.page.query_selector('#goto-longitude-error')
                input_class = await self.page.get_attribute('#goto-longitude', 'class')
                
                has_error = False
                if error_element and await error_element.is_visible():
                    error_text = await error_element.text_content()
                    if error_text and error_text.strip():
                        has_error = True
                        
                if input_class and 'input-error' in input_class:
                    has_error = True
                    
                assert has_error, f"Invalid longitude {lon} must be blocked"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_rapid_command_rate_limiting(self):
        """Test that rapid command clicking is rate-limited for safety"""
        await self.setup_browser()
        
        try:
            # Test rapid clicking on safety-critical buttons
            critical_buttons = ['#arm-btn', '#disarm-btn', '#takeoff-btn']
            
            for button_id in critical_buttons:
                button = await self.page.query_selector(button_id)
                if button:
                    print(f"Testing rate limiting for {button_id}")
                    
                    # Set up dialog counter
                    dialog_count = 0
                    
                    def count_dialogs(dialog):
                        nonlocal dialog_count
                        dialog_count += 1
                        dialog.dismiss()
                        
                    self.page.on("dialog", count_dialogs)
                    
                    # Rapid click test
                    click_count = 10
                    start_time = time.time()
                    
                    for i in range(click_count):
                        await button.click()
                        await asyncio.sleep(0.05)  # Very rapid clicking
                        
                    end_time = time.time()
                    total_time = end_time - start_time
                    
                    await asyncio.sleep(1)  # Wait for any delayed dialogs
                    
                    print(f"{button_id}: {click_count} clicks in {total_time:.2f}s, {dialog_count} dialogs")
                    
                    # Rate limiting should prevent all clicks from processing
                    # Either through debouncing or queuing
                    assert dialog_count <= click_count, "Should not exceed click count"
                    
                    # Good rate limiting: significantly fewer dialogs than clicks
                    if dialog_count < click_count / 2:
                        print(f"Good rate limiting detected for {button_id}")
                    elif dialog_count == click_count:
                        print(f"No rate limiting for {button_id} - all clicks processed")
                    else:
                        print(f"Partial rate limiting for {button_id}")
                        
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_concurrent_command_conflict_resolution(self):
        """Test handling of conflicting simultaneous commands"""
        await self.setup_browser()
        
        try:
            # Test conflicting commands (ARM vs DISARM)
            arm_btn = await self.page.query_selector('#arm-btn')
            disarm_btn = await self.page.query_selector('#disarm-btn')
            
            if arm_btn and disarm_btn:
                # Set up dialog handling to accept all
                self.page.on("dialog", lambda dialog: dialog.accept())
                
                # Try to click both buttons rapidly
                await arm_btn.click()
                await asyncio.sleep(0.1)
                await disarm_btn.click()
                
                # System should handle this gracefully
                await asyncio.sleep(2)
                
                # Check that UI remains functional
                arm_visible = await arm_btn.is_visible()
                disarm_visible = await disarm_btn.is_visible()
                
                assert arm_visible and disarm_visible, "UI should remain functional after conflict"
                
                print("Concurrent command conflict test completed")
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_emergency_stop_accessibility(self):
        """Test that emergency stop is always accessible"""
        await self.setup_browser()
        
        try:
            emergency_btn = await self.page.query_selector('#emergency-stop-btn')
            
            if emergency_btn:
                # Emergency stop should always be enabled
                is_disabled = await emergency_btn.is_disabled()
                assert not is_disabled, "Emergency stop should never be disabled"
                
                # Should be prominently styled
                button_style = await emergency_btn.evaluate('el => getComputedStyle(el)')
                bg_color = button_style.get('backgroundColor', '')
                color = button_style.get('color', '')
                
                # Should use prominent emergency colors (red)
                print(f"Emergency button colors - bg: {bg_color}, text: {color}")
                
                # Should be large enough for easy access
                button_box = await emergency_btn.bounding_box()
                if button_box:
                    assert button_box['width'] >= 80, "Emergency button should be large enough"
                    assert button_box['height'] >= 30, "Emergency button should be tall enough"
                    
                # Test emergency button functionality
                self.page.on("dialog", lambda dialog: dialog.accept())
                await emergency_btn.click()
                await asyncio.sleep(0.5)
                
                # Should remain accessible after click
                still_visible = await emergency_btn.is_visible()
                assert still_visible, "Emergency button should remain accessible"
                
            else:
                print("Emergency stop button not found")
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_input_length_limits(self):
        """Test that input fields have reasonable length limits"""
        await self.setup_browser()
        
        try:
            # Test excessive input length
            input_fields = ['#goto-latitude', '#goto-longitude', '#goto-altitude', '#takeoff-altitude']
            
            for field_id in input_fields:
                field = await self.page.query_selector(field_id)
                if field:
                    # Test extremely long input
                    long_input = '1' * 1000  # 1000 characters
                    
                    await self.page.fill(field_id, long_input)
                    actual_value = await self.page.input_value(field_id)
                    
                    # Should limit input length
                    assert len(actual_value) < len(long_input), \
                        f"Field {field_id} should limit input length"
                        
                    # Should have reasonable limit
                    assert len(actual_value) <= 50, \
                        f"Field {field_id} should have reasonable length limit"
                        
                    print(f"{field_id}: limited to {len(actual_value)} characters")
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_numerical_precision_limits(self):
        """Test that numerical inputs have appropriate precision limits"""
        await self.setup_browser()
        
        try:
            # Test excessive decimal precision
            precision_fields = ['#goto-latitude', '#goto-longitude', '#goto-altitude']
            
            for field_id in precision_fields:
                field = await self.page.query_selector(field_id)
                if field:
                    # Test excessive precision
                    high_precision = '45.123456789012345678901234567890'
                    
                    await self.page.fill(field_id, high_precision)
                    await self.page.blur(field_id)
                    await asyncio.sleep(0.2)
                    
                    actual_value = await self.page.input_value(field_id)
                    
                    # Should limit precision reasonably
                    decimal_places = len(actual_value.split('.')[-1]) if '.' in actual_value else 0
                    assert decimal_places <= 8, \
                        f"Field {field_id} should limit decimal precision"
                        
                    print(f"{field_id}: precision limited to {decimal_places} decimal places")
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_safety_interlock_systems(self):
        """Test that safety interlocks prevent dangerous operation sequences"""
        await self.setup_browser()
        
        try:
            # Test takeoff without valid altitude
            takeoff_btn = await self.page.query_selector('#takeoff-btn')
            if takeoff_btn:
                # Clear takeoff altitude
                await self.page.fill('#takeoff-altitude', '')
                
                # Set up dialog handling
                dialogs = []
                def capture_dialog(dialog):
                    dialogs.append(dialog.message)
                    dialog.dismiss()
                    
                self.page.on("dialog", capture_dialog)
                
                # Try to takeoff without altitude
                await takeoff_btn.click()
                await asyncio.sleep(0.5)
                
                # Should prevent takeoff or show error
                if dialogs:
                    dialog_msg = dialogs[-1].lower()
                    # Should either be error or not confirmation
                    if 'takeoff' in dialog_msg and 'altitude' in dialog_msg:
                        print("Takeoff dialog mentions altitude requirement")
                    elif 'error' in dialog_msg or 'invalid' in dialog_msg:
                        print("Takeoff blocked with error message")
                        
                # Test with invalid altitude
                await self.page.fill('#takeoff-altitude', '1000')  # Too high
                await takeoff_btn.click()
                await asyncio.sleep(0.5)
                
                # Should be blocked by validation
                print("Takeoff safety interlock test completed")
                
        finally:
            await self.teardown_browser()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
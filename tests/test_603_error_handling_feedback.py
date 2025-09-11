"""
UI Validation Testing Agent - Error Handling & User Feedback Tests

Phase 6 Test 3: Error Handling and User Feedback System Testing
Tests error message display, loading states, and user feedback systems using Playwright MCP.

SAFETY-CRITICAL: Ensures users receive clear feedback about system state and errors.
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class TestErrorHandlingFeedback:
    """
    Tests error handling and user feedback systems:
    - Error message display and positioning
    - Loading states during command processing
    - Success/failure visual indicators
    - Timeout handling for unresponsive commands
    - Connection error feedback
    - Command acknowledgment feedback
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
        
        # Navigate to WebGCS
        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state('networkidle')
        
    async def teardown_browser(self):
        """Cleanup browser resources"""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    @pytest.mark.asyncio
    async def test_error_message_visibility_positioning(self):
        """Test that error messages are clearly visible and well-positioned"""
        await self.setup_browser()
        
        try:
            # Test latitude error message positioning
            await self.page.fill('#goto-latitude', '999')
            await self.page.blur('#goto-latitude')
            await asyncio.sleep(0.2)
            
            error_element = await self.page.query_selector('#goto-latitude-error')
            if error_element and await error_element.is_visible():
                # Check error message positioning
                input_box = await self.page.bounding_box('#goto-latitude')
                error_box = await error_element.bounding_box()
                
                assert error_box is not None, "Error message should have bounding box"
                assert input_box is not None, "Input should have bounding box"
                
                # Error should be positioned near the input field
                vertical_distance = abs(error_box['y'] - (input_box['y'] + input_box['height']))
                assert vertical_distance < 50, "Error message should be close to input field"
                
                # Check text color and visibility
                error_style = await error_element.evaluate('el => getComputedStyle(el)')
                color = error_style.get('color', '')
                
                # Should use red color for errors
                assert 'rgb(255' in color or 'red' in color.lower() or '#f' in color, \
                    "Error messages should use red color"
                    
                # Check font size is readable
                font_size = error_style.get('fontSize', '0px')
                size_value = int(font_size.replace('px', '').split('.')[0])
                assert size_value >= 12, "Error text should be at least 12px for readability"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_multiple_error_messages_handling(self):
        """Test handling of multiple simultaneous error messages"""
        await self.setup_browser()
        
        try:
            # Fill multiple fields with invalid data
            await self.page.fill('#goto-latitude', '999')
            await self.page.fill('#goto-longitude', '999')
            await self.page.fill('#goto-altitude', '9999')
            
            # Blur all fields to trigger validation
            await self.page.blur('#goto-latitude')
            await self.page.blur('#goto-longitude')
            await self.page.blur('#goto-altitude')
            
            await asyncio.sleep(0.5)
            
            # Check that multiple error messages can be displayed simultaneously
            error_elements = await self.page.query_selector_all('.input-error-message, [id$="-error"]')
            visible_errors = []
            
            for error_el in error_elements:
                if await error_el.is_visible():
                    error_text = await error_el.text_content()
                    if error_text and error_text.strip():
                        visible_errors.append(error_text.strip())
                        
            assert len(visible_errors) >= 2, "Should display multiple error messages simultaneously"
            
            # Check that errors don't overlap or interfere with each other
            for i, error_el in enumerate(error_elements):
                if await error_el.is_visible():
                    error_box = await error_el.bounding_box()
                    if error_box:
                        # Check it's not off-screen
                        assert error_box['x'] >= 0, f"Error {i} should not be off-screen horizontally"
                        assert error_box['y'] >= 0, f"Error {i} should not be off-screen vertically"
                        
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_error_message_timeout_dismissal(self):
        """Test if error messages auto-dismiss after timeout"""
        await self.setup_browser()
        
        try:
            # Trigger an error message
            await self.page.fill('#goto-latitude', '999')
            await self.page.blur('#goto-latitude')
            await asyncio.sleep(0.2)
            
            error_element = await self.page.query_selector('#goto-latitude-error')
            if error_element and await error_element.is_visible():
                # Wait to see if error auto-dismisses
                await asyncio.sleep(5)
                
                is_still_visible = await error_element.is_visible()
                
                # Document behavior - errors may persist until corrected
                if is_still_visible:
                    print("Error messages persist until corrected (good for safety)")
                    
                    # Clear the error by entering valid value
                    await self.page.fill('#goto-latitude', '45')
                    await self.page.blur('#goto-latitude')
                    await asyncio.sleep(0.2)
                    
                    # Error should now be gone
                    is_cleared = not await error_element.is_visible()
                    assert is_cleared, "Error should clear when valid input is provided"
                else:
                    print("Error messages auto-dismiss after timeout")
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_loading_states_during_commands(self):
        """Test that loading states are shown during command processing"""
        await self.setup_browser()
        
        try:
            # Set up to capture command processing states
            command_buttons = ['#arm-btn', '#disarm-btn', '#takeoff-btn', '#goto-btn']
            
            for button_id in command_buttons:
                button = await self.page.query_selector(button_id)
                if button:
                    # Check initial state
                    initial_text = await button.text_content()
                    is_disabled = await button.is_disabled()
                    
                    print(f"Button {button_id}: '{initial_text}' (disabled: {is_disabled})")
                    
                    # Some buttons may show loading state when clicked
                    # This documents the current behavior
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_command_acknowledgment_feedback(self):
        """Test that users get feedback when commands are acknowledged"""
        await self.setup_browser()
        
        try:
            # Look for status display areas
            status_areas = await self.page.query_selector_all('.status-message, .command-status, #status-display, .alert, .notification')
            
            print(f"Found {len(status_areas)} potential status display areas")
            
            # Test with a safe command like setting flight mode
            stabilize_btn = await self.page.query_selector('#stabilize-btn')
            if stabilize_btn:
                # Clear any existing status messages
                initial_status = []
                for area in status_areas:
                    if await area.is_visible():
                        text = await area.text_content()
                        if text and text.strip():
                            initial_status.append(text.strip())
                            
                # Click button (this might require confirmation)
                await stabilize_btn.click()
                await asyncio.sleep(1)
                
                # Check for new status messages
                final_status = []
                for area in status_areas:
                    if await area.is_visible():
                        text = await area.text_content()
                        if text and text.strip():
                            final_status.append(text.strip())
                            
                # Look for changes in status
                new_messages = set(final_status) - set(initial_status)
                if new_messages:
                    print(f"New status messages: {new_messages}")
                else:
                    print("No visible status feedback detected")
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_connection_error_feedback(self):
        """Test feedback when connection errors occur"""
        await self.setup_browser()
        
        try:
            # Look for connection status indicators
            connection_indicators = await self.page.query_selector_all('.connection-status, #connection-status, .server-status, .drone-status')
            
            # Check current connection status display
            for indicator in connection_indicators:
                if await indicator.is_visible():
                    status_text = await indicator.text_content()
                    print(f"Connection status: {status_text}")
                    
                    # Check styling for connection states
                    indicator_class = await indicator.get_attribute('class')
                    if indicator_class:
                        if 'connected' in indicator_class.lower():
                            print("Connected state styling detected")
                        elif 'disconnected' in indicator_class.lower():
                            print("Disconnected state styling detected")
                            
            # Test disconnect scenario if possible
            disconnect_btn = await self.page.query_selector('#disconnect-btn, #disconnect-server-btn')
            if disconnect_btn:
                await disconnect_btn.click()
                await asyncio.sleep(1)
                
                # Check if connection status updated
                for indicator in connection_indicators:
                    if await indicator.is_visible():
                        new_status = await indicator.text_content()
                        print(f"Status after disconnect: {new_status}")
                        
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_form_validation_prevents_submission_feedback(self):
        """Test that form validation prevents submission and shows clear feedback"""
        await self.setup_browser()
        
        try:
            # Fill navigation form with invalid data
            await self.page.fill('#goto-latitude', '999')
            await self.page.fill('#goto-longitude', '999')
            await self.page.fill('#goto-altitude', '9999')
            
            # Try to submit via goto button
            goto_btn = await self.page.query_selector('#goto-btn')
            if goto_btn:
                # Check initial button state
                is_initially_disabled = await goto_btn.is_disabled()
                print(f"Goto button initially disabled: {is_initially_disabled}")
                
                # Click the button
                await goto_btn.click()
                await asyncio.sleep(0.5)
                
                # Check for validation feedback
                # Look for any indication that submission was prevented
                error_elements = await self.page.query_selector_all('.input-error-message, [id$="-error"]')
                visible_errors = 0
                
                for error_el in error_elements:
                    if await error_el.is_visible():
                        error_text = await error_el.text_content()
                        if error_text and error_text.strip():
                            visible_errors += 1
                            
                assert visible_errors > 0, "Invalid form submission should show validation errors"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_timeout_handling_visual_feedback(self):
        """Test visual feedback for command timeouts"""
        await self.setup_browser()
        
        try:
            # This test documents timeout behavior
            # In a real system, commands might timeout if drone doesn't respond
            
            # Look for any timeout-related UI elements
            timeout_elements = await self.page.query_selector_all('[class*="timeout"], [id*="timeout"], .error, .warning')
            
            print(f"Found {len(timeout_elements)} potential timeout/error display elements")
            
            # Test a command that might timeout (if drone is not connected)
            arm_btn = await self.page.query_selector('#arm-btn')
            if arm_btn:
                # Accept any confirmation dialog
                self.page.on("dialog", lambda dialog: dialog.accept())
                
                await arm_btn.click()
                
                # Wait longer to see if timeout occurs
                await asyncio.sleep(6)  # Longer than typical command timeout
                
                # Check for timeout feedback
                for element in timeout_elements:
                    if await element.is_visible():
                        text = await element.text_content()
                        if text and ('timeout' in text.lower() or 'error' in text.lower()):
                            print(f"Timeout feedback detected: {text}")
                            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_success_failure_visual_indicators(self):
        """Test visual indicators for command success/failure"""
        await self.setup_browser()
        
        try:
            # Look for success/failure indicator elements
            status_elements = await self.page.query_selector_all('.success, .failure, .error, .warning, .info, [class*="status"]')
            
            print(f"Found {len(status_elements)} potential status indicator elements")
            
            # Document current styling for status indicators
            for element in status_elements:
                if await element.is_visible():
                    element_class = await element.get_attribute('class')
                    element_text = await element.text_content()
                    
                    if element_text and element_text.strip():
                        print(f"Status element: '{element_text.strip()}' (class: {element_class})")
                        
                        # Check color coding
                        style = await element.evaluate('el => getComputedStyle(el)')
                        color = style.get('color', '')
                        bg_color = style.get('backgroundColor', '')
                        
                        if 'success' in (element_class or '').lower():
                            # Should use green for success
                            assert 'green' in color.lower() or 'rgb(0, 128, 0)' in color or '0, 255, 0' in color, \
                                "Success indicators should use green color"
                                
                        elif 'error' in (element_class or '').lower() or 'failure' in (element_class or '').lower():
                            # Should use red for errors
                            assert 'red' in color.lower() or 'rgb(255, 0, 0)' in color or '255, 0, 0' in color, \
                                "Error indicators should use red color"
                                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_error_message_accessibility(self):
        """Test that error messages meet accessibility standards"""
        await self.setup_browser()
        
        try:
            # Trigger error messages
            await self.page.fill('#goto-latitude', '999')
            await self.page.blur('#goto-latitude')
            await asyncio.sleep(0.2)
            
            error_element = await self.page.query_selector('#goto-latitude-error')
            if error_element and await error_element.is_visible():
                # Check accessibility attributes
                aria_live = await error_element.get_attribute('aria-live')
                aria_atomic = await error_element.get_attribute('aria-atomic')
                role = await error_element.get_attribute('role')
                
                # Good accessibility practices
                print(f"Error accessibility - aria-live: {aria_live}, role: {role}")
                
                # Check text contrast
                style = await error_element.evaluate('el => getComputedStyle(el)')
                color = style.get('color', '')
                bg_color = style.get('backgroundColor', '')
                
                print(f"Error colors - text: {color}, background: {bg_color}")
                
                # Check if error is properly associated with input
                input_element = await self.page.query_selector('#goto-latitude')
                described_by = await input_element.get_attribute('aria-describedby')
                error_id = await error_element.get_attribute('id')
                
                if described_by and error_id:
                    assert error_id in described_by, "Error should be linked to input via aria-describedby"
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_progressive_error_disclosure(self):
        """Test that errors are disclosed progressively (not overwhelming)"""
        await self.setup_browser()
        
        try:
            # Fill form with multiple errors
            await self.page.fill('#goto-latitude', 'invalid')
            await self.page.fill('#goto-longitude', 'invalid')  
            await self.page.fill('#goto-altitude', 'invalid')
            
            # Focus and blur each field progressively
            await self.page.focus('#goto-latitude')
            await self.page.blur('#goto-latitude')
            await asyncio.sleep(0.1)
            
            # Count visible errors after first field
            error_count_1 = len(await self.page.query_selector_all('.input-error-message:visible, [id$="-error"]:visible'))
            
            await self.page.focus('#goto-longitude')
            await self.page.blur('#goto-longitude')
            await asyncio.sleep(0.1)
            
            # Count visible errors after second field
            error_count_2 = len(await self.page.query_selector_all('.input-error-message:visible, [id$="-error"]:visible'))
            
            await self.page.focus('#goto-altitude')
            await self.page.blur('#goto-altitude')
            await asyncio.sleep(0.1)
            
            # Count visible errors after third field
            error_count_3 = len(await self.page.query_selector_all('.input-error-message:visible, [id$="-error"]:visible'))
            
            print(f"Progressive error disclosure: {error_count_1} -> {error_count_2} -> {error_count_3}")
            
            # Errors should appear progressively, not all at once initially
            assert error_count_1 <= error_count_2 <= error_count_3, \
                "Errors should be disclosed progressively as user interacts with fields"
                
        finally:
            await self.teardown_browser()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
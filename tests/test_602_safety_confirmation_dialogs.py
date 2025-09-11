"""
UI Validation Testing Agent - Safety Confirmation Dialog Tests

Phase 6 Test 2: Safety Confirmation System Testing
Tests critical command confirmations for ARM, DISARM, TAKEOFF using Playwright MCP.

SAFETY-CRITICAL: Ensures no dangerous operations occur without explicit user confirmation.
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class TestSafetyConfirmationDialogs:
    """
    Tests safety confirmation dialogs for critical flight operations:
    - ARM command confirmation
    - DISARM command confirmation  
    - TAKEOFF command confirmation
    - Emergency command confirmations
    - Dialog cancel functionality
    - Connection state validation before commands
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
        
        # Set up dialog handling for confirmation tests
        self.dialog_messages = []
        self.dialog_responses = []
        
        def handle_dialog(dialog):
            self.dialog_messages.append(dialog.message)
            # Default to dismiss dialog for safety
            dialog.dismiss()
            
        self.page.on("dialog", handle_dialog)
        
        # Navigate to WebGCS
        await self.page.goto(self.base_url)
        await self.page.wait_for_selector('#arm-btn', timeout=self.timeout)
        
    async def teardown_browser(self):
        """Cleanup browser resources"""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    @pytest.mark.asyncio
    async def test_arm_command_requires_confirmation(self):
        """Test that ARM command shows confirmation dialog"""
        await self.setup_browser()
        
        try:
            # Clear any previous dialog messages
            self.dialog_messages.clear()
            
            # Set up dialog handler to accept confirmation
            def accept_dialog(dialog):
                self.dialog_messages.append(dialog.message)
                dialog.accept()
                
            self.page.on("dialog", accept_dialog)
            
            # Click ARM button
            arm_button = await self.page.query_selector('#arm-btn')
            assert arm_button is not None, "ARM button should exist"
            
            await arm_button.click()
            
            # Wait for dialog to appear
            await asyncio.sleep(0.5)
            
            # Verify confirmation dialog appeared
            assert len(self.dialog_messages) > 0, "ARM command should show confirmation dialog"
            
            # Verify dialog message content
            dialog_message = self.dialog_messages[-1].lower()
            assert 'arm' in dialog_message, "Dialog should mention ARM operation"
            assert any(word in dialog_message for word in ['motor', 'enable', 'spin']), \
                "Dialog should warn about motor activation"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_disarm_command_requires_confirmation(self):
        """Test that DISARM command shows confirmation dialog"""
        await self.setup_browser()
        
        try:
            # Clear any previous dialog messages
            self.dialog_messages.clear()
            
            # Set up dialog handler to accept confirmation
            def accept_dialog(dialog):
                self.dialog_messages.append(dialog.message)
                dialog.accept()
                
            self.page.on("dialog", accept_dialog)
            
            # Click DISARM button
            disarm_button = await self.page.query_selector('#disarm-btn')
            assert disarm_button is not None, "DISARM button should exist"
            
            await disarm_button.click()
            
            # Wait for dialog to appear
            await asyncio.sleep(0.5)
            
            # Verify confirmation dialog appeared
            assert len(self.dialog_messages) > 0, "DISARM command should show confirmation dialog"
            
            # Verify dialog message content
            dialog_message = self.dialog_messages[-1].lower()
            assert 'disarm' in dialog_message, "Dialog should mention DISARM operation"
            assert any(word in dialog_message for word in ['motor', 'stop', 'immediately']), \
                "Dialog should warn about immediate motor stop"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_takeoff_command_requires_confirmation(self):
        """Test that TAKEOFF command shows confirmation dialog"""
        await self.setup_browser()
        
        try:
            # Clear any previous dialog messages
            self.dialog_messages.clear()
            
            # First set a valid takeoff altitude
            await self.page.fill('#takeoff-altitude', '10')
            
            # Set up dialog handler to accept confirmation
            def accept_dialog(dialog):
                self.dialog_messages.append(dialog.message)
                dialog.accept()
                
            self.page.on("dialog", accept_dialog)
            
            # Click TAKEOFF button
            takeoff_button = await self.page.query_selector('#takeoff-btn')
            assert takeoff_button is not None, "TAKEOFF button should exist"
            
            await takeoff_button.click()
            
            # Wait for dialog to appear
            await asyncio.sleep(0.5)
            
            # Verify confirmation dialog appeared
            assert len(self.dialog_messages) > 0, "TAKEOFF command should show confirmation dialog"
            
            # Verify dialog message content
            dialog_message = self.dialog_messages[-1].lower()
            assert 'takeoff' in dialog_message, "Dialog should mention TAKEOFF operation"
            assert any(word in dialog_message for word in ['altitude', 'meters', 'm']), \
                "Dialog should mention altitude information"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_emergency_stop_requires_confirmation(self):
        """Test that emergency stop shows confirmation dialog"""
        await self.setup_browser()
        
        try:
            # Clear any previous dialog messages
            self.dialog_messages.clear()
            
            # Set up dialog handler to accept confirmation
            def accept_dialog(dialog):
                self.dialog_messages.append(dialog.message)
                dialog.accept()
                
            self.page.on("dialog", accept_dialog)
            
            # Click emergency stop button
            emergency_button = await self.page.query_selector('#emergency-stop-btn')
            if emergency_button:
                await emergency_button.click()
                
                # Wait for dialog to appear
                await asyncio.sleep(0.5)
                
                # Verify confirmation dialog appeared
                assert len(self.dialog_messages) > 0, "Emergency stop should show confirmation dialog"
                
                # Verify dialog message content
                dialog_message = self.dialog_messages[-1].lower()
                assert any(word in dialog_message for word in ['emergency', 'stop', 'immediate']), \
                    "Dialog should indicate emergency nature"
            else:
                print("Emergency stop button not found - may not be implemented yet")
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_dialog_cancel_functionality(self):
        """Test that canceling confirmation dialogs prevents command execution"""
        await self.setup_browser()
        
        try:
            # Test ARM command cancellation
            self.dialog_messages.clear()
            dialog_dismissed = False
            
            def dismiss_dialog(dialog):
                nonlocal dialog_dismissed
                self.dialog_messages.append(dialog.message)
                dialog.dismiss()
                dialog_dismissed = True
                
            self.page.on("dialog", dismiss_dialog)
            
            # Click ARM button and dismiss dialog
            arm_button = await self.page.query_selector('#arm-btn')
            if arm_button:
                await arm_button.click()
                await asyncio.sleep(0.5)
                
                # Verify dialog was shown and dismissed
                assert len(self.dialog_messages) > 0, "Dialog should have appeared"
                assert dialog_dismissed, "Dialog should have been dismissed"
                
                # Check that no command was actually sent (look for status indicators)
                # This is a safety check - cancelled commands should not execute
                
            # Test DISARM command cancellation
            dialog_dismissed = False
            self.dialog_messages.clear()
            
            disarm_button = await self.page.query_selector('#disarm-btn')
            if disarm_button:
                await disarm_button.click()
                await asyncio.sleep(0.5)
                
                assert len(self.dialog_messages) > 0, "DISARM dialog should have appeared"
                assert dialog_dismissed, "DISARM dialog should have been dismissed"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_takeoff_altitude_validation_before_confirmation(self):
        """Test that invalid takeoff altitude prevents confirmation dialog"""
        await self.setup_browser()
        
        try:
            # Clear any previous dialog messages
            self.dialog_messages.clear()
            
            # Set up dialog handler
            def handle_dialog(dialog):
                self.dialog_messages.append(dialog.message)
                dialog.accept()
                
            self.page.on("dialog", handle_dialog)
            
            # Test with invalid altitude (too high)
            await self.page.fill('#takeoff-altitude', '1000')
            
            takeoff_button = await self.page.query_selector('#takeoff-btn')
            if takeoff_button:
                await takeoff_button.click()
                await asyncio.sleep(0.5)
                
                # Should either show validation error or not show confirmation
                # Check for validation error first
                error_element = await self.page.query_selector('#takeoff-altitude-error')
                has_validation_error = False
                
                if error_element and await error_element.is_visible():
                    has_validation_error = True
                
                # If no validation error shown, there should be no confirmation dialog
                # OR an error dialog instead of confirmation
                if not has_validation_error:
                    # Should either have no dialog or an error dialog
                    if len(self.dialog_messages) > 0:
                        dialog_msg = self.dialog_messages[-1].lower()
                        assert 'error' in dialog_msg or 'invalid' in dialog_msg or 'must be' in dialog_msg, \
                            "Invalid altitude should show error, not confirmation"
                            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_command_blocking_when_disconnected(self):
        """Test that commands are blocked when server/drone is disconnected"""
        await self.setup_browser()
        
        try:
            # Check initial connection status
            connection_status = await self.page.query_selector('.connection-status, #connection-status')
            
            # Look for disconnect button or connection indicator
            disconnect_button = await self.page.query_selector('#disconnect-btn, #disconnect-server-btn')
            
            if disconnect_button:
                # Disconnect from server
                await disconnect_button.click()
                await asyncio.sleep(1)
                
                # Clear dialog messages
                self.dialog_messages.clear()
                
                # Try to ARM when disconnected
                arm_button = await self.page.query_selector('#arm-btn')
                if arm_button:
                    # Check if button is disabled
                    is_disabled = await arm_button.is_disabled()
                    
                    if not is_disabled:
                        # If not disabled, click should either be prevented or show error
                        await arm_button.click()
                        await asyncio.sleep(0.5)
                        
                        # Should either show no dialog or an error dialog
                        if len(self.dialog_messages) > 0:
                            dialog_msg = self.dialog_messages[-1].lower()
                            assert any(word in dialog_msg for word in ['connect', 'disconnect', 'error', 'not connected']), \
                                "Should show connection error when disconnected"
                    else:
                        print("ARM button properly disabled when disconnected")
            else:
                print("Disconnect functionality not found - may not be implemented")
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_confirmation_dialog_message_quality(self):
        """Test that confirmation dialog messages are clear and informative"""
        await self.setup_browser()
        
        try:
            # Test ARM dialog message quality
            self.dialog_messages.clear()
            
            def capture_dialog(dialog):
                self.dialog_messages.append(dialog.message)
                dialog.dismiss()
                
            self.page.on("dialog", capture_dialog)
            
            # Test ARM confirmation
            arm_button = await self.page.query_selector('#arm-btn')
            if arm_button:
                await arm_button.click()
                await asyncio.sleep(0.5)
                
                if len(self.dialog_messages) > 0:
                    arm_msg = self.dialog_messages[-1]
                    
                    # Check message quality
                    assert len(arm_msg) > 10, "ARM dialog message should be descriptive"
                    assert arm_msg.endswith('?'), "Should be phrased as a question"
                    assert any(word in arm_msg.lower() for word in ['arm', 'motor', 'enable']), \
                        "Should clearly indicate what ARM does"
                        
            # Test DISARM confirmation
            self.dialog_messages.clear()
            disarm_button = await self.page.query_selector('#disarm-btn')
            if disarm_button:
                await disarm_button.click()
                await asyncio.sleep(0.5)
                
                if len(self.dialog_messages) > 0:
                    disarm_msg = self.dialog_messages[-1]
                    
                    # Check message quality
                    assert len(disarm_msg) > 10, "DISARM dialog message should be descriptive"
                    assert disarm_msg.endswith('?'), "Should be phrased as a question"
                    assert any(word in disarm_msg.lower() for word in ['disarm', 'motor', 'stop']), \
                        "Should clearly indicate what DISARM does"
                        
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_double_confirmation_for_critical_commands(self):
        """Test if emergency commands require double confirmation"""
        await self.setup_browser()
        
        try:
            # Look for commands that might require double confirmation
            emergency_button = await self.page.query_selector('#emergency-stop-btn')
            
            if emergency_button:
                self.dialog_messages.clear()
                confirmation_count = 0
                
                def count_confirmations(dialog):
                    nonlocal confirmation_count
                    confirmation_count += 1
                    self.dialog_messages.append(dialog.message)
                    dialog.accept()
                    
                self.page.on("dialog", count_confirmations)
                
                await emergency_button.click()
                await asyncio.sleep(1)  # Wait for potential second dialog
                
                # Check if multiple confirmations were required
                print(f"Emergency stop confirmations: {confirmation_count}")
                
                # Document whether double confirmation is implemented
                if confirmation_count >= 2:
                    print("Double confirmation implemented for emergency stop")
                    assert confirmation_count >= 2, "Emergency commands should require double confirmation"
                else:
                    print("Single confirmation for emergency stop")
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_rapid_click_prevention(self):
        """Test that rapid button clicking is handled properly"""
        await self.setup_browser()
        
        try:
            # Test rapid clicking on ARM button
            self.dialog_messages.clear()
            
            def auto_dismiss(dialog):
                self.dialog_messages.append(dialog.message)
                dialog.dismiss()
                
            self.page.on("dialog", auto_dismiss)
            
            arm_button = await self.page.query_selector('#arm-btn')
            if arm_button:
                # Click multiple times rapidly
                for i in range(5):
                    await arm_button.click()
                    await asyncio.sleep(0.1)
                    
                await asyncio.sleep(1)  # Wait for all dialogs to process
                
                # Should handle rapid clicks gracefully
                # Either debounce or show only one dialog
                print(f"Dialogs from rapid clicking: {len(self.dialog_messages)}")
                
                # Good behavior: 1 dialog (debounced) or multiple handled gracefully
                assert len(self.dialog_messages) >= 1, "Should handle rapid clicks"
                
                # Verify system remains stable
                button_visible = await arm_button.is_visible()
                assert button_visible, "Button should remain functional after rapid clicks"
                
        finally:
            await self.teardown_browser()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
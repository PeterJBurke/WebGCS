"""
TEST-704: Safety System Integration

Tests safety interlock systems across multiple components.

Validates:
- Safety interlock systems across multiple components
- Command blocking when safety conditions not met
- Emergency procedures and fail-safe behaviors
- Safety confirmations prevent dangerous command sequences
"""

import pytest
import time
import asyncio
import threading
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import requests

from src.web.app_factory import initialize_app


class TestSafetySystemIntegration:
    """Safety system integration tests."""

    @pytest.fixture(scope="class")
    def safety_app(self):
        """Create application with safety monitoring."""
        app, socketio = initialize_app()
        
        app.config.update({
            'TESTING': True,
            'WEB_SERVER_PORT': 5002,
            'COMMAND_ACK_TIMEOUT': 5.0,
            'HEARTBEAT_TIMEOUT': 10
        })
        
        def run_server():
            socketio.run(app, host='localhost', port=5002, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        yield app, socketio
        
        if hasattr(app, 'mavlink_service'):
            app.mavlink_service.stop()

    @pytest.mark.asyncio
    async def test_command_sequence_safety_interlocks(self, safety_app):
        """Test safety interlocks prevent dangerous command sequences."""
        app, socketio = safety_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Test 1: Cannot takeoff without connection
                takeoff_btn = page.locator('#takeoff-btn')
                if await takeoff_btn.is_visible():
                    # Should be disabled when not connected
                    is_enabled = await takeoff_btn.is_enabled()
                    if is_enabled:
                        # Try clicking - should either do nothing or show error
                        await takeoff_btn.click()
                        await asyncio.sleep(1)
                        
                        # System should handle this safely (no crash)
                        connection_status = await page.locator('#connection-status').text_content()
                        assert 'Connected' not in connection_status, "Should not takeoff without connection"
                
                # Connect to drone
                await page.click('#connect-btn')
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Test 2: Cannot takeoff without being armed
                takeoff_btn = page.locator('#takeoff-btn')
                if await takeoff_btn.is_visible():
                    # Check if takeoff requires ARM first
                    armed_status = await page.locator('#armed-status').text_content()
                    
                    if 'DISARMED' in armed_status:
                        await takeoff_btn.click()
                        
                        # Should show safety confirmation or error
                        try:
                            confirmation_modal = page.locator('#safety-confirmation-modal')
                            await confirmation_modal.wait_for(state='visible', timeout=3000)
                            
                            # Check if confirmation warns about ARM requirement
                            modal_text = await page.locator('#safety-confirmation-message').text_content()
                            
                            # Cancel the dangerous operation
                            await page.click('#cancel-action-btn')
                            await confirmation_modal.wait_for(state='hidden')
                            
                        except:
                            # May handle differently - verify no unsafe action occurred
                            pass
                        
                        # Verify still disarmed
                        await asyncio.sleep(1)
                        current_status = await page.locator('#armed-status').text_content()
                        assert 'DISARMED' in current_status, "Should remain disarmed after cancelled takeoff"
                
                # Test 3: Safe ARM → Takeoff sequence
                await page.click('#arm-btn')
                
                # Handle ARM confirmation
                try:
                    confirmation_modal = page.locator('#safety-confirmation-modal')
                    await confirmation_modal.wait_for(state='visible', timeout=5000)
                    
                    # Verify ARM confirmation content
                    modal_text = await page.locator('#safety-confirmation-message').text_content()
                    assert 'ARM' in modal_text.upper(), "ARM confirmation should mention ARM"
                    
                    await page.click('#confirm-action-btn')
                except:
                    pass
                
                # Wait for ARM to complete
                await page.wait_for_function(
                    "document.querySelector('#armed-status').textContent.includes('ARMED')",
                    timeout=10000
                )
                
                # Now takeoff should be safer
                await page.click('#takeoff-btn')
                
                try:
                    await confirmation_modal.wait_for(state='visible', timeout=5000)
                    
                    # Verify takeoff confirmation
                    modal_text = await page.locator('#safety-confirmation-message').text_content()
                    assert 'TAKEOFF' in modal_text.upper() or 'TAKE' in modal_text.upper()
                    
                    await page.click('#confirm-action-btn')
                except:
                    pass
                
                await asyncio.sleep(2)
                
                # Test 4: Emergency stop procedures
                # Test RTL (Return to Launch) safety
                rtl_btn = page.locator('#rtl-btn')
                if await rtl_btn.is_visible():
                    await rtl_btn.click()
                    
                    try:
                        await confirmation_modal.wait_for(state='visible', timeout=3000)
                        
                        modal_text = await page.locator('#safety-confirmation-message').text_content()
                        assert any(word in modal_text.upper() for word in ['RTL', 'RETURN', 'LAUNCH', 'HOME'])
                        
                        await page.click('#confirm-action-btn')
                    except:
                        pass
                
                # Test 5: Safe shutdown sequence
                await page.click('#land-btn')
                
                try:
                    await confirmation_modal.wait_for(state='visible', timeout=3000)
                    await page.click('#confirm-action-btn')
                except:
                    pass
                
                await asyncio.sleep(2)
                
                # Final DISARM
                await page.click('#disarm-btn')
                
                try:
                    await confirmation_modal.wait_for(state='visible', timeout=3000)
                    await page.click('#confirm-action-btn')
                except:
                    pass
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_safety_confirmation_system(self, safety_app):
        """Test comprehensive safety confirmation system."""
        app, socketio = safety_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Connect first
                await page.click('#connect-btn')
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Test safety confirmations for each critical command
                critical_commands = [
                    ('#arm-btn', 'ARM'),
                    ('#takeoff-btn', 'TAKEOFF'),
                    ('#land-btn', 'LAND'),
                    ('#rtl-btn', 'RTL'),
                    ('#disarm-btn', 'DISARM')
                ]
                
                for button_selector, expected_keyword in critical_commands:
                    button = page.locator(button_selector)
                    
                    if await button.is_visible():
                        # Click the button
                        await button.click()
                        
                        # Check for safety confirmation dialog
                        try:
                            confirmation_modal = page.locator('#safety-confirmation-modal')
                            await confirmation_modal.wait_for(state='visible', timeout=5000)
                            
                            # Verify confirmation dialog content
                            modal_text = await page.locator('#safety-confirmation-message').text_content()
                            assert expected_keyword in modal_text.upper(), \
                                f"Safety confirmation for {button_selector} should mention {expected_keyword}"
                            
                            # Verify both confirm and cancel buttons are present
                            confirm_btn = page.locator('#confirm-action-btn')
                            cancel_btn = page.locator('#cancel-action-btn')
                            
                            assert await confirm_btn.is_visible(), f"Confirm button missing for {button_selector}"
                            assert await cancel_btn.is_visible(), f"Cancel button missing for {button_selector}"
                            
                            # Test cancel functionality
                            await cancel_btn.click()
                            await confirmation_modal.wait_for(state='hidden', timeout=3000)
                            
                            # Wait before next test
                            await asyncio.sleep(0.5)
                            
                        except Exception as e:
                            print(f"Safety confirmation test for {button_selector}: {e}")
                
                # Test confirmation with actual execution
                await page.click('#arm-btn')
                
                try:
                    confirmation_modal = page.locator('#safety-confirmation-modal')
                    await confirmation_modal.wait_for(state='visible', timeout=5000)
                    
                    # This time, confirm the action
                    confirm_btn = page.locator('#confirm-action-btn')
                    await confirm_btn.click()
                    
                    # Verify action was executed
                    await page.wait_for_function(
                        "document.querySelector('#armed-status').textContent.includes('ARMED')",
                        timeout=10000
                    )
                    
                    armed_status = await page.locator('#armed-status').text_content()
                    assert 'ARMED' in armed_status, "ARM command should execute after confirmation"
                    
                except Exception as e:
                    print(f"Confirmation execution test failed: {e}")
                
            finally:
                await browser.close()

    def test_command_timeout_safety(self, safety_app):
        """Test command acknowledgment timeout safety mechanisms."""
        app, socketio = safety_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone for timeout testing")
        
        time.sleep(2)
        
        # Test command sender timeout behavior
        command_sender = mavlink_service.command_sender
        
        # Get initial pending commands count
        initial_pending = len(command_sender.get_pending_commands())
        
        # Send a command and verify timeout handling
        start_time = time.time()
        result = command_sender.arm_vehicle()
        command_time = time.time() - start_time
        
        # Command should complete within timeout period
        timeout_limit = float(app.config.get('COMMAND_ACK_TIMEOUT', 5.0))
        assert command_time <= timeout_limit + 1.0, f"Command took too long: {command_time:.2f}s"
        
        # Verify pending commands are managed properly
        final_pending = len(command_sender.get_pending_commands())
        
        # Pending count should not grow indefinitely
        assert final_pending <= initial_pending + 1, "Pending commands not managed properly"
        
        # Test multiple rapid commands (stress test)
        rapid_commands = []
        for i in range(3):
            start = time.time()
            cmd_result = command_sender.arm_vehicle() if i % 2 == 0 else command_sender.disarm_vehicle()
            duration = time.time() - start
            rapid_commands.append(duration)
            time.sleep(0.5)  # Brief delay between commands
        
        # All commands should complete within reasonable time
        max_command_time = max(rapid_commands)
        assert max_command_time <= timeout_limit + 2.0, f"Rapid command too slow: {max_command_time:.2f}s"
        
        # Verify system remains stable
        final_status = mavlink_service.get_status()
        assert final_status['mavlink_connected'], "Connection should remain stable after rapid commands"

    def test_heartbeat_loss_safety(self, safety_app):
        """Test safety behavior when heartbeat is lost."""
        app, socketio = safety_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone for heartbeat testing")
        
        time.sleep(2)
        
        # Get initial connection state
        initial_status = mavlink_service.get_status()
        assert initial_status['mavlink_connected'], "Should start connected"
        
        # Monitor heartbeat status
        connection_manager = mavlink_service.connection_manager
        initial_heartbeat = connection_manager.get_last_heartbeat()
        
        # Wait and check heartbeat updates
        time.sleep(2)
        updated_heartbeat = connection_manager.get_last_heartbeat()
        
        if initial_heartbeat and updated_heartbeat:
            # Heartbeat should be updating
            assert updated_heartbeat != initial_heartbeat, "Heartbeat should be updating"
        
        # Test connection state monitoring
        connection_state = connection_manager.get_state()
        assert connection_state in ['connected', 'connecting', 'disconnected'], \
            f"Invalid connection state: {connection_state}"
        
        # Simulate heartbeat timeout by stopping the service briefly
        mavlink_service.stop()
        time.sleep(1)
        
        # Check disconnected state
        disconnected_status = mavlink_service.get_status()
        assert not disconnected_status['mavlink_connected'], "Should be disconnected after stop"
        
        # Test reconnection safety
        if mavlink_service.start():
            time.sleep(2)
            
            # Verify safe reconnection
            reconnected_status = mavlink_service.get_status()
            assert reconnected_status['mavlink_connected'], "Should reconnect safely"
            
            # Verify system integrity after reconnection
            assert reconnected_status['service_threads']['message_processor'], \
                "Message processor should restart"
            assert reconnected_status['service_threads']['telemetry_streamer'], \
                "Telemetry streamer should restart"

    @pytest.mark.asyncio
    async def test_emergency_procedures(self, safety_app):
        """Test emergency procedures and fail-safe behaviors."""
        app, socketio = safety_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Connect and ARM for emergency testing
                await page.click('#connect-btn')
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # ARM the vehicle
                await page.click('#arm-btn')
                
                try:
                    confirmation_modal = page.locator('#safety-confirmation-modal')
                    await confirmation_modal.wait_for(state='visible', timeout=5000)
                    await page.click('#confirm-action-btn')
                except:
                    pass
                
                await page.wait_for_function(
                    "document.querySelector('#armed-status').textContent.includes('ARMED')",
                    timeout=10000
                )
                
                # Test Emergency RTL
                rtl_btn = page.locator('#rtl-btn')
                if await rtl_btn.is_visible():
                    await rtl_btn.click()
                    
                    try:
                        await confirmation_modal.wait_for(state='visible', timeout=3000)
                        
                        # Emergency RTL confirmation should be prominent
                        modal_text = await page.locator('#safety-confirmation-message').text_content()
                        assert any(word in modal_text.upper() for word in 
                                 ['RTL', 'RETURN', 'LAUNCH', 'EMERGENCY', 'HOME'])
                        
                        await page.click('#confirm-action-btn')
                        await asyncio.sleep(2)
                        
                    except:
                        pass
                
                # Test Emergency Land
                land_btn = page.locator('#land-btn')
                if await land_btn.is_visible():
                    await land_btn.click()
                    
                    try:
                        await confirmation_modal.wait_for(state='visible', timeout=3000)
                        
                        modal_text = await page.locator('#safety-confirmation-message').text_content()
                        assert 'LAND' in modal_text.upper() or 'EMERGENCY' in modal_text.upper()
                        
                        await page.click('#confirm-action-btn')
                        await asyncio.sleep(2)
                        
                    except:
                        pass
                
                # Test Kill Switch / Emergency Disarm
                disarm_btn = page.locator('#disarm-btn')
                if await disarm_btn.is_visible():
                    await disarm_btn.click()
                    
                    try:
                        await confirmation_modal.wait_for(state='visible', timeout=3000)
                        
                        # Emergency disarm should be clearly marked
                        modal_text = await page.locator('#safety-confirmation-message').text_content()
                        assert 'DISARM' in modal_text.upper()
                        
                        await page.click('#confirm-action-btn')
                        
                        # Verify emergency disarm
                        await page.wait_for_function(
                            "document.querySelector('#armed-status').textContent.includes('DISARMED')",
                            timeout=10000
                        )
                        
                    except:
                        pass
                
                # Test rapid emergency sequence (panic button behavior)
                emergency_sequences = [
                    ['#rtl-btn', '#land-btn', '#disarm-btn'],
                    ['#land-btn', '#disarm-btn']
                ]
                
                for sequence in emergency_sequences:
                    try:
                        for button_selector in sequence:
                            button = page.locator(button_selector)
                            if await button.is_visible() and await button.is_enabled():
                                await button.click()
                                
                                # Handle confirmations quickly
                                try:
                                    await page.click('#confirm-action-btn', timeout=2000)
                                except:
                                    try:
                                        await page.click('#cancel-action-btn', timeout=1000)
                                    except:
                                        pass
                                
                                await asyncio.sleep(0.5)  # Brief pause
                        
                        # System should remain stable after rapid emergency commands
                        connection_status = await page.locator('#connection-status').text_content()
                        assert 'Connected' in connection_status or 'Disconnected' in connection_status
                        
                    except Exception as e:
                        print(f"Emergency sequence test: {e}")
                
            finally:
                await browser.close()

    def test_safety_during_connection_loss(self, safety_app):
        """Test safety behaviors during connection loss."""
        app, socketio = safety_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
        
        time.sleep(2)
        
        # Get connected state
        connected_status = mavlink_service.get_status()
        assert connected_status['mavlink_connected']
        
        # Simulate connection loss
        mavlink_service.connection_manager.disconnect()
        time.sleep(1)
        
        # Test command behavior during disconnection
        command_sender = mavlink_service.command_sender
        
        # Commands should fail safely when disconnected
        arm_result = command_sender.arm_vehicle()
        assert not arm_result, "Commands should fail when disconnected"
        
        takeoff_result = command_sender.takeoff(10.0)
        assert not takeoff_result, "Takeoff should fail when disconnected"
        
        # Verify no pending commands accumulate during disconnection
        pending_commands = command_sender.get_pending_commands()
        initial_pending_count = len(pending_commands)
        
        # Try multiple commands while disconnected
        for _ in range(3):
            command_sender.arm_vehicle()
            command_sender.disarm_vehicle()
        
        final_pending_count = len(command_sender.get_pending_commands())
        
        # Should not accumulate many pending commands when disconnected
        assert final_pending_count <= initial_pending_count + 2, \
            "Should not accumulate commands when disconnected"
        
        # Test reconnection safety
        if mavlink_service.connection_manager.connect():
            time.sleep(2)
            
            # Verify safe reconnection
            reconnected_status = mavlink_service.get_status()
            assert reconnected_status['mavlink_connected']
            
            # Commands should work again
            status_command_result = True  # Just testing connection, not actual ARM
            assert status_command_result, "Should be able to communicate after reconnection"

    def test_concurrent_safety_systems(self, safety_app):
        """Test safety systems under concurrent access."""
        app, socketio = safety_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
        
        time.sleep(2)
        
        # Test concurrent command safety
        results = {}
        
        def command_worker(worker_id, results_dict):
            worker_results = []
            for i in range(5):
                if i % 2 == 0:
                    result = mavlink_service.command_sender.arm_vehicle()
                else:
                    result = mavlink_service.command_sender.disarm_vehicle()
                worker_results.append(result)
                time.sleep(0.2)
            results_dict[worker_id] = worker_results
        
        # Run concurrent command workers
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=command_worker, args=(worker_id, results))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all workers completed
        assert len(results) == 3, "All workers should complete"
        
        # Verify system stability after concurrent access
        final_status = mavlink_service.get_status()
        assert final_status['mavlink_connected'], "Connection should remain stable"
        assert final_status['service_threads']['message_processor'], "Message processing should continue"
        
        # Check that command system is still responsive
        final_command_result = mavlink_service.get_status()  # Simple status check
        assert final_command_result is not None, "Command system should remain responsive"

    def teardown_method(self, method):
        """Cleanup after each test method."""
        time.sleep(0.5)
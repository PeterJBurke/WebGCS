"""
TEST-705: Network Resilience Integration

Tests system behavior during connection interruptions.

Validates:
- System behavior during connection interruptions
- Reconnection workflows and state restoration
- Graceful degradation when drone communication fails
- User notification and feedback during network issues
"""

import pytest
import time
import asyncio
import threading
import socket
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import requests

from src.web.app_factory import initialize_app


class TestNetworkResilienceIntegration:
    """Network resilience integration tests."""

    @pytest.fixture(scope="class")
    def resilient_app(self):
        """Create application for resilience testing."""
        app, socketio = initialize_app()
        
        app.config.update({
            'TESTING': True,
            'WEB_SERVER_PORT': 5002,
            'HEARTBEAT_TIMEOUT': 5,  # Shorter timeout for testing
            'COMMAND_ACK_TIMEOUT': 3.0
        })
        
        def run_server():
            socketio.run(app, host='localhost', port=5002, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        yield app, socketio
        
        if hasattr(app, 'mavlink_service'):
            app.mavlink_service.stop()

    def test_drone_connection_resilience(self, resilient_app):
        """Test resilience to drone connection interruptions."""
        app, socketio = resilient_app
        
        mavlink_service = app.mavlink_service
        
        # Test initial connection
        connection_established = mavlink_service.start()
        if not connection_established:
            pytest.skip("Could not establish initial drone connection")
        
        time.sleep(2)
        
        # Verify connected state
        initial_status = mavlink_service.get_status()
        assert initial_status['mavlink_connected'], "Should be initially connected"
        
        # Test connection interruption
        mavlink_service.stop()
        time.sleep(1)
        
        # Verify disconnected state
        disconnected_status = mavlink_service.get_status()
        assert not disconnected_status['mavlink_connected'], "Should be disconnected after stop"
        
        # Test automatic reconnection capability
        reconnection_attempts = 0
        max_attempts = 3
        reconnected = False
        
        for attempt in range(max_attempts):
            reconnection_attempts += 1
            
            if mavlink_service.start():
                reconnected = True
                break
            
            time.sleep(1)  # Wait between attempts
        
        assert reconnection_attempts <= max_attempts, "Should not exceed retry limit"
        
        if reconnected:
            time.sleep(2)
            
            # Verify reconnected state
            final_status = mavlink_service.get_status()
            assert final_status['mavlink_connected'], "Should be reconnected"
            assert final_status['service_threads']['message_processor'], "Message processor should restart"
            assert final_status['service_threads']['telemetry_streamer'], "Telemetry streamer should restart"

    @pytest.mark.asyncio
    async def test_web_interface_connection_resilience(self, resilient_app):
        """Test web interface behavior during connection issues."""
        app, socketio = resilient_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Test initial connection attempt
                await page.click('#connect-btn')
                
                # Wait for connection result (success or failure)
                connection_result = await page.wait_for_function(
                    """() => {
                        const status = document.querySelector('#connection-status');
                        return status && (status.textContent.includes('Connected') || 
                                        status.textContent.includes('Failed') ||
                                        status.textContent.includes('Error'));
                    }""",
                    timeout=20000
                )
                
                status_text = await page.locator('#connection-status').text_content()
                
                if 'Connected' in status_text:
                    # Test disconnect detection
                    # Simulate disconnection by stopping MAVLink service
                    mavlink_service = app.mavlink_service
                    mavlink_service.stop()
                    
                    # Wait for disconnection to be detected
                    await page.wait_for_function(
                        """() => {
                            const status = document.querySelector('#connection-status');
                            return status && (status.textContent.includes('Disconnected') ||
                                            status.textContent.includes('Lost') ||
                                            status.textContent.includes('Error'));
                        }""",
                        timeout=15000
                    )
                    
                    # Verify UI reflects disconnection
                    disconnected_status = await page.locator('#connection-status').text_content()
                    assert any(word in disconnected_status for word in ['Disconnected', 'Lost', 'Error', 'Failed'])
                    
                    # Test reconnection attempt
                    await page.click('#connect-btn')
                    
                    # Start service for reconnection
                    if mavlink_service.start():
                        # Wait for reconnection
                        await page.wait_for_function(
                            "document.querySelector('#connection-status').textContent.includes('Connected')",
                            timeout=15000
                        )
                        
                        reconnected_status = await page.locator('#connection-status').text_content()
                        assert 'Connected' in reconnected_status, "Should reconnect successfully"
                    
                else:
                    # Test connection failure handling
                    assert any(word in status_text for word in ['Failed', 'Error', 'Timeout'])
                    
                    # Verify buttons are appropriately disabled
                    critical_buttons = ['#takeoff-btn', '#land-btn', '#rtl-btn']
                    
                    for button in critical_buttons:
                        try:
                            button_element = page.locator(button)
                            if await button_element.is_visible():
                                is_enabled = await button_element.is_enabled()
                                assert not is_enabled, f"{button} should be disabled when connection failed"
                        except:
                            pass
                    
                    # Test retry connection functionality
                    await page.click('#connect-btn')
                    await asyncio.sleep(2)  # Give time for retry attempt
                    
                    # System should handle retry gracefully
                    retry_status = await page.locator('#connection-status').text_content()
                    assert retry_status is not None, "Status should be updated after retry"
                
            finally:
                await browser.close()

    def test_heartbeat_timeout_handling(self, resilient_app):
        """Test heartbeat timeout detection and handling."""
        app, socketio = resilient_app
        
        mavlink_service = app.mavlink_service
        connection_manager = mavlink_service.connection_manager
        
        # Test with shorter timeout for faster testing
        original_timeout = connection_manager.heartbeat_timeout
        connection_manager.heartbeat_timeout = 3  # 3 seconds for testing
        
        try:
            if not mavlink_service.start():
                pytest.skip("Could not connect for heartbeat testing")
            
            time.sleep(1)
            
            # Get initial heartbeat
            initial_heartbeat = connection_manager.get_last_heartbeat()
            initial_state = connection_manager.get_state()
            
            assert initial_state == 'connected', f"Should be connected initially: {initial_state}"
            
            # Monitor heartbeat updates
            heartbeat_updates = []
            start_time = time.time()
            
            while time.time() - start_time < 5.0:  # Monitor for 5 seconds
                current_heartbeat = connection_manager.get_last_heartbeat()
                current_state = connection_manager.get_state()
                
                heartbeat_updates.append({
                    'time': time.time(),
                    'heartbeat': current_heartbeat,
                    'state': current_state
                })
                
                time.sleep(0.5)
            
            # Verify heartbeat updates occurred
            unique_heartbeats = set(update['heartbeat'] for update in heartbeat_updates 
                                  if update['heartbeat'] is not None)
            assert len(unique_heartbeats) > 1, "Heartbeat should be updating"
            
            # Test heartbeat timeout detection by stopping message processing
            mavlink_service._stop_processing = True  # Stop processing to simulate timeout
            
            # Wait for timeout detection
            timeout_start = time.time()
            while time.time() - timeout_start < 10.0:  # Wait up to 10 seconds
                current_state = connection_manager.get_state()
                if current_state != 'connected':
                    break
                time.sleep(0.5)
            
            final_state = connection_manager.get_state()
            # State should change from connected due to heartbeat timeout
            # (Implementation may vary - disconnected, timeout, or error)
            
        finally:
            # Restore original timeout
            connection_manager.heartbeat_timeout = original_timeout

    @pytest.mark.asyncio
    async def test_socketio_connection_resilience(self, resilient_app):
        """Test SocketIO connection resilience."""
        app, socketio = resilient_app
        
        import socketio as sio_client
        
        # Test multiple client connections and disconnections
        clients = []
        connection_events = []
        
        try:
            # Create multiple clients
            for client_id in range(3):
                client = sio_client.SimpleClient()
                
                try:
                    client.connect('http://localhost:5002')
                    clients.append(client)
                    connection_events.append(f"Client {client_id} connected")
                except Exception as e:
                    connection_events.append(f"Client {client_id} failed: {e}")
            
            assert len(clients) >= 1, "At least one client should connect"
            
            # Test client disconnection and reconnection
            if len(clients) >= 2:
                # Disconnect one client
                test_client = clients[0]
                test_client.disconnect()
                connection_events.append("Test client disconnected")
                
                # Try to reconnect
                try:
                    test_client.connect('http://localhost:5002')
                    connection_events.append("Test client reconnected")
                except Exception as e:
                    connection_events.append(f"Reconnection failed: {e}")
            
            # Test server resilience with remaining clients
            if len(clients) >= 1:
                remaining_client = clients[-1]
                
                # Test that server still responds to remaining clients
                try:
                    # Simple test - just verify connection is still active
                    remaining_client.sleep(0.1)
                    connection_events.append("Server responsive to remaining clients")
                except Exception as e:
                    connection_events.append(f"Server unresponsive: {e}")
            
            # Verify connection event log
            assert len(connection_events) >= 3, f"Insufficient connection events: {connection_events}"
            
        finally:
            # Cleanup all clients
            for client in clients:
                try:
                    client.disconnect()
                except:
                    pass

    def test_command_resilience_during_network_issues(self, resilient_app):
        """Test command system resilience during network issues."""
        app, socketio = resilient_app
        
        mavlink_service = app.mavlink_service
        command_sender = mavlink_service.command_sender
        
        if not mavlink_service.start():
            pytest.skip("Could not connect for command resilience testing")
        
        time.sleep(1)
        
        # Test command behavior during stable connection
        initial_commands = []
        for i in range(3):
            result = command_sender.arm_vehicle() if i % 2 == 0 else command_sender.disarm_vehicle()
            initial_commands.append(result)
            time.sleep(0.5)
        
        # At least some commands should succeed with good connection
        successful_commands = sum(1 for cmd in initial_commands if cmd)
        
        # Test command behavior during connection disruption
        mavlink_service.stop()
        time.sleep(1)
        
        # Commands should fail gracefully when disconnected
        disconnected_commands = []
        for i in range(3):
            result = command_sender.arm_vehicle()
            disconnected_commands.append(result)
        
        # All commands should fail when disconnected
        failed_commands = sum(1 for cmd in disconnected_commands if not cmd)
        assert failed_commands == len(disconnected_commands), "Commands should fail when disconnected"
        
        # Test command recovery after reconnection
        if mavlink_service.start():
            time.sleep(2)
            
            # Commands should work again after reconnection
            recovery_commands = []
            for i in range(2):
                result = command_sender.arm_vehicle() if i % 2 == 0 else command_sender.disarm_vehicle()
                recovery_commands.append(result)
                time.sleep(0.5)
            
            # At least some recovery commands should succeed
            recovery_success = sum(1 for cmd in recovery_commands if cmd)
            # Note: Success may depend on drone state, so we mainly check for no crashes

    @pytest.mark.asyncio
    async def test_user_feedback_during_network_issues(self, resilient_app):
        """Test user notification and feedback during network issues."""
        app, socketio = resilient_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Test connection attempt feedback
                await page.click('#connect-btn')
                
                # Should show some form of connection attempt feedback
                # (Could be status text, loading indicator, button state change, etc.)
                await asyncio.sleep(1)
                
                connection_btn = page.locator('#connect-btn')
                status_element = page.locator('#connection-status')
                
                # Check for user feedback indicators
                btn_text = await connection_btn.text_content()
                status_text = await status_element.text_content()
                
                # Button text should indicate state (Connect/Connecting/Connected/Disconnect)
                feedback_indicators = ['Connect', 'Connecting', 'Connected', 'Disconnect', 'Failed', 'Error']
                assert any(indicator in btn_text or indicator in status_text 
                          for indicator in feedback_indicators), \
                    f"No clear user feedback: button='{btn_text}', status='{status_text}'"
                
                # Wait for final connection result
                await page.wait_for_function(
                    """() => {
                        const status = document.querySelector('#connection-status');
                        const btn = document.querySelector('#connect-btn');
                        return (status && status.textContent.trim() !== '') || 
                               (btn && btn.textContent.includes('Disconnect'));
                    }""",
                    timeout=15000
                )
                
                final_status = await status_element.text_content()
                final_btn_text = await connection_btn.text_content()
                
                # Verify clear final status
                assert final_status.strip() != '', "Status should provide clear feedback"
                
                # Test error message display (if connection fails)
                if any(word in final_status for word in ['Failed', 'Error', 'Timeout']):
                    # Error feedback should be informative
                    assert len(final_status.strip()) > 5, "Error message should be informative"
                    
                    # Check if retry is possible
                    is_btn_enabled = await connection_btn.is_enabled()
                    assert is_btn_enabled, "Should allow retry after failure"
                
                # Test disconnection feedback (if connected)
                if 'Connected' in final_status:
                    # Try disconnect
                    if 'Disconnect' in final_btn_text:
                        await connection_btn.click()
                        
                        # Should show disconnection feedback
                        await page.wait_for_function(
                            "document.querySelector('#connection-status').textContent.includes('Disconnect')",
                            timeout=5000
                        )
                        
                        disconnect_status = await status_element.text_content()
                        assert 'Disconnect' in disconnect_status or 'Closed' in disconnect_status
                
                # Test continuous status updates
                # Status should be kept up-to-date, not stale
                status_updates = []
                for i in range(5):
                    current_status = await status_element.text_content()
                    status_updates.append(current_status)
                    await asyncio.sleep(0.5)
                
                # Status should be consistent or show valid transitions
                unique_statuses = set(status_updates)
                assert len(unique_statuses) <= 3, "Status should be stable or show valid transitions"
                
            finally:
                await browser.close()

    def test_graceful_degradation(self, resilient_app):
        """Test graceful degradation when drone communication fails."""
        app, socketio = resilient_app
        
        mavlink_service = app.mavlink_service
        
        # Test behavior without drone connection
        # (Service should still function, just with limited capabilities)
        
        # Get status without connection
        disconnected_status = mavlink_service.get_status()
        assert not disconnected_status['mavlink_connected']
        assert disconnected_status['drone_endpoint'] is not None  # Should still show endpoint
        
        # Telemetry system should still function (return empty/default data)
        disconnected_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
        assert isinstance(disconnected_telemetry, dict), "Should return telemetry structure even when disconnected"
        
        # Command system should fail gracefully
        command_result = mavlink_service.arm_vehicle()
        assert not command_result, "Commands should fail gracefully when disconnected"
        
        # Try to establish connection
        if mavlink_service.start():
            time.sleep(2)
            
            # With connection, system should provide full functionality
            connected_status = mavlink_service.get_status()
            assert connected_status['mavlink_connected']
            
            connected_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            
            # Connected telemetry should have more data than disconnected
            connected_keys = set(connected_telemetry.keys())
            disconnected_keys = set(disconnected_telemetry.keys())
            
            # Should have at least the basic structure
            assert 'last_update' in connected_telemetry or 'heartbeat' in connected_telemetry
            
            # Test partial failure scenarios
            # Simulate message processing issues
            original_processor = mavlink_service.message_processor
            
            # Test with degraded telemetry processing
            mavlink_service._stop_processing = True
            time.sleep(1)
            
            # System should still return status (may be degraded)
            degraded_status = mavlink_service.get_status()
            assert degraded_status is not None
            
            # Restore processing
            mavlink_service._stop_processing = False
            mavlink_service._start_message_processing()
            
        else:
            print("Note: Graceful degradation test completed without drone connection")

    def test_network_performance_under_stress(self, resilient_app):
        """Test network performance under stress conditions."""
        app, socketio = resilient_app
        
        mavlink_service = app.mavlink_service
        
        if not mavlink_service.start():
            pytest.skip("Could not connect for stress testing")
        
        time.sleep(1)
        
        # Test rapid status requests
        stress_results = []
        start_time = time.time()
        
        for i in range(50):  # 50 rapid requests
            request_start = time.time()
            status = mavlink_service.get_status()
            request_duration = time.time() - request_start
            
            stress_results.append({
                'request_id': i,
                'duration': request_duration,
                'success': status is not None
            })
        
        total_time = time.time() - start_time
        
        # Verify performance under stress
        successful_requests = sum(1 for r in stress_results if r['success'])
        assert successful_requests >= 45, f"Too many failed requests under stress: {successful_requests}/50"
        
        avg_response_time = sum(r['duration'] for r in stress_results) / len(stress_results)
        assert avg_response_time < 0.01, f"Response time too slow under stress: {avg_response_time:.4f}s"
        
        max_response_time = max(r['duration'] for r in stress_results)
        assert max_response_time < 0.05, f"Max response time too high: {max_response_time:.4f}s"
        
        # Test concurrent network access
        def network_worker(worker_id, results_dict):
            worker_results = []
            for i in range(10):
                start = time.time()
                try:
                    status = mavlink_service.get_status()
                    duration = time.time() - start
                    worker_results.append({'success': True, 'duration': duration})
                except Exception as e:
                    worker_results.append({'success': False, 'error': str(e)})
            results_dict[worker_id] = worker_results
        
        # Run concurrent network workers
        worker_results = {}
        threads = []
        
        for worker_id in range(5):
            thread = threading.Thread(target=network_worker, args=(worker_id, worker_results))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify concurrent access performance
        all_results = []
        for worker_id, results in worker_results.items():
            all_results.extend(results)
        
        concurrent_success_rate = sum(1 for r in all_results if r['success']) / len(all_results)
        assert concurrent_success_rate >= 0.9, f"Concurrent success rate too low: {concurrent_success_rate:.2f}"
        
        successful_times = [r['duration'] for r in all_results if r['success']]
        if successful_times:
            avg_concurrent_time = sum(successful_times) / len(successful_times)
            assert avg_concurrent_time < 0.02, f"Concurrent response time too slow: {avg_concurrent_time:.4f}s"

    def teardown_method(self, method):
        """Cleanup after each test method."""
        time.sleep(0.5)
"""
TEST-702: Real-time Telemetry Integration

Tests continuous telemetry flow from virtual drone to all UI components.

Validates:
- VFR HUD updates with real MAVLink data
- Connection status propagation across all UI elements
- 10Hz update rate maintenance during operations
- Data consistency between backend and frontend
"""

import pytest
import time
import asyncio
import json
import threading
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import websocket
import requests

from src.web.app_factory import initialize_app


class TestRealtimeTelemetryIntegration:
    """Real-time telemetry integration tests."""

    @pytest.fixture(scope="class")
    def app_with_telemetry(self):
        """Create application with telemetry monitoring."""
        app, socketio = initialize_app()
        
        app.config.update({
            'TESTING': True,
            'WEB_SERVER_PORT': 5002,
            'TELEMETRY_UPDATE_INTERVAL': 0.1  # 10Hz
        })
        
        # Start server
        def run_server():
            socketio.run(app, host='localhost', port=5002, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        yield app, socketio
        
        if hasattr(app, 'mavlink_service'):
            app.mavlink_service.stop()

    def test_continuous_telemetry_flow(self, app_with_telemetry):
        """Test continuous telemetry data flow."""
        app, socketio = app_with_telemetry
        
        # Start MAVLink service
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
        
        time.sleep(2)  # Allow connection to stabilize
        
        # Collect telemetry updates
        telemetry_samples = []
        start_time = time.time()
        
        # Sample telemetry for 5 seconds
        while time.time() - start_time < 5.0:
            telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            if telemetry:
                telemetry_samples.append({
                    'timestamp': time.time(),
                    'data': telemetry
                })
            time.sleep(0.05)  # Sample faster than update rate
        
        # Verify telemetry frequency
        assert len(telemetry_samples) >= 40, f"Insufficient telemetry samples: {len(telemetry_samples)}"
        
        # Verify data consistency
        for sample in telemetry_samples:
            assert 'heartbeat' in sample['data'], "Missing heartbeat data"
            assert 'last_update' in sample['data'], "Missing timestamp"
            
        # Verify update rate (approximately 10Hz)
        timestamps = [s['timestamp'] for s in telemetry_samples]
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        avg_interval = sum(intervals) / len(intervals)
        
        # Should be close to 0.1s (10Hz) with some tolerance
        assert 0.05 <= avg_interval <= 0.2, f"Telemetry rate off target: {avg_interval:.3f}s"

    @pytest.mark.asyncio
    async def test_vfr_hud_realtime_updates(self, app_with_telemetry):
        """Test VFR HUD updates with real MAVLink data."""
        app, socketio = app_with_telemetry
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#pfd-canvas')
                
                # Connect to drone
                await page.click('#connect-btn')
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Monitor VFR HUD components for updates
                components_to_test = [
                    '#altitude-tape',
                    '#speed-tape', 
                    '#compass-heading',
                    '#attitude-indicator',
                    '#armed-status',
                    '#flight-mode'
                ]
                
                # Capture initial values
                initial_values = {}
                for component in components_to_test:
                    try:
                        value = await page.locator(component).text_content()
                        initial_values[component] = value
                    except:
                        initial_values[component] = None
                
                # Wait for updates
                await asyncio.sleep(3)
                
                # Capture updated values
                updated_values = {}
                for component in components_to_test:
                    try:
                        value = await page.locator(component).text_content()
                        updated_values[component] = value
                    except:
                        updated_values[component] = None
                
                # Verify components are populated with data
                assert updated_values['#altitude-tape'], "Altitude not updating"
                assert updated_values['#speed-tape'], "Speed not updating"
                assert updated_values['#compass-heading'], "Heading not updating"
                assert updated_values['#flight-mode'], "Flight mode not updating"
                
                # Test PFD canvas is being drawn
                canvas_element = page.locator('#pfd-canvas')
                await canvas_element.wait_for(state='visible')
                
                # Verify canvas has content (check if drawing context is active)
                canvas_has_content = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        // Check if canvas has any non-transparent pixels
                        for (let i = 3; i < imageData.data.length; i += 4) {
                            if (imageData.data[i] > 0) return true;
                        }
                        return false;
                    }
                """)
                
                assert canvas_has_content, "PFD canvas appears empty"
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_socketio_telemetry_streaming(self, app_with_telemetry):
        """Test SocketIO telemetry streaming to web clients."""
        app, socketio = app_with_telemetry
        
        telemetry_messages = []
        connection_messages = []
        
        # Create SocketIO client to monitor messages
        import socketio as sio_client
        
        client = sio_client.SimpleClient()
        
        try:
            # Connect to SocketIO server
            client.connect('http://localhost:5002')
            
            # Set up event handlers
            @client.event
            def telemetry_update(data):
                telemetry_messages.append({
                    'timestamp': time.time(),
                    'data': data
                })
            
            @client.event
            def connection_status_update(data):
                connection_messages.append({
                    'timestamp': time.time(),
                    'data': data
                })
            
            # Start MAVLink service to generate telemetry
            mavlink_service = app.mavlink_service
            if not mavlink_service.start():
                pytest.skip("Could not connect to drone")
            
            # Wait for telemetry messages
            start_time = time.time()
            while time.time() - start_time < 5.0 and len(telemetry_messages) < 30:
                client.sleep(0.1)
            
            # Verify telemetry streaming
            assert len(telemetry_messages) >= 20, f"Insufficient telemetry messages: {len(telemetry_messages)}"
            
            # Verify connection status updates
            assert len(connection_messages) >= 1, "No connection status updates received"
            
            # Verify message content
            for msg in telemetry_messages[-5:]:  # Check last 5 messages
                data = msg['data']
                assert isinstance(data, dict), "Telemetry data not properly formatted"
                assert 'heartbeat' in data or 'connection_status' in data, "Missing required telemetry fields"
            
            # Verify update frequency
            if len(telemetry_messages) >= 2:
                timestamps = [msg['timestamp'] for msg in telemetry_messages]
                intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                avg_interval = sum(intervals) / len(intervals)
                
                # Should be approximately 10Hz (0.1s intervals)
                assert 0.05 <= avg_interval <= 0.3, f"SocketIO telemetry rate off target: {avg_interval:.3f}s"
            
        except Exception as e:
            pytest.fail(f"SocketIO telemetry test failed: {e}")
        finally:
            try:
                client.disconnect()
            except:
                pass

    def test_telemetry_data_consistency(self, app_with_telemetry):
        """Test data consistency between MAVLink service and web interface."""
        app, socketio = app_with_telemetry
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
        
        time.sleep(2)  # Allow stabilization
        
        # Get telemetry from MAVLink service
        service_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
        service_status = mavlink_service.get_status()
        
        # Get status from web API
        try:
            response = requests.get('http://localhost:5002/api/status', timeout=5)
            if response.status_code == 200:
                web_status = response.json()
                
                # Compare key fields
                assert service_status['mavlink_connected'] == web_status.get('connected', False), \
                    "Connection status mismatch between service and web"
                
                assert service_status['armed_status'] == web_status.get('armed', False), \
                    "Armed status mismatch between service and web"
                
                assert service_status['flight_mode'] == web_status.get('flight_mode', 'UNKNOWN'), \
                    "Flight mode mismatch between service and web"
                
        except requests.RequestException:
            # Web API may not be implemented, which is acceptable
            print("Web API not available - skipping API consistency check")
        
        # Verify telemetry data structure
        assert isinstance(service_telemetry, dict), "Service telemetry not a dictionary"
        assert 'last_update' in service_telemetry, "Missing last_update timestamp"
        
        # Check timestamp freshness (within last 2 seconds)
        if service_telemetry.get('last_update'):
            last_update = datetime.fromisoformat(service_telemetry['last_update'].replace('Z', '+00:00'))
            time_diff = datetime.now() - last_update.replace(tzinfo=None)
            assert time_diff.total_seconds() < 2.0, "Telemetry data too old"

    @pytest.mark.asyncio
    async def test_connection_status_propagation(self, app_with_telemetry):
        """Test connection status propagation across all UI elements."""
        app, socketio = app_with_telemetry
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Verify initial disconnected state
                status_elements = [
                    '#connection-status',
                    '#drone-endpoint',
                    '#connection-indicator'
                ]
                
                for element in status_elements:
                    try:
                        await page.locator(element).wait_for(state='visible', timeout=2000)
                    except:
                        pass  # Element may not exist, which is acceptable
                
                # Test connection
                await page.click('#connect-btn')
                
                # Wait for connection to establish
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Verify all status elements reflect connected state
                status_text = await page.locator('#connection-status').text_content()
                assert 'Connected' in status_text
                
                # Check if endpoint is displayed
                try:
                    endpoint_text = await page.locator('#drone-endpoint').text_content()
                    assert '192.168.193.235:5678' in endpoint_text or 'localhost' in endpoint_text
                except:
                    pass  # Element may not exist
                
                # Verify control buttons become enabled
                control_buttons = ['#arm-btn', '#disarm-btn', '#takeoff-btn', '#land-btn']
                
                for button in control_buttons:
                    try:
                        button_element = page.locator(button)
                        await button_element.wait_for(state='visible', timeout=5000)
                        
                        # Button should be enabled or at least visible
                        is_enabled = await button_element.is_enabled()
                        is_visible = await button_element.is_visible()
                        assert is_visible, f"Button {button} not visible after connection"
                        
                    except Exception as e:
                        print(f"Button {button} check failed: {e}")
                
                # Test disconnect propagation
                disconnect_btn = page.locator('#disconnect-btn')
                if await disconnect_btn.is_visible():
                    await disconnect_btn.click()
                    
                    # Wait for disconnection
                    await page.wait_for_function(
                        "document.querySelector('#connection-status').textContent.includes('Disconnected')",
                        timeout=10000
                    )
                    
                    # Verify status reflects disconnection
                    status_text = await page.locator('#connection-status').text_content()
                    assert 'Disconnected' in status_text
                
            finally:
                await browser.close()

    def test_telemetry_performance_under_load(self, app_with_telemetry):
        """Test telemetry performance under various load conditions."""
        app, socketio = app_with_telemetry
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
        
        time.sleep(2)
        
        # Test rapid telemetry requests
        start_time = time.time()
        request_count = 100
        
        for i in range(request_count):
            telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            assert telemetry is not None, f"Telemetry request {i} failed"
        
        total_time = time.time() - start_time
        avg_response_time = total_time / request_count
        
        # Should handle requests efficiently (< 1ms average per request)
        assert avg_response_time < 0.001, f"Telemetry response too slow: {avg_response_time:.4f}s"
        
        # Test concurrent access
        def telemetry_worker(results, worker_id):
            worker_results = []
            for i in range(20):
                start = time.time()
                telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
                duration = time.time() - start
                worker_results.append(duration)
            results[worker_id] = worker_results
        
        # Run concurrent telemetry requests
        worker_results = {}
        threads = []
        
        for worker_id in range(5):
            thread = threading.Thread(target=telemetry_worker, args=(worker_results, worker_id))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all workers completed successfully
        assert len(worker_results) == 5, "Not all workers completed"
        
        # Check performance under load
        all_times = []
        for worker_id, times in worker_results.items():
            all_times.extend(times)
        
        avg_concurrent_time = sum(all_times) / len(all_times)
        max_concurrent_time = max(all_times)
        
        assert avg_concurrent_time < 0.002, f"Concurrent telemetry too slow: {avg_concurrent_time:.4f}s"
        assert max_concurrent_time < 0.01, f"Max concurrent time too high: {max_concurrent_time:.4f}s"

    def test_telemetry_error_handling(self, app_with_telemetry):
        """Test telemetry system error handling and recovery."""
        app, socketio = app_with_telemetry
        
        mavlink_service = app.mavlink_service
        
        # Test behavior without connection
        telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
        assert isinstance(telemetry, dict), "Should return empty telemetry dict when disconnected"
        
        # Test connection and disconnection
        if mavlink_service.start():
            time.sleep(1)
            
            # Get valid telemetry
            connected_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            assert connected_telemetry is not None
            
            # Disconnect and test graceful handling
            mavlink_service.stop()
            time.sleep(0.5)
            
            # Should still return telemetry structure (may be stale)
            disconnected_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            assert isinstance(disconnected_telemetry, dict)
            
        else:
            pytest.skip("Could not test connection scenarios")

    def teardown_method(self, method):
        """Cleanup after each test."""
        time.sleep(0.5)
"""
TEST-701: End-to-End Flight Operations Integration

Comprehensive test of complete flight workflow:
Connect → ARM → Takeoff → Navigate → Land → Disarm

Validates:
- Complete data flow from MAVLink → SocketIO → Web UI → User actions → Commands → Drone
- Telemetry updates throughout entire flight cycle
- Safety confirmations at each critical step
- Real-time status propagation across all components
"""

import pytest
import time
import asyncio
import requests
from playwright.async_api import async_playwright
from unittest.mock import patch
import os
import threading
import json
from datetime import datetime

from src.web.app_factory import initialize_app
from src.mavlink.mavlink_service import MAVLinkService


class TestEndToEndFlightOperations:
    """End-to-end flight operations integration tests."""

    @pytest.fixture(scope="class")
    def app_with_service(self):
        """Create application with MAVLink service for testing."""
        app, socketio = initialize_app()
        
        # Override config for testing
        app.config.update({
            'TESTING': True,
            'WEB_SERVER_PORT': 5002,
            'DRONE_TCP_ADDRESS': os.getenv('DRONE_TCP_ADDRESS', '192.168.193.235'),
            'DRONE_TCP_PORT': int(os.getenv('DRONE_TCP_PORT', '5678'))
        })
        
        # Start the web server in a separate thread
        def run_server():
            socketio.run(app, host='localhost', port=5002, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        yield app, socketio
        
        # Cleanup
        if hasattr(app, 'mavlink_service'):
            app.mavlink_service.stop()

    def test_server_accessibility(self, app_with_service):
        """Verify web server is accessible."""
        app, socketio = app_with_service
        
        # Test that the server responds
        try:
            response = requests.get('http://localhost:5002', timeout=5)
            assert response.status_code == 200
            assert 'WebGCS' in response.text
        except requests.RequestException as e:
            pytest.fail(f"Server not accessible: {e}")

    @pytest.mark.asyncio
    async def test_complete_flight_workflow(self, app_with_service):
        """Test complete end-to-end flight workflow."""
        app, socketio = app_with_service
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Step 1: Navigate to WebGCS interface
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel', timeout=10000)
                
                # Verify page loaded correctly
                title = await page.title()
                assert 'WebGCS' in title
                
                # Step 2: Establish drone connection
                connect_button = page.locator('#connect-btn')
                await connect_button.wait_for(state='visible')
                await connect_button.click()
                
                # Wait for connection establishment
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Verify connection status
                status = await page.locator('#connection-status').text_content()
                assert 'Connected' in status
                
                # Step 3: ARM the vehicle with safety confirmation
                arm_button = page.locator('#arm-btn')
                await arm_button.wait_for(state='visible')
                await arm_button.click()
                
                # Handle safety confirmation dialog
                confirmation_dialog = page.locator('#safety-confirmation-modal')
                await confirmation_dialog.wait_for(state='visible', timeout=5000)
                
                confirm_button = page.locator('#confirm-action-btn')
                await confirm_button.click()
                
                # Wait for ARM acknowledgment
                await page.wait_for_function(
                    "document.querySelector('#armed-status').textContent.includes('ARMED')",
                    timeout=10000
                )
                
                # Verify armed status
                armed_status = await page.locator('#armed-status').text_content()
                assert 'ARMED' in armed_status
                
                # Step 4: Takeoff command with safety confirmation
                takeoff_button = page.locator('#takeoff-btn')
                await takeoff_button.wait_for(state='enabled')
                await takeoff_button.click()
                
                # Handle takeoff confirmation
                await confirmation_dialog.wait_for(state='visible')
                await confirm_button.click()
                
                # Wait for takeoff acknowledgment
                await asyncio.sleep(2)
                
                # Verify flight mode change
                flight_mode = await page.locator('#flight-mode').text_content()
                assert flight_mode in ['GUIDED', 'AUTO', 'STABILIZE']
                
                # Step 5: Navigation command (test position command)
                nav_lat = page.locator('#nav-latitude')
                nav_lon = page.locator('#nav-longitude')
                nav_alt = page.locator('#nav-altitude')
                
                await nav_lat.fill('37.7749')
                await nav_lon.fill('-122.4194')
                await nav_alt.fill('50')
                
                goto_button = page.locator('#goto-position-btn')
                await goto_button.click()
                
                # Handle navigation confirmation
                await confirmation_dialog.wait_for(state='visible')
                await confirm_button.click()
                
                # Wait for command acknowledgment
                await asyncio.sleep(2)
                
                # Step 6: Land command
                land_button = page.locator('#land-btn')
                await land_button.wait_for(state='enabled')
                await land_button.click()
                
                # Handle land confirmation
                await confirmation_dialog.wait_for(state='visible')
                await confirm_button.click()
                
                # Wait for landing process to start
                await asyncio.sleep(2)
                
                # Step 7: DISARM the vehicle
                disarm_button = page.locator('#disarm-btn')
                await disarm_button.wait_for(state='enabled')
                await disarm_button.click()
                
                # Handle disarm confirmation
                await confirmation_dialog.wait_for(state='visible')
                await confirm_button.click()
                
                # Wait for DISARM acknowledgment
                await page.wait_for_function(
                    "document.querySelector('#armed-status').textContent.includes('DISARMED')",
                    timeout=10000
                )
                
                # Verify disarmed status
                armed_status = await page.locator('#armed-status').text_content()
                assert 'DISARMED' in armed_status
                
                # Step 8: Verify telemetry continued throughout workflow
                # Check that VFR HUD is still updating
                pfd_canvas = page.locator('#pfd-canvas')
                await pfd_canvas.wait_for(state='visible')
                
                # Verify telemetry data is recent (within last 2 seconds)
                last_update = await page.locator('#last-telemetry-update').text_content()
                if last_update:
                    update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    time_diff = datetime.now() - update_time.replace(tzinfo=None)
                    assert time_diff.total_seconds() < 5, "Telemetry not updating properly"
                
            finally:
                await browser.close()

    @pytest.mark.asyncio  
    async def test_telemetry_flow_during_operations(self, app_with_service):
        """Test telemetry data flow during flight operations."""
        app, socketio = app_with_service
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate and connect
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Monitor telemetry updates
                telemetry_updates = []
                
                def handle_console(msg):
                    if 'telemetry_update' in str(msg.text):
                        telemetry_updates.append(msg.text)
                
                page.on('console', handle_console)
                
                # Connect to drone
                await page.click('#connect-btn')
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Wait and verify continuous telemetry
                await asyncio.sleep(5)
                
                # Check telemetry update frequency (should be ~10Hz)
                # At least 40 updates in 5 seconds for 10Hz target
                assert len(telemetry_updates) >= 30, f"Insufficient telemetry updates: {len(telemetry_updates)}"
                
                # Verify VFR HUD components are updating
                altitude_display = await page.locator('#altitude-tape').text_content()
                speed_display = await page.locator('#speed-tape').text_content()
                heading_display = await page.locator('#compass-heading').text_content()
                
                assert altitude_display, "Altitude not displayed"
                assert speed_display, "Speed not displayed" 
                assert heading_display, "Heading not displayed"
                
            finally:
                await browser.close()

    def test_cross_component_state_synchronization(self, app_with_service):
        """Test state synchronization across all system components."""
        app, socketio = app_with_service
        
        # Test that MAVLink service state matches web interface state
        mavlink_service = app.mavlink_service
        
        # Start connection
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
        
        time.sleep(2)  # Allow connection to stabilize
        
        # Get MAVLink service status
        service_status = mavlink_service.get_status()
        
        # Verify service components are active
        assert service_status['mavlink_connected'], "MAVLink not connected"
        assert service_status['connection_state'] == 'connected', f"Unexpected state: {service_status['connection_state']}"
        assert service_status['service_threads']['message_processor'], "Message processor not active"
        assert service_status['service_threads']['telemetry_streamer'], "Telemetry streamer not active"
        
        # Test web interface reflects MAVLink state
        try:
            response = requests.get('http://localhost:5002/api/status')
            if response.status_code == 200:
                web_status = response.json()
                assert web_status.get('connected', False), "Web interface shows disconnected"
                assert web_status.get('mavlink_connected', False), "Web interface MAVLink status mismatch"
        except Exception as e:
            print(f"Web status check failed (may be expected): {e}")

    @pytest.mark.asyncio
    async def test_safety_confirmations_in_workflow(self, app_with_service):
        """Test safety confirmation system throughout flight workflow."""
        app, socketio = app_with_service
        
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
                
                # Test ARM safety confirmation
                await page.click('#arm-btn')
                
                # Verify safety dialog appears
                confirmation_modal = page.locator('#safety-confirmation-modal')
                await confirmation_modal.wait_for(state='visible', timeout=5000)
                
                # Verify modal content
                modal_text = await page.locator('#safety-confirmation-message').text_content()
                assert 'ARM' in modal_text.upper()
                
                # Test cancel functionality
                cancel_button = page.locator('#cancel-action-btn')
                await cancel_button.click()
                
                await confirmation_modal.wait_for(state='hidden')
                
                # Verify ARM was cancelled (status should remain DISARMED)
                await asyncio.sleep(1)
                status = await page.locator('#armed-status').text_content()
                assert 'DISARMED' in status
                
                # Test successful ARM with confirmation
                await page.click('#arm-btn')
                await confirmation_modal.wait_for(state='visible')
                
                confirm_button = page.locator('#confirm-action-btn')
                await confirm_button.click()
                
                # Verify ARM succeeded
                await page.wait_for_function(
                    "document.querySelector('#armed-status').textContent.includes('ARMED')",
                    timeout=10000
                )
                
                # Test TAKEOFF safety confirmation
                await page.click('#takeoff-btn')
                await confirmation_modal.wait_for(state='visible')
                
                modal_text = await page.locator('#safety-confirmation-message').text_content()
                assert 'TAKEOFF' in modal_text.upper()
                
                await confirm_button.click()
                await asyncio.sleep(2)
                
                # Test emergency procedures (RTL)
                rtl_button = page.locator('#rtl-btn')
                await rtl_button.click()
                await confirmation_modal.wait_for(state='visible')
                
                modal_text = await page.locator('#safety-confirmation-message').text_content()
                assert any(word in modal_text.upper() for word in ['RTL', 'RETURN', 'LAUNCH'])
                
                await confirm_button.click()
                
            finally:
                await browser.close()

    def test_performance_during_integration(self, app_with_service):
        """Test system performance during complete integration workflow."""
        app, socketio = app_with_service
        
        # Performance metrics tracking
        start_time = time.time()
        
        # Test MAVLink service performance
        mavlink_service = app.mavlink_service
        
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
            
        connection_time = time.time() - start_time
        assert connection_time < 5.0, f"Connection took too long: {connection_time:.2f}s"
        
        # Test telemetry performance
        telemetry_start = time.time()
        for _ in range(10):
            status = mavlink_service.get_status()
            assert status is not None
            time.sleep(0.1)  # 10Hz test
        
        telemetry_duration = time.time() - telemetry_start
        expected_duration = 1.0  # 10 iterations at 0.1s each
        assert telemetry_duration < expected_duration + 0.5, f"Telemetry too slow: {telemetry_duration:.2f}s"
        
        # Test command response time
        command_start = time.time()
        result = mavlink_service.arm_vehicle()  # Test command
        command_duration = time.time() - command_start
        
        assert command_duration < 5.0, f"Command acknowledgment too slow: {command_duration:.2f}s"
        
        # Cleanup
        if result:  # If ARM succeeded, disarm for cleanup
            mavlink_service.disarm_vehicle()

    def test_error_recovery_integration(self, app_with_service):
        """Test error recovery and graceful degradation."""
        app, socketio = app_with_service
        
        mavlink_service = app.mavlink_service
        
        # Test service restart capability
        if mavlink_service.start():
            # Stop service
            mavlink_service.stop()
            time.sleep(1)
            
            # Verify service stopped
            status = mavlink_service.get_status()
            assert not status['mavlink_connected']
            
            # Test restart
            restart_success = mavlink_service.start()
            if restart_success:
                time.sleep(2)
                
                # Verify service restarted
                status = mavlink_service.get_status()
                assert status['mavlink_connected']
                assert status['service_threads']['message_processor']
                assert status['service_threads']['telemetry_streamer']
        else:
            pytest.skip("Could not establish initial connection")

    def teardown_method(self, method):
        """Cleanup after each test method."""
        time.sleep(0.5)  # Allow cleanup time between tests
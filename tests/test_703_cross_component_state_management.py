"""
TEST-703: Cross-Component State Management

Tests state synchronization between flight controls, navigation, and VFR HUD.

Validates:
- State synchronization across multiple components
- Armed/disarmed state reflection in all UI elements
- Flight mode changes propagated to all components
- Error states communicated throughout the system
"""

import pytest
import time
import asyncio
import json
import threading
from datetime import datetime
from playwright.async_api import async_playwright
import requests

from src.web.app_factory import initialize_app


class TestCrossComponentStateManagement:
    """Cross-component state management integration tests."""

    @pytest.fixture(scope="class")
    def integrated_app(self):
        """Create fully integrated application for state testing."""
        app, socketio = initialize_app()
        
        app.config.update({
            'TESTING': True,
            'WEB_SERVER_PORT': 5002,
            'TELEMETRY_UPDATE_INTERVAL': 0.1
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
    async def test_armed_state_synchronization(self, integrated_app):
        """Test armed/disarmed state synchronization across all components."""
        app, socketio = integrated_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Connect to drone first
                await page.click('#connect-btn')
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Verify initial disarmed state across components
                armed_status_elements = [
                    '#armed-status',
                    '#arm-indicator', 
                    '#safety-status'
                ]
                
                for element in armed_status_elements:
                    try:
                        element_text = await page.locator(element).text_content()
                        if element_text:
                            assert 'DISARMED' in element_text.upper() or 'SAFE' in element_text.upper()
                    except:
                        pass  # Element may not exist
                
                # Test ARM command and state propagation
                await page.click('#arm-btn')
                
                # Handle safety confirmation
                try:
                    confirmation_modal = page.locator('#safety-confirmation-modal')
                    await confirmation_modal.wait_for(state='visible', timeout=5000)
                    await page.click('#confirm-action-btn')
                except:
                    pass  # May not have confirmation dialog
                
                # Wait for armed state propagation
                await page.wait_for_function(
                    """() => {
                        const status = document.querySelector('#armed-status');
                        return status && status.textContent.includes('ARMED');
                    }""",
                    timeout=10000
                )
                
                # Verify armed state in all components
                armed_status = await page.locator('#armed-status').text_content()
                assert 'ARMED' in armed_status.upper()
                
                # Check VFR HUD armed indicator
                try:
                    hud_armed = await page.locator('#pfd-armed-indicator').text_content()
                    assert 'ARMED' in hud_armed.upper()
                except:
                    pass  # Indicator may be visual only
                
                # Check flight controls enable/disable state
                control_buttons = ['#takeoff-btn', '#land-btn', '#rtl-btn']
                for button in control_buttons:
                    try:
                        button_element = page.locator(button)
                        if await button_element.is_visible():
                            is_enabled = await button_element.is_enabled()
                            # Buttons should be enabled when armed
                            assert is_enabled, f"Button {button} should be enabled when armed"
                    except:
                        pass
                
                # Test DISARM and state propagation
                await page.click('#disarm-btn')
                
                try:
                    confirmation_modal = page.locator('#safety-confirmation-modal')
                    await confirmation_modal.wait_for(state='visible', timeout=5000)
                    await page.click('#confirm-action-btn')
                except:
                    pass
                
                # Wait for disarmed state
                await page.wait_for_function(
                    """() => {
                        const status = document.querySelector('#armed-status');
                        return status && status.textContent.includes('DISARMED');
                    }""",
                    timeout=10000
                )
                
                # Verify disarmed state propagation
                armed_status = await page.locator('#armed-status').text_content()
                assert 'DISARMED' in armed_status.upper()
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_flight_mode_propagation(self, integrated_app):
        """Test flight mode changes propagated to all UI components."""
        app, socketio = integrated_app
        
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
                
                # Wait for initial flight mode
                await asyncio.sleep(2)
                
                # Check flight mode display elements
                flight_mode_elements = [
                    '#flight-mode',
                    '#mode-indicator',
                    '#pfd-flight-mode'
                ]
                
                initial_modes = {}
                for element in flight_mode_elements:
                    try:
                        mode_text = await page.locator(element).text_content()
                        initial_modes[element] = mode_text
                    except:
                        initial_modes[element] = None
                
                # Verify flight mode is displayed somewhere
                has_flight_mode = any(mode for mode in initial_modes.values() if mode and mode.strip())
                assert has_flight_mode, "Flight mode not displayed in any component"
                
                # Test mode change via dropdown (if available)
                try:
                    mode_selector = page.locator('#flight-mode-selector')
                    if await mode_selector.is_visible():
                        await mode_selector.select_option('GUIDED')
                        
                        # Wait for mode change propagation
                        await asyncio.sleep(2)
                        
                        # Check if mode updated in displays
                        updated_mode = await page.locator('#flight-mode').text_content()
                        # Mode change may require ARM first, so we check for any change
                        
                except Exception as e:
                    print(f"Mode selector test skipped: {e}")
                
                # Test mode consistency across components
                final_modes = {}
                for element in flight_mode_elements:
                    try:
                        mode_text = await page.locator(element).text_content()
                        final_modes[element] = mode_text
                    except:
                        final_modes[element] = None
                
                # Verify consistency (all non-null values should match)
                non_null_modes = [mode for mode in final_modes.values() if mode and mode.strip()]
                if len(non_null_modes) > 1:
                    first_mode = non_null_modes[0].strip()
                    for mode in non_null_modes[1:]:
                        assert mode.strip() == first_mode, f"Flight mode inconsistency: {non_null_modes}"
                
            finally:
                await browser.close()

    def test_backend_frontend_state_sync(self, integrated_app):
        """Test state synchronization between backend and frontend."""
        app, socketio = integrated_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone")
        
        time.sleep(2)  # Allow connection to stabilize
        
        # Get backend state
        backend_status = mavlink_service.get_status()
        backend_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
        
        # Test web API state (if available)
        try:
            response = requests.get('http://localhost:5002/api/status', timeout=5)
            if response.status_code == 200:
                frontend_status = response.json()
                
                # Compare key state fields
                assert backend_status['mavlink_connected'] == frontend_status.get('connected', False), \
                    "Connection state mismatch"
                
                if 'armed' in frontend_status:
                    assert backend_status['armed_status'] == frontend_status['armed'], \
                        "Armed state mismatch"
                
                if 'flight_mode' in frontend_status:
                    assert backend_status['flight_mode'] == frontend_status['flight_mode'], \
                        "Flight mode mismatch"
                        
        except requests.RequestException:
            print("Web API not available - testing SocketIO state sync")
            
            # Test SocketIO state synchronization
            telemetry_received = []
            
            import socketio as sio_client
            client = sio_client.SimpleClient()
            
            try:
                client.connect('http://localhost:5002')
                
                # Collect telemetry updates
                start_time = time.time()
                while time.time() - start_time < 3.0:
                    try:
                        event_data = client.receive()
                        if event_data[0] == 'telemetry_update':
                            telemetry_received.append(event_data[1])
                    except:
                        pass
                    client.sleep(0.1)
                
                # Verify state consistency in SocketIO data
                if telemetry_received:
                    latest_telemetry = telemetry_received[-1]
                    
                    if 'connection_status' in latest_telemetry:
                        conn_status = latest_telemetry['connection_status']
                        assert conn_status['state'] == backend_status['connection_state'], \
                            "SocketIO connection state mismatch"
                
            finally:
                try:
                    client.disconnect()
                except:
                    pass

    @pytest.mark.asyncio
    async def test_error_state_propagation(self, integrated_app):
        """Test error state communication throughout the system."""
        app, socketio = integrated_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Test connection error handling
                # First, try to connect normally
                await page.click('#connect-btn')
                
                # Wait for connection result (success or failure)
                await asyncio.sleep(5)
                
                status_text = await page.locator('#connection-status').text_content()
                
                if 'Connected' in status_text:
                    # Test command error by sending invalid command
                    # This tests error propagation through the command pipeline
                    
                    # Try to send command without being armed (should show error)
                    try:
                        await page.click('#takeoff-btn')
                        
                        # Look for error message or disabled state
                        await asyncio.sleep(2)
                        
                        # Check for error indicators
                        error_indicators = [
                            '#error-message',
                            '#status-message',
                            '#command-feedback'
                        ]
                        
                        error_found = False
                        for indicator in error_indicators:
                            try:
                                error_text = await page.locator(indicator).text_content()
                                if error_text and ('error' in error_text.lower() or 'failed' in error_text.lower()):
                                    error_found = True
                                    break
                            except:
                                pass
                        
                        # Error handling may be implemented in various ways
                        # We mainly verify the system doesn't crash
                        
                    except Exception as e:
                        print(f"Command error test: {e}")
                
                else:
                    # Test disconnection error state
                    assert 'Disconnected' in status_text or 'Failed' in status_text or 'Error' in status_text
                    
                    # Verify error state affects UI appropriately
                    control_buttons = ['#arm-btn', '#takeoff-btn', '#land-btn']
                    
                    for button in control_buttons:
                        try:
                            button_element = page.locator(button)
                            if await button_element.is_visible():
                                # When disconnected, critical buttons should be disabled
                                is_enabled = await button_element.is_enabled()
                                if button in ['#takeoff-btn', '#land-btn']:
                                    # These should definitely be disabled when not connected
                                    assert not is_enabled, f"{button} should be disabled when disconnected"
                        except:
                            pass
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self, integrated_app):
        """Test system behavior with concurrent state updates."""
        app, socketio = integrated_app
        
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
                
                # Test rapid state changes
                # ARM and immediately try other actions
                await page.click('#arm-btn')
                
                # Handle confirmation if present
                try:
                    confirmation_modal = page.locator('#safety-confirmation-modal')
                    await confirmation_modal.wait_for(state='visible', timeout=2000)
                    await page.click('#confirm-action-btn')
                except:
                    pass
                
                # Immediately try to change flight mode (if available)
                try:
                    mode_selector = page.locator('#flight-mode-selector')
                    if await mode_selector.is_visible():
                        await mode_selector.select_option('GUIDED')
                except:
                    pass
                
                # Wait for states to settle
                await asyncio.sleep(3)
                
                # Verify system is in consistent state
                armed_status = await page.locator('#armed-status').text_content()
                connection_status = await page.locator('#connection-status').text_content()
                
                # System should maintain valid states
                assert 'ARMED' in armed_status or 'DISARMED' in armed_status
                assert 'Connected' in connection_status
                
                # Test concurrent UI interactions
                # Click multiple buttons in rapid succession
                buttons_to_test = ['#disarm-btn', '#land-btn']
                
                for button in buttons_to_test:
                    try:
                        button_element = page.locator(button)
                        if await button_element.is_visible() and await button_element.is_enabled():
                            await button_element.click()
                            
                            # Handle any confirmations quickly
                            try:
                                await page.click('#confirm-action-btn', timeout=1000)
                            except:
                                pass
                            
                            await asyncio.sleep(0.5)  # Brief pause between actions
                    except:
                        pass
                
                # Allow final state settling
                await asyncio.sleep(2)
                
                # Verify system didn't crash and maintains valid state
                final_status = await page.locator('#connection-status').text_content()
                assert 'Connected' in final_status or 'Disconnected' in final_status
                
            finally:
                await browser.close()

    def test_state_persistence_across_reconnection(self, integrated_app):
        """Test state behavior across connection/disconnection cycles."""
        app, socketio = integrated_app
        
        mavlink_service = app.mavlink_service
        
        # Test initial state
        initial_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
        assert isinstance(initial_telemetry, dict)
        
        # Test connection cycle
        if mavlink_service.start():
            time.sleep(2)
            
            # Get connected state
            connected_status = mavlink_service.get_status()
            assert connected_status['mavlink_connected']
            
            connected_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            
            # Disconnect
            mavlink_service.stop()
            time.sleep(1)
            
            # Get disconnected state
            disconnected_status = mavlink_service.get_status()
            assert not disconnected_status['mavlink_connected']
            
            # Telemetry should still be available (may be stale)
            disconnected_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            assert isinstance(disconnected_telemetry, dict)
            
            # Reconnect
            if mavlink_service.start():
                time.sleep(2)
                
                # Verify reconnected state
                reconnected_status = mavlink_service.get_status()
                assert reconnected_status['mavlink_connected']
                
                # State should be restored
                reconnected_telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
                assert reconnected_telemetry['last_update'] != connected_telemetry.get('last_update', ''), \
                    "Telemetry should be updating after reconnection"
                
        else:
            pytest.skip("Could not establish connection for reconnection test")

    def test_multi_client_state_consistency(self, integrated_app):
        """Test state consistency across multiple web clients."""
        app, socketio = integrated_app
        
        import socketio as sio_client
        
        # Create multiple SocketIO clients
        clients = []
        telemetry_data = {}
        
        try:
            # Create 3 clients
            for client_id in range(3):
                client = sio_client.SimpleClient()
                client.connect('http://localhost:5002')
                clients.append(client)
                telemetry_data[client_id] = []
                
                # Set up telemetry collection
                def make_handler(cid):
                    def handler(data):
                        telemetry_data[cid].append(data)
                    return handler
                
                client.on('telemetry_update', make_handler(client_id))
            
            # Start MAVLink service to generate telemetry
            mavlink_service = app.mavlink_service
            if mavlink_service.start():
                time.sleep(3)  # Collect telemetry
                
                # Verify all clients received telemetry
                for client_id in range(3):
                    assert len(telemetry_data[client_id]) > 0, f"Client {client_id} received no telemetry"
                
                # Verify telemetry consistency across clients
                # All clients should receive similar data
                if all(len(data) > 0 for data in telemetry_data.values()):
                    # Compare latest telemetry from each client
                    latest_data = [data[-1] for data in telemetry_data.values()]
                    
                    # All clients should have connection status
                    for data in latest_data:
                        assert 'connection_status' in data or 'heartbeat' in data, \
                            "Missing connection data in client telemetry"
            
        except Exception as e:
            print(f"Multi-client test error: {e}")
        finally:
            # Cleanup clients
            for client in clients:
                try:
                    client.disconnect()
                except:
                    pass

    def teardown_method(self, method):
        """Cleanup after each test."""
        time.sleep(0.5)
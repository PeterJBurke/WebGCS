#!/usr/bin/env python3
"""
CRITICAL TEST: Fixed Connect Button and Virtual Drone Communication
Tests the recently fixed connection-manager.js and verifies end-to-end communication
"""
import pytest
import time
import threading
import requests
import socketio
import json
from pymavlink import mavutil
import subprocess
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


class TestFixedConnectButton:
    """Critical test suite for the fixed connect button functionality"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.server_url = "http://localhost:5001"
        cls.virtual_drone_ip = "192.168.193.235"
        cls.virtual_drone_port = 5678
        cls.connection_string = f"tcp:{cls.virtual_drone_ip}:{cls.virtual_drone_port}"
        
        # Test results tracking
        cls.test_results = {
            'server_healthy': False,
            'ui_loads_without_js_errors': False,
            'connect_button_exists': False,
            'connect_button_clickable': False,
            'websocket_connection_works': False,
            'mavlink_connection_established': False,
            'heartbeat_messages_received': False,
            'ui_state_updates_correctly': False,
            'virtual_drone_responsive': False,
            'end_to_end_workflow_complete': False
        }
        
        # Initialize web driver
        cls._init_web_driver()
        
        # Verify server is running
        cls._verify_server_running()
        
    @classmethod
    def _init_web_driver(cls):
        """Initialize Chrome web driver for UI testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        chrome_options.add_argument("--remote-debugging-port=9223")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
            print("Chrome driver initialized successfully")
        except Exception as e:
            print(f"Chrome driver setup failed: {e}")
            pytest.skip("Chrome driver not available - cannot test UI")
    
    @classmethod
    def _verify_server_running(cls):
        """Verify WebGCS server is running"""
        try:
            response = requests.get(f"{cls.server_url}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            cls.test_results['server_healthy'] = True
            print(f"Server healthy: {data}")
        except Exception as e:
            pytest.skip(f"WebGCS server not accessible at {cls.server_url}: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Clean up after tests"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def test_01_virtual_drone_direct_connection(self):
        """CRITICAL: Verify virtual drone is accessible directly via MAVLink"""
        print(f"\n=== Testing Direct Virtual Drone Connection ===")
        print(f"Target: {self.connection_string}")
        
        try:
            # Direct MAVLink connection test
            connection = mavutil.mavlink_connection(
                self.connection_string,
                source_system=255,
                timeout=5.0
            )
            
            print("MAVLink connection object created, waiting for messages...")
            
            # Wait for messages to confirm drone responsiveness
            start_time = time.time()
            messages_received = []
            
            while time.time() - start_time < 15.0:  # 15 second timeout
                try:
                    msg = connection.recv_match(timeout=1.0)
                    if msg:
                        message_type = msg.get_type()
                        messages_received.append(message_type)
                        print(f"Received: {message_type}")
                        
                        if len(messages_received) >= 3:  # Got sufficient messages
                            break
                except:
                    pass
            
            connection.close()
            
            assert len(messages_received) > 0, f"No messages received from virtual drone at {self.connection_string}"
            
            self.test_results['virtual_drone_responsive'] = True
            print(f"✅ Virtual drone is responsive: {len(messages_received)} messages received")
            print(f"Message types: {list(set(messages_received))}")
            
        except Exception as e:
            pytest.fail(f"Virtual drone connection failed: {e}")
    
    def test_02_load_ui_check_javascript_errors(self):
        """CRITICAL: Load UI and verify no JavaScript errors in console"""
        print(f"\n=== Testing UI Load and JavaScript Health ===")
        
        # Load the main page
        self.driver.get(self.server_url)
        
        # Wait for page to fully load
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "connect-btn"))
        )
        
        # Check for JavaScript errors in console
        logs = self.driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        if js_errors:
            print("JavaScript errors found:")
            for error in js_errors:
                print(f"  {error['level']}: {error['message']}")
            pytest.fail(f"JavaScript errors detected: {len(js_errors)} errors")
        
        self.test_results['ui_loads_without_js_errors'] = True
        print("✅ UI loaded successfully with no JavaScript errors")
    
    def test_03_connect_button_elements_verification(self):
        """CRITICAL: Verify connect button and related elements exist and are functional"""
        print(f"\n=== Testing Connect Button Elements ===")
        
        # Check connect button exists and properties
        connect_btn = self.driver.find_element(By.ID, "connect-btn")
        assert connect_btn.is_displayed(), "Connect button not visible"
        assert connect_btn.text == "Connect", f"Connect button text incorrect: {connect_btn.text}"
        assert not connect_btn.get_attribute('disabled'), "Connect button should not be disabled initially"
        
        self.test_results['connect_button_exists'] = True
        print("✅ Connect button exists and has correct properties")
        
        # Check disconnect button
        disconnect_btn = self.driver.find_element(By.ID, "disconnect-btn")
        assert disconnect_btn.get_attribute('disabled'), "Disconnect button should be disabled initially"
        
        # Check IP and Port inputs
        ip_input = self.driver.find_element(By.ID, "ip-address")
        port_input = self.driver.find_element(By.ID, "port-number")
        
        assert ip_input.get_attribute('value') == "192.168.193.235", "IP input default value incorrect"
        assert port_input.get_attribute('value') == "5678", "Port input default value incorrect"
        
        # Check status elements
        connection_status = self.driver.find_element(By.ID, "connection-status")
        heartbeat_counter = self.driver.find_element(By.ID, "heartbeat-counter")
        
        assert "disconnected" in connection_status.get_attribute('class').lower()
        assert heartbeat_counter.text == "0", f"Heartbeat counter should start at 0: {heartbeat_counter.text}"
        
        print("✅ All connection UI elements verified and correct")
    
    def test_04_websocket_connection_establishment(self):
        """CRITICAL: Test WebSocket connection to server"""
        print(f"\n=== Testing WebSocket Connection ===")
        
        websocket_connected = threading.Event()
        connection_events = []
        telemetry_events = []
        
        # Create SocketIO client
        sio = socketio.Client()
        
        @sio.event
        def connect():
            print("WebSocket connected to server")
            websocket_connected.set()
        
        @sio.event
        def connection_status(data):
            print(f"Connection status event: {data}")
            connection_events.append(data)
        
        @sio.event
        def telemetry_update(data):
            print(f"Telemetry update: {data}")
            telemetry_events.append(data)
        
        @sio.event
        def command_result(data):
            print(f"Command result: {data}")
        
        try:
            sio.connect(self.server_url)
            assert websocket_connected.wait(timeout=10), "WebSocket connection timeout"
            
            self.test_results['websocket_connection_works'] = True
            print("✅ WebSocket connection established successfully")
            
            # Store client for next tests
            self._websocket_client = sio
            self._connection_events = connection_events
            self._telemetry_events = telemetry_events
            
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {e}")
    
    def test_05_connect_button_click_functionality(self):
        """CRITICAL: Test connect button click triggers proper sequence"""
        print(f"\n=== Testing Connect Button Click Functionality ===")
        
        # Clear previous events
        self._connection_events.clear()
        self._telemetry_events.clear()
        
        # Find and click connect button
        connect_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "connect-btn"))
        )
        
        print("Clicking connect button...")
        connect_btn.click()
        
        self.test_results['connect_button_clickable'] = True
        
        # Verify button state changes
        WebDriverWait(self.driver, 5).until(
            lambda driver: driver.find_element(By.ID, "connect-btn").text == "Connecting..."
        )
        
        # Verify button is disabled during connection
        assert connect_btn.get_attribute('disabled'), "Connect button should be disabled while connecting"
        
        print("✅ Connect button click triggered properly - button shows 'Connecting...' and is disabled")
    
    def test_06_verify_connection_process_events(self):
        """CRITICAL: Verify WebSocket events during connection process"""
        print(f"\n=== Testing Connection Process Events ===")
        
        # Wait for connection status events
        start_time = time.time()
        while time.time() - start_time < 20:  # 20 second timeout
            if self._connection_events:
                break
            time.sleep(0.5)
        
        assert len(self._connection_events) > 0, "No connection status events received"
        
        latest_event = self._connection_events[-1]
        print(f"Latest connection event: {latest_event}")
        
        # Should have connecting or connected status
        status = latest_event.get('status')
        assert status in ['connecting', 'connected'], f"Unexpected status: {status}"
        
        print(f"✅ Connection process events received: status = {status}")
    
    def test_07_verify_mavlink_connection_established(self):
        """CRITICAL: Verify MAVLink connection is established to virtual drone"""
        print(f"\n=== Testing MAVLink Connection Establishment ===")
        
        # Wait for telemetry indicating successful connection
        start_time = time.time()
        connected = False
        
        while time.time() - start_time < 30:  # 30 second timeout for connection
            # Check latest telemetry events
            if self._telemetry_events:
                latest_telemetry = self._telemetry_events[-1]
                if latest_telemetry.get('connected') == True:
                    connected = True
                    print(f"Connection established! System ID: {latest_telemetry.get('system_id', 'N/A')}")
                    break
            
            # Also check via server health endpoint
            try:
                response = requests.get(f"{self.server_url}/health", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('drone_connected'):
                        connected = True
                        print("Connection confirmed via health endpoint")
                        break
            except:
                pass
            
            time.sleep(0.5)
        
        assert connected, "MAVLink connection not established within timeout"
        
        self.test_results['mavlink_connection_established'] = True
        print("✅ MAVLink connection successfully established to virtual drone")
    
    def test_08_verify_heartbeat_message_reception(self):
        """CRITICAL: Verify heartbeat messages are being received and UI updates"""
        print(f"\n=== Testing Heartbeat Reception ===")
        
        # Monitor heartbeat counter in UI
        heartbeat_counter = self.driver.find_element(By.ID, "heartbeat-counter")
        
        # Wait for heartbeat count to increase
        initial_count = int(heartbeat_counter.text)
        print(f"Initial heartbeat count: {initial_count}")
        
        # Wait for heartbeat to increment (should be fast once connected)
        start_time = time.time()
        heartbeat_received = False
        
        while time.time() - start_time < 15:  # 15 second timeout
            current_count = int(heartbeat_counter.text)
            if current_count > initial_count:
                print(f"Heartbeat count increased to: {current_count}")
                heartbeat_received = True
                break
            time.sleep(0.5)
        
        assert heartbeat_received, f"No heartbeat increase detected (stayed at {initial_count})"
        
        self.test_results['heartbeat_messages_received'] = True
        print("✅ Heartbeat messages successfully received and UI updated")
    
    def test_09_verify_ui_state_updates(self):
        """CRITICAL: Verify UI correctly reflects connected state"""
        print(f"\n=== Testing UI State Updates ===")
        
        # Check connection status indicator
        connection_status = self.driver.find_element(By.ID, "connection-status")
        status_class = connection_status.get_attribute('class')
        status_text = connection_status.text
        
        print(f"Connection status: '{status_text}' (class: {status_class})")
        
        assert 'connected' in status_class.lower(), f"Status class should contain 'connected': {status_class}"
        assert 'connected' in status_text.lower(), f"Status text should indicate connected: {status_text}"
        
        # Check button states
        connect_btn = self.driver.find_element(By.ID, "connect-btn")
        disconnect_btn = self.driver.find_element(By.ID, "disconnect-btn")
        
        assert connect_btn.get_attribute('disabled'), "Connect button should be disabled when connected"
        assert connect_btn.text == "Connect", "Connect button should show 'Connect' when connected"
        assert not disconnect_btn.get_attribute('disabled'), "Disconnect button should be enabled when connected"
        
        self.test_results['ui_state_updates_correctly'] = True
        print("✅ UI state correctly reflects connected state")
    
    def test_10_test_disconnect_functionality(self):
        """CRITICAL: Test disconnect button functionality"""
        print(f"\n=== Testing Disconnect Functionality ===")
        
        # Click disconnect button
        disconnect_btn = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, "disconnect-btn"))
        )
        
        disconnect_btn.click()
        print("Disconnect button clicked")
        
        # Wait for UI to reflect disconnected state
        WebDriverWait(self.driver, 10).until(
            lambda driver: 'disconnected' in driver.find_element(By.ID, "connection-status").get_attribute('class').lower()
        )
        
        # Verify disconnected state
        connection_status = self.driver.find_element(By.ID, "connection-status")
        connect_btn = self.driver.find_element(By.ID, "connect-btn")
        disconnect_btn = self.driver.find_element(By.ID, "disconnect-btn")
        
        assert 'disconnected' in connection_status.get_attribute('class').lower()
        assert not connect_btn.get_attribute('disabled'), "Connect button should be enabled after disconnect"
        assert disconnect_btn.get_attribute('disabled'), "Disconnect button should be disabled after disconnect"
        
        print("✅ Disconnect functionality working correctly")
    
    def test_11_end_to_end_workflow_validation(self):
        """CRITICAL: Validate complete end-to-end workflow"""
        print(f"\n=== End-to-End Workflow Validation ===")
        
        # Test one complete cycle: connect -> verify -> disconnect
        print("Testing complete connect/disconnect cycle...")
        
        # 1. Start from disconnected state (should be from previous test)
        connection_status = self.driver.find_element(By.ID, "connection-status")
        assert 'disconnected' in connection_status.get_attribute('class').lower()
        
        # 2. Click connect again
        connect_btn = self.driver.find_element(By.ID, "connect-btn")
        connect_btn.click()
        
        # 3. Wait for connection
        WebDriverWait(self.driver, 30).until(
            lambda driver: 'connected' in driver.find_element(By.ID, "connection-status").get_attribute('class').lower()
        )
        
        # 4. Verify heartbeat increases
        heartbeat_counter = self.driver.find_element(By.ID, "heartbeat-counter")
        initial_count = int(heartbeat_counter.text)
        
        time.sleep(3)  # Wait for heartbeats
        
        final_count = int(heartbeat_counter.text)
        assert final_count > initial_count, "Heartbeat should increase during connection"
        
        # 5. Disconnect
        disconnect_btn = self.driver.find_element(By.ID, "disconnect-btn")
        disconnect_btn.click()
        
        # 6. Verify disconnected
        WebDriverWait(self.driver, 10).until(
            lambda driver: 'disconnected' in driver.find_element(By.ID, "connection-status").get_attribute('class').lower()
        )
        
        self.test_results['end_to_end_workflow_complete'] = True
        print("✅ Complete end-to-end workflow validated successfully")
    
    def test_12_cleanup_websocket(self):
        """Clean up WebSocket connection"""
        if hasattr(self, '_websocket_client'):
            self._websocket_client.disconnect()
            print("WebSocket client disconnected")
    
    def test_99_final_validation_report(self):
        """CRITICAL: Generate final validation report"""
        print(f"\n{'='*70}")
        print("CRITICAL TEST RESULTS: Fixed Connect Button & Virtual Drone Communication")
        print('='*70)
        
        # Print detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:35}: {status}")
        
        # Calculate success rate
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\nTest Results: {passed_tests}/{total_tests} passed ({success_rate:.1f}%)")
        
        # Critical success criteria
        critical_tests = [
            'virtual_drone_responsive',
            'ui_loads_without_js_errors', 
            'connect_button_clickable',
            'mavlink_connection_established',
            'heartbeat_messages_received',
            'ui_state_updates_correctly'
        ]
        
        critical_passed = all(self.test_results.get(test, False) for test in critical_tests)
        
        print(f"\nCRITICAL SUCCESS CRITERIA:")
        for test in critical_tests:
            status = "✅ PASS" if self.test_results.get(test, False) else "❌ FAIL"
            print(f"  {test}: {status}")
        
        print(f"\nOVERALL RESULT: {'✅ SUCCESS' if critical_passed else '❌ FAILURE'}")
        
        if critical_passed:
            print(f"""
🎉 MISSION ACCOMPLISHED! 
✅ Connect button JavaScript syntax error FIXED
✅ Web interface loads without JavaScript errors  
✅ Connect button successfully communicates with virtual drone at {self.virtual_drone_ip}:{self.virtual_drone_port}
✅ MAVLink connection established and heartbeat messages received
✅ UI correctly updates to show connection status
✅ Complete end-to-end workflow validated

The fixed connection-manager.js is working perfectly!
""")
        else:
            failed_critical = [test for test in critical_tests if not self.test_results.get(test, False)]
            print(f"""
❌ MISSION INCOMPLETE
Failed critical tests: {', '.join(failed_critical)}

The connect button fix needs additional attention.
""")
        
        print('='*70)
        
        # Assert for pytest
        assert critical_passed, f"Critical tests failed: {[test for test in critical_tests if not self.test_results.get(test, False)]}"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])
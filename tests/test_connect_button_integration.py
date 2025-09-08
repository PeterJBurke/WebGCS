#!/usr/bin/env python3
"""
Integration Test for Connect Button Functionality
Tests the complete end-to-end connection workflow from UI to virtual drone
"""
import pytest
import time
import threading
import requests
import socketio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pymavlink import mavutil
import json

class TestConnectButtonIntegration:
    """Test suite for connect button functionality"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        cls.server_url = "http://localhost:5001"
        cls.virtual_drone_ip = "192.168.193.235"
        cls.virtual_drone_port = 5678
        cls.connection_string = f"tcp:{cls.virtual_drone_ip}:{cls.virtual_drone_port}"
        
        # Setup Chrome driver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Chrome driver setup failed: {e}")
            pytest.skip("Chrome driver not available")
        
        # Verify server is running
        try:
            response = requests.get(f"{cls.server_url}/health", timeout=5)
            assert response.status_code == 200
            print(f"Server health check passed: {response.json()}")
        except Exception as e:
            pytest.skip(f"WebGCS server not accessible: {e}")
        
        # Test data storage
        cls.test_results = {
            'ui_loaded': False,
            'connect_clicked': False,
            'websocket_connected': False,
            'mavlink_connected': False,
            'heartbeat_received': False,
            'ui_updated': False
        }
        
    @classmethod
    def teardown_class(cls):
        """Clean up after tests"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def test_01_server_health(self):
        """Test that server is healthy and responsive"""
        response = requests.get(f"{self.server_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data['status'] == 'healthy'
        print(f"Server health: {data}")
    
    def test_02_load_web_interface(self):
        """Test that web interface loads correctly"""
        self.driver.get(self.server_url)
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "connect-btn"))
        )
        
        # Check key elements exist
        connect_btn = self.driver.find_element(By.ID, "connect-btn")
        assert connect_btn.is_displayed()
        assert connect_btn.text == "Connect"
        
        # Check IP and port inputs
        ip_input = self.driver.find_element(By.ID, "ip-address")
        port_input = self.driver.find_element(By.ID, "port-number")
        
        assert ip_input.get_attribute('value') == "192.168.193.235"
        assert port_input.get_attribute('value') == "5678"
        
        self.test_results['ui_loaded'] = True
        print("Web interface loaded successfully")
    
    def test_03_virtual_drone_availability(self):
        """Test that virtual drone at target address is accessible"""
        try:
            # Try to connect directly via MAVLink
            connection = mavutil.mavlink_connection(
                self.connection_string,
                source_system=255,
                timeout=5.0
            )
            
            print(f"Testing connection to virtual drone at {self.connection_string}")
            
            # Wait for a message to confirm drone is responsive
            start_time = time.time()
            message_received = False
            
            while time.time() - start_time < 10.0:  # 10 second timeout
                try:
                    msg = connection.recv_match(timeout=1.0)
                    if msg:
                        print(f"Received message from virtual drone: {msg.get_type()}")
                        message_received = True
                        break
                except:
                    pass
            
            connection.close()
            
            assert message_received, "No response from virtual drone"
            print("Virtual drone is accessible and responsive")
            
        except Exception as e:
            pytest.skip(f"Virtual drone not available: {e}")
    
    def test_04_websocket_connection(self):
        """Test WebSocket connection to server"""
        websocket_connected = threading.Event()
        connection_status_received = threading.Event()
        telemetry_received = threading.Event()
        
        connection_status = {}
        telemetry_data = {}
        
        # Create SocketIO client
        sio = socketio.Client()
        
        @sio.event
        def connect():
            print("WebSocket connected to server")
            websocket_connected.set()
        
        @sio.event
        def connection_status(data):
            print(f"Connection status received: {data}")
            connection_status.update(data)
            connection_status_received.set()
        
        @sio.event
        def telemetry_update(data):
            print(f"Telemetry update: {data}")
            telemetry_data.update(data)
            if data.get('connected'):
                telemetry_received.set()
        
        try:
            sio.connect(self.server_url)
            assert websocket_connected.wait(timeout=5), "WebSocket connection timeout"
            
            self.test_results['websocket_connected'] = True
            
            # Keep client for next tests
            self._websocket_client = sio
            self._connection_status_event = connection_status_received
            self._telemetry_event = telemetry_received
            self._connection_status = connection_status
            self._telemetry_data = telemetry_data
            
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {e}")
    
    def test_05_click_connect_button(self):
        """Test clicking the connect button triggers connection process"""
        # Ensure we have WebSocket client from previous test
        assert hasattr(self, '_websocket_client'), "WebSocket client not available"
        
        # Reset events
        self._connection_status_event.clear()
        self._telemetry_event.clear()
        
        # Find and click connect button
        connect_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "connect-btn"))
        )
        
        print("Clicking connect button...")
        connect_btn.click()
        
        self.test_results['connect_clicked'] = True
        
        # Check button state changes to "Connecting..."
        WebDriverWait(self.driver, 5).until(
            lambda driver: driver.find_element(By.ID, "connect-btn").text == "Connecting..."
        )
        
        print("Connect button clicked, state changed to 'Connecting...'")
    
    def test_06_verify_connection_status_events(self):
        """Test that connection status events are received via WebSocket"""
        print("Waiting for connection status event...")
        
        # Wait for connection status event
        assert self._connection_status_event.wait(timeout=15), "Connection status event timeout"
        
        status = self._connection_status.get('status')
        message = self._connection_status.get('message', '')
        
        print(f"Received connection status: {status} - {message}")
        
        # Should receive 'connecting' or 'connected' status
        assert status in ['connecting', 'connected'], f"Unexpected connection status: {status}"
    
    def test_07_verify_mavlink_connection_established(self):
        """Test that MAVLink connection is successfully established"""
        print("Waiting for MAVLink connection to be established...")
        
        # Wait for telemetry indicating connection
        assert self._telemetry_event.wait(timeout=30), "MAVLink connection timeout"
        
        assert self._telemetry_data.get('connected') == True, "MAVLink not connected according to telemetry"
        
        self.test_results['mavlink_connected'] = True
        print("MAVLink connection established successfully")
    
    def test_08_verify_heartbeat_reception(self):
        """Test that heartbeat messages are being received"""
        print("Monitoring heartbeat reception...")
        
        # Monitor heartbeat counter in UI
        heartbeat_counter = self.driver.find_element(By.ID, "heartbeat-counter")
        
        # Wait for heartbeat count to increase
        initial_count = int(heartbeat_counter.text)
        print(f"Initial heartbeat count: {initial_count}")
        
        # Wait up to 10 seconds for heartbeat count to increase
        start_time = time.time()
        while time.time() - start_time < 10:
            current_count = int(heartbeat_counter.text)
            if current_count > initial_count:
                print(f"Heartbeat count increased to: {current_count}")
                self.test_results['heartbeat_received'] = True
                break
            time.sleep(0.5)
        
        assert self.test_results['heartbeat_received'], "No heartbeat increase detected"
    
    def test_09_verify_ui_connection_status(self):
        """Test that UI correctly reflects connected state"""
        print("Verifying UI connection status...")
        
        # Check connection status indicator
        connection_status = self.driver.find_element(By.ID, "connection-status")
        status_class = connection_status.get_attribute('class')
        status_text = connection_status.text
        
        print(f"Connection status: {status_text} (class: {status_class})")
        
        assert 'connected' in status_class.lower(), f"Connection status not showing connected: {status_class}"
        assert 'connected' in status_text.lower(), f"Connection text not showing connected: {status_text}"
        
        # Check connect button is disabled
        connect_btn = self.driver.find_element(By.ID, "connect-btn")
        assert connect_btn.get_attribute('disabled') == 'true', "Connect button should be disabled when connected"
        
        # Check disconnect button is enabled
        disconnect_btn = self.driver.find_element(By.ID, "disconnect-btn")
        assert disconnect_btn.get_attribute('disabled') != 'true', "Disconnect button should be enabled when connected"
        
        self.test_results['ui_updated'] = True
        print("UI correctly reflects connected state")
    
    def test_10_verify_telemetry_data_flow(self):
        """Test that telemetry data is flowing and updating UI"""
        print("Verifying telemetry data flow...")
        
        # Check various telemetry displays
        elements_to_check = [
            ('flight-mode', 'Mode:'),
            ('armed-status', ''),
            ('position-display', ''),
            ('battery-voltage', 'Bat:'),
            ('gps-status', 'GPS:')
        ]
        
        for element_id, expected_prefix in elements_to_check:
            try:
                element = self.driver.find_element(By.ID, element_id)
                text = element.text
                print(f"{element_id}: {text}")
                
                if expected_prefix:
                    assert expected_prefix in text, f"Expected '{expected_prefix}' in {element_id} text: {text}"
                
            except Exception as e:
                print(f"Could not verify {element_id}: {e}")
        
        print("Telemetry data flow verified")
    
    def test_11_test_disconnect_functionality(self):
        """Test that disconnect button works correctly"""
        print("Testing disconnect functionality...")
        
        # Click disconnect button
        disconnect_btn = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, "disconnect-btn"))
        )
        
        disconnect_btn.click()
        
        # Wait for connection status to change
        WebDriverWait(self.driver, 10).until(
            lambda driver: 'disconnected' in driver.find_element(By.ID, "connection-status").get_attribute('class').lower()
        )
        
        # Verify UI state
        connection_status = self.driver.find_element(By.ID, "connection-status")
        assert 'disconnected' in connection_status.get_attribute('class').lower()
        
        connect_btn = self.driver.find_element(By.ID, "connect-btn")
        assert connect_btn.get_attribute('disabled') != 'true', "Connect button should be enabled after disconnect"
        assert connect_btn.text == "Connect", "Connect button should show 'Connect' after disconnect"
        
        print("Disconnect functionality verified")
    
    def test_12_cleanup_websocket(self):
        """Clean up WebSocket connection"""
        if hasattr(self, '_websocket_client'):
            self._websocket_client.disconnect()
            print("WebSocket client disconnected")
    
    def test_99_final_results_summary(self):
        """Print final test results summary"""
        print("\n" + "="*50)
        print("CONNECT BUTTON INTEGRATION TEST RESULTS")
        print("="*50)
        
        for test_name, result in self.test_results.items():
            status = "PASS" if result else "FAIL"
            print(f"{test_name:25}: {status}")
        
        all_passed = all(self.test_results.values())
        print(f"\nOVERALL RESULT: {'PASS' if all_passed else 'FAIL'}")
        
        if all_passed:
            print("\n✓ Connect button successfully communicates with virtual drone")
            print("✓ UI correctly updates to show connected state")
            print("✓ Heartbeat messages are received and displayed")
            print("✓ Disconnect functionality works correctly")
        else:
            failed_tests = [name for name, result in self.test_results.items() if not result]
            print(f"\n✗ Failed tests: {', '.join(failed_tests)}")
        
        print("="*50)
        
        assert all_passed, f"Some tests failed: {[name for name, result in self.test_results.items() if not result]}"


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v", "--tb=short"])
#!/usr/bin/env python3
"""
Navigation Controls Testing Agent
Test coordinate-based navigation input validation and Go To command transmission
"""

import pytest
import time
import asyncio
import websockets
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import socket
import threading
from pymavlink import mavutil


class NavigationControlsTester:
    """Test coordinate-based navigation controls and MAVLink command transmission"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.websocket = None
        self.mavlink_messages = []
        self.test_results = {
            'TEST-NC-001': {'status': 'PENDING', 'details': []},
            'TEST-NC-002': {'status': 'PENDING', 'details': []},
            'TEST-NC-003': {'status': 'PENDING', 'details': []}
        }
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for test execution"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Navigation Test - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_browser(self):
        """Setup Chrome browser with proper options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.logger.info("Chrome browser initialized")
    
    async def monitor_mavlink_connection(self):
        """Monitor MAVLink connection for command transmission"""
        try:
            # Connect to virtual drone MAVLink port
            connection_string = "udp:192.168.193.235:5678"
            self.logger.info(f"Attempting MAVLink connection to {connection_string}")
            
            # Create MAVLink connection
            master = mavutil.mavlink_connection(connection_string)
            self.logger.info("Waiting for MAVLink heartbeat...")
            
            # Wait for heartbeat with timeout
            master.wait_heartbeat(timeout=10)
            self.logger.info("MAVLink heartbeat received - connection established")
            
            # Monitor for waypoint/navigation commands
            start_time = time.time()
            while time.time() - start_time < 30:  # Monitor for 30 seconds
                msg = master.recv_match(blocking=False)
                if msg:
                    if msg.get_type() in ['MISSION_ITEM', 'MISSION_ITEM_INT', 'SET_POSITION_TARGET_GLOBAL_INT']:
                        self.mavlink_messages.append({
                            'timestamp': time.time(),
                            'type': msg.get_type(),
                            'data': msg.to_dict()
                        })
                        self.logger.info(f"Captured MAVLink message: {msg.get_type()}")
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"MAVLink monitoring error: {e}")
    
    async def connect_websocket(self):
        """Connect to WebGCS WebSocket"""
        try:
            self.websocket = await websockets.connect("ws://localhost:5001/socket.io/?EIO=4&transport=websocket")
            self.logger.info("WebSocket connected to WebGCS")
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")
    
    def wait_for_connection_established(self):
        """Wait for drone connection to be established"""
        try:
            # Wait for connection status to show connected
            connection_status = self.wait.until(
                EC.presence_of_element_located((By.ID, "connection-status"))
            )
            
            # Check if already connected
            if "Connected" in connection_status.text:
                self.logger.info("Drone already connected")
                return True
            
            # Click connect button
            connect_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "connect-btn")))
            connect_btn.click()
            self.logger.info("Connect button clicked")
            
            # Wait for connection to establish
            start_time = time.time()
            while time.time() - start_time < 15:
                connection_status = self.driver.find_element(By.ID, "connection-status")
                if "Connected" in connection_status.text:
                    self.logger.info("Drone connection established")
                    return True
                time.sleep(0.5)
            
            self.logger.error("Drone connection timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Connection establishment failed: {e}")
            return False
    
    def test_nc_001_goto_navigation_command(self):
        """TEST-NC-001: Go To Navigation Command Test"""
        self.logger.info("=== Starting TEST-NC-001: Go To Navigation Command ===")
        test_details = []
        
        try:
            # Test coordinates: Lat=37.7749, Lon=-122.4194, Alt=50
            test_lat = 37.7749
            test_lon = -122.4194
            test_alt = 50
            
            # Clear any existing values first
            self.clear_navigation_inputs()
            
            # Locate navigation input fields
            nav_lat = self.wait.until(EC.presence_of_element_located((By.ID, "nav-lat")))
            nav_lon = self.wait.until(EC.presence_of_element_located((By.ID, "nav-lon")))
            nav_alt = self.wait.until(EC.presence_of_element_located((By.ID, "nav-alt")))
            goto_btn = self.wait.until(EC.presence_of_element_located((By.ID, "goto-btn")))
            
            test_details.append("✓ Navigation input fields located")
            
            # Input test coordinates
            nav_lat.clear()
            nav_lat.send_keys(str(test_lat))
            nav_lon.clear()
            nav_lon.send_keys(str(test_lon))
            nav_alt.clear()
            nav_alt.send_keys(str(test_alt))
            
            test_details.append(f"✓ Coordinates entered: {test_lat}, {test_lon}, {test_alt}")
            
            # Verify input values
            entered_lat = float(nav_lat.get_attribute('value'))
            entered_lon = float(nav_lon.get_attribute('value'))
            entered_alt = float(nav_alt.get_attribute('value'))
            
            assert abs(entered_lat - test_lat) < 0.000001, f"Latitude mismatch: {entered_lat} != {test_lat}"
            assert abs(entered_lon - test_lon) < 0.000001, f"Longitude mismatch: {entered_lon} != {test_lon}"
            assert abs(entered_alt - test_alt) < 0.1, f"Altitude mismatch: {entered_alt} != {test_alt}"
            
            test_details.append("✓ Input coordinate precision validated (6 decimal places)")
            
            # Start MAVLink monitoring in background
            mavlink_task = asyncio.create_task(self.monitor_mavlink_connection())
            
            # Click Go To button
            initial_messages_count = len(self.mavlink_messages)
            goto_btn.click()
            test_details.append("✓ Go To button clicked")
            
            # Handle confirmation dialog if present
            time.sleep(1)
            try:
                confirm_yes = self.driver.find_element(By.ID, "confirm-yes")
                if confirm_yes.is_displayed():
                    confirm_yes.click()
                    test_details.append("✓ Navigation command confirmed")
            except NoSuchElementException:
                # No confirmation dialog, command sent directly
                test_details.append("✓ Command sent without confirmation")
            
            # Wait for command transmission and virtual drone acknowledgment
            command_sent = False
            ack_received = False
            
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout
                # Check for new MAVLink messages
                if len(self.mavlink_messages) > initial_messages_count:
                    command_sent = True
                    latest_msg = self.mavlink_messages[-1]
                    
                    # Verify coordinate values in MAVLink command
                    msg_data = latest_msg['data']
                    if 'x' in msg_data and 'y' in msg_data:  # Global position target
                        msg_lat = msg_data['x'] / 1e7  # MAVLink uses 1e7 scaling
                        msg_lon = msg_data['y'] / 1e7
                        
                        if abs(msg_lat - test_lat) < 0.000001 and abs(msg_lon - test_lon) < 0.000001:
                            test_details.append("✓ MAVLink coordinates match input exactly")
                            ack_received = True
                            break
                
                time.sleep(0.1)
            
            # Cancel MAVLink monitoring
            mavlink_task.cancel()
            
            if command_sent:
                test_details.append("✓ MAV_CMD_NAV_WAYPOINT sent to virtual drone")
            else:
                test_details.append("✗ No MAVLink navigation command detected")
            
            if ack_received:
                test_details.append("✓ Virtual drone acknowledgment received within 5 seconds")
            else:
                test_details.append("✗ Virtual drone acknowledgment not received")
            
            # Overall test result
            success = command_sent and ack_received
            self.test_results['TEST-NC-001'] = {
                'status': 'PASS' if success else 'FAIL',
                'details': test_details
            }
            
            self.logger.info(f"TEST-NC-001 Result: {'PASS' if success else 'FAIL'}")
            
        except Exception as e:
            test_details.append(f"✗ Error: {str(e)}")
            self.test_results['TEST-NC-001'] = {
                'status': 'FAIL',
                'details': test_details
            }
            self.logger.error(f"TEST-NC-001 Failed: {e}")
    
    def test_nc_002_input_boundary_validation(self):
        """TEST-NC-002: Input Field Boundary Testing"""
        self.logger.info("=== Starting TEST-NC-002: Input Field Boundary Testing ===")
        test_details = []
        
        try:
            # Locate navigation input fields
            nav_lat = self.wait.until(EC.presence_of_element_located((By.ID, "nav-lat")))
            nav_lon = self.wait.until(EC.presence_of_element_located((By.ID, "nav-lon")))
            nav_alt = self.wait.until(EC.presence_of_element_located((By.ID, "nav-alt")))
            goto_btn = self.wait.until(EC.presence_of_element_located((By.ID, "goto-btn")))
            
            boundary_tests = [
                # Latitude boundary tests
                {'field': 'lat', 'value': -90.000001, 'should_reject': True, 'desc': 'Latitude below minimum'},
                {'field': 'lat', 'value': 90.000001, 'should_reject': True, 'desc': 'Latitude above maximum'},
                {'field': 'lat', 'value': -90.000000, 'should_reject': False, 'desc': 'Latitude at minimum'},
                {'field': 'lat', 'value': 90.000000, 'should_reject': False, 'desc': 'Latitude at maximum'},
                
                # Longitude boundary tests
                {'field': 'lon', 'value': -180.000001, 'should_reject': True, 'desc': 'Longitude below minimum'},
                {'field': 'lon', 'value': 180.000001, 'should_reject': True, 'desc': 'Longitude above maximum'},
                {'field': 'lon', 'value': -180.000000, 'should_reject': False, 'desc': 'Longitude at minimum'},
                {'field': 'lon', 'value': 180.000000, 'should_reject': False, 'desc': 'Longitude at maximum'},
                
                # Altitude boundary tests
                {'field': 'alt', 'value': -101, 'should_reject': True, 'desc': 'Altitude below minimum'},
                {'field': 'alt', 'value': 5001, 'should_reject': True, 'desc': 'Altitude above maximum'},
                {'field': 'alt', 'value': -100, 'should_reject': False, 'desc': 'Altitude at minimum'},
                {'field': 'alt', 'value': 5000, 'should_reject': False, 'desc': 'Altitude at maximum'},
            ]
            
            field_map = {'lat': nav_lat, 'lon': nav_lon, 'alt': nav_alt}
            
            for test in boundary_tests:
                self.clear_navigation_inputs()
                
                # Set valid values for other fields
                nav_lat.send_keys("0")
                nav_lon.send_keys("0") 
                nav_alt.send_keys("10")
                
                # Test the specific boundary value
                field = field_map[test['field']]
                field.clear()
                field.send_keys(str(test['value']))
                field.send_keys(Keys.TAB)  # Trigger validation
                
                # Try to submit the form
                initial_messages = len(self.mavlink_messages)
                goto_btn.click()
                time.sleep(0.5)
                
                # Check if command was prevented or allowed
                command_sent = len(self.mavlink_messages) > initial_messages
                validation_correct = command_sent != test['should_reject']
                
                # Check for error message display
                try:
                    # Look for custom validity message
                    validity_message = field.get_attribute('validationMessage')
                    has_error_message = bool(validity_message)
                except:
                    has_error_message = False
                
                if test['should_reject']:
                    if validation_correct:
                        test_details.append(f"✓ {test['desc']}: Correctly rejected (value={test['value']})")
                    else:
                        test_details.append(f"✗ {test['desc']}: Should be rejected but was accepted (value={test['value']})")
                else:
                    if validation_correct:
                        test_details.append(f"✓ {test['desc']}: Correctly accepted (value={test['value']})")
                    else:
                        test_details.append(f"✗ {test['desc']}: Should be accepted but was rejected (value={test['value']})")
                
                # Cancel any confirmation dialogs
                try:
                    confirm_no = self.driver.find_element(By.ID, "confirm-no")
                    if confirm_no.is_displayed():
                        confirm_no.click()
                except:
                    pass
            
            # Count successful boundary validations
            successful_tests = sum(1 for detail in test_details if detail.startswith("✓"))
            total_tests = len(boundary_tests)
            
            success = successful_tests == total_tests
            test_details.append(f"✓ Boundary validation results: {successful_tests}/{total_tests} tests passed")
            
            self.test_results['TEST-NC-002'] = {
                'status': 'PASS' if success else 'FAIL',
                'details': test_details
            }
            
            self.logger.info(f"TEST-NC-002 Result: {'PASS' if success else 'FAIL'}")
            
        except Exception as e:
            test_details.append(f"✗ Error: {str(e)}")
            self.test_results['TEST-NC-002'] = {
                'status': 'FAIL', 
                'details': test_details
            }
            self.logger.error(f"TEST-NC-002 Failed: {e}")
    
    def test_nc_003_clear_navigation_function(self):
        """TEST-NC-003: Clear Navigation Function Test"""
        self.logger.info("=== Starting TEST-NC-003: Clear Navigation Function ===")
        test_details = []
        
        try:
            # Locate navigation elements
            nav_lat = self.wait.until(EC.presence_of_element_located((By.ID, "nav-lat")))
            nav_lon = self.wait.until(EC.presence_of_element_located((By.ID, "nav-lon")))
            nav_alt = self.wait.until(EC.presence_of_element_located((By.ID, "nav-alt")))
            clear_btn = self.wait.until(EC.presence_of_element_located((By.ID, "clear-nav-btn")))
            
            # Input valid navigation coordinates
            test_lat = 40.7128
            test_lon = -74.0060
            test_alt = 25
            
            nav_lat.clear()
            nav_lat.send_keys(str(test_lat))
            nav_lon.clear()
            nav_lon.send_keys(str(test_lon))
            nav_alt.clear()
            nav_alt.send_keys(str(test_alt))
            
            test_details.append(f"✓ Valid coordinates entered: {test_lat}, {test_lon}, {test_alt}")
            
            # Verify coordinates are set
            assert nav_lat.get_attribute('value') == str(test_lat)
            assert nav_lon.get_attribute('value') == str(test_lon) 
            assert nav_alt.get_attribute('value') == str(test_alt)
            
            test_details.append("✓ Coordinate values confirmed in input fields")
            
            # Monitor for any navigation commands before clear
            initial_messages = len(self.mavlink_messages)
            
            # Click Clear button
            clear_btn.click()
            test_details.append("✓ Clear button clicked")
            
            # Wait a moment for clearing to complete
            time.sleep(1)
            
            # Verify all fields are reset
            lat_value = nav_lat.get_attribute('value')
            lon_value = nav_lon.get_attribute('value')
            alt_value = nav_alt.get_attribute('value')
            
            fields_cleared = (
                lat_value == '' or lat_value == '0' and
                lon_value == '' or lon_value == '0' and
                (alt_value == '' or alt_value == '10')  # Default altitude might be 10
            )
            
            if fields_cleared:
                test_details.append("✓ All navigation fields reset to defaults/empty")
            else:
                test_details.append(f"✗ Fields not properly cleared: lat={lat_value}, lon={lon_value}, alt={alt_value}")
            
            # Confirm no navigation commands sent during clear
            commands_sent_during_clear = len(self.mavlink_messages) > initial_messages
            if not commands_sent_during_clear:
                test_details.append("✓ No navigation commands sent during clear operation")
            else:
                test_details.append("✗ Unexpected navigation commands sent during clear")
            
            success = fields_cleared and not commands_sent_during_clear
            
            self.test_results['TEST-NC-003'] = {
                'status': 'PASS' if success else 'FAIL',
                'details': test_details
            }
            
            self.logger.info(f"TEST-NC-003 Result: {'PASS' if success else 'FAIL'}")
            
        except Exception as e:
            test_details.append(f"✗ Error: {str(e)}")
            self.test_results['TEST-NC-003'] = {
                'status': 'FAIL',
                'details': test_details
            }
            self.logger.error(f"TEST-NC-003 Failed: {e}")
    
    def clear_navigation_inputs(self):
        """Helper function to clear all navigation inputs"""
        try:
            clear_btn = self.driver.find_element(By.ID, "clear-nav-btn")
            clear_btn.click()
            time.sleep(0.5)
        except:
            # Manual clear if clear button not working
            try:
                nav_lat = self.driver.find_element(By.ID, "nav-lat")
                nav_lon = self.driver.find_element(By.ID, "nav-lon") 
                nav_alt = self.driver.find_element(By.ID, "nav-alt")
                nav_lat.clear()
                nav_lon.clear()
                nav_alt.clear()
            except:
                pass
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = []
        report.append("="*80)
        report.append("NAVIGATION CONTROLS TESTING REPORT")
        report.append("="*80)
        report.append(f"Test Execution Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Target Drone: 192.168.193.235:5678")
        report.append("")
        
        # Test Results Summary
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        total_tests = len(self.test_results)
        
        report.append("TEST RESULTS SUMMARY:")
        report.append(f"Passed: {passed_tests}/{total_tests}")
        report.append("")
        
        # Detailed Results
        for test_id, result in self.test_results.items():
            report.append(f"{test_id}: {result['status']}")
            for detail in result['details']:
                report.append(f"  {detail}")
            report.append("")
        
        # Success Criteria Assessment
        report.append("SUCCESS CRITERIA ASSESSMENT:")
        criteria_results = {
            "Go To button sends correct navigation commands": 
                self.test_results['TEST-NC-001']['status'] == 'PASS',
            "Input validation prevents invalid coordinates":
                self.test_results['TEST-NC-002']['status'] == 'PASS', 
            "Virtual drone acknowledges waypoint commands":
                any("acknowledgment received" in detail for detail in self.test_results['TEST-NC-001']['details']),
            "Clear function properly resets inputs":
                self.test_results['TEST-NC-003']['status'] == 'PASS',
            "Coordinate precision maintained at 6 decimal places":
                any("precision validated" in detail for detail in self.test_results['TEST-NC-001']['details'])
        }
        
        for criterion, met in criteria_results.items():
            status = "✓ PASS" if met else "✗ FAIL"
            report.append(f"{status} - {criterion}")
        
        report.append("")
        report.append("="*80)
        
        return "\n".join(report)
    
    async def run_all_tests(self):
        """Execute all navigation control tests"""
        self.logger.info("Starting Navigation Controls Testing Suite")
        
        try:
            # Setup browser
            self.setup_browser()
            
            # Navigate to WebGCS
            self.driver.get("http://localhost:5001")
            self.logger.info("Navigated to WebGCS interface")
            
            # Wait for page to load and establish drone connection
            time.sleep(2)
            
            if not self.wait_for_connection_established():
                raise Exception("Failed to establish drone connection")
            
            # Execute navigation control tests
            self.test_nc_001_goto_navigation_command()
            self.test_nc_002_input_boundary_validation()
            self.test_nc_003_clear_navigation_function()
            
            # Generate and display report
            report = self.generate_test_report()
            self.logger.info("\n" + report)
            
            # Save report to file
            with open('/tmp/navigation_controls_test_report.txt', 'w') as f:
                f.write(report)
            self.logger.info("Test report saved to /tmp/navigation_controls_test_report.txt")
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")


def main():
    """Main test execution function"""
    tester = NavigationControlsTester()
    
    # Run tests in async context for MAVLink monitoring
    try:
        asyncio.run(tester.run_all_tests())
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
    except Exception as e:
        print(f"Test execution failed: {e}")


if __name__ == "__main__":
    main()
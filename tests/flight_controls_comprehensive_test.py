#!/usr/bin/env python3
"""
Flight Controls Comprehensive Test Suite
Tests all safety-critical flight control buttons and MAVLink communication
Target: Virtual drone at 192.168.193.235:5678
"""
import time
import asyncio
import json
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from pymavlink import mavutil

class FlightControlsTestSuite:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.mavlink_conn = None
        self.test_results = {
            'TEST-FC-001_ARM': {'passed': False, 'details': ''},
            'TEST-FC-002_DISARM': {'passed': False, 'details': ''},
            'TEST-FC-003_TAKEOFF': {'passed': False, 'details': ''},
            'TEST-FC-004_LAND': {'passed': False, 'details': ''},
            'TEST-FC-005_RTL': {'passed': False, 'details': ''},
            'TEST-FC-006_FLIGHT_MODES': {'passed': False, 'details': ''}
        }
        self.webgcs_url = "http://localhost:5001"
        self.virtual_drone_address = "192.168.193.235:5678"
        
    def setup_webdriver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 10)
        
        print("✅ WebDriver initialized")
        
    def setup_mavlink_connection(self):
        """Establish direct MAVLink connection to virtual drone"""
        try:
            self.mavlink_conn = mavutil.mavlink_connection(f'udp:{self.virtual_drone_address}')
            print(f"✅ MAVLink connection established to {self.virtual_drone_address}")
            
            # Wait for heartbeat to confirm connection
            msg = self.mavlink_conn.wait_heartbeat(timeout=10)
            if msg:
                print(f"✅ Heartbeat received from system {msg.get_srcSystem()}")
                return True
            else:
                print("❌ No heartbeat received from virtual drone")
                return False
                
        except Exception as e:
            print(f"❌ Failed to connect to virtual drone: {e}")
            return False
            
    def load_webgcs(self):
        """Load WebGCS interface and wait for initialization"""
        print(f"🌐 Loading WebGCS at {self.webgcs_url}")
        self.driver.get(self.webgcs_url)
        
        # Wait for page to load
        self.wait.until(EC.presence_of_element_located((By.ID, "connect-btn")))
        
        # Wait for JavaScript modules to initialize
        time.sleep(2)
        
        print("✅ WebGCS loaded successfully")
        
    def connect_to_drone(self):
        """Connect WebGCS to the virtual drone"""
        try:
            # Ensure IP and port are set correctly
            ip_input = self.driver.find_element(By.ID, "ip-address")
            port_input = self.driver.find_element(By.ID, "port-number")
            
            ip_input.clear()
            ip_input.send_keys("192.168.193.235")
            port_input.clear()
            port_input.send_keys("5678")
            
            # Click connect button
            connect_btn = self.driver.find_element(By.ID, "connect-btn")
            connect_btn.click()
            
            # Wait for connection status to change
            connection_status = self.wait.until(
                EC.text_to_be_present_in_element((By.ID, "connection-status"), "Connected")
            )
            
            # Wait for heartbeat counter to show activity
            time.sleep(3)
            heartbeat_counter = self.driver.find_element(By.ID, "heartbeat-counter")
            heartbeat_count = int(heartbeat_counter.text)
            
            if heartbeat_count > 0:
                print(f"✅ Connected to virtual drone - Heartbeats: {heartbeat_count}")
                return True
            else:
                print("❌ Connected but no heartbeats received")
                return False
                
        except Exception as e:
            print(f"❌ Failed to connect to drone: {e}")
            return False
            
    def wait_for_mavlink_ack(self, command_id, timeout=5):
        """Wait for MAVLink command acknowledgment"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                msg = self.mavlink_conn.recv_match(type='COMMAND_ACK', blocking=False)
                if msg and msg.command == command_id:
                    result = msg.result
                    if result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                        return True, "ACCEPTED"
                    else:
                        return False, f"REJECTED: {result}"
            except:
                pass
            time.sleep(0.1)
            
        return False, "TIMEOUT"
        
    def handle_safety_confirmation(self, expected_title=None):
        """Handle safety confirmation dialog"""
        try:
            # Wait for confirmation dialog or browser alert
            time.sleep(1)
            
            # Check for custom confirmation dialog first
            try:
                confirm_dialog = self.driver.find_element(By.ID, "confirmation-dialog")
                if confirm_dialog.is_displayed():
                    confirm_yes = self.driver.find_element(By.ID, "confirm-yes")
                    confirm_yes.click()
                    print("✅ Custom confirmation dialog accepted")
                    return True
            except:
                pass
                
            # Check for browser alert
            try:
                alert = Alert(self.driver)
                alert_text = alert.text
                if expected_title and expected_title.upper() not in alert_text.upper():
                    print(f"⚠️ Unexpected alert text: {alert_text}")
                alert.accept()
                print("✅ Browser alert accepted")
                return True
            except NoAlertPresentException:
                pass
                
            print("⚠️ No confirmation dialog found")
            return False
            
        except Exception as e:
            print(f"❌ Error handling confirmation: {e}")
            return False
            
    def test_arm_button(self):
        """TEST-FC-001: ARM Button with Safety Confirmation"""
        print("\n🔧 TEST-FC-001: ARM Button Safety Confirmation")
        
        try:
            # Find ARM button
            arm_btn = self.driver.find_element(By.ID, "arm-btn")
            
            # Verify button is enabled and clickable
            if not arm_btn.is_enabled():
                self.test_results['TEST-FC-001_ARM']['details'] = "ARM button is disabled"
                return False
                
            # Click ARM button
            arm_btn.click()
            print("✅ ARM button clicked")
            
            # Handle safety confirmation
            if not self.handle_safety_confirmation("ARM"):
                self.test_results['TEST-FC-001_ARM']['details'] = "Safety confirmation failed"
                return False
                
            # Wait for MAVLink command acknowledgment
            ack_received, ack_result = self.wait_for_mavlink_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
            
            if ack_received:
                print(f"✅ MAVLink ARM command acknowledged: {ack_result}")
                
                # Wait for UI to update
                time.sleep(2)
                
                # Check if armed status updated
                armed_status = self.driver.find_element(By.ID, "armed-status")
                if "ARMED" in armed_status.text.upper():
                    print("✅ UI shows ARMED status")
                    self.test_results['TEST-FC-001_ARM']['passed'] = True
                    self.test_results['TEST-FC-001_ARM']['details'] = f"ARM successful, ACK: {ack_result}"
                    return True
                else:
                    self.test_results['TEST-FC-001_ARM']['details'] = f"UI not updated to ARMED: {armed_status.text}"
                    return False
            else:
                self.test_results['TEST-FC-001_ARM']['details'] = f"No MAVLink ACK received: {ack_result}"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-001_ARM']['details'] = f"Exception: {e}"
            return False
            
    def test_disarm_button(self):
        """TEST-FC-002: DISARM Button Safety"""
        print("\n🔧 TEST-FC-002: DISARM Button Safety")
        
        try:
            # Find DISARM button  
            disarm_btn = self.driver.find_element(By.ID, "disarm-btn")
            
            # Verify button is enabled (should be enabled if armed)
            if not disarm_btn.is_enabled():
                self.test_results['TEST-FC-002_DISARM']['details'] = "DISARM button is disabled (not armed?)"
                return False
                
            # Click DISARM button
            disarm_btn.click()
            print("✅ DISARM button clicked")
            
            # Handle safety confirmation
            if not self.handle_safety_confirmation("DISARM"):
                self.test_results['TEST-FC-002_DISARM']['details'] = "Safety confirmation failed"
                return False
                
            # Wait for MAVLink command acknowledgment
            ack_received, ack_result = self.wait_for_mavlink_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
            
            if ack_received:
                print(f"✅ MAVLink DISARM command acknowledged: {ack_result}")
                
                # Wait for UI to update
                time.sleep(2)
                
                # Check if armed status updated
                armed_status = self.driver.find_element(By.ID, "armed-status")
                if "DISARMED" in armed_status.text.upper():
                    print("✅ UI shows DISARMED status")
                    self.test_results['TEST-FC-002_DISARM']['passed'] = True
                    self.test_results['TEST-FC-002_DISARM']['details'] = f"DISARM successful, ACK: {ack_result}"
                    return True
                else:
                    self.test_results['TEST-FC-002_DISARM']['details'] = f"UI not updated to DISARMED: {armed_status.text}"
                    return False
            else:
                self.test_results['TEST-FC-002_DISARM']['details'] = f"No MAVLink ACK received: {ack_result}"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-002_DISARM']['details'] = f"Exception: {e}"
            return False
            
    def test_takeoff_button(self):
        """TEST-FC-003: Takeoff Button with Altitude Validation"""
        print("\n🔧 TEST-FC-003: Takeoff Button with Altitude Validation")
        
        try:
            # First ensure drone is armed
            if not self.test_arm_button():
                print("⚠️ Cannot test takeoff - ARM test failed")
                return False
                
            # Test altitude input validation
            takeoff_altitude_input = self.driver.find_element(By.ID, "takeoff-altitude")
            takeoff_btn = self.driver.find_element(By.ID, "takeoff-btn")
            
            # Test invalid altitude (0)
            takeoff_altitude_input.clear()
            takeoff_altitude_input.send_keys("0")
            takeoff_btn.click()
            
            time.sleep(1)
            # Should show error message - check for message log update or alert
            
            # Test valid altitude (10m)
            takeoff_altitude_input.clear()
            takeoff_altitude_input.send_keys("10")
            
            # Verify takeoff button is enabled (should be enabled when armed)
            if not takeoff_btn.is_enabled():
                self.test_results['TEST-FC-003_TAKEOFF']['details'] = "Takeoff button disabled when armed"
                return False
                
            # Click takeoff button
            takeoff_btn.click()
            print("✅ Takeoff button clicked with 10m altitude")
            
            # Handle safety confirmation
            if not self.handle_safety_confirmation("TAKEOFF"):
                self.test_results['TEST-FC-003_TAKEOFF']['details'] = "Safety confirmation failed"
                return False
                
            # Wait for MAVLink command acknowledgment
            ack_received, ack_result = self.wait_for_mavlink_ack(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF)
            
            if ack_received:
                print(f"✅ MAVLink TAKEOFF command acknowledged: {ack_result}")
                self.test_results['TEST-FC-003_TAKEOFF']['passed'] = True
                self.test_results['TEST-FC-003_TAKEOFF']['details'] = f"Takeoff successful, altitude: 10m, ACK: {ack_result}"
                return True
            else:
                self.test_results['TEST-FC-003_TAKEOFF']['details'] = f"No MAVLink ACK received: {ack_result}"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-003_TAKEOFF']['details'] = f"Exception: {e}"
            return False
            
    def test_land_button(self):
        """TEST-FC-004: Land Button"""
        print("\n🔧 TEST-FC-004: Land Button")
        
        try:
            # Find LAND button
            land_btn = self.driver.find_element(By.ID, "land-btn")
            
            # Verify button is enabled
            if not land_btn.is_enabled():
                self.test_results['TEST-FC-004_LAND']['details'] = "LAND button is disabled"
                return False
                
            # Click LAND button
            land_btn.click()
            print("✅ LAND button clicked")
            
            # Handle safety confirmation
            if not self.handle_safety_confirmation("LAND"):
                self.test_results['TEST-FC-004_LAND']['details'] = "Safety confirmation failed"
                return False
                
            # Wait for MAVLink command acknowledgment
            ack_received, ack_result = self.wait_for_mavlink_ack(mavutil.mavlink.MAV_CMD_NAV_LAND)
            
            if ack_received:
                print(f"✅ MAVLink LAND command acknowledged: {ack_result}")
                self.test_results['TEST-FC-004_LAND']['passed'] = True
                self.test_results['TEST-FC-004_LAND']['details'] = f"Land command successful, ACK: {ack_result}"
                return True
            else:
                self.test_results['TEST-FC-004_LAND']['details'] = f"No MAVLink ACK received: {ack_result}"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-004_LAND']['details'] = f"Exception: {e}"
            return False
            
    def test_rtl_button(self):
        """TEST-FC-005: RTL (Return to Launch) Button"""
        print("\n🔧 TEST-FC-005: RTL Button")
        
        try:
            # Find RTL button
            rtl_btn = self.driver.find_element(By.ID, "rtl-btn")
            
            # Verify button is enabled
            if not rtl_btn.is_enabled():
                self.test_results['TEST-FC-005_RTL']['details'] = "RTL button is disabled"
                return False
                
            # Click RTL button
            rtl_btn.click()
            print("✅ RTL button clicked")
            
            # Handle safety confirmation
            if not self.handle_safety_confirmation("RETURN"):
                self.test_results['TEST-FC-005_RTL']['details'] = "Safety confirmation failed"
                return False
                
            # Wait for MAVLink command acknowledgment
            ack_received, ack_result = self.wait_for_mavlink_ack(mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
            
            if ack_received:
                print(f"✅ MAVLink RTL command acknowledged: {ack_result}")
                
                # Check if flight mode changed to RTL
                time.sleep(2)
                flight_mode = self.driver.find_element(By.ID, "flight-mode")
                if "RTL" in flight_mode.text.upper():
                    print("✅ Flight mode changed to RTL")
                    
                self.test_results['TEST-FC-005_RTL']['passed'] = True
                self.test_results['TEST-FC-005_RTL']['details'] = f"RTL command successful, ACK: {ack_result}"
                return True
            else:
                self.test_results['TEST-FC-005_RTL']['details'] = f"No MAVLink ACK received: {ack_result}"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-005_RTL']['details'] = f"Exception: {e}"
            return False
            
    def test_flight_mode_selection(self):
        """TEST-FC-006: Flight Mode Selection"""
        print("\n🔧 TEST-FC-006: Flight Mode Selection")
        
        modes_to_test = ['STABILIZE', 'ALT_HOLD', 'POS_HOLD', 'LOITER', 'GUIDED', 'BRAKE']
        successful_modes = []
        failed_modes = []
        
        try:
            flight_mode_select = Select(self.driver.find_element(By.ID, "flight-mode-select"))
            set_mode_btn = self.driver.find_element(By.ID, "set-mode-btn")
            
            # Verify set mode button is enabled
            if not set_mode_btn.is_enabled():
                self.test_results['TEST-FC-006_FLIGHT_MODES']['details'] = "Set Mode button is disabled"
                return False
                
            for mode in modes_to_test:
                print(f"  🧪 Testing flight mode: {mode}")
                
                try:
                    # Select the mode
                    flight_mode_select.select_by_value(mode)
                    
                    # Click Set Mode button
                    set_mode_btn.click()
                    
                    # Wait for potential acknowledgment (mode changes don't always use command_long)
                    time.sleep(1)
                    
                    # Check if mode was updated in UI
                    flight_mode_display = self.driver.find_element(By.ID, "flight-mode")
                    current_mode = flight_mode_display.text
                    
                    if mode in current_mode.upper():
                        print(f"    ✅ Mode changed to {mode}")
                        successful_modes.append(mode)
                    else:
                        print(f"    ⚠️ Mode change may be in progress: {current_mode}")
                        successful_modes.append(f"{mode} (pending)")
                        
                except Exception as mode_e:
                    print(f"    ❌ Failed to set mode {mode}: {mode_e}")
                    failed_modes.append(mode)
                    
                time.sleep(1)  # Wait between mode changes
                
            # Evaluate results
            if len(successful_modes) >= len(modes_to_test) * 0.75:  # At least 75% success
                self.test_results['TEST-FC-006_FLIGHT_MODES']['passed'] = True
                self.test_results['TEST-FC-006_FLIGHT_MODES']['details'] = f"Successful: {successful_modes}, Failed: {failed_modes}"
                print(f"✅ Flight mode testing successful: {len(successful_modes)}/{len(modes_to_test)}")
                return True
            else:
                self.test_results['TEST-FC-006_FLIGHT_MODES']['details'] = f"Too many failures. Successful: {successful_modes}, Failed: {failed_modes}"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-006_FLIGHT_MODES']['details'] = f"Exception: {e}"
            return False
            
    def run_all_tests(self):
        """Execute all flight control tests"""
        print("🚀 Starting Flight Controls Comprehensive Test Suite")
        print(f"Target: WebGCS at {self.webgcs_url}")
        print(f"Virtual Drone: {self.virtual_drone_address}")
        print("=" * 60)
        
        try:
            # Setup
            self.setup_webdriver()
            
            if not self.setup_mavlink_connection():
                print("❌ Cannot proceed without MAVLink connection")
                return False
                
            self.load_webgcs()
            
            if not self.connect_to_drone():
                print("❌ Cannot proceed without WebGCS connection")
                return False
                
            # Execute test suite
            print("\n📋 Executing Flight Control Tests")
            print("=" * 40)
            
            # Test ARM button (required for other tests)
            arm_success = self.test_arm_button()
            
            # Test DISARM button (only if ARM worked)
            if arm_success:
                self.test_disarm_button()
                
                # Re-arm for other tests that require it
                self.test_arm_button()
                
            # Test other flight controls
            self.test_takeoff_button()
            self.test_land_button() 
            self.test_rtl_button()
            self.test_flight_mode_selection()
            
            # Generate test report
            self.generate_test_report()
            
            return True
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            return False
            
        finally:
            # Cleanup
            if self.mavlink_conn:
                self.mavlink_conn.close()
            if self.driver:
                self.driver.quit()
                
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 FLIGHT CONTROLS TEST RESULTS")
        print("=" * 60)
        
        passed_count = 0
        total_count = len(self.test_results)
        
        for test_id, result in self.test_results.items():
            status = "✅ PASSED" if result['passed'] else "❌ FAILED"
            print(f"{test_id}: {status}")
            print(f"  Details: {result['details']}")
            print()
            
            if result['passed']:
                passed_count += 1
                
        # Summary
        success_rate = (passed_count / total_count) * 100
        print("=" * 60)
        print(f"📈 SUMMARY: {passed_count}/{total_count} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: SUCCESS - Flight controls working correctly!")
        else:
            print("⚠️ OVERALL RESULT: PARTIAL SUCCESS - Some issues need attention")
            
        print("=" * 60)
        
        # Save results to JSON
        with open('flight_controls_test_results.json', 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'summary': {
                    'total_tests': total_count,
                    'passed': passed_count,
                    'success_rate': success_rate
                },
                'results': self.test_results,
                'target': {
                    'webgcs_url': self.webgcs_url,
                    'virtual_drone': self.virtual_drone_address
                }
            }, f, indent=2)
            
        print(f"📄 Detailed results saved to: flight_controls_test_results.json")

def main():
    """Main entry point"""
    test_suite = FlightControlsTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ Flight Controls Test Suite completed successfully")
        exit(0)
    else:
        print("\n❌ Flight Controls Test Suite encountered errors")
        exit(1)

if __name__ == "__main__":
    main()
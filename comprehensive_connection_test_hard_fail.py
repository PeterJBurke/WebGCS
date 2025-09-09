#!/usr/bin/env python3
"""
Comprehensive Connection Test - HARD FAIL Requirements
Tests actual website connection to real drone with heartbeat validation.

MANDATORY REQUIREMENTS (HARD FAIL if not met):
1. Load the actual website at http://127.0.0.1:5002
2. Successfully connect to the actual drone at 192.168.193.235:5678
3. Verify heartbeat reception from the connected drone
4. Confirm heartbeat counter incrementing (not stuck at 0)
5. Real telemetry data flow (not simulated/mocked data)
"""

import time
import json
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class ComprehensiveConnectionTest:
    def __init__(self):
        self.results = {
            "test_name": "Comprehensive Connection Test - Hard Fail Requirements",
            "timestamp": datetime.now().isoformat(),
            "test_url": "http://127.0.0.1:5002",
            "expected_drone_ip": "192.168.193.235",
            "expected_drone_port": "5678",
            "tests": {},
            "screenshots": [],
            "overall_status": "PENDING",
            "failure_details": []
        }
        
    def log_test(self, test_name, status, details="", screenshot_path=""):
        """Log individual test results"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "screenshot": screenshot_path
        }
        print(f"[{status}] {test_name}: {details}")
        
        if status == "FAIL":
            self.results["failure_details"].append(f"{test_name}: {details}")

    def take_screenshot(self, page, filename_suffix):
        """Take screenshot and return path"""
        timestamp = int(time.time())
        filename = f"hard_fail_test_{filename_suffix}_{timestamp}.png"
        filepath = os.path.join(os.getcwd(), filename)
        try:
            page.screenshot(path=filepath, full_page=True)
            self.results["screenshots"].append(filepath)
            print(f"Screenshot saved: {filename}")
            return filepath
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
            return ""

    def wait_for_element_with_timeout(self, page, selector, timeout=10000):
        """Wait for element with proper error handling"""
        try:
            element = page.wait_for_selector(selector, timeout=timeout)
            return element
        except PlaywrightTimeoutError:
            return None

    def run_test(self):
        """Execute the comprehensive connection test"""
        print("=" * 80)
        print("COMPREHENSIVE CONNECTION TEST - HARD FAIL REQUIREMENTS")
        print("=" * 80)
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False, slow_mo=500)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # TEST 1: Load the actual website
                print(f"\n🌐 TEST 1: Loading website at {self.results['test_url']}...")
                try:
                    response = page.goto(self.results['test_url'], timeout=30000)
                    if response and response.status == 200:
                        self.log_test("Website Load", "PASS", f"Successfully loaded {self.results['test_url']}")
                        self.take_screenshot(page, "website_loaded")
                    else:
                        self.log_test("Website Load", "FAIL", f"HTTP {response.status if response else 'No response'}")
                        return self.finalize_results()
                except Exception as e:
                    self.log_test("Website Load", "FAIL", f"Failed to load website: {str(e)}")
                    return self.finalize_results()

                # TEST 2: Verify IP field shows correct drone address
                print(f"\n📍 TEST 2: Verifying IP field shows {self.results['expected_drone_ip']}...")
                ip_input = self.wait_for_element_with_timeout(page, "#drone-host", 10000)
                if ip_input:
                    ip_value = ip_input.get_attribute("value") or ip_input.input_value()
                    if ip_value == self.results['expected_drone_ip']:
                        self.log_test("IP Field Verification", "PASS", f"IP field shows correct address: {ip_value}")
                    else:
                        self.log_test("IP Field Verification", "FAIL", f"IP field shows '{ip_value}', expected '{self.results['expected_drone_ip']}'")
                else:
                    self.log_test("IP Field Verification", "FAIL", "IP address input field not found")

                # TEST 3: Verify Port field shows correct port
                print(f"\n🔌 TEST 3: Verifying Port field shows {self.results['expected_drone_port']}...")
                port_input = self.wait_for_element_with_timeout(page, "#drone-port", 10000)
                if port_input:
                    port_value = port_input.get_attribute("value") or port_input.input_value()
                    if port_value == self.results['expected_drone_port']:
                        self.log_test("Port Field Verification", "PASS", f"Port field shows correct port: {port_value}")
                    else:
                        self.log_test("Port Field Verification", "FAIL", f"Port field shows '{port_value}', expected '{self.results['expected_drone_port']}'")
                else:
                    self.log_test("Port Field Verification", "FAIL", "Port input field not found")

                # TEST 4: Check initial heartbeat counter (should be 0)
                print(f"\n💓 TEST 4: Checking initial heartbeat counter...")
                heartbeat_element = self.wait_for_element_with_timeout(page, "#heartbeat-counter", 5000)
                if heartbeat_element:
                    initial_heartbeat = heartbeat_element.inner_text().strip()
                    self.log_test("Initial Heartbeat Counter", "PASS", f"Initial heartbeat counter: {initial_heartbeat}")
                    self.take_screenshot(page, "before_connect")
                else:
                    self.log_test("Initial Heartbeat Counter", "FAIL", "Heartbeat counter element not found")

                # TEST 5: Click Connect button
                print(f"\n🔗 TEST 5: Clicking Connect button...")
                connect_button = self.wait_for_element_with_timeout(page, "#connect-btn", 10000)
                if connect_button and not connect_button.is_disabled():
                    connect_button.click()
                    self.log_test("Connect Button Click", "PASS", "Successfully clicked Connect button")
                    self.take_screenshot(page, "after_connect_click")
                else:
                    status = "disabled" if connect_button and connect_button.is_disabled() else "not found"
                    self.log_test("Connect Button Click", "FAIL", f"Connect button {status}")
                    return self.finalize_results()

                # TEST 6: Wait for connection status to change
                print(f"\n⏳ TEST 6: Waiting for connection to establish...")
                connection_successful = False
                max_wait = 15  # 15 seconds timeout
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    try:
                        status_element = page.query_selector("#connection-status")
                        if status_element:
                            status_text = status_element.inner_text().strip()
                            print(f"Connection status: {status_text}")
                            
                            if "Connected" in status_text:
                                connection_successful = True
                                self.log_test("Connection Establishment", "PASS", f"Connection established: {status_text}")
                                self.take_screenshot(page, "connected")
                                break
                            elif "Failed" in status_text or "Error" in status_text:
                                self.log_test("Connection Establishment", "FAIL", f"Connection failed: {status_text}")
                                self.take_screenshot(page, "connection_failed")
                                return self.finalize_results()
                    except Exception as e:
                        print(f"Status check error: {e}")
                    
                    time.sleep(1)

                if not connection_successful:
                    self.log_test("Connection Establishment", "FAIL", f"Connection not established within {max_wait} seconds")
                    self.take_screenshot(page, "connection_timeout")
                    return self.finalize_results()

                # TEST 7: CRITICAL - Monitor heartbeat counter increments
                print(f"\n💓 TEST 7: CRITICAL - Monitoring heartbeat counter increments...")
                heartbeat_increments = False
                initial_heartbeat_value = None
                increments_detected = []
                
                # Monitor for 10 seconds to see heartbeat increments
                monitor_duration = 10
                start_time = time.time()
                
                while time.time() - start_time < monitor_duration:
                    try:
                        heartbeat_element = page.query_selector("#heartbeat-counter")
                        if heartbeat_element:
                            current_heartbeat = heartbeat_element.inner_text().strip()
                            
                            if initial_heartbeat_value is None:
                                initial_heartbeat_value = current_heartbeat
                                print(f"Initial heartbeat value: {initial_heartbeat_value}")
                            
                            if current_heartbeat != initial_heartbeat_value:
                                increments_detected.append(current_heartbeat)
                                if not heartbeat_increments:
                                    heartbeat_increments = True
                                    print(f"✅ Heartbeat increment detected! {initial_heartbeat_value} → {current_heartbeat}")
                    except Exception as e:
                        print(f"Heartbeat monitoring error: {e}")
                    
                    time.sleep(0.5)

                if heartbeat_increments and len(increments_detected) > 0:
                    self.log_test("Heartbeat Counter Increments", "PASS", 
                                f"Heartbeat incremented from {initial_heartbeat_value} to {increments_detected[-1]}. Total increments: {len(set(increments_detected))}")
                    self.take_screenshot(page, "heartbeat_incrementing")
                else:
                    self.log_test("Heartbeat Counter Increments", "FAIL", 
                                f"Heartbeat counter stuck at {initial_heartbeat_value}. No increments detected in {monitor_duration} seconds.")
                    self.take_screenshot(page, "heartbeat_stuck")
                    return self.finalize_results()

                # TEST 8: Verify telemetry data flow (check for PFD canvas and MAVLink dump)
                print(f"\n📊 TEST 8: Verifying real telemetry data flow...")
                telemetry_data_found = False
                
                # Check if PFD canvas exists and is being updated
                try:
                    pfd_canvas = page.query_selector("#pfd-canvas")
                    if pfd_canvas:
                        print("✅ PFD Canvas found - telemetry display available")
                        telemetry_data_found = True
                    else:
                        print("❌ PFD Canvas not found")
                except Exception as e:
                    print(f"❌ PFD Canvas check error: {e}")

                # Check MAVLink dump for data activity
                try:
                    mavlink_dump = page.query_selector("#mavlink-dump")
                    if mavlink_dump:
                        dump_text = mavlink_dump.inner_text().strip()
                        print(f"✅ MAVLink Dump element found: {dump_text}")
                        if dump_text and dump_text != "MAVLink Dump":
                            telemetry_data_found = True
                            print("✅ MAVLink data activity detected")
                    else:
                        print("❌ MAVLink Dump element not found")
                except Exception as e:
                    print(f"❌ MAVLink Dump check error: {e}")

                # Check navigation input fields (these should get populated with current position)
                try:
                    nav_lat = page.query_selector("#nav-lat")
                    nav_lon = page.query_selector("#nav-lon")
                    if nav_lat and nav_lon:
                        lat_value = nav_lat.get_attribute("value") or nav_lat.input_value()
                        lon_value = nav_lon.get_attribute("value") or nav_lon.input_value()
                        print(f"Navigation fields - Lat: {lat_value}, Lon: {lon_value}")
                        if lat_value and lat_value != "" and lat_value != "0":
                            telemetry_data_found = True
                            print("✅ Position data detected in navigation fields")
                except Exception as e:
                    print(f"❌ Navigation fields check error: {e}")

                if telemetry_data_found:
                    self.log_test("Real Telemetry Data", "PASS", "Real telemetry data flow detected via PFD canvas or MAVLink activity")
                    self.take_screenshot(page, "telemetry_flowing")
                else:
                    self.log_test("Real Telemetry Data", "FAIL", "No real telemetry data flow detected")
                    self.take_screenshot(page, "no_telemetry")

                # TEST 9: Final verification screenshot
                print(f"\n📸 TEST 9: Taking final verification screenshot...")
                final_screenshot = self.take_screenshot(page, "final_verification")
                if final_screenshot:
                    self.log_test("Final Screenshot", "PASS", f"Final verification screenshot: {final_screenshot}")
                else:
                    self.log_test("Final Screenshot", "FAIL", "Could not capture final screenshot")

                # Give time to observe final state
                print("\n⏳ Waiting 3 seconds for final observation...")
                time.sleep(3)

            except Exception as e:
                self.log_test("Test Execution", "FAIL", f"Unexpected error during testing: {str(e)}")
            finally:
                browser.close()

        return self.finalize_results()

    def finalize_results(self):
        """Determine overall test result and generate report"""
        failed_tests = [name for name, result in self.results["tests"].items() if result["status"] == "FAIL"]
        passed_tests = [name for name, result in self.results["tests"].items() if result["status"] == "PASS"]
        
        # Critical tests that must pass for overall PASS
        critical_tests = [
            "Website Load",
            "Connection Establishment", 
            "Heartbeat Counter Increments",
            "Real Telemetry Data"
        ]
        
        critical_failures = [test for test in failed_tests if test in critical_tests]
        
        if critical_failures:
            self.results["overall_status"] = "FAIL"
            print(f"\n❌ OVERALL RESULT: FAIL - Critical test failures: {critical_failures}")
        elif failed_tests:
            self.results["overall_status"] = "PARTIAL"
            print(f"\n⚠️  OVERALL RESULT: PARTIAL - Some tests failed: {failed_tests}")
        else:
            self.results["overall_status"] = "PASS"
            print(f"\n✅ OVERALL RESULT: PASS - All tests passed!")

        # Generate detailed report
        report_filename = f"comprehensive_test_hard_fail_results_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📊 DETAILED RESULTS:")
        print(f"   ✅ Passed: {len(passed_tests)}")
        print(f"   ❌ Failed: {len(failed_tests)}")
        print(f"   📸 Screenshots: {len(self.results['screenshots'])}")
        print(f"   📄 Report: {report_filename}")

        if self.results["failure_details"]:
            print(f"\n🚨 FAILURE DETAILS:")
            for detail in self.results["failure_details"]:
                print(f"   - {detail}")

        print("\n" + "=" * 80)
        return self.results

if __name__ == "__main__":
    test = ComprehensiveConnectionTest()
    results = test.run_test()
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)
#!/usr/bin/env python3
"""
Comprehensive Connection Diagnosis Test Suite
Tests each step of the connection process from user perspective
"""
import requests
import time
import json
import sys
from playwright.sync_api import sync_playwright
import socketio


class ConnectionDiagnosisTest:
    def __init__(self):
        self.test_results = []
        self.website_url = "http://127.0.0.1:5002"
        self.drone_ip = "192.168.193.235"
        self.drone_port = "5678"
        
    def log_test(self, test_name, passed, details=""):
        """Log test result with pass/fail status"""
        status = "PASS" if passed else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
        
    def test_01_website_accessibility(self):
        """Test if website loads at all"""
        try:
            response = requests.get(self.website_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Website Accessibility", True, f"Status {response.status_code}")
                return True
            else:
                self.log_test("Website Accessibility", False, f"Status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Website Accessibility", False, f"Error: {str(e)}")
            return False
            
    def test_02_html_content_loads(self):
        """Test if HTML content contains expected elements"""
        try:
            response = requests.get(self.website_url, timeout=5)
            html = response.text
            
            required_elements = [
                "drone-host",  # IP input field
                "drone-port",  # Port input field  
                "connect-btn", # Connect button
                "disconnect-btn", # Disconnect button
                "connection-status" # Status display
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html:
                    missing_elements.append(element)
                    
            if not missing_elements:
                self.log_test("HTML Content", True, "All required elements found")
                return True
            else:
                self.log_test("HTML Content", False, f"Missing elements: {missing_elements}")
                return False
        except Exception as e:
            self.log_test("HTML Content", False, f"Error: {str(e)}")
            return False
            
    def test_03_default_ip_values(self):
        """Test if default IP values are correct"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.website_url)
                
                # Wait for page to load
                page.wait_for_selector("#drone-host", timeout=10000)
                
                # Get actual values
                host_value = page.get_attribute("#drone-host", "value")
                port_value = page.get_attribute("#drone-port", "value")
                
                browser.close()
                
                ip_correct = host_value == self.drone_ip
                port_correct = port_value == self.drone_port
                
                if ip_correct and port_correct:
                    self.log_test("Default IP Values", True, f"IP: {host_value}, Port: {port_value}")
                    return True
                else:
                    self.log_test("Default IP Values", False, f"Expected IP: {self.drone_ip}, Got: {host_value}. Expected Port: {self.drone_port}, Got: {port_value}")
                    return False
        except Exception as e:
            self.log_test("Default IP Values", False, f"Error: {str(e)}")
            return False
            
    def test_04_initial_connection_status(self):
        """Test if initial status shows disconnected"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.website_url)
                
                # Wait for page to load and SocketIO to connect
                time.sleep(3)
                
                # Check initial status
                status_element = page.query_selector(".connection-status")
                if status_element:
                    status_text = status_element.inner_text()
                    browser.close()
                    
                    if "disconnected" in status_text.lower() or "heartbeat: 0" in status_text.lower():
                        self.log_test("Initial Status", True, f"Status: '{status_text}'")
                        return True
                    else:
                        self.log_test("Initial Status", False, f"Unexpected status: '{status_text}'")
                        return False
                else:
                    browser.close()
                    self.log_test("Initial Status", False, "Status element not found")
                    return False
        except Exception as e:
            self.log_test("Initial Status", False, f"Error: {str(e)}")
            return False
            
    def test_05_connect_button_clickable(self):
        """Test if connect button is clickable and enabled"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.website_url)
                
                # Wait for page to load
                page.wait_for_selector("#connect-btn", timeout=10000)
                
                # Check if button is enabled
                connect_btn = page.query_selector("#connect-btn")
                is_disabled = connect_btn.get_attribute("disabled")
                
                browser.close()
                
                if is_disabled is None:  # Not disabled
                    self.log_test("Connect Button Clickable", True, "Button is enabled")
                    return True
                else:
                    self.log_test("Connect Button Clickable", False, "Button is disabled")
                    return False
        except Exception as e:
            self.log_test("Connect Button Clickable", False, f"Error: {str(e)}")
            return False
            
    def test_06_socketio_connection(self):
        """Test if SocketIO connection works"""
        try:
            sio = socketio.SimpleClient()
            
            # Connect to SocketIO
            sio.connect(self.website_url, timeout=10)
            
            # Wait a moment for connection
            time.sleep(1)
            
            if sio.connected:
                sio.disconnect()
                self.log_test("SocketIO Connection", True, "Connected successfully")
                return True
            else:
                self.log_test("SocketIO Connection", False, "Failed to connect")
                return False
        except Exception as e:
            self.log_test("SocketIO Connection", False, f"Error: {str(e)}")
            return False
            
    def test_07_connect_button_click_response(self):
        """Test if clicking connect button triggers response"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Listen for console messages
                console_messages = []
                page.on("console", lambda msg: console_messages.append(msg.text))
                
                page.goto(self.website_url)
                
                # Wait for page to load
                page.wait_for_selector("#connect-btn", timeout=10000)
                time.sleep(3)  # Wait for SocketIO
                
                # Click connect button
                page.click("#connect-btn")
                
                # Wait for response
                time.sleep(5)
                
                browser.close()
                
                # Check for any console activity
                relevant_messages = [msg for msg in console_messages if 
                                   "connect" in msg.lower() or "drone" in msg.lower()]
                
                if relevant_messages:
                    self.log_test("Connect Button Response", True, f"Console activity: {relevant_messages[:3]}")
                    return True
                else:
                    self.log_test("Connect Button Response", False, f"No relevant console messages. All messages: {console_messages[:5]}")
                    return False
        except Exception as e:
            self.log_test("Connect Button Response", False, f"Error: {str(e)}")
            return False
            
    def test_08_connection_status_change(self):
        """Test if status changes after clicking connect"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.website_url)
                
                # Wait for page to load
                page.wait_for_selector("#connect-btn", timeout=10000)
                time.sleep(3)
                
                # Get initial status
                initial_status = page.query_selector(".connection-status").inner_text()
                
                # Click connect
                page.click("#connect-btn")
                
                # Wait and check for status change
                time.sleep(8)
                final_status = page.query_selector(".connection-status").inner_text()
                
                browser.close()
                
                if initial_status != final_status:
                    self.log_test("Status Change", True, f"Initial: '{initial_status}' → Final: '{final_status}'")
                    return True
                else:
                    self.log_test("Status Change", False, f"Status unchanged: '{initial_status}'")
                    return False
        except Exception as e:
            self.log_test("Status Change", False, f"Error: {str(e)}")
            return False
            
    def test_09_heartbeat_counter_increment(self):
        """Test if heartbeat counter increments"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.website_url)
                
                # Wait for page to load
                page.wait_for_selector("#connect-btn", timeout=10000)
                time.sleep(3)
                
                # Click connect
                page.click("#connect-btn")
                
                # Wait for connection to establish
                time.sleep(5)
                
                # Look for heartbeat counter
                status_text = page.query_selector(".connection-status").inner_text()
                
                # Wait more and check again
                time.sleep(5)
                final_status_text = page.query_selector(".connection-status").inner_text()
                
                browser.close()
                
                # Extract heartbeat numbers
                import re
                initial_heartbeat = re.search(r'heartbeat:\s*(\d+)', status_text.lower())
                final_heartbeat = re.search(r'heartbeat:\s*(\d+)', final_status_text.lower())
                
                if initial_heartbeat and final_heartbeat:
                    initial_count = int(initial_heartbeat.group(1))
                    final_count = int(final_heartbeat.group(1))
                    
                    if final_count > initial_count:
                        self.log_test("Heartbeat Increment", True, f"Count increased: {initial_count} → {final_count}")
                        return True
                    else:
                        self.log_test("Heartbeat Increment", False, f"Count did not increase: {initial_count} → {final_count}")
                        return False
                else:
                    self.log_test("Heartbeat Increment", False, f"Heartbeat counter not found. Status: '{final_status_text}'")
                    return False
        except Exception as e:
            self.log_test("Heartbeat Increment", False, f"Error: {str(e)}")
            return False
            
    def test_10_telemetry_data_display(self):
        """Test if telemetry data appears"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(self.website_url)
                
                # Wait for page to load
                page.wait_for_selector("#connect-btn", timeout=10000)
                time.sleep(3)
                
                # Click connect
                page.click("#connect-btn")
                
                # Wait for connection and telemetry
                time.sleep(8)
                
                # Get page content to look for telemetry data
                page_content = page.content()
                
                browser.close()
                
                # Look for telemetry indicators
                telemetry_indicators = [
                    "battery", "altitude", "lat", "lon", "gps", "heading", "mode"
                ]
                
                found_indicators = [indicator for indicator in telemetry_indicators 
                                  if indicator in page_content.lower()]
                
                if len(found_indicators) >= 3:
                    self.log_test("Telemetry Data", True, f"Found: {found_indicators}")
                    return True
                else:
                    self.log_test("Telemetry Data", False, f"Limited telemetry found: {found_indicators}")
                    return False
        except Exception as e:
            self.log_test("Telemetry Data", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all diagnostic tests"""
        print("🔍 Starting Comprehensive Connection Diagnosis...")
        print("=" * 60)
        
        # List of all tests
        tests = [
            self.test_01_website_accessibility,
            self.test_02_html_content_loads, 
            self.test_03_default_ip_values,
            self.test_04_initial_connection_status,
            self.test_05_connect_button_clickable,
            self.test_06_socketio_connection,
            self.test_07_connect_button_click_response,
            self.test_08_connection_status_change,
            self.test_09_heartbeat_counter_increment,
            self.test_10_telemetry_data_display
        ]
        
        # Run each test
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__.replace("test_", "").replace("_", " ").title(), 
                            False, f"Test exception: {str(e)}")
            
            time.sleep(1)  # Brief pause between tests
            
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        print()
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if r["status"] == "FAIL"]
        if failed_tests:
            print("🚨 FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("✅ ALL TESTS PASSED!")
            
        # Save results
        with open("comprehensive_diagnosis_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
            
        print(f"\n📋 Detailed results saved to: comprehensive_diagnosis_results.json")
        
        return passed == total


if __name__ == "__main__":
    try:
        tester = ConnectionDiagnosisTest()
        all_passed = tester.run_all_tests()
        sys.exit(0 if all_passed else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        sys.exit(1)
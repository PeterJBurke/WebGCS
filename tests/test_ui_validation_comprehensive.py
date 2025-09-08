#!/usr/bin/env python3
"""
Comprehensive UI Validation Testing Agent
Tests input validation, error handling, and safety confirmation systems across all WebGCS forms.

This script systematically tests:
- Connection form validation (IP addresses, ports)
- Navigation input validation (coordinates, altitude bounds)
- Flight control validation (takeoff altitude, safety confirmations)
- Error message display and user feedback
- Safety confirmation dialogs for critical operations
- Boundary condition testing

Success Criteria:
✅ Invalid inputs are properly rejected
✅ Error messages display clearly for users  
✅ Safety confirmations prevent accidental operations
✅ Form validation blocks invalid command transmission
✅ Boundary conditions handled correctly
✅ User feedback is clear and helpful
"""

import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

class UIValidationTester:
    def __init__(self):
        self.setup_browser()
        self.test_results = []
        self.failed_tests = []
        
    def setup_browser(self):
        """Setup Chrome browser with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        # Keep browser visible for demonstration
        # chrome_options.add_argument('--headless')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(2)
        except Exception as e:
            print(f"❌ Failed to setup Chrome browser: {e}")
            print("🔧 Make sure ChromeDriver is installed and in PATH")
            raise
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present and return it"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            print(f"⚠️  Element not found: {value}")
            return None
    
    def wait_for_clickable(self, by, value, timeout=10):
        """Wait for element to be clickable and return it"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            print(f"⚠️  Element not clickable: {value}")
            return None
    
    def check_for_error_message(self, expected_text_fragment=None):
        """Check if error message is displayed on the page"""
        try:
            # Check for various error message locations
            error_selectors = [
                "//div[contains(@class, 'error')]",
                "//div[contains(@class, 'alert')]", 
                "//div[contains(@class, 'message')]",
                "//span[contains(@class, 'error')]",
                "//*[contains(text(), 'error')]",
                "//*[contains(text(), 'Error')]",
                "//*[contains(text(), 'invalid')]",
                "//*[contains(text(), 'Invalid')]",
                "//*[contains(text(), 'must be')]",
                "//*[contains(text(), 'required')]"
            ]
            
            for selector in error_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        error_text = element.text.strip()
                        if error_text:
                            if expected_text_fragment:
                                if expected_text_fragment.lower() in error_text.lower():
                                    return True, error_text
                            else:
                                return True, error_text
            
            # Check for custom validity messages on inputs
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                try:
                    validity_msg = self.driver.execute_script("return arguments[0].validationMessage;", input_elem)
                    if validity_msg:
                        if expected_text_fragment:
                            if expected_text_fragment.lower() in validity_msg.lower():
                                return True, validity_msg
                        else:
                            return True, validity_msg
                except:
                    pass
            
            return False, None
        except Exception as e:
            print(f"⚠️  Error checking for error message: {e}")
            return False, None
    
    def check_for_confirmation_dialog(self):
        """Check if confirmation dialog is displayed"""
        try:
            # Check for modal dialog
            dialog = self.driver.find_element(By.ID, "confirmation-dialog")
            if dialog.is_displayed():
                return True, dialog
            return False, None
        except NoSuchElementException:
            # Check for browser alert
            try:
                alert = self.driver.switch_to.alert
                return True, alert
            except:
                return False, None
    
    def log_test_result(self, test_name, success, details="", error_found=False, error_message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': success,
            'details': details,
            'error_found': error_found,
            'error_message': error_message
        }
        self.test_results.append(result)
        
        if error_found and error_message:
            print(f"{status} {test_name}: {details} | Error: {error_message}")
        else:
            print(f"{status} {test_name}: {details}")
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_connection_form_validation(self):
        """Test connection form IP address and port validation"""
        print("\n🔍 TESTING CONNECTION FORM VALIDATION")
        print("=" * 60)
        
        try:
            # Navigate to WebGCS
            self.driver.get("http://localhost:5001")
            time.sleep(2)
            
            # Find connection form elements
            ip_input = self.wait_for_element(By.ID, "ip-address")
            port_input = self.wait_for_element(By.ID, "port-number") 
            connect_btn = self.wait_for_element(By.ID, "connect-btn")
            
            if not all([ip_input, port_input, connect_btn]):
                self.log_test_result("Connection Form Elements", False, "Missing form elements")
                return
            
            # Test 1: Invalid IP address formats
            invalid_ips = [
                "256.1.1.1",        # Out of range
                "192.168.1",        # Incomplete
                "192.168.1.1.1",    # Too many octets
                "abc.def.ghi.jkl",  # Non-numeric
                "192.168.-1.1",     # Negative number
                "",                 # Empty
                "999.999.999.999"   # Way out of range
            ]
            
            for invalid_ip in invalid_ips:
                ip_input.clear()
                ip_input.send_keys(invalid_ip)
                
                # Try to connect to trigger validation
                connect_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("invalid")
                self.log_test_result(
                    f"Invalid IP: {invalid_ip}", 
                    error_found, 
                    f"Expected error for invalid IP: {invalid_ip}",
                    error_found,
                    error_msg or "No error message shown"
                )
            
            # Test 2: Invalid port numbers
            invalid_ports = [
                "0",          # Below minimum
                "65536",      # Above maximum
                "-1",         # Negative
                "abc",        # Non-numeric
                "70000",      # Way above maximum
                "",           # Empty
                "3.14"        # Decimal
            ]
            
            # Set valid IP first
            ip_input.clear()
            ip_input.send_keys("192.168.193.235")
            
            for invalid_port in invalid_ports:
                port_input.clear()
                port_input.send_keys(invalid_port)
                
                # Try to connect to trigger validation
                connect_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("port")
                self.log_test_result(
                    f"Invalid Port: {invalid_port}", 
                    error_found, 
                    f"Expected error for invalid port: {invalid_port}",
                    error_found,
                    error_msg or "No error message shown"
                )
            
            # Test 3: Valid inputs should not show errors
            ip_input.clear()
            ip_input.send_keys("192.168.193.235")
            port_input.clear()
            port_input.send_keys("5678")
            
            connect_btn.click()
            time.sleep(1)
            
            error_found, error_msg = self.check_for_error_message()
            self.log_test_result(
                "Valid Connection Inputs", 
                not error_found, 
                "Valid inputs should not trigger validation errors",
                error_found,
                error_msg or "No error message (good)"
            )
            
        except Exception as e:
            self.log_test_result("Connection Form Validation", False, f"Test failed with exception: {e}")
    
    def test_navigation_input_validation(self):
        """Test navigation coordinate and altitude validation"""
        print("\n🧭 TESTING NAVIGATION INPUT VALIDATION")
        print("=" * 60)
        
        try:
            # Find navigation form elements
            lat_input = self.wait_for_element(By.ID, "nav-lat")
            lon_input = self.wait_for_element(By.ID, "nav-lon")
            alt_input = self.wait_for_element(By.ID, "nav-alt")
            goto_btn = self.wait_for_element(By.ID, "goto-btn")
            
            if not all([lat_input, lon_input, alt_input, goto_btn]):
                self.log_test_result("Navigation Form Elements", False, "Missing navigation form elements")
                return
            
            # Test 1: Invalid latitude values
            invalid_lats = [
                "91.0",        # Above maximum
                "-91.0",       # Below minimum  
                "180.0",       # Way out of range
                "-180.0",      # Way out of range
                "abc",         # Non-numeric
                "",            # Empty
                "90.000001"    # Just above maximum
            ]
            
            for invalid_lat in invalid_lats:
                lat_input.clear()
                lat_input.send_keys(invalid_lat)
                lon_input.clear()
                lon_input.send_keys("0")
                alt_input.clear()
                alt_input.send_keys("10")
                
                goto_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("latitude")
                self.log_test_result(
                    f"Invalid Latitude: {invalid_lat}", 
                    error_found, 
                    f"Expected error for invalid latitude: {invalid_lat}",
                    error_found,
                    error_msg or "No error message shown"
                )
            
            # Test 2: Invalid longitude values
            invalid_lons = [
                "181.0",       # Above maximum
                "-181.0",      # Below minimum
                "360.0",       # Way out of range
                "-360.0",      # Way out of range
                "xyz",         # Non-numeric
                "",            # Empty
                "180.000001"   # Just above maximum
            ]
            
            for invalid_lon in invalid_lons:
                lat_input.clear()
                lat_input.send_keys("0")
                lon_input.clear()
                lon_input.send_keys(invalid_lon)
                alt_input.clear()
                alt_input.send_keys("10")
                
                goto_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("longitude")
                self.log_test_result(
                    f"Invalid Longitude: {invalid_lon}", 
                    error_found, 
                    f"Expected error for invalid longitude: {invalid_lon}",
                    error_found,
                    error_msg or "No error message shown"
                )
            
            # Test 3: Invalid altitude values
            invalid_alts = [
                "-101",        # Below minimum
                "5001",        # Above maximum
                "10000",       # Way above maximum
                "-1000",       # Way below minimum
                "abc",         # Non-numeric
                ""             # Empty
            ]
            
            for invalid_alt in invalid_alts:
                lat_input.clear()
                lat_input.send_keys("37.7749")
                lon_input.clear()
                lon_input.send_keys("-122.4194")
                alt_input.clear()
                alt_input.send_keys(invalid_alt)
                
                goto_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("altitude")
                self.log_test_result(
                    f"Invalid Altitude: {invalid_alt}", 
                    error_found, 
                    f"Expected error for invalid altitude: {invalid_alt}",
                    error_found,
                    error_msg or "No error message shown"
                )
            
            # Test 4: Valid coordinate boundaries
            valid_coords = [
                ("90", "180", "5000"),      # Maximum values
                ("-90", "-180", "-100"),    # Minimum values
                ("0", "0", "0"),            # Zero values
                ("37.7749", "-122.4194", "100")  # Typical values
            ]
            
            for lat, lon, alt in valid_coords:
                lat_input.clear()
                lat_input.send_keys(lat)
                lon_input.clear()
                lon_input.send_keys(lon)
                alt_input.clear()
                alt_input.send_keys(alt)
                
                goto_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message()
                self.log_test_result(
                    f"Valid Coordinates: ({lat}, {lon}, {alt})", 
                    not error_found, 
                    f"Valid coordinates should not trigger errors: ({lat}, {lon}, {alt})",
                    error_found,
                    error_msg or "No error message (good)"
                )
            
            # Test 5: Precision validation
            lat_input.clear()
            lat_input.send_keys("37.123456789")  # High precision
            lon_input.clear() 
            lon_input.send_keys("-122.987654321")
            alt_input.clear()
            alt_input.send_keys("50")
            
            # Check if precision is handled properly
            time.sleep(0.5)
            lat_value = lat_input.get_attribute("value")
            lon_value = lon_input.get_attribute("value")
            
            # Should format to 6 decimal places or similar
            precision_handled = len(lat_value.split('.')[-1]) <= 8 if '.' in lat_value else True
            self.log_test_result(
                "High Precision Coordinates", 
                precision_handled, 
                f"Precision handling: lat={lat_value}, lon={lon_value}",
                False,
                ""
            )
            
        except Exception as e:
            self.log_test_result("Navigation Input Validation", False, f"Test failed with exception: {e}")
    
    def test_flight_control_validation(self):
        """Test flight control button validation and safety confirmations"""
        print("\n✈️ TESTING FLIGHT CONTROL VALIDATION")
        print("=" * 60)
        
        try:
            # Find flight control elements
            arm_btn = self.wait_for_element(By.ID, "arm-btn")
            disarm_btn = self.wait_for_element(By.ID, "disarm-btn")
            takeoff_btn = self.wait_for_element(By.ID, "takeoff-btn")
            takeoff_alt = self.wait_for_element(By.ID, "takeoff-altitude")
            land_btn = self.wait_for_element(By.ID, "land-btn")
            rtl_btn = self.wait_for_element(By.ID, "rtl-btn")
            
            if not all([arm_btn, disarm_btn, takeoff_btn, takeoff_alt, land_btn, rtl_btn]):
                self.log_test_result("Flight Control Elements", False, "Missing flight control elements")
                return
            
            # Test 1: Invalid takeoff altitude values
            invalid_alts = [
                "0",           # At minimum (should be > 0)
                "1001",        # Above maximum
                "-5",          # Negative
                "abc",         # Non-numeric
                "",            # Empty
                "10000"        # Way above maximum
            ]
            
            for invalid_alt in invalid_alts:
                takeoff_alt.clear()
                takeoff_alt.send_keys(invalid_alt)
                
                takeoff_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("altitude")
                
                # Also check if confirmation dialog appears (it shouldn't for invalid inputs)
                dialog_found, dialog = self.check_for_confirmation_dialog()
                if dialog_found:
                    # Dismiss dialog if it appeared inappropriately
                    try:
                        if hasattr(dialog, 'dismiss'):
                            dialog.dismiss()
                        else:
                            no_btn = self.driver.find_element(By.ID, "confirm-no")
                            no_btn.click()
                    except:
                        pass
                
                self.log_test_result(
                    f"Invalid Takeoff Altitude: {invalid_alt}", 
                    error_found or not dialog_found, 
                    f"Expected error for invalid takeoff altitude: {invalid_alt}. Dialog appeared: {dialog_found}",
                    error_found,
                    error_msg or "Invalid input should be rejected"
                )
            
            # Test 2: Valid takeoff altitude
            valid_alts = ["1", "5", "50", "100", "1000"]
            
            for valid_alt in valid_alts:
                takeoff_alt.clear()
                takeoff_alt.send_keys(valid_alt)
                
                takeoff_btn.click()
                time.sleep(0.5)
                
                # For valid altitudes, either should show error (not connected) or confirmation dialog
                error_found, error_msg = self.check_for_error_message()
                dialog_found, dialog = self.check_for_confirmation_dialog()
                
                # Dismiss any dialog that appeared
                if dialog_found:
                    try:
                        if hasattr(dialog, 'dismiss'):
                            dialog.dismiss()
                        else:
                            no_btn = self.driver.find_element(By.ID, "confirm-no")
                            no_btn.click()
                    except:
                        pass
                
                # Valid input should either trigger connection error or confirmation
                valid_response = error_found or dialog_found
                self.log_test_result(
                    f"Valid Takeoff Altitude: {valid_alt}", 
                    valid_response, 
                    f"Valid altitude should trigger connection check or confirmation: {valid_alt}",
                    error_found,
                    error_msg or ("Confirmation dialog appeared" if dialog_found else "No response")
                )
            
            # Test 3: Safety confirmation dialogs (when not connected, should show connection error)
            safety_buttons = [
                ("ARM", arm_btn, "arm"),
                ("DISARM", disarm_btn, "disarm"), 
                ("LAND", land_btn, "land"),
                ("RTL", rtl_btn, "rtl")
            ]
            
            for btn_name, btn_element, expected_keyword in safety_buttons:
                btn_element.click()
                time.sleep(0.5)
                
                # Should show connection error when not connected
                error_found, error_msg = self.check_for_error_message("connected")
                dialog_found, dialog = self.check_for_confirmation_dialog()
                
                # Dismiss any dialog
                if dialog_found:
                    try:
                        if hasattr(dialog, 'dismiss'):
                            dialog.dismiss()
                        else:
                            no_btn = self.driver.find_element(By.ID, "confirm-no")
                            no_btn.click()
                    except:
                        pass
                
                # When not connected, should show connection error
                self.log_test_result(
                    f"Safety Button {btn_name} (Disconnected)", 
                    error_found, 
                    f"Should show connection error for {btn_name} when disconnected",
                    error_found,
                    error_msg or "No connection error shown"
                )
            
            # Test 4: Flight mode validation
            mode_select = self.wait_for_element(By.ID, "flight-mode-select")
            set_mode_btn = self.wait_for_element(By.ID, "set-mode-btn")
            
            if mode_select and set_mode_btn:
                # Should show connection error when not connected
                set_mode_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("connected")
                self.log_test_result(
                    "Set Mode (Disconnected)", 
                    error_found, 
                    "Should show connection error for mode change when disconnected",
                    error_found,
                    error_msg or "No connection error shown"
                )
            
        except Exception as e:
            self.log_test_result("Flight Control Validation", False, f"Test failed with exception: {e}")
    
    def test_error_message_display(self):
        """Test that error messages are clearly displayed to users"""
        print("\n🚨 TESTING ERROR MESSAGE DISPLAY")
        print("=" * 60)
        
        try:
            # Test various ways error messages should be displayed
            
            # Test 1: Try to send command without connection
            goto_btn = self.wait_for_element(By.ID, "goto-btn")
            if goto_btn:
                # Fill in some coordinates
                lat_input = self.wait_for_element(By.ID, "nav-lat")
                lon_input = self.wait_for_element(By.ID, "nav-lon")
                alt_input = self.wait_for_element(By.ID, "nav-alt")
                
                if all([lat_input, lon_input, alt_input]):
                    lat_input.clear()
                    lat_input.send_keys("37.7749")
                    lon_input.clear() 
                    lon_input.send_keys("-122.4194")
                    alt_input.clear()
                    alt_input.send_keys("100")
                    
                    goto_btn.click()
                    time.sleep(1)
                    
                    # Should show clear error message
                    error_found, error_msg = self.check_for_error_message("connected")
                    
                    # Check if error message is visually prominent
                    if error_found:
                        # Try to find the error message element and check its styling
                        error_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'connected') or contains(text(), 'Connected')]")
                        for elem in error_elements:
                            if elem.is_displayed():
                                # Check if error styling is applied
                                classes = elem.get_attribute("class") or ""
                                color = self.driver.execute_script("return window.getComputedStyle(arguments[0]).color;", elem)
                                background = self.driver.execute_script("return window.getComputedStyle(arguments[0]).backgroundColor;", elem)
                                
                                visible_error = "error" in classes.lower() or "red" in color or "rgb(255" in color
                                break
                        else:
                            visible_error = False
                    else:
                        visible_error = False
                    
                    self.log_test_result(
                        "Error Message Visibility", 
                        error_found and visible_error, 
                        f"Error message should be visible and styled appropriately",
                        error_found,
                        f"{error_msg}. Visually prominent: {visible_error}"
                    )
            
            # Test 2: Invalid input error messages
            port_input = self.wait_for_element(By.ID, "port-number")
            connect_btn = self.wait_for_element(By.ID, "connect-btn")
            
            if port_input and connect_btn:
                port_input.clear()
                port_input.send_keys("70000")  # Invalid port
                connect_btn.click()
                time.sleep(0.5)
                
                error_found, error_msg = self.check_for_error_message("port")
                
                # Check message clarity and helpfulness
                helpful_error = False
                if error_found and error_msg:
                    # Good error messages should explain the valid range
                    helpful_keywords = ["between", "1", "65535", "range", "must be"]
                    helpful_error = any(keyword in error_msg.lower() for keyword in helpful_keywords)
                
                self.log_test_result(
                    "Helpful Error Messages", 
                    helpful_error, 
                    "Error messages should explain valid input ranges",
                    error_found,
                    f"{error_msg}. Contains helpful info: {helpful_error}"
                )
            
            # Test 3: Error message persistence and dismissal
            # Error messages should persist until user corrects input
            if port_input:
                port_input.clear()
                port_input.send_keys("abc")  # Invalid input
                port_input.send_keys(Keys.TAB)  # Trigger validation
                time.sleep(0.5)
                
                error_found_1, _ = self.check_for_error_message()
                
                # Now fix the input
                port_input.clear()
                port_input.send_keys("5678")  # Valid input
                port_input.send_keys(Keys.TAB)
                time.sleep(0.5)
                
                error_found_2, _ = self.check_for_error_message()
                
                self.log_test_result(
                    "Error Message Persistence", 
                    error_found_1 and not error_found_2, 
                    "Error should appear with invalid input and disappear when fixed",
                    error_found_1,
                    f"Error before fix: {error_found_1}, Error after fix: {error_found_2}"
                )
            
        except Exception as e:
            self.log_test_result("Error Message Display", False, f"Test failed with exception: {e}")
    
    def test_safety_confirmation_dialogs(self):
        """Test safety confirmation dialogs for critical operations"""
        print("\n🛡️ TESTING SAFETY CONFIRMATION DIALOGS")
        print("=" * 60)
        
        try:
            # First attempt to connect to enable buttons (even if connection fails)
            ip_input = self.wait_for_element(By.ID, "ip-address")
            port_input = self.wait_for_element(By.ID, "port-number")
            connect_btn = self.wait_for_element(By.ID, "connect-btn")
            
            if all([ip_input, port_input, connect_btn]):
                ip_input.clear()
                ip_input.send_keys("192.168.193.235")
                port_input.clear()
                port_input.send_keys("5678")
                connect_btn.click()
                time.sleep(2)  # Wait for connection attempt
            
            # Test confirmation dialogs for safety-critical commands
            # Note: These will show connection errors, but we're testing the confirmation flow
            
            # Test 1: ARM button safety confirmation
            arm_btn = self.wait_for_element(By.ID, "arm-btn")
            if arm_btn and not arm_btn.get_attribute("disabled"):
                arm_btn.click()
                time.sleep(0.5)
                
                dialog_found, dialog = self.check_for_confirmation_dialog()
                if dialog_found:
                    # Test dialog content
                    try:
                        if hasattr(dialog, 'text'):
                            dialog_text = dialog.text
                        else:
                            dialog_text = self.driver.find_element(By.ID, "confirm-message").text
                        
                        contains_warning = any(word in dialog_text.lower() 
                                             for word in ["arm", "propel", "spin", "danger", "warning"])
                        
                        # Test cancellation
                        try:
                            if hasattr(dialog, 'dismiss'):
                                dialog.dismiss()
                            else:
                                no_btn = self.driver.find_element(By.ID, "confirm-no")
                                no_btn.click()
                        except:
                            pass
                        
                        self.log_test_result(
                            "ARM Safety Confirmation", 
                            contains_warning, 
                            f"ARM confirmation should contain safety warning",
                            True,
                            f"Dialog text: {dialog_text[:100]}..."
                        )
                    except Exception as e:
                        self.log_test_result("ARM Safety Confirmation", False, f"Dialog interaction failed: {e}")
                else:
                    # Check if connection error was shown instead
                    error_found, error_msg = self.check_for_error_message("connected")
                    self.log_test_result(
                        "ARM Safety Confirmation", 
                        error_found, 
                        "Should show either confirmation dialog or connection error",
                        error_found,
                        error_msg or "No dialog or error shown"
                    )
            
            # Test 2: DISARM button safety confirmation  
            disarm_btn = self.wait_for_element(By.ID, "disarm-btn")
            if disarm_btn and not disarm_btn.get_attribute("disabled"):
                disarm_btn.click()
                time.sleep(0.5)
                
                dialog_found, dialog = self.check_for_confirmation_dialog()
                error_found, error_msg = self.check_for_error_message("connected")
                
                if dialog_found:
                    try:
                        if hasattr(dialog, 'dismiss'):
                            dialog.dismiss()
                        else:
                            no_btn = self.driver.find_element(By.ID, "confirm-no")
                            no_btn.click()
                    except:
                        pass
                
                self.log_test_result(
                    "DISARM Safety Confirmation", 
                    dialog_found or error_found, 
                    "Should show confirmation dialog or connection error for DISARM",
                    error_found,
                    error_msg or "Confirmation dialog appeared"
                )
            
            # Test 3: Takeoff confirmation with altitude
            takeoff_btn = self.wait_for_element(By.ID, "takeoff-btn")
            takeoff_alt = self.wait_for_element(By.ID, "takeoff-altitude")
            
            if all([takeoff_btn, takeoff_alt]) and not takeoff_btn.get_attribute("disabled"):
                takeoff_alt.clear()
                takeoff_alt.send_keys("50")
                takeoff_btn.click()
                time.sleep(0.5)
                
                dialog_found, dialog = self.check_for_confirmation_dialog()
                error_found, error_msg = self.check_for_error_message()
                
                if dialog_found:
                    try:
                        # Check if altitude is mentioned in confirmation
                        if hasattr(dialog, 'text'):
                            dialog_text = dialog.text
                        else:
                            dialog_text = self.driver.find_element(By.ID, "confirm-message").text
                        
                        altitude_mentioned = "50" in dialog_text or "altitude" in dialog_text.lower()
                        
                        # Cancel the dialog
                        if hasattr(dialog, 'dismiss'):
                            dialog.dismiss()
                        else:
                            no_btn = self.driver.find_element(By.ID, "confirm-no")
                            no_btn.click()
                        
                        self.log_test_result(
                            "Takeoff Confirmation Details", 
                            altitude_mentioned, 
                            "Takeoff confirmation should mention altitude",
                            True,
                            f"Dialog mentions altitude: {altitude_mentioned}"
                        )
                    except Exception as e:
                        self.log_test_result("Takeoff Confirmation Details", False, f"Dialog check failed: {e}")
                
                self.log_test_result(
                    "Takeoff Safety Confirmation", 
                    dialog_found or error_found, 
                    "Should show confirmation dialog or connection error for takeoff",
                    error_found,
                    error_msg or "Confirmation dialog appeared"
                )
            
            # Test 4: Land and RTL confirmations
            safety_buttons = [("LAND", "land-btn"), ("RTL", "rtl-btn")]
            
            for btn_name, btn_id in safety_buttons:
                btn = self.wait_for_element(By.ID, btn_id)
                if btn and not btn.get_attribute("disabled"):
                    btn.click()
                    time.sleep(0.5)
                    
                    dialog_found, dialog = self.check_for_confirmation_dialog()
                    error_found, error_msg = self.check_for_error_message("connected")
                    
                    if dialog_found:
                        try:
                            if hasattr(dialog, 'dismiss'):
                                dialog.dismiss()
                            else:
                                no_btn = self.driver.find_element(By.ID, "confirm-no")
                                no_btn.click()
                        except:
                            pass
                    
                    self.log_test_result(
                        f"{btn_name} Safety Confirmation", 
                        dialog_found or error_found, 
                        f"Should show confirmation dialog or connection error for {btn_name}",
                        error_found,
                        error_msg or "Confirmation dialog appeared"
                    )
            
        except Exception as e:
            self.log_test_result("Safety Confirmation Dialogs", False, f"Test failed with exception: {e}")
    
    def test_boundary_conditions(self):
        """Test boundary conditions for all numeric inputs"""
        print("\n⚡ TESTING BOUNDARY CONDITIONS")
        print("=" * 60)
        
        try:
            # Test exact boundary values for coordinates
            boundary_tests = [
                # (description, lat, lon, alt, should_pass)
                ("Max Latitude", "90", "0", "100", True),
                ("Min Latitude", "-90", "0", "100", True),
                ("Over Max Latitude", "90.000001", "0", "100", False),
                ("Under Min Latitude", "-90.000001", "0", "100", False),
                
                ("Max Longitude", "0", "180", "100", True),
                ("Min Longitude", "0", "-180", "100", True),
                ("Over Max Longitude", "0", "180.000001", "100", False),
                ("Under Min Longitude", "0", "-180.000001", "100", False),
                
                ("Max Altitude", "0", "0", "5000", True),
                ("Min Altitude", "0", "0", "-100", True),
                ("Over Max Altitude", "0", "0", "5001", False),
                ("Under Min Altitude", "0", "0", "-101", False),
                
                ("Zero Coordinates", "0", "0", "0", True),
            ]
            
            lat_input = self.wait_for_element(By.ID, "nav-lat")
            lon_input = self.wait_for_element(By.ID, "nav-lon")
            alt_input = self.wait_for_element(By.ID, "nav-alt")
            goto_btn = self.wait_for_element(By.ID, "goto-btn")
            
            if all([lat_input, lon_input, alt_input, goto_btn]):
                for description, lat, lon, alt, should_pass in boundary_tests:
                    lat_input.clear()
                    lat_input.send_keys(lat)
                    lon_input.clear()
                    lon_input.send_keys(lon)
                    alt_input.clear()
                    alt_input.send_keys(alt)
                    
                    goto_btn.click()
                    time.sleep(0.5)
                    
                    error_found, error_msg = self.check_for_error_message()
                    
                    # For valid boundary values, should show connection error (not input validation error)
                    if should_pass:
                        connection_error = error_found and ("connected" in error_msg.lower() if error_msg else False)
                        validation_error = error_found and not connection_error
                        test_passed = not validation_error  # Should not have validation error
                    else:
                        # Invalid values should show validation error
                        test_passed = error_found
                    
                    self.log_test_result(
                        f"Boundary: {description}", 
                        test_passed, 
                        f"Values: ({lat}, {lon}, {alt}) - Should pass: {should_pass}",
                        error_found,
                        error_msg or "No error message"
                    )
            
            # Test port number boundaries
            port_input = self.wait_for_element(By.ID, "port-number")
            connect_btn = self.wait_for_element(By.ID, "connect-btn")
            
            if all([port_input, connect_btn]):
                port_boundaries = [
                    ("Min Port", "1", True),
                    ("Max Port", "65535", True),
                    ("Under Min Port", "0", False),
                    ("Over Max Port", "65536", False),
                ]
                
                # Set valid IP first
                ip_input = self.wait_for_element(By.ID, "ip-address")
                if ip_input:
                    ip_input.clear()
                    ip_input.send_keys("192.168.193.235")
                
                for description, port_val, should_pass in port_boundaries:
                    port_input.clear()
                    port_input.send_keys(port_val)
                    
                    connect_btn.click()
                    time.sleep(0.5)
                    
                    error_found, error_msg = self.check_for_error_message("port")
                    
                    if should_pass:
                        test_passed = not error_found  # Should not have port validation error
                    else:
                        test_passed = error_found  # Should have port validation error
                    
                    self.log_test_result(
                        f"Port {description}", 
                        test_passed, 
                        f"Port: {port_val} - Should pass: {should_pass}",
                        error_found,
                        error_msg or "No error message"
                    )
            
            # Test takeoff altitude boundaries
            takeoff_alt = self.wait_for_element(By.ID, "takeoff-altitude")
            takeoff_btn = self.wait_for_element(By.ID, "takeoff-btn")
            
            if all([takeoff_alt, takeoff_btn]):
                altitude_boundaries = [
                    ("Min Takeoff Altitude", "1", True),
                    ("Max Takeoff Altitude", "1000", True),
                    ("Zero Takeoff Altitude", "0", False),
                    ("Over Max Takeoff Altitude", "1001", False),
                ]
                
                for description, alt_val, should_pass in altitude_boundaries:
                    takeoff_alt.clear()
                    takeoff_alt.send_keys(alt_val)
                    
                    takeoff_btn.click()
                    time.sleep(0.5)
                    
                    error_found, error_msg = self.check_for_error_message("altitude")
                    dialog_found, dialog = self.check_for_confirmation_dialog()
                    
                    # Dismiss any dialog
                    if dialog_found:
                        try:
                            if hasattr(dialog, 'dismiss'):
                                dialog.dismiss()
                            else:
                                no_btn = self.driver.find_element(By.ID, "confirm-no")
                                no_btn.click()
                        except:
                            pass
                    
                    if should_pass:
                        # Valid altitudes should either show connection error or confirmation dialog
                        test_passed = error_found or dialog_found
                    else:
                        # Invalid altitudes should show validation error
                        test_passed = error_found and "altitude" in error_msg.lower() if error_msg else False
                    
                    self.log_test_result(
                        f"Takeoff {description}", 
                        test_passed, 
                        f"Altitude: {alt_val}m - Should pass: {should_pass}",
                        error_found,
                        error_msg or ("Confirmation dialog appeared" if dialog_found else "No response")
                    )
            
        except Exception as e:
            self.log_test_result("Boundary Conditions", False, f"Test failed with exception: {e}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 STARTING COMPREHENSIVE UI VALIDATION TESTING")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_connection_form_validation()
        self.test_navigation_input_validation()
        self.test_flight_control_validation()
        self.test_error_message_display()
        self.test_safety_confirmation_dialogs()
        self.test_boundary_conditions()
        
        # Generate summary report
        end_time = time.time()
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['status'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE UI VALIDATION TEST RESULTS")
        print("=" * 80)
        
        print(f"⏱️  Total Testing Time: {end_time - start_time:.1f} seconds")
        print(f"📊 Total Tests Run: {total_tests}")
        print(f"✅ Tests Passed: {passed_tests}")
        print(f"❌ Tests Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS ({len(self.failed_tests)}):")
            for failed_test in self.failed_tests:
                print(f"  • {failed_test}")
        
        print("\n📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            status = "✅ PASS" if result['status'] else "❌ FAIL"
            print(f"{status} {result['test']}: {result['details']}")
            if result['error_message']:
                print(f"    📝 {result['error_message']}")
        
        # Validation Summary
        print(f"\n🛡️ INPUT VALIDATION SUMMARY:")
        validation_categories = {
            'Connection Form': 0,
            'Navigation Input': 0, 
            'Flight Control': 0,
            'Error Display': 0,
            'Safety Confirmation': 0,
            'Boundary Conditions': 0
        }
        
        for result in self.test_results:
            if 'Connection' in result['test'] or 'IP' in result['test'] or 'Port' in result['test']:
                validation_categories['Connection Form'] += result['status']
            elif 'Navigation' in result['test'] or 'Latitude' in result['test'] or 'Longitude' in result['test']:
                validation_categories['Navigation Input'] += result['status']
            elif 'Flight' in result['test'] or 'Takeoff' in result['test'] or 'ARM' in result['test']:
                validation_categories['Flight Control'] += result['status']
            elif 'Error' in result['test'] or 'Message' in result['test']:
                validation_categories['Error Display'] += result['status']
            elif 'Safety' in result['test'] or 'Confirmation' in result['test']:
                validation_categories['Safety Confirmation'] += result['status']
            elif 'Boundary' in result['test']:
                validation_categories['Boundary Conditions'] += result['status']
        
        for category, passed in validation_categories.items():
            total_in_category = sum(1 for result in self.test_results 
                                  if any(keyword in result['test'] for keyword in category.split()))
            if total_in_category > 0:
                success_rate = (passed / total_in_category) * 100
                print(f"  {category}: {passed}/{total_in_category} ({success_rate:.0f}%)")
        
        # Final Assessment
        overall_success = (passed_tests / total_tests) * 100
        print(f"\n🎯 OVERALL UI VALIDATION ASSESSMENT:")
        if overall_success >= 95:
            print("🌟 EXCELLENT: WebGCS has robust input validation and error handling")
        elif overall_success >= 85:
            print("✅ GOOD: WebGCS has solid input validation with minor improvements needed")
        elif overall_success >= 70:
            print("⚠️ FAIR: WebGCS has basic validation but needs significant improvements")
        else:
            print("❌ POOR: WebGCS validation needs major improvements for safety")
        
        return overall_success >= 85
    
    def cleanup(self):
        """Cleanup browser resources"""
        try:
            self.driver.quit()
            print("🧹 Browser cleanup completed")
        except Exception as e:
            print(f"⚠️ Browser cleanup warning: {e}")

def main():
    """Main test execution"""
    
    # Check if WebGCS server is running
    try:
        response = requests.get("http://localhost:5001/health", timeout=5)
        if response.status_code != 200:
            print("❌ WebGCS server health check failed")
            return False
    except requests.exceptions.RequestException:
        print("❌ WebGCS server is not running on localhost:5001")
        print("🔧 Please start the server with: uv run python app.py")
        return False
    
    print("✅ WebGCS server is running and healthy")
    
    # Run comprehensive validation tests
    tester = UIValidationTester()
    
    try:
        success = tester.run_all_tests()
        return success
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Testing failed with unexpected error: {e}")
        return False
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
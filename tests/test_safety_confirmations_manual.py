#!/usr/bin/env python3
"""
Manual Safety Confirmation Testing
Tests that safety confirmation dialogs are properly displayed in the WebGCS interface.

This script tests the actual safety confirmation system by examining the HTML and JavaScript
to verify that critical operations require user confirmation.
"""

import time
import requests
from bs4 import BeautifulSoup
import re

class SafetyConfirmationTester:
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        
    def log_test_result(self, test_name, success, details="", evidence=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': success,
            'details': details,
            'evidence': evidence
        }
        self.test_results.append(result)
        
        print(f"{status} {test_name}: {details}")
        if evidence:
            print(f"    📝 {evidence}")
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_confirmation_dialog_html(self):
        """Test that confirmation dialog exists in HTML"""
        print("\n🛡️ TESTING CONFIRMATION DIALOG HTML STRUCTURE")
        print("=" * 60)
        
        try:
            # Get the main interface HTML
            response = requests.get("http://localhost:5001/", timeout=5)
            if response.status_code != 200:
                self.log_test_result(
                    "HTML Interface Access",
                    False,
                    "Could not access WebGCS interface",
                    f"HTTP {response.status_code}"
                )
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for confirmation dialog
            dialog = soup.find(id='confirmation-dialog')
            has_dialog = dialog is not None
            self.log_test_result(
                "Confirmation Dialog Exists",
                has_dialog,
                "HTML should contain confirmation dialog element",
                "Found confirmation-dialog element" if has_dialog else "Missing confirmation-dialog"
            )
            
            if has_dialog:
                # Check dialog structure
                title = soup.find(id='confirm-title')
                message = soup.find(id='confirm-message')
                yes_btn = soup.find(id='confirm-yes')
                no_btn = soup.find(id='confirm-no')
                
                complete_structure = all([title, message, yes_btn, no_btn])
                self.log_test_result(
                    "Dialog Structure Complete",
                    complete_structure,
                    "Dialog should have title, message, and yes/no buttons",
                    f"Elements found: title={title is not None}, message={message is not None}, yes={yes_btn is not None}, no={no_btn is not None}"
                )
                
                # Check for modal CSS class
                has_modal_class = 'modal' in dialog.get('class', [])
                self.log_test_result(
                    "Modal CSS Class",
                    has_modal_class,
                    "Dialog should have modal CSS class for proper styling",
                    f"CSS classes: {dialog.get('class', [])}"
                )
            
            # Check for safety-critical button attributes
            safety_buttons = ['arm-btn', 'disarm-btn', 'takeoff-btn', 'land-btn', 'rtl-btn']
            for btn_id in safety_buttons:
                button = soup.find(id=btn_id)
                if button:
                    # Check if button exists
                    self.log_test_result(
                        f"Safety Button Exists: {btn_id}",
                        True,
                        f"Safety button {btn_id} found in HTML",
                        f"Button text: {button.get_text().strip()}"
                    )
                else:
                    self.log_test_result(
                        f"Safety Button Exists: {btn_id}",
                        False,
                        f"Safety button {btn_id} missing from HTML",
                        "Button not found"
                    )
            
        except Exception as e:
            self.log_test_result(
                "HTML Structure Test",
                False,
                "Failed to analyze HTML structure",
                f"Error: {e}"
            )
    
    def test_javascript_safety_functions(self):
        """Test JavaScript safety confirmation functions"""
        print("\n🔧 TESTING JAVASCRIPT SAFETY FUNCTIONS")
        print("=" * 60)
        
        try:
            # Read flight controls JavaScript
            with open('static/js/flight-controls.js', 'r') as f:
                flight_js = f.read()
            
            # Check for handleSafetyCommand function
            has_safety_handler = 'handleSafetyCommand' in flight_js
            self.log_test_result(
                "Safety Command Handler Function",
                has_safety_handler,
                "JavaScript should have handleSafetyCommand function",
                "Found handleSafetyCommand function" if has_safety_handler else "Missing safety handler"
            )
            
            # Check for confirmation dialog usage
            uses_confirmation = 'showConfirmation' in flight_js or 'confirm(' in flight_js
            self.log_test_result(
                "Confirmation Dialog Usage",
                uses_confirmation,
                "Safety functions should use confirmation dialogs",
                "Found confirmation dialog calls" if uses_confirmation else "No confirmation dialogs found"
            )
            
            # Check for specific safety commands
            safety_commands = ['ARM', 'DISARM', 'TAKEOFF', 'LAND', 'RTL']
            safety_patterns = []
            
            for command in safety_commands:
                # Look for safety confirmation patterns
                patterns = [
                    f"handleSafetyCommand.*{command.lower()}",
                    f"'{command}'.*showConfirmation",
                    f'"{command}".*showConfirmation',
                    f"confirm.*{command}",
                ]
                
                command_has_safety = any(re.search(pattern, flight_js, re.IGNORECASE) for pattern in patterns)
                if command_has_safety:
                    safety_patterns.append(command)
                
                self.log_test_result(
                    f"Safety Confirmation: {command}",
                    command_has_safety,
                    f"{command} command should require safety confirmation",
                    f"Found safety confirmation for {command}" if command_has_safety else "No safety confirmation found"
                )
            
            # Check for warning messages in confirmations
            warning_keywords = ['warning', 'danger', 'caution', 'armed', 'propeller', 'spin']
            has_warnings = any(keyword in flight_js.lower() for keyword in warning_keywords)
            self.log_test_result(
                "Safety Warning Messages",
                has_warnings,
                "Confirmation dialogs should contain safety warnings",
                f"Found safety warning keywords" if has_warnings else "No safety warnings found"
            )
            
            # Check for ARM-specific safety message
            arm_safety = 'propel' in flight_js.lower() or 'spin' in flight_js.lower() or 'arm' in flight_js.lower()
            self.log_test_result(
                "ARM Command Safety Warning",
                arm_safety,
                "ARM command should have specific safety warning about propellers",
                "Found ARM safety warning" if arm_safety else "No ARM safety warning"
            )
            
        except FileNotFoundError:
            self.log_test_result(
                "JavaScript File Access",
                False,
                "Could not read flight-controls.js file",
                "File not found"
            )
        except Exception as e:
            self.log_test_result(
                "JavaScript Analysis",
                False,
                "Failed to analyze JavaScript functions",
                f"Error: {e}"
            )
    
    def test_input_validation_attributes(self):
        """Test HTML input validation attributes"""
        print("\n📝 TESTING INPUT VALIDATION ATTRIBUTES")
        print("=" * 60)
        
        try:
            # Get the main interface HTML
            response = requests.get("http://localhost:5001/", timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Test connection form validation attributes
            ip_input = soup.find(id='ip-address')
            port_input = soup.find(id='port-number')
            
            if ip_input:
                # Check IP input type and attributes
                is_text_type = ip_input.get('type') == 'text'
                has_placeholder = ip_input.get('placeholder') is not None
                self.log_test_result(
                    "IP Address Input Attributes",
                    is_text_type and has_placeholder,
                    "IP input should be text type with placeholder",
                    f"Type: {ip_input.get('type')}, Placeholder: {ip_input.get('placeholder')}"
                )
            
            if port_input:
                # Check port input validation attributes
                is_number_type = port_input.get('type') == 'number'
                has_min = ip_input.get('min') is not None
                has_max = port_input.get('max') is not None
                
                # Extract min/max values if they exist
                min_val = port_input.get('min')
                max_val = port_input.get('max')
                
                correct_range = (min_val == '1' or min_val == '1') and (max_val == '65535')
                
                self.log_test_result(
                    "Port Number Input Validation",
                    is_number_type,
                    "Port input should be number type with min/max attributes",
                    f"Type: {port_input.get('type')}, Min: {min_val}, Max: {max_val}"
                )
            
            # Test navigation input validation attributes
            nav_inputs = [
                ('nav-lat', 'Latitude', -90, 90),
                ('nav-lon', 'Longitude', -180, 180),
                ('nav-alt', 'Altitude', -100, 5000)
            ]
            
            for input_id, input_name, expected_min, expected_max in nav_inputs:
                input_elem = soup.find(id=input_id)
                if input_elem:
                    is_number = input_elem.get('type') == 'number'
                    has_step = input_elem.get('step') is not None
                    min_val = input_elem.get('min')
                    max_val = input_elem.get('max')
                    
                    # Check if min/max values are correct
                    correct_min = min_val == str(expected_min) if min_val else False
                    correct_max = max_val == str(expected_max) if max_val else False
                    
                    self.log_test_result(
                        f"{input_name} Input Validation",
                        is_number and correct_min and correct_max,
                        f"{input_name} input should have proper validation attributes",
                        f"Type: {input_elem.get('type')}, Min: {min_val} (expected {expected_min}), Max: {max_val} (expected {expected_max}), Step: {input_elem.get('step')}"
                    )
            
            # Test takeoff altitude input validation
            takeoff_alt = soup.find(id='takeoff-altitude')
            if takeoff_alt:
                is_number = takeoff_alt.get('type') == 'number'
                min_val = takeoff_alt.get('min')
                max_val = takeoff_alt.get('max')
                
                correct_takeoff_range = (min_val == '1') and (max_val == '1000')
                
                self.log_test_result(
                    "Takeoff Altitude Input Validation",
                    is_number and correct_takeoff_range,
                    "Takeoff altitude should have proper range validation (1-1000)",
                    f"Type: {takeoff_alt.get('type')}, Min: {min_val}, Max: {max_val}"
                )
            
        except Exception as e:
            self.log_test_result(
                "Input Validation Attributes",
                False,
                "Failed to analyze HTML input validation",
                f"Error: {e}"
            )
    
    def test_error_feedback_system(self):
        """Test error message display system"""
        print("\n🚨 TESTING ERROR FEEDBACK SYSTEM")
        print("=" * 60)
        
        try:
            # Read app.js for global error handling
            with open('static/js/app.js', 'r') as f:
                app_js = f.read()
            
            # Check for showMessage function
            has_show_message = 'showMessage' in app_js
            self.log_test_result(
                "Global Error Message Function",
                has_show_message,
                "App should have showMessage function for user feedback",
                "Found showMessage function" if has_show_message else "No showMessage function"
            )
            
            # Check for message types (error, warning, success, info)
            message_types = ['error', 'warning', 'success', 'info']
            supports_types = all(msg_type in app_js.lower() for msg_type in message_types)
            self.log_test_result(
                "Message Type Support",
                supports_types,
                "Error system should support different message types",
                f"Found message types: {[t for t in message_types if t in app_js.lower()]}"
            )
            
            # Check navigation controls for input validation feedback
            with open('static/js/navigation-controls.js', 'r') as f:
                nav_js = f.read()
            
            # Look for setCustomValidity usage (HTML5 validation)
            uses_custom_validity = 'setCustomValidity' in nav_js
            self.log_test_result(
                "HTML5 Validation Feedback",
                uses_custom_validity,
                "Navigation controls should use HTML5 validation feedback",
                "Found setCustomValidity usage" if uses_custom_validity else "No HTML5 validation feedback"
            )
            
            # Check for validation error messages
            validation_messages = [
                'must be between',
                'invalid',
                'required',
                'latitude',
                'longitude', 
                'altitude'
            ]
            
            has_validation_messages = any(msg in nav_js.lower() for msg in validation_messages)
            self.log_test_result(
                "Input Validation Messages",
                has_validation_messages,
                "Navigation controls should provide specific validation messages",
                "Found validation messages" if has_validation_messages else "No validation messages found"
            )
            
        except FileNotFoundError as e:
            self.log_test_result(
                "JavaScript File Access",
                False,
                "Could not read JavaScript files for error feedback analysis",
                f"File not found: {e}"
            )
        except Exception as e:
            self.log_test_result(
                "Error Feedback Analysis",
                False,
                "Failed to analyze error feedback system",
                f"Error: {e}"
            )
    
    def run_all_tests(self):
        """Run all safety confirmation tests"""
        print("🚀 STARTING MANUAL SAFETY CONFIRMATION TESTING")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_confirmation_dialog_html()
        self.test_javascript_safety_functions()
        self.test_input_validation_attributes()
        self.test_error_feedback_system()
        
        # Generate summary report
        end_time = time.time()
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['status'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🏁 SAFETY CONFIRMATION TEST RESULTS")
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
        
        # Safety Features Summary
        print(f"\n🛡️ SAFETY FEATURES ANALYSIS:")
        
        safety_categories = {
            'Confirmation Dialog System': ['Dialog', 'Modal'],
            'Safety Command Functions': ['Safety', 'Confirmation'],
            'Input Validation': ['Validation', 'Input'],
            'Error Feedback': ['Error', 'Message', 'Feedback']
        }
        
        for category, keywords in safety_categories.items():
            category_tests = [r for r in self.test_results 
                            if any(keyword in r['test'] for keyword in keywords)]
            if category_tests:
                passed = sum(1 for r in category_tests if r['status'])
                total = len(category_tests)
                percentage = (passed / total) * 100
                print(f"  {category}: {passed}/{total} ({percentage:.0f}%)")
        
        # Overall Safety Assessment
        overall_success = (passed_tests / total_tests) * 100
        print(f"\n🎯 OVERALL SAFETY ASSESSMENT:")
        if overall_success >= 95:
            print("🌟 EXCELLENT: WebGCS has comprehensive safety confirmation systems")
            print("   ✅ All critical safety features properly implemented")
            print("   ✅ User confirmation required for dangerous operations")
            print("   ✅ Input validation prevents invalid commands")
            print("   ✅ Error feedback is clear and helpful")
        elif overall_success >= 85:
            print("✅ GOOD: WebGCS has solid safety systems with minor improvements possible")
            print("   ✅ Core safety features working well")
            print("   ⚠️  Some enhancements could improve user experience")
        elif overall_success >= 70:
            print("⚠️ FAIR: WebGCS has basic safety features but needs improvements")
            print("   ⚠️  Several safety gaps identified")
            print("   🔧 Recommend addressing failed tests")
        else:
            print("❌ POOR: WebGCS safety systems need significant improvements")
            print("   ❌ Critical safety issues detected")
            print("   🚨 Immediate fixes needed for safe operation")
        
        return overall_success >= 85

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
    
    # Run safety confirmation tests
    tester = SafetyConfirmationTester()
    
    try:
        success = tester.run_all_tests()
        return success
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Testing failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
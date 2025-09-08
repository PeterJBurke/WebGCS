#!/usr/bin/env python3
"""
Direct UI Validation Logic Testing
Tests input validation, error handling, and safety systems without browser automation.

This script systematically tests:
- Backend validation functions in mavlink_command_sender.py
- Frontend JavaScript validation (by examining code)
- Safety confirmation requirements
- Boundary condition handling
- Error message generation

Success Criteria:
✅ Invalid inputs are properly rejected by backend
✅ Validation functions handle edge cases correctly
✅ Safety confirmations are required for critical operations
✅ Error messages provide clear feedback
✅ Boundary conditions are handled correctly
"""

import sys
import time
import json
import requests
from mavlink_command_sender import (
    send_goto_command, send_takeoff_command, send_arm_disarm_command,
    send_mode_change_command, send_land_command, send_rtl_command,
    process_flight_command
)
import re

class DirectValidationTester:
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.mock_connection = MockMAVLinkConnection()
        
    def log_test_result(self, test_name, success, details="", error_message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': success,
            'details': details,
            'error_message': error_message
        }
        self.test_results.append(result)
        
        print(f"{status} {test_name}: {details}")
        if error_message:
            print(f"    📝 {error_message}")
        
        if not success:
            self.failed_tests.append(test_name)
    
    def test_coordinate_validation(self):
        """Test coordinate validation in backend"""
        print("\n🧭 TESTING COORDINATE VALIDATION (BACKEND)")
        print("=" * 60)
        
        # Test invalid latitude values
        invalid_lats = [
            (91.0, "Above maximum"),
            (-91.0, "Below minimum"), 
            (180.0, "Way out of range"),
            (-180.0, "Way out of range"),
            (90.000001, "Just above maximum"),
            (-90.000001, "Just below minimum")
        ]
        
        for lat, description in invalid_lats:
            result = send_goto_command(self.mock_connection, lat, 0, 100)
            success = not result['success'] and 'latitude' in result.get('error', '').lower()
            self.log_test_result(
                f"Invalid Latitude: {lat} ({description})",
                success,
                f"Expected rejection for latitude {lat}",
                result.get('error', 'No error message')
            )
        
        # Test invalid longitude values
        invalid_lons = [
            (181.0, "Above maximum"),
            (-181.0, "Below minimum"),
            (360.0, "Way out of range"),
            (-360.0, "Way out of range"),
            (180.000001, "Just above maximum"),
            (-180.000001, "Just below minimum")
        ]
        
        for lon, description in invalid_lons:
            result = send_goto_command(self.mock_connection, 0, lon, 100)
            success = not result['success'] and 'longitude' in result.get('error', '').lower()
            self.log_test_result(
                f"Invalid Longitude: {lon} ({description})",
                success,
                f"Expected rejection for longitude {lon}",
                result.get('error', 'No error message')
            )
        
        # Test invalid altitude values
        invalid_alts = [
            (-101, "Below minimum"),
            (5001, "Above maximum"),
            (10000, "Way above maximum"),
            (-1000, "Way below minimum")
        ]
        
        for alt, description in invalid_alts:
            result = send_goto_command(self.mock_connection, 0, 0, alt)
            success = not result['success'] and 'altitude' in result.get('error', '').lower()
            self.log_test_result(
                f"Invalid Altitude: {alt} ({description})",
                success,
                f"Expected rejection for altitude {alt}",
                result.get('error', 'No error message')
            )
        
        # Test valid boundary values
        valid_coords = [
            (90, 180, 5000, "Maximum values"),
            (-90, -180, -100, "Minimum values"),
            (0, 0, 0, "Zero values"),
            (37.7749, -122.4194, 100, "Typical values")
        ]
        
        for lat, lon, alt, description in valid_coords:
            result = send_goto_command(self.mock_connection, lat, lon, alt)
            success = result['success']
            self.log_test_result(
                f"Valid Coordinates: ({lat}, {lon}, {alt}) ({description})",
                success,
                f"Expected acceptance for valid coordinates ({lat}, {lon}, {alt})",
                result.get('message', 'Command accepted')
            )
    
    def test_takeoff_altitude_validation(self):
        """Test takeoff altitude validation"""
        print("\n✈️ TESTING TAKEOFF ALTITUDE VALIDATION")
        print("=" * 60)
        
        # Test invalid takeoff altitudes
        invalid_alts = [
            (0, "Zero altitude"),
            (-5, "Negative altitude"),
            (101, "Above maximum (safety limit)"),
            (1000, "Way above safe maximum"),
            ("abc", "Non-numeric input")
        ]
        
        for alt, description in invalid_alts:
            result = send_takeoff_command(self.mock_connection, alt)
            success = not result['success'] and 'altitude' in result.get('error', '').lower()
            self.log_test_result(
                f"Invalid Takeoff Altitude: {alt} ({description})",
                success,
                f"Expected rejection for takeoff altitude {alt}",
                result.get('error', 'No error message')
            )
        
        # Test valid takeoff altitudes
        valid_alts = [
            (1, "Minimum altitude"),
            (5, "Standard altitude"),
            (50, "Higher altitude"),
            (100, "Maximum altitude")
        ]
        
        for alt, description in valid_alts:
            result = send_takeoff_command(self.mock_connection, alt)
            success = result['success']
            self.log_test_result(
                f"Valid Takeoff Altitude: {alt} ({description})",
                success,
                f"Expected acceptance for takeoff altitude {alt}",
                result.get('message', 'Command accepted')
            )
    
    def test_flight_mode_validation(self):
        """Test flight mode validation"""
        print("\n🎮 TESTING FLIGHT MODE VALIDATION")
        print("=" * 60)
        
        # Test invalid flight modes
        invalid_modes = [
            "INVALID_MODE",
            "UNKNOWN",
            "HOVER",  # Not in ArduPilot mode list
            "FLY",
            "",
            None
        ]
        
        for mode in invalid_modes:
            if mode is None:
                # Test missing mode parameter
                result = process_flight_command({'command': 'SET_MODE', 'params': {}}, self.mock_connection)
            else:
                result = send_mode_change_command(self.mock_connection, mode)
            
            success = not result['success'] and ('mode' in result.get('error', '').lower() or 
                                               'unknown' in result.get('error', '').lower())
            self.log_test_result(
                f"Invalid Flight Mode: {mode}",
                success,
                f"Expected rejection for invalid mode {mode}",
                result.get('error', 'No error message')
            )
        
        # Test valid flight modes (from AP_CUSTOM_MODES in config.py)
        valid_modes = [
            "STABILIZE",
            "ALT_HOLD", 
            "LOITER",
            "GUIDED",
            "RTL",
            "LAND",
            "AUTO"
        ]
        
        for mode in valid_modes:
            result = send_mode_change_command(self.mock_connection, mode)
            success = result['success']
            self.log_test_result(
                f"Valid Flight Mode: {mode}",
                success,
                f"Expected acceptance for valid mode {mode}",
                result.get('message', 'Command accepted')
            )
    
    def test_command_parameter_validation(self):
        """Test command parameter requirements"""
        print("\n📋 TESTING COMMAND PARAMETER VALIDATION")
        print("=" * 60)
        
        # Test missing required parameters
        missing_param_tests = [
            ({'command': 'GOTO', 'params': {'lat': 37.7749, 'lon': -122.4194}}, "Missing altitude"),
            ({'command': 'GOTO', 'params': {'lat': 37.7749, 'alt': 100}}, "Missing longitude"),
            ({'command': 'GOTO', 'params': {'lon': -122.4194, 'alt': 100}}, "Missing latitude"),
            ({'command': 'GOTO', 'params': {}}, "Missing all coordinates"),
            ({'command': 'TAKEOFF', 'params': {}}, "Missing takeoff altitude"),
            ({'command': 'SET_MODE', 'params': {}}, "Missing flight mode"),
        ]
        
        for command_data, description in missing_param_tests:
            result = process_flight_command(command_data, self.mock_connection)
            success = not result['success'] and ('parameter' in result.get('error', '').lower() or 
                                               'required' in result.get('error', '').lower())
            self.log_test_result(
                f"Missing Parameter: {description}",
                success,
                f"Expected rejection for missing parameter: {description}",
                result.get('error', 'No error message')
            )
        
        # Test invalid parameter types
        invalid_type_tests = [
            ({'command': 'GOTO', 'params': {'lat': 'abc', 'lon': 0, 'alt': 100}}, "Non-numeric latitude"),
            ({'command': 'GOTO', 'params': {'lat': 0, 'lon': 'xyz', 'alt': 100}}, "Non-numeric longitude"),
            ({'command': 'GOTO', 'params': {'lat': 0, 'lon': 0, 'alt': 'high'}}, "Non-numeric altitude"),
            ({'command': 'TAKEOFF', 'params': {'altitude': 'five'}}, "Non-numeric takeoff altitude"),
        ]
        
        for command_data, description in invalid_type_tests:
            result = process_flight_command(command_data, self.mock_connection)
            success = not result['success'] and ('invalid' in result.get('error', '').lower() or 
                                               'parameter' in result.get('error', '').lower())
            self.log_test_result(
                f"Invalid Parameter Type: {description}",
                success,
                f"Expected rejection for invalid parameter type: {description}",
                result.get('error', 'No error message')
            )
    
    def test_safety_critical_commands(self):
        """Test that safety-critical commands are properly identified"""
        print("\n🛡️ TESTING SAFETY-CRITICAL COMMAND IDENTIFICATION")
        print("=" * 60)
        
        # Commands that should require safety confirmation
        safety_commands = ['ARM', 'DISARM', 'TAKEOFF', 'LAND', 'RTL']
        
        # Test that these commands execute (backend doesn't handle confirmation, UI does)
        for command in safety_commands:
            if command == 'ARM':
                result = send_arm_disarm_command(self.mock_connection, arm=True)
            elif command == 'DISARM':
                result = send_arm_disarm_command(self.mock_connection, arm=False)
            elif command == 'TAKEOFF':
                result = send_takeoff_command(self.mock_connection, 10)
            elif command == 'LAND':
                result = send_land_command(self.mock_connection)
            elif command == 'RTL':
                result = send_rtl_command(self.mock_connection)
            
            success = result['success']  # Backend should accept valid commands
            self.log_test_result(
                f"Safety Command Backend: {command}",
                success,
                f"Backend should accept valid {command} command (UI handles confirmation)",
                result.get('message', 'Command processed')
            )
        
        # Test unknown commands are rejected
        result = process_flight_command({'command': 'UNKNOWN_COMMAND', 'params': {}}, self.mock_connection)
        success = not result['success'] and 'unknown' in result.get('error', '').lower()
        self.log_test_result(
            "Unknown Command Rejection",
            success,
            "Unknown commands should be rejected",
            result.get('error', 'No error message')
        )
    
    def test_error_message_quality(self):
        """Test that error messages are helpful and informative"""
        print("\n💬 TESTING ERROR MESSAGE QUALITY")
        print("=" * 60)
        
        # Test coordinate validation error messages
        result = send_goto_command(self.mock_connection, 91, 0, 100)
        lat_error = result.get('error', '')
        lat_helpful = ('latitude' in lat_error.lower() and 
                      ('90' in lat_error or '-90' in lat_error or 'range' in lat_error.lower()))
        self.log_test_result(
            "Latitude Error Message Quality",
            lat_helpful,
            "Latitude error should mention valid range (-90 to 90)",
            lat_error
        )
        
        result = send_goto_command(self.mock_connection, 0, 181, 100)
        lon_error = result.get('error', '')
        lon_helpful = ('longitude' in lon_error.lower() and 
                      ('180' in lon_error or '-180' in lon_error or 'range' in lon_error.lower()))
        self.log_test_result(
            "Longitude Error Message Quality",
            lon_helpful,
            "Longitude error should mention valid range (-180 to 180)",
            lon_error
        )
        
        result = send_goto_command(self.mock_connection, 0, 0, 5001)
        alt_error = result.get('error', '')
        alt_helpful = ('altitude' in alt_error.lower() and 
                      ('5000' in alt_error or '-100' in alt_error or 'range' in alt_error.lower()))
        self.log_test_result(
            "Altitude Error Message Quality",
            alt_helpful,
            "Altitude error should mention valid range (-100 to 5000)",
            alt_error
        )
        
        # Test takeoff altitude error message
        result = send_takeoff_command(self.mock_connection, 101)
        takeoff_error = result.get('error', '')
        takeoff_helpful = ('altitude' in takeoff_error.lower() and 
                          ('100' in takeoff_error or '0' in takeoff_error))
        self.log_test_result(
            "Takeoff Altitude Error Quality",
            takeoff_helpful,
            "Takeoff altitude error should mention valid range",
            takeoff_error
        )
        
        # Test mode validation error message
        result = send_mode_change_command(self.mock_connection, "INVALID_MODE")
        mode_error = result.get('error', '')
        mode_helpful = ('mode' in mode_error.lower() and 
                       ('unknown' in mode_error.lower() or 'available' in mode_error.lower()))
        self.log_test_result(
            "Flight Mode Error Quality",
            mode_helpful,
            "Flight mode error should mention unknown mode",
            mode_error
        )
    
    def test_boundary_precision_handling(self):
        """Test handling of boundary values and precision"""
        print("\n⚡ TESTING BOUNDARY VALUE PRECISION")
        print("=" * 60)
        
        # Test exact boundary values
        boundary_tests = [
            (90.0, "Max latitude"),
            (-90.0, "Min latitude"),
            (180.0, "Max longitude"),
            (-180.0, "Min longitude"),
            (5000.0, "Max altitude"),
            (-100.0, "Min altitude")
        ]
        
        # Test latitude boundaries
        for lat_val, description in [(90.0, "Max latitude"), (-90.0, "Min latitude")]:
            result = send_goto_command(self.mock_connection, lat_val, 0, 100)
            success = result['success']
            self.log_test_result(
                f"Latitude Boundary: {lat_val} ({description})",
                success,
                f"Exact boundary value {lat_val} should be accepted",
                result.get('message', 'Accepted')
            )
        
        # Test longitude boundaries
        for lon_val, description in [(180.0, "Max longitude"), (-180.0, "Min longitude")]:
            result = send_goto_command(self.mock_connection, 0, lon_val, 100)
            success = result['success']
            self.log_test_result(
                f"Longitude Boundary: {lon_val} ({description})",
                success,
                f"Exact boundary value {lon_val} should be accepted",
                result.get('message', 'Accepted')
            )
        
        # Test altitude boundaries
        for alt_val, description in [(5000.0, "Max altitude"), (-100.0, "Min altitude")]:
            result = send_goto_command(self.mock_connection, 0, 0, alt_val)
            success = result['success']
            self.log_test_result(
                f"Altitude Boundary: {alt_val} ({description})",
                success,
                f"Exact boundary value {alt_val} should be accepted",
                result.get('message', 'Accepted')
            )
        
        # Test values just outside boundaries
        outside_boundary_tests = [
            (90.000001, 0, 100, "Latitude just above max"),
            (-90.000001, 0, 100, "Latitude just below min"),
            (0, 180.000001, 100, "Longitude just above max"),
            (0, -180.000001, 100, "Longitude just below min"),
            (0, 0, 5000.001, "Altitude just above max"),
            (0, 0, -100.001, "Altitude just below min")
        ]
        
        for lat, lon, alt, description in outside_boundary_tests:
            result = send_goto_command(self.mock_connection, lat, lon, alt)
            success = not result['success']  # Should be rejected
            self.log_test_result(
                f"Outside Boundary: {description}",
                success,
                f"Value just outside boundary should be rejected: {description}",
                result.get('error', 'No error')
            )
    
    def analyze_frontend_validation(self):
        """Analyze frontend JavaScript validation code"""
        print("\n🌐 ANALYZING FRONTEND VALIDATION CODE")
        print("=" * 60)
        
        try:
            # Read connection manager JavaScript
            with open('static/js/connection-manager.js', 'r') as f:
                connection_js = f.read()
            
            # Check for IP validation
            ip_validation = 'validateIP' in connection_js and 'ipRegex' in connection_js
            self.log_test_result(
                "Frontend IP Validation Function",
                ip_validation,
                "Connection manager should have IP validation function",
                "Found validateIP function" if ip_validation else "Missing IP validation"
            )
            
            # Check for port validation
            port_validation = 'validatePortInput' in connection_js and ('1' in connection_js and '65535' in connection_js)
            self.log_test_result(
                "Frontend Port Validation Function",
                port_validation,
                "Connection manager should validate port range 1-65535",
                "Found port validation" if port_validation else "Missing port validation"
            )
            
            # Read navigation controls JavaScript
            with open('static/js/navigation-controls.js', 'r') as f:
                nav_js = f.read()
            
            # Check for coordinate validation
            lat_validation = 'validateLatitudeInput' in nav_js and ('-90' in nav_js and '90' in nav_js)
            self.log_test_result(
                "Frontend Latitude Validation",
                lat_validation,
                "Navigation controls should validate latitude range -90 to 90",
                "Found latitude validation" if lat_validation else "Missing latitude validation"
            )
            
            lon_validation = 'validateLongitudeInput' in nav_js and ('-180' in nav_js and '180' in nav_js)
            self.log_test_result(
                "Frontend Longitude Validation",
                lon_validation,
                "Navigation controls should validate longitude range -180 to 180",
                "Found longitude validation" if lon_validation else "Missing longitude validation"
            )
            
            alt_validation = 'validateAltitudeInput' in nav_js and ('-100' in nav_js and '5000' in nav_js)
            self.log_test_result(
                "Frontend Altitude Validation",
                alt_validation,
                "Navigation controls should validate altitude range -100 to 5000",
                "Found altitude validation" if alt_validation else "Missing altitude validation"
            )
            
            # Read flight controls JavaScript
            with open('static/js/flight-controls.js', 'r') as f:
                flight_js = f.read()
            
            # Check for safety confirmations
            safety_confirmation = 'handleSafetyCommand' in flight_js and 'showConfirmation' in flight_js
            self.log_test_result(
                "Frontend Safety Confirmations",
                safety_confirmation,
                "Flight controls should require safety confirmations",
                "Found safety confirmation system" if safety_confirmation else "Missing safety confirmations"
            )
            
            # Check for takeoff altitude validation
            takeoff_validation = 'validateTakeoffAltitude' in flight_js and ('1' in flight_js and '1000' in flight_js)
            self.log_test_result(
                "Frontend Takeoff Altitude Validation",
                takeoff_validation,
                "Flight controls should validate takeoff altitude 1-1000m",
                "Found takeoff validation" if takeoff_validation else "Missing takeoff validation"
            )
            
        except FileNotFoundError as e:
            self.log_test_result(
                "Frontend Code Analysis",
                False,
                f"Could not read frontend JavaScript files: {e}",
                "JavaScript files not found"
            )
    
    def test_server_health_and_endpoints(self):
        """Test server health and validation endpoints"""
        print("\n🔧 TESTING SERVER HEALTH AND ENDPOINTS")
        print("=" * 60)
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:5001/health", timeout=5)
            health_ok = response.status_code == 200
            self.log_test_result(
                "Server Health Endpoint",
                health_ok,
                "Health endpoint should return 200 OK",
                f"Status: {response.status_code}" if not health_ok else "Health OK"
            )
            
            if health_ok:
                health_data = response.json()
                has_status = 'status' in health_data
                self.log_test_result(
                    "Health Endpoint Data",
                    has_status,
                    "Health endpoint should return status information",
                    f"Data: {health_data}"
                )
            
            # Test main interface endpoint
            response = requests.get("http://localhost:5001/", timeout=5)
            interface_ok = response.status_code == 200
            self.log_test_result(
                "Main Interface Endpoint",
                interface_ok,
                "Main interface should load successfully",
                f"Status: {response.status_code}" if not interface_ok else "Interface loaded"
            )
            
        except requests.exceptions.RequestException as e:
            self.log_test_result(
                "Server Connection Test",
                False,
                "Could not connect to WebGCS server",
                f"Connection error: {e}"
            )
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 STARTING DIRECT UI VALIDATION TESTING")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_coordinate_validation()
        self.test_takeoff_altitude_validation()
        self.test_flight_mode_validation()
        self.test_command_parameter_validation()
        self.test_safety_critical_commands()
        self.test_error_message_quality()
        self.test_boundary_precision_handling()
        self.analyze_frontend_validation()
        self.test_server_health_and_endpoints()
        
        # Generate summary report
        end_time = time.time()
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['status'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("🏁 DIRECT UI VALIDATION TEST RESULTS")
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
        
        # Validation Summary by Category
        print(f"\n🛡️ VALIDATION TESTING SUMMARY:")
        
        categories = {
            'Backend Coordinate Validation': ['Latitude', 'Longitude', 'Altitude', 'Coordinates'],
            'Backend Command Validation': ['Takeoff', 'Flight Mode', 'Parameter', 'Safety Command'],
            'Error Message Quality': ['Error Message', 'Error Quality'],
            'Boundary Condition Handling': ['Boundary', 'Precision'],
            'Frontend Code Analysis': ['Frontend'],
            'Server Health': ['Server', 'Health', 'Endpoint']
        }
        
        for category, keywords in categories.items():
            category_tests = [r for r in self.test_results 
                            if any(keyword in r['test'] for keyword in keywords)]
            if category_tests:
                passed = sum(1 for r in category_tests if r['status'])
                total = len(category_tests)
                percentage = (passed / total) * 100
                print(f"  {category}: {passed}/{total} ({percentage:.0f}%)")
        
        # Key Findings
        print(f"\n🔍 KEY VALIDATION FINDINGS:")
        
        # Check critical validation areas
        coordinate_tests = [r for r in self.test_results if 'Coordinate' in r['test'] or 'Latitude' in r['test'] or 'Longitude' in r['test'] or 'Altitude' in r['test']]
        coord_success = sum(1 for r in coordinate_tests if r['status']) / len(coordinate_tests) * 100 if coordinate_tests else 0
        
        safety_tests = [r for r in self.test_results if 'Safety' in r['test'] or 'Confirmation' in r['test']]  
        safety_success = sum(1 for r in safety_tests if r['status']) / len(safety_tests) * 100 if safety_tests else 0
        
        error_tests = [r for r in self.test_results if 'Error' in r['test']]
        error_success = sum(1 for r in error_tests if r['status']) / len(error_tests) * 100 if error_tests else 0
        
        boundary_tests = [r for r in self.test_results if 'Boundary' in r['test']]
        boundary_success = sum(1 for r in boundary_tests if r['status']) / len(boundary_tests) * 100 if boundary_tests else 0
        
        print(f"  • Coordinate Validation: {coord_success:.0f}% effective")
        print(f"  • Safety Systems: {safety_success:.0f}% implemented")
        print(f"  • Error Message Quality: {error_success:.0f}% helpful")
        print(f"  • Boundary Handling: {boundary_success:.0f}% robust")
        
        # Overall Assessment
        overall_success = (passed_tests / total_tests) * 100
        print(f"\n🎯 OVERALL VALIDATION ASSESSMENT:")
        if overall_success >= 95:
            print("🌟 EXCELLENT: WebGCS has comprehensive input validation and safety systems")
            print("   ✅ All critical validation functions working correctly")
            print("   ✅ Error messages are clear and helpful")
            print("   ✅ Safety confirmations properly implemented")
            print("   ✅ Boundary conditions handled robustly")
        elif overall_success >= 85:
            print("✅ GOOD: WebGCS has solid input validation with minor areas for improvement")
            print("   ✅ Core validation functions working well")
            print("   ⚠️  Some areas may need enhancement")
        elif overall_success >= 70:
            print("⚠️ FAIR: WebGCS has basic validation but needs improvements")
            print("   ⚠️  Several validation issues found")
            print("   🔧 Recommend addressing failed tests")
        else:
            print("❌ POOR: WebGCS validation needs significant improvements")
            print("   ❌ Critical validation failures detected") 
            print("   🚨 Safety concerns - immediate fixes needed")
        
        # Recommendations
        if failed_tests > 0:
            print(f"\n📋 RECOMMENDATIONS:")
            if any('Frontend' in test for test in self.failed_tests):
                print("  🌐 Review frontend JavaScript validation functions")
            if any('Error' in test for test in self.failed_tests):
                print("  💬 Improve error message clarity and helpfulness")
            if any('Boundary' in test for test in self.failed_tests):
                print("  ⚡ Strengthen boundary condition handling")
            if any('Safety' in test for test in self.failed_tests):
                print("  🛡️ Enhance safety confirmation systems")
        
        return overall_success >= 85


class MockMAVLinkConnection:
    """Mock MAVLink connection for testing validation without real drone"""
    def __init__(self):
        self.target_system = 1
        self.target_component = 1
        self.mav = self
    
    def command_long_send(self, *args, **kwargs):
        """Mock command sending - always succeeds for testing validation logic"""
        pass
    
    def set_mode_send(self, *args, **kwargs):
        """Mock mode setting - always succeeds for testing validation logic"""
        pass


def main():
    """Main test execution"""
    
    print("✅ Starting Direct UI Validation Testing")
    print("   Testing backend validation logic without browser automation")
    
    # Run comprehensive validation tests
    tester = DirectValidationTester()
    
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
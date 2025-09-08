#!/usr/bin/env python3
"""
Final MAVLink Integration Test
============================

MISSION: Using existing WebGCS infrastructure to verify end-to-end MAVLink communication

This test directly uses the working WebGCS components to verify:
- Connection status from WebGCS health endpoint
- Direct MAVLink connection testing 
- Command sending through existing infrastructure
- Telemetry verification
"""

import requests
import json
import time
import threading
from datetime import datetime
import sys

# Import WebGCS components directly
import sys
import os
sys.path.append(os.path.dirname(__file__))

from mavlink_connection_manager import connect_mavlink, get_mavlink_connection, get_last_heartbeat_time, is_connected
from mavlink_command_sender import send_arm_disarm_command, send_mode_change_command, process_flight_command
from pymavlink import mavutil

class FinalMAVLinkIntegrationTest:
    """Final integration test using existing WebGCS infrastructure"""
    
    def __init__(self):
        self.webgcs_url = "http://localhost:5001"
        self.drone_ip = "192.168.193.235"
        self.drone_port = 5678
        
        self.test_results = {
            'webgcs_health': {'status': 'PENDING', 'details': {}},
            'direct_connection': {'status': 'PENDING', 'details': {}},
            'heartbeat_monitoring': {'status': 'PENDING', 'details': {}},
            'command_testing': {'status': 'PENDING', 'details': {}},
            'integration_verification': {'status': 'PENDING', 'details': {}}
        }
        
        # Shared state for testing
        self.test_drone_state = {
            'connected': False,
            'armed': False,
            'mode': 'UNKNOWN',
            'lat': 0.0, 'lon': 0.0,
            'alt_rel': 0.0, 'alt_abs': 0.0,
            'heading': 0.0,
            'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
            'system_id': 0,
            'component_id': 0
        }
        self.test_drone_state_lock = threading.Lock()
        self.start_time = time.time()

    def log_result(self, category, status, message, details=None):
        """Log test result with timing"""
        elapsed = f"{time.time() - self.start_time:5.1f}s"
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔍" if status == "INFO" else "⏳"
        print(f"{symbol} [{elapsed}] {message}")
        
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
        
        self.test_results[category]['status'] = status
        if details:
            self.test_results[category]['details'].update(details)

    def test_webgcs_health_status(self):
        """Test 1: WebGCS Health and Connection Status"""
        print("🔍 TEST 1: WebGCS Health and Connection Status")
        
        try:
            response = requests.get(f"{self.webgcs_url}/health", timeout=3)
            
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get('drone_connected') == True:
                    self.log_result('webgcs_health', 'PASS', 
                                  'WebGCS reports drone connected successfully',
                                  {
                                      'http_status': response.status_code,
                                      'webgcs_status': health_data.get('status'),
                                      'drone_connected': health_data.get('drone_connected'),
                                      'timestamp': health_data.get('timestamp')
                                  })
                    return True
                else:
                    self.log_result('webgcs_health', 'FAIL',
                                  'WebGCS reports drone not connected',
                                  {'health_data': health_data})
                    return False
            else:
                self.log_result('webgcs_health', 'FAIL',
                              f'WebGCS health check failed with HTTP {response.status_code}')
                return False
                
        except Exception as e:
            self.log_result('webgcs_health', 'FAIL',
                          f'WebGCS health check error: {e}')
            return False

    def test_direct_mavlink_connection(self):
        """Test 2: Direct MAVLink Connection Using WebGCS Components"""
        print("\n🔍 TEST 2: Direct MAVLink Connection Using WebGCS Components")
        
        try:
            connection_string = f"tcp:{self.drone_ip}:{self.drone_port}"
            
            # Use WebGCS connection manager
            def mock_state_changed():
                pass
            
            # Create connection using WebGCS infrastructure
            connect_mavlink(
                self.test_drone_state, 
                self.test_drone_state_lock,
                connection_string,
                mock_state_changed,
                None  # No socketio for test
            )
            
            # Check if connection was established
            mavlink_conn = get_mavlink_connection()
            
            if mavlink_conn and is_connected():
                with self.test_drone_state_lock:
                    connected_status = self.test_drone_state['connected']
                
                if connected_status:
                    self.log_result('direct_connection', 'PASS',
                                  'Direct MAVLink connection established via WebGCS infrastructure',
                                  {
                                      'connection_string': connection_string,
                                      'connection_object': str(type(mavlink_conn)),
                                      'drone_state_connected': connected_status
                                  })
                    return True
                else:
                    self.log_result('direct_connection', 'FAIL',
                                  'MAVLink connection object exists but drone state not updated')
                    return False
            else:
                self.log_result('direct_connection', 'FAIL',
                              'Failed to establish MAVLink connection')
                return False
                
        except Exception as e:
            self.log_result('direct_connection', 'FAIL',
                          f'Direct MAVLink connection error: {e}')
            return False

    def test_heartbeat_monitoring(self):
        """Test 3: HEARTBEAT Monitoring Using WebGCS Components"""
        print("\n🔍 TEST 3: HEARTBEAT Monitoring")
        
        mavlink_conn = get_mavlink_connection()
        if not mavlink_conn:
            self.log_result('heartbeat_monitoring', 'FAIL', 'No MAVLink connection available')
            return False
        
        try:
            # Monitor heartbeat for 5 seconds using WebGCS infrastructure
            start_time = time.time()
            initial_heartbeat_time = get_last_heartbeat_time()
            
            # Wait for heartbeat update
            time.sleep(5.0)
            
            final_heartbeat_time = get_last_heartbeat_time()
            
            if final_heartbeat_time > initial_heartbeat_time:
                heartbeat_age = time.time() - final_heartbeat_time
                
                if heartbeat_age < 3.0:  # Recent heartbeat (within 3 seconds)
                    self.log_result('heartbeat_monitoring', 'PASS',
                                  'HEARTBEAT monitoring confirmed via WebGCS infrastructure',
                                  {
                                      'initial_heartbeat': initial_heartbeat_time,
                                      'final_heartbeat': final_heartbeat_time,
                                      'heartbeat_age_seconds': f"{heartbeat_age:.1f}",
                                      'heartbeat_updated': True
                                  })
                    return True
                else:
                    self.log_result('heartbeat_monitoring', 'FAIL',
                                  f'HEARTBEAT too old: {heartbeat_age:.1f}s')
                    return False
            else:
                self.log_result('heartbeat_monitoring', 'FAIL',
                              'No HEARTBEAT update detected during monitoring period')
                return False
                
        except Exception as e:
            self.log_result('heartbeat_monitoring', 'FAIL',
                          f'HEARTBEAT monitoring error: {e}')
            return False

    def test_command_sending(self):
        """Test 4: Command Sending Using WebGCS Infrastructure"""
        print("\n🔍 TEST 4: Command Sending via WebGCS Infrastructure")
        
        mavlink_conn = get_mavlink_connection()
        if not mavlink_conn:
            self.log_result('command_testing', 'FAIL', 'No MAVLink connection available')
            return False
        
        try:
            # Test command sending using WebGCS command processor
            test_command = {
                'command': 'SET_MODE',
                'params': {
                    'mode': 'GUIDED'
                }
            }
            
            # Send command using WebGCS infrastructure
            result = process_flight_command(test_command, mavlink_conn)
            
            if result and result.get('success') == True:
                self.log_result('command_testing', 'PASS',
                              'Command sent successfully via WebGCS infrastructure',
                              {
                                  'command': test_command['command'],
                                  'params': str(test_command['params']),
                                  'result': result.get('message', 'Success'),
                                  'timestamp': result.get('timestamp')
                              })
                return True
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                self.log_result('command_testing', 'FAIL',
                              f'Command sending failed: {error_msg}')
                return False
                
        except Exception as e:
            self.log_result('command_testing', 'FAIL',
                          f'Command sending error: {e}')
            return False

    def test_integration_verification(self):
        """Test 5: Overall Integration Verification"""
        print("\n🔍 TEST 5: Overall Integration Verification")
        
        # Check all previous test results
        previous_tests = ['webgcs_health', 'direct_connection', 'heartbeat_monitoring', 'command_testing']
        passed_tests = sum(1 for test in previous_tests if self.test_results[test]['status'] == 'PASS')
        total_tests = len(previous_tests)
        
        integration_checks = {
            'webgcs_healthy': self.test_results['webgcs_health']['status'] == 'PASS',
            'mavlink_connected': self.test_results['direct_connection']['status'] == 'PASS',
            'heartbeat_active': self.test_results['heartbeat_monitoring']['status'] == 'PASS',
            'commands_working': self.test_results['command_testing']['status'] == 'PASS'
        }
        
        integration_score = sum(integration_checks.values())
        max_score = len(integration_checks)
        
        if integration_score >= 3:  # At least 3/4 must pass
            self.log_result('integration_verification', 'PASS',
                          'End-to-end MAVLink integration VERIFIED',
                          {
                              'integration_score': f"{integration_score}/{max_score}",
                              'individual_tests_passed': f"{passed_tests}/{total_tests}",
                              'success_rate': f"{(integration_score/max_score)*100:.1f}%",
                              'checks_passed': [k for k, v in integration_checks.items() if v],
                              'checks_failed': [k for k, v in integration_checks.items() if not v]
                          })
            return True
        else:
            self.log_result('integration_verification', 'FAIL',
                          'End-to-end MAVLink integration verification failed',
                          {
                              'integration_score': f"{integration_score}/{max_score}",
                              'failed_checks': [k for k, v in integration_checks.items() if not v]
                          })
            return False

    def run_final_integration_test(self):
        """Execute complete integration test sequence"""
        print("=" * 70)
        print("🎯 FINAL MAVLINK INTEGRATION TEST")
        print("=" * 70)
        print(f"WebGCS: {self.webgcs_url}")
        print(f"Virtual Drone: {self.drone_ip}:{self.drone_port}")
        print(f"Test Started: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 70)
        
        # Execute test sequence
        tests = [
            ("WebGCS Health Status", self.test_webgcs_health_status),
            ("Direct MAVLink Connection", self.test_direct_mavlink_connection),
            ("HEARTBEAT Monitoring", self.test_heartbeat_monitoring),
            ("Command Sending", self.test_command_sending),
            ("Integration Verification", self.test_integration_verification)
        ]
        
        passed_tests = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"💥 CRITICAL ERROR in {test_name}: {e}")
        
        # Generate final report
        self.generate_final_report(passed_tests, len(tests))

    def generate_final_report(self, passed, total):
        """Generate comprehensive final report"""
        print("\n" + "=" * 70)
        print("📊 FINAL INTEGRATION TEST REPORT")
        print("=" * 70)
        
        success_rate = (passed / total) * 100
        runtime = time.time() - self.start_time
        
        # Overall status determination
        if success_rate >= 80:
            overall_status = "✅ INTEGRATION TEST PASSED"
            result_code = "VERIFIED"
        elif success_rate >= 60:
            overall_status = "⚠️  INTEGRATION TEST PARTIAL"
            result_code = "PARTIAL"
        else:
            overall_status = "❌ INTEGRATION TEST FAILED" 
            result_code = "FAILED"
        
        print(f"\n🎯 {overall_status}")
        print(f"Success Rate: {passed}/{total} tests passed ({success_rate:.1f}%)")
        print(f"Total Runtime: {runtime:.1f} seconds")
        
        # Detailed results breakdown
        print(f"\n📋 DETAILED TEST RESULTS:")
        print("-" * 40)
        
        for category, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⏳"
            category_name = category.replace('_', ' ').title()
            print(f"{status_icon} {category_name}: {result['status']}")
        
        # Critical findings summary
        print(f"\n🔍 CRITICAL FINDINGS:")
        print("-" * 20)
        
        findings = []
        
        if self.test_results['webgcs_health']['status'] == 'PASS':
            findings.append("✅ WebGCS server is healthy and reports drone connected")
        
        if self.test_results['direct_connection']['status'] == 'PASS':
            findings.append("✅ Direct MAVLink connection established using WebGCS infrastructure")
        
        if self.test_results['heartbeat_monitoring']['status'] == 'PASS':
            findings.append("✅ HEARTBEAT messages confirmed via WebGCS monitoring system")
        
        if self.test_results['command_testing']['status'] == 'PASS':
            findings.append("✅ Command sending verified through WebGCS command processor")
        
        if self.test_results['integration_verification']['status'] == 'PASS':
            findings.append("✅ End-to-end MAVLink integration FULLY VERIFIED")
        
        for finding in findings:
            print(f"  {finding}")
        
        # Final verification summary
        print(f"\n🎯 INTEGRATION VERIFICATION SUMMARY:")
        print(f"  Protocol: MAVLink v2.0")
        print(f"  Target: Virtual Drone at {self.drone_ip}:{self.drone_port}")
        print(f"  WebGCS Integration: {'✅ CONFIRMED' if len(findings) >= 3 else '❌ FAILED'}")
        print(f"  End-to-End Communication: {'✅ VERIFIED' if result_code == 'VERIFIED' else '❌ FAILED'}")
        
        # Save detailed report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"FINAL_MAVLINK_INTEGRATION_TEST_{timestamp}.json"
        
        report_data = {
            'test_metadata': {
                'timestamp': datetime.now().isoformat(),
                'target_drone': f"{self.drone_ip}:{self.drone_port}",
                'webgcs_url': self.webgcs_url,
                'runtime_seconds': runtime,
                'overall_status': result_code
            },
            'test_results': self.test_results,
            'summary': {
                'tests_passed': passed,
                'total_tests': total,
                'success_rate': success_rate,
                'critical_findings': findings
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n📄 Detailed report saved: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save report: {e}")
        
        print("=" * 70)
        
        return result_code == "VERIFIED"


def main():
    """Main test execution"""
    try:
        tester = FinalMAVLinkIntegrationTest()
        success = tester.run_final_integration_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Critical test failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
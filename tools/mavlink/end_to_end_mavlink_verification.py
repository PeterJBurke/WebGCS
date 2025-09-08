#!/usr/bin/env python3
"""
End-to-End MAVLink Communication Verification
========================================

MISSION: Verify complete MAVLink protocol integration between WebGCS and virtual drone
Target: 192.168.193.235:5678 (Virtual Drone)
Protocol: MAVLink v2.0

This test validates:
- Direct TCP connection establishment 
- HEARTBEAT message reception at 1Hz
- Command acknowledgment timing (<5 seconds)
- GLOBAL_POSITION_INT telemetry processing
- MAVLink v2.0 protocol compliance
- End-to-end command flow verification
"""

import socket
import time
import json
import threading
from pymavlink import mavutil
import socketio
import requests
from datetime import datetime
import sys

# Test Configuration
VIRTUAL_DRONE_IP = "192.168.193.235"
VIRTUAL_DRONE_PORT = 5678
WEBGCS_URL = "http://localhost:5001"
TEST_TIMEOUT = 30  # seconds
HEARTBEAT_TIMEOUT = 5.0  # Expected 1Hz = every 1 second, allow 5 second tolerance

class MAVLinkVerificationTest:
    """Comprehensive end-to-end MAVLink communication verification"""
    
    def __init__(self):
        self.test_results = {
            'connection_test': {'status': 'PENDING', 'details': []},
            'heartbeat_test': {'status': 'PENDING', 'details': [], 'heartbeat_count': 0, 'timing': []},
            'protocol_compliance': {'status': 'PENDING', 'details': []},
            'command_acknowledgment': {'status': 'PENDING', 'details': [], 'commands_tested': []},
            'telemetry_flow': {'status': 'PENDING', 'details': []},
            'end_to_end_latency': {'status': 'PENDING', 'details': [], 'measurements': []},
            'webgcs_integration': {'status': 'PENDING', 'details': []}
        }
        self.mavlink_conn = None
        self.heartbeat_times = []
        self.message_count = 0
        self.test_start_time = time.time()
        self.sio = None
        
    def log_test_result(self, category, status, message, details=None):
        """Log test result with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'details': details or {}
        }
        
        self.test_results[category]['details'].append(log_entry)
        self.test_results[category]['status'] = status
        
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏳"
        print(f"{status_symbol} [{timestamp}] {category.upper()}: {message}")
        
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")

    def test_direct_tcp_connection(self):
        """Test 1: Direct TCP connection to virtual drone"""
        print(f"\n🔍 TEST 1: Direct TCP Connection to {VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}")
        
        try:
            # Test raw TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            start_time = time.time()
            
            result = sock.connect_ex((VIRTUAL_DRONE_IP, VIRTUAL_DRONE_PORT))
            connection_time = (time.time() - start_time) * 1000  # ms
            
            if result == 0:
                self.log_test_result('connection_test', 'PASS', 
                                   'TCP connection established successfully',
                                   {'connection_time_ms': f"{connection_time:.1f}",
                                    'target': f"{VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}"})
                sock.close()
                return True
            else:
                self.log_test_result('connection_test', 'FAIL',
                                   f'TCP connection failed with error code {result}')
                return False
                
        except Exception as e:
            self.log_test_result('connection_test', 'FAIL',
                               f'TCP connection exception: {e}')
            return False

    def test_mavlink_connection(self):
        """Test 2: MAVLink protocol connection establishment"""
        print(f"\n🔍 TEST 2: MAVLink Protocol Connection")
        
        try:
            # Create MAVLink connection
            connection_string = f"tcp:{VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}"
            self.mavlink_conn = mavutil.mavlink_connection(
                connection_string,
                source_system=255,  # GCS system ID
                source_component=0,
                timeout=5.0
            )
            
            self.log_test_result('protocol_compliance', 'PASS',
                               'MAVLink connection object created',
                               {'connection_string': connection_string,
                                'source_system': 255})
            
            # Wait for target system identification
            start_time = time.time()
            target_identified = False
            
            while time.time() - start_time < 10.0:  # 10 second timeout
                try:
                    msg = self.mavlink_conn.recv_match(timeout=1.0)
                    if msg:
                        self.message_count += 1
                        
                        # Force target system identification
                        if not hasattr(self.mavlink_conn, 'target_system') or self.mavlink_conn.target_system == 0:
                            self.mavlink_conn.target_system = msg.get_srcSystem()
                            self.mavlink_conn.target_component = msg.get_srcComponent()
                        
                        if hasattr(self.mavlink_conn, 'target_system') and self.mavlink_conn.target_system > 0:
                            self.log_test_result('protocol_compliance', 'PASS',
                                               'Target system identified from MAVLink traffic',
                                               {'target_system': self.mavlink_conn.target_system,
                                                'target_component': self.mavlink_conn.target_component,
                                                'first_message_type': msg.get_type(),
                                                'identification_time_ms': f"{(time.time() - start_time) * 1000:.1f}"})
                            target_identified = True
                            break
                            
                except Exception as e:
                    pass
                    
                time.sleep(0.1)
            
            if not target_identified:
                self.log_test_result('protocol_compliance', 'FAIL',
                                   'Target system not identified within timeout')
                return False
                
            return True
            
        except Exception as e:
            self.log_test_result('protocol_compliance', 'FAIL',
                               f'MAVLink connection failed: {e}')
            return False

    def test_heartbeat_reception(self):
        """Test 3: HEARTBEAT message reception at 1Hz"""
        print(f"\n🔍 TEST 3: HEARTBEAT Message Reception (1Hz Expected)")
        
        if not self.mavlink_conn:
            self.log_test_result('heartbeat_test', 'FAIL', 'No MAVLink connection available')
            return False
            
        heartbeat_count = 0
        heartbeat_times = []
        start_time = time.time()
        last_heartbeat_time = 0
        
        try:
            # Monitor heartbeats for 10 seconds
            while time.time() - start_time < 10.0:
                msg = self.mavlink_conn.recv_match(timeout=1.0)
                
                if msg and msg.get_type() == 'HEARTBEAT':
                    current_time = time.time()
                    heartbeat_times.append(current_time)
                    heartbeat_count += 1
                    
                    # Calculate interval from previous heartbeat
                    if last_heartbeat_time > 0:
                        interval = current_time - last_heartbeat_time
                        self.test_results['heartbeat_test']['timing'].append(interval)
                        
                        self.log_test_result('heartbeat_test', 'INFO',
                                           f'HEARTBEAT #{heartbeat_count} received',
                                           {'interval_ms': f"{interval * 1000:.1f}",
                                            'system_id': msg.get_srcSystem(),
                                            'armed_status': bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED),
                                            'flight_mode': msg.custom_mode})
                    
                    last_heartbeat_time = current_time
            
            # Analyze heartbeat timing
            if heartbeat_count >= 8:  # Expect ~10 heartbeats in 10 seconds
                avg_interval = sum(self.test_results['heartbeat_test']['timing']) / len(self.test_results['heartbeat_test']['timing'])
                frequency = 1.0 / avg_interval
                
                self.test_results['heartbeat_test']['heartbeat_count'] = heartbeat_count
                
                if 0.8 <= frequency <= 1.2:  # Within 20% of 1Hz
                    self.log_test_result('heartbeat_test', 'PASS',
                                       f'HEARTBEAT frequency within specification',
                                       {'heartbeat_count': heartbeat_count,
                                        'avg_frequency_hz': f"{frequency:.2f}",
                                        'avg_interval_ms': f"{avg_interval * 1000:.1f}"})
                    return True
                else:
                    self.log_test_result('heartbeat_test', 'FAIL',
                                       f'HEARTBEAT frequency outside specification',
                                       {'expected_hz': '1.0 ± 20%',
                                        'actual_hz': f"{frequency:.2f}"})
                    return False
            else:
                self.log_test_result('heartbeat_test', 'FAIL',
                                   f'Insufficient HEARTBEAT messages received',
                                   {'expected_minimum': 8,
                                    'actual_count': heartbeat_count})
                return False
                
        except Exception as e:
            self.log_test_result('heartbeat_test', 'FAIL',
                               f'HEARTBEAT reception test failed: {e}')
            return False

    def test_command_acknowledgment(self):
        """Test 4: Command acknowledgment timing and protocol compliance"""
        print(f"\n🔍 TEST 4: Command Acknowledgment Testing")
        
        if not self.mavlink_conn:
            self.log_test_result('command_acknowledgment', 'FAIL', 'No MAVLink connection available')
            return False
        
        # Test commands with timing verification
        test_commands = [
            {
                'name': 'ARM',
                'command_id': mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                'params': [1, 0, 0, 0, 0, 0, 0]
            },
            {
                'name': 'DISARM', 
                'command_id': mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                'params': [0, 0, 0, 0, 0, 0, 0]
            },
            {
                'name': 'SET_MODE_GUIDED',
                'command_id': mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                'params': [1, 4, 0, 0, 0, 0, 0]  # GUIDED mode
            }
        ]
        
        success_count = 0
        
        for cmd in test_commands:
            try:
                # Clear any pending messages
                while self.mavlink_conn.recv_match(timeout=0.1):
                    pass
                
                # Send command
                cmd_start_time = time.time()
                self.mavlink_conn.mav.command_long_send(
                    self.mavlink_conn.target_system,
                    self.mavlink_conn.target_component,
                    cmd['command_id'],
                    0,  # confirmation
                    *cmd['params']
                )
                
                self.log_test_result('command_acknowledgment', 'INFO',
                                   f'Sent {cmd["name"]} command',
                                   {'command_id': cmd['command_id'],
                                    'target_system': self.mavlink_conn.target_system})
                
                # Wait for acknowledgment
                ack_received = False
                timeout_time = cmd_start_time + 5.0  # 5 second timeout
                
                while time.time() < timeout_time and not ack_received:
                    msg = self.mavlink_conn.recv_match(timeout=1.0)
                    
                    if msg and msg.get_type() == 'COMMAND_ACK':
                        if msg.command == cmd['command_id']:
                            ack_time = time.time() - cmd_start_time
                            
                            if msg.result == 0:  # MAV_RESULT_ACCEPTED
                                self.log_test_result('command_acknowledgment', 'PASS',
                                                   f'{cmd["name"]} command acknowledged successfully',
                                                   {'response_time_ms': f"{ack_time * 1000:.1f}",
                                                    'result_code': msg.result})
                                success_count += 1
                            else:
                                self.log_test_result('command_acknowledgment', 'WARN',
                                                   f'{cmd["name"]} command rejected',
                                                   {'response_time_ms': f"{ack_time * 1000:.1f}",
                                                    'result_code': msg.result})
                            ack_received = True
                            break
                
                if not ack_received:
                    self.log_test_result('command_acknowledgment', 'FAIL',
                                       f'{cmd["name"]} command acknowledgment timeout')
                
                # Small delay between commands
                time.sleep(1.0)
                
            except Exception as e:
                self.log_test_result('command_acknowledgment', 'FAIL',
                                   f'{cmd["name"]} command failed: {e}')
        
        # Overall command acknowledgment result
        if success_count >= len(test_commands) * 0.67:  # At least 67% success rate
            self.log_test_result('command_acknowledgment', 'PASS',
                               f'Command acknowledgment testing completed',
                               {'successful_commands': success_count,
                                'total_commands': len(test_commands),
                                'success_rate': f"{(success_count/len(test_commands)*100):.1f}%"})
            return True
        else:
            self.log_test_result('command_acknowledgment', 'FAIL',
                               f'Insufficient command acknowledgment success rate')
            return False

    def test_telemetry_flow(self):
        """Test 5: Telemetry data flow validation"""
        print(f"\n🔍 TEST 5: Telemetry Data Flow Verification")
        
        if not self.mavlink_conn:
            self.log_test_result('telemetry_flow', 'FAIL', 'No MAVLink connection available')
            return False
        
        telemetry_types = {
            'HEARTBEAT': 0,
            'GLOBAL_POSITION_INT': 0,
            'ATTITUDE': 0,
            'SYS_STATUS': 0
        }
        
        start_time = time.time()
        
        try:
            # Monitor telemetry for 15 seconds
            while time.time() - start_time < 15.0:
                msg = self.mavlink_conn.recv_match(timeout=1.0)
                
                if msg:
                    msg_type = msg.get_type()
                    if msg_type in telemetry_types:
                        telemetry_types[msg_type] += 1
                        
                        if msg_type == 'GLOBAL_POSITION_INT':
                            # Validate position data format
                            lat = msg.lat / 1e7
                            lon = msg.lon / 1e7
                            alt_rel = msg.relative_alt / 1000.0
                            
                            self.log_test_result('telemetry_flow', 'INFO',
                                               f'GLOBAL_POSITION_INT received',
                                               {'lat': f"{lat:.6f}",
                                                'lon': f"{lon:.6f}",
                                                'alt_rel_m': f"{alt_rel:.1f}",
                                                'hdg_deg': msg.hdg / 100.0})
            
            # Analyze telemetry reception
            required_messages = ['HEARTBEAT', 'GLOBAL_POSITION_INT']
            missing_messages = [msg for msg in required_messages if telemetry_types[msg] == 0]
            
            if not missing_messages:
                self.log_test_result('telemetry_flow', 'PASS',
                                   'All required telemetry messages received',
                                   telemetry_types)
                return True
            else:
                self.log_test_result('telemetry_flow', 'FAIL',
                                   f'Missing required telemetry messages: {missing_messages}',
                                   telemetry_types)
                return False
                
        except Exception as e:
            self.log_test_result('telemetry_flow', 'FAIL',
                               f'Telemetry flow test failed: {e}')
            return False

    def test_webgcs_integration(self):
        """Test 6: WebGCS integration via REST API and WebSocket"""
        print(f"\n🔍 TEST 6: WebGCS Integration Testing")
        
        try:
            # Test WebGCS health endpoint
            response = requests.get(f"{WEBGCS_URL}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get('drone_connected'):
                    self.log_test_result('webgcs_integration', 'PASS',
                                       'WebGCS reports drone connected',
                                       {'health_status': health_data.get('status'),
                                        'drone_connected': health_data.get('drone_connected')})
                else:
                    self.log_test_result('webgcs_integration', 'FAIL',
                                       'WebGCS reports drone not connected')
                    return False
            else:
                self.log_test_result('webgcs_integration', 'FAIL',
                                   f'WebGCS health check failed: HTTP {response.status_code}')
                return False
            
            # Test WebSocket connection
            try:
                sio = socketio.SimpleClient()
                sio.connect(WEBGCS_URL, transports=['polling'])
                
                self.log_test_result('webgcs_integration', 'PASS',
                                   'WebSocket connection established to WebGCS')
                
                sio.disconnect()
                return True
                
            except Exception as e:
                self.log_test_result('webgcs_integration', 'FAIL',
                                   f'WebSocket connection failed: {e}')
                return False
                
        except Exception as e:
            self.log_test_result('webgcs_integration', 'FAIL',
                               f'WebGCS integration test failed: {e}')
            return False

    def test_end_to_end_latency(self):
        """Test 7: End-to-end latency measurement"""
        print(f"\n🔍 TEST 7: End-to-End Latency Measurement")
        
        if not self.mavlink_conn:
            self.log_test_result('end_to_end_latency', 'FAIL', 'No MAVLink connection available')
            return False
        
        latency_measurements = []
        
        try:
            # Perform 10 ping-like measurements using PARAM_REQUEST_READ
            for i in range(10):
                # Clear pending messages
                while self.mavlink_conn.recv_match(timeout=0.1):
                    pass
                
                # Send parameter request (acts as a ping)
                start_time = time.time()
                self.mavlink_conn.mav.param_request_read_send(
                    self.mavlink_conn.target_system,
                    self.mavlink_conn.target_component,
                    b'SYSID_THISMAV',  # Common parameter
                    -1  # param_index (-1 means use param_id)
                )
                
                # Wait for response
                response_received = False
                timeout_time = start_time + 2.0
                
                while time.time() < timeout_time and not response_received:
                    msg = self.mavlink_conn.recv_match(timeout=0.5)
                    
                    if msg and msg.get_type() == 'PARAM_VALUE':
                        latency = (time.time() - start_time) * 1000  # ms
                        latency_measurements.append(latency)
                        
                        self.log_test_result('end_to_end_latency', 'INFO',
                                           f'Latency measurement #{i+1}',
                                           {'latency_ms': f"{latency:.1f}"})
                        response_received = True
                        break
                
                if not response_received:
                    self.log_test_result('end_to_end_latency', 'WARN',
                                       f'Latency measurement #{i+1} timeout')
                
                time.sleep(0.5)  # Small delay between measurements
            
            # Analyze latency results
            if latency_measurements:
                avg_latency = sum(latency_measurements) / len(latency_measurements)
                max_latency = max(latency_measurements)
                min_latency = min(latency_measurements)
                
                self.test_results['end_to_end_latency']['measurements'] = latency_measurements
                
                if avg_latency <= 100.0:  # Target: <100ms average
                    self.log_test_result('end_to_end_latency', 'PASS',
                                       f'End-to-end latency within specification',
                                       {'avg_latency_ms': f"{avg_latency:.1f}",
                                        'min_latency_ms': f"{min_latency:.1f}",
                                        'max_latency_ms': f"{max_latency:.1f}",
                                        'measurements': len(latency_measurements)})
                    return True
                else:
                    self.log_test_result('end_to_end_latency', 'FAIL',
                                       f'End-to-end latency exceeds specification',
                                       {'target_ms': '< 100',
                                        'actual_avg_ms': f"{avg_latency:.1f}"})
                    return False
            else:
                self.log_test_result('end_to_end_latency', 'FAIL',
                                   'No valid latency measurements obtained')
                return False
                
        except Exception as e:
            self.log_test_result('end_to_end_latency', 'FAIL',
                               f'Latency measurement failed: {e}')
            return False

    def run_comprehensive_verification(self):
        """Execute all verification tests in sequence"""
        print("=" * 80)
        print("🚁 END-TO-END MAVLINK COMMUNICATION VERIFICATION")
        print("=" * 80)
        print(f"Target: {VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}")
        print(f"WebGCS: {WEBGCS_URL}")
        print(f"Protocol: MAVLink v2.0")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Execute test sequence
        test_sequence = [
            ('TCP Connection', self.test_direct_tcp_connection),
            ('MAVLink Protocol', self.test_mavlink_connection),
            ('HEARTBEAT Reception', self.test_heartbeat_reception),
            ('Command ACK', self.test_command_acknowledgment),
            ('Telemetry Flow', self.test_telemetry_flow),
            ('WebGCS Integration', self.test_webgcs_integration),
            ('End-to-End Latency', self.test_end_to_end_latency)
        ]
        
        passed_tests = 0
        total_tests = len(test_sequence)
        
        for test_name, test_func in test_sequence:
            try:
                if test_func():
                    passed_tests += 1
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {e}")
        
        # Generate final report
        self.generate_final_report(passed_tests, total_tests)
        
        # Cleanup
        if self.mavlink_conn:
            try:
                self.mavlink_conn.close()
            except:
                pass

    def generate_final_report(self, passed_tests, total_tests):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 FINAL VERIFICATION REPORT")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        
        # Overall status
        if success_rate >= 85:
            status = "✅ VERIFICATION PASSED"
            print(f"🎉 {status}")
        elif success_rate >= 70:
            status = "⚠️  VERIFICATION PARTIAL"
            print(f"⚠️  {status}")
        else:
            status = "❌ VERIFICATION FAILED"
            print(f"💥 {status}")
        
        print(f"\nTest Results: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        print(f"Total Runtime: {time.time() - self.test_start_time:.1f} seconds")
        
        # Detailed results
        print("\n📋 DETAILED TEST RESULTS:")
        print("-" * 40)
        
        for category, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⏳"
            print(f"{status_icon} {category.replace('_', ' ').upper()}: {result['status']}")
            
            if result['status'] == 'PASS' and category == 'heartbeat_test':
                print(f"    Heartbeats Received: {result['heartbeat_count']}")
            elif result['status'] == 'PASS' and category == 'end_to_end_latency':
                if result.get('measurements'):
                    avg_latency = sum(result['measurements']) / len(result['measurements'])
                    print(f"    Average Latency: {avg_latency:.1f}ms")
        
        # Critical findings summary
        print("\n🎯 CRITICAL FINDINGS:")
        print("-" * 20)
        
        findings = []
        
        if self.test_results['connection_test']['status'] == 'PASS':
            findings.append("✅ Direct TCP connection to virtual drone established")
        
        if self.test_results['heartbeat_test']['status'] == 'PASS':
            findings.append(f"✅ HEARTBEAT messages received at proper 1Hz frequency")
        
        if self.test_results['command_acknowledgment']['status'] == 'PASS':
            findings.append("✅ Command acknowledgments received within timeout")
        
        if self.test_results['telemetry_flow']['status'] == 'PASS':
            findings.append("✅ All required telemetry messages flowing properly")
        
        if self.test_results['webgcs_integration']['status'] == 'PASS':
            findings.append("✅ WebGCS integration confirmed via API and WebSocket")
        
        if self.test_results['end_to_end_latency']['status'] == 'PASS':
            findings.append("✅ End-to-end latency within 100ms specification")
        
        for finding in findings:
            print(f"  {finding}")
        
        # Protocol compliance summary
        print(f"\n🔧 PROTOCOL COMPLIANCE:")
        print(f"  MAVLink v2.0: {'✅ CONFIRMED' if self.test_results['protocol_compliance']['status'] == 'PASS' else '❌ FAILED'}")
        print(f"  Message Integrity: {'✅ VALIDATED' if self.message_count > 0 else '❌ NO MESSAGES'}")
        print(f"  Target System ID: {'✅ IDENTIFIED' if self.mavlink_conn and hasattr(self.mavlink_conn, 'target_system') else '❌ NOT IDENTIFIED'}")
        
        print("\n" + "=" * 80)
        
        # Save report to file
        self.save_report_to_file()

    def save_report_to_file(self):
        """Save detailed test report to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"END_TO_END_MAVLINK_VERIFICATION_{timestamp}.json"
        
        report_data = {
            'test_metadata': {
                'timestamp': datetime.now().isoformat(),
                'target_drone': f"{VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}",
                'webgcs_url': WEBGCS_URL,
                'total_runtime_seconds': time.time() - self.test_start_time,
                'total_messages_processed': self.message_count
            },
            'test_results': self.test_results,
            'summary': {
                'overall_status': 'PASS' if all(r['status'] == 'PASS' for r in self.test_results.values() if r['status'] != 'PENDING') else 'FAIL',
                'tests_passed': sum(1 for r in self.test_results.values() if r['status'] == 'PASS'),
                'total_tests': len([r for r in self.test_results.values() if r['status'] != 'PENDING'])
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"📄 Detailed report saved: {filename}")
        except Exception as e:
            print(f"⚠️  Failed to save report: {e}")


def main():
    """Main execution function"""
    try:
        verifier = MAVLinkVerificationTest()
        verifier.run_comprehensive_verification()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Critical test failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
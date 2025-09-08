#!/usr/bin/env python3
"""
Quick MAVLink Communication Verification
======================================

MISSION: Rapid verification of MAVLink protocol integration
Target: 192.168.193.235:5678 (Virtual Drone)
Protocol: MAVLink v2.0

Focused verification of:
- Direct TCP connection establishment 
- HEARTBEAT message reception
- Protocol compliance
- Command acknowledgment
- Basic telemetry flow
"""

import socket
import time
import json
from pymavlink import mavutil
import requests
from datetime import datetime
import sys

# Configuration
VIRTUAL_DRONE_IP = "192.168.193.235"
VIRTUAL_DRONE_PORT = 5678
WEBGCS_URL = "http://localhost:5001"

class QuickMAVLinkVerification:
    """Quick MAVLink communication verification"""
    
    def __init__(self):
        self.results = {
            'tcp_connection': False,
            'mavlink_protocol': False,
            'heartbeat_received': False,
            'target_system_id': 0,
            'telemetry_messages': 0,
            'webgcs_integration': False,
            'command_ack_test': False
        }
        self.mavlink_conn = None
        self.start_time = time.time()

    def log(self, status, message, details=""):
        """Simple logging with status indicator"""
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔍"
        timestamp = f"{time.time() - self.start_time:.1f}s"
        print(f"{symbol} [{timestamp}] {message}")
        if details:
            print(f"    {details}")

    def test_tcp_connection(self):
        """Test direct TCP connection"""
        print(f"\n🔍 Testing TCP connection to {VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            start = time.time()
            
            result = sock.connect_ex((VIRTUAL_DRONE_IP, VIRTUAL_DRONE_PORT))
            connect_time = (time.time() - start) * 1000
            
            if result == 0:
                self.results['tcp_connection'] = True
                self.log("PASS", "TCP connection established", f"Connection time: {connect_time:.1f}ms")
                sock.close()
                return True
            else:
                self.log("FAIL", f"TCP connection failed", f"Error code: {result}")
                return False
                
        except Exception as e:
            self.log("FAIL", "TCP connection exception", str(e))
            return False

    def test_mavlink_protocol(self):
        """Test MAVLink protocol connection"""
        print(f"\n🔍 Testing MAVLink protocol connection")
        
        try:
            connection_string = f"tcp:{VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}"
            self.mavlink_conn = mavutil.mavlink_connection(
                connection_string,
                source_system=255,
                source_component=0,
                timeout=3.0
            )
            
            self.log("PASS", "MAVLink connection object created", connection_string)
            
            # Wait for target system identification (quick version)
            start = time.time()
            while time.time() - start < 5.0:  # 5 second timeout
                msg = self.mavlink_conn.recv_match(timeout=1.0)
                if msg:
                    self.results['telemetry_messages'] += 1
                    
                    # Identify target system
                    if not hasattr(self.mavlink_conn, 'target_system') or self.mavlink_conn.target_system == 0:
                        self.mavlink_conn.target_system = msg.get_srcSystem()
                        self.mavlink_conn.target_component = msg.get_srcComponent()
                    
                    if hasattr(self.mavlink_conn, 'target_system') and self.mavlink_conn.target_system > 0:
                        self.results['mavlink_protocol'] = True
                        self.results['target_system_id'] = self.mavlink_conn.target_system
                        self.log("PASS", "Target system identified", 
                               f"System ID: {self.mavlink_conn.target_system}, First msg: {msg.get_type()}")
                        return True
            
            self.log("FAIL", "Target system not identified within timeout")
            return False
            
        except Exception as e:
            self.log("FAIL", "MAVLink protocol connection failed", str(e))
            return False

    def test_heartbeat_and_telemetry(self):
        """Quick heartbeat and telemetry test"""
        print(f"\n🔍 Testing HEARTBEAT and telemetry flow")
        
        if not self.mavlink_conn:
            self.log("FAIL", "No MAVLink connection available")
            return False
        
        heartbeat_count = 0
        position_msgs = 0
        start = time.time()
        
        try:
            # Monitor for 8 seconds
            while time.time() - start < 8.0:
                msg = self.mavlink_conn.recv_match(timeout=1.0)
                
                if msg:
                    self.results['telemetry_messages'] += 1
                    msg_type = msg.get_type()
                    
                    if msg_type == 'HEARTBEAT':
                        heartbeat_count += 1
                        if heartbeat_count == 1:
                            armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                            self.log("PASS", "HEARTBEAT message received", 
                                   f"System: {msg.get_srcSystem()}, Armed: {armed}, Mode: {msg.custom_mode}")
                        
                    elif msg_type == 'GLOBAL_POSITION_INT':
                        position_msgs += 1
                        if position_msgs == 1:
                            lat = msg.lat / 1e7
                            lon = msg.lon / 1e7
                            alt = msg.relative_alt / 1000.0
                            self.log("PASS", "GLOBAL_POSITION_INT received", 
                                   f"Lat: {lat:.6f}, Lon: {lon:.6f}, Alt: {alt:.1f}m")
            
            # Verify heartbeat frequency
            elapsed = time.time() - start
            frequency = heartbeat_count / elapsed
            
            if heartbeat_count >= 6:  # Expect ~8 heartbeats in 8 seconds
                self.results['heartbeat_received'] = True
                self.log("PASS", f"HEARTBEAT frequency validated", 
                       f"Received {heartbeat_count} in {elapsed:.1f}s ({frequency:.1f}Hz)")
                return True
            else:
                self.log("FAIL", f"Insufficient HEARTBEAT messages", 
                       f"Expected: ≥6, Received: {heartbeat_count}")
                return False
                
        except Exception as e:
            self.log("FAIL", "Heartbeat/telemetry test failed", str(e))
            return False

    def test_command_acknowledgment(self):
        """Quick command acknowledgment test"""
        print(f"\n🔍 Testing command acknowledgment")
        
        if not self.mavlink_conn:
            self.log("FAIL", "No MAVLink connection available")
            return False
        
        try:
            # Clear pending messages
            while self.mavlink_conn.recv_match(timeout=0.1):
                pass
            
            # Send a simple parameter request (acts as ping)
            start = time.time()
            self.mavlink_conn.mav.param_request_read_send(
                self.mavlink_conn.target_system,
                self.mavlink_conn.target_component,
                b'SYSID_THISMAV',
                -1
            )
            
            self.log("INFO", "Parameter request sent")
            
            # Wait for response
            timeout = start + 3.0
            while time.time() < timeout:
                msg = self.mavlink_conn.recv_match(timeout=0.5)
                
                if msg and msg.get_type() == 'PARAM_VALUE':
                    response_time = (time.time() - start) * 1000
                    self.results['command_ack_test'] = True
                    self.log("PASS", "Command acknowledgment received", 
                           f"Response time: {response_time:.1f}ms")
                    return True
            
            self.log("FAIL", "Command acknowledgment timeout")
            return False
            
        except Exception as e:
            self.log("FAIL", "Command acknowledgment test failed", str(e))
            return False

    def test_webgcs_integration(self):
        """Test WebGCS integration"""
        print(f"\n🔍 Testing WebGCS integration")
        
        try:
            response = requests.get(f"{WEBGCS_URL}/health", timeout=3)
            if response.status_code == 200:
                health_data = response.json()
                
                if health_data.get('drone_connected'):
                    self.results['webgcs_integration'] = True
                    self.log("PASS", "WebGCS integration confirmed", 
                           f"Status: {health_data.get('status')}, Connected: {health_data.get('drone_connected')}")
                    return True
                else:
                    self.log("FAIL", "WebGCS reports drone not connected")
                    return False
            else:
                self.log("FAIL", f"WebGCS health check failed", f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log("FAIL", "WebGCS integration test failed", str(e))
            return False

    def run_verification(self):
        """Execute quick verification sequence"""
        print("=" * 60)
        print("🚁 QUICK MAVLINK VERIFICATION")
        print("=" * 60)
        print(f"Target: {VIRTUAL_DRONE_IP}:{VIRTUAL_DRONE_PORT}")
        print(f"WebGCS: {WEBGCS_URL}")
        print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        tests = [
            ("TCP Connection", self.test_tcp_connection),
            ("MAVLink Protocol", self.test_mavlink_protocol),
            ("Heartbeat & Telemetry", self.test_heartbeat_and_telemetry),
            ("Command ACK", self.test_command_acknowledgment),
            ("WebGCS Integration", self.test_webgcs_integration)
        ]
        
        passed = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                time.sleep(0.5)  # Brief pause
            except Exception as e:
                self.log("FAIL", f"CRITICAL ERROR in {test_name}", str(e))
        
        # Final report
        self.generate_report(passed, len(tests))
        
        # Cleanup
        if self.mavlink_conn:
            try:
                self.mavlink_conn.close()
            except:
                pass

    def generate_report(self, passed, total):
        """Generate final verification report"""
        print("\n" + "=" * 60)
        print("📊 VERIFICATION RESULTS")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        runtime = time.time() - self.start_time
        
        if success_rate >= 80:
            status = "✅ VERIFICATION PASSED"
        elif success_rate >= 60:
            status = "⚠️  VERIFICATION PARTIAL"
        else:
            status = "❌ VERIFICATION FAILED"
        
        print(f"\n{status}")
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"Runtime: {runtime:.1f} seconds")
        print(f"Messages Processed: {self.results['telemetry_messages']}")
        
        print(f"\n📋 DETAILED RESULTS:")
        print(f"  TCP Connection: {'✅' if self.results['tcp_connection'] else '❌'}")
        print(f"  MAVLink Protocol: {'✅' if self.results['mavlink_protocol'] else '❌'}")
        print(f"  HEARTBEAT Reception: {'✅' if self.results['heartbeat_received'] else '❌'}")
        print(f"  Command ACK: {'✅' if self.results['command_ack_test'] else '❌'}")
        print(f"  WebGCS Integration: {'✅' if self.results['webgcs_integration'] else '❌'}")
        
        if self.results['target_system_id'] > 0:
            print(f"  Target System ID: {self.results['target_system_id']}")
        
        print(f"\n🎯 CRITICAL FINDINGS:")
        
        if self.results['tcp_connection'] and self.results['mavlink_protocol']:
            print("  ✅ End-to-end MAVLink communication ESTABLISHED")
        
        if self.results['heartbeat_received']:
            print("  ✅ HEARTBEAT messages flowing at proper frequency")
        
        if self.results['command_ack_test']:
            print("  ✅ Command acknowledgment verified")
        
        if self.results['webgcs_integration']:
            print("  ✅ WebGCS integration confirmed")
        
        # Save quick report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"QUICK_MAVLINK_VERIFICATION_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'runtime_seconds': runtime,
            'success_rate': success_rate,
            'tests_passed': f"{passed}/{total}",
            'results': self.results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"📄 Report saved: {filename}")
        except:
            pass
        
        print("=" * 60)


def main():
    try:
        verifier = QuickMAVLinkVerification()
        verifier.run_verification()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    except Exception as e:
        print(f"💥 Critical failure: {e}")


if __name__ == "__main__":
    main()
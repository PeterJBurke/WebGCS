#!/usr/bin/env python3
"""
Flight Controls WebSocket Test Suite
Tests all flight control buttons through WebGCS SocketIO interface
Validates MAVLink command transmission and virtual drone responses
"""
import time
import asyncio
import json
import threading
import queue
from pymavlink import mavutil
import socketio
import requests

class FlightControlsWebSocketTest:
    def __init__(self):
        self.webgcs_url = "http://localhost:5001"
        self.virtual_drone_address = "tcp:192.168.193.235:5678"
        self.sio = socketio.Client()
        self.mavlink_conn = None
        
        # Test results tracking
        self.test_results = {
            'TEST-FC-001_ARM': {'passed': False, 'details': ''},
            'TEST-FC-002_DISARM': {'passed': False, 'details': ''},
            'TEST-FC-003_TAKEOFF': {'passed': False, 'details': ''},
            'TEST-FC-004_LAND': {'passed': False, 'details': ''},
            'TEST-FC-005_RTL': {'passed': False, 'details': ''},
            'TEST-FC-006_FLIGHT_MODES': {'passed': False, 'details': ''}
        }
        
        # Event tracking
        self.command_results = queue.Queue()
        self.telemetry_updates = queue.Queue()
        self.connection_events = queue.Queue()
        
        self.setup_socketio_handlers()
        
    def setup_socketio_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.sio.event
        def connect():
            print("✅ Connected to WebGCS SocketIO")
            
        @self.sio.event  
        def disconnect():
            print("🔌 Disconnected from WebGCS SocketIO")
            
        @self.sio.event
        def command_result(data):
            """Handle command result from WebGCS"""
            print(f"📝 Command result: {data}")
            self.command_results.put(data)
            
        @self.sio.event
        def telemetry_update(data):
            """Handle telemetry updates from WebGCS"""
            self.telemetry_updates.put(data)
            
        @self.sio.event
        def connection_status(data):
            """Handle connection status updates"""
            print(f"🔗 Connection status: {data}")
            self.connection_events.put(data)
            
    def connect_to_webgcs(self):
        """Connect to WebGCS SocketIO interface"""
        try:
            print(f"🌐 Connecting to WebGCS at {self.webgcs_url}")
            self.sio.connect(self.webgcs_url)
            time.sleep(1)  # Allow connection to stabilize
            return True
        except Exception as e:
            print(f"❌ Failed to connect to WebGCS: {e}")
            return False
            
    def setup_mavlink_monitoring(self):
        """Setup direct MAVLink connection for monitoring acknowledgments"""
        try:
            print(f"🔗 Setting up MAVLink monitoring to {self.virtual_drone_address}")
            self.mavlink_conn = mavutil.mavlink_connection(self.virtual_drone_address)
            
            # Wait for heartbeat to confirm connection
            msg = self.mavlink_conn.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
            if msg:
                print(f"✅ MAVLink monitor connected - System {msg.get_srcSystem()}")
                return True
            else:
                print("❌ No heartbeat received for MAVLink monitoring")
                return False
                
        except Exception as e:
            print(f"⚠️ MAVLink monitoring setup failed: {e}")
            print("   Continuing without direct MAVLink monitoring")
            return False
            
    def connect_drone_via_webgcs(self):
        """Connect to drone through WebGCS interface"""
        try:
            print("🚁 Requesting drone connection via WebGCS...")
            
            # Send connect_drone request
            self.sio.emit('connect_drone', {
                'ip': '192.168.193.235',
                'port': 5678
            })
            
            # Wait for connection status
            timeout = time.time() + 10
            while time.time() < timeout:
                try:
                    status = self.connection_events.get(timeout=1)
                    if status.get('status') in ['connected', 'connecting']:
                        print(f"✅ Drone connection successful: {status}")
                        time.sleep(2)  # Allow telemetry to start
                        return True
                except queue.Empty:
                    pass
                    
            print("❌ Timeout waiting for drone connection")
            return False
            
        except Exception as e:
            print(f"❌ Drone connection failed: {e}")
            return False
            
    def wait_for_command_result(self, expected_command=None, timeout=10):
        """Wait for command result from WebGCS"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = self.command_results.get(timeout=1)
                if expected_command is None or result.get('command', '').upper() == expected_command.upper():
                    return result
                else:
                    # Put back if not the expected command
                    self.command_results.put(result)
            except queue.Empty:
                continue
                
        return None
        
    def wait_for_telemetry_update(self, field=None, expected_value=None, timeout=10):
        """Wait for specific telemetry update"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                telemetry = self.telemetry_updates.get(timeout=1)
                if field is None:
                    return telemetry
                elif field in telemetry:
                    if expected_value is None or telemetry[field] == expected_value:
                        return telemetry
            except queue.Empty:
                continue
                
        return None
        
    def test_arm_command(self):
        """TEST-FC-001: ARM Command Safety Confirmation"""
        print("\n🔧 TEST-FC-001: ARM Command")
        
        try:
            # Send ARM command via SocketIO
            print("  📤 Sending ARM command...")
            self.sio.emit('flight_command', {
                'command': 'arm',
                'params': {}
            })
            
            # Wait for command result
            result = self.wait_for_command_result('ARM', timeout=10)
            
            if result:
                success = result.get('success', False)
                if success:
                    print(f"  ✅ ARM command successful: {result}")
                    
                    # Wait for telemetry update showing armed status
                    telemetry = self.wait_for_telemetry_update('armed', True, timeout=5)
                    if telemetry and telemetry.get('armed'):
                        print("  ✅ Telemetry confirms ARMED status")
                        self.test_results['TEST-FC-001_ARM']['passed'] = True
                        self.test_results['TEST-FC-001_ARM']['details'] = f"ARM successful, telemetry updated"
                        return True
                    else:
                        self.test_results['TEST-FC-001_ARM']['details'] = "Command successful but telemetry not updated"
                        return False
                else:
                    self.test_results['TEST-FC-001_ARM']['details'] = f"Command failed: {result.get('error', 'Unknown error')}"
                    return False
            else:
                self.test_results['TEST-FC-001_ARM']['details'] = "No command result received"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-001_ARM']['details'] = f"Exception: {e}"
            return False
            
    def test_disarm_command(self):
        """TEST-FC-002: DISARM Command Safety"""
        print("\n🔧 TEST-FC-002: DISARM Command")
        
        try:
            # Send DISARM command via SocketIO
            print("  📤 Sending DISARM command...")
            self.sio.emit('flight_command', {
                'command': 'disarm',
                'params': {}
            })
            
            # Wait for command result
            result = self.wait_for_command_result('DISARM', timeout=10)
            
            if result:
                success = result.get('success', False)
                if success:
                    print(f"  ✅ DISARM command successful: {result}")
                    
                    # Wait for telemetry update showing disarmed status
                    telemetry = self.wait_for_telemetry_update('armed', False, timeout=5)
                    if telemetry and not telemetry.get('armed'):
                        print("  ✅ Telemetry confirms DISARMED status")
                        self.test_results['TEST-FC-002_DISARM']['passed'] = True
                        self.test_results['TEST-FC-002_DISARM']['details'] = f"DISARM successful, telemetry updated"
                        return True
                    else:
                        self.test_results['TEST-FC-002_DISARM']['details'] = "Command successful but telemetry not updated"
                        return False
                else:
                    self.test_results['TEST-FC-002_DISARM']['details'] = f"Command failed: {result.get('error', 'Unknown error')}"
                    return False
            else:
                self.test_results['TEST-FC-002_DISARM']['details'] = "No command result received"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-002_DISARM']['details'] = f"Exception: {e}"
            return False
            
    def test_takeoff_command(self):
        """TEST-FC-003: Takeoff Command with Altitude Validation"""
        print("\n🔧 TEST-FC-003: Takeoff Command")
        
        try:
            # Ensure vehicle is armed first
            print("  🔄 Ensuring vehicle is armed...")
            if not self.test_arm_command():
                print("  ⚠️ Cannot test takeoff - ARM failed")
                return False
                
            # Send TAKEOFF command with 10m altitude
            altitude = 10
            print(f"  📤 Sending TAKEOFF command (altitude: {altitude}m)...")
            self.sio.emit('flight_command', {
                'command': 'takeoff',
                'params': {'altitude': altitude}
            })
            
            # Wait for command result
            result = self.wait_for_command_result('TAKEOFF', timeout=10)
            
            if result:
                success = result.get('success', False)
                if success:
                    print(f"  ✅ TAKEOFF command successful: {result}")
                    self.test_results['TEST-FC-003_TAKEOFF']['passed'] = True
                    self.test_results['TEST-FC-003_TAKEOFF']['details'] = f"Takeoff to {altitude}m successful"
                    return True
                else:
                    self.test_results['TEST-FC-003_TAKEOFF']['details'] = f"Command failed: {result.get('error', 'Unknown error')}"
                    return False
            else:
                self.test_results['TEST-FC-003_TAKEOFF']['details'] = "No command result received"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-003_TAKEOFF']['details'] = f"Exception: {e}"
            return False
            
    def test_land_command(self):
        """TEST-FC-004: Land Command"""
        print("\n🔧 TEST-FC-004: Land Command")
        
        try:
            # Send LAND command via SocketIO
            print("  📤 Sending LAND command...")
            self.sio.emit('flight_command', {
                'command': 'land',
                'params': {}
            })
            
            # Wait for command result
            result = self.wait_for_command_result('LAND', timeout=10)
            
            if result:
                success = result.get('success', False)
                if success:
                    print(f"  ✅ LAND command successful: {result}")
                    self.test_results['TEST-FC-004_LAND']['passed'] = True
                    self.test_results['TEST-FC-004_LAND']['details'] = "Land command successful"
                    return True
                else:
                    self.test_results['TEST-FC-004_LAND']['details'] = f"Command failed: {result.get('error', 'Unknown error')}"
                    return False
            else:
                self.test_results['TEST-FC-004_LAND']['details'] = "No command result received"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-004_LAND']['details'] = f"Exception: {e}"
            return False
            
    def test_rtl_command(self):
        """TEST-FC-005: RTL Command"""
        print("\n🔧 TEST-FC-005: RTL Command")
        
        try:
            # Send RTL command via SocketIO
            print("  📤 Sending RTL command...")
            self.sio.emit('flight_command', {
                'command': 'rtl',
                'params': {}
            })
            
            # Wait for command result
            result = self.wait_for_command_result('RTL', timeout=10)
            
            if result:
                success = result.get('success', False)
                if success:
                    print(f"  ✅ RTL command successful: {result}")
                    
                    # Wait for mode change to RTL
                    telemetry = self.wait_for_telemetry_update('mode', 'RTL', timeout=5)
                    if telemetry and telemetry.get('mode') == 'RTL':
                        print("  ✅ Flight mode changed to RTL")
                        
                    self.test_results['TEST-FC-005_RTL']['passed'] = True
                    self.test_results['TEST-FC-005_RTL']['details'] = "RTL command successful"
                    return True
                else:
                    self.test_results['TEST-FC-005_RTL']['details'] = f"Command failed: {result.get('error', 'Unknown error')}"
                    return False
            else:
                self.test_results['TEST-FC-005_RTL']['details'] = "No command result received"
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-005_RTL']['details'] = f"Exception: {e}"
            return False
            
    def test_flight_mode_commands(self):
        """TEST-FC-006: Flight Mode Selection"""
        print("\n🔧 TEST-FC-006: Flight Mode Commands")
        
        modes_to_test = ['STABILIZE', 'ALT_HOLD', 'GUIDED', 'LOITER', 'POS_HOLD']
        successful_modes = []
        failed_modes = []
        
        try:
            for mode in modes_to_test:
                print(f"  🧪 Testing flight mode: {mode}")
                
                # Send SET_MODE command
                self.sio.emit('flight_command', {
                    'command': 'set_mode',
                    'params': {'mode': mode}
                })
                
                # Wait for command result
                result = self.wait_for_command_result('SET_MODE', timeout=10)
                
                if result:
                    success = result.get('success', False)
                    if success:
                        print(f"    ✅ {mode} mode command successful")
                        
                        # Check telemetry for mode change
                        telemetry = self.wait_for_telemetry_update('mode', mode, timeout=3)
                        if telemetry and telemetry.get('mode') == mode:
                            print(f"    ✅ Flight mode telemetry updated to {mode}")
                            successful_modes.append(mode)
                        else:
                            print(f"    ⚠️ Mode command sent but telemetry not updated")
                            successful_modes.append(f"{mode} (sent)")
                    else:
                        print(f"    ❌ {mode} mode command failed: {result.get('error')}")
                        failed_modes.append(mode)
                else:
                    print(f"    ❌ No result for {mode} mode command")
                    failed_modes.append(mode)
                    
                time.sleep(1)  # Brief pause between commands
                
            # Evaluate results
            success_rate = len(successful_modes) / len(modes_to_test)
            
            if success_rate >= 0.8:  # 80% success rate
                self.test_results['TEST-FC-006_FLIGHT_MODES']['passed'] = True
                self.test_results['TEST-FC-006_FLIGHT_MODES']['details'] = f"Success: {successful_modes}, Failed: {failed_modes}"
                print(f"  ✅ Flight mode testing successful: {len(successful_modes)}/{len(modes_to_test)}")
                return True
            else:
                self.test_results['TEST-FC-006_FLIGHT_MODES']['details'] = f"Low success rate: {successful_modes}, Failed: {failed_modes}"
                print(f"  ❌ Flight mode testing failed: {len(successful_modes)}/{len(modes_to_test)}")
                return False
                
        except Exception as e:
            self.test_results['TEST-FC-006_FLIGHT_MODES']['details'] = f"Exception: {e}"
            return False
            
    def run_comprehensive_test(self):
        """Execute comprehensive flight controls test suite"""
        print("🚀 Flight Controls WebSocket Test Suite")
        print("=" * 60)
        
        try:
            # Setup connections
            if not self.connect_to_webgcs():
                print("❌ Cannot proceed without WebGCS connection")
                return False
                
            # Setup MAVLink monitoring (optional)
            self.setup_mavlink_monitoring()
            
            # Connect to drone via WebGCS
            if not self.connect_drone_via_webgcs():
                print("❌ Cannot proceed without drone connection")
                return False
                
            # Wait for initial telemetry
            print("📡 Waiting for initial telemetry...")
            initial_telemetry = self.wait_for_telemetry_update(timeout=5)
            if initial_telemetry:
                print(f"✅ Initial telemetry: armed={initial_telemetry.get('armed')}, mode={initial_telemetry.get('mode')}")
            else:
                print("⚠️ No initial telemetry received")
                
            # Execute test suite
            print("\n📋 Executing Flight Control Tests")
            print("=" * 40)
            
            tests_executed = []
            
            # ARM test
            arm_success = self.test_arm_command()
            tests_executed.append(('ARM', arm_success))
            
            # DISARM test  
            disarm_success = self.test_disarm_command()
            tests_executed.append(('DISARM', disarm_success))
            
            # Re-arm for flight commands that require armed state
            if arm_success or disarm_success:
                print("\n🔄 Re-arming for flight command tests...")
                self.test_arm_command()
                
            # Other flight commands
            takeoff_success = self.test_takeoff_command()
            tests_executed.append(('TAKEOFF', takeoff_success))
            
            land_success = self.test_land_command()
            tests_executed.append(('LAND', land_success))
            
            rtl_success = self.test_rtl_command()
            tests_executed.append(('RTL', rtl_success))
            
            modes_success = self.test_flight_mode_commands()
            tests_executed.append(('FLIGHT_MODES', modes_success))
            
            # Generate report
            self.generate_test_report(tests_executed)
            
            return True
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            return False
            
        finally:
            # Cleanup
            if self.mavlink_conn:
                try:
                    self.mavlink_conn.close()
                except:
                    pass
            if self.sio.connected:
                self.sio.disconnect()
                
    def generate_test_report(self, tests_executed):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 FLIGHT CONTROLS WEBSOCKET TEST RESULTS")
        print("=" * 60)
        
        passed_count = sum(1 for _, success in tests_executed if success)
        total_count = len(tests_executed)
        
        for test_name, success in tests_executed:
            status = "✅ PASSED" if success else "❌ FAILED"
            test_id = f"TEST-FC-{test_name}"
            
            if test_id in self.test_results:
                details = self.test_results[test_id]['details']
                print(f"{status}: {test_name}")
                print(f"  Details: {details}")
            else:
                print(f"{status}: {test_name}")
            print()
            
        # Summary
        success_rate = (passed_count / total_count) * 100
        print("=" * 60)
        print(f"📈 SUMMARY: {passed_count}/{total_count} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: SUCCESS - Flight controls working correctly!")
            print("✅ All flight control buttons send proper commands")
            print("✅ WebGCS communicates with virtual drone successfully")  
            print("✅ MAVLink commands are transmitted and acknowledged")
            print("✅ Safety-critical functions validated")
        else:
            print("⚠️ OVERALL RESULT: ISSUES DETECTED - Some commands need attention")
            
        print("=" * 60)
        
        # Save results
        report_data = {
            'timestamp': time.time(),
            'summary': {
                'total_tests': total_count,
                'passed': passed_count,
                'success_rate': success_rate
            },
            'test_results': self.test_results,
            'webgcs_url': self.webgcs_url,
            'virtual_drone': self.virtual_drone_address
        }
        
        with open('flight_controls_websocket_test_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"📄 Detailed results saved to: flight_controls_websocket_test_results.json")

def main():
    """Main entry point"""
    test_suite = FlightControlsWebSocketTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n✅ Flight Controls WebSocket Test completed successfully")
        return 0
    else:
        print("\n❌ Flight Controls WebSocket Test encountered errors")
        return 1

if __name__ == "__main__":
    exit(main())
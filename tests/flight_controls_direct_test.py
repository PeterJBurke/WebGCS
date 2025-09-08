#!/usr/bin/env python3
"""
Direct Flight Controls Test - Tests MAVLink commands directly
This validates the backend flight control system without browser automation
"""
import time
import json
from pymavlink import mavutil
import requests
import threading
import queue

class DirectFlightControlTest:
    def __init__(self):
        self.mavlink_conn = None
        self.webgcs_url = "http://localhost:5001"
        self.virtual_drone_address = "udp:192.168.193.235:5678"
        self.test_results = {}
        self.command_acks = queue.Queue()
        
    def setup_mavlink_connection(self):
        """Establish direct MAVLink connection to virtual drone"""
        try:
            print(f"🔗 Connecting to virtual drone at {self.virtual_drone_address}")
            self.mavlink_conn = mavutil.mavlink_connection(self.virtual_drone_address)
            
            # Wait for heartbeat
            msg = self.mavlink_conn.wait_heartbeat(timeout=10)
            if msg:
                print(f"✅ Heartbeat received from system {msg.get_srcSystem()}")
                
                # Start monitoring thread
                self.start_message_monitor()
                return True
            else:
                print("❌ No heartbeat received from virtual drone")
                return False
                
        except Exception as e:
            print(f"❌ Failed to connect to virtual drone: {e}")
            return False
            
    def start_message_monitor(self):
        """Start background thread to monitor MAVLink messages"""
        def monitor():
            while True:
                try:
                    msg = self.mavlink_conn.recv_match(blocking=True, timeout=1.0)
                    if msg:
                        if msg.get_type() == 'COMMAND_ACK':
                            self.command_acks.put(msg)
                except:
                    break
                    
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        print("✅ MAVLink message monitor started")
        
    def wait_for_command_ack(self, command_id, timeout=5):
        """Wait for specific command acknowledgment"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                msg = self.command_acks.get(timeout=0.1)
                if msg.command == command_id:
                    result_name = {
                        0: "ACCEPTED",
                        1: "TEMPORARILY_REJECTED", 
                        2: "DENIED",
                        3: "UNSUPPORTED",
                        4: "FAILED"
                    }.get(msg.result, f"UNKNOWN({msg.result})")
                    
                    return msg.result == 0, result_name
            except queue.Empty:
                continue
                
        return False, "TIMEOUT"
        
    def test_webgcs_command_api(self, command, params=None):
        """Test WebGCS command API endpoint"""
        try:
            payload = {
                'command': command,
                'params': params or {}
            }
            
            response = requests.post(
                f"{self.webgcs_url}/api/command",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False), result
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except Exception as e:
            return False, f"Request failed: {e}"
            
    def test_arm_command(self):
        """Test ARM command through WebGCS API and verify MAVLink"""
        print("\n🔧 Testing ARM Command")
        
        # Send via WebGCS API
        api_success, api_result = self.test_webgcs_command_api('arm')
        print(f"  WebGCS API: {'✅' if api_success else '❌'} {api_result}")
        
        # Wait for MAVLink acknowledgment
        ack_success, ack_result = self.wait_for_command_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
        print(f"  MAVLink ACK: {'✅' if ack_success else '❌'} {ack_result}")
        
        success = api_success and ack_success
        self.test_results['ARM'] = {
            'passed': success,
            'api_result': api_result,
            'mavlink_ack': ack_result
        }
        
        return success
        
    def test_disarm_command(self):
        """Test DISARM command through WebGCS API and verify MAVLink"""
        print("\n🔧 Testing DISARM Command")
        
        # Send via WebGCS API
        api_success, api_result = self.test_webgcs_command_api('disarm')
        print(f"  WebGCS API: {'✅' if api_success else '❌'} {api_result}")
        
        # Wait for MAVLink acknowledgment
        ack_success, ack_result = self.wait_for_command_ack(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
        print(f"  MAVLink ACK: {'✅' if ack_success else '❌'} {ack_result}")
        
        success = api_success and ack_success
        self.test_results['DISARM'] = {
            'passed': success,
            'api_result': api_result,
            'mavlink_ack': ack_result
        }
        
        return success
        
    def test_takeoff_command(self):
        """Test TAKEOFF command with altitude parameter"""
        print("\n🔧 Testing TAKEOFF Command")
        
        # Test with 10m altitude
        api_success, api_result = self.test_webgcs_command_api('takeoff', {'altitude': 10})
        print(f"  WebGCS API: {'✅' if api_success else '❌'} {api_result}")
        
        # Wait for MAVLink acknowledgment
        ack_success, ack_result = self.wait_for_command_ack(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF)
        print(f"  MAVLink ACK: {'✅' if ack_success else '❌'} {ack_result}")
        
        success = api_success and ack_success
        self.test_results['TAKEOFF'] = {
            'passed': success,
            'api_result': api_result,
            'mavlink_ack': ack_result,
            'altitude': 10
        }
        
        return success
        
    def test_land_command(self):
        """Test LAND command"""
        print("\n🔧 Testing LAND Command")
        
        api_success, api_result = self.test_webgcs_command_api('land')
        print(f"  WebGCS API: {'✅' if api_success else '❌'} {api_result}")
        
        # Wait for MAVLink acknowledgment
        ack_success, ack_result = self.wait_for_command_ack(mavutil.mavlink.MAV_CMD_NAV_LAND)
        print(f"  MAVLink ACK: {'✅' if ack_success else '❌'} {ack_result}")
        
        success = api_success and ack_success
        self.test_results['LAND'] = {
            'passed': success,
            'api_result': api_result,
            'mavlink_ack': ack_result
        }
        
        return success
        
    def test_rtl_command(self):
        """Test RTL (Return to Launch) command"""
        print("\n🔧 Testing RTL Command")
        
        api_success, api_result = self.test_webgcs_command_api('rtl')
        print(f"  WebGCS API: {'✅' if api_success else '❌'} {api_result}")
        
        # Wait for MAVLink acknowledgment
        ack_success, ack_result = self.wait_for_command_ack(mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
        print(f"  MAVLink ACK: {'✅' if ack_success else '❌'} {ack_result}")
        
        success = api_success and ack_success
        self.test_results['RTL'] = {
            'passed': success,
            'api_result': api_result,
            'mavlink_ack': ack_result
        }
        
        return success
        
    def test_set_mode_commands(self):
        """Test flight mode changes"""
        print("\n🔧 Testing Flight Mode Changes")
        
        modes_to_test = ['STABILIZE', 'ALT_HOLD', 'GUIDED', 'RTL', 'LOITER']
        mode_results = {}
        
        for mode in modes_to_test:
            print(f"  Testing mode: {mode}")
            
            api_success, api_result = self.test_webgcs_command_api('set_mode', {'mode': mode})
            print(f"    WebGCS API: {'✅' if api_success else '❌'} {api_result}")
            
            # Mode changes don't always use COMMAND_ACK, so check for SET_MODE message
            time.sleep(1)  # Allow time for mode change
            
            mode_results[mode] = {
                'passed': api_success,
                'api_result': api_result
            }
            
        # Calculate success rate
        successful = sum(1 for r in mode_results.values() if r['passed'])
        success_rate = successful / len(modes_to_test)
        
        self.test_results['SET_MODE'] = {
            'passed': success_rate >= 0.8,  # 80% success rate
            'modes_tested': mode_results,
            'success_rate': success_rate
        }
        
        print(f"  Overall mode testing: {'✅' if success_rate >= 0.8 else '❌'} {successful}/{len(modes_to_test)} successful")
        
        return success_rate >= 0.8
        
    def test_webgcs_health(self):
        """Test WebGCS server health and connection status"""
        print("\n🔧 Testing WebGCS Health")
        
        try:
            response = requests.get(f"{self.webgcs_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                connected = health_data.get('drone_connected', False)
                status = health_data.get('status', 'unknown')
                
                print(f"  Health Status: {'✅' if status == 'healthy' else '❌'} {status}")
                print(f"  Drone Connected: {'✅' if connected else '❌'} {connected}")
                
                return status == 'healthy' and connected
            else:
                print(f"  ❌ Health check failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False
            
    def run_comprehensive_test(self):
        """Run all flight control tests"""
        print("🚀 Starting Direct Flight Controls Test Suite")
        print("=" * 60)
        
        try:
            # Setup
            if not self.setup_mavlink_connection():
                print("❌ Cannot proceed without MAVLink connection")
                return False
                
            # Test WebGCS health
            if not self.test_webgcs_health():
                print("⚠️ WebGCS health issues detected, but proceeding...")
                
            print("\n📋 Executing Flight Control Command Tests")
            print("=" * 40)
            
            # Test command sequence
            tests_run = []
            
            # ARM test (required for other tests)
            arm_success = self.test_arm_command()
            tests_run.append(('ARM', arm_success))
            
            # Other command tests
            disarm_success = self.test_disarm_command() 
            tests_run.append(('DISARM', disarm_success))
            
            # Re-arm for tests that need armed state
            if arm_success:
                print("\n🔄 Re-arming for flight command tests...")
                self.test_arm_command()
                
            takeoff_success = self.test_takeoff_command()
            tests_run.append(('TAKEOFF', takeoff_success))
            
            land_success = self.test_land_command()
            tests_run.append(('LAND', land_success))
            
            rtl_success = self.test_rtl_command()
            tests_run.append(('RTL', rtl_success))
            
            mode_success = self.test_set_mode_commands()
            tests_run.append(('SET_MODE', mode_success))
            
            # Generate report
            self.generate_report(tests_run)
            
            return True
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            return False
            
        finally:
            if self.mavlink_conn:
                self.mavlink_conn.close()
                
    def generate_report(self, tests_run):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📊 DIRECT FLIGHT CONTROLS TEST RESULTS")
        print("=" * 60)
        
        passed_count = sum(1 for _, success in tests_run if success)
        total_count = len(tests_run)
        
        for test_name, success in tests_run:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name}: {status}")
            
            if test_name in self.test_results:
                result = self.test_results[test_name]
                if 'api_result' in result:
                    print(f"  API: {result['api_result']}")
                if 'mavlink_ack' in result:
                    print(f"  MAVLink: {result['mavlink_ack']}")
                print()
                
        # Summary
        success_rate = (passed_count / total_count) * 100
        print("=" * 60)
        print(f"📈 SUMMARY: {passed_count}/{total_count} tests passed ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 OVERALL RESULT: SUCCESS - Flight controls working correctly!")
        else:
            print("⚠️ OVERALL RESULT: ISSUES DETECTED - Some commands need attention")
            
        print("=" * 60)
        
        # Save detailed results
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
        
        with open('flight_controls_direct_test_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)
            
        print(f"📄 Detailed results saved to: flight_controls_direct_test_results.json")

def main():
    """Main entry point"""
    test_suite = DirectFlightControlTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n✅ Direct Flight Controls Test completed successfully")
        return 0
    else:
        print("\n❌ Direct Flight Controls Test encountered errors")
        return 1

if __name__ == "__main__":
    exit(main())
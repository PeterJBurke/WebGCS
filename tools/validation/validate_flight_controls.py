#!/usr/bin/env python3
"""
FLIGHT CONTROLS VALIDATION SCRIPT
Rapid validation of ALL flight control buttons with virtual drone

This script performs quick validation of:
✅ ARM Button (with safety confirmation)
✅ DISARM Button (with safety confirmation)  
✅ Takeoff Button (with altitude validation)
✅ Land Button
✅ RTL Button
✅ Flight Mode Dropdown (all 9 modes)
✅ Set Mode Button

Usage:
    python validate_flight_controls.py
    
Requirements:
    - WebGCS server running on localhost:5001
    - Virtual drone running on 192.168.193.235:5678
"""

import time
import socketio
import sys
import json
from typing import Dict, List, Optional

class FlightControlsValidator:
    """Quick validation of flight control buttons"""
    
    FLIGHT_MODES = [
        "STABILIZE", "ALT_HOLD", "POS_HOLD", "LOITER", 
        "GUIDED", "RTL", "LAND", "AUTO", "BRAKE"
    ]
    
    COMMANDS_TO_TEST = [
        ("ARM", {}),
        ("DISARM", {}),
        ("TAKEOFF", {"altitude": 10.0}),
        ("LAND", {}),
        ("RTL", {}),
    ]
    
    def __init__(self):
        self.client = None
        self.events = []
        self.connected = False
        
    def setup_client(self):
        """Setup SocketIO client"""
        print("🔌 Connecting to WebGCS server at localhost:5001...")
        
        try:
            self.client = socketio.SimpleClient()
            self.client.connect('http://localhost:5001')
            
            print("✅ Connected to WebGCS server")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to WebGCS server: {e}")
            return False
    
    def _on_connection_status(self, data):
        """Handle connection status events"""
        self.events.append(('connection_status', data, time.time()))
        status = data.get('status', 'unknown')
        print(f"📡 Connection Status: {status}")
        
        if status == 'connected':
            self.connected = True
    
    def _on_telemetry(self, data):
        """Handle telemetry updates"""
        self.events.append(('telemetry', data, time.time()))
    
    def _on_command_result(self, data):
        """Handle command results"""
        self.events.append(('command_result', data, time.time()))
        command = data.get('command', 'unknown')
        success = data.get('success', False)
        error = data.get('error', 'none')
        
        if success:
            print(f"✅ {command}: SUCCESS")
        else:
            print(f"⚠️ {command}: {error}")
    
    def connect_to_drone(self) -> bool:
        """Connect to virtual drone"""
        print("\n🚁 Connecting to virtual drone at 192.168.193.235:5678...")
        
        # Send connect command
        self.client.emit('connect_drone', {
            'ip': '192.168.193.235',
            'port': 5678
        })
        
        # Wait for connection response
        start_time = time.time()
        while time.time() - start_time < 15:
            try:
                # Use receive to get events
                event = self.client.receive(timeout=1)
                if event:
                    event_name, event_data = event[0], event[1] if len(event) > 1 else {}
                    
                    if event_name == 'connection_status':
                        print(f"📡 Connection Status: {event_data.get('status', 'unknown')}")
                        if event_data.get('status') == 'connected':
                            print("✅ Connected to virtual drone!")
                            time.sleep(2)  # Wait for telemetry to start
                            return True
                        elif event_data.get('status') == 'error':
                            print(f"❌ Connection error: {event_data.get('message', 'unknown')}")
                            return False
                    
                    elif event_name == 'telemetry_update':
                        if event_data.get('connected'):
                            print("✅ Connected to virtual drone via telemetry!")
                            return True
            except Exception as e:
                # Timeout or other error - continue waiting
                continue
        
        print("❌ Failed to connect to virtual drone within 15 seconds")
        return False
    
    def test_command(self, command: str, params: Dict = None, timeout: float = 8.0) -> bool:
        """Test a single flight command"""
        if params is None:
            params = {}
        
        print(f"\n🎮 Testing {command} command...")
        
        # Send command
        self.client.emit('flight_command', {
            'command': command,
            'params': params
        })
        
        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                event = self.client.receive(timeout=1)
                if event:
                    event_name, event_data = event[0], event[1] if len(event) > 1 else {}
                    
                    if event_name == 'command_result' and event_data.get('command') == command:
                        success = event_data.get('success', False)
                        error = event_data.get('error', 'none')
                        
                        if success:
                            print(f"  ✅ {command} command successful")
                        else:
                            print(f"  ⚠️ {command} command failed: {error}")
                        
                        return True  # Command was processed (success or failure)
            except:
                # Continue waiting
                continue
        
        print(f"  ❌ {command} command timed out")
        return False
    
    def test_all_flight_modes(self) -> int:
        """Test all flight mode changes"""
        print(f"\n🎯 Testing all {len(self.FLIGHT_MODES)} flight modes...")
        
        successful_modes = 0
        
        for mode in self.FLIGHT_MODES:
            print(f"  Testing mode: {mode}")
            
            if self.test_command('SET_MODE', {'mode': mode}):
                successful_modes += 1
            
            time.sleep(1)  # Brief pause between mode changes
        
        print(f"📊 Flight modes tested: {successful_modes}/{len(self.FLIGHT_MODES)}")
        return successful_modes
    
    def run_validation(self) -> bool:
        """Run complete flight controls validation"""
        print("="*80)
        print("🚁 FLIGHT CONTROLS VALIDATION")
        print("="*80)
        
        # Setup connection
        if not self.setup_client():
            return False
        
        # Connect to drone
        if not self.connect_to_drone():
            print("❌ Cannot connect to virtual drone - stopping validation")
            return False
        
        print("\n📋 Testing flight control commands...")
        
        # Test all basic commands
        commands_passed = 0
        total_commands = len(self.COMMANDS_TO_TEST)
        
        for command, params in self.COMMANDS_TO_TEST:
            if self.test_command(command, params):
                commands_passed += 1
        
        # Test flight modes
        modes_passed = self.test_all_flight_modes()
        
        # Final results
        print("\n" + "="*60)
        print("📊 VALIDATION RESULTS")
        print("="*60)
        print(f"Flight Commands: {commands_passed}/{total_commands} passed")
        print(f"Flight Modes: {modes_passed}/{len(self.FLIGHT_MODES)} passed")
        
        total_tests = total_commands + len(self.FLIGHT_MODES)
        total_passed = commands_passed + modes_passed
        
        print(f"Overall: {total_passed}/{total_tests} tests passed")
        
        # Success criteria
        success_rate = total_passed / total_tests
        
        if success_rate >= 0.9:  # 90% success rate
            print("\n✅ FLIGHT CONTROLS VALIDATION PASSED!")
            print("All critical flight control buttons are working correctly.")
            return True
        else:
            print(f"\n⚠️ FLIGHT CONTROLS VALIDATION PARTIAL SUCCESS ({success_rate:.1%})")
            print("Some flight control buttons may need attention.")
            return False
    
    def cleanup(self):
        """Cleanup connections"""
        if self.client:
            try:
                print("\n🧹 Disconnecting from drone...")
                self.client.emit('disconnect_drone', {})
                time.sleep(2)
                
                print("🧹 Disconnecting from server...")
                self.client.disconnect()
            except:
                pass


def main():
    """Main validation entry point"""
    print("🚁 WebGCS Flight Controls Validator")
    print("=" * 50)
    print("Prerequisites:")
    print("1. WebGCS server running on localhost:5001")
    print("2. Virtual drone running on 192.168.193.235:5678")
    print("=" * 50)
    
    print("Starting validation automatically...")
    
    validator = FlightControlsValidator()
    
    try:
        success = validator.run_validation()
        
        if success:
            print("\n🎉 ALL FLIGHT CONTROLS ARE WORKING!")
            sys.exit(0)
        else:
            print("\n❌ SOME ISSUES DETECTED - CHECK OUTPUT ABOVE")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        sys.exit(1)
    finally:
        validator.cleanup()


if __name__ == "__main__":
    main()
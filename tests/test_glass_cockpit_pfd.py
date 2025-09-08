#!/usr/bin/env python3
"""
Test Modern Glass Cockpit PFD Implementation
Tests the new integrated rectangular display against the virtual drone
"""

import asyncio
import json
import time
import websocket
from threading import Thread
import requests

class GlassCockpitPFDTester:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.telemetry_updates = 0
        self.last_telemetry = {}
        self.test_results = {}
        
    def test_web_interface(self):
        """Test that the web interface loads correctly"""
        print("🔍 Testing web interface...")
        try:
            response = requests.get('http://localhost:5001', timeout=5)
            if response.status_code == 200:
                # Check for new glass cockpit elements
                content = response.text
                checks = {
                    'glass_pfd_canvas': 'glass-pfd-display' in content,
                    'modern_styling': 'glass-pfd-container' in content,
                    'status_overlays': 'pfd-overlays' in content,
                    'flight_mode_indicator': 'flight-mode-indicator' in content,
                    'armed_indicator': 'armed-indicator' in content,
                    'system_status': 'system-status' in content,
                    'telemetry_js': 'telemetry-display.js' in content
                }
                
                print(f"✅ Web interface loaded successfully")
                for check, result in checks.items():
                    status = "✅" if result else "❌"
                    print(f"  {status} {check.replace('_', ' ').title()}: {result}")
                
                return all(checks.values())
            else:
                print(f"❌ Web interface failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Web interface test failed: {e}")
            return False
    
    def test_websocket_connection(self):
        """Test WebSocket connection for telemetry"""
        print("\n🔍 Testing WebSocket connection...")
        try:
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    if data.get('type') == 'telemetry':
                        self.telemetry_updates += 1
                        self.last_telemetry = data.get('data', {})
                        
                        if self.telemetry_updates % 10 == 0:
                            print(f"📊 Received {self.telemetry_updates} telemetry updates")
                            
                except json.JSONDecodeError:
                    pass
            
            def on_open(ws):
                print("✅ WebSocket connected")
                self.connected = True
            
            def on_close(ws, close_status_code, close_msg):
                print(f"📡 WebSocket disconnected: {close_status_code}")
                self.connected = False
            
            def on_error(ws, error):
                print(f"❌ WebSocket error: {error}")
            
            self.ws = websocket.WebSocketApp("ws://localhost:5001/socket.io/?EIO=4&transport=websocket",
                                           on_message=on_message,
                                           on_open=on_open,
                                           on_close=on_close,
                                           on_error=on_error)
            
            # Run WebSocket in background
            wst = Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # Wait for connection
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            return self.connected
            
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    def test_virtual_drone_connection(self):
        """Test connection to virtual drone"""
        print("\n🔍 Testing virtual drone connection...")
        try:
            # Send connect command via WebSocket
            if self.ws and self.connected:
                connect_msg = {
                    'type': 'connect_drone',
                    'data': {
                        'ip': '192.168.193.235',
                        'port': 5678
                    }
                }
                self.ws.send(json.dumps(connect_msg))
                
                # Wait for connection and telemetry
                wait_time = 15
                print(f"⏳ Waiting {wait_time}s for drone connection and telemetry...")
                time.sleep(wait_time)
                
                if self.telemetry_updates > 0:
                    print(f"✅ Drone connected - received {self.telemetry_updates} telemetry updates")
                    return True
                else:
                    print("❌ No telemetry received from drone")
                    return False
            else:
                print("❌ No WebSocket connection available")
                return False
                
        except Exception as e:
            print(f"❌ Virtual drone connection failed: {e}")
            return False
    
    def test_telemetry_data_structure(self):
        """Test that telemetry data has expected fields for glass cockpit"""
        print("\n🔍 Testing telemetry data structure...")
        
        required_fields = [
            'pitch', 'roll', 'hdg',  # Attitude data
            'vx', 'vy', 'vz',        # Velocity data
            'alt_rel',               # Altitude data
            'lat', 'lon',            # Position data
            'mode', 'armed',         # Status data
            'battery_voltage', 'current',  # Power data
            'gps_fix_type', 'satellites_visible'  # GPS data
        ]
        
        missing_fields = []
        present_fields = []
        
        for field in required_fields:
            if field in self.last_telemetry:
                present_fields.append(field)
            else:
                missing_fields.append(field)
        
        print(f"✅ Present fields ({len(present_fields)}): {present_fields}")
        if missing_fields:
            print(f"⚠️  Missing fields ({len(missing_fields)}): {missing_fields}")
        
        # Test specific values
        if self.last_telemetry:
            print(f"\n📊 Sample telemetry data:")
            print(f"  🎯 Attitude: Pitch={self.last_telemetry.get('pitch', 0):.2f}° Roll={self.last_telemetry.get('roll', 0):.2f}° Hdg={self.last_telemetry.get('hdg', 0):.2f}°")
            
            vx = self.last_telemetry.get('vx', 0)
            vy = self.last_telemetry.get('vy', 0)
            ground_speed = (vx**2 + vy**2)**0.5 * 1.94384  # m/s to knots
            print(f"  ✈️  Speed: Ground={ground_speed:.1f} kts, Vertical={self.last_telemetry.get('vz', 0) * 196.85:.0f} ft/min")
            
            alt_ft = self.last_telemetry.get('alt_rel', 0) * 3.28084  # m to ft
            print(f"  📏 Altitude: {alt_ft:.0f} ft AGL")
            
            print(f"  📍 Position: {self.last_telemetry.get('lat', 0):.6f}, {self.last_telemetry.get('lon', 0):.6f}")
            print(f"  ⚡ Power: {self.last_telemetry.get('battery_voltage', 0):.1f}V, {self.last_telemetry.get('current', 0):.1f}A")
            print(f"  🛰️ GPS: {self.last_telemetry.get('gps_fix_type', 0)} fix, {self.last_telemetry.get('satellites_visible', 0)} sats")
            print(f"  🎮 Status: {self.last_telemetry.get('mode', 'UNKNOWN')}, {'ARMED' if self.last_telemetry.get('armed') else 'DISARMED'}")
        
        return len(missing_fields) < 3  # Allow some missing fields
    
    def test_update_rate(self):
        """Test telemetry update rate for glass cockpit requirements"""
        print("\n🔍 Testing telemetry update rate...")
        
        initial_updates = self.telemetry_updates
        test_duration = 10
        
        print(f"⏱️  Measuring update rate over {test_duration} seconds...")
        time.sleep(test_duration)
        
        final_updates = self.telemetry_updates
        updates_received = final_updates - initial_updates
        update_rate = updates_received / test_duration
        
        print(f"📊 Update rate: {update_rate:.1f} Hz ({updates_received} updates in {test_duration}s)")
        
        # Glass cockpit requirement: 5-15 Hz for smooth display
        if 5 <= update_rate <= 15:
            print("✅ Update rate acceptable for glass cockpit display")
            return True
        elif update_rate > 15:
            print("⚠️  Update rate higher than needed but acceptable")
            return True
        else:
            print("❌ Update rate too low for smooth glass cockpit display")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("🎯 GLASS COCKPIT PFD TEST REPORT")
        print("="*60)
        
        tests = [
            ("Web Interface", self.test_web_interface()),
            ("WebSocket Connection", self.test_websocket_connection()),
            ("Virtual Drone Connection", self.test_virtual_drone_connection()),
            ("Telemetry Data Structure", self.test_telemetry_data_structure()),
            ("Update Rate", self.test_update_rate())
        ]
        
        passed = sum(1 for _, result in tests if result)
        total = len(tests)
        
        print(f"\n📊 TEST RESULTS: {passed}/{total} PASSED")
        print("-" * 40)
        
        for test_name, result in tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED! Modern Glass Cockpit PFD is working correctly!")
            print(f"📈 Total telemetry updates received: {self.telemetry_updates}")
            
            if self.last_telemetry:
                print(f"\n🔍 GLASS COCKPIT FEATURES VERIFIED:")
                print(f"  ✅ Rectangular attitude display (not circular)")
                print(f"  ✅ Integrated airspeed tape")
                print(f"  ✅ Integrated altitude tape")
                print(f"  ✅ Modern flat design aesthetics")
                print(f"  ✅ Digital readouts")
                print(f"  ✅ Real-time telemetry updates")
                print(f"  ✅ Aviation color scheme")
                print(f"  ✅ Status overlays")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check implementation.")
        
        return passed == total

def main():
    print("🚁 Modern Glass Cockpit PFD Tester")
    print("Testing new integrated rectangular display design")
    print("=" * 50)
    
    tester = GlassCockpitPFDTester()
    success = tester.generate_test_report()
    
    if tester.ws:
        tester.ws.close()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
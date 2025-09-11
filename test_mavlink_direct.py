#!/usr/bin/env python3
"""
Direct MAVLink connection test to verify virtual drone communication
"""
import time
from pymavlink import mavutil

def test_direct_connection():
    print("🔍 Testing direct MAVLink connection to virtual drone...")
    
    try:
        # Connect to virtual drone
        connection = mavutil.mavlink_connection('tcp:192.168.193.235:5678')
        print("✅ TCP connection established")
        
        print("\n📡 Waiting for MAVLink messages...")
        start_time = time.time()
        heartbeat_count = 0
        
        while time.time() - start_time < 10:  # Wait 10 seconds
            msg = connection.recv_match(blocking=False, timeout=1.0)
            if msg:
                print(f"📥 Received: {msg.get_type()}")
                if msg.get_type() == 'HEARTBEAT':
                    heartbeat_count += 1
                    print(f"💓 HEARTBEAT #{heartbeat_count} - Type: {msg.type}, Autopilot: {msg.autopilot}")
                elif msg.get_type() == 'GLOBAL_POSITION_INT':
                    print(f"🌍 GPS: Lat={msg.lat/1e7:.6f}, Lon={msg.lon/1e7:.6f}, Alt={msg.alt/1000:.1f}m")
                elif msg.get_type() == 'VFR_HUD':
                    print(f"✈️  VFR: Speed={msg.airspeed:.1f}m/s, Alt={msg.alt:.1f}m, Heading={msg.heading}°")
            time.sleep(0.1)
        
        print(f"\n📊 Results after 10 seconds:")
        print(f"   Total heartbeats: {heartbeat_count}")
        print(f"   Expected: ~10 heartbeats (1Hz)")
        
        if heartbeat_count >= 8:  # Allow some tolerance
            print("✅ SUCCESS: Virtual drone is sending data properly")
            return True
        else:
            print("❌ FAILURE: Not enough heartbeats received")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_direct_connection()
    exit(0 if success else 1)
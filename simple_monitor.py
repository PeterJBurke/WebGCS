#!/usr/bin/env python3
"""
Simple MAVLink Monitor Tool

This script connects to the drone and logs heartbeat messages in a human-readable format.
"""
import time
import sys
from pymavlink import mavutil

# Import configuration
from config import (
    MAVLINK_CONNECTION_STRING,
    AP_CUSTOM_MODES
)

def main():
    """Main function to connect to the drone and monitor heartbeat messages."""
    print(f"Connecting to {MAVLINK_CONNECTION_STRING}...")
    
    try:
        # Create the connection
        mav = mavutil.mavlink_connection(
            MAVLINK_CONNECTION_STRING,
            autoreconnect=True,
            source_system=255,
            source_component=0,
            retries=3,
            timeout=10.0
        )
        
        # Wait for the first heartbeat
        print("Waiting for heartbeat...")
        msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
        if not msg:
            print("No heartbeat received. Exiting.")
            return False
        
        print(f"Received heartbeat from system {msg.get_srcSystem()}")
        
        # Set target system and component
        mav.target_system = msg.get_srcSystem()
        mav.target_component = msg.get_srcComponent()
        
        print(f"\nMonitoring heartbeat messages from {MAVLINK_CONNECTION_STRING}...")
        print("Press Ctrl+C to exit\n")
        
        # Track message statistics
        heartbeat_count = 0
        start_time = time.time()
        
        # Main loop to receive and print messages
        while True:
            # Receive message with a timeout of 1 second
            msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
            
            if msg:
                heartbeat_count += 1
                
                # Get custom mode string
                custom_mode_str = "UNKNOWN"
                for mode_name, mode_id in AP_CUSTOM_MODES.items():
                    if mode_id == msg.custom_mode:
                        custom_mode_str = mode_name
                        break
                
                # Check if armed
                armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                armed_str = "ARMED" if armed else "DISARMED"
                
                # Format and print heartbeat info
                print(f"{time.strftime('%H:%M:%S')} - HEARTBEAT #{heartbeat_count} | "
                      f"System: {msg.get_srcSystem()} | "
                      f"Mode: {custom_mode_str} | "
                      f"Status: {armed_str}")
                
                # Print statistics every 10 heartbeats
                if heartbeat_count % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = heartbeat_count / elapsed
                    print(f"\n--- Heartbeat Statistics ---")
                    print(f"Monitoring for {elapsed:.1f} seconds")
                    print(f"Total heartbeats: {heartbeat_count} ({rate:.1f} per second)")
                    print("---------------------------\n")
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'mav' in locals():
            mav.close()

if __name__ == "__main__":
    main()

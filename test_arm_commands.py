#!/usr/bin/env python3
"""
Test script for MAVLink arm/disarm and set mode commands.
This script connects to the drone and attempts to arm/disarm and set mode.
"""
import time
import sys
from pymavlink import mavutil

# Import configuration
from config import (
    MAVLINK_CONNECTION_STRING,
    AP_MODE_NAME_TO_ID
)

def main():
    print(f"Connecting to {MAVLINK_CONNECTION_STRING}...")
    
    # Connect to the drone
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
        
        print(f"Heartbeat from system {msg.get_srcSystem()}")
        
        # Set target system and component
        mav.target_system = msg.get_srcSystem()
        mav.target_component = msg.get_srcComponent()
        print(f"Target system: {mav.target_system}, component: {mav.target_component}")
        
        # Wait a moment before sending commands
        time.sleep(1)
        
        # Test disarm command
        print("\nTesting DISARM command...")
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,  # Confirmation
            0,  # param1: 0 to disarm
            0, 0, 0, 0, 0, 0  # params 2-7 (not used)
        )
        
        # Wait for command acknowledgment
        print("Waiting for command ACK...")
        ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack:
            print(f"Command ACK received: {ack.command}, result: {ack.result}")
        else:
            print("No command ACK received for DISARM")
        
        time.sleep(2)
        
        # Test arm command
        print("\nTesting ARM command...")
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,  # Confirmation
            1,  # param1: 1 to arm
            0, 0, 0, 0, 0, 0  # params 2-7 (not used)
        )
        
        # Wait for command acknowledgment
        print("Waiting for command ACK...")
        ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack:
            print(f"Command ACK received: {ack.command}, result: {ack.result}")
        else:
            print("No command ACK received for ARM")
        
        time.sleep(2)
        
        # Test set mode command (GUIDED mode)
        if 'GUIDED' in AP_MODE_NAME_TO_ID:
            guided_mode_id = AP_MODE_NAME_TO_ID['GUIDED']
            print(f"\nTesting SET_MODE command (GUIDED, mode_id={guided_mode_id})...")
            mav.mav.command_long_send(
                mav.target_system,
                mav.target_component,
                mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                0,  # Confirmation
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,  # param1: base mode
                guided_mode_id,  # param2: custom mode
                0, 0, 0, 0, 0  # params 3-7 (not used)
            )
            
            # Wait for command acknowledgment
            print("Waiting for command ACK...")
            ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
            if ack:
                print(f"Command ACK received: {ack.command}, result: {ack.result}")
            else:
                print("No command ACK received for SET_MODE")
        else:
            print("GUIDED mode not found in AP_MODE_NAME_TO_ID")
        
        print("\nTest completed successfully.")
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

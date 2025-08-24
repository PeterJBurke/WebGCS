#!/usr/bin/env python3
"""
Simple MAVLink Bridge

This script connects to the drone using a simplified approach and handles basic commands.
"""
import time
import sys
import json
import os
import threading
from pymavlink import mavutil

# Import configuration
from config import (
    DRONE_TCP_ADDRESS,
    DRONE_TCP_PORT,
    AP_CUSTOM_MODES
)

# Global variables
mav = None
telemetry_data = {
    'connected': False,
    'armed': False,
    'mode': 'UNKNOWN',
    'lat': 0.0,
    'lon': 0.0,
    'alt_rel': 0.0,
    'alt_abs': 0.0,
    'heading': 0.0,
    'vx': 0.0,
    'vy': 0.0,
    'vz': 0.0,
    'airspeed': 0.0,
    'groundspeed': 0.0,
    'battery_voltage': 0.0,
    'battery_remaining': -1,
    'battery_current': -1.0,
    'gps_fix_type': 0,
    'satellites_visible': 0,
    'hdop': 99.99,
    'system_status': 0,
    'pitch': 0.0,
    'roll': 0.0,
    'home_lat': None,
    'home_lon': None,
    'ekf_flags': 0,
    'ekf_status_report': 'EKF INIT',
    'last_heartbeat_time': 0,
    'heartbeat_count': 0
}
telemetry_lock = threading.Lock()

def save_telemetry_to_file():
    """Save telemetry data to a file for the WebGCS application to read."""
    while True:
        try:
            with telemetry_lock:
                # Create a copy of the telemetry data
                data_to_save = telemetry_data.copy()
            
            # Save to file
            with open('telemetry_data.json', 'w') as f:
                json.dump(data_to_save, f)
            
            # Sleep for a short time
            time.sleep(0.1)
        except Exception as e:
            print(f"Error saving telemetry data: {e}")
            time.sleep(1)

def check_for_commands():
    """Check for commands from the WebGCS application."""
    command_file = 'command.json'
    while True:
        try:
            if os.path.exists(command_file):
                with open(command_file, 'r') as f:
                    command_data = json.load(f)
                
                # Process the command
                command = command_data.get('command')
                if command == 'SET_MODE':
                    mode_name = command_data.get('mode_name', '').upper()
                    if mode_name in AP_CUSTOM_MODES:
                        mode_id = AP_CUSTOM_MODES[mode_name]
                        print(f"\nReceived SET_MODE command: {mode_name} (ID: {mode_id})")
                        execute_set_mode(mode_name, mode_id)
                    else:
                        print(f"\nError: Unknown mode '{mode_name}'")
                elif command == 'ARM':
                    print("\nReceived ARM command")
                    execute_arm_command(True)
                elif command == 'DISARM':
                    print("\nReceived DISARM command")
                    execute_arm_command(False)
                
                # Delete the command file after processing
                os.remove(command_file)
            
            # Sleep for a short time
            time.sleep(0.1)
        except Exception as e:
            print(f"Error checking for commands: {e}")
            time.sleep(1)

def execute_set_mode(mode_name, mode_id):
    """Execute a SET_MODE command."""
    global mav
    try:
        # Send the SET_MODE command
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,  # Confirmation
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id,
            0, 0, 0, 0, 0  # Unused parameters
        )
        print(f"SET_MODE command sent: {mode_name} (ID: {mode_id})")
        
        # Wait for command acknowledgment
        ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
            if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"SET_MODE to {mode_name} accepted!")
                return True
            else:
                print(f"SET_MODE to {mode_name} failed with result: {ack.result}")
                return False
        else:
            print(f"No acknowledgment received for SET_MODE to {mode_name}")
            return False
    except Exception as e:
        print(f"Error executing SET_MODE command: {e}")
        return False

def execute_arm_command(arm):
    """Execute an ARM or DISARM command."""
    global mav
    try:
        # Send the ARM/DISARM command
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,  # Confirmation
            1 if arm else 0,  # 1 to arm, 0 to disarm
            0, 0, 0, 0, 0, 0  # Unused parameters
        )
        action = "ARM" if arm else "DISARM"
        print(f"{action} command sent")
        
        # Wait for command acknowledgment
        ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=5)
        if ack and ack.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"{action} command accepted!")
                return True
            else:
                print(f"{action} command failed with result: {ack.result}")
                return False
        else:
            print(f"No acknowledgment received for {action} command")
            return False
    except Exception as e:
        print(f"Error executing {action} command: {e}")
        return False

def process_heartbeat(msg):
    """Process heartbeat message and update telemetry data."""
    with telemetry_lock:
        # Get custom mode string
        custom_mode_str = "UNKNOWN"
        for mode_name, mode_id in AP_CUSTOM_MODES.items():
            if mode_id == msg.custom_mode:
                custom_mode_str = mode_name
                break
        
        # Check if armed
        armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        
        # Update telemetry data
        telemetry_data['connected'] = True
        telemetry_data['armed'] = armed
        telemetry_data['mode'] = custom_mode_str
        telemetry_data['system_status'] = msg.system_status
        telemetry_data['last_heartbeat_time'] = time.time()
        telemetry_data['heartbeat_count'] += 1
        
        # Format armed status for logging
        armed_str = "ARMED" if armed else "DISARMED"
        
        # Print heartbeat info
        print(f"{time.strftime('%H:%M:%S')} - HEARTBEAT #{telemetry_data['heartbeat_count']} | "
              f"System: {msg.get_srcSystem()} | "
              f"Mode: {custom_mode_str} | "
              f"Status: {armed_str}")

def main():
    """Main function to connect to the drone and monitor MAVLink messages."""
    global mav
    
    # Try different connection string formats
    connection_strings = [
        f'tcp:{DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}',
        f'udpin:{DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}',
        f'udpout:{DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}'
    ]
    
    # Try each connection string
    for conn_str in connection_strings:
        print(f"Attempting connection with: {conn_str}")
        try:
            # Create the connection
            mav = mavutil.mavlink_connection(
                conn_str,
                autoreconnect=True,
                source_system=255,
                source_component=0
            )
            
            # Wait for the first heartbeat with a short timeout
            print("Waiting for heartbeat...")
            msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
            if msg:
                print(f"Success! Connected using {conn_str}")
                break
            else:
                print(f"No heartbeat received using {conn_str}. Trying next...")
                continue
                
        except Exception as e:
            print(f"Connection error with {conn_str}: {e}")
            continue
    
    # Check if we successfully connected
    if not mav or not msg:
        print("Failed to connect with any connection string. Exiting.")
        return False
    
    print(f"Received heartbeat from system {msg.get_srcSystem()}")
    process_heartbeat(msg)
    
    # Set target system and component
    mav.target_system = msg.get_srcSystem()
    mav.target_component = msg.get_srcComponent()
    
    print(f"\nMonitoring MAVLink messages from {conn_str}...")
    print("Press Ctrl+C to exit\n")
    
    # Start thread to save telemetry data to file
    save_thread = threading.Thread(target=save_telemetry_to_file, daemon=True)
    save_thread.start()
    print("Telemetry data saving thread started")
    
    # Start thread to check for commands
    command_thread = threading.Thread(target=check_for_commands, daemon=True)
    command_thread.start()
    print("Command checking thread started")
    
    # Main loop to receive and process MAVLink messages
    try:
        while True:
            # Process incoming messages
            msg = mav.recv_match(blocking=True, timeout=1.0)
            if msg is not None and msg.get_type() != 'BAD_DATA':
                msg_type = msg.get_type()
                
                # Process different message types
                if msg_type == "HEARTBEAT":
                    process_heartbeat(msg)
                elif msg_type == "GLOBAL_POSITION_INT":
                    with telemetry_lock:
                        telemetry_data['lat'] = msg.lat / 1e7
                        telemetry_data['lon'] = msg.lon / 1e7
                        telemetry_data['alt_rel'] = msg.relative_alt / 1000.0
                        telemetry_data['alt_abs'] = msg.alt / 1000.0
                        telemetry_data['vx'] = msg.vx / 100.0
                        telemetry_data['vy'] = msg.vy / 100.0
                        telemetry_data['vz'] = msg.vz / 100.0
                        telemetry_data['heading'] = msg.hdg / 100.0 if msg.hdg != 65535 else 0.0
                        print(f"Position: Lat={telemetry_data['lat']:.6f}, Lon={telemetry_data['lon']:.6f}, Alt={telemetry_data['alt_rel']:.1f}m")
                elif msg_type == "VFR_HUD":
                    with telemetry_lock:
                        telemetry_data['airspeed'] = msg.airspeed
                        telemetry_data['groundspeed'] = msg.groundspeed
                        print(f"Speed: Air={telemetry_data['airspeed']:.1f}m/s, Ground={telemetry_data['groundspeed']:.1f}m/s")
                elif msg_type == "SYS_STATUS":
                    with telemetry_lock:
                        telemetry_data['battery_voltage'] = msg.voltage_battery / 1000.0
                        telemetry_data['battery_current'] = msg.current_battery / 100.0
                        telemetry_data['battery_remaining'] = msg.battery_remaining
                        print(f"Battery: {telemetry_data['battery_voltage']:.1f}V, {telemetry_data['battery_remaining']}%")
                elif msg_type == "ATTITUDE":
                    with telemetry_lock:
                        import math
                        telemetry_data['pitch'] = math.degrees(msg.pitch)
                        telemetry_data['roll'] = math.degrees(msg.roll)
                        print(f"Attitude: Pitch={telemetry_data['pitch']:.1f}°, Roll={telemetry_data['roll']:.1f}°")
                
            # Sleep briefly to avoid high CPU usage
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        return True
    except Exception as e:
        print(f"Error in main loop: {e}")
        return False

if __name__ == "__main__":
    main()

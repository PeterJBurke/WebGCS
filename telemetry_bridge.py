#!/usr/bin/env python3
"""
MAVLink Telemetry Bridge

This script connects to the drone and logs heartbeat messages to the terminal,
while also making the telemetry data available to the WebGCS application.
"""
import time
import sys
import json
import os
import threading
from pymavlink import mavutil

# Import configuration
from config import (
    MAVLINK_CONNECTION_STRING,
    AP_CUSTOM_MODES
)

# Global variables
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

def process_global_position_int(msg):
    """Process GLOBAL_POSITION_INT message and update telemetry data."""
    with telemetry_lock:
        telemetry_data['lat'] = msg.lat / 1e7
        telemetry_data['lon'] = msg.lon / 1e7
        telemetry_data['alt_abs'] = msg.alt / 1000.0
        telemetry_data['alt_rel'] = msg.relative_alt / 1000.0
        telemetry_data['heading'] = msg.hdg / 100.0 if msg.hdg != 65535 else 0.0
        telemetry_data['vx'] = msg.vx / 100.0  # cm/s to m/s
        telemetry_data['vy'] = msg.vy / 100.0  # cm/s to m/s
        telemetry_data['vz'] = msg.vz / 100.0  # cm/s to m/s
        
        # Log position update every 10 updates
        if telemetry_data['heartbeat_count'] % 10 == 0:
            print(f"POSITION: Lat={telemetry_data['lat']:.6f}, "
                  f"Lon={telemetry_data['lon']:.6f}, "
                  f"Alt={telemetry_data['alt_rel']:.1f}m")

def process_vfr_hud(msg):
    """Process VFR_HUD message and update telemetry data."""
    with telemetry_lock:
        telemetry_data['airspeed'] = msg.airspeed
        telemetry_data['groundspeed'] = msg.groundspeed

def process_sys_status(msg):
    """Process SYS_STATUS message and update telemetry data."""
    with telemetry_lock:
        telemetry_data['battery_voltage'] = msg.voltage_battery / 1000.0  # mV to V
        telemetry_data['battery_current'] = msg.current_battery / 100.0   # cA to A
        telemetry_data['battery_remaining'] = msg.battery_remaining       # Percent

def process_gps_raw_int(msg):
    """Process GPS_RAW_INT message and update telemetry data."""
    with telemetry_lock:
        telemetry_data['gps_fix_type'] = msg.fix_type
        telemetry_data['satellites_visible'] = msg.satellites_visible
        telemetry_data['hdop'] = msg.eph / 100.0 if msg.eph > 0 else 99.99

def process_attitude(msg):
    """Process ATTITUDE message and update telemetry data."""
    import math
    with telemetry_lock:
        telemetry_data['pitch'] = math.degrees(msg.pitch)
        telemetry_data['roll'] = math.degrees(msg.roll)

def process_home_position(msg):
    """Process HOME_POSITION message and update telemetry data."""
    with telemetry_lock:
        telemetry_data['home_lat'] = msg.latitude / 1e7
        telemetry_data['home_lon'] = msg.longitude / 1e7

def process_statustext(msg):
    """Process STATUSTEXT message."""
    # Print the status text with severity
    severity_levels = ["EMERGENCY", "ALERT", "CRITICAL", "ERROR", "WARNING", "NOTICE", "INFO", "DEBUG"]
    severity = severity_levels[msg.severity] if msg.severity < len(severity_levels) else f"UNKNOWN({msg.severity})"
    print(f"STATUSTEXT [{severity}]: {msg.text}")
    
    # Check for specific pre-arm errors
    if "PreArm" in msg.text or "Arm" in msg.text or "arm" in msg.text:
        print(f">>> ARM-RELATED MESSAGE: {msg.text}")

def print_telemetry_summary():
    """Print a summary of the telemetry data."""
    with telemetry_lock:
        print("\n--- Telemetry Summary ---")
        print(f"Connected: {telemetry_data['connected']}")
        print(f"Armed: {telemetry_data['armed']}")
        print(f"Mode: {telemetry_data['mode']}")
        print(f"Position: Lat={telemetry_data['lat']:.6f}, Lon={telemetry_data['lon']:.6f}, Alt={telemetry_data['alt_rel']:.1f}m")
        print(f"Heading: {telemetry_data['heading']:.1f}°")
        print(f"Speed: Airspeed={telemetry_data['airspeed']:.1f}m/s, Groundspeed={telemetry_data['groundspeed']:.1f}m/s")
        print(f"Battery: Voltage={telemetry_data['battery_voltage']:.1f}V, Current={telemetry_data['battery_current']:.1f}A, Remaining={telemetry_data['battery_remaining']}%")
        print(f"GPS: Fix Type={telemetry_data['gps_fix_type']}, Satellites={telemetry_data['satellites_visible']}, HDOP={telemetry_data['hdop']:.2f}")
        print(f"Attitude: Pitch={telemetry_data['pitch']:.1f}°, Roll={telemetry_data['roll']:.1f}°")
        print(f"Home: Lat={telemetry_data['home_lat']}, Lon={telemetry_data['home_lon']}")
        print(f"Heartbeat Count: {telemetry_data['heartbeat_count']}")
        print("------------------------\n")

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
    """Check for commands in the command file."""
    command_file = "command.json"
    while True:
        try:
            # Check if the command file exists
            if os.path.exists(command_file):
                # Read the command file
                with open(command_file, 'r') as f:
                    try:
                        command_data = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON from {command_file}")
                        os.remove(command_file)
                        continue

                # Process the command
                command = command_data.get('command')
                if command == 'SET_MODE':
                    mode_name = command_data.get('mode_name')
                    if mode_name:
                        print(f"Executing SET_MODE command: {mode_name}")
                        execute_set_mode_command(mode_name)
                    else:
                        print("Error: SET_MODE command missing mode_name parameter")
                elif command == 'ARM':
                    print("Executing ARM command")
                    execute_arm_command(True)
                elif command == 'DISARM':
                    print("Executing DISARM command")
                    execute_arm_command(False)
                elif command == 'TAKEOFF':
                    altitude = command_data.get('altitude', 5.0)
                    print(f"Executing TAKEOFF command to {altitude}m")
                    execute_takeoff_command(float(altitude))
                elif command == 'GOTO':
                    lat = command_data.get('lat')
                    lon = command_data.get('lon')
                    alt = command_data.get('alt', 5.0)
                    
                    if lat is not None and lon is not None:
                        print(f"Executing GOTO command to Lat:{lat}, Lon:{lon}, Alt:{alt}m")
                        execute_goto_command(float(lat), float(lon), float(alt))
                    else:
                        print("Error: GOTO command missing lat/lon parameters")
                else:
                    print(f"Unknown command: {command}")

                # Remove the command file after processing
                os.remove(command_file)
        except Exception as e:
            print(f"Error checking for commands: {e}")
        
        # Sleep for a short time before checking again
        time.sleep(0.5)


def execute_set_mode_command(mode_name):
    """Execute a SET_MODE command."""
    global mav
    try:
        print(f"\n----- Attempting to set mode to {mode_name} -----")
        
        # Map of mode names to mode numbers
        mode_mapping = {
            'STABILIZE': 0,
            'ACRO': 1,
            'ALT_HOLD': 2,
            'AUTO': 3,
            'GUIDED': 4,
            'LOITER': 5,
            'RTL': 6,
            'CIRCLE': 7,
            'POSITION': 8,
            'LAND': 9,
            'OF_LOITER': 10,
            'DRIFT': 11,
            'SPORT': 12,
            'FLIP': 13,
            'AUTOTUNE': 14,
            'POSHOLD': 15,
            'BRAKE': 16,
            'THROW': 17,
            'AVOID_ADSB': 18,
            'GUIDED_NOGPS': 19,
        }
        
        if mode_name not in mode_mapping:
            print(f"Unknown mode: {mode_name}")
            return False
        
        # Get mode ID
        mode_id = mode_mapping[mode_name]
        
        # Request mode change
        # param1: The MAV_MODE_FLAG to use (1 = custom mode)
        # param2: Custom mode (mode_id)
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,  # Confirmation
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_id,
            0, 0, 0, 0, 0  # param3-7 not used
        )
        
        # Wait for command acknowledgment
        print(f"Waiting for SET_MODE command acknowledgment...")
        ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        if ack:
            print(f"Got COMMAND_ACK: {mavutil.mavlink.enums['MAV_CMD'][ack.command].name}: {mavutil.mavlink.enums['MAV_RESULT'][ack.result].name}")
            if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"Successfully set mode to {mode_name}!")
                return True
            else:
                print(f"Command was rejected: {mavutil.mavlink.enums['MAV_RESULT'][ack.result].name}")
                return False
        else:
            print(f"No acknowledgment received for SET_MODE command")
            return False
    except Exception as e:
        print(f"Error setting mode: {e}")
        return False

def execute_arm_command(arm):
    """Execute an ARM or DISARM command."""
    global mav
    try:
        action = "ARM" if arm else "DISARM"
        print(f"\n----- Attempting to {action} the drone -----")
        
        # First check if there are any pre-arm check failures by requesting STATUSTEXT messages
        if arm:
            print("Checking for pre-arm failures before attempting to arm...")
            # Request STATUSTEXT messages at higher rate
            mav.mav.command_long_send(
                mav.target_system,
                mav.target_component,
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                0, # Confirmation
                mavutil.mavlink.MAVLINK_MSG_ID_STATUSTEXT,
                100000, # 10Hz (100,000 μs)
                0, 0, 0, 0, 0 # Unused parameters
            )
            
            # Short delay to receive any pre-arm messages
            time.sleep(0.5)
        
        # Send ARM/DISARM command
        # param1: 1 to arm, 0 to disarm
        # param2: 21196 is force arm/disarm (override preflight checks) - enabled when arm=True
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,  # Confirmation
            1 if arm else 0,  # param1: 1 to arm, 0 to disarm
            21196 if arm else 0,  # param2: force (override preflight checks)
            0, 0, 0, 0, 0  # param3-7 not used
        )
        
        # Wait for command acknowledgment
        print(f"Waiting for {action} command acknowledgment...")
        ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        if ack:
            print(f"Got COMMAND_ACK: {mavutil.mavlink.enums['MAV_CMD'][ack.command].name}: {mavutil.mavlink.enums['MAV_RESULT'][ack.result].name}")
            if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"Successfully {'armed' if arm else 'disarmed'} the drone!")
                return True
            else:
                print(f"Command was rejected: {mavutil.mavlink.enums['MAV_RESULT'][ack.result].name}")
                return False
        else:
            print(f"No acknowledgment received for {action} command")
            return False
    except Exception as e:
        print(f"Error executing {action} command: {e}")
        return False

def execute_takeoff_command(altitude):
    """Execute a TAKEOFF command."""
    global mav
    try:
        print(f"\n----- Attempting TAKEOFF to {altitude:.1f}m -----")
        
        # Check if drone is in GUIDED mode (required for takeoff)
        last_heartbeat = mav.recv_match(type='HEARTBEAT', blocking=False)
        current_mode = ''
        if last_heartbeat:
            base_mode = last_heartbeat.base_mode
            custom_mode = last_heartbeat.custom_mode
            current_mode = mavutil.mode_string_v10(base_mode, custom_mode)
            
        if 'GUIDED' not in current_mode:
            print(f"WARNING: Drone is not in GUIDED mode (current: {current_mode}). Setting GUIDED mode first.")
            execute_set_mode_command('GUIDED')
            time.sleep(1)  # Give time for mode change to take effect
        
        # Check if drone is armed
        is_armed = False
        last_heartbeat = mav.recv_match(type='HEARTBEAT', blocking=False)
        if last_heartbeat and hasattr(last_heartbeat, 'base_mode'):
            is_armed = (last_heartbeat.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        
        if not is_armed:
            print("WARNING: Drone is not armed. Attempting to arm first.")
            if not execute_arm_command(True):
                print("Failed to arm. Takeoff aborted.")
                return False
            # Wait for arm to take effect
            time.sleep(1)
        
        # Send takeoff command
        print(f"Sending TAKEOFF command to altitude {altitude:.1f}m")
        mav.mav.command_long_send(
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0,  # Confirmation
            0, 0, 0, 0, 0, 0,  # param1-6 (ignored)
            altitude  # param7 = altitude
        )
        
        # Wait for command acknowledgment
        ack = mav.recv_match(type='COMMAND_ACK', blocking=True, timeout=3)
        if ack:
            if ack.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                print(f"TAKEOFF command accepted! Taking off to {altitude:.1f}m")
                return True
            else:
                result_codes = {
                    mavutil.mavlink.MAV_RESULT_DENIED: "DENIED",
                    mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED: "TEMPORARILY_REJECTED",
                    mavutil.mavlink.MAV_RESULT_UNSUPPORTED: "UNSUPPORTED",
                    mavutil.mavlink.MAV_RESULT_FAILED: "FAILED"
                }
                result_text = result_codes.get(ack.result, f"Unknown ({ack.result})")
                print(f"TAKEOFF command REJECTED: {result_text}")
                return False
        else:
            print("No acknowledgment received for TAKEOFF command")
            return False
            
    except Exception as e:
        print(f"Error executing TAKEOFF command: {e}")
        return False

def execute_goto_command(lat, lon, alt):
    """Execute a GOTO command to fly to a specific lat/lon/alt."""
    global mav
    try:
        print(f"\n----- Attempting GOTO to Lat:{lat:.7f}, Lon:{lon:.7f}, Alt:{alt:.1f}m -----")
        
        # Check if drone is in GUIDED mode (required for waypoint navigation)
        last_heartbeat = mav.recv_match(type='HEARTBEAT', blocking=False)
        current_mode = ''
        if last_heartbeat:
            base_mode = last_heartbeat.base_mode
            custom_mode = last_heartbeat.custom_mode
            current_mode = mavutil.mode_string_v10(base_mode, custom_mode)
            
        if 'GUIDED' not in current_mode:
            print(f"WARNING: Drone is not in GUIDED mode (current: {current_mode}). Setting GUIDED mode first.")
            execute_set_mode_command('GUIDED')
            time.sleep(1)  # Give time for mode change to take effect
        
        # Check if drone is armed
        is_armed = False
        last_heartbeat = mav.recv_match(type='HEARTBEAT', blocking=False)
        if last_heartbeat and hasattr(last_heartbeat, 'base_mode'):
            is_armed = (last_heartbeat.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        
        if not is_armed:
            print("WARNING: Drone is not armed. Attempting to arm first.")
            if not execute_arm_command(True):
                print("Failed to arm. GOTO aborted.")
                return False
            # Wait for arm to take effect
            time.sleep(1)
        
        # Send SET_POSITION_TARGET_GLOBAL_INT command (equivalent to GOTO)
        print(f"Sending GOTO command to Lat:{lat:.7f}, Lon:{lon:.7f}, Alt:{alt:.1f}m")
        mav.mav.set_position_target_global_int_send(
            0,       # time_boot_ms (not used)
            mav.target_system,
            mav.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
            0b110111111000,  # type_mask (position only: lat, lon, alt)
            int(lat * 1e7),  # lat_int (scaled)
            int(lon * 1e7),  # lon_int (scaled)
            float(alt),      # alt in meters
            0, 0, 0,  # vx, vy, vz (not used)
            0, 0, 0,  # afx, afy, afz (not used)
            0, 0      # yaw, yaw_rate (not used)
        )
        
        print(f"GOTO command sent successfully to Lat:{lat:.7f}, Lon:{lon:.7f}, Alt:{alt:.1f}m")
        # There's no direct ACK for SET_POSITION_TARGET_GLOBAL_INT, so we assume success if no exception
        return True
            
    except Exception as e:
        print(f"Error executing GOTO command: {e}")
        return False

def main():
    """Main function to connect to the drone and monitor MAVLink messages."""
    global mav
    print(f"Connecting to {MAVLINK_CONNECTION_STRING}...")
    
    # Set up connection retry loop
    max_retries = 5
    retry_count = 0
    connection_successful = False
    
    while retry_count < max_retries and not connection_successful:
        try:
            # Create the connection
            mav = mavutil.mavlink_connection(
                MAVLINK_CONNECTION_STRING,
                autoreconnect=True,
                source_system=255,
                source_component=0
            )
            
            # Wait for the first heartbeat
            print(f"Attempt {retry_count + 1}/{max_retries}: Waiting for heartbeat...")
            msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
            if not msg:
                print(f"Attempt {retry_count + 1}: No heartbeat received. Retrying...")
                retry_count += 1
                continue
            
            connection_successful = True
        except Exception as e:
            print(f"Connection error on attempt {retry_count + 1}: {e}")
            retry_count += 1
            time.sleep(2)  # Wait before retrying
    
    if not connection_successful:
        print(f"Failed to connect after {max_retries} attempts. Exiting.")
        return False
    
    print(f"Received heartbeat from system {msg.get_srcSystem()}")
    process_heartbeat(msg)
    
    # Set target system and component
    mav.target_system = msg.get_srcSystem()
    mav.target_component = msg.get_srcComponent()
    
    print(f"\nMonitoring MAVLink messages from {MAVLINK_CONNECTION_STRING}...")
    print("Press Ctrl+C to exit\n")
    
    # Start thread to save telemetry data to file
    save_thread = threading.Thread(target=save_telemetry_to_file, daemon=True)
    save_thread.start()
    print("Telemetry data saving thread started")
    
    # Start thread to check for commands
    command_thread = threading.Thread(target=check_for_commands, daemon=True)
    command_thread.start()
    print("Command checking thread started")
    
    # Track time for periodic summary
    last_summary_time = time.time()
    
    # Main loop to receive and process MAVLink messages
    try:
        while True:
            # Process incoming messages
            msg = mav.recv_match(blocking=True, timeout=1.0)
            if msg is not None:
                msg_type = msg.get_type()
                
                # Process different message types
                if msg_type == "HEARTBEAT":
                    process_heartbeat(msg)
                elif msg_type == "GLOBAL_POSITION_INT":
                    process_global_position_int(msg)
                elif msg_type == "VFR_HUD":
                    process_vfr_hud(msg)
                elif msg_type == "SYS_STATUS":
                    process_sys_status(msg)
                elif msg_type == "GPS_RAW_INT":
                    process_gps_raw_int(msg)
                elif msg_type == "ATTITUDE":
                    process_attitude(msg)
                elif msg_type == "HOME_POSITION":
                    process_home_position(msg)
                elif msg_type == "STATUSTEXT":
                    process_statustext(msg)
            
            # Periodically print a summary of telemetry data
            current_time = time.time()
            if current_time - last_summary_time > 30:  # Every 30 seconds
                print_telemetry_summary()
                last_summary_time = current_time
            
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

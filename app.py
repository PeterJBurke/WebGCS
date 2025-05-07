# *** ADDED: Windows Console Encoding Fix ***
import sys
import os
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# *** ADDED: Explicit Monkey Patching ***
from gevent import monkey
monkey.patch_all()

import sys
import time
import threading
import json
import gevent
from gevent.event import Event
# *** REMOVED: Imports for explicit gevent server ***
# from gevent import pywsgi
# from geventwebsocket.handler import WebSocketHandler
import math
import traceback
import collections
from pymavlink import mavutil
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# Import configuration
from config import (
    DRONE_TCP_ADDRESS,
    DRONE_TCP_PORT,
    MAVLINK_CONNECTION_STRING,
    WEB_SERVER_HOST,
    WEB_SERVER_PORT,
    SECRET_KEY,
    HEARTBEAT_TIMEOUT,
    REQUEST_STREAM_RATE_HZ,
    COMMAND_ACK_TIMEOUT,
    TELEMETRY_UPDATE_INTERVAL,
    AP_CUSTOM_MODES,
    AP_MODE_NAME_TO_ID
)

# --- Configuration ---
MAV_RESULT_ENUM = mavutil.mavlink.enums['MAV_RESULT']
MAV_RESULT_STR = {v: k for k, v in MAV_RESULT_ENUM.items()}
MAV_TYPE_ENUM = mavutil.mavlink.enums['MAV_TYPE']
MAV_TYPE_STR = {v: k for k, v in MAV_TYPE_ENUM.items()}
MAV_STATE_ENUM = mavutil.mavlink.enums['MAV_STATE']
MAV_STATE_STR = {v: k for k, v in MAV_STATE_ENUM.items()}
MAV_AUTOPILOT_ENUM = mavutil.mavlink.enums['MAV_AUTOPILOT']
MAV_AUTOPILOT_STR = {v: k for k, v in MAV_AUTOPILOT_ENUM.items()}
MAV_MODE_FLAG_ENUM = mavutil.mavlink.enums['MAV_MODE_FLAG']


# --- Flask & SocketIO Setup ---
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app,
                    async_mode='gevent',
                    cors_allowed_origins="*"  # Allow cross-origin requests
                   )


# --- Global State ---
mavlink_connection = None
mavlink_thread = None
telemetry_update_thread = None
last_heartbeat_time = 0
drone_state_changed = False
drone_state_lock = threading.Lock()
connection_event = Event()  # Added to coordinate connection attempts

drone_state = {
    'connected': False, 'armed': False, 'mode': 'UNKNOWN',
    'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0, 'alt_abs': 0.0, 'heading': 0.0,
    'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
    'airspeed': 0.0, 'groundspeed': 0.0,
    'battery_voltage': 0.0, 'battery_remaining': -1, 'battery_current': -1.0,
    'gps_fix_type': 0, 'satellites_visible': 0, 'hdop': 99.99,
    'system_status': 0,
    'pitch': 0.0, 'roll': 0.0,
    'home_lat': None, 'home_lon': None,
    'ekf_flags': 0,
    'ekf_status_report': 'EKF INIT',
}
data_streams_requested = False
home_position_requested = False
pending_commands = collections.OrderedDict() # {cmd_id: timestamp}
fence_request_pending = False # New flag for fence request
fence_request_lock = threading.Lock() # Lock for the flag
mission_request_pending = False # New flag for mission request
mission_request_lock = threading.Lock() # Lock for the mission flag

# --- MAVLink Helper Functions ---
def get_ekf_status_report(flags):
    if not (flags & mavutil.mavlink.MAV_SYS_STATUS_SENSOR_ANGULAR_RATE_CONTROL): return "EKF INIT (Gyro)"
    if not (flags & mavutil.mavlink.MAV_SYS_STATUS_SENSOR_ATTITUDE_STABILIZATION): return "EKF INIT (Att)"
    ekf_flags_bits = flags >> 16
    if not (ekf_flags_bits & mavutil.mavlink.EKF_ATTITUDE): return "EKF Bad Att"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_VELOCITY_HORIZ): return "EKF Bad Vel(H)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_VELOCITY_VERT): return "EKF Bad Vel(V)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_POS_HORIZ_ABS):
        if not (ekf_flags_bits & mavutil.mavlink.EKF_POS_HORIZ_REL): return "EKF Bad Pos(H)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_POS_VERT_ABS): return "EKF Bad Pos(V)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_PRED_POS_HORIZ_REL): return "EKF Variance (H)"
    return "EKF OK"

def log_command_action(command_name, params=None, details=None, level="INFO"):
    """Log command details to terminal in a standardized format with state tracking"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    params_str = f", Params: {params}" if params else ""
    details_str = f" - {details}" if details else ""
    
    # Format log message with a level indicator
    log_message = f"[{timestamp}] {level} | COMMAND: {command_name}{params_str}{details_str}"
    
    # Print with a visible separator for easier log reading
    print("\n" + "="*80)
    print(log_message)
    
    # For important commands, add current drone state summary
    if command_name in ['GOTO', 'SET_MODE', 'NAV_WAYPOINT', 'MAV_CMD_DO_SET_MODE'] or level == "ERROR":
        with drone_state_lock:
            state_summary = f"DRONE STATE: Mode={drone_state.get('mode', 'UNKNOWN')}, " \
                           f"Armed={drone_state.get('armed', False)}, " \
                           f"Connected={drone_state.get('connected', False)}, " \
                           f"Pos=({drone_state.get('lat', 0.0):.6f}, {drone_state.get('lon', 0.0):.6f}, Alt={drone_state.get('alt_rel', 0.0):.1f}m)"
            print(state_summary)
    
    print("="*80)
    return log_message

def process_heartbeat(msg):
    """Process HEARTBEAT message with enhanced logging for mode changes"""
    global last_heartbeat_time
    last_heartbeat_time = time.time()
    
    with drone_state_lock:
        prev_mode = drone_state.get('mode', 'UNKNOWN')
        prev_armed = drone_state.get('armed', False)
        
        # Update drone state
        drone_state['connected'] = True
        drone_state['armed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        
        if msg.get_srcSystem() == mavlink_connection.target_system:
            custom_mode_str = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
            new_mode = custom_mode_str[0] if custom_mode_str else 'UNKNOWN'
            drone_state['mode'] = new_mode
            
            # Log mode or armed state changes
            if new_mode != prev_mode:
                log_command_action("MODE_CHANGE", None, f"Mode changed from {prev_mode} to {new_mode}")
                
            if drone_state['armed'] != prev_armed:
                status = "ARMED" if drone_state['armed'] else "DISARMED"
                log_command_action("ARM_STATUS", None, f"Vehicle {status}")
    
    # Log detailed heartbeat information
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get human-readable enumerations
    mav_type = MAV_TYPE_STR.get(msg.type, f"UNKNOWN_TYPE({msg.type})")
    autopilot = MAV_AUTOPILOT_STR.get(msg.autopilot, f"UNKNOWN_AP({msg.autopilot})")
    system_status = MAV_STATE_STR.get(msg.system_status, f"UNKNOWN_STATE({msg.system_status})")
    
    # Extract base mode flags
    mode_flags = []
    for flag_bit, flag_name in MAV_MODE_FLAG_ENUM.items():
        if isinstance(flag_bit, int) and msg.base_mode & flag_bit:
            mode_flags.append(flag_name.name)
    mode_flags_str = ", ".join(mode_flags) if mode_flags else "NONE"
    
    # Get custom mode string
    custom_mode_str = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
    custom_mode_name = custom_mode_str[0] if custom_mode_str else f"UNKNOWN({msg.custom_mode})"
    
    # Format system/component ID
    sysid = msg.get_srcSystem()
    compid = msg.get_srcComponent()
    
    # Print detailed heartbeat log
    print(f"\n{'='*30} HEARTBEAT {'='*30}")
    print(f"[{timestamp}] HEARTBEAT from System:{sysid} Component:{compid}")
    print(f"├── Vehicle Type: {mav_type}")
    print(f"├── Autopilot: {autopilot}")
    print(f"├── System Status: {system_status}")
    print(f"├── Mode Flags: {mode_flags_str}")
    print(f"├── Custom Mode: {custom_mode_name} (Value: {msg.custom_mode})")
    print(f"├── Mavlink Version: {msg.mavlink_version}")
    print(f"└── Armed: {'YES' if drone_state['armed'] else 'NO'}")
    print(f"{'='*70}")
    
    drone_state_changed = True

def connect_mavlink():
    """Attempts to establish MAVLink connection TO the drone via UDP."""
    global mavlink_connection, last_heartbeat_time, data_streams_requested, home_position_requested, pending_commands, connection_event
    
    print("Attempting MAVLink connection...")
    
    # Close existing connection if any
    if mavlink_connection:
        try:
            mavlink_connection.close()
        except Exception as close_err:
            print(f"Error closing connection: {close_err}")
        finally:
            mavlink_connection = None

    # Reset state variables
    with drone_state_lock:
        drone_state['connected'] = False
        drone_state['armed'] = False
        drone_state['ekf_status_report'] = 'INIT'
    data_streams_requested = False
    home_position_requested = False
    pending_commands.clear()
    connection_event.clear()

    try:
        mavlink_connection = mavutil.mavlink_connection(MAVLINK_CONNECTION_STRING)
        print("MAVLink connection established")
        return True
    except Exception as e:
        print(f"MAVLink connection error: {e}")
        return False

def request_data_streams(req_rate_hz=REQUEST_STREAM_RATE_HZ):
    """Requests necessary data streams from the flight controller."""
    global data_streams_requested
    
    if not mavlink_connection or not drone_state.get("connected", False) or mavlink_connection.target_system == 0: 
        return

    try:
        target_sys = mavlink_connection.target_system
        target_comp = mavlink_connection.target_component
        messages_to_request = { 
            mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT: 1, 
            mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS: 1, 
            mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: 5, 
            mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD: 2, 
            mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE: 10, 
            mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT: 1, 
            mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION: 0.2, 
            mavutil.mavlink.MAVLINK_MSG_ID_STATUSTEXT: 1, 
            mavutil.mavlink.MAVLINK_MSG_ID_COMMAND_ACK: 5, 
        }
        for msg_id, rate_hz in messages_to_request.items():
            interval_us = int(1e6 / rate_hz) if rate_hz > 0 else -1
            if msg_id == mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION and home_position_requested: interval_us = -1
            if interval_us != -1 or (msg_id == mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION and not home_position_requested):
                mavlink_connection.mav.command_long_send(target_sys, target_comp, mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0, msg_id, interval_us, 0, 0, 0, 0, 0)
                gevent.sleep(0.05)
        data_streams_requested = True
    except Exception as req_err: 
        print(f"Error requesting data streams: {req_err}")
        data_streams_requested = False

def check_pending_command_timeouts():
    """Check for command timeouts and emit timeout messages."""
    global pending_commands
    current_time = time.time()
    timed_out_commands = []
    for cmd, send_time in pending_commands.items():
        if current_time - send_time > COMMAND_ACK_TIMEOUT:
            timed_out_commands.append(cmd)
            cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name if cmd in mavutil.mavlink.enums['MAV_CMD'] else f'ID {cmd}'
            print(f"Command {cmd_name} timed out")
            socketio.emit('command_ack_received', {
                'command': cmd,
                'command_name': cmd_name,
                'result': -1,  # Custom: Timeout
                'result_text': 'TIMEOUT'
            })
    for cmd in timed_out_commands:
        del pending_commands[cmd]

def process_command_ack(msg):
    """Process and log COMMAND_ACK messages with enhanced details"""
    cmd = msg.command
    result = msg.result
    
    # Get command name for logging
    cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name if cmd in mavutil.mavlink.enums['MAV_CMD'] else f'ID {cmd}'
    
    # Get result name
    result_name = MAV_RESULT_STR.get(result, 'UNKNOWN')
    
    # Skip logging and emitting MAV_CMD_REQUEST_MESSAGE commands with UNKNOWN results
    if cmd == mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE and result_name == 'UNKNOWN':
        # Just remove from pending commands silently
        if cmd in pending_commands:
            del pending_commands[cmd]
        return
    
    # Log with detailed explanation
    explanation = "Command acknowledged with"
    if result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
        explanation = "Command ACCEPTED by vehicle"
        level = "INFO"
    elif result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
        explanation = "Command TEMPORARILY REJECTED - vehicle might be in wrong state"
        level = "WARNING"
    elif result == mavutil.mavlink.MAV_RESULT_DENIED:
        explanation = "Command DENIED - vehicle rejected the command"
        level = "ERROR"
    elif result == mavutil.mavlink.MAV_RESULT_UNSUPPORTED:
        explanation = "Command UNSUPPORTED - vehicle does not support this command"
        level = "ERROR"
    elif result == mavutil.mavlink.MAV_RESULT_FAILED:
        explanation = "Command FAILED during execution"
        level = "ERROR"
    elif result == mavutil.mavlink.MAV_RESULT_IN_PROGRESS:
        explanation = "Command accepted and IN PROGRESS"
        level = "INFO"
    else:
        # Modified to provide more informative message for UNKNOWN result
        if result_name == 'UNKNOWN' and len(mavlink_connection.mav.command_ack_queue) > 0:
            # If we have pending commands and receive an UNKNOWN result, it's likely accepted
            explanation = "Command ACCEPTED by vehicle"
            level = "INFO"
        else:
            explanation = "Command response UNKNOWN - vehicle might be using different protocol"
            level = "WARNING"
    
    # Create a better display text for results
    display_result = result_name
    if result_name == 'UNKNOWN' and explanation == "Command ACCEPTED by vehicle":
        display_result = f"{result_name} - {explanation}"
    elif result == mavutil.mavlink.MAV_RESULT_UNSUPPORTED:
        display_result = f"{result_name} - {explanation}"
    elif result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
        display_result = f"{result_name} - {explanation}"
    elif result == mavutil.mavlink.MAV_RESULT_DENIED:
        display_result = f"{result_name} - {explanation}"
    elif result == mavutil.mavlink.MAV_RESULT_FAILED:
        display_result = f"{result_name} - {explanation}"
    
    log_command_action(f"ACK_{cmd_name}", f"Result: {display_result}", explanation, level)
    
    # Remove from pending commands if it exists
    if cmd in pending_commands:
        del pending_commands[cmd]
    
    # Emit to frontend
    socketio.emit('command_ack_received', {
        'command': cmd,
        'command_name': cmd_name,
        'result': result,
        'result_text': display_result,
        'explanation': explanation
    })

def mavlink_receive_loop():
    """Background thread for receiving MAVLink messages."""
    global mavlink_connection, last_heartbeat_time, drone_state_changed, data_streams_requested, home_position_requested
    print("MAVLink receive loop starting...")
    message_counts = collections.defaultdict(int)
    last_status_print = time.time()
    geofence_points = []
    
    while True:
        try:
            if not mavlink_connection:
                if connection_event.wait(timeout=5):
                    print("Connection event received")
                    continue
                else:
                    if connect_mavlink():
                        print("Reconnection successful")
                    gevent.sleep(1)
                    continue

            msg = mavlink_connection.recv_match(blocking=True, timeout=1.0)
            if msg:
                msg_type = msg.get_type()
                message_counts[msg_type] += 1
                
                # Update last status print time without printing
                current_time = time.time()
                if current_time - last_status_print >= 1.0:
                    last_status_print = current_time

                # Process messages with enhanced logging
                if msg_type == 'HEARTBEAT':
                    process_heartbeat(msg)
                elif msg_type == 'FENCE_POINT':
                    # Process fence point message
                    if msg.count > 0:  # Only process if we have fence points
                        print(f"Received FENCE_POINT {msg.idx + 1}/{msg.count}: Lat={msg.lat:.7f}, Lon={msg.lng:.7f}")
                        while len(geofence_points) <= msg.idx:
                            geofence_points.append(None)
                        geofence_points[msg.idx] = [msg.lat, msg.lng]
                        
                        # If we have all points and they're valid
                        if None not in geofence_points[:msg.count]:
                            print(f"Complete fence received with {msg.count} points")
                            # Emit the complete fence to the frontend
                            socketio.emit('geofence_update', {
                                'points': geofence_points[:msg.count]
                            })
                elif msg_type == 'FENCE_STATUS':
                    # Process fence status and request points if needed
                    breach_status = "No Breach" if msg.breach_status == 0 else f"BREACH TYPE {msg.breach_status}"
                    print(f"Received FENCE_STATUS: {breach_status}, Breach Count: {msg.breach_count}, Breach Time: {msg.breach_time}s")
                    if msg.breach_status == 0:  # No breach
                        if not geofence_points:  # If we don't have the fence points
                            print("No fence points in memory, requesting from drone...")
                            # Request fence point count
                            mavlink_connection.mav.command_long_send(
                                mavlink_connection.target_system,
                                mavlink_connection.target_component,
                                mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
                                0,
                                mavutil.mavlink.MAVLINK_MSG_ID_FENCE_POINT,
                                0, 0, 0, 0, 0, 0
                            )
                elif msg_type == 'GLOBAL_POSITION_INT':
                    with drone_state_lock:
                        drone_state['lat'] = msg.lat / 1e7
                        drone_state['lon'] = msg.lon / 1e7
                        drone_state['alt_rel'] = msg.relative_alt / 1000.0
                        drone_state['alt_abs'] = msg.alt / 1000.0
                        drone_state['vx'] = msg.vx / 100.0
                        drone_state['vy'] = msg.vy / 100.0
                        drone_state['vz'] = msg.vz / 100.0
                        drone_state['heading'] = msg.hdg / 100.0 if msg.hdg != 65535 else 0
                        drone_state['groundspeed'] = math.sqrt(drone_state['vx']**2 + drone_state['vy']**2)
                        drone_state['airspeed'] = drone_state['groundspeed']  # Approximation
                    drone_state_changed = True
                elif msg_type == 'VFR_HUD':
                    with drone_state_lock:
                        drone_state['airspeed'] = msg.airspeed
                        drone_state['groundspeed'] = msg.groundspeed
                    drone_state_changed = True
                elif msg_type == 'SYS_STATUS':
                    with drone_state_lock:
                        drone_state['battery_voltage'] = msg.voltage_battery / 1000.0 if msg.voltage_battery > 0 else 0
                        drone_state['battery_current'] = msg.current_battery / 100.0 if msg.current_battery != -1 else -1
                        drone_state['battery_remaining'] = msg.battery_remaining
                        drone_state['system_status'] = msg.onboard_control_sensors_present
                        drone_state['ekf_flags'] = msg.onboard_control_sensors_health
                        drone_state['ekf_status_report'] = get_ekf_status_report(msg.onboard_control_sensors_health)
                    drone_state_changed = True
                elif msg_type == 'GPS_RAW_INT':
                    with drone_state_lock:
                        drone_state['gps_fix_type'] = msg.fix_type
                        drone_state['satellites_visible'] = msg.satellites_visible
                        drone_state['hdop'] = msg.eph / 100.0 if msg.eph != 65535 else 99.99
                    drone_state_changed = True
                elif msg_type == 'ATTITUDE':
                    with drone_state_lock:
                        drone_state['pitch'] = msg.pitch
                        drone_state['roll'] = msg.roll
                    drone_state_changed = True
                elif msg_type == 'HOME_POSITION':
                    with drone_state_lock:
                        drone_state['home_lat'] = msg.latitude / 1e7
                        drone_state['home_lon'] = msg.longitude / 1e7
                    home_position_requested = True
                    drone_state_changed = True
                elif msg_type == 'STATUSTEXT':
                    text = msg.text.strip()
                    if text:
                        severity_str = ['EMERGENCY', 'ALERT', 'CRITICAL', 'ERROR', 'WARNING', 'NOTICE', 'INFO', 'DEBUG'][msg.severity]
                        print(f"Status Text ({severity_str}): {text}")
                        msg_type = 'error' if msg.severity <= 3 else 'warning' if msg.severity == 4 else 'info'
                        socketio.emit('status_message', {'text': text, 'type': msg_type})
                elif msg_type == 'COMMAND_ACK':
                    process_command_ack(msg)
                socketio.emit('mavlink_message', {'mavpackettype': msg_type})

            # Check for command timeouts
            check_pending_command_timeouts()

            # Check heartbeat timeout
            if time.time() - last_heartbeat_time > HEARTBEAT_TIMEOUT:
                with drone_state_lock:
                    if drone_state['connected']:
                        print("Heartbeat timeout - marking drone as disconnected")
                        drone_state['connected'] = False
                        drone_state_changed = True

            # Request data streams if needed
            if drone_state['connected'] and not data_streams_requested:
                request_data_streams()

            # Request home position if needed
            if drone_state['connected'] and not home_position_requested:
                try:
                    mavlink_connection.mav.command_long_send(
                        mavlink_connection.target_system,
                        mavlink_connection.target_component,
                        mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,
                        0, mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION,
                        0, 0, 0, 0, 0, 0
                    )
                except Exception as e:
                    print(f"Error requesting home position: {e}")
            
            # --- Handle Pending Fence Request ---
            if fence_request_pending:
                _execute_fence_request()
            # ---------------------------------
            
            # --- Handle Pending Mission Request ---
            if mission_request_pending:
                _execute_mission_request()
            # ---------------------------------

        except Exception as e:
            print(f"Error in MAVLink receive loop: {e}")
            traceback.print_exc()
            gevent.sleep(1)

def _execute_fence_request():
    """Executes the fence request logic. Called from main loop."""
    global fence_request_pending, mavlink_connection
    
    # Reset flag immediately
    with fence_request_lock:
        fence_request_pending = False
        
    print("\n--- Executing Pending Fence Request ---")
    status_msg = "Starting fence request..."
    cmd_type = 'info'
    success = False
    fence_points = []
    
    try:
        if not mavlink_connection or not drone_state.get("connected", False):
            raise Exception("Cannot request fence: Drone not connected.")

        target_sys = mavlink_connection.target_system
        target_comp = mavlink_connection.target_component
        print(f"Requesting mission list for SYS:{target_sys} COMP:{target_comp}...")

        mavlink_connection.mav.mission_request_list_send(
            target_sys, target_comp, mavutil.mavlink.MAV_MISSION_TYPE_FENCE
        )

        print("Waiting for MISSION_COUNT...")
        msg = mavlink_connection.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)

        if not msg:
            raise Exception("Timeout waiting for MISSION_COUNT.")
        if msg.mission_type != mavutil.mavlink.MAV_MISSION_TYPE_FENCE:
            raise Exception(f"Received MISSION_COUNT for wrong mission type: {msg.mission_type}")

        fence_count = msg.count
        print(f"Found {fence_count} fence items.")
        socketio.emit('status_message', {'text': f"Found {fence_count} fence points", 'type': 'info'})

        if fence_count == 0:
            status_msg = "No fence points defined."
            cmd_type = 'warning'
            success = True
        else:
            for seq in range(fence_count):
                print(f"Requesting fence point {seq + 1}/{fence_count}...")
                mavlink_connection.mav.mission_request_send(
                    target_sys, target_comp, seq, mavutil.mavlink.MAV_MISSION_TYPE_FENCE
                )
                print("Waiting for MISSION_ITEM...")
                item = mavlink_connection.recv_match(type='MISSION_ITEM', blocking=True, timeout=5)
                if not item:
                    raise Exception(f"Timeout waiting for MISSION_ITEM {seq}.")
                
                lat = item.x / 1e7 if abs(item.x) > 180 else item.x
                lon = item.y / 1e7 if abs(item.y) > 180 else item.y
                print(f"  Point {seq+1}: Lat={lat:.7f}, Lon={lon:.7f}, Alt={item.z:.2f}")
                fence_points.append([lat, lon])

            # Print summary
            print("\nFence Summary:")
            print("-------------")
            for idx, point in enumerate(fence_points):
                print(f"Point {idx + 1}: Lat={point[0]:.7f}, Lon={point[1]:.7f}")
            
            socketio.emit('geofence_update', {'points': fence_points})
            status_msg = f"Retrieved {fence_count} fence points successfully."
            cmd_type = 'info'
            success = True

    except Exception as e:
        status_msg = f"Error during fence request: {e}"
        cmd_type = 'error'
        success = False
        print(f"\nError: {status_msg}")
        traceback.print_exc()

    finally:
        print("--- Fence Request Execution Finished ---")
        # Emit final status for the operation initiated by REQUEST_FENCE
        socketio.emit('status_message', {'text': status_msg, 'type': cmd_type})
        socketio.emit('command_result', {'command': 'REQUEST_FENCE', 'success': success, 'message': status_msg})

def _execute_mission_request():
    """Executes the mission request logic. Called from main loop."""
    global mission_request_pending, mavlink_connection
    
    # Reset flag immediately
    with mission_request_lock:
        mission_request_pending = False
        
    print("\n--- Executing Pending Mission Request ---")
    status_msg = "Starting mission request..."
    cmd_type = 'info'
    success = False
    waypoints = []
    
    try:
        if not mavlink_connection or not drone_state.get("connected", False):
            raise Exception("Cannot request mission: Drone not connected.")

        target_sys = mavlink_connection.target_system
        target_comp = mavlink_connection.target_component
        print(f"Requesting mission list for SYS:{target_sys} COMP:{target_comp}...")

        mavlink_connection.mav.mission_request_list_send(
            target_sys, target_comp, mavutil.mavlink.MAV_MISSION_TYPE_MISSION
        )

        print("Waiting for MISSION_COUNT...")
        msg = mavlink_connection.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)

        if not msg:
            raise Exception("Timeout waiting for MISSION_COUNT.")
        if msg.mission_type != mavutil.mavlink.MAV_MISSION_TYPE_MISSION:
            raise Exception(f"Received MISSION_COUNT for wrong mission type: {msg.mission_type}")

        waypoint_count = msg.count
        print(f"Found {waypoint_count} mission waypoints.")
        socketio.emit('status_message', {'text': f"Found {waypoint_count} waypoints", 'type': 'info'})

        if waypoint_count == 0:
            status_msg = "No mission waypoints defined."
            cmd_type = 'warning'
            success = True
            socketio.emit('mission_update', {'waypoints': []})
        else:
            for seq in range(waypoint_count):
                print(f"Requesting waypoint {seq + 1}/{waypoint_count}...")
                mavlink_connection.mav.mission_request_send(
                    target_sys, target_comp, seq, mavutil.mavlink.MAV_MISSION_TYPE_MISSION
                )
                print("Waiting for MISSION_ITEM...")
                item = mavlink_connection.recv_match(type='MISSION_ITEM', blocking=True, timeout=5)
                if not item:
                    raise Exception(f"Timeout waiting for MISSION_ITEM {seq}.")
                
                # Process waypoint data
                lat = item.x
                lon = item.y
                alt = item.z
                cmd = item.command
                frame = item.frame
                param1 = item.param1
                param2 = item.param2
                param3 = item.param3
                param4 = item.param4
                
                # Get command name if available
                cmd_name = "UNKNOWN"
                if hasattr(mavutil.mavlink, 'enums') and 'MAV_CMD' in mavutil.mavlink.enums:
                    if cmd in mavutil.mavlink.enums['MAV_CMD']:
                        cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name
                
                # Get frame name if available
                frame_name = "UNKNOWN"
                if hasattr(mavutil.mavlink, 'enums') and 'MAV_FRAME' in mavutil.mavlink.enums:
                    if frame in mavutil.mavlink.enums['MAV_FRAME']:
                        frame_name = mavutil.mavlink.enums['MAV_FRAME'][frame].name
                
                print(f"  Command: {cmd} ({cmd_name})")
                print(f"  Frame: {frame} ({frame_name})")
                print(f"  Location: Lat={lat:.7f}, Lon={lon:.7f}, Alt={alt:.2f}m")
                print(f"  Parameters: [{param1:.2f}, {param2:.2f}, {param3:.2f}, {param4:.2f}]")
                
                waypoints.append({
                    'seq': item.seq,
                    'command': cmd,
                    'command_name': cmd_name,
                    'frame': frame,
                    'frame_name': frame_name,
                    'lat': lat,
                    'lon': lon,
                    'alt': alt,
                    'param1': param1,
                    'param2': param2,
                    'param3': param3,
                    'param4': param4
                })

            # Send mission acknowledgment
            mavlink_connection.mav.mission_ack_send(
                target_sys, target_comp, 
                mavutil.mavlink.MAV_MISSION_ACCEPTED,
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )

            # Print summary in the terminal
            print("\nMission Summary:")
            print("----------------")
            for i, wp in enumerate(waypoints):
                cmd_desc = f"{wp['command']} ({wp['command_name']})"
                if wp['command'] == mavutil.mavlink.MAV_CMD_NAV_WAYPOINT:
                    print(f"WP #{i+1}: WAYPOINT at Lat={wp['lat']:.7f}, Lon={wp['lon']:.7f}, Alt={wp['alt']:.2f}m")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF:
                    print(f"WP #{i+1}: TAKEOFF to Alt={wp['alt']:.2f}m")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_NAV_LAND:
                    print(f"WP #{i+1}: LAND at Lat={wp['lat']:.7f}, Lon={wp['lon']:.7f}")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH:
                    print(f"WP #{i+1}: RETURN TO LAUNCH")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_DO_JUMP:
                    print(f"WP #{i+1}: DO JUMP to #{int(wp['param1'])+1}, {int(wp['param2'])} times")
                else:
                    print(f"WP #{i+1}: {cmd_desc} at Lat={wp['lat']:.7f}, Lon={wp['lon']:.7f}, Alt={wp['alt']:.2f}m")
            
            socketio.emit('mission_update', {'waypoints': waypoints})
            status_msg = f"Retrieved {waypoint_count} waypoints successfully."
            cmd_type = 'info'
            success = True

    except Exception as e:
        status_msg = f"Error during mission request: {e}"
        cmd_type = 'error'
        success = False
        print(f"\nError: {status_msg}")
        traceback.print_exc()

    finally:
        print("--- Mission Request Execution Finished ---")
        # Emit final status for the operation initiated by REQUEST_MISSION
        socketio.emit('status_message', {'text': status_msg, 'type': cmd_type})
        socketio.emit('command_result', {'command': 'REQUEST_MISSION', 'success': success, 'message': status_msg})

def periodic_telemetry_update():
    """Periodically send telemetry updates to web clients."""
    global drone_state_changed
    update_count = 0
    
    while True:
        try:
            if drone_state_changed:
                with drone_state_lock:
                    socketio.emit('telemetry_update', drone_state)
                    drone_state_changed = False
                    update_count += 1
            gevent.sleep(TELEMETRY_UPDATE_INTERVAL)
        except Exception as e:
            print(f"Error in telemetry update: {e}")
            gevent.sleep(1)


# --- Flask Routes and SocketIO Handlers ---
@app.route('/')
def index():
    return render_template("index.html", version="v2.63-Desktop-TCP-AckEkf")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/favicon.ico')
def favicon():
    # Return "204 No Content" which tells the browser there is no icon without causing an error
    return '', 204

@app.route('/mavlink_dump')
def mavlink_dump():
    return render_template("mavlink_dump.html", version="v2.63-Desktop-TCP-AckEkf")

@socketio.on('connect')
def handle_connect():
    print("Web UI Client connected")
    emit('telemetry_update', drone_state)
    status_text = 'Backend connected. '
    status_text += 'Drone link active.' if drone_state.get('connected') else 'Attempting drone link...'
    emit('status_message', {'text': status_text, 'type': 'info'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Web UI Client disconnected")

def send_mavlink_command(command, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0):
    global mavlink_connection, pending_commands
    
    # Get command name for logging
    cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'
    
    if not mavlink_connection or not drone_state.get("connected", False):
        warn_msg = f"CMD {cmd_name} Failed: Drone not connected."
        log_command_action(cmd_name, None, f"ERROR: {warn_msg}", "ERROR")
        return (False, warn_msg)
        
    target_sys = mavlink_connection.target_system
    target_comp = mavlink_connection.target_component
    
    if target_sys == 0:
        err_msg = f"CMD {cmd_name} Failed: Invalid target system."
        log_command_action(cmd_name, None, f"ERROR: {err_msg}", "ERROR")
        return (False, err_msg)
        
    try:
        # Format the parameters for logging
        params = f"p1={p1:.2f}, p2={p2:.2f}, p3={p3:.2f}, p4={p4:.2f}, p5={p5:.6f}, p6={p6:.6f}, p7={p7:.2f}"
        
        # Log using our new function with full details
        log_command_action(cmd_name, params, f"To SYS:{target_sys} COMP:{target_comp}", "INFO")
        
        # Keep the original logging as well for now
        print(f"Sending CMD {cmd_name} ({command}) to SYS:{target_sys} COMP:{target_comp} | Params: {params}")
        
        mavlink_connection.mav.command_long_send(target_sys, target_comp, command, 0, p1, p2, p3, p4, p5, p6, p7)
        
        if command not in [mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE]:
            pending_commands[command] = time.time()
            if len(pending_commands) > 30:
                oldest_cmd = next(iter(pending_commands))
                print(f"Warning: Pending cmd limit, removing oldest: {oldest_cmd}")
                del pending_commands[oldest_cmd]
                
        success_msg = f"CMD {cmd_name} sent."
        return (True, success_msg)
    except Exception as e:
        err_msg = f"CMD {cmd_name} Send Error: {e}"
        log_command_action(cmd_name, None, f"EXCEPTION: {err_msg}", "ERROR")
        traceback.print_exc()
        return (False, err_msg)

def request_geofence_data():
    """Request geofence data using the mission protocol."""
    if not mavlink_connection or not drone_state.get("connected", False):
        print("Cannot request geofence: No connection")
        return False

    try:
        print("\nRequesting geofence mission list...")
        # Request the geofence mission list
        mavlink_connection.mav.mission_request_list_send(
            mavlink_connection.target_system,
            mavlink_connection.target_component,
            mavutil.mavlink.MAV_MISSION_TYPE_FENCE
        )

        # Wait for MISSION_COUNT
        msg = mavlink_connection.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)
        if not msg:
            msg = "No response to mission list request"
            cmd_type = 'error'
            success = False
            socketio.emit('status_message', {'text': msg, 'type': cmd_type})
            return
        
        if msg.mission_type != mavutil.mavlink.MAV_MISSION_TYPE_FENCE:
            msg = "Received mission count but not for fence"
            cmd_type = 'error'
            success = False
            socketio.emit('status_message', {'text': msg, 'type': cmd_type})
            return

        fence_count = msg.count
        print(f"\nNumber of geofence items: {fence_count}")
        socketio.emit('status_message', {'text': f"Found {fence_count} fence points", 'type': 'info'})
        
        if fence_count == 0:
            msg = "No fence points defined"
            cmd_type = 'warning'
            success = True
            socketio.emit('status_message', {'text': msg, 'type': cmd_type})
            return

        fence_points = []

        # Request each fence point
        for seq in range(fence_count):
            print(f"\nRequesting fence point {seq + 1}/{fence_count}")
            mavlink_connection.mav.mission_request_send(
                mavlink_connection.target_system,
                mavlink_connection.target_component,
                seq,
                mavutil.mavlink.MAV_MISSION_TYPE_FENCE
            )

            item = mavlink_connection.recv_match(type='MISSION_ITEM', blocking=True, timeout=5)
            if item:
                # Convert lat/lon from int to float degrees
                lat = item.x / 1e7 if abs(item.x) > 180 else item.x
                lon = item.y / 1e7 if abs(item.y) > 180 else item.y
                
                print(f"  Command: {item.command}")
                print(f"  Frame: {item.frame}")
                print(f"  Location: Lat={lat:.7f}, Lon={lon:.7f}, Alt={item.z:.2f}")
                
                fence_points.append([lat, lon])
            else:
                msg = f"Timeout waiting for fence point {seq}"
                cmd_type = 'error'
                success = False
                socketio.emit('status_message', {'text': msg, 'type': cmd_type})
                return

        # Send the complete fence to the frontend
        socketio.emit('geofence_update', {
            'points': fence_points
        })
        
        success = True
        msg = f"Retrieved {fence_count} fence points successfully"
        cmd_type = 'info'
        
    except Exception as e:
        success = False
        msg = f"Error requesting geofence: {e}"
        cmd_type = 'error'
        print(msg)

    socketio.emit('status_message', {'text': msg, 'type': cmd_type})
    socketio.emit('command_result', {'command': cmd, 'success': success, 'message': msg})

@socketio.on('send_command')
def handle_send_command(data):
    """Handles commands received from the web UI."""
    global fence_request_pending, mission_request_pending
    cmd = data.get('command')
    
    # Log the command receipt
    log_data = {k: v for k, v in data.items() if k != 'command'}  # Get all params except command
    log_command_action(f"RECEIVED_{cmd}", str(log_data) if log_data else None, "Command received from UI", "INFO")
    
    print(f"UI Command Received: {cmd} Data: {data}")
    success = False
    msg = f'{cmd} processing...'
    cmd_type = 'info'

    if not drone_state.get("connected", False):
        msg = f'CMD {cmd} Fail: Disconnected.'
        cmd_type = 'error'
        log_command_action(cmd, None, f"ERROR: {msg}", "ERROR")
        socketio.emit('status_message', {'text': msg, 'type': cmd_type})
        socketio.emit('command_result', {'command': cmd, 'success': False, 'message': msg})
        return

    if cmd == 'ARM':
        success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=1)
        cmd_type = 'info' if success else 'error'
        msg = f'ARM command sent.' if success else f'ARM Failed: {msg_send}'
    elif cmd == 'DISARM':
        success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=0)
        cmd_type = 'info' if success else 'error'
        msg = f'DISARM command sent.' if success else f'DISARM Failed: {msg_send}'
    elif cmd == 'TAKEOFF':
        try:
            alt = float(data.get('altitude', 5.0))
            if not (0 < alt <= 1000):
                raise ValueError("Altitude must be > 0 and <= 1000")
            success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, p7=alt)
            cmd_type = 'info' if success else 'error'
            msg = f'Takeoff to {alt:.1f}m command sent.' if success else f'Takeoff Failed: {msg_send}'
        except (ValueError, TypeError) as e:
            success = False
            msg = f'Invalid Takeoff Alt: {e}'
            cmd_type = 'error'
    elif cmd == 'LAND':
        success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_NAV_LAND)
        cmd_type = 'info' if success else 'error'
        msg = 'LAND command sent.' if success else f'LAND Failed: {msg_send}'
    elif cmd == 'RTL':
        success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
        cmd_type = 'info' if success else 'error'
        msg = 'RTL command sent.' if success else f'RTL Failed: {msg_send}'
    elif cmd == 'SET_MODE':
        mode_string = data.get('mode_string')
        if mode_string and mode_string in AP_CUSTOM_MODES:
            custom_mode = AP_CUSTOM_MODES[mode_string]
            base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
            print(f"Attempting to set mode: {mode_string} (Custom Mode: {custom_mode})")
            success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_DO_SET_MODE, p1=base_mode, p2=custom_mode)
            cmd_type = 'info' if success else 'error'
            msg = f'Set Mode {mode_string} command sent.' if success else f'Set Mode {mode_string} Failed: {msg_send}'
        else:
            success = False
            msg = f'Invalid/Unknown Mode: {mode_string}'
            cmd_type = 'error'
    elif cmd == 'GOTO':
        try:
            lat = float(data.get('lat'))
            lon = float(data.get('lon'))
            alt = float(data.get('alt'))
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude out of range [-90, 90]")
            if not (-180 <= lon <= 180):
                raise ValueError("Longitude out of range [-180, 180]")
            if not (-100 <= alt <= 5000):
                raise ValueError("Altitude out of range [-100, 5000]")
            
            log_command_action("GOTO", 
                               f"Lat: {lat:.7f}, Lon: {lon:.7f}, Alt: {alt:.1f}m",
                               "Processing flight command", 
                               "INFO")
            
            # First, set the mode to GUIDED using direct SET_MODE method
            if 'GUIDED' not in AP_CUSTOM_MODES:
                raise Exception("GUIDED mode not available in AP_CUSTOM_MODES")
                
            if not mavlink_connection:
                raise Exception("No MAVLink connection")
            
            # Set the mode to GUIDED
            guided_mode = AP_CUSTOM_MODES['GUIDED']
            print(f"Setting mode to GUIDED (Custom Mode: {guided_mode}) using direct method")
            log_command_action("SET_MODE", f"Mode: GUIDED ({guided_mode})", "Setting mode via direct command", "INFO")
            
            mavlink_connection.mav.set_mode_send(
                mavlink_connection.target_system,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                guided_mode
            )
            
            # Wait briefly for mode to change
            time.sleep(1)
            
            # Log the GoTo command
            print(f"Sending position target to Lat:{lat:.6f}, Lon:{lon:.6f}, Alt:{alt:.1f}m")
            log_command_action("SET_POSITION_TARGET_GLOBAL_INT", 
                               f"Lat: {lat:.7f}, Lon: {lon:.7f}, Alt: {alt:.1f}m",
                               "Sending position target for guided navigation", 
                               "INFO")
            
            # Use SET_POSITION_TARGET_GLOBAL_INT for guided mode
            mavlink_connection.mav.set_position_target_global_int_send(
                0,       # time_boot_ms (not used)
                mavlink_connection.target_system,  # target system
                mavlink_connection.target_component,  # target component
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
                0b110111111000,  # type_mask (only position)
                int(lat * 1e7),  # lat_int - latitude in 1e7 degrees
                int(lon * 1e7),  # lon_int - longitude in 1e7 degrees
                float(alt),      # altitude in meters
                0, 0, 0,  # velocity x, y, z (not used)
                0, 0, 0,  # acceleration x, y, z (not used)
                0, 0      # yaw, yaw_rate (not used)
            )
            
            success = True
            msg_send = "GoTo command sent using SET_POSITION_TARGET_GLOBAL_INT"
            cmd_type = 'info'
            msg = f'GoTo sent (Lat:{lat:.6f}, Lon:{lon:.6f}, Alt:{alt:.1f}m)'
            
        except Exception as e:
            success = False
            msg = f'Error sending GoTo command: {str(e)}'
            cmd_type = 'error'
            log_command_action("GOTO", None, f"ERROR: {msg}", "ERROR")
            traceback.print_exc()
    elif cmd == 'REQUEST_FENCE':
        print(f"\nReceived UI command: {cmd}")
        with fence_request_lock:
            if not fence_request_pending:
                fence_request_pending = True
                success = True
                msg = "Fence request initiated."
                cmd_type = 'info'
                print(msg)
            else:
                success = False
                msg = "Fence request already in progress."
                cmd_type = 'warning'
                print(msg)
    elif cmd == 'REQUEST_MISSION':
        print(f"\nReceived UI command: {cmd}")
        with mission_request_lock:
            if not mission_request_pending:
                mission_request_pending = True
                success = True
                msg = "Mission request initiated."
                cmd_type = 'info'
                print(msg)
            else:
                success = False
                msg = "Mission request already in progress."
                cmd_type = 'warning'
                print(msg)
    else:
        msg = f'Unknown command received: {cmd}'
        cmd_type = 'warning'
        success = False

    socketio.emit('status_message', {'text': msg, 'type': cmd_type})
    socketio.emit('command_result', {'command': cmd, 'success': success, 'message': msg})


if __name__ == '__main__':
    print(f"Starting server on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    # Start the background threads
    mavlink_thread = gevent.spawn(mavlink_receive_loop)
    telemetry_update_thread = gevent.spawn(periodic_telemetry_update)
    socketio.run(app, 
                host=WEB_SERVER_HOST, 
                port=WEB_SERVER_PORT, 
                debug=True,
                use_reloader=False)  # Disable reloader to prevent duplicate threads

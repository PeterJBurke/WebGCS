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
import datetime
import socket

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
    AP_MODE_NAME_TO_ID,
    MAVLINK_DIALECT,             # Added import
    RECONNECTION_ATTEMPT_DELAY,   # Added import
    DEBUG,                        # Added import
    DRONE_BAUD_RATE,              # Added import
    MAVLINK_SOURCE_SYSTEM         # Added import
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

# --- Logging Helper ---
def log_message(message, level="INFO"):
    """Prints a standardized log message with timestamp and level."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level:<8} | {message}")

# --- Constants for MAVLink connection ---
CONNECTION_ATTEMPT_TIMEOUT_S = 5 # Timeout for establishing initial connection
HEARTBEAT_WAIT_ITERATIONS = 10 # Number of iterations to wait for heartbeat
HEARTBEAT_WAIT_PER_ITERATION_S = 1 # Seconds for each individual wait_heartbeat call
MESSAGE_RECEIVE_TIMEOUT_S = 1     # Timeout for master.recv_match() in message loop
MAVLINK_THREAD_STOP_TIMEOUT_S = 5 # Seconds to wait for the MAVLink thread to stop

# --- Flask & SocketIO Setup ---
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app,
                    async_mode='gevent',
                    cors_allowed_origins="*"  # Allow cross-origin requests
                   )


# --- Global State ---
master = None
mav_thread = None
telemetry_update_thread = None
drone_state_changed = False # Flag to indicate drone_state has changed and needs to be emitted
drone_state_lock = threading.Lock()
connection_event = Event()  # Added to coordinate connection attempts
telemetry_loop_active = False # Global flag to indicate if the main telemetry loop in mavlink_receive_loop is active

# Globals for dynamic MAVLink target and thread control
current_mavlink_target_ip = DRONE_TCP_ADDRESS
current_mavlink_target_port = DRONE_TCP_PORT
mavlink_thread_stop_event = threading.Event() # Used to signal the MAVLink thread to stop
mavlink_connection_lock = threading.Lock() # Protects master, mav_thread, and target IP/Port manipulation

# Initialize drone_state with all expected keys
drone_state = {
    'connected': False,
    'armed': False,
    'mode': 'UNKNOWN',
    'message': '',
    'last_heartbeat_time': 0, # Initialize last_heartbeat_time
    'ekf_status': None,
    'battery': None,
    'gps_fix_type': 0,
    'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0, 'alt_abs': 0.0, 'heading': 0.0,
    'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
    'airspeed': 0.0, 'groundspeed': 0.0,
    'battery_voltage': 0.0, 'battery_remaining': -1, 'battery_current': -1.0,
    'satellites_visible': 0, 'hdop': 99.99,
    'system_status': 0,
    'pitch': 0.0, 'roll': 0.0,
    'home_lat': None, 'home_lon': None,
    'ekf_flags': 0,
    'ekf_status_report': 'EKF INIT',
    'mavlink_target_ip': DRONE_TCP_ADDRESS,  # Use global
    'mavlink_target_port': DRONE_TCP_PORT   # Use global
}
data_streams_requested = False
home_position_requested = False
pending_commands = collections.OrderedDict() # {cmd_id: timestamp}
fence_request_pending = False # New flag for fence request
fence_request_lock = threading.Lock() # Lock for the flag
mission_request_pending = False # New flag for mission request
mission_request_lock = threading.Lock() # Lock for the mission flag

# --- Helper Functions ---
def emit_status_message(text, message_type, room=None):
    """Helper function to emit a status message to the client(s)."""
    print(f"STATUS [{message_type.upper()}]: {text}" + (f" (Room: {room})" if room else ""))
    if room:
        socketio.emit('status_message', {'text': text, 'type': message_type}, room=room)
    else:
        socketio.emit('status_message', {'text': text, 'type': message_type})

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
    # No longer using global last_heartbeat_time, update drone_state directly
    # last_heartbeat_time = time.time()
    
    with drone_state_lock:
        drone_state['last_heartbeat_time'] = time.time() # Update drone_state
        prev_mode = drone_state.get('mode', 'UNKNOWN')
        prev_armed = drone_state.get('armed', False)
        
        # Update drone state
        drone_state['connected'] = True
        drone_state['armed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        
        if master and msg.get_srcSystem() == master.target_system:
            custom_mode_str = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
            new_mode = custom_mode_str[0] if custom_mode_str else 'UNKNOWN'
            drone_state['mode'] = new_mode
            
            # Log mode or armed state changes
            if new_mode != prev_mode:
                log_command_action("MODE_CHANGE", None, f"Mode changed from {prev_mode} to {new_mode}")
                
            if drone_state['armed'] != prev_armed:
                status = "ARMED" if drone_state['armed'] else "DISARMED"
                log_command_action("ARM_STATUS", None, f"Vehicle {status}")
    
    # Detailed human-readable log for heartbeat at INFO level - d892ba4 style
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    sysid = msg.get_srcSystem()
    compid = msg.get_srcComponent()
    type_str = mavutil.mavlink.enums['MAV_TYPE'][msg.type].name if msg.type in mavutil.mavlink.enums['MAV_TYPE'] else str(msg.type)
    autopilot_str = mavutil.mavlink.enums['MAV_AUTOPILOT'][msg.autopilot].name if msg.autopilot in mavutil.mavlink.enums['MAV_AUTOPILOT'] else str(msg.autopilot)
    armed_str = "ARMED" if drone_state['armed'] else "DISARMED"
    status_str = mavutil.mavlink.enums['MAV_STATE'][msg.system_status].name if msg.system_status in mavutil.mavlink.enums['MAV_STATE'] else str(msg.system_status)
    
    separator = "=" * 80 # 80 characters for the separator line
    heartbeat_details = (
        f"[{timestamp_str}] HEARTBEAT\n"
        f"  SYS: {sysid}\n"
        f"  COMP: {compid}\n"
        f"  Type: {type_str}\n"
        f"  Autopilot: {autopilot_str}\n"
        f"  Mode: {drone_state['mode']}\n"
        f"  Armed: {armed_str}\n"
        f"  Status: {status_str}\n"
        f"  MAVLink Version: {msg.mavlink_version}"
    )
    print(heartbeat_details)
    print(separator)
    
    # Emit an event for the UI to indicate a heartbeat was received
    socketio.emit('heartbeat_received', {'sysid': sysid, 'compid': compid})

    # Conditional detailed print based on DEBUG flag from config
    if DEBUG:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        sysid = msg.get_srcSystem()
        compid = msg.get_srcComponent()
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
        
        print(f"\n{'='*30} HEARTBEAT (Detailed) {'='*30}")
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

def handle_mavlink_message(msg):
    """Processes various MAVLink messages and updates drone_state."""
    global drone_state, drone_state_changed, data_streams_requested, home_position_requested
    msg_type = msg.get_type()

    if msg_type == 'HEARTBEAT':
        process_heartbeat(msg)
        return # process_heartbeat handles its own state change flag

    # For other messages, acquire lock to modify drone_state
    with drone_state_lock:
        changed_in_this_handler = False # Flag to track if this specific handler instance changed state

        if msg_type == 'COMMAND_ACK':
            process_command_ack(msg) # This function handles logging and emits to SocketIO
            # It doesn't typically change drone_state directly, so no changed_in_this_handler = True

        elif msg_type == 'GLOBAL_POSITION_INT':
            drone_state['lat'] = msg.lat / 1e7
            drone_state['lon'] = msg.lon / 1e7
            drone_state['alt_rel'] = msg.relative_alt / 1000.0  # meters
            drone_state['alt_abs'] = msg.alt / 1000.0  # meters MSL
            drone_state['hdg'] = msg.hdg / 100.0  # degrees
            changed_in_this_handler = True
        
        elif msg_type == 'ATTITUDE':
            drone_state['pitch'] = math.degrees(msg.pitch)
            drone_state['roll'] = math.degrees(msg.roll)
            # Yaw (heading) is often more reliably taken from GLOBAL_POSITION_INT.hdg or VFR_HUD.heading
            changed_in_this_handler = True

        elif msg_type == 'VFR_HUD':
            drone_state['airspeed'] = msg.airspeed  # m/s
            drone_state['groundspeed'] = msg.groundspeed  # m/s
            # drone_state['alt_rel'] = msg.alt # VFR_HUD alt is often AGL, GLOBAL_POSITION_INT.relative_alt is AMSL or AGL depending on source
            drone_state['heading'] = msg.heading  # degrees
            # drone_state['throttle'] = msg.throttle # throttle percentage 0-100
            changed_in_this_handler = True

        elif msg_type == 'SYS_STATUS':
            drone_state['battery_voltage'] = msg.voltage_battery / 1000.0  # V
            drone_state['battery_remaining'] = msg.battery_remaining  # %
            # ArduPilot sends current in cA, so divide by 100 for Amps. -1 if not available.
            drone_state['battery_current'] = msg.current_battery / 100.0 if msg.current_battery != -1 else -1.0 
            # drone_state['system_status'] = msg.onboard_control_sensors_present # This is a bitmask of sensors present
            # It's better to use msg.onboard_control_sensors_health for EKF status, etc.
            # drone_state['ekf_status_report'] = get_ekf_status_report(msg.onboard_control_sensors_health)
            changed_in_this_handler = True

        elif msg_type == 'GPS_RAW_INT':
            drone_state['gps_fix_type'] = msg.fix_type
            drone_state['satellites_visible'] = msg.satellites_visible
            drone_state['hdop'] = msg.eph / 100.0 if msg.eph != 65535 else 99.99 # eph is HDOP
            changed_in_this_handler = True

        elif msg_type == 'HOME_POSITION':
            drone_state['home_lat'] = msg.latitude / 1e7
            drone_state['home_lon'] = msg.longitude / 1e7
            home_position_requested = True # Mark as received
            emit_status_message("Home position received.", "info")
            changed_in_this_handler = True
        
        elif msg_type == 'STATUSTEXT':
            message_text = "".join(chr(c) for c in msg.text if c != 0) # Convert to string and remove null terminators
            severity_enum = mavutil.mavlink.enums.get('MAV_SEVERITY', {})
            severity = severity_enum.get(msg.severity, mavutil.mavlink.MAV_SEVERITY_INFO).name.replace('MAV_SEVERITY_', '')
            print(f"STATUSTEXT [{severity}]: {message_text}")
            if msg.severity <= mavutil.mavlink.MAV_SEVERITY_WARNING: # WARNING, ERROR, CRITICAL, ALERT, EMERGENCY
                 log_level = "warning" if msg.severity == mavutil.mavlink.MAV_SEVERITY_WARNING else "error"
                 emit_status_message(f"Drone: {message_text}", log_level)
            # STATUSTEXT usually doesn't change core drone_state variables directly, so no changed_in_this_handler

        # elif msg_type == 'EKF_STATUS_REPORT': # ArduPilot specific
        #     drone_state['ekf_flags'] = msg.flags
        #     drone_state['ekf_status_report'] = get_ekf_status_report(msg.flags) # Assuming get_ekf_status_report expects EKF flags directly
        #     changed_in_this_handler = True

        # Add more MAVLink message types to process as needed

        if changed_in_this_handler:
            drone_state_changed = True # Set the global flag if any state was changed by this handler

def connect_mavlink():
    """Attempts to establish MAVLink connection TO the drone via UDP."""
    global master, drone_state, data_streams_requested, home_position_requested, last_heartbeat_time
    
    connection_string = f"tcp:{current_mavlink_target_ip}:{current_mavlink_target_port}"
    log_message(f"MAVLink: Attempting connection to {connection_string}...", "INFO")

    try:
        # Attempt to establish connection
        # Aligning with d892ba4: remove explicit source_component and dialect
        temp_master = mavutil.mavlink_connection(
            connection_string, 
            autoreconnect=True, 
            source_system=255, # Standard GCS system ID, was also in d892ba4 implicitly or explicitly
            # source_component=190, # REMOVED - Let pymavlink default or drone decide
            baud=115200, # Not strictly for TCP, but doesn't hurt. Was commented out in d892ba4 snippet.
            # dialect=MAVLINK_DIALECT # REMOVED - Let pymavlink auto-detect/default
        )
        
        # Wait for the first HEARTBEAT message to confirm connection
        hb_msg = None
        for _ in range(HEARTBEAT_WAIT_ITERATIONS):
            if mavlink_thread_stop_event.is_set():
                log_message("MAVLink: Stop event received while waiting for heartbeat.", "DEBUG")
                raise gevent.GreenletExit("Stop event received")
            hb_msg = temp_master.wait_heartbeat(timeout=HEARTBEAT_WAIT_PER_ITERATION_S)
            if hb_msg:
                break
            log_message(f"MAVLink: Heartbeat wait iteration for {connection_string}, retrying...", "DEBUG")
        
        if not hb_msg:
            log_message(f"MAVLink: No heartbeat from {connection_string} after {HEARTBEAT_WAIT_ITERATIONS} attempts.", "ERROR")
            raise ConnectionError("Failed to receive heartbeat")
        
        # --- Successfully connected and got heartbeat ---
        master = temp_master
        drone_state['connected'] = True
        drone_state['mavlink_target_ip'] = current_mavlink_target_ip
        drone_state['mavlink_target_port'] = current_mavlink_target_port
        drone_state_changed = True
        data_streams_requested = False
        home_position_requested = False
        log_message(f"MAVLink: Connection established to {connection_string}", "SUCCESS")
        emit_status_message(f"Connected to MAVLink at {connection_string}", "success")
        request_data_streams()
        # request_fence_points() # Commented out
        # request_mission_items() # Commented out
    except Exception as e:
        print(f"MAVLink connection to {connection_string} failed: {e}")
        master = None
        drone_state['connected'] = False
        emit_status_message(f"Failed to connect to MAVLink at {connection_string}. Retrying...", "error")
        print(f"MAVLink disconnected or connection failed. Retrying in {RECONNECTION_ATTEMPT_DELAY} seconds...")
        time.sleep(RECONNECTION_ATTEMPT_DELAY) # Use imported constant

def request_data_streams(req_rate_hz=REQUEST_STREAM_RATE_HZ):
    """Requests necessary data streams from the flight controller using MAV_CMD_SET_MESSAGE_INTERVAL."""
    global data_streams_requested, master, home_position_requested
    
    if not master or not drone_state.get("connected", False) or master.target_system == 0:
        log_message("Cannot request data streams: MAVLink not connected or target system unknown.", "WARNING")
        return

    target_sys = master.target_system
    target_comp = master.target_component if master.target_component != 0 else 1 
    log_message(f"Requesting all data streams via SET_MESSAGE_INTERVAL from SYSID {target_sys} COMPID {target_comp}", "INFO")

    streams_to_request = {
        mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT: 1,
        mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS: 1,
        mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: req_rate_hz,
        mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE: req_rate_hz * 2 if req_rate_hz * 2 <= 50 else 50,
        mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD: req_rate_hz,
        mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT: 1,
        mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION: 0, # Request once
        mavutil.mavlink.MAVLINK_MSG_ID_STATUSTEXT: 1,
    }

    try:
        for msg_id, rate_hz_val in streams_to_request.items():
            if msg_id == mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION and home_position_requested and rate_hz_val == 0:
                log_message(f"Skipping HOME_POSITION (MsgID {msg_id}) request as it's already received.", "DEBUG")
                continue

            interval_us = int(1e6 / rate_hz_val) if rate_hz_val > 0 else 0
            # For MAVLINK_MSG_ID_HOME_POSITION with rate_hz_val == 0, interval_us becomes 0, which is correct for one-shot request.
            # If rate_hz_val < 0 (to stop stream), interval_us should be -1. We are not using this here.
            
            msg_name = mavutil.mavlink.enums['MAVLINK_MSG'][msg_id].name if msg_id in mavutil.mavlink.enums['MAVLINK_MSG'] else f'MsgID {msg_id}'
            log_message(f"Req: {msg_name} at {rate_hz_val}Hz (Interval: {interval_us}us)", "INFO")
            
            master.mav.command_long_send(
                target_sys, 
                target_comp, 
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 
                0,                      # Confirmation
                msg_id,                 # param1: Message ID to control
                interval_us,            # param2: Interval in microseconds (-1 to disable, 0 to request once/default rate)
                0,0,0,0,0               # Unused params
            )
            gevent.sleep(0.05) # Small delay between requests
        
        data_streams_requested = True
        log_message("All data stream requests sent.", "INFO")

    except Exception as req_err: 
        log_message(f"Error requesting data streams: {req_err}", "ERROR")
        data_streams_requested = False

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
        if master and result_name == 'UNKNOWN' and len(master.mav.command_ack_queue) > 0:
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
    elif result_name == 'UNKNOWN' and explanation == "Command response UNKNOWN - vehicle might be using different protocol":
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
    """Background thread for MAVLink connection, message receiving, and reconnection logic."""
    global master, mavlink_thread_stop_event, drone_state, drone_state_changed, telemetry_loop_active
    global current_mavlink_target_ip, current_mavlink_target_port, data_streams_requested, home_position_requested

    log_message("MAVLink receive loop starting...")

    while not mavlink_thread_stop_event.is_set():
        connection_successful = False
        temp_master_conn = None # Use a temporary var for the connection in this loop iteration

        with drone_state_lock:
            if drone_state.get('connected', False):
                drone_state['connected'] = False
                drone_state_changed = True

        try:
            with mavlink_connection_lock:
                target_ip = current_mavlink_target_ip
                target_port = current_mavlink_target_port
            conn_str = f"tcp:{target_ip}:{target_port}"
            log_message(f"MAVLink: Attempting connection to {conn_str}...")

            try:
                with gevent.Timeout(CONNECTION_ATTEMPT_TIMEOUT_S):
                    temp_master_conn = mavutil.mavlink_connection(
                        conn_str, baud=DRONE_BAUD_RATE, source_system=MAVLINK_SOURCE_SYSTEM,
                        autoreconnect=False, dialect=MAVLINK_DIALECT
                    )
            except gevent.Timeout:
                log_message(f"MAVLink: Connection to {conn_str} timed out after {CONNECTION_ATTEMPT_TIMEOUT_S}s.", "WARNING")
                raise ConnectionError("Connection attempt timed out")
            except (socket.error, OSError) as se:
                log_message(f"MAVLink: Socket/OS error connecting to {conn_str}: {se}", "ERROR")
                raise ConnectionError(f"Socket/OS error: {se}") from se

            if mavlink_thread_stop_event.is_set(): break
            if not temp_master_conn: raise ConnectionError("temp_master_conn is None after attempt.")

            log_message(f"MAVLink: Waiting for heartbeat from {conn_str}...")
            hb_msg = None
            for _ in range(HEARTBEAT_WAIT_ITERATIONS):
                if mavlink_thread_stop_event.is_set():
                    log_message("MAVLink: Stop event received while waiting for heartbeat.", "DEBUG")
                    raise gevent.GreenletExit("Stop event received")
                hb_msg = temp_master_conn.wait_heartbeat(timeout=HEARTBEAT_WAIT_PER_ITERATION_S)
                if hb_msg:
                    break
                log_message(f"MAVLink: Heartbeat wait iteration for {conn_str}, retrying...", "DEBUG")
            
            if mavlink_thread_stop_event.is_set() or not hb_msg:
                if temp_master_conn: temp_master_conn.close()
                if not hb_msg and not mavlink_thread_stop_event.is_set():
                    log_message(f"MAVLink: No heartbeat from {conn_str} after {HEARTBEAT_WAIT_ITERATIONS} attempts.", "ERROR")
                # This will proceed to the 'finally' block, then to the reconnect delay logic
                # If stop event is set, it will break from outer while loop after 'finally'
                # If only heartbeat failed, it will retry after delay.
                if not hb_msg: raise ConnectionError("Failed to receive heartbeat")
                else: break # Stop event was set

            # --- Successfully connected and got heartbeat ---
            with mavlink_connection_lock:
                master = temp_master_conn # Assign to global master under lock
                drone_state['connected'] = True
                drone_state['mavlink_target_ip'] = target_ip
                drone_state['mavlink_target_port'] = target_port
                drone_state_changed = True
                data_streams_requested = False
                home_position_requested = False
                log_message(f"MAVLink: Connection established to {conn_str}", "SUCCESS")
                emit_status_message(f"Connected to MAVLink at {conn_str}", "success")
                request_data_streams()
                # request_fence_points() # Commented out
                # request_mission_items() # Commented out
            connection_successful = True

            # Main message processing loop
            log_message("MAVLink: Entering message processing loop.")
            telemetry_loop_active = True # Signal that the main loop is active

            while not mavlink_thread_stop_event.is_set():
                # Check for stop event before blocking call
                if mavlink_thread_stop_event.is_set():
                    log_message("MAVLink: Stop event detected before recv_match.", "DEBUG")
                    break

                msg = master.recv_match(blocking=False, timeout=0.01) # Non-blocking with short timeout

                if msg:
                    # Remove direct logging from the loop; handling and specific logging (like for HEARTBEAT)
                    # will occur in handle_mavlink_message and its sub-functions.
                    handle_mavlink_message(msg)
                else:
                    # This will log if no message is received in the 0.01s timeout
                    # log_message("LOOP: master.recv_match returned None", "TRACE") # Potentially too verbose, use TRACE or DEBUG
                    # It's normal for recv_match to return None with timeout
                    # Yield control to allow other greenlets to run, crucial for responsiveness.
                    gevent.sleep(0.01)

                # Explicitly check stop event again after potential processing or sleep
                if mavlink_thread_stop_event.is_set():
                    log_message("MAVLink: Stop event detected after recv_match/sleep.", "DEBUG")
                    break

            log_message("MAVLink: Exited message processing loop.", "DEBUG")

        except gevent.Timeout as t:
            log_message(f"MAVLink: Timeout in main loop: {t}", "WARNING")
        except ConnectionError as ce: # Catch our specific ConnectionErrors (timeout, no heartbeat, socket error)
            log_message(f"MAVLink: ConnectionError in main loop: {ce}", "ERROR")
            # Ensure drone_state reflects disconnection if a connection attempt fails here
            with drone_state_lock:
                if drone_state.get('connected', True): # If it was true or not set
                    drone_state['connected'] = False
                    drone_state_changed = True
            emit_status_message(f"Failed to connect to MAVLink: {ce}", "error")
            # Fall through to the reconnection delay logic
        except Exception as e_outer:
            log_message(f"MAVLink: Unhandled exception in receive loop: {e_outer}\n{traceback.format_exc()}", "CRITICAL")
            with drone_state_lock:
                drone_state['connected'] = False
                drone_state_changed = True
            emit_status_message(f"MAVLink system error: {e_outer}", "error")
            # Fall through to the reconnection delay logic
        
        finally:
            # Cleanup for this attempt if temp_master_conn was created and is not the current master
            with mavlink_connection_lock:
                if temp_master_conn and (master is None or id(master) != id(temp_master_conn)):
                    log_message(f"MAVLink: Closing temporary connection object (ID: {id(temp_master_conn)}).", "DEBUG")
                    temp_master_conn.close()
                # If 'master' is set and connection_successful is false, means the established connection died.
                if master and not connection_successful:
                    log_message(f"MAVLink: Closing master connection (ID: {id(master)}) due to loop exit without success.", "DEBUG")
                    master.close()
                    master = None # Clear global master
                    with drone_state_lock:
                        if drone_state.get('connected', False):
                             drone_state['connected'] = False
                             drone_state_changed = True
            if telemetry_loop_active and not connection_successful:
                log_message("MAVLink: Setting telemetry_loop_active to False as connection lost/failed.")
                telemetry_loop_active = False
        # End of main try/except/finally for one connection attempt cycle

        # --- Reconnection Delay Logic (if not stopping) ---
        if not mavlink_thread_stop_event.is_set():
            if not connection_successful: # Only log retry if connection failed
                 log_message(f"MAVLink: Disconnected or connection failed. Retrying in {RECONNECTION_ATTEMPT_DELAY}s...")
                 emit_status_message(f"MAVLink connection lost. Retrying...", "warning")
            
            for _ in range(RECONNECTION_ATTEMPT_DELAY):
                if mavlink_thread_stop_event.is_set():
                    log_message("MAVLink: Stop event during reconnection delay. Exiting loop.")
                    break
                gevent.sleep(1)
            
            if mavlink_thread_stop_event.is_set():
                break # Break from the main while loop
        else:
            log_message("MAVLink: Stop event detected after connection attempt cycle. Terminating loop.")
            break # Ensure exit if stop event was set
    
    # Final cleanup before thread exits completely
    with mavlink_connection_lock:
        if master:
            log_message(f"MAVLink: Final cleanup, closing master connection (ID: {id(master)}). Thread exiting.")
            master.close()
            master = None
    with drone_state_lock:
        if drone_state.get('connected', False):
            drone_state['connected'] = False
            drone_state_changed = True
    telemetry_loop_active = False
    log_message("MAVLink receive loop terminated.")

# --- Telemetry Update Thread (for SocketIO) ---
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
    print('Client connected')
    # Send initial state immediately to the newly connected client
    with mavlink_connection_lock:
        current_state_copy = drone_state.copy() # Ensure thread-safe copy
        # The drone_state already uses current_mavlink_target_ip/port, 
        # but we explicitly set it here from globals for clarity and to ensure it's the most recent if accessed before drone_state is updated by mav_thread
        current_state_copy['mavlink_target_ip'] = current_mavlink_target_ip
        current_state_copy['mavlink_target_port'] = current_mavlink_target_port
    socketio.emit('telemetry_update', current_state_copy, room=request.sid)
    emit_status_message("Web client connected.", "info", room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('update_mavlink_target')
def handle_update_mavlink_target(data):
    global current_mavlink_target_ip, current_mavlink_target_port, drone_state, master, mav_thread, mavlink_thread_stop_event, mavlink_connection_lock

    new_ip = data.get('ip')
    new_port_str = data.get('port')

    if not new_ip or not new_port_str:
        emit_status_message("Invalid IP or Port received for MAVLink target update.", "error")
        return
    
    try:
        new_port = int(new_port_str)
        if not (1 <= new_port <= 65535):
            raise ValueError("Port out of range")
    except ValueError:
        emit_status_message(f"Invalid Port number: '{new_port_str}'. Must be an integer between 1-65535.", "error")
        return

    print(f"Received MAVLink target update request: IP={new_ip}, Port={new_port}")
    emit_status_message(f"Switching MAVLink target to {new_ip}:{new_port}...", "info")

    # Signal current MAVLink thread to stop
    mavlink_thread_stop_event.set()

    with mavlink_connection_lock: # Ensure exclusive access
        if mav_thread and mav_thread.is_alive():
            print("Stopping current MAVLink thread...")
            # The mavlink_thread itself handles closing 'master' when stop_event is set.
            # We just need to join it.
            mav_thread.join(timeout=10) # Wait for the thread to terminate (10s timeout)
            if mav_thread.is_alive():
                print("ERROR: MAVLink thread did not terminate in time!")
                emit_status_message("Error: Could not stop existing MAVLink connection. Please restart the server.", "error")
                # Not clearing stop_event here, as the old thread might still be lingering
                return # Prevent starting a new thread if old one is stuck
            else:
                print("Current MAVLink thread stopped.")
        else:
            print("No active MAVLink thread to stop or thread already stopped.")

        # Update target and drone_state (under lock)
        current_mavlink_target_ip = new_ip
        current_mavlink_target_port = new_port
        drone_state['mavlink_target_ip'] = current_mavlink_target_ip
        drone_state['mavlink_target_port'] = current_mavlink_target_port
        drone_state['connected'] = False # New target, not yet connected
        # No need to close master here, mavlink_thread's cleanup should handle it when stop_event is set.
        master = None # Ensure master is None before new thread starts
        
    # Emit an immediate update to the UI to show the new target and disconnected status
    socketio.emit('telemetry_update', drone_state.copy())
    emit_status_message(f"MAVLink target updated to {new_ip}:{new_port}. Attempting connection...", "info")

    # Clear the stop event and start a new MAVLink thread
    mavlink_thread_stop_event.clear()
    
    mav_thread = threading.Thread(target=mavlink_receive_loop, daemon=True) # Corrected function name
    mav_thread.start()
    print(f"New MAVLink thread started for {current_mavlink_target_ip}:{current_mavlink_target_port}")

@socketio.on('command')
def handle_command(data):
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
                
            if not master:
                raise Exception("No MAVLink connection")
            
            # Set the mode to GUIDED
            guided_mode = AP_CUSTOM_MODES['GUIDED']
            print(f"Setting mode to GUIDED (Custom Mode: {guided_mode}) using direct method")
            log_command_action("SET_MODE", f"Mode: GUIDED ({guided_mode})", "Setting mode via direct command", "INFO")
            
            master.mav.set_mode_send(
                master.target_system,
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
            master.mav.set_position_target_global_int_send(
                0,       # time_boot_ms (not used)
                master.target_system,  # target system
                master.target_component,  # target component
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

def stop_mavlink_thread():
    """Stops the MAVLink communication thread if it's running."""
    global mav_thread, mavlink_thread_stop_event, master, telemetry_loop_active

    if mav_thread and mav_thread.is_alive():
        log_message("Stopping current MAVLink thread...")
        mavlink_thread_stop_event.set()
        gevent.sleep(0)  # Yield to allow the mavlink_thread to process the event
        mav_thread.join(timeout=MAVLINK_THREAD_STOP_TIMEOUT_S) # Use the constant

        if mav_thread.is_alive():
            log_message("ERROR: MAVLink thread did not terminate in time!", "ERROR")
            # The emit_status_message is handled by the caller (handle_update_mavlink_target)
            return False
        log_message("MAVLink thread stopped successfully.")
    else:
        log_message("MAVLink thread already stopped or not initialized.", "DEBUG")

    mav_thread = None
    mavlink_thread_stop_event.clear()  # Clear for the next thread instance
    telemetry_loop_active = False
    
    # Ensure master connection is closed and state reflects disconnection
    with mavlink_connection_lock:
        if master:
            log_message("stop_mavlink_thread: Closing master connection.", "DEBUG")
            master.close()
            master = None
    with drone_state_lock:
        if drone_state.get('connected', False) or drone_state.get('mavlink_target_ip') is not None:
            drone_state['connected'] = False
            # drone_state['mavlink_target_ip'] = None # Cleared by new connection attempt or UI
            # drone_state['mavlink_target_port'] = None
            drone_state_changed = True
    return True

if __name__ == '__main__':
    print(f"Starting server on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    # Start the background threads
    mav_thread = threading.Thread(target=mavlink_receive_loop, daemon=True) # Corrected function name
    mav_thread.start()

    print("Starting periodic telemetry update thread...")
    telemetry_update_thread = gevent.spawn(periodic_telemetry_update)
    socketio.run(app, 
                host=WEB_SERVER_HOST, 
                port=WEB_SERVER_PORT, 
                debug=True,
                use_reloader=False)  # Disable reloader to prevent duplicate threads

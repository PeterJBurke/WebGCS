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
import atexit
import logging # Cascade Added import

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
    MAVLINK_DIALECT,              # Added MAVLink dialect
    RECONNECTION_ATTEMPT_DELAY,   # Added import
    DEBUG,                        # Added import
    DRONE_BAUD_RATE,              # Added import
    MAVLINK_SOURCE_SYSTEM,        # Added import
    REQUEST_STREAM_RATE_HZ
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

# Create a reverse map for ArduPilot custom modes for easier lookup by number
ARDUPILOT_MODE_NAME_MAP = {v: k for k, v in AP_CUSTOM_MODES.items()} if AP_CUSTOM_MODES else {}

# --- Logging Configuration ---
# Cascade Added: Configure standard logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all levels
    format='%(asctime)s [%(levelname)-8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler("webgcs_debug.log", mode='w')] # 'w' overwrites log on each start
)

# --- Logging Helper (using standard logging) ---
def log_message(message, level="INFO"):
    """Logs a message using the standard logging module."""
    level = level.upper() # Ensure level is uppercase for logger methods
    if level == "DEBUG":
        logging.debug(message)
    elif level == "WARNING":
        logging.warning(message)
    elif level == "ERROR":
        logging.error(message)
    elif level == "CRITICAL":
        logging.critical(message)
    else: # Default to INFO
        logging.info(message)

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

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template("index.html", version="v2.63-Desktop-TCP-AckEkf")
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

def log_heartbeat_details(msg):
    global drone_state # For reading
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")
    sysid = msg.get_srcSystem()
    compid = msg.get_srcComponent()

    current_sys_state = drone_state.get(sysid, {}) 
    mode_to_log = current_sys_state.get('mode', 'NOT_SET_IN_STATE')
    armed_to_log = current_sys_state.get('armed', False) 
    
    armed_str = "ARMED" if armed_to_log else "DISARMED"
    type_str = mavutil.mavlink.enums['MAV_TYPE'][msg.type].name if msg.type in mavutil.mavlink.enums['MAV_TYPE'] else str(msg.type)
    autopilot_str = mavutil.mavlink.enums['MAV_AUTOPILOT'][msg.autopilot].name if msg.autopilot in mavutil.mavlink.enums['MAV_AUTOPILOT'] else str(msg.autopilot)
    status_str = mavutil.mavlink.enums['MAV_STATE'][msg.system_status].name if msg.system_status in mavutil.mavlink.enums['MAV_STATE'] else str(msg.system_status)
    
    separator = "=" * 80 
    heartbeat_details = (
        f"[{timestamp_str}] HEARTBEAT_DETAILS (for SYSID {sysid})\n"
        f"  SYS: {sysid}\n"
        f"  COMP: {compid}\n"
        f"  Type: {type_str}\n"
        f"  Autopilot: {autopilot_str}\n"
        f"  Mode (from drone_state[{sysid}]): {mode_to_log}\n" 
        f"  Armed (from drone_state[{sysid}]): {armed_str}\n" 
        f"  Status (from msg): {status_str}\n"
        f"  MAVLink Version: {msg.mavlink_version}"
    )
    print(heartbeat_details)
    print(separator)

def handle_heartbeat(msg): # master will be accessed as a global
    """Handles incoming HEARTBEAT messages, updates drone_state, and logs details."""
    global drone_state, master # Ensure master is accessible

    sysid = msg.get_srcSystem()

    if sysid not in drone_state:
        drone_state[sysid] = {
            'mode': 'INITIALIZING',
            'armed': False
        }
    
    new_mode_num = msg.custom_mode
    autopilot_type = msg.autopilot
    is_armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

    new_mode_str = f"ModeNum_{new_mode_num}" # Default if not found

    if autopilot_type == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA:
        new_mode_str = ARDUPILOT_MODE_NAME_MAP.get(new_mode_num, f"Unknown_AP_Mode_{new_mode_num}")
    elif autopilot_type == mavutil.mavlink.MAV_AUTOPILOT_PX4:
        # Placeholder for PX4 main modes if needed - PX4 uses base_mode primarily for standard modes
        # For PX4 custom modes, MAV_MODE_FLAG_CUSTOM_MODE_ENABLED in base_mode is checked,
        # and custom_mode holds a PX4-specific value.
        # This example focuses on ArduPilot custom modes for now.
        # We'd need a PX4 specific custom_mode map if we were to decode them.
        # Fallback to MAVLink standard mode mapping if custom bit not set, or just use number.

        # Attempt to get standard mode string from base_mode bits (excluding custom flag)
        standard_mode_bits = msg.base_mode & ~mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
        standard_mode_str = mavutil.mode_string_v10(standard_mode_bits) # Tries to map standard bits
        if standard_mode_str and standard_mode_str != "MAV_MODE_MANUAL_ARMED": # mode_string_v10 can be vague
            new_mode_str = standard_mode_str
        
        if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED:
            new_mode_str = f"PX4_Custom({new_mode_num})" # Simple representation for PX4 custom mode
        # If no better string found, it remains ModeNum_X or the basic standard_mode_str

    else: # Other autopilots or unknown
        # Generic attempt to map standard modes from base_mode
        standard_mode_bits = msg.base_mode & ~mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
        standard_mode_str = mavutil.mode_string_v10(standard_mode_bits)
        if standard_mode_str and standard_mode_str != "MAV_MODE_MANUAL_ARMED":
            new_mode_str = standard_mode_str
        else:
            new_mode_str = f"UnknownAutopilot_ModeNum_{new_mode_num}"

    # Update drone_state
    state_changed_loc = False
    if drone_state[sysid].get('mode') != new_mode_str:
        drone_state[sysid]['mode'] = new_mode_str
        state_changed_loc = True

    if drone_state[sysid].get('armed') != is_armed:
        drone_state[sysid]['armed'] = is_armed
        state_changed_loc = True

    drone_state[sysid].update({
        'last_heartbeat': time.time(),
        'autopilot': msg.autopilot,
        'type': msg.type,
        'system_status': msg.system_status,
        'mavlink_version': msg.mavlink_version,
        'base_mode': msg.base_mode, 
        'custom_mode_raw': new_mode_num 
    })

    # If this heartbeat is from the primary target system, update the top-level state
    if master and hasattr(master, 'target_system') and sysid == master.target_system:
        log_message(f"HEARTBEAT_CHECK_TOP_LEVEL: Checking for top-level update from SYSID {sysid}. State changed locally: {state_changed_loc}", level="INFO") # Cascade Changed Log
        # Update the top-level drone_state based on changes detected for this system ID
        if state_changed_loc: 
            current_primary_target_state = drone_state[sysid]
            drone_state.update({ 
                'mode': current_primary_target_state.get('mode'),
                'armed': current_primary_target_state.get('armed'),
                'last_heartbeat': current_primary_target_state.get('last_heartbeat'),
                'autopilot': current_primary_target_state.get('autopilot'),
                'type': current_primary_target_state.get('type'),
                'system_status': current_primary_target_state.get('system_status'),
                'mavlink_version': current_primary_target_state.get('mavlink_version'),
                'base_mode': current_primary_target_state.get('base_mode'),
                'custom_mode_raw': current_primary_target_state.get('custom_mode_raw')
                # Note: 'connected' status is handled elsewhere (e.g., connect/disconnect logic)
            })
            log_message(f"HEARTBEAT_TOP_LEVEL_UPDATE: Updated top-level drone_state from SYSID {sysid}", level="DEBUG") # Cascade Changed Log

    # Log if any change occurred for this specific sysid
    if state_changed_loc:
        log_message(f"HEARTBEAT_STATE_CHANGE: SYSID {sysid}: Mode changed to '{drone_state[sysid]['mode']}', Armed changed to: {drone_state[sysid]['armed']}", level="INFO") # Cascade Changed Log
    
    log_message(f"HEARTBEAT_OUT: drone_state[{sysid}] is now: Mode='{drone_state[sysid]['mode']}', Armed={drone_state[sysid]['armed']}", level="DEBUG") # Cascade Changed Log

    log_heartbeat_details(msg)

    # Emit an event to the frontend when a heartbeat is processed for any system
    socketio.emit('heartbeat_received', {'sysid': sysid})

def handle_mavlink_message(msg):
    """Processes various MAVLink messages and updates drone_state."""
    # print(f"--- ENTERED handle_mavlink_message with msg type: {msg.get_type()} (ID: {msg.get_msgId()}) ---") # <-- REMOVED PRINT
    global drone_state, drone_state_changed, data_streams_requested, home_position_requested
    msg_type = msg.get_type()

    # --- Add Debug Log Here ---
    msg_id = msg.get_msgId()
    # msg_type = msg.get_type() # Redundant, already assigned above
    log_message(f"Received MAVLink Msg: Type={msg_type}, ID={msg_id}", level="DEBUG") # Cascade Changed Log Level
    # --- End Debug Log ---

    if msg_type == 'HEARTBEAT':
        handle_heartbeat(msg) # MODIFIED CALL to new function
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
            if isinstance(msg.text, bytes):
                try:
                    # Decode bytes, stopping at the first null terminator
                    message_text = msg.text.split(b'\x00', 1)[0].decode('utf-8', errors='replace')
                except Exception as e:
                    message_text = f"Error decoding STATUSTEXT (bytes): {e}"
                    log_message(f"STATUSTEXT decode (bytes) error: {e} on data: {msg.text!r}", "ERROR")
            elif isinstance(msg.text, str):
                # Already a string, stop at the first null terminator
                message_text = msg.text.split('\x00', 1)[0]
            else:
                message_text = "Unknown STATUSTEXT format"
                log_message(f"STATUSTEXT has unexpected msg.text type: {type(msg.text)} content: {msg.text!r}", "WARNING")
            
            severity_enum = mavutil.mavlink.enums.get('MAV_SEVERITY', {})
            severity = severity_enum.get(msg.severity, mavutil.mavlink.MAV_SEVERITY_INFO).name.replace('MAV_SEVERITY_', '')
            log_message(f"STATUSTEXT [{severity}]: {message_text}", level=severity) # Cascade Changed Print to Log
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
        
        # Removed request_data_streams() call
    except Exception as e:
        print(f"MAVLink connection to {connection_string} failed: {e}")
        master = None
        drone_state['connected'] = False
        emit_status_message(f"Failed to connect to MAVLink at {connection_string}. Retrying...", "error")
        print(f"MAVLink disconnected or connection failed. Retrying in {RECONNECTION_ATTEMPT_DELAY} seconds...")
        time.sleep(RECONNECTION_ATTEMPT_DELAY) # Use imported constant

def send_mavlink_command(command, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0, confirmation=0, target_system=None, target_component=None):
    """
    Sends a MAVLink COMMAND_LONG message.
    Returns (True, "Command sent successfully") or (False, "Error message").
    """
    global master, drone_state, app # Added app for app.logger

    if not drone_state.get("connected") or not master:
        log_command_action(f"CMD_SEND_FAIL (No Connection)", f"CmdID:{command}", "MAVLink connection is not active.", "ERROR")
        return False, "MAVLink connection is not active."

    effective_target_system = target_system if target_system is not None else drone_state.get("system_id", 1)
    effective_target_component = target_component if target_component is not None else drone_state.get("component_id", 1)
    
    if effective_target_system == 0:
        log_command_action(f"CMD_SEND_FAIL (Invalid Target)", f"CmdID:{command}", "Target system ID is 0. Refusing to broadcast.", "ERROR")
        return False, "Target system ID is 0. Refusing to broadcast."

    try:
        log_command_action(f"SENDING_CMD", f"CmdID:{command}, P:[{p1:.2f},{p2:.2f},{p3:.2f},{p4:.2f},{p5:.2f},{p6:.2f},{p7:.2f}] TargetSYS:{effective_target_system} TargetCOMP:{effective_target_component}", "Attempting to send command.", "DEBUG")
        master.mav.command_long_send(
            effective_target_system,       # target_system
            effective_target_component,    # target_component
            command,                       # command ID (e.g., mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM)
            confirmation,                  # confirmation
            p1, p2, p3, p4, p5, p6, p7     # params
        )
        log_command_action(f"CMD_SENT_OK", f"CmdID:{command}", "command_long_send executed.", "INFO")
        return True, "Command sent successfully."
    except Exception as e:
        error_msg = f"Failed to send MAVLink command {command}: {str(e)}"
        log_command_action(f"CMD_SEND_ERROR", f"CmdID:{command}", error_msg, "ERROR")
        app.logger.error(error_msg)
        return False, error_msg

def process_command_ack(msg):
    """Process and log COMMAND_ACK messages with enhanced details"""
    command_id = msg.command
    result = msg.result
    
    # Get command name for logging
    cmd_name = mavutil.mavlink.enums['MAV_CMD'][command_id].name if command_id in mavutil.mavlink.enums['MAV_CMD'] else f'UNKNOWN_CMD_ID_{command_id}'
    
    # Get result name
    result_text = MAV_RESULT_STR.get(result, 'UNKNOWN_RESULT')
    
    # Determine log level and refine explanation
    log_level = "INFO"
    explanation = f"Command {cmd_name} ({command_id}) {result_text}"

    if result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
        explanation = f"Command {cmd_name} ({command_id}) ACCEPTED by vehicle"
    elif result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
        log_level = "WARNING" # Keep as WARNING for temporary rejections
        explanation = f"Command {cmd_name} ({command_id}) TEMPORARILY REJECTED by vehicle (may be in wrong state)"
    elif result == mavutil.mavlink.MAV_RESULT_DENIED:
        log_level = "ERROR"
        explanation = f"Command {cmd_name} ({command_id}) DENIED by vehicle"
    else: # Other non-accepted results
        log_level = "ERROR"
        explanation = f"Command {cmd_name} ({command_id}) {result_text} (Result Code: {result})"

    # Skip logging MAV_CMD_REQUEST_MESSAGE commands with specific UNKNOWN results if desired (current logic does this)
    if command_id == mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE and result_text == 'UNKNOWN_RESULT': # Check against updated result_text
        if command_id in pending_commands:
            del pending_commands[command_id]
        return
    
    # Log with detailed explanation
    log_message(explanation, level=log_level) # Use the derived log_level
    
    # Update last_command_ack (This part seems to be missing from the snippet but should be present)
    # Ensure this part aligns with your existing logic for updating drone_state and emitting to UI
    global last_command_ack, drone_state_changed, drone_state_lock
    with drone_state_lock:
        last_command_ack = {
            'command': command_id,
            'command_name': cmd_name,
            'result': result,
            'result_text': result_text,
            'timestamp': time.time()
        }
        drone_state_changed = True # Notify telemetry loop

    # Emit command result to UI
    socketio.emit('command_result', {
        'command_id': command_id,
        'command_name': cmd_name,
        'result': result,
        'result_text': result_text,
        'success': result == mavutil.mavlink.MAV_RESULT_ACCEPTED
    })
    log_message(f"ACK_PROCESS: Finished processing ACK for {cmd_name} ({command_id})", level="DEBUG") # Cascade Added Log

    # Remove from pending commands if it was tracked
    if command_id in pending_commands:
        del pending_commands[command_id]

def mavlink_receive_loop():
    """Background thread for MAVLink connection, message receiving, and reconnection logic."""
    global master, mavlink_thread_stop_event, drone_state, drone_state_changed, telemetry_loop_active
    global current_mavlink_target_ip, current_mavlink_target_port, data_streams_requested, home_position_requested

    log_message("MAVLink receive loop starting...")

    while not mavlink_thread_stop_event.is_set():
        log_message(f"Thread Status: Alive. Current Target: {current_mavlink_target_ip}:{current_mavlink_target_port}. Connected: {drone_state.get('connected', False)}. Thread ID: {threading.get_ident()}", "INFO")
        time.sleep(1) # Log status every second
        connection_successful = False
        temp_master_conn = None # Use a temporary var for the connection in this loop iteration

        with drone_state_lock:
            if drone_state.get('connected', False):
                drone_state['connected'] = False
                drone_state_changed = True

        try:
            with mavlink_connection_lock: # Ensure exclusive access
                target_ip = current_mavlink_target_ip
                target_port = current_mavlink_target_port
            conn_str = f"tcp:{target_ip}:{target_port}"
            log_message(f"MAVLink: Attempting connection to {conn_str}...")

            try:
                log_message("MAVLink: Calling mavutil.mavlink_connection...", "DEBUG") 
                temp_master_conn = mavutil.mavlink_connection(
                    conn_str, baud=DRONE_BAUD_RATE,
                    autoreconnect=False 
                )
                log_message("MAVLink: mavutil.mavlink_connection call finished.", "DEBUG") 
            except gevent.Timeout:
                log_message(f"MAVLink: Connection to {conn_str} timed out after {CONNECTION_ATTEMPT_TIMEOUT_S}s.", "WARNING")
                raise ConnectionError("Connection attempt timed out")
            except (socket.error, OSError) as se:
                log_message(f"MAVLink: Socket/OS error connecting to {conn_str}: {se}", "ERROR")
                raise ConnectionError(f"Socket/OS error: {se}") from se

            if mavlink_thread_stop_event.is_set():
                break
            if not temp_master_conn:
                log_message("MAVLink: temp_master_conn is None after connection attempt block.", "ERROR")
                raise ConnectionError("temp_master_conn is None after attempt.")

            log_message(f"MAVLink: Waiting for heartbeat from {conn_str}...")
            hb_msg = None
            for i in range(HEARTBEAT_WAIT_ITERATIONS):
                log_message(f"MAVLink: Heartbeat wait iteration {i+1}/{HEARTBEAT_WAIT_ITERATIONS} starting...", "DEBUG") 
                if mavlink_thread_stop_event.is_set():
                    log_message("MAVLink: Stop event received while waiting for heartbeat.", "DEBUG")
                    raise gevent.GreenletExit("Stop event received")
                hb_msg = temp_master_conn.wait_heartbeat(timeout=HEARTBEAT_WAIT_PER_ITERATION_S)
                log_message(f"MAVLink: Heartbeat wait iteration {i+1} finished. Got msg: {bool(hb_msg)}", "DEBUG") 
                if hb_msg:
                    break
                # log_message(f"MAVLink: Heartbeat wait iteration for {conn_str}, retrying...", "DEBUG") # Covered by loop logs
            
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
                
                log_message(f"Processing first received heartbeat: {hb_msg}", "DEBUG")
                handle_mavlink_message(hb_msg)

                # --- Use REQUEST_DATA_STREAM instead of SET_MESSAGE_INTERVAL ---
                stream_rate_hz = 4 # Request streams at 4 Hz
                target_sys = master.target_system
                target_comp = master.target_component # Use the specific component ID from heartbeat
                log_message(f"Requesting MAV_DATA_STREAM_ALL at {stream_rate_hz} Hz from SYSID {target_sys} COMPID {target_comp} using REQUEST_DATA_STREAM", "INFO")
                master.mav.request_data_stream_send(
                    target_sys,
                    target_comp,
                    mavutil.mavlink.MAV_DATA_STREAM_ALL, # Request all streams
                    stream_rate_hz,  # Rate in Hz
                    1  # Start sending (1)
                )
                data_streams_requested = True # Mark streams as requested
                # --- End of REQUEST_DATA_STREAM logic ---
                
                log_message("MAVLink: Entering message processing loop.", "INFO")
            connection_successful = True

            # Main message processing loop
            telemetry_loop_active = True # Signal that the main loop is active

            while not mavlink_thread_stop_event.is_set():
                log_message(f"[DEBUG] Top of MAVLink receive loop. Target: {current_mavlink_target_ip}:{current_mavlink_target_port}. Connected: {drone_state.get('connected', False)}. Thread ID: {threading.get_ident()}", "DEBUG")
                try:
                    if master is None:
                        log_message("MAVLink connection lost in receive loop.", "WARNING")
                        drone_state["connected"] = False
                        emit_status_message("MAVLink connection lost.", "error")
                        break
                    # Wait for next MAVLink message
                    msg = master.recv_match(blocking=True, timeout=MESSAGE_RECEIVE_TIMEOUT_S)
                    if msg is not None:
                        log_message(f"[DEBUG] Received MAVLink message: {msg.get_type()}", "DEBUG")
                        handle_mavlink_message(msg)
                    else:
                        log_message("[DEBUG] No MAVLink message received (timeout)", "DEBUG")
                except Exception as e:
                    log_message(f"[ERROR] Exception in MAVLink receive loop: {e}\n{traceback.format_exc()}", "ERROR")
                log_message(f"[DEBUG] End of MAVLink receive loop iteration", "DEBUG")

            log_message("MAVLink receive loop exiting.", "INFO")
            telemetry_loop_active = False
        except gevent.Timeout as t:
            log_message(f"MAVLink: Timeout in main loop: {t}", "WARNING")
        except ConnectionError as ce: # Catch our specific ConnectionErrors (timeout, no heartbeat, socket error)
            log_message(f"MAVLink: ConnectionError in main loop: {ce}", "ERROR")
            # Ensure drone_state reflects disconnection if a connection attempt fails here
            with drone_state_lock:
                if drone_state.get('connected', True): 
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
            if not connection_successful:
                log_message(f"MAVLink: Disconnected or connection failed. Retrying in {RECONNECTION_ATTEMPT_DELAY}s...")
                emit_status_message(f"MAVLink connection lost. Retrying...", "warning")
                for _ in range(RECONNECTION_ATTEMPT_DELAY):
                    if mavlink_thread_stop_event.is_set():
                        log_message("MAVLink: Stop event during reconnection delay. Exiting loop.")
                        break
                    gevent.sleep(1)
        else:
            log_message("MAVLink: Stop event detected after connection attempt cycle. Terminating loop.")
            break

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


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Send initial state immediately to the newly connected client
    with mavlink_connection_lock:
        current_state_copy = drone_state.copy()  # Ensure thread-safe copy
        # The drone_state already uses current_mavlink_target_ip/port, 
        # but we explicitly set it here from globals for clarity and to ensure it's the most recent if accessed before drone_state is updated by mav_thread
        current_state_copy['mavlink_target_ip'] = current_mavlink_target_ip
        current_state_copy['mavlink_target_port'] = current_mavlink_target_port

    socketio.emit('telemetry_update', current_state_copy, room=request.sid)
    emit_status_message("Web client connected.", "info", room=request.sid)


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
    try:
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
    except Exception as ex:
        print(f"Exception while stopping MAVLink thread: {ex}")
        emit_status_message(f"Exception while stopping MAVLink thread: {ex}", "error")

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
        if drone_state.get('connected', False) or drone_state.get('mavlink_target_ip') is not None:
            with drone_state_lock:
                drone_state['connected'] = False
                # drone_state['mavlink_target_ip'] = None # Cleared by new connection attempt or UI
                # drone_state['mavlink_target_port'] = None
                drone_state_changed = True
    return True

# --- Main Execution Block ---
if __name__ == '__main__':
    # Add a short delay to allow the OS to release the port if restarting quickly
    time.sleep(2) # Increased delay to 2 seconds
    
    print(f"Starting server on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    # Start the background threads
    # Note: mavlink_receive_loop now starts the MAVLink connection attempt
    mav_thread = threading.Thread(target=mavlink_receive_loop, daemon=True) # Corrected function name
    mav_thread.start()

    print("Starting periodic telemetry update thread...")
    telemetry_update_thread = gevent.spawn(periodic_telemetry_update)
    
    try:
        socketio.run(app, 
                    host=WEB_SERVER_HOST, 
                    port=WEB_SERVER_PORT, 
                    debug=True,
                    use_reloader=False)  # Disable reloader to prevent duplicate threads
    finally:
        # --- Add Cleanup Logic Here ---
        log_message("Server process ending. Stopping background tasks...", "INFO")
        stop_mavlink_thread() # Ensure MAVLink connection and thread are stopped
        
        if telemetry_update_thread and not telemetry_update_thread.dead:
            log_message("Attempting to kill telemetry update greenlet...", "DEBUG")
            try:
                telemetry_update_thread.kill(block=False) # Non-blocking kill attempt
                log_message("Telemetry update greenlet kill signal sent.", "DEBUG")
            except Exception as e:
                log_message(f"Error killing telemetry greenlet: {e}", "WARNING")
        else:
            log_message("Telemetry update greenlet already stopped or not initialized.", "DEBUG")
            
        log_message("Cleanup complete.", "INFO")
        # --- End Cleanup Logic ---

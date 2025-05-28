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

# Import from new MAVLink connection manager
from mavlink_connection_manager import (
    mavlink_receive_loop_runner,
    get_mavlink_connection,
    get_connection_event,
    add_pending_command
)

# Import MAVLink message processors
from mavlink_message_processor import process_heartbeat, process_global_position_int, process_command_ack

# Import MAVLink utilities
from mavlink_utils import (
    MAV_RESULT_STR,
    MAV_TYPE_STR,
    MAV_STATE_STR,
    MAV_AUTOPILOT_STR,
    MAV_MODE_FLAG_ENUM
)
from request_handlers import init_request_handlers, _execute_fence_request, _execute_mission_request
import socketio_handlers

pending_commands = {}  # Initialize dictionary to track pending MAVLink commands
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

# --- Flask & SocketIO Setup ---
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app,
                    async_mode='gevent',
                    cors_allowed_origins="*"  # Allow cross-origin requests
                   )


# --- Global State ---

def set_drone_state_changed_flag():
    """Sets the global flag to indicate drone_state has been modified."""
    global drone_state_changed
    drone_state_changed = True

# mavlink_connection, last_heartbeat_time, connection_event are now managed in mavlink_connection_manager
mavlink_thread = None  # This will run mavlink_receive_loop_runner
telemetry_update_thread = None
drone_state_changed = False # Used by periodic_telemetry_update
drone_state_lock = threading.Lock() # Shared lock for drone_state

# drone_state remains central, accessed by multiple modules
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
# data_streams_requested and pending_commands are now managed in mavlink_connection_manager
home_position_requested = False # This might move to a feature handler or telemetry processor
app_shared_state = {
    'fence_request_pending': False,
    'mission_request_pending': False,
    'fence_points_list': [],
    'waypoints_list': []
}
fence_request_lock = threading.Lock() # Lock for the flag

mission_request_lock = threading.Lock() # Lock for the mission flag


# --- Scheduler Functions for SocketIO Handlers (called by socketio_handlers) ---
def _schedule_fence_request():
    """Sets a flag to trigger fence request using app_shared_state."""
    global app_shared_state, fence_request_lock
    with fence_request_lock:
        if not app_shared_state['fence_request_pending']:
            log_command_action("SCHEDULE_FENCE_REQUEST", details="Fence request scheduled by UI.")
            app_shared_state['fence_request_pending'] = True
        else:
            pass # Already pending

def _schedule_mission_request():
    """Sets a flag to trigger mission request using app_shared_state."""
    global app_shared_state, mission_request_lock
    with mission_request_lock:
        if not app_shared_state['mission_request_pending']:
            log_command_action("SCHEDULE_MISSION_REQUEST", details="Mission request scheduled by UI.")
            app_shared_state['mission_request_pending'] = True
        else:
            pass # Already pending

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

# process_heartbeat and process_command_ack functions moved to mavlink_message_processor.py

# mavlink_receive_loop function moved to mavlink_connection_manager.py and will be run by mavlink_receive_loop_runner

# _execute_fence_request has been moved to request_handlers.py

# _execute_mission_request has been moved to request_handlers.py

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

# handle_connect moved to socketio_handlers.py

# handle_disconnect moved to socketio_handlers.py

# send_mavlink_command moved and adapted into socketio_handlers.py as _send_mavlink_command_handler

# request_geofence_data logic is now handled by _schedule_fence_request (called from socketio_handlers)
# and _execute_fence_request (called from mavlink_message_router_loop).

# Removed old handlers

from socketio_handlers import init_socketio_handlers

# ... (rest of the code remains the same)


if __name__ == '__main__':
    print(f"Starting server on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    # Start the background threads
    # Placeholder for message processor and feature callbacks
    # This dictionary will be passed to mavlink_receive_loop_runner
    message_processor_callbacks = {
        'HEARTBEAT': process_heartbeat, 
        'GLOBAL_POSITION_INT': process_global_position_int,
        'COMMAND_ACK': process_command_ack,
        # 'SYS_STATUS': process_sys_status, # Example
    }

    feature_callbacks = {
        'EXECUTE_FENCE_REQUEST': _execute_fence_request, # Now imported
        'EXECUTE_MISSION_REQUEST': _execute_mission_request # Now imported
    }

    mavlink_thread = threading.Thread(
        target=mavlink_receive_loop_runner,
        args=(
            drone_state, drone_state_lock, socketio,
            MAVLINK_CONNECTION_STRING, HEARTBEAT_TIMEOUT,
            REQUEST_STREAM_RATE_HZ, COMMAND_ACK_TIMEOUT,
            message_processor_callbacks,
            feature_callbacks,
            log_command_action,
            set_drone_state_changed_flag,
            app_shared_state # Pass app_shared_state
        ),
        daemon=True
    )
    mavlink_thread.start()

    telemetry_update_thread = threading.Thread(target=periodic_telemetry_update, daemon=True)
    telemetry_update_thread.start()

    # Prepare context for and initialize SocketIO handlers
    app_context = {
        'log_command_action': log_command_action,
        'get_mavlink_connection': get_mavlink_connection, # from mavlink_connection_manager
        'drone_state': drone_state,
        'pending_commands_dict': pending_commands, # The global dict in app.py
        'AP_MODE_NAME_TO_ID': AP_CUSTOM_MODES, # from config (Name->ID mapping)
        'schedule_fence_request_in_app': _schedule_fence_request,
        'schedule_mission_request_in_app': _schedule_mission_request
    }
    # Prepare context for and initialize request_handlers
    request_handlers_context = {
        'socketio': socketio,
        'get_mavlink_connection': get_mavlink_connection,
        'drone_state': drone_state,
        'drone_state_lock': drone_state_lock,
        'log_command_action': log_command_action,
        'app_shared_state': app_shared_state,
        'fence_request_lock': fence_request_lock,
        'mission_request_lock': mission_request_lock
    }
    init_request_handlers(request_handlers_context)

    socketio_handlers.init_socketio_handlers(socketio, app_context)

    socketio.run(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT, debug=False, use_reloader=False)  # Disable reloader to prevent duplicate threads

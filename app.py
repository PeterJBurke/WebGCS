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
    MAV_AUTOPILOT_STR
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
                    cors_allowed_origins="*",  # Allow cross-origin requests
                    ping_timeout=60,          # Longer ping timeout (default behavior)
                    ping_interval=25,         # Standard ping interval
                    max_http_buffer_size=1e6, # Increase buffer size
                    engineio_logger=False,    # Disable logging
                    socketio_logger=False     # Disable logging
                   )


# --- Global State ---

def set_drone_state_changed_flag():
    """Sets the global flag to indicate drone_state has been modified."""
    global drone_state_changed
    drone_state_changed = True

def log_heartbeat_message(msg):
    """Log heartbeat message with special formatting for visibility and timestamp."""
    from datetime import datetime
    from pymavlink import mavutil
    from mavlink_utils import MAV_TYPE_STR, MAV_AUTOPILOT_STR, MAV_STATE_STR
    from config import AP_CUSTOM_MODES
    
    # Get current timestamp in human readable format
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
    
    # Parse heartbeat message details
    system_status_str = MAV_STATE_STR.get(msg.system_status, f"UNKNOWN({msg.system_status})")
    vehicle_type_str = MAV_TYPE_STR.get(msg.type, f"UNKNOWN({msg.type})")
    autopilot_type_str = MAV_AUTOPILOT_STR.get(msg.autopilot, f"UNKNOWN({msg.autopilot})")
    
    # Decode base mode flags
    base_mode_flags = []
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED:
        base_mode_flags.append("CUSTOM_MODE_ENABLED")
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_TEST_ENABLED:
        base_mode_flags.append("TEST_ENABLED")
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_AUTO_ENABLED:
        base_mode_flags.append("AUTO_ENABLED")
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_GUIDED_ENABLED:
        base_mode_flags.append("GUIDED_ENABLED")
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_STABILIZE_ENABLED:
        base_mode_flags.append("STABILIZE_ENABLED")
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_HIL_ENABLED:
        base_mode_flags.append("HIL_ENABLED")
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_MANUAL_INPUT_ENABLED:
        base_mode_flags.append("MANUAL_INPUT_ENABLED")
    if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
        base_mode_flags.append("SAFETY_ARMED")
    
    base_mode_str = ", ".join(base_mode_flags) if base_mode_flags else "NONE"
    
    # Get custom mode string
    custom_mode_str_list = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
    custom_mode_str = custom_mode_str_list[0] if custom_mode_str_list else f'CUSTOM_MODE({msg.custom_mode})'
    
    # Format armed status
    armed_status = "ARMED" if (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) else "DISARMED"
    
    # Print heartbeat with special formatting
    print()
    print("=" * 80)
    print("                              HEARTBEAT MESSAGE RECEIVED")
    print("=" * 80)
    print(f"TIMESTAMP: {timestamp}")
    print()
    print(f"SYSTEM ID: {msg.get_srcSystem()}  |  COMPONENT ID: {msg.get_srcComponent()}")
    print(f"VEHICLE TYPE: {vehicle_type_str}")
    print(f"AUTOPILOT: {autopilot_type_str}")
    print(f"SYSTEM STATUS: {system_status_str}")
    print(f"FLIGHT MODE: {custom_mode_str}")
    print(f"ARMED STATUS: {armed_status}")
    print(f"BASE MODE FLAGS: [{base_mode_str}]")
    print("=" * 80)
    print()

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

def read_telemetry_from_file():
    """Read telemetry data from the file created by the telemetry bridge script."""
    try:
        import json
        import os
        
        telemetry_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telemetry_data.json')
        
        if os.path.exists(telemetry_file):
            with open(telemetry_file, 'r') as f:
                data = json.load(f)
                print(f"Read telemetry data from file: connected={data.get('connected')}, mode={data.get('mode')}, armed={data.get('armed')}")
                return data, True
        else:
            print(f"Telemetry file not found: {telemetry_file}")
            return None, False
    except Exception as e:
        print(f"Error reading telemetry data from file: {e}")
        return None, False

def periodic_telemetry_update():
    """Periodically send telemetry updates to web clients."""
    global drone_state_changed
    update_count = 0
    last_debug_time = time.time()
    last_file_check_time = 0
    
    while True:
        try:
            current_time = time.time()
            
            # Check for telemetry data from file every 1 second (only as fallback if no live connection)
            mavlink_conn = get_mavlink_connection()
            if current_time - last_file_check_time >= 1 and not mavlink_conn:
                file_data, success = read_telemetry_from_file()
                if success and file_data:
                    with drone_state_lock:
                        # Update drone_state with data from file (fallback only)
                        for key, value in file_data.items():
                            if key in drone_state:
                                drone_state[key] = value
                        
                        # Set connected flag based on the file data's connected status
                        drone_state['connected'] = file_data.get('connected', False)
                        
                        # For testing: Accept any telemetry data as connected (comment out heartbeat timeout check)
                        # last_heartbeat_time = file_data.get('last_heartbeat_time', 0)
                        # if current_time - last_heartbeat_time > 300:  # Consider disconnected if no heartbeat within 300 seconds (5 minutes)
                        #     drone_state['connected'] = False
                        
                        # Signal that drone_state has changed
                        drone_state_changed = True
                        
                        # Print debug info about the connection status
                        # print(f"[FALLBACK] Connection status from file: {file_data.get('connected')}, Updated status: {drone_state['connected']}")
                        # print(f"[FALLBACK] Last heartbeat time: {file_data.get('last_heartbeat_time', 0)}, Current time: {current_time}, Diff: {current_time - file_data.get('last_heartbeat_time', 0)}s")
                        
                        # No simulated heartbeats - only real MAVLink heartbeats should trigger heart animation
                
                last_file_check_time = current_time
            
            # Log telemetry status every 5 seconds for debugging
            if current_time - last_debug_time >= 5:
                with drone_state_lock:
                    connected = drone_state.get('connected', False)
                    armed = drone_state.get('armed', False)
                    mode = drone_state.get('mode', 'UNKNOWN')
                    lat = drone_state.get('lat', 0.0)
                    lon = drone_state.get('lon', 0.0)
                    alt_rel = drone_state.get('alt_rel', 0.0)
                    
                # print(f"\n[TELEMETRY DEBUG] Update count: {update_count}, State changed: {drone_state_changed}")
                # print(f"[TELEMETRY DEBUG] Connected: {connected}, Armed: {armed}, Mode: {mode}")
                # print(f"[TELEMETRY DEBUG] Position: Lat={lat:.6f}, Lon={lon:.6f}, Alt={alt_rel:.1f}m")
                # print(f"[TELEMETRY DEBUG] Full drone_state: {drone_state}\n")
                
                last_debug_time = current_time
            
            # Send telemetry update if state has changed
            if drone_state_changed:
                with drone_state_lock:
                    # Emit telemetry update to all connected clients
                    # print(f"Sending telemetry update to web clients (update #{update_count+1})")
                    socketio.emit('telemetry_update', drone_state)
                    
                drone_state_changed = False
                update_count += 1
            
            gevent.sleep(TELEMETRY_UPDATE_INTERVAL)
        except Exception as e:
            print(f"Error in telemetry update: {e}")
            import traceback
            traceback.print_exc()
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

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': time.time(),
        'drone_connected': drone_state.get('connected', False),
        'drone_mode': drone_state.get('mode', 'UNKNOWN'),
        'drone_armed': drone_state.get('armed', False)
    })

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
    
    # Initialize contexts for handlers first
    app_context = {
        'log_command_action': log_command_action,
        'get_mavlink_connection': get_mavlink_connection,
        'drone_state': drone_state,
        'pending_commands_dict': pending_commands,
        'AP_MODE_NAME_TO_ID': AP_CUSTOM_MODES,
        'schedule_fence_request_in_app': _schedule_fence_request,
        'schedule_mission_request_in_app': _schedule_mission_request
    }
    
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
    
    # Start telemetry update thread 
    telemetry_update_thread = threading.Thread(target=periodic_telemetry_update, daemon=True)
    telemetry_update_thread.start()
    print("Telemetry update thread started")
    
    # Start MAVLink connection in background - don't wait for it
    def start_mavlink_connection_async():
        try:
            print(f"Attempting to connect to drone at {DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT} via {MAVLINK_CONNECTION_STRING}")
            
            # Start the MAVLink connection thread
            mavlink_thread = gevent.spawn(mavlink_receive_loop_runner, 
                                        MAVLINK_CONNECTION_STRING, 
                                        drone_state, 
                                        drone_state_lock, 
                                        pending_commands, 
                                        get_connection_event(), 
                                        log_command_action, 
                                        socketio, 
                                        set_drone_state_changed_flag, 
                                        app_shared_state, 
                                        _execute_fence_request, 
                                        _execute_mission_request, 
                                        HEARTBEAT_TIMEOUT, 
                                        REQUEST_STREAM_RATE_HZ, 
                                        COMMAND_ACK_TIMEOUT,
                                        log_heartbeat_message)
            return mavlink_thread
        except Exception as e:
            print(f"Error starting MAVLink thread: {e}")
            print("Continuing without MAVLink connection.")
            return None
    
    # Start MAVLink connection in a background thread - don't block server startup
    mavlink_connection_thread = threading.Thread(target=start_mavlink_connection_async, daemon=True)
    mavlink_connection_thread.start()
    
    # Start Flask-SocketIO server immediately 
    print(">>> Starting Flask-SocketIO server...")
    try:
        socketio.run(app, host='0.0.0.0', port=WEB_SERVER_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f">>> EXCEPTION during socketio.run: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(">>> Flask-SocketIO server finished.")

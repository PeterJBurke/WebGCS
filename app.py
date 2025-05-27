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
socketio = SocketIO(app,
                    async_mode='gevent',
                    cors_allowed_origins="*"  # Allow cross-origin requests
                   )


# --- Global State ---
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

# process_heartbeat and process_command_ack functions moved to mavlink_message_processor.py

# mavlink_receive_loop function moved to mavlink_connection_manager.py and will be run by mavlink_receive_loop_runner

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
    global pending_commands # mavlink_connection is now accessed via get_mavlink_connection()
    
    # Get command name for logging
    cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'

    current_mavlink_connection = get_mavlink_connection() # Define before use
    
    if not current_mavlink_connection or not drone_state.get("connected", False):
        warn_msg = f"CMD {cmd_name} Failed: Drone not connected."
        log_command_action(cmd_name, None, f"ERROR: {warn_msg}", "ERROR")
        return (False, warn_msg)
        
    # current_mavlink_connection is already defined, ensure it's used for target_sys and target_comp
    target_sys = current_mavlink_connection.target_system
    target_comp = current_mavlink_connection.target_component
    
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
        
        # current_mavlink_connection is already defined, ensure it's used for sending command
        current_mavlink_connection.mav.command_long_send(target_sys, target_comp, command, 0, p1, p2, p3, p4, p5, p6, p7)
        
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
    print(f"DEBUG: handle_send_command received data: {data}") # Log raw data
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
        print(f"DEBUG: UI command ARM. Sending MAV_CMD_COMPONENT_ARM_DISARM with p1=1 (ARM)")
        success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=1)
        cmd_type = 'info' if success else 'error'
        msg = f'ARM command sent.' if success else f'ARM Failed: {msg_send}'
    elif cmd == 'DISARM':
        print(f"DEBUG: UI command DISARM. Sending MAV_CMD_COMPONENT_ARM_DISARM with p1=0 (DISARM)")
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
            print(f"DEBUG: UI command SET_MODE. Mode String: {mode_string}, Custom Mode Value: {custom_mode}")
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
    # Placeholder for message processor and feature callbacks
    # This dictionary will be passed to mavlink_receive_loop_runner
    message_processor_callbacks = {
        'HEARTBEAT': process_heartbeat, 
        'GLOBAL_POSITION_INT': process_global_position_int,
        'COMMAND_ACK': process_command_ack,
        # 'SYS_STATUS': process_sys_status, # Example
    }

    feature_callbacks = {}

    mavlink_thread = threading.Thread(
        target=mavlink_receive_loop_runner,
        args=(
            drone_state, drone_state_lock, socketio,
            MAVLINK_CONNECTION_STRING, HEARTBEAT_TIMEOUT,
            REQUEST_STREAM_RATE_HZ, COMMAND_ACK_TIMEOUT,
            message_processor_callbacks, feature_callbacks, log_command_action # Pass log_command_action as a callback
        ),
        daemon=True
    )
    mavlink_thread.start()

    telemetry_update_thread = threading.Thread(target=periodic_telemetry_update, daemon=True)
    telemetry_update_thread.start()

    socketio.run(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT, debug=False, use_reloader=False)  # Disable reloader to prevent duplicate threads

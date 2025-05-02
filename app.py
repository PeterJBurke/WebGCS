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

# *** connect_mavlink function with ALL exception blocks corrected ***
def connect_mavlink():
    """Attempts to establish MAVLink connection TO the drone via UDP."""
    global mavlink_connection, last_heartbeat_time, data_streams_requested, home_position_requested, pending_commands, connection_event
    
    print("\n" + "="*50)
    print("DETAILED CONNECTION DEBUG")
    print("="*50)
    print(f"Connection string: {MAVLINK_CONNECTION_STRING}")
    print(f"Current connection state: {'Connected' if mavlink_connection else 'Not connected'}")
    
    # Close existing connection if any
    if mavlink_connection:
        try:
            print("Closing existing MAVLink connection...")
            mavlink_connection.close()
        except Exception as close_err:
            print(f"Error closing existing connection: {close_err}")
        finally:
            mavlink_connection = None
            print("Connection object set to None")

    # Reset state variables
    with drone_state_lock:
        drone_state['connected'] = False
        drone_state['armed'] = False
        drone_state['ekf_status_report'] = 'INIT'
    data_streams_requested = False
    home_position_requested = False
    pending_commands.clear()
    connection_event.clear()
    print("All state variables reset")

    def _attempt_connection():
        """Internal function to handle connection attempt"""
        try:
            print("Creating MAVLink connection object...")
            mav = mavutil.mavlink_connection(
                MAVLINK_CONNECTION_STRING,
                source_system=250,
                source_component=1,
                retries=3,
                robust_parsing=True
            )
            print(f"Connection object created: {mav}")
            
            print("Waiting for heartbeat (10 second timeout)...")
            msg = mav.wait_heartbeat(timeout=10)
            if msg:
                print(f"Heartbeat received! System: {mav.target_system}, Component: {mav.target_component}")
                print(f"Autopilot type: {msg.autopilot}")
                print(f"Vehicle type: {msg.type}")
                print(f"System status: {msg.system_status}")
                return mav, True
        except Exception as e:
            print(f"Connection attempt failed: {str(e)}")
        return None, False

    # Connection attempt with retries
    max_retries = 3
    for attempt in range(max_retries):
        print(f"\nConnection attempt {attempt + 1}/{max_retries}")
        
        # Use gevent to handle the connection attempt
        mavlink_connection, success = gevent.spawn(_attempt_connection).get(timeout=15)
        
        if success and mavlink_connection and mavlink_connection.target_system != 0:
            print("Connection successful!")
            with drone_state_lock:
                drone_state['connected'] = True
            last_heartbeat_time = time.time()
            connection_event.set()
            
            print("Requesting data streams...")
            request_data_streams()
            print("Connection process complete!")
            print("="*50 + "\n")
            return True
        
        if attempt < max_retries - 1:
            print("Retrying in 2 seconds...")
            gevent.sleep(2)
    
    print("All connection attempts failed")
    print("="*50 + "\n")
    return False


def request_data_streams(req_rate_hz=REQUEST_STREAM_RATE_HZ):
    """Requests necessary data streams from the flight controller."""
    global data_streams_requested
    print("\nDEBUG: Attempting to request data streams...")
    print(f"Connection state: {bool(mavlink_connection)}")
    print(f"Drone connected: {drone_state.get('connected', False)}")
    print(f"Target system: {mavlink_connection.target_system if mavlink_connection else 'N/A'}")
    
    if not mavlink_connection or not drone_state.get("connected", False) or mavlink_connection.target_system == 0: 
        print("DEBUG: Skipping data stream request - connection not ready")
        return
    try:
        target_sys = mavlink_connection.target_system
        target_comp = mavlink_connection.target_component
        print(f"DEBUG: Requesting streams from SYS:{target_sys} COMP:{target_comp} at {req_rate_hz}Hz...")
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
                print(f"DEBUG: Requested msg_id {msg_id} at {interval_us}us interval")
                gevent.sleep(0.05)
        data_streams_requested = True
        print("DEBUG: All data stream requests sent successfully")
    except Exception as req_err: 
        print(f"ERROR Sending data stream requests: {req_err}")
        traceback.print_exc()
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

def mavlink_receive_loop():
    """Background thread for receiving MAVLink messages."""
    global mavlink_connection, last_heartbeat_time, drone_state_changed, data_streams_requested, home_position_requested
    print("MAVLink receive loop starting...")
    message_counts = collections.defaultdict(int)
    last_count_print = time.time()
    
    while True:
        try:
            if not mavlink_connection:
                print("DEBUG: No MAVLink connection available...")
                # Wait for connection event or timeout
                if connection_event.wait(timeout=5):
                    print("Connection event received, continuing...")
                    continue
                else:
                    # Try to reconnect
                    if connect_mavlink():
                        print("Reconnection successful")
                    else:
                        gevent.sleep(1)
                    continue

            msg = mavlink_connection.recv_match(blocking=True, timeout=1.0)
            if msg:
                msg_type = msg.get_type()
                message_counts[msg_type] += 1
                
                # Print message statistics every 5 seconds
                current_time = time.time()
                if current_time - last_count_print >= 5:
                    print("\nMessage counts in last 5 seconds:")
                    for mtype, count in message_counts.items():
                        print(f"{mtype}: {count}")
                    message_counts.clear()
                    last_count_print = current_time
                    print(f"Connection state: {drone_state['connected']}")
                    print(f"Data streams requested: {data_streams_requested}")
                    print(f"Target system: {mavlink_connection.target_system}")
                    print(f"Target component: {mavlink_connection.target_component}\n")

                if msg_type == 'HEARTBEAT':
                    last_heartbeat_time = time.time()
                    with drone_state_lock:
                        drone_state['connected'] = True
                        drone_state['armed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                        if msg.get_srcSystem() == mavlink_connection.target_system:
                            custom_mode_str = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
                            drone_state['mode'] = custom_mode_str[0] if custom_mode_str else 'UNKNOWN'
                    print(f"DEBUG: HEARTBEAT processed. SysID:{msg.get_srcSystem()} LastHB:{last_heartbeat_time} Now:{time.time()} Armed:{drone_state['armed']} Mode:{drone_state['mode']}")
                    drone_state_changed = True

                elif msg_type == 'GLOBAL_POSITION_INT':
                    with drone_state_lock:
                        drone_state['lat'] = msg.lat / 1e7
                        drone_state['lon'] = msg.lon / 1e7
                        drone_state['alt_rel'] = msg.relative_alt / 1000.0
                        drone_state['alt_abs'] = msg.alt / 1000.0
                        drone_state['vx'] = msg.vx / 100.0
                        drone_state['vy'] = msg.vy / 100.0
                        drone_state['vz'] = msg.vz / 100.0
                        drone_state['heading'] = msg.hdg / 100.0 if msg.hdg != 65535 else drone_state['heading']
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
                    cmd = msg.command
                    if cmd in pending_commands:
                        del pending_commands[cmd]
                        cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name if cmd in mavutil.mavlink.enums['MAV_CMD'] else f'ID {cmd}'
                        result_name = MAV_RESULT_STR.get(msg.result, 'UNKNOWN')
                        print(f"Command ACK: {cmd_name} -> {result_name}")
                        socketio.emit('command_ack_received', {
                            'command': cmd,
                            'command_name': cmd_name,
                            'result': msg.result,
                            'result_text': result_name
                        })

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

        except Exception as e:
            print(f"Error in MAVLink receive loop: {e}")
            traceback.print_exc()
            gevent.sleep(1)

def periodic_telemetry_update():
    """Periodically send telemetry updates to web clients."""
    global drone_state_changed
    print("Starting periodic telemetry update thread...")
    update_count = 0
    last_debug = time.time()
    
    while True:
        try:
            current_time = time.time()
            if drone_state_changed:
                with drone_state_lock:
                    socketio.emit('telemetry_update', drone_state)
                    drone_state_changed = False
                    update_count += 1
                    
                    # Print debug info every 5 seconds
                    if current_time - last_debug >= 5:
                        print(f"DEBUG: Sent {update_count} telemetry updates in last 5s")
                        update_count = 0
                        last_debug = current_time
                        
            gevent.sleep(TELEMETRY_UPDATE_INTERVAL)
        except Exception as e:
            print(f"Error in telemetry update: {e}")
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
    if not mavlink_connection or not drone_state.get("connected", False):
        cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'
        warn_msg = f"CMD {cmd_name} Failed: Drone not connected."
        print(warn_msg)
        return (False, warn_msg)
    target_sys = mavlink_connection.target_system
    target_comp = mavlink_connection.target_component
    if target_sys == 0:
        err_msg = f"CMD {command} Failed: Invalid target system."
        print(err_msg)
        return (False, err_msg)
    try:
        cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'
        print(f"Sending CMD {cmd_name} ({command}) to SYS:{target_sys} COMP:{target_comp} | Params: p1={p1:.2f}, p2={p2:.2f}, p3={p3:.2f}, p4={p4:.2f}, p5={p5:.6f}, p6={p6:.6f}, p7={p7:.2f}")
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
        cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'
        err_msg = f"CMD {cmd_name} Send Error: {e}"
        print(err_msg)
        traceback.print_exc()
        return (False, err_msg)

@socketio.on('send_command')
def handle_send_command(data):
    """Handles commands received from the web UI."""
    cmd = data.get('command')
    print(f"UI Command Received: {cmd} Data: {data}")
    success = False
    msg = f'{cmd} processing...'
    cmd_type = 'info'

    if not drone_state.get("connected", False):
        msg = f'CMD {cmd} Fail: Disconnected.'
        cmd_type = 'error'
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
            success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_DO_REPOSITION, p1=-1, p4=math.nan, p5=lat, p6=lon, p7=alt)
            cmd_type = 'info' if success else 'error'
            msg = f'GoTo sent (Lat:{lat:.6f}, Lon:{lon:.6f}, Alt:{alt:.1f}m).' if success else f'GoTo Failed: {msg_send}'
        except (ValueError, TypeError, KeyError) as e:
            success = False
            msg = f'Invalid GoTo parameters: {e}'
            cmd_type = 'error'
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

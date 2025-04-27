# *** ADDED: Explicit Monkey Patching ***
from gevent import monkey
monkey.patch_all()

import sys
import time
import threading
import json
import gevent
# *** ADDED: Imports for explicit gevent server ***
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
import math
import traceback
import collections
from pymavlink import mavutil
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

# --- Configuration ---
DRONE_TCP_ADDRESS = '192.168.1.247'
DRONE_TCP_PORT = '5678'
MAVLINK_CONNECTION_STRING = f'tcp:{DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}'

WEB_SERVER_HOST = '0.0.0.0'
WEB_SERVER_PORT = 5000

# --- Constants ---
HEARTBEAT_TIMEOUT = 7
REQUEST_STREAM_RATE_HZ = 4
COMMAND_ACK_TIMEOUT = 5
TELEMETRY_UPDATE_INTERVAL = 0.1 # Seconds (10 Hz)

# ArduPilot Custom Flight Modes
AP_CUSTOM_MODES = { 'STABILIZE': 0, 'ACRO': 1, 'ALT_HOLD': 2, 'AUTO': 3, 'GUIDED': 4, 'LOITER': 5, 'RTL': 6, 'LAND': 9, 'POS_HOLD': 16, 'BRAKE': 17, 'THROW': 18, 'AVOID_ADSB': 19, 'GUIDED_NOGPS': 20, 'SMART_RTL': 21, 'FLOWHOLD': 22, 'FOLLOW': 23, 'ZIGZAG': 24, 'SYSTEMID': 25, 'AUTOROTATE': 26, 'AUTO_RTL': 27 }
AP_MODE_NAME_TO_ID = {v: k for k, v in AP_CUSTOM_MODES.items()}
MAV_RESULT_ENUM = mavutil.mavlink.enums['MAV_RESULT']
MAV_RESULT_STR = {v: k for k, v in MAV_RESULT_ENUM.items()}


# --- Flask & SocketIO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'desktop_drone_secret!'
socketio = SocketIO(app,
                    async_mode='gevent',
                    # logger=True,        # Keep logs disabled for cleaner output unless debugging disconnects
                    # engineio_logger=True
                   )


# --- Global State ---
mavlink_connection = None
mavlink_thread = None
telemetry_update_thread = None
last_heartbeat_time = 0
drone_state_changed = False
drone_state_lock = threading.Lock()

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
    """Attempts to establish MAVLink connection TO the drone via TCP."""
    global mavlink_connection, last_heartbeat_time, data_streams_requested, home_position_requested, pending_commands
    # Close existing connection if any
    if mavlink_connection:
        try:
            print("Closing existing MAVLink connection before reconnect...")
            mavlink_connection.close()
        except Exception as close_err:
            print(f"Minor error closing existing connection: {close_err}")
        finally:
            mavlink_connection = None # Ensure it's None after attempt

    # Reset state variables
    with drone_state_lock:
        drone_state['connected'] = False; drone_state['armed'] = False
        drone_state['ekf_status_report'] = 'INIT'
    data_streams_requested = False; home_position_requested = False
    pending_commands.clear()

    try:
        # Attempt connection and heartbeat wait
        print(f"Attempting TCP connection: {MAVLINK_CONNECTION_STRING}...")
        mavlink_connection = mavutil.mavlink_connection(MAVLINK_CONNECTION_STRING, source_system=250)
        print("Waiting for initial heartbeat...")
        mavlink_connection.wait_heartbeat(timeout=10) # Wait for the first heartbeat

        # Check if connection succeeded (target_system is set)
        if mavlink_connection.target_system == 0:
            print("No initial heartbeat received after connect. Check drone TCP server, network, firewall.")
            # Attempt to close if object exists but failed heartbeat wait
            if mavlink_connection:
                try: mavlink_connection.close()
                except Exception: pass
            mavlink_connection = None # Ensure reset
            return False
        else:
            # Success!
            print(f"MAVLink connected! Drone SYSID:{mavlink_connection.target_system} COMPID:{mavlink_connection.target_component}")
            with drone_state_lock: drone_state['connected'] = True
            last_heartbeat_time = time.time()
            request_data_streams() # Request streams now we are connected
            return True

    # --- Specific Exception Handlers ---
    except (ConnectionRefusedError, OSError, TimeoutError) as e: # Catch specific network/timeout errors first
        print(f"MAVLink Connect Network/Timeout Error: {e}. Check drone server & network settings.")
        with drone_state_lock:
            drone_state['connected'] = False; drone_state['armed'] = False
            drone_state['ekf_status_report'] = 'N/A'
        # *** CORRECTED try/except block for closing on network error ***
        if mavlink_connection:
            try:
                 print("Attempting to close connection after network error...")
                 mavlink_connection.close()
            except Exception as close_ex_inner:
                 print(f"Error closing connection within network exception handler: {close_ex_inner}")
        # Ensure mavlink_connection is set to None *after* attempting close
        mavlink_connection = None
        return False # Return False as connection failed

    except Exception as e: # Catch any other unexpected exceptions during connect/wait
        print(f"MAVLink Connect - Unexpected General Exception: {e}")
        traceback.print_exc() # Provide full traceback for debugging unexpected issues
        with drone_state_lock:
            drone_state['connected'] = False; drone_state['armed'] = False
            drone_state['ekf_status_report'] = 'N/A'
        # Ensure connection is closed and set to None even after unexpected exception
        if mavlink_connection:
            try: # Properly indented try/except/finally
                print("Closing connection after general exception during connect...")
                mavlink_connection.close()
            except Exception as close_ex:
                print(f"Error closing connection during exception handling: {close_ex}")
            finally:
                # Ensure mavlink_connection is None regardless of close success/failure
                mavlink_connection = None
        return False # Return False as connection failed


def request_data_streams(req_rate_hz=REQUEST_STREAM_RATE_HZ):
    """Requests necessary data streams from the flight controller."""
    global data_streams_requested
    if not mavlink_connection or not drone_state.get("connected", False) or mavlink_connection.target_system == 0: return
    try:
        target_sys = mavlink_connection.target_system; target_comp = mavlink_connection.target_component
        # print(f"DEBUG: Requesting streams from SYS:{target_sys} COMP:{target_comp} at {req_rate_hz}Hz...")
        messages_to_request = { mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT: 1, mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS: 1, mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: 5, mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD: 2, mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE: 10, mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT: 1, mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION: 0.2, mavutil.mavlink.MAVLINK_MSG_ID_STATUSTEXT: 1, mavutil.mavlink.MAVLINK_MSG_ID_COMMAND_ACK: 5, }
        for msg_id, rate_hz in messages_to_request.items():
            interval_us = int(1e6 / rate_hz) if rate_hz > 0 else -1
            if msg_id == mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION and home_position_requested: interval_us = -1
            if interval_us != -1 or (msg_id == mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION and not home_position_requested):
                mavlink_connection.mav.command_long_send(target_sys, target_comp, mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0, msg_id, interval_us, 0, 0, 0, 0, 0)
                gevent.sleep(0.05)
        data_streams_requested = True
        # print("DEBUG: Data stream requests sent.")
    except Exception as req_err: print(f"ERROR Sending data stream requests: {req_err}"); data_streams_requested = False


def check_pending_command_timeouts():
    """Checks for timed-out commands that haven't received an ACK."""
    now = time.time(); timed_out_cmds = []
    for cmd_id, timestamp in list(pending_commands.items()):
        if now - timestamp > COMMAND_ACK_TIMEOUT: timed_out_cmds.append(cmd_id)
    for cmd_id in timed_out_cmds:
        if cmd_id in pending_commands:
            cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd_id].name if cmd_id in mavutil.mavlink.enums['MAV_CMD'] else f'ID {cmd_id}'; print(f"WARNING: Command {cmd_name} ({cmd_id}) timed out without ACK.")
            socketio.emit('command_ack_received', { 'command_id': cmd_id, 'command_name': cmd_name, 'result': -1, 'result_text': 'Timeout' }, namespace='/drone')
            try: del pending_commands[cmd_id]
            except KeyError: pass

def mavlink_receive_loop():
    """Main loop processing incoming MAVLink messages."""
    global last_heartbeat_time, drone_state, mavlink_connection, data_streams_requested, home_position_requested, drone_state_changed
    last_ack_check_time = time.time()

    while True:
        if mavlink_connection is None:
            if not connect_mavlink():
                with drone_state_lock: drone_state_changed = True
                gevent.sleep(5); continue
        if drone_state.get('connected') and (time.time() - last_heartbeat_time > HEARTBEAT_TIMEOUT):
            print(f"MAVLink timeout (>{HEARTBEAT_TIMEOUT}s). Resetting.")
            if mavlink_connection:
                try: mavlink_connection.close(); print("Closed timed-out connection.");
                except Exception as e: print(f"Error closing on timeout: {e}")
            mavlink_connection = None
            with drone_state_lock:
                drone_state['connected'] = False; drone_state['armed'] = False; drone_state['ekf_status_report'] = 'N/A'
                drone_state_changed = True
            data_streams_requested = False; home_position_requested = False; pending_commands.clear()
            gevent.sleep(1); continue

        now = time.time()
        if now - last_ack_check_time > 1.0:
             check_pending_command_timeouts(); last_ack_check_time = now

        msg = None
        state_updated_by_msg = False
        try:
            msg = mavlink_connection.recv_match(blocking=False, timeout=0.02)
        except (mavutil.mavlink.MAVLinkException, OSError, ConnectionResetError, BrokenPipeError) as e:
             print(f"MAVLink Comms Error: {e}. Resetting.")
             if mavlink_connection:
                 try: mavlink_connection.close(); print("Closed connection after comms error.");
                 except Exception as e: print(f"Err closing on comms err: {e}")
             mavlink_connection = None
             with drone_state_lock:
                 drone_state['connected'] = False; drone_state['armed'] = False; drone_state['ekf_status_report'] = 'N/A'
                 drone_state_changed = True
             data_streams_requested = False; home_position_requested = False; pending_commands.clear()
             gevent.sleep(5); continue
        except Exception as e: print(f"Unexpected Error recv_match: {e}"); traceback.print_exc(); gevent.sleep(1); continue

        if msg:
            msg_type = msg.get_type()
            # --- Raw MAVLink broadcast REMOVED ---

            try:
                with drone_state_lock:
                    original_state_repr = repr(drone_state)
                    # --- Message Parsing Logic (inside lock) ---
                    if msg_type == 'HEARTBEAT':
                        if msg.get_srcSystem() == mavlink_connection.target_system:
                            last_heartbeat_time = time.time(); was_connected = drone_state["connected"]
                            drone_state['connected'] = True; drone_state['armed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                            if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED: drone_state['mode'] = AP_MODE_NAME_TO_ID.get(msg.custom_mode, f"Custom({msg.custom_mode})")
                            else: drone_state['mode'] = mavutil.mode_string_v10(msg)
                            drone_state['system_status'] = msg.system_status
                            if (not was_connected or not data_streams_requested) and mavlink_connection.target_system != 0: request_data_streams()
                            if not was_connected: socketio.emit('status_message', {'text': 'Drone Reconnected', 'type': 'info'}, namespace='/drone')
                    elif msg_type == 'GLOBAL_POSITION_INT': drone_state.update({'lat': msg.lat / 1e7, 'lon': msg.lon / 1e7, 'alt_rel': msg.relative_alt / 1000.0, 'alt_abs': msg.alt / 1000.0, 'heading': msg.hdg / 100.0 if msg.hdg != 65535 else drone_state.get('heading', 0.0), 'vx': msg.vx / 100.0, 'vy': msg.vy / 100.0, 'vz': msg.vz / 100.0, 'groundspeed': math.sqrt(msg.vx**2 + msg.vy**2) / 100.0})
                    elif msg_type == 'VFR_HUD':
                        drone_state['airspeed'] = msg.airspeed
                        if drone_state.get('groundspeed', 0.0) == 0.0: drone_state['groundspeed'] = msg.groundspeed
                    elif msg_type == 'GPS_RAW_INT': drone_state.update({'gps_fix_type': msg.fix_type, 'satellites_visible': msg.satellites_visible if msg.satellites_visible != 255 else -1, 'hdop': msg.eph / 100.0 if msg.eph != 65535 else 99.99})
                    elif msg_type == 'SYS_STATUS':
                         ekf_flags = msg.onboard_control_sensors_health
                         drone_state.update({'battery_voltage': msg.voltage_battery / 1000.0, 'battery_remaining': msg.battery_remaining, 'battery_current': msg.current_battery / 100.0 if msg.current_battery >= 0 else -1.0, 'ekf_flags': ekf_flags, 'ekf_status_report': get_ekf_status_report(ekf_flags)})
                    elif msg_type == 'STATUSTEXT':
                        message_text = msg.text.rstrip('\x00'); print(f"STATUSTEXT [{msg.severity}]: {message_text}")
                        severity_map = {0:'error', 1:'error', 2:'error', 3:'error', 4:'warning', 5:'info', 6:'info', 7:'info', mavutil.mavlink.MAV_SEVERITY_DEBUG:'debug'}
                        ui_msg_type = severity_map.get(msg.severity, 'info')
                        if ui_msg_type != 'debug': socketio.emit('status_message', {'text': message_text, 'type': ui_msg_type}, namespace='/drone')
                    elif msg_type == 'ATTITUDE': drone_state.update({'pitch': msg.pitch, 'roll': msg.roll})
                    elif msg_type == 'HOME_POSITION':
                        if not home_position_requested: home_lat = msg.latitude / 1e7; home_lon = msg.longitude / 1e7; print(f"Received HOME_POSITION: Lat={home_lat}, Lon={home_lon}"); drone_state.update({'home_lat': home_lat, 'home_lon': home_lon}); home_position_requested = True
                    elif msg_type == 'COMMAND_ACK':
                        cmd_id = msg.command; result = msg.result; result_text = MAV_RESULT_STR.get(result, f"Unknown ({result})"); cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd_id].name if cmd_id in mavutil.mavlink.enums['MAV_CMD'] else f'ID {cmd_id}'; print(f"ACK Received: CMD={cmd_name}({cmd_id}), Result={result_text}({result})")
                        socketio.emit('command_ack_received', { 'command_id': cmd_id, 'command_name': cmd_name, 'result': result, 'result_text': result_text }, namespace='/drone')
                        if cmd_id in pending_commands: del pending_commands[cmd_id]
                        else: print(f"Info: Received ACK for untracked/external command: {cmd_name}")
                    # --- End Message Parsing ---

                    if repr(drone_state) != original_state_repr:
                         state_updated_by_msg = True
                # Lock released here

                if state_updated_by_msg:
                    drone_state_changed = True

                gevent.sleep(0.001)

            except Exception as parse_err: print(f"Error parsing {msg_type}: {parse_err}"); traceback.print_exc()
        else:
             gevent.sleep(0.005)


def periodic_telemetry_update():
    """Periodically sends telemetry updates to clients if state has changed."""
    global drone_state_changed
    while True:
        try:
            should_emit = False
            if drone_state_changed:
                 with drone_state_lock:
                     if drone_state_changed:
                         state_copy = drone_state.copy()
                         drone_state_changed = False
                         should_emit = True
            if should_emit:
                socketio.emit('telemetry_update', state_copy, namespace='/drone')
        except Exception as e:
            print(f"Error in periodic_telemetry_update: {e}")
            traceback.print_exc()
        gevent.sleep(TELEMETRY_UPDATE_INTERVAL)


# --- Flask Routes and SocketIO Handlers ---
@app.route('/')
def index(): return render_template("index.html", version="v2.63-Desktop-TCP-AckEkf")
@app.route('/mavlink_dump')
def mavlink_dump(): return render_template("mavlink_dump.html", version="v2.63-Desktop-TCP-AckEkf")
@socketio.on('connect', namespace='/drone')
def handle_connect(): print("Web UI Client connected"); emit('telemetry_update', drone_state); status_text = 'Backend connected. '; status_text += 'Drone link active.' if drone_state.get('connected') else 'Attempting drone link...'; emit('status_message', {'text': status_text, 'type': 'info'})
@socketio.on('disconnect', namespace='/drone')
def handle_disconnect(): print("Web UI Client disconnected")

def send_mavlink_command(command, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0):
    global mavlink_connection, pending_commands
    if not mavlink_connection or not drone_state.get("connected", False): cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'; warn_msg = f"CMD {cmd_name} Failed: Drone not connected."; print(warn_msg); return (False, warn_msg)
    target_sys = mavlink_connection.target_system; target_comp = mavlink_connection.target_component
    if target_sys == 0: err_msg = f"CMD {command} Failed: Invalid target system."; print(err_msg); return (False, err_msg)
    try:
        cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'
        print(f"Sending CMD {cmd_name} ({command}) to SYS:{target_sys} COMP:{target_comp} | Params: p1={p1:.2f}, p2={p2:.2f}, p3={p3:.2f}, p4={p4:.2f}, p5={p5:.6f}, p6={p6:.6f}, p7={p7:.2f}")
        mavlink_connection.mav.command_long_send(target_sys, target_comp, command, 0, p1, p2, p3, p4, p5, p6, p7)
        if command not in [mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE]:
            pending_commands[command] = time.time()
            if len(pending_commands) > 30: oldest_cmd = next(iter(pending_commands)); print(f"Warning: Pending cmd limit, removing oldest: {oldest_cmd}"); del pending_commands[oldest_cmd]
        success_msg = f"CMD {cmd_name} sent."; return (True, success_msg)
    except Exception as e: cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'; err_msg = f"CMD {cmd_name} Send Error: {e}"; print(err_msg); traceback.print_exc(); return (False, err_msg)

# handle_send_command with CORRECTED syntax for try/except blocks
@socketio.on('send_command', namespace='/drone')
def handle_send_command(data):
    """Handles commands received from the web UI."""
    cmd = data.get('command'); print(f"UI Command Received: {cmd} Data: {data}")
    success = False; msg = f'{cmd} processing...'; cmd_type = 'info'
    if not drone_state.get("connected", False): msg = f'CMD {cmd} Fail: Disconnected.'; cmd_type = 'error'; socketio.emit('status_message', {'text': msg, 'type': cmd_type}, namespace='/drone'); socketio.emit('command_result', {'command': cmd, 'success': False, 'message': msg}, namespace='/drone'); return
    if cmd == 'ARM': success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=1); cmd_type = 'info' if success else 'error'; msg = f'ARM command sent.' if success else f'ARM Failed: {msg_send}'
    elif cmd == 'DISARM': success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, p1=0); cmd_type = 'info' if success else 'error'; msg = f'DISARM command sent.' if success else f'DISARM Failed: {msg_send}'
    elif cmd == 'TAKEOFF':
        try:
            alt = float(data.get('altitude', 5.0))
            if not (0 < alt <= 1000): raise ValueError("Altitude must be > 0 and <= 1000")
            success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, p7=alt)
            cmd_type = 'info' if success else 'error'; msg = f'Takeoff to {alt:.1f}m command sent.' if success else f'Takeoff Failed: {msg_send}'
        except (ValueError, TypeError) as e:
             success = False; msg = f'Invalid Takeoff Alt: {e}'; cmd_type = 'error'
    elif cmd == 'LAND': success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_NAV_LAND); cmd_type = 'info' if success else 'error'; msg = 'LAND command sent.' if success else f'LAND Failed: {msg_send}'
    elif cmd == 'RTL': success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH); cmd_type = 'info' if success else 'error'; msg = 'RTL command sent.' if success else f'RTL Failed: {msg_send}'
    elif cmd == 'SET_MODE':
        mode_string = data.get('mode_string')
        if mode_string and mode_string in AP_CUSTOM_MODES:
            custom_mode = AP_CUSTOM_MODES[mode_string]; base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
            print(f"Attempting to set mode: {mode_string} (Custom Mode: {custom_mode})")
            success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_DO_SET_MODE, p1=base_mode, p2=custom_mode)
            cmd_type = 'info' if success else 'error'; msg = f'Set Mode {mode_string} command sent.' if success else f'Set Mode {mode_string} Failed: {msg_send}'
        else:
            success = False; msg = f'Invalid/Unknown Mode: {mode_string}'; cmd_type = 'error'
    elif cmd == 'GOTO':
        try:
            lat = float(data.get('lat')); lon = float(data.get('lon')); alt = float(data.get('alt'))
            if not (-90 <= lat <= 90): raise ValueError("Latitude out of range [-90, 90]")
            if not (-180 <= lon <= 180): raise ValueError("Longitude out of range [-180, 180]")
            if not (-100 <= alt <= 5000): raise ValueError("Altitude out of range [-100, 5000]")
            success, msg_send = send_mavlink_command(mavutil.mavlink.MAV_CMD_DO_REPOSITION, p1=-1, p4=math.nan, p5=lat, p6=lon, p7=alt)
            cmd_type = 'info' if success else 'error'; msg = f'GoTo sent (Lat:{lat:.6f}, Lon:{lon:.6f}, Alt:{alt:.1f}m).' if success else f'GoTo Failed: {msg_send}'
        except (ValueError, TypeError, KeyError) as e:
             success = False; msg = f'Invalid GoTo parameters: {e}'; cmd_type = 'error'
    else:
        msg = f'Unknown command received: {cmd}'; cmd_type = 'warning'; success = False

    socketio.emit('status_message', {'text': msg, 'type': cmd_type}, namespace='/drone')
    socketio.emit('command_result', {'command': cmd, 'success': success, 'message': msg}, namespace='/drone')


if __name__ == '__main__':
    print("Starting MAVLink listener greenlet...")
    mavlink_thread = gevent.spawn(mavlink_receive_loop)
    print("Starting periodic telemetry update greenlet...")
    telemetry_update_thread = gevent.spawn(periodic_telemetry_update)
    print(f"Starting Flask-SocketIO web server on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    print("Access the interface at http://<your_desktop_ip>:%s or http://127.0.0.1:%s" % (WEB_SERVER_PORT, WEB_SERVER_PORT))
    try:
        server = pywsgi.WSGIServer((WEB_SERVER_HOST, WEB_SERVER_PORT), app, handler_class=WebSocketHandler)
        print("Starting server with gevent pywsgi...")
        server.serve_forever()
    except KeyboardInterrupt: print("KeyboardInterrupt received, shutting down.")
    except Exception as e: print(f"Web Server Error: {e}"); traceback.print_exc(); sys.exit(1)
    finally:
        print("Server shutting down...")
        if 'server' in locals() and hasattr(server, 'stop'):
             print("Attempting to stop Gevent server...")
             server.stop(timeout=1)
        if telemetry_update_thread and not telemetry_update_thread.dead: print("Stopping Telemetry update greenlet..."); telemetry_update_thread.kill(block=False)
        if mavlink_thread and not mavlink_thread.dead: print("Stopping MAVLink listener greenlet..."); mavlink_thread.kill(block=True, timeout=2); print("MAVLink greenlet stopped." if mavlink_thread.dead else "Warning: MAVLink greenlet did not stop cleanly.")
        if mavlink_connection:
             try: print("Closing MAVLink connection..."); mavlink_connection.close(); print("MAVLink connection closed.")
             except Exception as e: print(f"Error closing MAVLink: {e}")
        print("Server stopped.")

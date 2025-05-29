from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
import threading
import time
import gevent
from pymavlink import mavutil
import json
import sys
import math
import traceback

# Import configuration
from config import (
    DRONE_TCP_ADDRESS,
    DRONE_TCP_PORT,
    MAVLINK_CONNECTION_STRING,
    WEB_SERVER_HOST,
    WEB_SERVER_PORT,
    SECRET_KEY,
    HEARTBEAT_TIMEOUT,
    REQUEST_STREAM_RATE_HZ
)

# --- Flask & SocketIO Setup ---
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True
socketio = SocketIO(app,
                    async_mode='gevent',
                    cors_allowed_origins="*"
                   )

# --- Global State ---
mavlink_connection = None
last_heartbeat_time = 0
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
drone_state_lock = threading.Lock()
drone_state_changed = False

# --- MAVLink Functions ---
def connect_to_drone():
    """Connect to the drone using the same method as test_heartbeat.py"""
    global mavlink_connection, drone_state, drone_state_lock
    
    print(f"Connecting to MAVLink endpoint: {MAVLINK_CONNECTION_STRING}")
    
    try:
        # Connect to the MAVLink endpoint (TCP)
        mavlink_connection = mavutil.mavlink_connection(MAVLINK_CONNECTION_STRING)
        
        print("Waiting for heartbeat messages...")
        
        # Wait for heartbeat to confirm connection
        msg = mavlink_connection.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
        if msg is not None:
            print(f"Received initial heartbeat from system {msg.get_srcSystem()}, confirming connection")
            
            # Update drone state
            with drone_state_lock:
                drone_state['connected'] = True
                drone_state_changed = True
            
            # Emit heartbeat event for UI animation
            socketio.emit('heartbeat_received', {'sysid': msg.get_srcSystem()})
            
            return True
        else:
            print("No heartbeat received within timeout period")
            return False
    except Exception as e:
        print(f"Error connecting to drone: {e}")
        traceback.print_exc()
        return False

def request_data_streams():
    """Request data streams from the drone"""
    global mavlink_connection
    
    if not mavlink_connection:
        print("No MAVLink connection to request streams")
        return
    
    print("Requesting data streams...")
    
    # Define messages and their desired rates in Hz
    messages_to_request = {
        mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT: 1,
        mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS: 1,
        mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT: 1,
        mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: REQUEST_STREAM_RATE_HZ,
        mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE: REQUEST_STREAM_RATE_HZ,
        mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD: REQUEST_STREAM_RATE_HZ,
        mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION: 0.2,
    }
    
    try:
        for msg_id, rate_hz in messages_to_request.items():
            interval_us = int(1e6 / rate_hz) if rate_hz > 0 else 0
            
            print(f"  Requesting MSG ID {msg_id} at {rate_hz} Hz (Interval: {interval_us} us)")
            mavlink_connection.mav.command_long_send(
                mavlink_connection.target_system,
                mavlink_connection.target_component,
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                0,  # Confirmation
                msg_id,
                interval_us,
                0, 0, 0, 0, 0  # params 3-7 not used
            )
            gevent.sleep(0.05)  # Small delay between requests
        
        print("Data streams request sequence completed.")
    except Exception as e:
        print(f"Error requesting data streams: {e}")
        traceback.print_exc()

def process_heartbeat(msg):
    """Process heartbeat message"""
    global last_heartbeat_time, drone_state, drone_state_lock, drone_state_changed
    
    last_heartbeat_time = time.time()
    
    # Extract mode information
    base_mode = msg.base_mode
    custom_mode = msg.custom_mode
    
    # Determine if armed
    armed = bool(base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    
    # Get human-readable mode name
    mode_name = mavutil.mode_string_v10(msg)
    
    with drone_state_lock:
        # Update connection status if needed
        if not drone_state['connected']:
            drone_state['connected'] = True
            print("Drone connected via heartbeat")
        
        # Update armed status and mode
        if drone_state['armed'] != armed or drone_state['mode'] != mode_name:
            drone_state['armed'] = armed
            drone_state['mode'] = mode_name
            drone_state_changed = True
    
    # Emit heartbeat event for UI animation
    socketio.emit('heartbeat_received', {'sysid': msg.get_srcSystem()})

def process_global_position_int(msg):
    """Process global position message"""
    global drone_state, drone_state_lock, drone_state_changed
    
    with drone_state_lock:
        # Update position data
        drone_state['lat'] = msg.lat / 1e7  # Convert from int32 (1e7) to float (degrees)
        drone_state['lon'] = msg.lon / 1e7
        drone_state['alt_rel'] = msg.relative_alt / 1000.0  # Convert from mm to m
        drone_state['alt_abs'] = msg.alt / 1000.0
        drone_state['heading'] = msg.hdg / 100.0 if msg.hdg != 65535 else drone_state['heading']  # hdg 65535 means unknown
        
        # Update velocity data
        drone_state['vx'] = msg.vx / 100.0  # Convert from cm/s to m/s
        drone_state['vy'] = msg.vy / 100.0
        drone_state['vz'] = msg.vz / 100.0
        
        drone_state_changed = True

def process_vfr_hud(msg):
    """Process VFR HUD message"""
    global drone_state, drone_state_lock, drone_state_changed
    
    with drone_state_lock:
        drone_state['airspeed'] = msg.airspeed
        drone_state['groundspeed'] = msg.groundspeed
        drone_state_changed = True

def process_sys_status(msg):
    """Process system status message"""
    global drone_state, drone_state_lock, drone_state_changed
    
    with drone_state_lock:
        drone_state['battery_voltage'] = msg.voltage_battery / 1000.0  # Convert from mV to V
        drone_state['battery_current'] = msg.current_battery / 100.0   # Convert from cA to A
        drone_state['battery_remaining'] = msg.battery_remaining       # Percentage
        drone_state_changed = True

def process_attitude(msg):
    """Process attitude message"""
    global drone_state, drone_state_lock, drone_state_changed
    
    with drone_state_lock:
        # Convert from radians to degrees
        drone_state['pitch'] = math.degrees(msg.pitch)
        drone_state['roll'] = math.degrees(msg.roll)
        drone_state_changed = True

def process_gps_raw_int(msg):
    """Process GPS raw int message"""
    global drone_state, drone_state_lock, drone_state_changed
    
    with drone_state_lock:
        drone_state['gps_fix_type'] = msg.fix_type
        drone_state['satellites_visible'] = msg.satellites_visible
        drone_state['hdop'] = msg.eph / 100.0 if msg.eph != 65535 else 99.99  # eph 65535 means unknown
        drone_state_changed = True

def process_home_position(msg):
    """Process home position message"""
    global drone_state, drone_state_lock, drone_state_changed
    
    with drone_state_lock:
        drone_state['home_lat'] = msg.latitude / 1e7  # Convert from int32 (1e7) to float (degrees)
        drone_state['home_lon'] = msg.longitude / 1e7
        drone_state_changed = True
        print(f"Home position set: {drone_state['home_lat']}, {drone_state['home_lon']}")

def mavlink_receive_loop():
    """Main loop for receiving MAVLink messages"""
    global mavlink_connection, last_heartbeat_time, drone_state, drone_state_lock
    
    print("MAVLink receive loop started")
    
    # Message handlers
    message_handlers = {
        'HEARTBEAT': process_heartbeat,
        'GLOBAL_POSITION_INT': process_global_position_int,
        'VFR_HUD': process_vfr_hud,
        'SYS_STATUS': process_sys_status,
        'ATTITUDE': process_attitude,
        'GPS_RAW_INT': process_gps_raw_int,
        'HOME_POSITION': process_home_position,
    }
    
    while True:
        try:
            if not mavlink_connection:
                # If connection is lost, try to reconnect
                if connect_to_drone():
                    # Request data streams after successful connection
                    request_data_streams()
                else:
                    # Wait before trying again
                    time.sleep(5)
                    continue
            
            # Check for heartbeat timeout
            if last_heartbeat_time > 0 and (time.time() - last_heartbeat_time > HEARTBEAT_TIMEOUT):
                print(f"Heartbeat timeout (>{HEARTBEAT_TIMEOUT}s). Drone disconnected.")
                with drone_state_lock:
                    drone_state['connected'] = False
                    drone_state_changed = True
                mavlink_connection = None
                last_heartbeat_time = 0
                socketio.emit('drone_disconnected', {'reason': 'Heartbeat timeout'})
                continue
            
            # Receive message with timeout (non-blocking)
            msg = mavlink_connection.recv_match(blocking=False, timeout=0.1)
            
            if msg:
                msg_type = msg.get_type()
                
                # Process message if handler exists
                if msg_type in message_handlers:
                    message_handlers[msg_type](msg)
            
            # Small sleep to avoid excessive CPU usage
            time.sleep(0.01)
            
        except Exception as e:
            print(f"Error in MAVLink receive loop: {e}")
            traceback.print_exc()
            
            # Reset connection on error
            if mavlink_connection:
                try:
                    mavlink_connection.close()
                except:
                    pass
                mavlink_connection = None
            
            with drone_state_lock:
                drone_state['connected'] = False
                drone_state_changed = True
            
            socketio.emit('drone_disconnected', {'reason': f'Error: {str(e)}'})
            time.sleep(1)  # Wait before trying to reconnect

def periodic_telemetry_update():
    """Periodically send telemetry updates to web clients"""
    global drone_state, drone_state_lock, drone_state_changed
    
    while True:
        try:
            if drone_state_changed:
                with drone_state_lock:
                    socketio.emit('telemetry_update', drone_state)
                    drone_state_changed = False
            time.sleep(0.1)  # 10 Hz update rate
        except Exception as e:
            print(f"Error in telemetry update: {e}")
            time.sleep(1)

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template("index.html", version="v2.63-Desktop-TCP-Simple")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/health')
def health_check():
    print("HEALTH CHECK ENDPOINT HIT")
    return "OK", 200

# --- Main ---
if __name__ == '__main__':
    print(f"Starting server on http://{WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    
    # Start telemetry update thread
    telemetry_thread = threading.Thread(target=periodic_telemetry_update, daemon=True)
    telemetry_thread.start()
    print("Telemetry update thread started")
    
    # Start MAVLink receive loop in a separate thread
    mavlink_thread = threading.Thread(target=mavlink_receive_loop, daemon=True)
    mavlink_thread.start()
    print("MAVLink receive loop started")
    
    # Start Flask-SocketIO server
    print("Starting Flask-SocketIO server...")
    try:
        socketio.run(app, host='0.0.0.0', port=WEB_SERVER_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error starting server: {e}")
        traceback.print_exc()

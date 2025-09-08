"""
WebGCS Flask Application
Web Ground Control Station main application with Flask-SocketIO
"""
import os
import sys
import threading
import time
from flask import Flask, render_template, jsonify, send_from_directory, request
from flask_socketio import SocketIO, emit

# Import configuration
from config import (
    WEB_SERVER_HOST, WEB_SERVER_PORT, SECRET_KEY,
    MAVLINK_CONNECTION_STRING, TELEMETRY_UPDATE_INTERVAL
)

# Import MAVLink components
from mavlink_connection_manager import connect_mavlink, get_mavlink_connection, disconnect_mavlink
from mavlink_message_processor import process_heartbeat, process_global_position_int
from mavlink_command_sender import process_flight_command

# Import high-performance logging
from high_performance_logger import setup_logger, get_logger

# Flask & SocketIO Setup
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True

socketio = SocketIO(
    app,
    async_mode='threading',
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e6,
    engineio_logger=True,
    socketio_logger=True
)

# Global State
drone_state = {
    'connected': False,
    'armed': False,
    'mode': 'UNKNOWN',
    'lat': 0.0, 'lon': 0.0,
    'alt_rel': 0.0, 'alt_abs': 0.0,
    'heading': 0.0,
    'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
    'system_id': 0,
    'component_id': 0,
    'system_status': 0
}
drone_state_lock = threading.Lock()
drone_state_changed = False

def log_command_action(command_name, params=None, details=None, level="INFO"):
    """High-performance logging function"""
    try:
        # Use high-performance logger
        logger = get_logger()
        
        # Format message with params and details
        params_str = f", Params: {params}" if params else ""
        details_str = f" - {details}" if details else ""
        message = f"{command_name}{params_str}{details_str}"
        
        # Log using high-performance system
        logger.log(level.upper(), "WebGCS", message)
        
        # Also print to console for development
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level} | {message}")
        
    except Exception as e:
        # Fallback to basic logging if high-performance logger fails
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        params_str = f", Params: {params}" if params else ""
        details_str = f" - {details}" if details else ""
        print(f"[{timestamp}] {level} | {command_name}{params_str}{details_str}")
        print(f"[{timestamp}] WARNING | Logging system error: {e}")

def set_drone_state_changed():
    """Mark drone state as changed for telemetry updates"""
    global drone_state_changed
    drone_state_changed = True

# Flask Routes
@app.route('/')
def index():
    """Main WebGCS interface page"""
    return render_template('index.html', version="Drone Control Interface v2.0")

@app.route('/health')
def health():
    """Health check endpoint"""
    with drone_state_lock:
        return jsonify({
            "status": "healthy",
            "drone_connected": drone_state.get("connected", False),
            "timestamp": time.time()
        })

@app.route('/static/<path:path>')
def send_static(path):
    """Static file serving"""
    return send_from_directory('static', path)

@app.route('/mavlink_dump')
def mavlink_dump():
    """MAVLink message dump page for debugging"""
    return render_template('mavlink_dump.html', version="WebGCS MAVLink Dump")

# SocketIO Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid if request else 'unknown'
    print(f"*** CONNECT EVENT RECEIVED *** Client connected: {client_id}")
    log_command_action("CLIENT_CONNECTED", details=f"Client ID: {client_id}")
    
    # Send initial telemetry to newly connected client
    with drone_state_lock:
        emit('telemetry_update', drone_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid if request else 'unknown'
    print(f"Client disconnected: {client_id}")
    log_command_action("CLIENT_DISCONNECTED", details=f"Client ID: {client_id}")

@socketio.on('flight_command')
def handle_flight_command(data):
    """Handle flight command from web client"""
    client_id = request.sid if request else 'unknown'
    command = data.get('command', 'UNKNOWN')
    params = data.get('params', {})
    
    print(f"Flight command received from {client_id}: {command} {params}")
    log_command_action("FLIGHT_COMMAND_RECEIVED", 
                      params={'command': command, 'params': params},
                      details=f"Client: {client_id}")
    
    try:
        # Get MAVLink connection
        mavlink_conn = get_mavlink_connection()
        
        if not mavlink_conn:
            result = {
                'success': False,
                'command': command,
                'error': 'No MAVLink connection available',
                'timestamp': time.time()
            }
        else:
            # Process the flight command
            result = process_flight_command(data, mavlink_conn, log_command_action)
        
        # Send result back to client
        emit('command_result', result)
        
        # Log the result
        status = "SUCCESS" if result.get('success') else "FAILED"
        log_command_action(f"FLIGHT_COMMAND_{status}",
                          params={'command': command},
                          details=f"Result: {result}")
        
    except Exception as e:
        error_result = {
            'success': False,
            'command': command,
            'error': f'Command processing error: {e}',
            'timestamp': time.time()
        }
        emit('command_result', error_result)
        
        log_command_action("FLIGHT_COMMAND_ERROR",
                          params={'command': command},
                          details=f"Error: {e}")

@socketio.on('connect_drone')
def handle_connect_drone(data):
    """Handle drone connection request from web interface"""
    client_id = request.sid if request else 'unknown'
    ip = data.get('ip', '192.168.193.235')
    port = data.get('port', 5678)
    
    connection_string = f"tcp:{ip}:{port}"
    print(f"Drone connection request from {client_id}: {connection_string}")
    
    log_command_action("DRONE_CONNECT_REQUEST", 
                      params={'ip': ip, 'port': port},
                      details=f"Client: {client_id}, Connection: {connection_string}")
    
    try:
        # Use existing connect_mavlink function with callbacks
        connect_mavlink(drone_state, drone_state_lock, connection_string, set_drone_state_changed, socketio)
        
        # Send immediate status update
        emit('connection_status', {
            'status': 'connecting',
            'message': f'Attempting to connect to {connection_string}...',
            'timestamp': time.time()
        })
        
        log_command_action("DRONE_CONNECT_INITIATED", 
                          details=f"Connection attempt started: {connection_string}")
        
    except Exception as e:
        emit('connection_status', {
            'status': 'error', 
            'message': f'Connection failed: {e}',
            'timestamp': time.time()
        })
        
        log_command_action("DRONE_CONNECT_ERROR",
                          details=f"Connection error: {e}")

@socketio.on('test_event')
def handle_test_event():
    """Test SocketIO event handler"""
    print("*** TEST EVENT RECEIVED ***")
    emit('test_response', {'message': 'Test event received'})

@socketio.on('disconnect_drone')
def handle_disconnect_drone():
    """Handle drone disconnection request from web interface"""
    client_id = request.sid if request else 'unknown'
    print(f"*** DISCONNECT EVENT RECEIVED *** from client {client_id}")
    print(f"Current drone connection state: {drone_state.get('connected', False)}")
    
    log_command_action("DRONE_DISCONNECT_REQUEST", details=f"Client: {client_id}")
    
    try:
        # Actually disconnect from MAVLink drone
        disconnect_mavlink()
        
        # Update state
        with drone_state_lock:
            drone_state['connected'] = False
        
        emit('connection_status', {
            'status': 'disconnected',
            'message': 'Disconnected from drone',
            'timestamp': time.time()
        })
        
        log_command_action("DRONE_DISCONNECTED", details="Drone connection terminated")
        
    except Exception as e:
        log_command_action("DRONE_DISCONNECT_ERROR", details=f"Disconnect error: {e}")
        print(f"Exception in disconnect handler: {e}")

print("Event handlers registered!")
print("Disconnect handler defined!")

# Telemetry Update Thread
_telemetry_thread = None

def telemetry_update_thread():
    """Send periodic telemetry updates to web clients"""
    global drone_state_changed
    
    while True:
        try:
            if drone_state_changed:
                with drone_state_lock:
                    socketio.emit('telemetry_update', drone_state)
                    drone_state_changed = False
            
            time.sleep(TELEMETRY_UPDATE_INTERVAL)
            
        except Exception as e:
            print(f"Telemetry update error: {e}")
            time.sleep(1)

def start_telemetry_thread():
    """Start telemetry update thread if not already running"""
    global _telemetry_thread
    
    if _telemetry_thread is None or not _telemetry_thread.is_alive():
        _telemetry_thread = threading.Thread(target=telemetry_update_thread, daemon=True)
        _telemetry_thread.start()
        print("Telemetry update thread started")

if __name__ == '__main__':
    print(f"Starting WebGCS server on {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    
    # Initialize high-performance logging system
    try:
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'webgcs.log')
        
        setup_logger(
            buffer_size=50000,
            log_level="INFO",
            enable_file_output=True,
            log_file_path=log_file,
            max_file_size_mb=10,
            max_log_files=5
        )
        print("High-performance logging system initialized")
        
    except Exception as e:
        print(f"Warning: Could not initialize high-performance logging: {e}")
        print("Falling back to basic console logging")
    
    # Start telemetry update thread
    start_telemetry_thread()
    
    # Start Flask-SocketIO server
    try:
        socketio.run(
            app,
            host=WEB_SERVER_HOST,
            port=WEB_SERVER_PORT,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True  # Allow for development/testing
        )
    except Exception as e:
        print(f"Server startup failed: {e}")
        sys.exit(1)
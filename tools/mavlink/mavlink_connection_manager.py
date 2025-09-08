"""
MAVLink Connection Manager
Handles MAVLink protocol connections and lifecycle management

Implements minimum functionality to pass TEST-001: Basic Connection Test
"""
from pymavlink import mavutil
import time
import threading
from mavlink_message_processor import process_heartbeat, process_global_position_int

# Module-level state
mavlink_connection_instance = None
last_heartbeat_time = 0
connection_lock = threading.Lock()
message_reading_thread = None
_message_thread_running = False


def connect_mavlink(drone_state, drone_state_lock, connection_string, set_state_changed_callback=None, socketio_instance=None):
    """
    Establishes MAVLink connection to specified endpoint
    
    Args:
        drone_state: Shared state dictionary
        drone_state_lock: Threading lock for drone_state
        connection_string: MAVLink connection string (e.g., "tcp:192.168.193.235:5678")
        set_state_changed_callback: Callback to mark state as changed for telemetry updates
        socketio_instance: SocketIO instance for broadcasting
    """
    global mavlink_connection_instance, last_heartbeat_time
    
    print(f"Connecting to MAVLink endpoint: {connection_string}")
    
    with connection_lock:
        try:
            # Create MAVLink connection with timeout
            mavlink_connection_instance = mavutil.mavlink_connection(
                connection_string,
                source_system=255,  # Ground Control Station ID
                source_component=0,
                timeout=3.0  # Connection timeout
            )
            
            print("MAVLink connection object created, waiting for target system...")
            
            # Wait for target system to be identified
            start_time = time.time()
            while time.time() - start_time < 3.0:  # 3 second timeout for target system
                # Check for incoming messages to establish target system
                try:
                    msg = mavlink_connection_instance.recv_match(timeout=0.5)
                    if msg:
                        print(f"Received message: {msg.get_type()}")
                        # Force target system identification on first message
                        if not hasattr(mavlink_connection_instance, 'target_system') or mavlink_connection_instance.target_system == 0:
                            mavlink_connection_instance.target_system = msg.get_srcSystem()
                            mavlink_connection_instance.target_component = msg.get_srcComponent()
                        
                        if hasattr(mavlink_connection_instance, 'target_system') and mavlink_connection_instance.target_system > 0:
                            print(f"Target system identified: {mavlink_connection_instance.target_system}")
                            
                            with drone_state_lock:
                                drone_state['connected'] = True
                                drone_state['system_id'] = mavlink_connection_instance.target_system
                            
                            last_heartbeat_time = time.time()
                            
                            # Notify frontend of successful connection
                            if socketio_instance:
                                socketio_instance.emit('connection_status', {
                                    'status': 'connected',
                                    'message': f'Connected to drone (System {mavlink_connection_instance.target_system})',
                                    'system_id': mavlink_connection_instance.target_system,
                                    'timestamp': time.time()
                                })
                            
                            # Start message reading thread
                            if set_state_changed_callback and socketio_instance:
                                start_message_reading_thread(drone_state, drone_state_lock, set_state_changed_callback, socketio_instance)
                            
                            return
                except:
                    pass
                
                time.sleep(0.1)
            
            print("Warning: Target system not identified within timeout")
            # Emit timeout error
            if socketio_instance:
                socketio_instance.emit('connection_status', {
                    'status': 'error',
                    'message': 'Connection timeout - no response from drone',
                    'timestamp': time.time()
                })
            
        except Exception as e:
            print(f"Connection failed: {e}")
            mavlink_connection_instance = None
            with drone_state_lock:
                drone_state['connected'] = False
            
            # Emit connection error
            if socketio_instance:
                socketio_instance.emit('connection_status', {
                    'status': 'error',
                    'message': f'Connection failed: {str(e)}',
                    'timestamp': time.time()
                })


def get_mavlink_connection():
    """Returns the current MAVLink connection instance"""
    return mavlink_connection_instance


def get_last_heartbeat_time():
    """Returns timestamp of last received heartbeat"""
    return last_heartbeat_time


def is_connected():
    """Check if MAVLink connection is active"""
    global mavlink_connection_instance
    return mavlink_connection_instance is not None


def disconnect_mavlink(drone_state, drone_state_lock, socketio_instance=None):
    """
    Disconnect from MAVLink endpoint and clean up resources
    """
    global mavlink_connection_instance, _message_thread_running
    
    print("Disconnecting from MAVLink endpoint...")
    
    # Stop message reading thread
    _message_thread_running = False
    
    with connection_lock:
        # Close connection
        if mavlink_connection_instance:
            try:
                mavlink_connection_instance.close()
            except:
                pass  # Ignore close errors
            mavlink_connection_instance = None
        
        # Update state
        with drone_state_lock:
            drone_state['connected'] = False
            drone_state['system_id'] = 0
        
        # Notify frontend
        if socketio_instance:
            socketio_instance.emit('connection_status', {
                'status': 'disconnected',
                'message': 'Disconnected from drone',
                'timestamp': time.time()
            })
    
    print("MAVLink disconnection complete")


def mavlink_message_reading_thread(drone_state, drone_state_lock, set_state_changed_callback, socketio_instance):
    """
    Continuous MAVLink message reading thread
    Processes HEARTBEAT and other messages to update drone state
    """
    global _message_thread_running, mavlink_connection_instance, last_heartbeat_time
    
    _message_thread_running = True
    print("MAVLink message reading thread started")
    
    while _message_thread_running and mavlink_connection_instance:
        try:
            # Read message with timeout
            msg = mavlink_connection_instance.recv_match(timeout=1.0)
            
            if msg:
                msg_type = msg.get_type()
                state_changed = False
                
                # Process different message types
                if msg_type == 'HEARTBEAT':
                    last_heartbeat_time = time.time()
                    state_changed = process_heartbeat(
                        msg, drone_state, drone_state_lock, mavlink_connection_instance,
                        None, socketio_instance  # log_cmd_action_cb, sio_instance
                    )
                    
                elif msg_type == 'GLOBAL_POSITION_INT':
                    state_changed = process_global_position_int(
                        msg, drone_state, drone_state_lock, mavlink_connection_instance,
                        None, socketio_instance  # log_cmd_action_cb, sio_instance
                    )
                
                # Notify main thread that state changed for telemetry updates
                if state_changed and set_state_changed_callback:
                    set_state_changed_callback()
                    
        except Exception as e:
            print(f"Message reading error: {e}")
            time.sleep(0.1)
    
    print("MAVLink message reading thread stopped")


def start_message_reading_thread(drone_state, drone_state_lock, set_state_changed_callback, socketio_instance):
    """Start the MAVLink message reading thread"""
    global message_reading_thread, _message_thread_running
    
    if message_reading_thread is None or not message_reading_thread.is_alive():
        message_reading_thread = threading.Thread(
            target=mavlink_message_reading_thread,
            args=(drone_state, drone_state_lock, set_state_changed_callback, socketio_instance),
            daemon=True
        )
        message_reading_thread.start()


def stop_message_reading_thread():
    """Stop the MAVLink message reading thread"""
    global _message_thread_running
    _message_thread_running = False


def disconnect_mavlink():
    """Disconnect and clean up MAVLink connection"""
    global mavlink_connection_instance, last_heartbeat_time
    
    # Stop message reading thread
    stop_message_reading_thread()
    
    with connection_lock:
        if mavlink_connection_instance:
            try:
                mavlink_connection_instance.close()
            except:
                pass
            mavlink_connection_instance = None
            last_heartbeat_time = 0
            print("MAVLink connection disconnected and cleaned up")
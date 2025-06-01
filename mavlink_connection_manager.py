import time
import threading
import collections
from pymavlink import mavutil
from gevent.event import Event
import inspect
import gevent # For gevent.sleep

# Import configuration constants
from config import AP_CUSTOM_MODES

# Import from our own modules
from mavlink_message_processor import (
    process_heartbeat,
    process_global_position_int,
    process_command_ack,
    process_vfr_hud,
    process_sys_status,
    process_gps_raw_int,
    process_attitude,
    process_home_position,
    process_statustext,
    process_mission_current
)

# Module-level state for MAVLink connection
mavlink_connection_instance = None
last_heartbeat_time_instance = 0
data_streams_requested_instance = False
pending_commands_instance = collections.OrderedDict() # Stores cmd_id: timestamp
connection_event_instance = Event() # Used to signal connection status

# Initialize feature callbacks dictionary
feature_callbacks = {}

# Dictionary mapping MAVLink message types to their handler functions
MAVLINK_MESSAGE_HANDLERS = {
    'HEARTBEAT': process_heartbeat,
    'GLOBAL_POSITION_INT': process_global_position_int,
    'COMMAND_ACK': process_command_ack,
    'VFR_HUD': process_vfr_hud,
    'SYS_STATUS': process_sys_status,
    'GPS_RAW_INT': process_gps_raw_int,
    'ATTITUDE': process_attitude,
    'HOME_POSITION': process_home_position,
    'STATUSTEXT': process_statustext,
    'MISSION_CURRENT': process_mission_current,
    # Add other message types and their handlers here
}

def get_mavlink_connection():
    """Returns the current MAVLink connection instance."""
    global mavlink_connection_instance
    return mavlink_connection_instance

def get_connection_event():
    """Returns the gevent Event for connection status."""
    global connection_event_instance
    return connection_event_instance

def add_pending_command(command_id):
    """Adds a command to the pending commands dictionary."""
    global pending_commands_instance
    pending_commands_instance[command_id] = time.time()

def connect_mavlink(drone_state, drone_state_lock, mavlink_connection_string_config):
    """Establishes a new MAVLink connection object and resets associated state.
    The caller is responsible for closing any pre-existing connection instance if needed.
    """
    global mavlink_connection_instance, data_streams_requested_instance, pending_commands_instance, connection_event_instance
    
    print(f"Attempting to create new MAVLink connection to: {mavlink_connection_string_config}")
    # Note: mavlink_connection_instance should be None when this is called,
    # or the caller should have handled closing the old one.

    # Reset relevant state for a new connection attempt
    with drone_state_lock:
        drone_state['connected'] = False
        drone_state['armed'] = False
        drone_state['ekf_status_report'] = 'INIT'
        # Add other relevant state resets if necessary
    data_streams_requested_instance = False
    pending_commands_instance.clear()
    connection_event_instance.clear()

    try:
        print(f"Creating MAVLink connection with simplified parameters...")
        # Create the MAVLink connection with simplified settings (like simple_monitor.py)
        mavlink_connection_instance = mavutil.mavlink_connection(
            mavlink_connection_string_config,
            autoreconnect=True,  # Enable auto-reconnect for robustness
            source_system=255,   # Use default source system ID
            source_component=0   # Use default source component ID
            # Removed retries and timeout to match simple_monitor.py approach
        )
        
        print(f"MAVLink connection object created: {mavlink_connection_string_config}")
        print("Waiting for heartbeat to confirm connection...")
        
        # Wait for heartbeat to confirm connection is working
        # Using a longer timeout to ensure we get a heartbeat
        msg = mavlink_connection_instance.recv_match(type='HEARTBEAT', blocking=True, timeout=15)
        if not msg:
            print("No heartbeat received within timeout period, connection not confirmed")
            mavlink_connection_instance.close()
            mavlink_connection_instance = None
            return False
        
        print(f"Received initial heartbeat from system {msg.get_srcSystem()}, confirming connection")
        
        # Extract mode information from heartbeat
        custom_mode = msg.custom_mode
        custom_mode_str = "UNKNOWN"
        for mode_name, mode_id in AP_CUSTOM_MODES.items():
            if mode_id == custom_mode:
                custom_mode_str = mode_name
                break
        
        # Check if armed
        armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        armed_str = "ARMED" if armed else "DISARMED"
        
        print(f"Drone is in {custom_mode_str} mode and is {armed_str}")
        
        # Set target system based on the received heartbeat
        mavlink_connection_instance.target_system = msg.get_srcSystem()
        mavlink_connection_instance.target_component = msg.get_srcComponent()
        print(f"Set target system to {mavlink_connection_instance.target_system}, component {mavlink_connection_instance.target_component}")
        
        # Update drone state to connected and set initial mode and armed status
        with drone_state_lock:
            drone_state['connected'] = True
            drone_state['was_just_connected_by_heartbeat'] = True
            drone_state['mode'] = custom_mode_str
            drone_state['armed'] = armed
            drone_state['system_status'] = msg.system_status
        
        connection_event_instance.set() # Signal that connection is successful
        return True
    except Exception as e:
        print(f"MAVLink connection error: {e}")
        if mavlink_connection_instance:
            try:
                mavlink_connection_instance.close()
            except:
                pass
        mavlink_connection_instance = None
        return False

def request_data_streams(req_rate_hz_config, home_position_is_known):
    """Requests necessary data streams from the flight controller using MAV_CMD_SET_MESSAGE_INTERVAL."""
    global data_streams_requested_instance, mavlink_connection_instance
    if not mavlink_connection_instance or not mavlink_connection_instance.target_system:
        print("No MAVLink connection or target system to request streams.")
        return

    print(f"Requesting data streams at {req_rate_hz_config} Hz...")
    target_sys = mavlink_connection_instance.target_system
    target_comp = mavlink_connection_instance.target_component

    # Define messages and their desired rates (restored to normal operation)
    messages_to_request = [
        (1, 'HEARTBEAT'),           # MAV_MSG_ID_HEARTBEAT
        (24, 'GPS_RAW_INT'),        # MAV_MSG_ID_GPS_RAW_INT  
        (33, 'GLOBAL_POSITION_INT'), # MAV_MSG_ID_GLOBAL_POSITION_INT
        (30, 'ATTITUDE'),           # MAV_MSG_ID_ATTITUDE
        (74, 'VFR_HUD'),            # MAV_MSG_ID_VFR_HUD
        (242, 'HOME_POSITION'),     # MAV_MSG_ID_HOME_POSITION
        (27, 'RAW_IMU'),            # MAV_MSG_ID_RAW_IMU
        (116, 'SCALED_PRESSURE'),   # MAV_MSG_ID_SCALED_PRESSURE
        (129, 'SCALED_PRESSURE2'),  # MAV_MSG_ID_SCALED_PRESSURE2
        (29, 'SCALED_PRESSURE3'),   # MAV_MSG_ID_SCALED_PRESSURE3
        (137, 'TERRAIN_REPORT'),    # MAV_MSG_ID_TERRAIN_REPORT
        (65, 'RC_CHANNELS'),        # MAV_MSG_ID_RC_CHANNELS
    ]

    # Send MAV_CMD_SET_MESSAGE_INTERVAL for each message type
    interval_us = int(1_000_000 / req_rate_hz_config)  # Convert Hz to microseconds
    
    for msg_id, msg_name in messages_to_request:
        try:
            print(f"  Requesting {msg_name} (ID: {msg_id}) at {req_rate_hz_config} Hz (Interval: {interval_us} us)")
            mavlink_connection_instance.mav.command_long_send(
                target_sys,                    # target_system
                target_comp,                   # target_component  
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, # command
                0,                             # confirmation
                msg_id,                        # param1: message_id
                interval_us,                   # param2: interval in microseconds
                0, 0, 0, 0, 0                  # param3-7: unused
            )
        except Exception as e:
            print(f"  Error requesting {msg_name}: {e}")

    print(f"Data stream requests sent at {req_rate_hz_config} Hz!")
    data_streams_requested_instance = True

def check_pending_command_timeouts(sio, command_ack_timeout_config, log_function):
    """Checks for timed-out MAVLink commands and emits SocketIO events."""
    global pending_commands_instance
    now = time.time()
    timed_out_commands = []
    for cmd_id, value in list(pending_commands_instance.items()): # Iterate over a copy
        # Handle both float timestamps and dict values with timestamp keys
        if isinstance(value, dict):
            timestamp = value.get('timestamp', 0)
        else:
            timestamp = value  # Assume it's a float timestamp
        
        if now - timestamp > command_ack_timeout_config:
            details = f"Command {cmd_id} (e.g., MAV_CMD_DO_SET_MODE) timed out after {command_ack_timeout_config}s."
            print(f"COMMAND TIMEOUT: {details}")
            if log_function:
                log_function("TIMEOUT", {"command_id": cmd_id}, details, level="WARN")
            sio.emit('command_timeout', {'command_id': cmd_id, 'status': 'TIMEOUT', 'message': details})
            timed_out_commands.append(cmd_id)

    for cmd_id in timed_out_commands:
        pending_commands_instance.pop(cmd_id, None)

def mavlink_receive_loop_runner(
    mavlink_connection_string_config,  # From app.py: MAVLINK_CONNECTION_STRING
    drone_state,                       # From app.py: drone_state (dict)
    drone_state_lock,                  # From app.py: drone_state_lock (Lock object)
    passed_pending_commands,           # From app.py: pending_commands (dict)
    passed_connection_event,           # From app.py: get_connection_event()
    log_function,                      # From app.py: log_command_action
    sio,                               # From app.py: socketio instance
    notify_state_changed_cb,           # From app.py: set_drone_state_changed_flag
    app_shared_state,                  # From app.py: app_shared_state (dict)
    execute_fence_request_cb,          # From app.py: _execute_fence_request
    execute_mission_request_cb,        # From app.py: _execute_mission_request
    heartbeat_timeout_config,          # From app.py: HEARTBEAT_TIMEOUT
    request_stream_rate_hz_config,     # From app.py: REQUEST_STREAM_RATE_HZ
    command_ack_timeout_config,        # From app.py: COMMAND_ACK_TIMEOUT
    heartbeat_log_cb=None              # Optional callback for custom heartbeat logging
):
    """Main loop for receiving MAVLink messages and managing connection state."""
    global mavlink_connection_instance, last_heartbeat_time_instance, data_streams_requested_instance, connection_event_instance, pending_commands_instance, feature_callbacks
    # Assign the passed pending_commands and connection_event to the module's global instances
    pending_commands_instance = passed_pending_commands
    connection_event_instance = passed_connection_event
    
    # Initialize feature callbacks
    feature_callbacks = {
        'EXECUTE_FENCE_REQUEST': execute_fence_request_cb,
        'EXECUTE_MISSION_REQUEST': execute_mission_request_cb
    }

    print("MAVLink receive loop thread started.")
    while True:
        if not mavlink_connection_instance: # Primary check: is there a connection object at all?
            # Attempt to create a new connection object
            if not connect_mavlink(drone_state, drone_state_lock, mavlink_connection_string_config):
                print("MAVLink connection object creation failed, retrying in 5s...")
                gevent.sleep(5) # Use gevent.sleep
                continue
            # If connect_mavlink was successful, mavlink_connection_instance is now set.
            # data_streams_requested_instance is reset within connect_mavlink.
            # The loop will then proceed to check for target_system and request streams if needed.

        # Ensure streams are requested if connected
        if mavlink_connection_instance and mavlink_connection_instance.target_system != 0 and not data_streams_requested_instance:
            home_is_known = drone_state.get('home_lat') is not None and drone_state.get('home_lon') is not None
            request_data_streams(request_stream_rate_hz_config, home_is_known)

        # Check for heartbeat timeout only if a heartbeat has been received at least once
        if last_heartbeat_time_instance != 0 and (time.time() - last_heartbeat_time_instance > heartbeat_timeout_config):
            print(f"Heartbeat timeout (>{heartbeat_timeout_config}s). Drone disconnected.")
            with drone_state_lock:
                drone_state['connected'] = False
            if mavlink_connection_instance:
                mavlink_connection_instance.close()
            mavlink_connection_instance = None
            last_heartbeat_time_instance = 0
            data_streams_requested_instance = False
            connection_event_instance.clear()
            sio.emit('drone_disconnected', {'reason': 'Heartbeat timeout'})
            continue # Attempt to reconnect

        check_pending_command_timeouts(sio, command_ack_timeout_config, log_function)

        # Execute pending fence request if flag is set
        if app_shared_state.get('fence_request_pending', False):
            if callable(feature_callbacks.get('EXECUTE_FENCE_REQUEST')):
                try:
                    log_function("MAVLINK_LOOP_EVENT", details="Executing pending fence request from mavlink_receive_loop_runner.")
                    feature_callbacks['EXECUTE_FENCE_REQUEST']()
                except Exception as e:
                    log_function("EXECUTE_FENCE_REQUEST_ERROR", details=f"Error in EXECUTE_FENCE_REQUEST: {e}", level="ERROR")
                    # Optionally reset flag here if appropriate, or let the handler do it
                    # app_shared_state['fence_request_pending'] = False 
            else:
                log_function("MAVLINK_LOOP_WARNING", details="'EXECUTE_FENCE_REQUEST' callback not found or not callable.", level="WARNING")

        # Execute pending mission request if flag is set
        if app_shared_state.get('mission_request_pending', False):
            if callable(feature_callbacks.get('EXECUTE_MISSION_REQUEST')):
                try:
                    log_function("MAVLINK_LOOP_EVENT", details="Executing pending mission request from mavlink_receive_loop_runner.")
                    feature_callbacks['EXECUTE_MISSION_REQUEST']()
                except Exception as e:
                    log_function("EXECUTE_MISSION_REQUEST_ERROR", details=f"Error in EXECUTE_MISSION_REQUEST: {e}", level="ERROR")
                    # Optionally reset flag here
                    # app_shared_state['mission_request_pending'] = False
            else:
                log_function("MAVLINK_LOOP_WARNING", details="'EXECUTE_MISSION_REQUEST' callback not found or not callable.", level="WARNING")


        drone_state_changed_iteration = False # Reset for this iteration
        try:
            if not mavlink_connection_instance:
                gevent.sleep(0.1) # Wait if connection is temporarily None
                continue
            
            # OPTIMIZED MESSAGE PROCESSING: Handle both heartbeats and other messages efficiently
            receive_start_time = time.time()
            
            # Check for any message (including heartbeats and telemetry)
            # Process all available messages in the buffer to minimize latency
            messages_processed_this_cycle = 0
            while True:
                msg = mavlink_connection_instance.recv_msg()  # Non-blocking read
                if not msg:
                    break # No more messages in the buffer for now
                
                messages_processed_this_cycle += 1
                msg_type = msg.get_type()
                print(f"[RECV-LOOP-DEBUG] Received MAVLink MSG ID: {msg.get_msgId()}, Type: {msg_type}") # Cascade: Log every received message
                current_time_unix = time.time() # Capture time immediately after getting msg_type message
                # print(f"[LOOP_TIMING] Received {msg_type} at {current_msg_receive_time:.4f}")

                # PRIORITY: Process heartbeats immediately
                if msg_type == 'HEARTBEAT':
                    hb_call_start_time = time.time()
                    heartbeat_changed = process_heartbeat(
                        msg, drone_state, drone_state_lock, 
                        mavlink_connection_instance, log_function, sio, heartbeat_log_cb
                    )
                    hb_call_end_time = time.time()
                    # print(f"[LOOP_TIMING] process_heartbeat for {msg_type} took {hb_call_end_time - hb_call_start_time:.4f}s")
                    if heartbeat_changed:
                        drone_state_changed_iteration = True
                else: # Not a HEARTBEAT
                    print(f"[HANDLER-DISPATCH] Processing non-HEARTBEAT MSG ID: {msg.get_msgId()}, Type: {msg_type}") # Cascade Debug
                    handler = MAVLINK_MESSAGE_HANDLERS.get(msg_type)
                    if handler:
                        print(f"[HANDLER-DISPATCH] Found handler: {handler.__name__} for {msg_type}. Preparing to call.") # Cascade Debug
                        try:
                            handler_kwargs = {
                                'msg': msg,
                                'drone_state': drone_state,
                                'drone_state_lock': drone_state_lock,
                                'mavlink_connection_instance': mavlink_connection_instance, # Full instance
                                'mav_connection': mavlink_connection_instance.mav, # .mav attribute for pymavlink calls
                                'mavlink_conn': mavlink_connection_instance,  # Pass the full instance
                                'log_function': log_function, # Passed into mavlink_receive_loop_runner
                                'log_cmd_action_cb': log_function, # Added for handlers expecting this name
                                'sio': sio, # Passed into mavlink_receive_loop_runner
                                'sio_instance': sio, # Added for handlers expecting this name
                                'target_sys': mavlink_connection_instance.target_system, # System ID from connection
                                'target_comp': mavlink_connection_instance.target_component, # Component ID from connection
                                'config': app_shared_state  # Use app_shared_state for the 'config' key
                            }
                            # Filter kwargs to only those accepted by the handler
                            sig = inspect.signature(handler)
                            valid_kwargs = {k: v for k, v in handler_kwargs.items() if k in sig.parameters}
                            
                            print(f"[HANDLER-DISPATCH] Calling handler {handler.__name__} with keys: {list(valid_kwargs.keys())}") # Cascade Debug
                            handler_changed_state = handler(**valid_kwargs)
                            print(f"[HANDLER-DISPATCH] Handler {handler.__name__} for {msg_type} returned: {handler_changed_state}") # Cascade Debug
                            if handler_changed_state:
                                drone_state_changed_iteration = True # Update flag if handler reported change
                        except Exception as e:
                            print(f"[HANDLER-DISPATCH-ERROR] Error processing message type {msg_type} with handler {handler.__name__}: {e}") # Cascade: Modified for clarity
                            import traceback
                            traceback.print_exc() # Cascade: Add full traceback for errors
                    else:
                        print(f"[HANDLER-DISPATCH] No handler found for MSG ID: {msg.get_msgId()}, Type: {msg_type}") # Cascade Debug
                
                # Handle message-specific post-processing
                if msg_type == 'HEARTBEAT':
                    last_heartbeat_time_instance = time.time() # Update with the time of the latest heartbeat
                    if drone_state.get('was_just_connected_by_heartbeat', False):
                        log_function("MAVLINK_EVENT", details="Drone connected (heartbeat processed).")
                        with drone_state_lock:
                            drone_state.pop('was_just_connected_by_heartbeat', None)
                    connection_event_instance.set()
                elif msg_type == 'COMMAND_ACK':
                    command_id_from_ack = msg.command
                    if command_id_from_ack in pending_commands_instance:
                        pending_commands_instance.pop(command_id_from_ack, None)
            
            # If no messages were processed in this cycle, sleep briefly to yield
            if messages_processed_this_cycle == 0:
                gevent.sleep(0.005)  # Sleep for 5ms (adjustable)

                # Existing debug print for no messages (runs every 5s if continuously no messages)
                if not hasattr(mavlink_receive_loop_runner, 'last_message_debug_time'):
                    mavlink_receive_loop_runner.last_message_debug_time = 0
                current_time = time.time()
                if current_time - mavlink_receive_loop_runner.last_message_debug_time > 5:  # Debug every 5 seconds
                    print(f"[DEBUG] No messages (non-blocking read) this iteration at {current_time:.3f}")
                    mavlink_receive_loop_runner.last_message_debug_time = current_time

            # If drone_state was changed by any message handler in this iteration, notify app.py
            if drone_state_changed_iteration:
                if callable(notify_state_changed_cb):
                    notify_state_changed_cb()

        except mavutil.mavlink.MAVError as e:
            log_function("MAVLINK_RECV_ERROR", details=f"MAVLink receive error: {e}", level="ERROR")
            if mavlink_connection_instance:
                mavlink_connection_instance.close()
            mavlink_connection_instance = None
            last_heartbeat_time_instance = 0
            data_streams_requested_instance = False
            connection_event_instance.clear()
            with drone_state_lock:
                drone_state['connected'] = False
            sio.emit('drone_disconnected', {'reason': 'MAVLink receive error'})
            gevent.sleep(1) # Wait a bit before trying to reconnect
            continue # To the start of the while loop to attempt reconnection
        except Exception as e:
            log_function("MAVLINK_LOOP_UNEXPECTED_ERROR", details=f"Unexpected error in MAVLink receive loop: {e}", level="CRITICAL")
            if mavlink_connection_instance:
                mavlink_connection_instance.close()
            mavlink_connection_instance = None
            last_heartbeat_time_instance = 0
            data_streams_requested_instance = False
            connection_event_instance.clear()
            with drone_state_lock:
                drone_state['connected'] = False
            sio.emit('drone_disconnected', {'reason': 'Unexpected loop error'})
            gevent.sleep(5) # Longer sleep for unexpected errors
            continue # To the start of the while loop
        except Exception as e:
            print(f"Error in MAVLink receive loop: {e}. Attempting to recover.")
            # import traceback
            # traceback.print_exc() # For detailed debugging
            if mavlink_connection_instance:
                try: mavlink_connection_instance.close()
                except: pass
            mavlink_connection_instance = None
            data_streams_requested_instance = False
            connection_event_instance.clear()
            with drone_state_lock:
                drone_state['connected'] = False
            sio.emit('drone_disconnected', {'reason': f'Receive loop error: {e}'})
            time.sleep(1) # Brief pause before attempting to reconnect
        
        # Add a small sleep to prevent 100% CPU usage and allow Flask server to process requests
        gevent.sleep(0.01)  # 10ms sleep to process messages frequently while keeping reasonable CPU usage

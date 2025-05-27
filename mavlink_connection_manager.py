import time
import threading
import collections
from pymavlink import mavutil
from gevent.event import Event
import gevent # For gevent.sleep

# Import from our own modules
from mavlink_message_processor import process_heartbeat

# Module-level state for MAVLink connection
mavlink_connection_instance = None
last_heartbeat_time_instance = 0
data_streams_requested_instance = False
pending_commands_instance = collections.OrderedDict() # Stores cmd_id: timestamp
connection_event_instance = Event() # Used to signal connection status

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
    
    print("Attempting to create new MAVLink connection object...")
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
        mavlink_connection_instance = mavutil.mavlink_connection(mavlink_connection_string_config)
        print(f"MAVLink connection established: {mavlink_connection_string_config}")
        connection_event_instance.set() # Signal that connection attempt was made (success or fail soon)
        return True
    except Exception as e:
        print(f"MAVLink connection error: {e}")
        mavlink_connection_instance = None
        return False

def request_data_streams(req_rate_hz_config, home_position_is_known):
    """Requests necessary data streams from the flight controller using MAV_CMD_SET_MESSAGE_INTERVAL."""
    global data_streams_requested_instance, mavlink_connection_instance
    if not mavlink_connection_instance or not mavlink_connection_instance.target_system:
        print("No MAVLink connection or target system to request streams.")
        return

    print(f"Requesting data streams (home known: {home_position_is_known})...")
    target_sys = mavlink_connection_instance.target_system
    target_comp = mavlink_connection_instance.target_component

    # Define messages and their desired rates in Hz
    # Use rates from config or sensible defaults if not all are in REQUEST_STREAM_RATE_HZ
    messages_to_request = {
        mavutil.mavlink.MAVLINK_MSG_ID_HEARTBEAT: 1,  # Already handled by ArduPilot, but good to ensure
        mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS: 1,
        mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT: 1, # Or GLOBAL_POSITION_INT at higher rate
        mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: req_rate_hz_config, # Higher rate for position
        mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE: req_rate_hz_config, # Higher rate for attitude
        mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD: req_rate_hz_config, # Contains relative altitude, ground/airspeed
        mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION: 0.2, # Request slowly until received
        # mavutil.mavlink.MAVLINK_MSG_ID_STATUSTEXT: 1, # For important messages - often event-driven
        # mavutil.mavlink.MAVLINK_MSG_ID_COMMAND_ACK: 5, # Ensure ACKs are streamed - event-driven, not streamed
        # Add other messages as needed, e.g.:
        # mavutil.mavlink.MAVLINK_MSG_ID_MISSION_CURRENT: 1,
        # mavutil.mavlink.MAVLINK_MSG_ID_RC_CHANNELS: 2, # If RC input display is needed
    }

    try:
        for msg_id, rate_hz in messages_to_request.items():
            interval_us = int(1e6 / rate_hz) if rate_hz > 0 else 0 # 0 to stop, -1 to leave unchanged
            
            # If home position is already known, stop requesting it (or set to very low rate)
            if msg_id == mavutil.mavlink.MAVLINK_MSG_ID_HOME_POSITION and home_position_is_known:
                interval_us = -1 # Set to -1 to leave rate unchanged (effectively stop if it was being requested)
                                 # Or set to 0 to explicitly stop: int(1e6 / 0.05) for once every 20s if you want to keep it very slow

            if interval_us != -1: # Send command if interval is not -1 (leave unchanged)
                print(f"  Requesting MSG ID {msg_id} at {rate_hz} Hz (Interval: {interval_us} us)")
                mavlink_connection_instance.mav.command_long_send(
                    target_sys, target_comp,
                    mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                    0, # Confirmation
                    msg_id,
                    interval_us,
                    0, 0, 0, 0, 0  # params 3-7 not used
                )
                gevent.sleep(0.05) # Small delay between requests, as per original app.py
        data_streams_requested_instance = True
        print("Data streams request sequence completed.")
    except Exception as e:
        print(f"Error requesting data streams: {e}")
        data_streams_requested_instance = False

def check_pending_command_timeouts(sio, command_ack_timeout_config, log_function):
    """Checks for timed-out MAVLink commands and emits SocketIO events."""
    global pending_commands_instance
    now = time.time()
    timed_out_commands = []
    for cmd_id, timestamp in list(pending_commands_instance.items()): # Iterate over a copy
        if now - timestamp > command_ack_timeout_config:
            details = f"Command {cmd_id} (e.g., MAV_CMD_DO_SET_MODE) timed out after {command_ack_timeout_config}s."
            print(f"COMMAND TIMEOUT: {details}")
            if log_function:
                log_function("TIMEOUT", {"command_id": cmd_id}, details, level="WARN")
            sio.emit('command_timeout', {'command_id': cmd_id, 'status': 'TIMEOUT', 'message': details})
            timed_out_commands.append(cmd_id)

    for cmd_id in timed_out_commands:
        pending_commands_instance.pop(cmd_id, None)

def mavlink_receive_loop_runner(drone_state, drone_state_lock, sio,
                                mavlink_connection_string_config, heartbeat_timeout_config,
                                request_stream_rate_hz_config, command_ack_timeout_config,
                                message_processor_callbacks, feature_callbacks, log_function):
    """Main loop for receiving MAVLink messages and managing connection state."""
    global mavlink_connection_instance, last_heartbeat_time_instance, data_streams_requested_instance, connection_event_instance, pending_commands_instance

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
        
        # Placeholders for complex feature execution (e.g., mission/fence downloads)
        # These would be called based on state flags set by their respective request handlers
        # if feature_callbacks.get('execute_fence_request_if_pending'):
        #     feature_callbacks['execute_fence_request_if_pending']()
        # if feature_callbacks.get('execute_mission_request_if_pending'):
        #     feature_callbacks['execute_mission_request_if_pending']()

        try:
            if not mavlink_connection_instance:
                gevent.sleep(0.1) # Wait if connection is temporarily None
                continue
            
            msg = mavlink_connection_instance.recv_match(blocking=False, timeout=0.05) # Short non-blocking timeout
            if not msg:
                gevent.sleep(0.01) # Minimal sleep if no message, to yield CPU
                continue

            msg_type = msg.get_type()

            # DEBUG: Log position-related messages (verbose, commented out as per user request)
            # if msg_type == 'GLOBAL_POSITION_INT':
            #     print(f"DEBUG: Received GLOBAL_POSITION_INT: lat={msg.lat}, lon={msg.lon}, alt={msg.alt}, relative_alt={msg.relative_alt}")
            # elif msg_type == 'GPS_RAW_INT':
            #     print(f"DEBUG: Received GPS_RAW_INT: lat={msg.lat}, lon={msg.lon}, alt={msg.alt}")

            # Update last_heartbeat_time for any HEARTBEAT message from the target system
            if msg.get_srcSystem() == mavlink_connection_instance.target_system and msg_type == 'HEARTBEAT':
                last_heartbeat_time_instance = time.time()
                # Explicitly mark connected on first valid heartbeat from target
                if not drone_state['connected']:
                    with drone_state_lock:
                        drone_state['connected'] = True
                    print("Drone formally connected (heartbeat received).")
                    sio.emit('drone_connected')

                # Call the dedicated HEARTBEAT processor
                # The log_function here is log_command_action from app.py
                drone_state_was_changed_by_heartbeat = process_heartbeat(
                    msg, 
                    drone_state, 
                    drone_state_lock, 
                    mavlink_connection_instance, 
                    log_function,  # This is log_command_action from app.py
                    sio
                )
                if drone_state_was_changed_by_heartbeat:
                    with drone_state_lock:
                        sio.emit('update_drone_state', dict(drone_state))

            # Handle other specific messages using callbacks from message_processor_callbacks
            elif msg_type in message_processor_callbacks: # Use elif to avoid double processing HEARTBEAT
                # Example: message_processor_callbacks[msg_type](msg, drone_state, drone_state_lock, mavlink_connection_instance, log_function, sio)
                # This part needs to be adapted based on how message_processor_callbacks is structured and used.
                # For now, we assume it's a dictionary of functions.
                if callable(message_processor_callbacks[msg_type]):
                    try:
                        changed = message_processor_callbacks[msg_type](msg, drone_state, drone_state_lock, mavlink_connection_instance, log_function, sio)
                        if changed:
                            # If the callback indicates a change, emit update_drone_state
                            with drone_state_lock:
                                sio.emit('update_drone_state', dict(drone_state))
                        
                        # If this was a COMMAND_ACK, remove it from pending commands
                        if msg_type == 'COMMAND_ACK':
                            command_id_from_ack = msg.command
                            if command_id_from_ack in pending_commands_instance:
                                # Use a try-except for cmd_name_for_log in case MAV_CMD enum isn't exhaustive or key is bad
                                try:
                                    cmd_name_for_log = mavutil.mavlink.enums['MAV_CMD'][command_id_from_ack].name
                                except KeyError:
                                    cmd_name_for_log = f'ID {command_id_from_ack}'
                                print(f"DEBUG: Removing command {cmd_name_for_log} (ID: {command_id_from_ack}) from pending_commands_instance due to ACK.")
                                del pending_commands_instance[command_id_from_ack]
                            # else: # Optional: Log if ACK received for a non-pending command
                            #     try:
                            #         cmd_name_for_log = mavutil.mavlink.enums['MAV_CMD'][command_id_from_ack].name
                            #     except KeyError:
                            #         cmd_name_for_log = f'ID {command_id_from_ack}'
                            #     print(f"DEBUG: Received ACK for {cmd_name_for_log} (ID: {command_id_from_ack}) which was not in pending_commands_instance.")
                                
                    except Exception as e:
                        print(f"Error processing message type {msg_type} via callback: {e}")
            
            elif msg_type in feature_callbacks: # For messages part of complex features like mission/fence downloads
                # Ensure the callback exists and is callable
                if callable(feature_callbacks[msg_type]):
                    try:
                        # The signature for feature_callbacks might be simpler, e.g., not needing log_function or full mavlink_conn
                        # Adjust as per the actual design of these callbacks
                        changed_by_feature = feature_callbacks[msg_type](msg, drone_state, drone_state_lock, sio, pending_commands_instance) # Example signature
                        if changed_by_feature:
                             with drone_state_lock:
                                sio.emit('update_drone_state', dict(drone_state))
                    except Exception as e:
                        print(f"Error processing message type {msg_type} via feature_callback: {e}")
            
            # Generic message emission for frontend logging/display (optional)
            # This could be too verbose for all messages.
            # sio.emit('mavlink_message', {'type': msg_type, 'data': msg.to_dict()})
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

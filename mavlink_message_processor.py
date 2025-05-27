"""
Handles processing of specific MAVLink messages.
"""
import time
from pymavlink import mavutil

# Import from our own modules
from config import AP_CUSTOM_MODES # ArduPilot specific
from mavlink_utils import (
    MAV_RESULT_STR, # Ensure MAV_RESULT_STR is imported
    MAV_TYPE_STR,
    MAV_AUTOPILOT_STR,
    MAV_STATE_STR,
    MAV_MODE_FLAG_ENUM
)

def process_heartbeat(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Process HEARTBEAT message with enhanced logging for mode changes.
    
    Args:
        msg: The MAVLink HEARTBEAT message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object (from mavlink_connection_manager).
        log_cmd_action_cb: Callback to the log_command_action function from app.py.
        sio_instance: The SocketIO instance for emitting events.
    
    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False

    with drone_state_lock:
        prev_mode = drone_state.get('mode', 'UNKNOWN')
        prev_armed = drone_state.get('armed', False)
        
        # Update drone state based on heartbeat
        # 'connected' is primarily set by mavlink_connection_manager upon receiving first heartbeat
        # but we can confirm it here too.
        drone_state['connected'] = True 
        drone_state['armed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        
        # Ensure we are processing heartbeat from the expected target system
        if mavlink_conn and msg.get_srcSystem() == mavlink_conn.target_system:
            custom_mode_str_list = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
            new_mode = custom_mode_str_list[0] if custom_mode_str_list else f'CUSTOM_MODE({msg.custom_mode})'
            drone_state['mode'] = new_mode
            
            # Log mode or armed state changes
            if new_mode != prev_mode:
                log_cmd_action_cb("MODE_CHANGE", None, f"Mode changed from {prev_mode} to {new_mode}")
                drone_state_changed_local = True
                
            if drone_state['armed'] != prev_armed:
                status = "ARMED" if drone_state['armed'] else "DISARMED"
                log_cmd_action_cb("ARM_STATUS", None, f"Vehicle {status}")
                drone_state_changed_local = True
        elif not mavlink_conn:
            print("Warning: mavlink_conn not available in process_heartbeat")

    # Emit event for UI animation - now sending generic mavlink_message
    if sio_instance and mavlink_conn and msg.get_srcSystem() == mavlink_conn.target_system: # Only emit for our drone
        sio_instance.emit('mavlink_message', msg.to_dict()) # Send the whole message dictionary

    # Determine if core state changed for the return value
    if drone_state.get('armed') != prev_armed or drone_state.get('mode') != prev_mode:
        drone_state_changed_local = True
    # If it wasn't changed by mode/arm status, it might have been set True earlier if other critical state changed.
    # However, for this function's contract with mavlink_connection_manager, only mode/arm changes are key for 'update_drone_state'.
    # The initial 'drone_state_changed_local = False' and updates within the lock cover this.

    return drone_state_changed_local

def process_global_position_int(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes GLOBAL_POSITION_INT message and updates drone_state.

    Args:
        msg: The MAVLink GLOBAL_POSITION_INT message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function.
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False
    if mavlink_conn and msg.get_srcSystem() == mavlink_conn.target_system:
        with drone_state_lock:
            # MAVLink GLOBAL_POSITION_INT:
            # lat, lon: Latitude and longitude (WGS84), in degrees * 1E7
            # alt: Altitude (AMSL), in meters * 1000 (positive for up)
            # relative_alt: Altitude above ground, in meters * 1000 (positive for up)
            # hdg: Vehicle heading (yaw angle), 0-35999 centi-degrees (0..359.99 degrees)
            #      0 = North, 90 = East. If unknown, set to: UINT16_MAX
            
            new_lat = msg.lat / 1e7
            new_lon = msg.lon / 1e7
            new_alt_msl = msg.alt / 1000.0
            new_alt_rel = msg.relative_alt / 1000.0
            # Use last known heading if current is unknown (UINT16_MAX)
            new_hdg = msg.hdg / 100.0 if msg.hdg != 65535 else drone_state.get('hdg', 0)

            # Check if any relevant value has changed to avoid unnecessary updates
            if (drone_state.get('lat') != new_lat or
                drone_state.get('lon') != new_lon or
                drone_state.get('alt_abs') != new_alt_msl or
                drone_state.get('alt_rel') != new_alt_rel or
                drone_state.get('hdg') != new_hdg):
                
                drone_state['lat'] = new_lat
                drone_state['lon'] = new_lon
                drone_state['alt_abs'] = new_alt_msl
                drone_state['alt_rel'] = new_alt_rel
                drone_state['hdg'] = new_hdg
                
                # print(f"DEBUG: Updated drone_state with GLOBAL_POSITION_INT: lat={new_lat}, lon={new_lon}, alt_rel={new_alt_rel}, hdg={new_hdg}")
                drone_state_changed_local = True
        
    return drone_state_changed_local

# Add other message processing functions here, e.g.:
# def process_sys_status(msg, drone_state, drone_state_lock, ...):
#     ...
# def process_gps_raw_int(msg, drone_state, drone_state_lock, ...):
#     ...

def process_command_ack(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Process and log COMMAND_ACK messages with enhanced details.
    This function is now part of mavlink_message_processor.
    Args:
        msg: The MAVLink COMMAND_ACK message object.
        drone_state: The shared dictionary holding drone state (not directly used by ACK processing but standard for processors).
        drone_state_lock: Threading lock for accessing drone_state (not directly used here).
        mavlink_conn: The MAVLink connection object (used for target system check if needed, and pending_commands).
        log_cmd_action_cb: Callback to the log_command_action function from app.py.
        sio_instance: The SocketIO instance for emitting events directly to the client.
    Returns:
        bool: False, as COMMAND_ACK itself doesn't typically change the core drone_state fields like lat/lon/mode.
              However, it provides feedback to the user.
    """
    print(f"DEBUG: process_command_ack received: {msg}") # Added for debugging

    cmd = msg.command
    result = msg.result
    
    # Get command name for logging
    # Ensure mavutil.mavlink.enums['MAV_CMD'] is accessible or pass it if not globally available
    cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name if cmd in mavutil.mavlink.enums['MAV_CMD'] else f'ID {cmd}'
    
    # Get result name (MAV_RESULT_STR needs to be imported or passed if not available)
    # Assuming MAV_RESULT_STR is available via mavlink_utils import in this module
    result_name = MAV_RESULT_STR.get(result, 'UNKNOWN')
    
    # Skip logging and emitting MAV_CMD_REQUEST_MESSAGE commands with UNKNOWN results
    # This logic about pending_commands needs to be handled by the caller (mavlink_connection_manager)
    # if cmd == mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE and result_name == 'UNKNOWN':
    #     # if mavlink_conn and cmd in mavlink_conn.pending_commands_instance: # Accessing pending_commands via mavlink_conn
    #     #     del mavlink_conn.pending_commands_instance[cmd]
    #     return False # No state change, no significant ACK to report
    
    explanation = "Command acknowledged with"
    level = "INFO"
    if result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
        explanation = "Command ACCEPTED by vehicle"
    elif result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
        explanation = "Command TEMPORARILY REJECTED - vehicle might be in wrong state"
        level = "WARNING"
    elif result == mavutil.mavlink.MAV_RESULT_DENIED:
        explanation = "Command DENIED - vehicle rejected the command"
        level = "ERROR"
    elif result == mavutil.mavlink.MAV_RESULT_UNSUPPORTED:
        explanation = "Command UNSUPPORTED - vehicle does not support this command"
        level = "ERROR"
    elif result == mavutil.mavlink.MAV_RESULT_FAILED:
        explanation = "Command FAILED during execution"
        level = "ERROR"
    elif result == mavutil.mavlink.MAV_RESULT_IN_PROGRESS:
        explanation = "Command accepted and IN PROGRESS"
    # The logic for 'UNKNOWN' result and command_ack_queue is complex and tied to mavlink_connection state
    # For now, simplifying this part. The original logic was:
    # else:
    #     if result_name == 'UNKNOWN' and mavlink_conn and len(mavlink_conn.mav.command_ack_queue) > 0:
    #         explanation = "Command ACCEPTED by vehicle (inferred from queue)"
    #     else:
    #         explanation = "Command response UNKNOWN"
    #         level = "WARNING"
    else: # Simplified else for now
        explanation = f"Command response: {result_name}"
        if result_name == 'UNKNOWN': level = "WARNING"

    display_result = result_name # Default display
    # More detailed display_result logic can be reinstated if needed
    if explanation != f"Command response: {result_name}": # If custom explanation was set
        display_result = f"{result_name} - {explanation}"

    log_cmd_action_cb(f"ACK_{cmd_name}", f"Result: {display_result} (Raw: {result})", explanation, level)
    
    # Removal from pending_commands should be handled by mavlink_connection_manager after this processor returns
    # if mavlink_conn and cmd in mavlink_conn.pending_commands_instance:
    #     del mavlink_conn.pending_commands_instance[cmd]
    
    # Emit to frontend using the passed sio_instance
    if sio_instance:
        ui_command_key = None
        # mavlink_conn is an instance of MavlinkConnectionManager
        # mavlink_conn.pending_commands refers to the global pending_commands dict from app.py
        if mavlink_conn and hasattr(mavlink_conn, 'pending_commands') and mavlink_conn.pending_commands:
            pending_command_info = mavlink_conn.pending_commands.get(cmd) # cmd is msg.command
            if pending_command_info:
                ui_command_key = pending_command_info.get('ui_command_name')

        sio_instance.emit('command_ack_received', {
            'command': cmd,  # MAVLink command ID (e.g., 176)
            'command_name': cmd_name,  # MAVLink command name string (e.g., "MAV_CMD_DO_SET_MODE")
            'ui_command_key': ui_command_key,  # UI command key (e.g., "SET_MODE", "ARM")
            'result': result,
            'result_text': display_result,
            'explanation': explanation,
            'level': level
        })
        
    return False # COMMAND_ACK itself doesn't change drone_state directly

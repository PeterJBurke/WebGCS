"""
Handles processing of specific MAVLink messages.
"""
import time
import math # Added for radians to degrees conversion
from pymavlink import mavutil

# Import from our own modules
from config import AP_CUSTOM_MODES # ArduPilot specific
from mavlink_utils import (
    MAV_RESULT_STR, # Ensure MAV_RESULT_STR is imported
    MAV_TYPE_STR,
    MAV_AUTOPILOT_STR,
    MAV_STATE_STR,
    MAV_MODE_FLAG_ENUM,
    get_ekf_status_report, # Added for SYS_STATUS processing
    MAV_SEVERITY_STR # Added for STATUSTEXT processing
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
    
    # Log heartbeat in human-readable format
    system_status_str = MAV_STATE_STR.get(msg.system_status, f"UNKNOWN({msg.system_status})")
    vehicle_type_str = MAV_TYPE_STR.get(msg.type, f"UNKNOWN({msg.type})")
    autopilot_type_str = MAV_AUTOPILOT_STR.get(msg.autopilot, f"UNKNOWN({msg.autopilot})")
    
    # Decode base mode flags
    base_mode_flags = []
    for flag_name, flag_value in MAV_MODE_FLAG_ENUM.items():
        if msg.base_mode & flag_value:
            base_mode_flags.append(flag_name.replace('MAV_MODE_FLAG_', ''))
    base_mode_str = ", ".join(base_mode_flags) if base_mode_flags else "NONE"
    
    # Get custom mode string
    custom_mode_str_list = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
    custom_mode_str = custom_mode_str_list[0] if custom_mode_str_list else f'CUSTOM_MODE({msg.custom_mode})'
    
    # Format armed status
    armed_status = "ARMED" if (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) else "DISARMED"
    
    # Print heartbeat info
    print(f"HEARTBEAT: SysID={msg.get_srcSystem()} CompID={msg.get_srcComponent()} | "
          f"Type={vehicle_type_str} | Autopilot={autopilot_type_str} | "
          f"Status={system_status_str} | Mode={custom_mode_str} | {armed_status} | "
          f"Base Mode Flags=[{base_mode_str}]")
    drone_state_changed_local = False

    with drone_state_lock:
        prev_mode = drone_state.get('mode', 'UNKNOWN')
        prev_armed = drone_state.get('armed', False)
        prev_connected = drone_state.get('connected', False)
        
        # Update drone state based on heartbeat
        current_connected_state = True # Heartbeat implies connection
        if not prev_connected and current_connected_state:
            drone_state['was_just_connected_by_heartbeat'] = True # Signal to mavlink_connection_manager
            drone_state_changed_local = True # Connection state itself changed
        
        drone_state['connected'] = current_connected_state
        drone_state['armed'] = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
        
        # Ensure we are processing heartbeat from the expected target system
        # The mavlink_conn.target_system check is crucial for multi-vehicle scenarios (not currently supported but good practice)
        # For a single drone setup, mavlink_conn.target_system might be 0 initially until first message.
        # The mavlink_receive_loop_runner already filters by msg.get_srcSystem() == mavlink_connection_instance.target_system
        # so this check here is somewhat redundant if mavlink_conn is the one from mavlink_connection_manager.
        # However, if mavlink_conn.target_system is not yet set, we might miss initial mode string.
        # For now, assume mavlink_conn.target_system is correctly set by the time we get here for the intended drone.

        custom_mode_str_list = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
        new_mode = custom_mode_str_list[0] if custom_mode_str_list else f'CUSTOM_MODE({msg.custom_mode})'
        
        if drone_state.get('mode') != new_mode:
            log_cmd_action_cb("MODE_CHANGE", None, f"Mode changed from {prev_mode} to {new_mode}")
            drone_state['mode'] = new_mode
            drone_state_changed_local = True
            
        if drone_state['armed'] != prev_armed:
            status = "ARMED" if drone_state['armed'] else "DISARMED"
            log_cmd_action_cb("ARM_STATUS", None, f"Vehicle {status}")
            drone_state_changed_local = True

    # Emit event for UI animation - now sending generic mavlink_message
    # Only emit for our drone (already filtered by mavlink_receive_loop_runner, but good for clarity)
    if sio_instance and mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        # Log telemetry data for debugging
        with drone_state_lock:
            print(f"Current Telemetry: Connected={drone_state.get('connected', False)}, "
                  f"Armed={drone_state.get('armed', False)}, "
                  f"Mode={drone_state.get('mode', 'UNKNOWN')}, "
                  f"Lat={drone_state.get('lat', 0.0):.6f}, "
                  f"Lon={drone_state.get('lon', 0.0):.6f}, "
                  f"Alt={drone_state.get('alt_rel', 0.0):.1f}m")
        
        sio_instance.emit('mavlink_message', msg.to_dict()) # Send the whole message dictionary

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
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
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
            # vx, vy, vz: Ground X, Y, Z speed (cm/s)
            new_vx = msg.vx / 100.0  # Convert cm/s to m/s
            new_vy = msg.vy / 100.0  # Convert cm/s to m/s
            new_vz = msg.vz / 100.0  # Convert cm/s to m/s (positive down, but often displayed as positive for climb)

            # Check if any relevant value has changed to avoid unnecessary updates
            if (drone_state.get('lat') != new_lat or
                drone_state.get('lon') != new_lon or
                drone_state.get('alt_abs') != new_alt_msl or
                drone_state.get('alt_rel') != new_alt_rel or
                drone_state.get('hdg') != new_hdg or
                drone_state.get('vx') != new_vx or
                drone_state.get('vy') != new_vy or
                drone_state.get('vz') != new_vz):
                
                drone_state['lat'] = new_lat
                drone_state['lon'] = new_lon
                drone_state['alt_abs'] = new_alt_msl
                drone_state['alt_rel'] = new_alt_rel
                drone_state['hdg'] = new_hdg
                drone_state['vx'] = new_vx
                drone_state['vy'] = new_vy
                drone_state['vz'] = new_vz
                
                # print(f"DEBUG: Updated drone_state with GLOBAL_POSITION_INT: lat={new_lat}, lon={new_lon}, alt_rel={new_alt_rel}, hdg={new_hdg}, vx={new_vx}, vy={new_vy}, vz={new_vz}")
                drone_state_changed_local = True
        
    return drone_state_changed_local

def process_vfr_hud(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes VFR_HUD message and updates drone_state.

    Args:
        msg: The MAVLink VFR_HUD message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function.
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        with drone_state_lock:
            new_airspeed = msg.airspeed
            new_groundspeed = msg.groundspeed
            # msg.alt for VFR_HUD is often AGL. We store it as 'alt_rel_vfr' for now.
            # The primary 'alt_rel' comes from GLOBAL_POSITION_INT.
            new_alt_vfr = msg.alt 
            new_climb_rate = msg.climb

            # Check if any relevant value has changed
            if (drone_state.get('airspeed') != new_airspeed or
                drone_state.get('groundspeed') != new_groundspeed or
                drone_state.get('alt_rel_vfr') != new_alt_vfr or # Storing as a separate field
                drone_state.get('climb_rate') != new_climb_rate):
                
                drone_state['airspeed'] = new_airspeed
                drone_state['groundspeed'] = new_groundspeed
                drone_state['alt_rel_vfr'] = new_alt_vfr # Store VFR_HUD altitude separately
                drone_state['climb_rate'] = new_climb_rate
                
                drone_state_changed_local = True
    return drone_state_changed_local

def process_sys_status(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes SYS_STATUS message and updates drone_state, including battery and EKF status.

    Args:
        msg: The MAVLink SYS_STATUS message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function.
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        with drone_state_lock:
            new_voltage = msg.voltage_battery / 1000.0  # mV to V
            new_current = msg.current_battery / 100.0  # cA to A (can be -1 if not available)
            new_remaining = msg.battery_remaining      # Percent (can be -1 if not available)
            
            # EKF status flags are in onboard_control_sensors_health
            new_ekf_flags = msg.onboard_control_sensors_health
            new_ekf_report = get_ekf_status_report(new_ekf_flags)

            # Other system status fields (optional to store all, but good for debugging)
            # drone_state['sys_status_present'] = msg.onboard_control_sensors_present
            # drone_state['sys_status_enabled'] = msg.onboard_control_sensors_enabled
            drone_state['sys_status_health_raw'] = new_ekf_flags # Store the raw health flags

            if (drone_state.get('battery_voltage') != new_voltage or
                drone_state.get('battery_current') != new_current or
                drone_state.get('battery_remaining') != new_remaining or
                drone_state.get('ekf_flags') != new_ekf_flags or 
                drone_state.get('ekf_status_report') != new_ekf_report):
                
                drone_state['battery_voltage'] = new_voltage
                drone_state['battery_current'] = new_current if new_current != -0.01 else None # Use None if -1 (0.01A)
                drone_state['battery_remaining'] = new_remaining if new_remaining != -1 else None # Use None if -1
                drone_state['ekf_flags'] = new_ekf_flags
                drone_state['ekf_status_report'] = new_ekf_report
                
                drone_state_changed_local = True
    return drone_state_changed_local

def process_gps_raw_int(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes GPS_RAW_INT message and updates drone_state.

    Args:
        msg: The MAVLink GPS_RAW_INT message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function.
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        with drone_state_lock:
            new_fix_type = msg.fix_type
            new_sats = msg.satellites_visible
            # eph is HDOP * 100. If unknown, it's UINT16_MAX (65535).
            new_hdop = msg.eph / 100.0 if msg.eph != 65535 else None 

            if (drone_state.get('gps_fix_type') != new_fix_type or
                drone_state.get('satellites_visible') != new_sats or
                drone_state.get('hdop') != new_hdop):
                
                drone_state['gps_fix_type'] = new_fix_type
                drone_state['satellites_visible'] = new_sats
                drone_state['hdop'] = new_hdop
                
                drone_state_changed_local = True
    return drone_state_changed_local

def process_attitude(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes ATTITUDE message and updates drone_state.

    Args:
        msg: The MAVLink ATTITUDE message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function.
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        with drone_state_lock:
            new_roll = math.degrees(msg.roll)
            new_pitch = math.degrees(msg.pitch)
            new_yaw = math.degrees(msg.yaw) # Note: GLOBAL_POSITION_INT.hdg is often preferred for 'heading'
            
            # Normalize yaw to 0-360 range if needed, though math.degrees output is typically -180 to 180
            # if new_yaw < 0:
            #     new_yaw += 360

            if (drone_state.get('roll') != new_roll or
                drone_state.get('pitch') != new_pitch or
                drone_state.get('yaw_attitude') != new_yaw): # Store as 'yaw_attitude' to distinguish from 'hdg'
                
                drone_state['roll'] = new_roll
                drone_state['pitch'] = new_pitch
                drone_state['yaw_attitude'] = new_yaw # Use a distinct key for yaw from ATTITUDE
                
                # Optionally store rates if needed for UI or other logic
                # drone_state['rollspeed'] = math.degrees(msg.rollspeed)
                # drone_state['pitchspeed'] = math.degrees(msg.pitchspeed)
                # drone_state['yawspeed'] = math.degrees(msg.yawspeed)

                drone_state_changed_local = True
    return drone_state_changed_local

def process_home_position(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes HOME_POSITION message and updates drone_state.

    Args:
        msg: The MAVLink HOME_POSITION message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function.
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        with drone_state_lock:
            new_home_lat = msg.latitude / 1e7
            new_home_lon = msg.longitude / 1e7
            new_home_alt_msl = msg.altitude / 1000.0 # AMSL

            if (drone_state.get('home_lat') != new_home_lat or
                drone_state.get('home_lon') != new_home_lon or
                drone_state.get('home_alt_msl') != new_home_alt_msl):
                
                drone_state['home_lat'] = new_home_lat
                drone_state['home_lon'] = new_home_lon
                drone_state['home_alt_msl'] = new_home_alt_msl
                
                # Log that home position has been updated
                if log_cmd_action_cb:
                    log_cmd_action_cb("HOME_POSITION_UPDATE", None, f"Home position set/updated: Lat {new_home_lat:.7f}, Lon {new_home_lon:.7f}, Alt {new_home_alt_msl:.2f}m AMSL")
                
                drone_state_changed_local = True
                
                # Potentially notify mavlink_connection_manager to stop requesting HOME_POSITION frequently
                # This is handled by request_data_streams checking drone_state for home_lat/lon

    return drone_state_changed_local

def process_statustext(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes STATUSTEXT message and emits it via SocketIO.

    Args:
        msg: The MAVLink STATUSTEXT message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function (used for logging).
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if drone_state was modified, False otherwise.
    """
    drone_state_changed = False
    
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        severity_val = msg.severity
        severity_str = MAV_SEVERITY_STR.get(severity_val, f'UNKNOWN_SEVERITY_{severity_val}')
        text_content = msg.text
        
        # Store the statustext in drone_state for reference by other functions
        with drone_state_lock:
            drone_state['last_statustext'] = text_content
            drone_state['last_statustext_time'] = time.time()
            drone_state['last_statustext_severity'] = severity_str
            drone_state_changed = True
        
        # Log the message to the server console as well
        log_level = "INFO"
        if severity_str.startswith("MAV_SEVERITY_ERROR") or severity_str.startswith("MAV_SEVERITY_CRITICAL") or severity_str.startswith("MAV_SEVERITY_ALERT") or severity_str.startswith("MAV_SEVERITY_EMERGENCY"):
            log_level = "ERROR"
        elif severity_str.startswith("MAV_SEVERITY_WARNING"):
            log_level = "WARNING"
        
        if log_cmd_action_cb:
            log_cmd_action_cb("STATUSTEXT", {"severity": severity_str}, text_content, level=log_level)
        else:
            print(f"STATUSTEXT [{severity_str}]: {text_content}") # Fallback print

        # Emit to clients
        if sio_instance:
            sio_instance.emit('statustext_received', {
                'severity_val': severity_val,
                'severity_str': severity_str.replace('MAV_SEVERITY_', ''), # Clean up for display
                'text': text_content
            })
            
    return drone_state_changed  # Return True if drone_state was modified

def process_mission_current(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Processes MISSION_CURRENT message and updates drone_state.

    Args:
        msg: The MAVLink MISSION_CURRENT message object.
        drone_state: The shared dictionary holding drone state.
        drone_state_lock: Threading lock for accessing drone_state.
        mavlink_conn: The MAVLink connection object.
        log_cmd_action_cb: Callback to the log_command_action function.
        sio_instance: The SocketIO instance for emitting events.

    Returns:
        bool: True if the drone_state was changed, False otherwise.
    """
    drone_state_changed_local = False
    if mavlink_conn and msg.get_srcSystem() == getattr(mavlink_conn, 'target_system', 0):
        with drone_state_lock:
            new_mission_current_seq = msg.seq

            if drone_state.get('mission_current_seq') != new_mission_current_seq:
                drone_state['mission_current_seq'] = new_mission_current_seq
                # Log the change if needed
                if log_cmd_action_cb:
                    log_cmd_action_cb("MISSION_UPDATE", {"current_wp_seq": new_mission_current_seq}, f"Current mission waypoint sequence: {new_mission_current_seq}")
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
    cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name if cmd in mavutil.mavlink.enums['MAV_CMD'] else f'ID {cmd}'
    
    # Get result name from MAV_RESULT_STR mapping
    result_name = MAV_RESULT_STR.get(result, 'UNKNOWN')
    
    # Determine explanation and level based on result
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
    else: 
        explanation = f"Command response: {result_name}"
        if result_name == 'UNKNOWN': level = "WARNING"

    # Format the display result
    display_result = result_name # Default display
    if explanation != f"Command response: {result_name}": # If custom explanation was set
        display_result = f"{result_name} - {explanation}"

    # Log the command acknowledgment
    log_cmd_action_cb(f"ACK_{cmd_name}", f"Result: {display_result} (Raw: {result})", explanation, level)
    
    # Extract UI command information from pending_commands
    ui_command_key = None
    ui_command_details = {}
    pending_command_info = None
    
    # Check if we have pending_commands_instance in mavlink_connection_manager
    if hasattr(mavlink_conn, 'pending_commands_instance'):
        pending_commands = mavlink_conn.pending_commands_instance
        if cmd in pending_commands:
            pending_command_info = pending_commands[cmd]
            
            # Handle both dictionary and timestamp formats
            if isinstance(pending_command_info, dict):
                ui_command_key = pending_command_info.get('ui_command_name')
                # Copy any additional details for the UI
                ui_command_details = {k: v for k, v in pending_command_info.items() 
                                    if k not in ['timestamp', 'ui_command_name']}
    
    # Special handling for specific commands
    if cmd == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
        # Check if this is an ARM or DISARM command based on pending_command_info
        if ui_command_key == 'ARM':
            if result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                with drone_state_lock:
                    drone_state['armed'] = True
                log_cmd_action_cb("ARM_SUCCESS", None, "Vehicle successfully ARMED", "INFO")
                if sio_instance:
                    sio_instance.emit('status_message', {
                        'text': 'Vehicle successfully ARMED', 
                        'type': 'success'
                    })
            else:
                # ARM failed, provide helpful feedback
                failure_reason = "Unknown reason"
                
                # Check if there's a recent STATUSTEXT message about arming failure
                rtl_not_armable = False
                with drone_state_lock:
                    last_statustext = drone_state.get('last_statustext', '')
                    if 'RTL mode not armable' in last_statustext:
                        rtl_not_armable = True
                        failure_reason = "RTL mode not armable. Please change to an armable mode like GUIDED or STABILIZE first."
                
                if not rtl_not_armable:  # If no specific statustext found, use generic messages
                    if result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
                        failure_reason = "Vehicle not ready to arm (check pre-arm checks)"
                    elif result == mavutil.mavlink.MAV_RESULT_DENIED:
                        failure_reason = "Arming denied (check current mode, safety switch, GPS lock, or other pre-arm requirements)"
                
                log_cmd_action_cb("ARM_FAILED", None, f"Failed to ARM: {failure_reason}", "ERROR")
                if sio_instance:
                    sio_instance.emit('status_message', {
                        'text': f'Failed to ARM: {failure_reason}', 
                        'type': 'error'
                    })
        
        elif ui_command_key == 'DISARM':
            if result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                with drone_state_lock:
                    drone_state['armed'] = False
                log_cmd_action_cb("DISARM_SUCCESS", None, "Vehicle successfully DISARMED", "INFO")
                if sio_instance:
                    sio_instance.emit('status_message', {
                        'text': 'Vehicle successfully DISARMED', 
                        'type': 'success'
                    })
            else:
                # DISARM failed, provide helpful feedback
                failure_reason = "Unknown reason"
                if result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
                    failure_reason = "Vehicle not ready to disarm (might be in flight)"
                elif result == mavutil.mavlink.MAV_RESULT_DENIED:
                    failure_reason = "Disarming denied (vehicle might be in flight)"
                
                log_cmd_action_cb("DISARM_FAILED", None, f"Failed to DISARM: {failure_reason}", "ERROR")
                if sio_instance:
                    sio_instance.emit('status_message', {
                        'text': f'Failed to DISARM: {failure_reason}', 
                        'type': 'error'
                    })
    
    elif cmd == mavutil.mavlink.MAV_CMD_DO_SET_MODE:
        # Handle SET_MODE acknowledgment
        mode_name = ui_command_details.get('mode_name', 'UNKNOWN')
        
        if result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
            log_cmd_action_cb("SET_MODE_SUCCESS", {"mode_name": mode_name}, 
                             f"Successfully set mode to {mode_name}", "INFO")
            if sio_instance:
                sio_instance.emit('status_message', {
                    'text': f'Successfully set mode to {mode_name}', 
                    'type': 'success'
                })
        else:
            # SET_MODE failed, provide helpful feedback
            failure_reason = "Unknown reason"
            if result == mavutil.mavlink.MAV_RESULT_TEMPORARILY_REJECTED:
                failure_reason = f"Vehicle not ready for {mode_name} mode (check mode requirements)"
            elif result == mavutil.mavlink.MAV_RESULT_DENIED:
                failure_reason = f"Mode {mode_name} denied (check vehicle state and mode requirements)"
            elif result == mavutil.mavlink.MAV_RESULT_UNSUPPORTED:
                failure_reason = f"Mode {mode_name} not supported by this vehicle"
            
            log_cmd_action_cb("SET_MODE_FAILED", {"mode_name": mode_name}, 
                             f"Failed to set mode to {mode_name}: {failure_reason}", "ERROR")
            if sio_instance:
                sio_instance.emit('status_message', {
                    'text': f'Failed to set mode to {mode_name}: {failure_reason}', 
                    'type': 'error'
                })

    # Emit the command acknowledgment to the frontend
    if sio_instance:
        sio_instance.emit('command_ack_received', {
            'command': cmd,  # MAVLink command ID (e.g., 176)
            'command_name': cmd_name,  # MAVLink command name string (e.g., "MAV_CMD_DO_SET_MODE")
            'ui_command_key': ui_command_key,  # UI command key (e.g., "SET_MODE", "ARM")
            'result': result,
            'result_text': display_result,
            'explanation': explanation,
            'level': level,
            'details': ui_command_details  # Additional command-specific details
        })
    
    # Return False since COMMAND_ACK itself doesn't typically change drone_state directly
    # (Any state changes would have been made in the special handling sections above)
    return False

"""
MAVLink Message Processor
Handles processing of specific MAVLink message types

Implements minimum functionality to pass TEST-002: Heartbeat Reception Test
"""
import time
import math
from pymavlink import mavutil

# Import configuration for flight modes
AP_CUSTOM_MODES = {
    'STABILIZE': 0,
    'ACRO': 1,
    'ALT_HOLD': 2,
    'AUTO': 3,
    'GUIDED': 4,
    'LOITER': 5,
    'RTL': 6,
    'LAND': 9,
    'POS_HOLD': 16,
    'BRAKE': 17,
    'THROW': 18,
    'AVOID_ADSB': 19,
    'GUIDED_NOGPS': 20,
    'SMART_RTL': 21,
    'FLOWHOLD': 22,
    'FOLLOW': 23,
    'ZIGZAG': 24,
    'SYSTEMID': 25,
    'AUTOROTATE': 26,
    'AUTO_RTL': 27
}


def process_heartbeat(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance, heartbeat_log_cb=None):
    """
    Process HEARTBEAT message and update drone state
    
    Args:
        msg: MAVLink HEARTBEAT message
        drone_state: Shared state dictionary  
        drone_state_lock: Threading lock
        mavlink_conn: MAVLink connection object
        log_cmd_action_cb: Logging callback
        sio_instance: SocketIO instance
        heartbeat_log_cb: Optional heartbeat logging callback
        
    Returns:
        bool: True if drone_state was modified
    """
    
    try:
        with drone_state_lock:
            # Update connection status
            drone_state['connected'] = True
            
            # Extract system and component IDs
            drone_state['system_id'] = msg.get_srcSystem()
            drone_state['component_id'] = msg.get_srcComponent()
            
            # Extract armed status from base mode
            drone_state['armed'] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            
            # Extract flight mode from custom mode
            custom_mode = msg.custom_mode
            mode_name = 'UNKNOWN'
            
            # Find mode name from custom mode number
            for mode_str, mode_num in AP_CUSTOM_MODES.items():
                if mode_num == custom_mode:
                    mode_name = mode_str
                    break
            
            if mode_name == 'UNKNOWN' and custom_mode != 0:
                mode_name = f'CUSTOM_{custom_mode}'
            
            drone_state['mode'] = mode_name
            
            # Store system status
            drone_state['system_status'] = msg.system_status
            
            # Log heartbeat processing
            if log_cmd_action_cb:
                log_cmd_action_cb(
                    "HEARTBEAT_PROCESSED", 
                    details=f"System {drone_state['system_id']}, Mode: {mode_name}, Armed: {drone_state['armed']}"
                )
        
        # Custom heartbeat logging if callback provided
        if heartbeat_log_cb:
            heartbeat_log_cb(msg)
        
        return True  # State was modified
        
    except Exception as e:
        if log_cmd_action_cb:
            log_cmd_action_cb("HEARTBEAT_ERROR", details=f"Processing failed: {e}")
        print(f"Error processing heartbeat: {e}")
        return False


def process_global_position_int(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Process GLOBAL_POSITION_INT message for position data"""
    
    try:
        with drone_state_lock:
            # Update position data (convert from 1E7 format)
            drone_state['lat'] = msg.lat / 1e7
            drone_state['lon'] = msg.lon / 1e7
            drone_state['alt_abs'] = msg.alt / 1000.0  # mm to m
            drone_state['alt_rel'] = msg.relative_alt / 1000.0  # mm to m
            
            # Update velocity (convert from cm/s to m/s)
            drone_state['vx'] = msg.vx / 100.0
            drone_state['vy'] = msg.vy / 100.0
            drone_state['vz'] = msg.vz / 100.0
            
            # Calculate heading from velocity
            if msg.hdg != 65535:  # Valid heading available
                drone_state['heading'] = msg.hdg / 100.0  # centidegrees to degrees
            else:
                # Calculate from velocity if heading not available
                if drone_state['vx'] != 0 or drone_state['vy'] != 0:
                    heading_rad = math.atan2(drone_state['vy'], drone_state['vx'])
                    drone_state['heading'] = math.degrees(heading_rad)
                    if drone_state['heading'] < 0:
                        drone_state['heading'] += 360
        
        return True
        
    except Exception as e:
        if log_cmd_action_cb:
            log_cmd_action_cb("POSITION_ERROR", details=f"Processing failed: {e}")
        return False


def process_command_ack(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Process COMMAND_ACK message for command acknowledgments"""
    
    try:
        command = msg.command
        result = msg.result
        
        # Log command acknowledgment
        if log_cmd_action_cb:
            result_str = "SUCCESS" if result == 0 else f"FAILED({result})"
            log_cmd_action_cb(
                "COMMAND_ACK", 
                params={'command': command, 'result': result},
                details=f"Command {command} result: {result_str}"
            )
        
        return False  # ACK doesn't modify drone state directly
        
    except Exception as e:
        if log_cmd_action_cb:
            log_cmd_action_cb("ACK_ERROR", details=f"Processing failed: {e}")
        return False
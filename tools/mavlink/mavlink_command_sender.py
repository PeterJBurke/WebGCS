"""
MAVLink Command Sender
Handles sending flight commands to drone via MAVLink protocol
"""
import time
from pymavlink import mavutil
from config import AP_CUSTOM_MODES

def send_arm_disarm_command(mavlink_conn, arm=True, log_callback=None):
    """
    Send ARM or DISARM command to drone
    
    Args:
        mavlink_conn: MAVLink connection object
        arm: True to arm, False to disarm
        log_callback: Optional logging callback
    
    Returns:
        dict: Command result with success status
    """
    if not mavlink_conn:
        return {'success': False, 'error': 'No MAVLink connection'}
    
    try:
        command = "ARM" if arm else "DISARM"
        
        # Send MAV_CMD_COMPONENT_ARM_DISARM command
        mavlink_conn.mav.command_long_send(
            mavlink_conn.target_system,    # target_system
            mavlink_conn.target_component, # target_component
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, # command
            0,          # confirmation
            1 if arm else 0,  # param1: 1 to arm, 0 to disarm
            0, 0, 0, 0, 0, 0  # param2-7 (unused)
        )
        
        if log_callback:
            log_callback(f"COMMAND_SENT", details=f"{command} command sent to drone")
        
        return {
            'success': True,
            'command': command,
            'timestamp': time.time(),
            'message': f"{command} command sent successfully"
        }
        
    except Exception as e:
        error_msg = f"{command} command failed: {e}"
        if log_callback:
            log_callback("COMMAND_ERROR", details=error_msg)
        
        return {
            'success': False,
            'command': command,
            'error': error_msg,
            'timestamp': time.time()
        }

def send_mode_change_command(mavlink_conn, mode_name, log_callback=None):
    """
    Send flight mode change command to drone
    
    Args:
        mavlink_conn: MAVLink connection object
        mode_name: Flight mode name (e.g., 'GUIDED', 'STABILIZE')
        log_callback: Optional logging callback
    
    Returns:
        dict: Command result with success status
    """
    if not mavlink_conn:
        return {'success': False, 'error': 'No MAVLink connection'}
    
    try:
        # Get custom mode number from mode name
        if mode_name not in AP_CUSTOM_MODES:
            return {
                'success': False,
                'command': 'SET_MODE',
                'error': f'Unknown flight mode: {mode_name}',
                'available_modes': list(AP_CUSTOM_MODES.keys())
            }
        
        custom_mode = AP_CUSTOM_MODES[mode_name]
        
        # Send MAV_CMD_DO_SET_MODE command
        mavlink_conn.mav.set_mode_send(
            mavlink_conn.target_system,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            custom_mode
        )
        
        if log_callback:
            log_callback("COMMAND_SENT", details=f"Mode change to {mode_name} sent")
        
        return {
            'success': True,
            'command': 'SET_MODE',
            'mode': mode_name,
            'custom_mode': custom_mode,
            'timestamp': time.time(),
            'message': f"Mode change to {mode_name} sent successfully"
        }
        
    except Exception as e:
        error_msg = f"Mode change command failed: {e}"
        if log_callback:
            log_callback("COMMAND_ERROR", details=error_msg)
        
        return {
            'success': False,
            'command': 'SET_MODE',
            'mode': mode_name,
            'error': error_msg,
            'timestamp': time.time()
        }

def send_takeoff_command(mavlink_conn, altitude, log_callback=None):
    """
    Send takeoff command to drone
    
    Args:
        mavlink_conn: MAVLink connection object
        altitude: Target altitude in meters
        log_callback: Optional logging callback
    
    Returns:
        dict: Command result with success status
    """
    if not mavlink_conn:
        return {'success': False, 'error': 'No MAVLink connection'}
    
    try:
        altitude = float(altitude)
        
        if altitude <= 0 or altitude > 100:  # Safety limits
            return {
                'success': False,
                'command': 'TAKEOFF',
                'error': f'Invalid altitude: {altitude}m (must be 0-100m)',
                'altitude': altitude
            }
        
        # Send MAV_CMD_NAV_TAKEOFF command
        mavlink_conn.mav.command_long_send(
            mavlink_conn.target_system,    # target_system
            mavlink_conn.target_component, # target_component
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, # command
            0,          # confirmation
            0,          # param1: minimum pitch (degrees)
            0,          # param2: empty
            0,          # param3: empty
            0,          # param4: yaw angle (degrees)
            0,          # param5: latitude (if zero, use current position)
            0,          # param6: longitude (if zero, use current position)  
            altitude    # param7: altitude (meters)
        )
        
        if log_callback:
            log_callback("COMMAND_SENT", details=f"Takeoff to {altitude}m sent")
        
        return {
            'success': True,
            'command': 'TAKEOFF',
            'altitude': altitude,
            'timestamp': time.time(),
            'message': f"Takeoff to {altitude}m sent successfully"
        }
        
    except Exception as e:
        error_msg = f"Takeoff command failed: {e}"
        if log_callback:
            log_callback("COMMAND_ERROR", details=error_msg)
        
        return {
            'success': False,
            'command': 'TAKEOFF',
            'altitude': altitude if 'altitude' in locals() else 'unknown',
            'error': error_msg,
            'timestamp': time.time()
        }

def send_goto_command(mavlink_conn, lat, lon, alt, log_callback=None):
    """
    Send navigation waypoint (Go To) command to drone
    
    Args:
        mavlink_conn: MAVLink connection object
        lat: Target latitude in degrees (-90 to 90)
        lon: Target longitude in degrees (-180 to 180) 
        alt: Target altitude in meters AGL (-100 to 5000)
        log_callback: Optional logging callback
    
    Returns:
        dict: Command result with success status
    """
    if not mavlink_conn:
        return {'success': False, 'error': 'No MAVLink connection'}
    
    try:
        # Validate and convert coordinates
        lat = float(lat)
        lon = float(lon)
        alt = float(alt)
        
        # Validate latitude range
        if lat < -90.0 or lat > 90.0:
            return {
                'success': False,
                'command': 'GOTO',
                'error': f'Invalid latitude: {lat} (must be -90 to 90 degrees)',
                'coordinates': {'lat': lat, 'lon': lon, 'alt': alt}
            }
        
        # Validate longitude range
        if lon < -180.0 or lon > 180.0:
            return {
                'success': False,
                'command': 'GOTO', 
                'error': f'Invalid longitude: {lon} (must be -180 to 180 degrees)',
                'coordinates': {'lat': lat, 'lon': lon, 'alt': alt}
            }
        
        # Validate altitude range (safety limits)
        if alt < -100.0 or alt > 5000.0:
            return {
                'success': False,
                'command': 'GOTO',
                'error': f'Invalid altitude: {alt}m (must be -100 to 5000m AGL)',
                'coordinates': {'lat': lat, 'lon': lon, 'alt': alt}
            }
        
        # Send MAV_CMD_NAV_WAYPOINT command
        # This command directs the vehicle to a specified waypoint location
        mavlink_conn.mav.command_long_send(
            mavlink_conn.target_system,    # target_system
            mavlink_conn.target_component, # target_component
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, # command (16)
            0,          # confirmation
            0,          # param1: hold time (seconds, 0=not specified)
            0,          # param2: acceptance radius in meters (0=use default)
            0,          # param3: pass radius in meters (0=pass through)
            0,          # param4: yaw angle in degrees (0=not specified)
            lat,        # param5: latitude (degrees)
            lon,        # param6: longitude (degrees)
            alt         # param7: altitude (meters AGL)
        )
        
        if log_callback:
            log_callback("COMMAND_SENT", 
                        details=f"Go To waypoint sent: {lat:.6f}, {lon:.6f}, {alt}m")
        
        return {
            'success': True,
            'command': 'GOTO',
            'coordinates': {
                'lat': lat,
                'lon': lon, 
                'alt': alt
            },
            'timestamp': time.time(),
            'message': f"Go To command sent: {lat:.6f}, {lon:.6f}, {alt}m AGL"
        }
        
    except (ValueError, TypeError) as e:
        error_msg = f"Go To command invalid parameters: {e}"
        if log_callback:
            log_callback("COMMAND_ERROR", details=error_msg)
        
        return {
            'success': False,
            'command': 'GOTO',
            'error': error_msg,
            'coordinates': {
                'lat': lat if 'lat' in locals() else 'invalid',
                'lon': lon if 'lon' in locals() else 'invalid',
                'alt': alt if 'alt' in locals() else 'invalid'
            },
            'timestamp': time.time()
        }
    except Exception as e:
        error_msg = f"Go To command failed: {e}"
        if log_callback:
            log_callback("COMMAND_ERROR", details=error_msg)
        
        return {
            'success': False,
            'command': 'GOTO',
            'error': error_msg,
            'timestamp': time.time()
        }

def send_land_command(mavlink_conn, log_callback=None):
    """
    Send land command to drone
    
    Args:
        mavlink_conn: MAVLink connection object
        log_callback: Optional logging callback
    
    Returns:
        dict: Command result with success status
    """
    if not mavlink_conn:
        return {'success': False, 'error': 'No MAVLink connection'}
    
    try:
        # Send MAV_CMD_NAV_LAND command
        mavlink_conn.mav.command_long_send(
            mavlink_conn.target_system,    # target_system
            mavlink_conn.target_component, # target_component
            mavutil.mavlink.MAV_CMD_NAV_LAND, # command
            0,          # confirmation
            0,          # param1: abort altitude (0=use default)
            0,          # param2: land mode (0=minimum descent velocity)
            0,          # param3: empty
            0,          # param4: yaw angle (degrees, 0=not specified)
            0,          # param5: latitude (0=use current position)
            0,          # param6: longitude (0=use current position)
            0           # param7: altitude (0=use current altitude)
        )
        
        if log_callback:
            log_callback("COMMAND_SENT", details="Land command sent")
        
        return {
            'success': True,
            'command': 'LAND',
            'timestamp': time.time(),
            'message': "Land command sent successfully"
        }
        
    except Exception as e:
        error_msg = f"Land command failed: {e}"
        if log_callback:
            log_callback("COMMAND_ERROR", details=error_msg)
        
        return {
            'success': False,
            'command': 'LAND',
            'error': error_msg,
            'timestamp': time.time()
        }

def send_rtl_command(mavlink_conn, log_callback=None):
    """
    Send Return to Launch (RTL) command to drone
    
    Args:
        mavlink_conn: MAVLink connection object
        log_callback: Optional logging callback
    
    Returns:
        dict: Command result with success status
    """
    if not mavlink_conn:
        return {'success': False, 'error': 'No MAVLink connection'}
    
    try:
        # Send MAV_CMD_NAV_RETURN_TO_LAUNCH command
        mavlink_conn.mav.command_long_send(
            mavlink_conn.target_system,    # target_system
            mavlink_conn.target_component, # target_component
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH, # command
            0,          # confirmation
            0, 0, 0, 0, 0, 0, 0  # param1-7 (unused for RTL)
        )
        
        if log_callback:
            log_callback("COMMAND_SENT", details="Return to Launch (RTL) command sent")
        
        return {
            'success': True,
            'command': 'RTL',
            'timestamp': time.time(),
            'message': "Return to Launch command sent successfully"
        }
        
    except Exception as e:
        error_msg = f"RTL command failed: {e}"
        if log_callback:
            log_callback("COMMAND_ERROR", details=error_msg)
        
        return {
            'success': False,
            'command': 'RTL',
            'error': error_msg,
            'timestamp': time.time()
        }

def process_flight_command(command_data, mavlink_conn, log_callback=None):
    """
    Process flight command based on command type
    
    Args:
        command_data: Dictionary with command and params
        mavlink_conn: MAVLink connection object
        log_callback: Optional logging callback
    
    Returns:
        dict: Command execution result
    """
    command = command_data.get('command', '').upper()
    params = command_data.get('params', {})
    
    if command == 'ARM':
        return send_arm_disarm_command(mavlink_conn, arm=True, log_callback=log_callback)
    
    elif command == 'DISARM':
        return send_arm_disarm_command(mavlink_conn, arm=False, log_callback=log_callback)
    
    elif command == 'SET_MODE':
        mode = params.get('mode', '').upper()
        if not mode:
            return {'success': False, 'error': 'Mode parameter required for SET_MODE command'}
        return send_mode_change_command(mavlink_conn, mode, log_callback=log_callback)
    
    elif command == 'TAKEOFF':
        altitude = params.get('altitude')
        if altitude is None:
            return {'success': False, 'error': 'Altitude parameter required for TAKEOFF command'}
        return send_takeoff_command(mavlink_conn, altitude, log_callback=log_callback)
    
    elif command == 'GOTO':
        lat = params.get('lat')
        lon = params.get('lon') 
        alt = params.get('alt')
        
        if lat is None or lon is None or alt is None:
            return {
                'success': False, 
                'error': 'Latitude, longitude, and altitude parameters required for GOTO command',
                'required_params': ['lat', 'lon', 'alt']
            }
        return send_goto_command(mavlink_conn, lat, lon, alt, log_callback=log_callback)
    
    elif command == 'LAND':
        return send_land_command(mavlink_conn, log_callback=log_callback)
    
    elif command == 'RTL':
        return send_rtl_command(mavlink_conn, log_callback=log_callback)
    
    else:
        return {
            'success': False,
            'command': command,
            'error': f'Unknown command: {command}',
            'supported_commands': ['ARM', 'DISARM', 'SET_MODE', 'TAKEOFF', 'GOTO', 'LAND', 'RTL']
        }
# /home/peter/Documents/WScode/WebGCS/socketio_handlers.py
import time
import traceback
import math
from flask import request # For request.sid
from flask_socketio import emit
from pymavlink import mavutil
import inspect
import linecache

# --- Context variables to be initialized by app.py ---
_socketio = None
_log_command_action = None
_get_mavlink_connection = None
_drone_state = None
_drone_state_lock = None
_pending_commands_dict = None 
_AP_MODE_NAME_TO_ID = None
_schedule_fence_request_in_app = None
_schedule_mission_request_in_app = None

def _log_wrapper_for_caller_info(command_name, params=None, details=None, level="INFO"):
    """Captures caller info and forwards to the main logger."""
    caller_filename = "UnknownFile"
    caller_lineno = 0
    caller_line_content = "Error: Could not retrieve source line." # Default error message

    try:
        # stack()[0] is _log_wrapper_for_caller_info itself.
        # stack()[1] is the frame of the function that called _log_wrapper_for_caller_info.
        # This is the frame whose line we want to log.
        frame_info = inspect.stack()[1]
        caller_filename = frame_info.filename
        caller_lineno = frame_info.lineno
        
        # Attempt to get the source line
        linecache.checkcache(caller_filename) 
        line = linecache.getline(caller_filename, caller_lineno).strip()
        if line:
            caller_line_content = line
        else:
            caller_line_content = f"Line {caller_lineno} not found or empty in {caller_filename}."

    except IndexError: # If inspect.stack() doesn't have enough frames
        caller_line_content = "Error: inspect.stack() call failed (IndexError)."
    except Exception as e: # Catch any other inspection errors
        caller_line_content = f"Error during inspection: {str(e)}"
        # For debugging the logger itself, uncomment below:
        # print(f"DEBUG: Logger inspection error: {e}, Filename: {caller_filename}, Lineno: {caller_lineno}")

    if _log_command_action: # Check if the main logger from app.py is available
        _log_command_action( # This calls app.py's log_command_action
            command_name,
            params=params,
            details=details,
            level=level,
            caller_filename=caller_filename,
            caller_lineno=caller_lineno,
            caller_line_content=caller_line_content
        )
    else:
        # Fallback if _log_command_action (app.py's logger) isn't initialized
        print(f"LOGGER_NOT_INITIALIZED: {level} | {command_name} | {params} | {details}")
        print(f"  Called from: {caller_filename}:{caller_lineno} -> {caller_line_content}")


# --- Function to send commands to the telemetry bridge script ---
def _send_command_to_bridge(command, **params):
    """
    Sends a command to the telemetry bridge script by writing to a command.json file.
    
    Args:
        command: Command name (e.g., 'SET_MODE', 'ARM', 'DISARM')
        **params: Additional parameters for the command
        
    Returns:
        bool: True if command was sent successfully, False otherwise
    """
    import json
    import os
    
    try:
        # Create command data
        command_data = {
            'command': command,
            **params
        }
        
        # Write command data to file
        with open('command.json', 'w') as f:
            json.dump(command_data, f)
        
        _log_wrapper_for_caller_info(command, params, f"Command sent to telemetry bridge: {command}", "INFO")
        return True
    except Exception as e:
        _log_wrapper_for_caller_info(command, params, f"Error sending command to telemetry bridge: {e}", "ERROR")
        return False

# --- Helper function (adapted from app.py's send_mavlink_command) ---
def _send_mavlink_command_handler(command, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0, confirmation=0):
    """
    Sends a MAVLink command_long.
    This is a helper for the SocketIO handlers and uses context variables.
    
    Args:
        command: MAVLink command ID (e.g., MAV_CMD_COMPONENT_ARM_DISARM)
        p1-p7: Command parameters
        confirmation: Confirmation parameter (0-255, incremented on retransmission)
        
    Returns:
        tuple: (success, message)
    """
    global _pending_commands_dict

    cmd_name = mavutil.mavlink.enums['MAV_CMD'][command].name if command in mavutil.mavlink.enums['MAV_CMD'] else f'ID {command}'
    current_mavlink_connection = _get_mavlink_connection()

    if not current_mavlink_connection or not _drone_state.get("connected", False):
        warn_msg = f"CMD {cmd_name} Failed: Drone not connected."
        _log_wrapper_for_caller_info(cmd_name, None, f"ERROR: {warn_msg}", "ERROR")
        return (False, warn_msg)

    target_sys = current_mavlink_connection.target_system
    target_comp = current_mavlink_connection.target_component

    if target_sys == 0:
        err_msg = f"CMD {cmd_name} Failed: Invalid target system."
        _log_wrapper_for_caller_info(cmd_name, None, f"ERROR: {err_msg}", "ERROR")
        return (False, err_msg)

    try:
        params_str = f"p1={p1:.2f}, p2={p2:.2f}, p3={p3:.2f}, p4={p4:.2f}, p5={p5:.6f}, p6={p6:.6f}, p7={p7:.2f}"
#        _log_wrapper_for_caller_info(cmd_name, params_str, f"To SYS:{target_sys} COMP:{target_comp}", "INFO")
        
        # Send the command
        current_mavlink_connection.mav.command_long_send(
            target_sys, 
            target_comp, 
            command, 
            confirmation,  # Confirmation parameter
            p1, p2, p3, p4, p5, p6, p7
        )

        # Track command in pending_commands_dict if it's not a stream request
        if command not in [mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE]:
            # If the command is not already in _pending_commands_dict with a dict value (from caller),
            # add it with a simple timestamp
            if command not in _pending_commands_dict or not isinstance(_pending_commands_dict[command], dict):
                _pending_commands_dict[command] = time.time()
            
            # Limit the size of pending_commands_dict
            if len(_pending_commands_dict) > 30:
                # Find the oldest command (by timestamp)
                oldest_cmd = None
                oldest_time = float('inf')
                
                for cmd_id, value in _pending_commands_dict.items():
                    cmd_time = value if isinstance(value, float) else value.get('timestamp', float('inf'))
                    if cmd_time < oldest_time:
                        oldest_time = cmd_time
                        oldest_cmd = cmd_id
                
                if oldest_cmd is not None:
                    print(f"Warning: Pending cmd limit, removing oldest: {oldest_cmd}")
                    del _pending_commands_dict[oldest_cmd]

        success_msg = f"CMD {cmd_name} sent."
        return (True, success_msg)
    except Exception as e:
        err_msg = f"CMD {cmd_name} Send Error: {e}"
        _log_wrapper_for_caller_info(cmd_name, None, f"EXCEPTION: {err_msg}", "ERROR")
        traceback.print_exc()
        return (False, err_msg)

# --- Initialization Function ---
def init_socketio_handlers(socketio_instance, app_context):
    global _socketio, _log_command_action, _get_mavlink_connection
    global _drone_state, _drone_state_lock, _pending_commands_dict, _AP_MODE_NAME_TO_ID
    global _schedule_fence_request_in_app, _schedule_mission_request_in_app

    _socketio = socketio_instance
    _log_command_action = app_context['log_command_action']
    _get_mavlink_connection = app_context['get_mavlink_connection']
    _drone_state = app_context['drone_state']
    _drone_state_lock = app_context['drone_state_lock']
    _pending_commands_dict = app_context['pending_commands_dict']
    _AP_MODE_NAME_TO_ID = app_context['AP_MODE_NAME_TO_ID']
    _schedule_fence_request_in_app = app_context['schedule_fence_request_in_app']
    _schedule_mission_request_in_app = app_context['schedule_mission_request_in_app']

    # --- SocketIO Event Handlers ---
    @_socketio.on('connect')
    def handle_connect():
        _log_wrapper_for_caller_info("CLIENT_CONNECTED", details=f"Client {request.sid} connected.")
        emit('telemetry_update', _drone_state)
        status_text = 'Backend connected. '
        status_text += 'Drone link active.' if _drone_state.get('connected') else 'Attempting drone link...'
        emit('status_message', {'text': status_text, 'type': 'info'})
        
        # Check if drone is already connected and emit connection status
        if _drone_state.get('connected', False):
            # Get current connection info from mavlink connection
            current_mavlink_connection = _get_mavlink_connection()
            if current_mavlink_connection:
                # Try to get the actual connection details
                try:
                    # Import here to avoid circular imports
                    from mavlink_connection_manager import get_current_connection_details
                    
                    ip, port = get_current_connection_details()
                    
                    if ip and port:
                        emit('connection_status', {
                            'status': 'connected',
                            'ip': ip,
                            'port': port
                        })
                        _log_wrapper_for_caller_info("CONNECTION_STATUS_SENT", details=f"Sent connected status to client {request.sid}: {ip}:{port}")
                    else:
                        # Fallback to config values if connection details not available
                        from config import DRONE_TCP_ADDRESS, DRONE_TCP_PORT
                        emit('connection_status', {
                            'status': 'connected',
                            'ip': DRONE_TCP_ADDRESS,
                            'port': DRONE_TCP_PORT
                        })
                        _log_wrapper_for_caller_info("CONNECTION_STATUS_SENT_CONFIG", details=f"Sent connected status to client {request.sid} using config: {DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}")
                except Exception as e:
                    # Fallback if we can't get the connection details
                    emit('connection_status', {
                        'status': 'connected',
                        'ip': 'unknown',
                        'port': 'unknown'
                    })
                    _log_wrapper_for_caller_info("CONNECTION_STATUS_SENT_FALLBACK", details=f"Sent connected status to client {request.sid} with unknown IP/port due to error: {e}")
            else:
                emit('connection_status', {
                    'status': 'disconnected'
                })
        else:
            emit('connection_status', {
                'status': 'disconnected'
            })
        
        print(f"Web UI Client {request.sid} connected. Initial telemetry sent.")

    @_socketio.on('disconnect')
    def handle_disconnect():
        _log_wrapper_for_caller_info("CLIENT_DISCONNECTED", details=f"Client {request.sid} disconnected.")
        print(f"Web UI Client {request.sid} disconnected.")

    @_socketio.on('send_command')
    def handle_send_command(data):
        """Handles commands received from the web UI."""
#        print(f"DEBUG: handle_send_command (socketio_handlers) received data: {data}")
        cmd = data.get('command')
        log_data = {k: v for k, v in data.items() if k != 'command'}
        #_log_wrapper_for_caller_info(f"RECEIVED_{cmd}", str(log_data) if log_data else None, "Command received from UI", "INFO")

        success = False
        msg = f'{cmd} processing...'
        cmd_type = 'info'

        if not _drone_state.get("connected", False):
            msg = f'CMD {cmd} Fail: Disconnected.'
            cmd_type = 'error'
            _log_wrapper_for_caller_info(cmd, None, f"ERROR: {msg}", "ERROR")
            emit('status_message', {'text': msg, 'type': cmd_type})
            emit('command_result', {'command': cmd, 'success': False, 'message': msg})
            return

        if cmd == 'ARM':
            # Check if current mode is armable
            current_mode = _drone_state.get('mode', 'UNKNOWN')
            if current_mode == 'RTL':
                success = False
                msg = f'ARM Failed: RTL mode is not armable. Please change to an armable mode like GUIDED or STABILIZE first.'
                cmd_type = 'error'
                _log_wrapper_for_caller_info("ARM_REJECTED", {"current_mode": current_mode}, 
                                       f"Cannot ARM in {current_mode} mode. Set to STABILIZE, LOITER, or ALT_HOLD first.", 
                                       "WARNING")
                # Store additional command details for the ACK handler
                _pending_commands_dict[mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM] = {
                    'timestamp': time.time(),
                    'ui_command_name': 'ARM'
                }
                
                # Send direct MAVLink ARM command
                success, msg_send = _send_mavlink_command_handler(
                    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                    p1=1  # 1 to arm, 0 to disarm
                )
                cmd_type = 'info' if success else 'error'
                msg = f'ARM command sent.' if success else f'ARM Failed: {msg_send}'
            else:
                # Store additional command details for the ACK handler
                _pending_commands_dict[mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM] = {
                    'timestamp': time.time(),
                    'ui_command_name': 'ARM'
                }
                
                # Send direct MAVLink ARM command
                success, msg_send = _send_mavlink_command_handler(
                    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                    p1=1  # 1 to arm, 0 to disarm
                )
                cmd_type = 'info' if success else 'error'
                msg = f'ARM command sent.' if success else f'ARM Failed: {msg_send}'
        elif cmd == 'DISARM':
            # Store additional command details for the ACK handler
            _pending_commands_dict[mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM] = {
                'timestamp': time.time(),
                'ui_command_name': 'DISARM'
            }
            
            # Send direct MAVLink DISARM command
            success, msg_send = _send_mavlink_command_handler(
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                p1=0  # 1 to arm, 0 to disarm
            )
            cmd_type = 'info' if success else 'error'
            msg = f'DISARM command sent.' if success else f'DISARM Failed: {msg_send}'
        elif cmd == 'TAKEOFF':
            try:
                alt = float(data.get('altitude', 5.0))
                if not (0 < alt <= 1000):
                    raise ValueError("Altitude must be > 0 and <= 1000")
                
                # Send direct MAVLink TAKEOFF command
                success, msg_send = _send_mavlink_command_handler(
                    mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                    p7=alt  # param7 = altitude
                )
                cmd_type = 'info' if success else 'error'
                msg = f'Takeoff to {alt:.1f}m command sent.' if success else f'TAKEOFF Failed: {msg_send}'
            except (ValueError, TypeError) as e:
                success = False
                msg = f"TAKEOFF Error: Invalid altitude '{data.get('altitude')}'. Details: {e}"
                cmd_type = 'error'
                _log_wrapper_for_caller_info("TAKEOFF", {"altitude": data.get('altitude')}, f"EXCEPTION: {msg}", "ERROR")
        elif cmd == 'LAND':
            success, msg_send = _send_mavlink_command_handler(mavutil.mavlink.MAV_CMD_NAV_LAND)
            cmd_type = 'info' if success else 'error'
            msg = 'LAND command sent.' if success else f'LAND Failed: {msg_send}'
        elif cmd == 'RTL':
            success, msg_send = _send_mavlink_command_handler(mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
            cmd_type = 'info' if success else 'error'
            msg = 'RTL command sent.' if success else f'RTL Failed: {msg_send}'
        elif cmd == 'SET_MODE':
            mode_name = data.get('mode_name', '').upper()
            if mode_name in _AP_MODE_NAME_TO_ID:
                mode_id = _AP_MODE_NAME_TO_ID[mode_name]
                
                #_log_wrapper_for_caller_info("SET_MODE_REQUEST", {"mode_name": mode_name}, 
                                   #f"Attempting to set mode to {mode_name}", "INFO")
                
                # Store additional command details for the ACK handler
                _pending_commands_dict[mavutil.mavlink.MAV_CMD_DO_SET_MODE] = {
                    'timestamp': time.time(),
                    'ui_command_name': 'SET_MODE',
                    'mode_name': mode_name
                }
                
                # Send direct MAVLink SET_MODE command
                success, msg_send = _send_mavlink_command_handler(
                    mavutil.mavlink.MAV_CMD_DO_SET_MODE,
                    p1=mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    p2=mode_id
                )
                cmd_type = 'info' if success else 'error'
                msg = f'SET_MODE to {mode_name} command sent.' if success else f'SET_MODE Failed: {msg_send}'
            else:
                success = False
                msg = f"SET_MODE Failed: Unknown mode '{mode_name}'"
                cmd_type = 'error'
                _log_wrapper_for_caller_info("SET_MODE", {"mode_name": mode_name}, f"ERROR: {msg}", "ERROR")
        elif cmd == 'REQUEST_HOME':
            _log_wrapper_for_caller_info("REQUEST_HOME", None, "UI requested home position update.", "INFO")
            # Actual MAVLink request for home should be managed elsewhere (e.g., periodic or by mavlink_connection_manager)
            msg = "Home position request noted. System will update if available."
            success = True 
            cmd_type = 'info'
        elif cmd == 'REQUEST_FENCE':
            _log_wrapper_for_caller_info("REQUEST_FENCE", None, "UI requested fence data.", "INFO")
            if _schedule_fence_request_in_app:
                _schedule_fence_request_in_app()
                msg = "Fence data request scheduled."
                success = True
            else:
                msg = "Fence request handler not available."
                success = False
                cmd_type = 'error'
        elif cmd == 'REQUEST_MISSION':
            _log_wrapper_for_caller_info("REQUEST_MISSION", None, "UI requested mission data.", "INFO")
            if _schedule_mission_request_in_app:
                _schedule_mission_request_in_app()
                msg = "Mission data request scheduled."
                success = True
            else:
                msg = "Mission request handler not available."
                success = False
                cmd_type = 'error'
        elif cmd == 'CLEAR_MISSION':
            success, msg_send = _send_mavlink_command_handler(mavutil.mavlink.MAV_CMD_MISSION_CLEAR_ALL, p2=0) # p2=0 for MAV_MISSION_TYPE_ALL
            cmd_type = 'info' if success else 'error'
            msg = 'CLEAR_MISSION command sent.' if success else f'CLEAR_MISSION Failed: {msg_send}'
        elif cmd == 'GOTO':
            try:
                lat = float(data.get('lat'))
                lon = float(data.get('lon'))
                # Use current relative altitude as default if not provided
                current_rel_alt = _drone_state.get('alt_rel', 10.0)
                alt = float(data.get('alt', current_rel_alt))
                
                _log_wrapper_for_caller_info("GOTO_START", data, f"Initiating GOTO to Lat:{lat:.7f}, Lon:{lon:.7f}, Alt:{alt:.1f}m using SET_POSITION_TARGET_GLOBAL_INT", "INFO")
                
                current_mav_connection = _get_mavlink_connection()
                
                if current_mav_connection and hasattr(current_mav_connection, 'target_system') and current_mav_connection.target_system != 0:
                    current_target_system = current_mav_connection.target_system
                    current_target_component = current_mav_connection.target_component

                    # Set type mask to ignore velocities, accelerations, and yaw
                    type_mask = (
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_VX_IGNORE |
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_VY_IGNORE |
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_VZ_IGNORE |
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE |
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE |
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_IGNORE |
                        mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE
                    )

                    current_mav_connection.mav.set_position_target_global_int_send(
                        0,  # time_boot_ms
                        current_target_system, current_target_component,
                        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                        type_mask,
                        int(lat * 1e7), int(lon * 1e7), alt,
                        0, 0, 0, 0, 0, 0, 0, 0  # vx, vy, vz, afx, afy, afz, yaw, yaw_rate (all ignored)
                    )
                    success = True
                    msg = f'GOTO to Lat:{lat:.7f}, Lon:{lon:.7f}, Alt:{alt:.1f}m command sent using SET_POSITION_TARGET_GLOBAL_INT.'
                    _log_wrapper_for_caller_info("GOTO_SENT", data, msg, "INFO")
                else:
                    success = False
                    msg = "GOTO Failed: MAVLink connection not available or target system not identified."
                    if current_mav_connection and hasattr(current_mav_connection, 'target_system'):
                        msg += f" (target_sys={current_mav_connection.target_system})"
                    _log_wrapper_for_caller_info("GOTO_FAIL", data, msg, "ERROR")
                
                cmd_type = 'info' if success else 'error'
                
            except (ValueError, TypeError) as e:
                success = False
                msg = f"GOTO Error: Invalid coordinates - lat: '{data.get('lat')}', lon: '{data.get('lon')}', alt: '{data.get('alt')}'. Details: {e}"
                cmd_type = 'error'
                _log_wrapper_for_caller_info("GOTO_ERROR", data, f"EXCEPTION: {msg}", "ERROR")
            except Exception as e:
                success = False
                msg = f"GOTO Error: Unexpected error processing GOTO command: {str(e)}"
                cmd_type = 'error'
                _log_wrapper_for_caller_info("GOTO_ERROR_EXC", data, f"EXCEPTION: {msg}", "ERROR")
        else:
            msg = f'Unknown command: {cmd}'
            cmd_type = 'warning'
            _log_wrapper_for_caller_info(cmd, data, f"WARNING: {msg}", "WARNING")

        if cmd != 'SET_MODE':
            _log_wrapper_for_caller_info(cmd, data, f"Result: {msg}", cmd_type.upper())
        emit('status_message', {'text': msg, 'type': cmd_type})
        emit('command_result', {'command': cmd, 'success': success, 'message': msg})

    @_socketio.on('goto_location')
    def goto_location(sid, data):
        print(f"[GOTO_HANDLER_DEBUG] 'goto_location' event received. SID: {sid}, Data: {data}")
        global _drone_state # _log_command_action and _get_mavlink_connection are in enclosing scope

        try:
            lat = float(data.get('lat'))
            lon = float(data.get('lon'))
            # Use a safe way to access _drone_state, assuming it's a shared dictionary
            current_rel_alt = _drone_state.get('alt_rel', 10.0) # Default to 10m if not available
            alt = float(data.get('alt', current_rel_alt))

            _log_wrapper_for_caller_info("GOTO_START", data, f"Initiating GOTO to Lat:{lat:.7f}, Lon:{lon:.7f}, Alt:{alt:.1f}m using SET_POSITION_TARGET_GLOBAL_INT", "INFO")
            
            current_mav_connection = _get_mavlink_connection()

            if current_mav_connection and hasattr(current_mav_connection, 'target_system') and current_mav_connection.target_system != 0:
                current_target_system = current_mav_connection.target_system
                current_target_component = current_mav_connection.target_component

                type_mask = (
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_VX_IGNORE |
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_VY_IGNORE |
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_VZ_IGNORE |
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE |
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE |
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_IGNORE |
                    mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE
                )

                current_mav_connection.mav.set_position_target_global_int_send(
                    0,  # time_boot_ms
                    current_target_system, current_target_component,
                    mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                    type_mask,
                    int(lat * 1e7), int(lon * 1e7), alt,
                    0, 0, 0, 0, 0, 0, 0, 0 # vx, vy, vz, afx, afy, afz, yaw, yaw_rate (all ignored)
                )
                success = True
                msg_send = 'GOTO (SET_POSITION_TARGET_GLOBAL_INT) command sent successfully.'
                _log_wrapper_for_caller_info("GOTO_SENT", data, msg_send, "INFO")
            else:
                success = False
                msg_send = "GOTO Failed: MAVLink connection not available or target system not identified."
                if current_mav_connection and hasattr(current_mav_connection, 'target_system'):
                    msg_send += f" (Details: conn_target_sys={current_mav_connection.target_system})"
                elif current_mav_connection:
                    msg_send += " (Details: target_system attribute missing on connection object)"
                else:
                    msg_send += " (Details: no MAVLink connection object retrieved)"
                _log_wrapper_for_caller_info("GOTO_FAIL", data, msg_send, "ERROR")

            cmd_type = 'info' if success else 'error'
            emit('goto_feedback', {'status': cmd_type, 'message': msg_send}, room=sid)
        except ValueError as e:
            _log_wrapper_for_caller_info("GOTO_ERROR_VAL", data, f"ValueError in GOTO: {str(e)}", "ERROR")
            emit('goto_feedback', {'status': 'error', 'message': f'Invalid GOTO parameters: {str(e)}'}, room=sid)
        except Exception as e:
            _log_wrapper_for_caller_info("GOTO_ERROR_EXC", data, f"Exception in GOTO: {str(e)}", "ERROR")
            emit('goto_feedback', {'status': 'error', 'message': f'Error processing GOTO command: {str(e)}'}, room=sid)

    @_socketio.on('drone_connect')
    def handle_drone_connect(data):
        """Handle drone connection request with custom IP and port."""
        _log_wrapper_for_caller_info("DRONE_CONNECT_REQUEST", data, "UI requested connection to custom IP/port", "INFO")
        
        try:
            ip = data.get('ip', '').strip()
            port = data.get('port')
            
            # Validate inputs
            if not ip:
                emit('connection_status', {
                    'status': 'error',
                    'message': 'IP address is required'
                })
                return
                
            if not port or not isinstance(port, int) or port < 1 or port > 65535:
                emit('connection_status', {
                    'status': 'error', 
                    'message': 'Valid port number (1-65535) is required'
                })
                return
            
            # Emit connecting status
            emit('connection_status', {
                'status': 'connecting',
                'ip': ip,
                'port': port
            })
            
            # Import needed functions from app context
            from mavlink_connection_manager import force_reconnect_with_new_address
            
            # Create new connection string
            connection_string = f'tcp:{ip}:{port}'
            
            # Get drone_state_lock from app context (we need to add this to the context)
            drone_state_lock = globals().get('_drone_state_lock')
            
            # Trigger reconnection with new address
            success = force_reconnect_with_new_address(connection_string, _drone_state, drone_state_lock)
            
            if success:
                emit('connection_status', {
                    'status': 'connected',
                    'ip': ip,
                    'port': port
                })
                _log_wrapper_for_caller_info("DRONE_CONNECT_SUCCESS", data, f"Successfully connected to {ip}:{port}", "INFO")
            else:
                emit('connection_status', {
                    'status': 'error',
                    'message': f'Failed to connect to {ip}:{port}'
                })
                _log_wrapper_for_caller_info("DRONE_CONNECT_FAILED", data, f"Failed to connect to {ip}:{port}", "ERROR")
                
        except Exception as e:
            _log_wrapper_for_caller_info("DRONE_CONNECT_ERROR", data, f"Exception during connection: {str(e)}", "ERROR")
            emit('connection_status', {
                'status': 'error',
                'message': f'Connection error: {str(e)}'
            })

    @_socketio.on('drone_disconnect')
    def handle_drone_disconnect():
        """Handle drone disconnection request."""
        _log_wrapper_for_caller_info("DRONE_DISCONNECT_REQUEST", None, "UI requested disconnection", "INFO")
        
        try:
            # Import needed functions from app context
            from mavlink_connection_manager import force_disconnect
            
            # Get drone_state_lock from app context
            drone_state_lock = globals().get('_drone_state_lock')
            
            # Trigger disconnection
            force_disconnect(_drone_state, drone_state_lock)
            
            emit('connection_status', {
                'status': 'disconnected'
            })
            _log_wrapper_for_caller_info("DRONE_DISCONNECT_SUCCESS", None, "Successfully disconnected", "INFO")
            
        except Exception as e:
            _log_wrapper_for_caller_info("DRONE_DISCONNECT_ERROR", None, f"Exception during disconnection: {str(e)}", "ERROR")
            emit('connection_status', {
                'status': 'error',
                'message': f'Disconnection error: {str(e)}'
            })

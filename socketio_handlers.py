# /home/peter/Documents/WScode/WebGCS/socketio_handlers.py
import time
import traceback
import math
from flask import request # For request.sid
from flask_socketio import emit
from pymavlink import mavutil

# --- Context variables to be initialized by app.py ---
_socketio = None
_log_command_action = None
_get_mavlink_connection = None
_drone_state = None
_pending_commands_dict = None 
_AP_MODE_NAME_TO_ID = None
_schedule_fence_request_in_app = None
_schedule_mission_request_in_app = None

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
        
        _log_command_action(command, params, f"Command sent to telemetry bridge: {command}", "INFO")
        return True
    except Exception as e:
        _log_command_action(command, params, f"Error sending command to telemetry bridge: {e}", "ERROR")
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
        _log_command_action(cmd_name, None, f"ERROR: {warn_msg}", "ERROR")
        return (False, warn_msg)

    target_sys = current_mavlink_connection.target_system
    target_comp = current_mavlink_connection.target_component

    if target_sys == 0:
        err_msg = f"CMD {cmd_name} Failed: Invalid target system."
        _log_command_action(cmd_name, None, f"ERROR: {err_msg}", "ERROR")
        return (False, err_msg)

    try:
        params_str = f"p1={p1:.2f}, p2={p2:.2f}, p3={p3:.2f}, p4={p4:.2f}, p5={p5:.6f}, p6={p6:.6f}, p7={p7:.2f}"
        _log_command_action(cmd_name, params_str, f"To SYS:{target_sys} COMP:{target_comp}", "INFO")
        
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
        _log_command_action(cmd_name, None, f"EXCEPTION: {err_msg}", "ERROR")
        traceback.print_exc()
        return (False, err_msg)

# --- Initialization Function ---
def init_socketio_handlers(socketio_instance, app_context):
    global _socketio, _log_command_action, _get_mavlink_connection
    global _drone_state, _pending_commands_dict, _AP_MODE_NAME_TO_ID
    global _schedule_fence_request_in_app, _schedule_mission_request_in_app

    _socketio = socketio_instance
    _log_command_action = app_context['log_command_action']
    _get_mavlink_connection = app_context['get_mavlink_connection']
    _drone_state = app_context['drone_state']
    _pending_commands_dict = app_context['pending_commands_dict']
    _AP_MODE_NAME_TO_ID = app_context['AP_MODE_NAME_TO_ID']
    _schedule_fence_request_in_app = app_context['schedule_fence_request_in_app']
    _schedule_mission_request_in_app = app_context['schedule_mission_request_in_app']

    # --- SocketIO Event Handlers ---
    @_socketio.on('connect')
    def handle_connect():
        _log_command_action("CLIENT_CONNECTED", details=f"Client {request.sid} connected.")
        emit('telemetry_update', _drone_state)
        status_text = 'Backend connected. '
        status_text += 'Drone link active.' if _drone_state.get('connected') else 'Attempting drone link...'
        emit('status_message', {'text': status_text, 'type': 'info'})
        print(f"Web UI Client {request.sid} connected. Initial telemetry sent.")

    @_socketio.on('disconnect')
    def handle_disconnect():
        _log_command_action("CLIENT_DISCONNECTED", details=f"Client {request.sid} disconnected.")
        print(f"Web UI Client {request.sid} disconnected.")

    @_socketio.on('send_command')
    def handle_send_command(data):
        """Handles commands received from the web UI."""
        print(f"DEBUG: handle_send_command (socketio_handlers) received data: {data}")
        cmd = data.get('command')
        log_data = {k: v for k, v in data.items() if k != 'command'}
        _log_command_action(f"RECEIVED_{cmd}", str(log_data) if log_data else None, "Command received from UI", "INFO")

        success = False
        msg = f'{cmd} processing...'
        cmd_type = 'info'

        if not _drone_state.get("connected", False):
            msg = f'CMD {cmd} Fail: Disconnected.'
            cmd_type = 'error'
            _log_command_action(cmd, None, f"ERROR: {msg}", "ERROR")
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
                _log_command_action("ARM_REJECTED", {"current_mode": current_mode}, 
                                   f"ARM command rejected: {current_mode} mode not armable", "ERROR")
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
                _log_command_action("TAKEOFF", {"altitude": data.get('altitude')}, f"EXCEPTION: {msg}", "ERROR")
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
                
                _log_command_action("SET_MODE_REQUEST", {"mode_name": mode_name}, 
                                   f"Attempting to set mode to {mode_name}", "INFO")
                
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
                _log_command_action("SET_MODE", {"mode_name": mode_name}, f"ERROR: {msg}", "ERROR")
        elif cmd == 'GOTO':
            try:
                lat = float(data.get('lat'))
                lon = float(data.get('lon'))
                alt = float(data.get('alt', _drone_state.get('alt_rel', 10.0)))  # Default to current rel alt or 10m

                _log_command_action("GOTO_START", data, f"Initiating GOTO to Lat:{lat:.7f}, Lon:{lon:.7f}, Alt:{alt:.1f}m", "INFO")
                
                # Send direct MAVLink GOTO command (using SET_POSITION_TARGET_GLOBAL_INT)
                # For now, use a simpler waypoint approach with MAV_CMD_NAV_WAYPOINT
                success, msg_send = _send_mavlink_command_handler(
                    mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                    p5=lat,  # latitude
                    p6=lon,  # longitude  
                    p7=alt   # altitude
                )
                cmd_type = 'info' if success else 'error'
                msg = f'GOTO command sent.' if success else f'GOTO Failed: {msg_send}'
                
            except (ValueError, TypeError) as e:
                success = False
                msg = f"GOTO Error: Invalid coordinates/altitude. Data: {data}. Details: {e}"
                cmd_type = 'error'
                _log_command_action("GOTO", data, f"EXCEPTION: {msg}", "ERROR")
            except Exception as e:  # Catch any other unexpected errors
                success = False
                msg = f"GOTO Unexpected Error: {e}"
                cmd_type = 'error'
                _log_command_action("GOTO", data, f"UNEXPECTED EXCEPTION: {msg} - {traceback.format_exc()}", "ERROR")
        elif cmd == 'REQUEST_HOME':
            _log_command_action("REQUEST_HOME", None, "UI requested home position update.", "INFO")
            # Actual MAVLink request for home should be managed elsewhere (e.g., periodic or by mavlink_connection_manager)
            msg = "Home position request noted. System will update if available."
            success = True 
            cmd_type = 'info'
        elif cmd == 'REQUEST_FENCE':
            _log_command_action("REQUEST_FENCE", None, "UI requested fence data.", "INFO")
            if _schedule_fence_request_in_app:
                _schedule_fence_request_in_app()
                msg = "Fence data request scheduled."
                success = True
            else:
                msg = "Fence request handler not available."
                success = False
                cmd_type = 'error'
        elif cmd == 'REQUEST_MISSION':
            _log_command_action("REQUEST_MISSION", None, "UI requested mission data.", "INFO")
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
        else:
            msg = f'Unknown command: {cmd}'
            cmd_type = 'warning'
            _log_command_action(cmd, data, f"WARNING: {msg}", "WARNING")

        _log_command_action(cmd, data, f"Result: {msg}", cmd_type.upper())
        emit('status_message', {'text': msg, 'type': cmd_type})
        emit('command_result', {'command': cmd, 'success': success, 'message': msg})

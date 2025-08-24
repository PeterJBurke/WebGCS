# /home/peter/Documents/WScode/WebGCS/request_handlers.py
import time
import traceback
from pymavlink import mavutil

# --- Context variables to be initialized by app.py --- 
_socketio = None
_get_mavlink_connection = None
_drone_state = None
_drone_state_lock = None # Added
_log_command_action = None # Added
_fence_request_lock = None
_mission_request_lock = None
_app_shared_state = {} # Renamed from _app_context for clarity

def init_request_handlers(context):
    """Initializes the request handlers with necessary context from app.py."""
    global _socketio, _get_mavlink_connection, _drone_state, _drone_state_lock, _log_command_action
    global _fence_request_lock, _mission_request_lock, _app_shared_state

    _socketio = context.get('socketio')
    _get_mavlink_connection = context.get('get_mavlink_connection')
    _drone_state = context.get('drone_state')
    _drone_state_lock = context.get('drone_state_lock')
    _log_command_action = context.get('log_command_action')
    _fence_request_lock = context.get('fence_request_lock')
    _mission_request_lock = context.get('mission_request_lock')
    _app_shared_state = context.get('app_shared_state') # This is the shared dictionary from app.py

def _execute_fence_request():
    """Executes the fence request logic. Called from app.py's main loop."""
    # Access pending flag via _app_context
    with _fence_request_lock:
        if not _app_shared_state.get('fence_request_pending', False):
            return # Should not happen if called correctly by app.py
        _app_shared_state['fence_request_pending'] = False
        
    print("\n--- Executing Pending Fence Request (in request_handlers.py) ---")
    status_msg = "Starting fence request..."
    cmd_type = 'info'
    success = False
    fence_points = []
    mavlink_connection = _get_mavlink_connection()
    
    try:
        if not mavlink_connection or not _drone_state.get("connected", False):
            raise Exception("Cannot request fence: Drone not connected.")

        target_sys = mavlink_connection.target_system
        target_comp = mavlink_connection.target_component
        print(f"Requesting mission list for SYS:{target_sys} COMP:{target_comp}...")

        mavlink_connection.mav.mission_request_list_send(
            target_sys, target_comp, mavutil.mavlink.MAV_MISSION_TYPE_FENCE
        )

        print("Waiting for MISSION_COUNT...")
        msg = mavlink_connection.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)

        if not msg:
            raise Exception("Timeout waiting for MISSION_COUNT.")
        if msg.mission_type != mavutil.mavlink.MAV_MISSION_TYPE_FENCE:
            raise Exception(f"Received MISSION_COUNT for wrong mission type: {msg.mission_type}")

        fence_count = msg.count
        print(f"Found {fence_count} fence items.")
        _socketio.emit('status_message', {'text': f"Found {fence_count} fence points", 'type': 'info'})

        if fence_count == 0:
            status_msg = "No fence points defined."
            cmd_type = 'warning'
            success = True
            # Update global fence_points_list in app.py if needed via _app_context
            if 'fence_points_list' in _app_shared_state:
                _app_shared_state['fence_points_list'] = []
        else:
            for seq in range(fence_count):
                print(f"Requesting fence point {seq + 1}/{fence_count}...")
                mavlink_connection.mav.mission_request_send(
                    target_sys, target_comp, seq, mavutil.mavlink.MAV_MISSION_TYPE_FENCE
                )
                print("Waiting for MISSION_ITEM...")
                item = mavlink_connection.recv_match(type='MISSION_ITEM', blocking=True, timeout=5)
                if not item:
                    raise Exception(f"Timeout waiting for MISSION_ITEM {seq}.")
                
                lat = item.x / 1e7 if abs(item.x) > 180 else item.x
                lon = item.y / 1e7 if abs(item.y) > 180 else item.y
                print(f"  Point {seq+1}: Lat={lat:.7f}, Lon={lon:.7f}, Alt={item.z:.2f}")
                fence_points.append([lat, lon])

            if 'fence_points_list' in _app_shared_state:
                 _app_shared_state['fence_points_list'] = list(fence_points) # Store a copy
            
            print("\nFence Summary:")
            print("-------------")
            for idx, point in enumerate(fence_points):
                print(f"Point {idx + 1}: Lat={point[0]:.7f}, Lon={point[1]:.7f}")
            
            _socketio.emit('geofence_update', {'points': fence_points})
            status_msg = f"Retrieved {fence_count} fence points successfully."
            cmd_type = 'info'
            success = True

    except Exception as e:
        status_msg = f"Error during fence request: {e}"
        cmd_type = 'error'
        success = False
        print(f"\nError: {status_msg}")
        traceback.print_exc()

    finally:
        print("--- Fence Request Execution Finished (in request_handlers.py) ---")
        _socketio.emit('status_message', {'text': status_msg, 'type': cmd_type})
        _socketio.emit('command_result', {'command': 'REQUEST_FENCE', 'success': success, 'message': status_msg})

def _execute_mission_request():
    """Executes the mission request logic. Called from app.py's main loop."""
    with _mission_request_lock:
        if not _app_shared_state.get('mission_request_pending', False):
            return # Should not happen
        _app_shared_state['mission_request_pending'] = False
        
    print("\n--- Executing Pending Mission Request (in request_handlers.py) ---")
    status_msg = "Starting mission request..."
    cmd_type = 'info'
    success = False
    waypoints = []
    mavlink_connection = _get_mavlink_connection()
    
    try:
        if not mavlink_connection or not _drone_state.get("connected", False):
            raise Exception("Cannot request mission: Drone not connected.")

        target_sys = mavlink_connection.target_system
        target_comp = mavlink_connection.target_component
        print(f"Requesting mission list for SYS:{target_sys} COMP:{target_comp}...")

        mavlink_connection.mav.mission_request_list_send(
            target_sys, target_comp, mavutil.mavlink.MAV_MISSION_TYPE_MISSION
        )

        print("Waiting for MISSION_COUNT...")
        msg = mavlink_connection.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)

        if not msg:
            raise Exception("Timeout waiting for MISSION_COUNT.")
        if msg.mission_type != mavutil.mavlink.MAV_MISSION_TYPE_MISSION:
            raise Exception(f"Received MISSION_COUNT for wrong mission type: {msg.mission_type}")

        waypoint_count = msg.count
        print(f"Found {waypoint_count} mission waypoints.")
        _socketio.emit('status_message', {'text': f"Found {waypoint_count} waypoints", 'type': 'info'})

        if waypoint_count == 0:
            status_msg = "No mission waypoints defined."
            cmd_type = 'warning'
            success = True
            _socketio.emit('mission_update', {'waypoints': []})
            if 'waypoints_list' in _app_shared_state:
                _app_shared_state['waypoints_list'] = []
        else:
            for seq in range(waypoint_count):
                print(f"Requesting waypoint {seq + 1}/{waypoint_count}...")
                mavlink_connection.mav.mission_request_send(
                    target_sys, target_comp, seq, mavutil.mavlink.MAV_MISSION_TYPE_MISSION
                )
                print("Waiting for MISSION_ITEM...")
                item = mavlink_connection.recv_match(type='MISSION_ITEM', blocking=True, timeout=5)
                if not item:
                    raise Exception(f"Timeout waiting for MISSION_ITEM {seq}.")
                
                lat = item.x
                lon = item.y
                alt = item.z
                cmd = item.command
                frame = item.frame
                param1 = item.param1
                param2 = item.param2
                param3 = item.param3
                param4 = item.param4
                
                cmd_name = "UNKNOWN"
                if hasattr(mavutil.mavlink, 'enums') and 'MAV_CMD' in mavutil.mavlink.enums:
                    if cmd in mavutil.mavlink.enums['MAV_CMD']:
                        cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name
                
                frame_name = "UNKNOWN"
                if hasattr(mavutil.mavlink, 'enums') and 'MAV_FRAME' in mavutil.mavlink.enums:
                    if frame in mavutil.mavlink.enums['MAV_FRAME']:
                        frame_name = mavutil.mavlink.enums['MAV_FRAME'][frame].name
                
                print(f"  Command: {cmd} ({cmd_name})")
                print(f"  Frame: {frame} ({frame_name})")
                print(f"  Location: Lat={lat:.7f}, Lon={lon:.7f}, Alt={alt:.2f}m")
                print(f"  Parameters: [{param1:.2f}, {param2:.2f}, {param3:.2f}, {param4:.2f}]")
                
                waypoints.append({
                    'seq': item.seq,
                    'command': cmd,
                    'command_name': cmd_name,
                    'frame': frame,
                    'frame_name': frame_name,
                    'lat': lat,
                    'lon': lon,
                    'alt': alt,
                    'param1': param1,
                    'param2': param2,
                    'param3': param3,
                    'param4': param4
                })

            mavlink_connection.mav.mission_ack_send(
                target_sys, target_comp, 
                mavutil.mavlink.MAV_MISSION_ACCEPTED,
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )

            if 'waypoints_list' in _app_shared_state:
                _app_shared_state['waypoints_list'] = list(waypoints) # Store a copy

            print("\nMission Summary:")
            print("----------------")
            for i, wp in enumerate(waypoints):
                cmd_desc = f"{wp['command']} ({wp['command_name']})"
                if wp['command'] == mavutil.mavlink.MAV_CMD_NAV_WAYPOINT:
                    print(f"WP #{i+1}: WAYPOINT at Lat={wp['lat']:.7f}, Lon={wp['lon']:.7f}, Alt={wp['alt']:.2f}m")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF:
                    print(f"WP #{i+1}: TAKEOFF to Alt={wp['alt']:.2f}m")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_NAV_LAND:
                    print(f"WP #{i+1}: LAND at Lat={wp['lat']:.7f}, Lon={wp['lon']:.7f}")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH:
                    print(f"WP #{i+1}: RETURN TO LAUNCH")
                elif wp['command'] == mavutil.mavlink.MAV_CMD_DO_JUMP:
                    print(f"WP #{i+1}: DO JUMP to #{int(wp['param1'])+1}, {int(wp['param2'])} times")
                # Add more mission item types as needed
                else:
                    print(f"WP #{i+1}: {cmd_desc} - Params: {wp['param1']:.1f}, {wp['param2']:.1f}, {wp['param3']:.1f}, {wp['param4']:.1f}, Lat:{wp['lat']:.5f}, Lon:{wp['lon']:.5f}, Alt:{wp['alt']:.1f}")

            _socketio.emit('mission_update', {'waypoints': waypoints})
            status_msg = f"Retrieved {waypoint_count} waypoints successfully."
            cmd_type = 'info'
            success = True

    except Exception as e:
        status_msg = f"Error during mission request: {e}"
        cmd_type = 'error'
        success = False
        print(f"\nError: {status_msg}")
        traceback.print_exc()

    finally:
        print("--- Mission Request Execution Finished (in request_handlers.py) ---")
        _socketio.emit('status_message', {'text': status_msg, 'type': cmd_type})
        _socketio.emit('command_result', {'command': 'REQUEST_MISSION', 'success': success, 'message': status_msg})

#!/usr/bin/env python3

from pymavlink import mavutil
import time
import sys
from config import MAVLINK_CONNECTION_STRING

def connect_mavlink(connection_string):
    """Establish MAVLink connection to the drone."""
    print(f"Connecting to drone on {connection_string}")
    try:
        return mavutil.mavlink_connection(connection_string)
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def wait_heartbeat(mav_connection):
    """Wait for the first heartbeat from the drone."""
    print("Waiting for heartbeat...")
    mav_connection.wait_heartbeat()
    print("Heartbeat received!")
    print(f"Connected to system {mav_connection.target_system} component {mav_connection.target_component}")

def request_mission_data(mav_connection):
    """Request and display mission waypoints from the drone."""
    if not mav_connection:
        print("No connection available")
        return False

    try:
        print("\nRequesting mission list...")
        # Request the mission list
        mav_connection.mav.mission_request_list_send(
            mav_connection.target_system,
            mav_connection.target_component,
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION  # 0 = Mission (waypoints)
        )

        # Wait for MISSION_COUNT
        print("Waiting for MISSION_COUNT...")
        msg = mav_connection.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)
        if not msg:
            print("No response to mission list request")
            return False
        if msg.mission_type != mavutil.mavlink.MAV_MISSION_TYPE_MISSION:
            print(f"Received mission count but wrong type: {msg.mission_type}")
            return False

        waypoint_count = msg.count
        print(f"\nNumber of waypoints: {waypoint_count}")
        
        if waypoint_count == 0:
            print("No waypoints defined")
            return True

        waypoints = []

        # Request each waypoint
        for seq in range(waypoint_count):
            print(f"\nRequesting waypoint {seq + 1}/{waypoint_count}")
            mav_connection.mav.mission_request_send(
                mav_connection.target_system,
                mav_connection.target_component,
                seq,
                mavutil.mavlink.MAV_MISSION_TYPE_MISSION
            )

            item = mav_connection.recv_match(type='MISSION_ITEM', blocking=True, timeout=5)
            if item:
                # Process waypoint data
                lat = item.x
                lon = item.y
                alt = item.z
                cmd = item.command
                frame = item.frame
                param1 = item.param1
                param2 = item.param2
                param3 = item.param3
                param4 = item.param4
                
                # Get command name if available
                cmd_name = "UNKNOWN"
                if hasattr(mavutil.mavlink, 'enums') and 'MAV_CMD' in mavutil.mavlink.enums:
                    if cmd in mavutil.mavlink.enums['MAV_CMD']:
                        cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd].name
                
                # Get frame name if available
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
            else:
                print(f"Timeout waiting for waypoint {seq}")
                return False

        # Send mission acknowledgment
        mav_connection.mav.mission_ack_send(
            mav_connection.target_system,
            mav_connection.target_component,
            mavutil.mavlink.MAV_MISSION_ACCEPTED,
            mavutil.mavlink.MAV_MISSION_TYPE_MISSION
        )

        # Print summary
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
            else:
                print(f"WP #{i+1}: {cmd_desc} at Lat={wp['lat']:.7f}, Lon={wp['lon']:.7f}, Alt={wp['alt']:.2f}m")

        return True

    except Exception as e:
        print(f"Error requesting mission: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # Default to the configured connection string or allow command line override
    connection_string = MAVLINK_CONNECTION_STRING
    
    # Allow connection string override from command line
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]

    # Connect to the drone
    mav_connection = connect_mavlink(connection_string)
    if not mav_connection:
        sys.exit(1)

    # Wait for heartbeat
    try:
        wait_heartbeat(mav_connection)
    except KeyboardInterrupt:
        print("\nUser interrupted while waiting for heartbeat")
        sys.exit(1)
    except Exception as e:
        print(f"\nError waiting for heartbeat: {e}")
        sys.exit(1)

    # Request mission data
    if not request_mission_data(mav_connection):
        print("\nFailed to retrieve complete mission data")
        sys.exit(1)
    
    print("\nMission data retrieval complete")

if __name__ == "__main__":
    main() 
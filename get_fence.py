#!/usr/bin/env python3

from pymavlink import mavutil
import time
import sys

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

def request_geofence_data(mav_connection):
    """Request and display geofence data from the drone."""
    if not mav_connection:
        print("No connection available")
        return False

    try:
        print("\nRequesting geofence mission list...")
        # Request the geofence mission list
        mav_connection.mav.mission_request_list_send(
            mav_connection.target_system,
            mav_connection.target_component,
            mavutil.mavlink.MAV_MISSION_TYPE_FENCE
        )

        # Wait for MISSION_COUNT
        msg = mav_connection.recv_match(type='MISSION_COUNT', blocking=True, timeout=5)
        if not msg:
            print("No response to mission list request")
            return False
        if msg.mission_type != mavutil.mavlink.MAV_MISSION_TYPE_FENCE:
            print("Received mission count but not for fence")
            return False

        fence_count = msg.count
        print(f"\nNumber of geofence items: {fence_count}")
        
        if fence_count == 0:
            print("No fence points defined")
            return True

        fence_points = []

        # Request each fence point
        for seq in range(fence_count):
            print(f"\nRequesting fence point {seq + 1}/{fence_count}")
            mav_connection.mav.mission_request_send(
                mav_connection.target_system,
                mav_connection.target_component,
                seq,
                mavutil.mavlink.MAV_MISSION_TYPE_FENCE
            )

            item = mav_connection.recv_match(type='MISSION_ITEM', blocking=True, timeout=5)
            if item:
                # Convert lat/lon from int to float degrees
                lat = item.x / 1e7 if abs(item.x) > 180 else item.x
                lon = item.y / 1e7 if abs(item.y) > 180 else item.y
                
                print(f"  Command: {item.command}")
                print(f"  Frame: {item.frame}")
                print(f"  Location: Lat={lat:.7f}, Lon={lon:.7f}, Alt={item.z:.2f}")
                print(f"  Parameters: {[item.param1, item.param2, item.param3, item.param4]}")
                
                fence_points.append({
                    'seq': item.seq,
                    'lat': lat,
                    'lon': lon,
                    'alt': item.z
                })
            else:
                print(f"Timeout waiting for fence point {seq}")
                return False

        # Print summary
        print("\nFence Summary:")
        print("-------------")
        for point in fence_points:
            print(f"Point {point['seq'] + 1}: Lat={point['lat']:.7f}, Lon={point['lon']:.7f}, Alt={point['alt']:.2f}m")

        return True

    except Exception as e:
        print(f"Error requesting geofence: {e}")
        return False

def main():
    # Default connection string - can be overridden by command line argument
    connection_string = "tcp:localhost:5760"
    
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

    # Request geofence data
    if not request_geofence_data(mav_connection):
        print("\nFailed to retrieve complete fence data")
        sys.exit(1)
    
    print("\nFence data retrieval complete")

if __name__ == "__main__":
    main() 
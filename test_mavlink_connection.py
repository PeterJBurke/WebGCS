import time
import sys
from pymavlink import mavutil

# *** MODIFIED: Use Drone's TCP Address and Port ***
connection_string = 'tcp:192.168.1.247:5678'
source_system_id = 254 # ID for this GCS script

print(f"Attempting to connect to drone MAVLink via TCP at: {connection_string}")
print("(Requires drone powered on, MAVLink TCP server running, and network connectivity)")

try:
    # Connect using the TCP string
    conn = mavutil.mavlink_connection(connection_string, source_system=source_system_id)
    print("Waiting up to 10 seconds for the first heartbeat from the drone...")

    # Wait for the first heartbeat message
    heartbeat = conn.wait_heartbeat(timeout=10)

    if heartbeat:
        print(f"SUCCESS: Heartbeat received!")
        print(f"  Drone System ID: {conn.target_system}")
        print(f"  Drone Component ID: {conn.target_component}")
        print(f"  Autopilot Type: {mavutil.mavlink.enums['MAV_AUTOPILOT'][heartbeat.autopilot].name}")
        print(f"  Vehicle Type: {mavutil.mavlink.enums['MAV_TYPE'][heartbeat.type].name}")
        conn.close()
        sys.exit(0)
    else:
        print("FAILED: No heartbeat received within the timeout.")
        print("Troubleshooting:")
        print("  - Is the drone powered on and MAVLink running?")
        print(f"  - Is the drone LISTENING for TCP connections on {connection_string.split(':')[1]}:{connection_string.split(':')[2]}?")
        print("  - Check network connection between desktop and drone (ping, traceroute).")
        print("  - Check desktop firewall (allow OUTGOING TCP to drone's IP/Port).")
        print("  - Check drone's firewall/configuration (allow incoming TCP from desktop IP or any).")
        if conn: conn.close()
        sys.exit(1)

except ConnectionRefusedError:
    print(f"FAILED: Connection Refused.")
    print(f"  Ensure the drone is running a TCP MAVLink server on {connection_string.split(':')[1]}:{connection_string.split(':')[2]}.")
    sys.exit(1)
except OSError as e: # Catch other network errors
    print(f"FAILED: OS Error during connection: {e}")
    print(f"  Check network route to {connection_string.split(':')[1]}.")
    sys.exit(1)
except Exception as e:
    print(f"FAILED: An error occurred during connection or reception: {e}")
    sys.exit(1)

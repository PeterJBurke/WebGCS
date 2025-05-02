from pymavlink import mavutil
import time

# Connection settings
connection_string = 'tcp:192.168.1.247:5678'

print(f"Attempting to connect to {connection_string}")
try:
    # Create connection object with more verbose output
    mav = mavutil.mavlink_connection(
        connection_string,
        source_system=250,
        source_component=1,
        retries=3,
        robust_parsing=True
    )
    
    print("Connection object created, waiting for heartbeat...")
    msg = mav.wait_heartbeat(timeout=10)
    print(f"Heartbeat received! System: {mav.target_system}, Component: {mav.target_component}")
    print(f"Autopilot type: {msg.autopilot}")
    print(f"Vehicle type: {msg.type}")
    print(f"System status: {msg.system_status}")
    
except Exception as e:
    print(f"Connection failed: {str(e)}")
    print("Try these troubleshooting steps:")
    print("1. Verify SITL/drone is running")
    print("2. Check firewall settings")
    print("3. Verify correct IP and port")
    print("4. Try UDP instead: 'udp:192.168.1.247:14550'") 
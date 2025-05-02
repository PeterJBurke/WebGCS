from pymavlink import mavutil
import time

# Connection settings
connection_string = 'udp:0.0.0.0:14550'

print(f"Attempting to connect to {connection_string}")
try:
    # Create connection object with more verbose output
    mav = mavutil.mavlink_connection(
        connection_string,
        source_system=255,  # Using 255 as source system ID
        source_component=0,
        input=True,        # Enable input
        dialect='ardupilotmega'  # Specify the dialect
    )
    
    print("Connection object created, waiting for heartbeat...")
    print("Listening for incoming messages...")
    
    # Listen for messages
    timeout = time.time() + 10  # 10 second timeout
    while time.time() < timeout:
        msg = mav.recv_match(blocking=True, timeout=1)
        if msg:
            print(f"Received message: {msg.get_type()}")
            if msg.get_type() == 'HEARTBEAT':
                print(f"Heartbeat from System: {msg.get_srcSystem()}, Component: {msg.get_srcComponent()}")
                print(f"Autopilot type: {msg.autopilot}")
                print(f"Vehicle type: {msg.type}")
                print(f"System status: {msg.system_status}")
                break
    
except Exception as e:
    print(f"Connection failed: {str(e)}")
    print("Try these troubleshooting steps:")
    print("1. Verify SITL/drone is running")
    print("2. Check firewall settings")
    print("3. Verify correct port (14550 for UDP)")
    print("4. Try TCP instead: 'tcp:127.0.0.1:5760'") 
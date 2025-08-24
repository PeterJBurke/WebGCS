from pymavlink import mavutil
import time
from config import MAVLINK_CONNECTION_STRING

print("Testing heartbeat-only reception (like testheartbeatFIXED.py approach)")
print(f"Connecting to: {MAVLINK_CONNECTION_STRING}")

# Create connection like app.py does
connection = mavutil.mavlink_connection(
    MAVLINK_CONNECTION_STRING,
    autoreconnect=True,
    source_system=255,
    source_component=0
)

print("Waiting for initial heartbeat...")
connection.wait_heartbeat()
print(f"Connected to system {connection.target_system}")

heartbeat_count = 0
last_mode = None

try:
    while True:
        # Test 1: Only receive HEARTBEAT messages (like testheartbeatFIXED.py)
        msg = connection.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
        
        if msg:
            heartbeat_count += 1
            current_mode = msg.custom_mode
            
            # Convert to mode name
            from config import AP_CUSTOM_MODES
            mode_name = "UNKNOWN"
            for name, mode_id in AP_CUSTOM_MODES.items():
                if mode_id == current_mode:
                    mode_name = name
                    break
            
            if last_mode != current_mode:
                print(f"*** MODE CHANGE DETECTED *** Count: {heartbeat_count}")
                print(f"    Previous mode: {last_mode} -> New mode: {current_mode} ({mode_name})")
                print(f"    Time: {time.strftime('%H:%M:%S')}")
                last_mode = current_mode
            else:
                print(f"Heartbeat #{heartbeat_count}: Mode {mode_name} ({current_mode}) at {time.strftime('%H:%M:%S')}")
        else:
            print("Timeout waiting for heartbeat")

except KeyboardInterrupt:
    print(f"\nStopping test. Received {heartbeat_count} heartbeats")
finally:
    connection.close() 
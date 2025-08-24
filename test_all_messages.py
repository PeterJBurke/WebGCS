from pymavlink import mavutil
import time
from config import MAVLINK_CONNECTION_STRING

print("Testing all-message reception (like app.py approach)")
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
other_message_count = 0
last_mode = None
message_types_seen = set()

try:
    while True:
        # Test 2: Receive ALL message types (like app.py)
        msg = connection.recv_match(blocking=False, timeout=0.1)
        
        if msg:
            msg_type = msg.get_type()
            message_types_seen.add(msg_type)
            
            if msg_type == 'HEARTBEAT':
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
                    print(f"*** MODE CHANGE DETECTED *** HB Count: {heartbeat_count}, Other msgs: {other_message_count}")
                    print(f"    Previous mode: {last_mode} -> New mode: {current_mode} ({mode_name})")
                    print(f"    Time: {time.strftime('%H:%M:%S')}")
                    print(f"    Message types seen since last heartbeat: {sorted(message_types_seen)}")
                    last_mode = current_mode
                    message_types_seen.clear()
                else:
                    if heartbeat_count % 5 == 0:  # Only print every 5th heartbeat to reduce spam
                        print(f"Heartbeat #{heartbeat_count}: Mode {mode_name} ({current_mode}) | Other messages: {other_message_count}")
                        print(f"    Recent message types: {sorted(message_types_seen)}")
                        message_types_seen.clear()
            else:
                other_message_count += 1
                # Uncomment to see all message types:
                # print(f"Received {msg_type}")

except KeyboardInterrupt:
    print(f"\nStopping test.")
    print(f"Total heartbeats: {heartbeat_count}")
    print(f"Total other messages: {other_message_count}")
    print(f"Ratio: {other_message_count/heartbeat_count:.1f} other messages per heartbeat")
finally:
    connection.close() 
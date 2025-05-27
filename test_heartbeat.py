import time
from pymavlink import mavutil
import sys

# Import the MAVLINK_CONNECTION_STRING from config.py
try:
    from config import MAVLINK_CONNECTION_STRING
except ImportError:
    print("Could not import MAVLINK_CONNECTION_STRING from config.py. Make sure this script is in the same directory as config.py.")
    sys.exit(1)

print(f"Connecting to MAVLink endpoint: {MAVLINK_CONNECTION_STRING}")

# Connect to the MAVLink endpoint (TCP)
mav = mavutil.mavlink_connection(MAVLINK_CONNECTION_STRING)

print("Waiting for heartbeat messages...")

# Store the last 10 heartbeat receive times
heartbeat_times = []

while True:
    msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
    if msg is not None:
        # Log the exact time with microsecond precision
        recv_time = time.time()
        heartbeat_times.append(recv_time)
        if len(heartbeat_times) > 10:
            heartbeat_times.pop(0)
        # Calculate running average heartbeat rate (Hz)
        if len(heartbeat_times) > 1:
            intervals = [heartbeat_times[i] - heartbeat_times[i-1] for i in range(1, len(heartbeat_times))]
            avg_interval = sum(intervals) / len(intervals)
            heartbeat_rate = 1.0 / avg_interval if avg_interval > 0 else 0.0
        else:
            heartbeat_rate = 0.0
        local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(recv_time))
        microseconds = int((recv_time - int(recv_time)) * 1_000_000)
        print(f"[{local_time}.{microseconds:06d}] HEARTBEAT received")
        # Log unique information for each heartbeat
        seq = msg._header.seq if hasattr(msg, '_header') and hasattr(msg._header, 'seq') else None
        sysid = msg.get_srcSystem() if hasattr(msg, 'get_srcSystem') else None
        compid = msg.get_srcComponent() if hasattr(msg, 'get_srcComponent') else None
        print(f"  Unique heartbeat info: seq={seq}, sysid={sysid}, compid={compid}")
        # Log all fields in the heartbeat message
        print("  All HEARTBEAT fields:")
        for k, v in msg.to_dict().items():
            print(f"    {k}: {v}")
        print("  Human-readable:", msg.to_dict())
        print("  Raw:", msg)
        print(f"  Running average heartbeat rate (last {len(heartbeat_times)}): {heartbeat_rate:.2f} Hz")
        print("-" * 60)
    else:
        recv_time = time.time()
        local_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(recv_time))
        microseconds = int((recv_time - int(recv_time)) * 1_000_000)
        print(f"[{local_time}.{microseconds:06d}] No heartbeat received in the last 5 seconds.")

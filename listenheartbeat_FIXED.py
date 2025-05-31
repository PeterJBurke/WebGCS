from pymavlink import mavutil
import time
from config import MAVLINK_CONNECTION_STRING

# Use PyMavlink for proper MAVLink handling (like listen.py does)
print("Connecting to drone using PyMavlink...")
the_connection = mavutil.mavlink_connection(MAVLINK_CONNECTION_STRING)

# Wait for the first heartbeat to establish connection
print('Waiting for heartbeat...')
the_connection.wait_heartbeat()
print('Heartbeat received! Connection established.')

# Dictionary to map autopilot types to human-readable names
AUTOPILOT_TYPES = {
    0: "Generic",
    1: "Reserved", 
    2: "SLUGS",
    3: "ArduPilotMega",
    4: "OpenPilot",
    5: "Generic Waypoints Only",
    6: "Generic Waypoints and Simple Navigation Only",
    7: "Generic Mission Full",
    8: "Invalid",
    9: "PPZ",
    10: "UDB",
    11: "FP",
    12: "PX4",
    13: "SMACCMPILOT",
    14: "AUTOQUAD",
    15: "ARMAZILA",
    16: "AEROB",
    17: "ASLUAV",
    18: "SmartAP",
    19: "AirRails"
}

# Dictionary to map vehicle types to human-readable names
VEHICLE_TYPES = {
    0: "Generic",
    1: "Fixed Wing",
    2: "Quadrotor", 
    3: "Coaxial",
    4: "Helicopter",
    5: "Antenna Tracker",
    6: "GCS",
    7: "Airship",
    8: "Free Balloon",
    9: "Rocket",
    10: "Ground Rover",
    11: "Surface Boat",
    12: "Submarine",
    13: "Hexarotor",
    14: "Octorotor",
    15: "Tricopter",
    16: "Flapping Wing",
    17: "Kite",
    18: "Onboard Companion Controller",
    19: "Two-rotor VTOL",
    20: "Quad-rotor VTOL",
    21: "Tiltrotor VTOL",
    22: "VTOL Reserved 2",
    23: "VTOL Reserved 3",
    24: "VTOL Reserved 4",
    25: "VTOL Reserved 5",
    26: "Gimbal",
    27: "ADSB system",
    28: "Steerable, 2-axis Gimbal",
    29: "Onboard IO Controller",
    30: "Vectored 6 DOF UUV",
    31: "Onboard Companion Computer"
}

# ArduPilot Copter custom modes
ARDUPILOT_COPTER_MODES = {
    0: "Stabilize",
    1: "Acro", 
    2: "AltHold",
    3: "Auto",
    4: "Guided",
    5: "Loiter",
    6: "RTL",
    7: "Circle",
    8: "Position",
    9: "Land",
    10: "OF_Loiter",
    11: "Drift",
    13: "Sport",
    14: "Flip",
    15: "AutoTune",
    16: "PosHold",
    17: "Brake",
    18: "Throw",
    19: "Avoid_ADSB",
    20: "Guided_NoGPS",
    21: "Smart_RTL",
    22: "FlowHold",
    23: "Follow",
    24: "ZigZag",
    25: "SystemID",
    26: "Heli_Autorotate"
}

# Base mode flag meanings
def decode_base_mode(base_mode):
    """Decode base mode flags into human readable format"""
    flags = []
    if base_mode & 0x01: flags.append("Custom Mode Enabled")
    if base_mode & 0x02: flags.append("Test Mode")
    if base_mode & 0x04: flags.append("Auto Mode")
    if base_mode & 0x08: flags.append("Guided Mode")
    if base_mode & 0x10: flags.append("Stabilize Mode")
    if base_mode & 0x20: flags.append("Hardware in Loop")
    if base_mode & 0x40: flags.append("Manual Input Enabled")
    if base_mode & 0x80: flags.append("Safety Armed")
    return flags

def get_flight_mode(base_mode, custom_mode, autopilot):
    """Get the actual flight mode name"""
    if base_mode & 0x01:  # Custom mode enabled
        if autopilot == 3:  # ArduPilotMega
            return ARDUPILOT_COPTER_MODES.get(custom_mode, f"Unknown Custom Mode ({custom_mode})")
    
    # Fallback to base mode interpretation
    if base_mode & 0x10:
        return "Stabilize (Base Mode)"
    elif base_mode & 0x04:
        return "Auto (Base Mode)"
    elif base_mode & 0x08:
        return "Guided (Base Mode)"
    else:
        return f"Unknown Mode (Base: 0x{base_mode:02X})"

print(f"System ID: {the_connection.target_system}, Component ID: {the_connection.target_component}")
print("Listening for heartbeat messages...")
print("Press Ctrl+C to stop\n")

heartbeat_count = 0

try:
    while True:
        # Wait for heartbeat message specifically
        msg = the_connection.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
        
        if msg:
            heartbeat_count += 1
            
            # Extract heartbeat information using PyMavlink parsing
            autopilot = msg.autopilot
            vehicle_type = msg.type
            base_mode = msg.base_mode
            custom_mode = msg.custom_mode
            system_status = msg.system_status
            mavlink_version = msg.mavlink_version
            
            # Get the actual flight mode
            flight_mode = get_flight_mode(base_mode, custom_mode, autopilot)
            
            # Print heartbeat information in human-readable format
            print(f"\n=== Heartbeat #{heartbeat_count} ===")
            print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"System: {the_connection.target_system}, Component: {the_connection.target_component}")
            print(f"Autopilot: {AUTOPILOT_TYPES.get(autopilot, 'Unknown')} ({autopilot})")
            print(f"Vehicle Type: {VEHICLE_TYPES.get(vehicle_type, 'Unknown')} ({vehicle_type})")
            print(f"Flight Mode: {flight_mode}")
            print(f"System Status: {system_status}")
            print(f"MAVLink Version: {mavlink_version}")
            print(f"Base Mode: 0x{base_mode:02X}")
            
            # Decode base mode flags
            flags = decode_base_mode(base_mode)
            if flags:
                print("Base Mode Flags:")
                for flag in flags:
                    print(f"  - {flag}")
            else:
                print("No base mode flags")
                
            # Show custom mode with human-readable name
            if base_mode & 0x01:  # Custom mode enabled
                custom_mode_name = ARDUPILOT_COPTER_MODES.get(custom_mode, f"Unknown ({custom_mode})")
                print(f"Custom Mode: {custom_mode_name} ({custom_mode})")
            else:
                print(f"Custom Mode: Not enabled (Base mode only)")
            print("=" * 30)
        else:
            print("Timeout waiting for heartbeat...")
            
except KeyboardInterrupt:
    print(f"\nStopping heartbeat listener... (Received {heartbeat_count} heartbeats)")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    the_connection.close()
    print("Connection closed.") 
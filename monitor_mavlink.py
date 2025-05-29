#!/usr/bin/env python3
"""
MAVLink Monitor Tool

This script connects to the drone and logs all MAVLink messages in a human-readable format.
Run this alongside the WebGCS application to monitor the MAVLink traffic.
"""
import time
import sys
from pymavlink import mavutil

# Import configuration
from config import (
    MAVLINK_CONNECTION_STRING,
    AP_CUSTOM_MODES
)

# Mapping for human-readable status values
from mavlink_utils import (
    MAV_RESULT_STR,
    MAV_TYPE_STR,
    MAV_STATE_STR,
    MAV_AUTOPILOT_STR,
    MAV_MODE_FLAG_ENUM
)

def format_heartbeat(msg):
    """Format a heartbeat message in human-readable format."""
    system_status_str = MAV_STATE_STR.get(msg.system_status, f"UNKNOWN({msg.system_status})")
    vehicle_type_str = MAV_TYPE_STR.get(msg.type, f"UNKNOWN({msg.type})")
    autopilot_type_str = MAV_AUTOPILOT_STR.get(msg.autopilot, f"UNKNOWN({msg.autopilot})")
    
    # Decode base mode flags
    base_mode_flags = []
    for flag_name, flag_value in MAV_MODE_FLAG_ENUM.items():
        if msg.base_mode & flag_value:
            base_mode_flags.append(flag_name.replace('MAV_MODE_FLAG_', ''))
    base_mode_str = ", ".join(base_mode_flags) if base_mode_flags else "NONE"
    
    # Get custom mode string
    custom_mode_str_list = [k for k, v in AP_CUSTOM_MODES.items() if v == msg.custom_mode]
    custom_mode_str = custom_mode_str_list[0] if custom_mode_str_list else f'CUSTOM_MODE({msg.custom_mode})'
    
    # Format armed status
    armed_status = "ARMED" if (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) else "DISARMED"
    
    return (f"HEARTBEAT: SysID={msg.get_srcSystem()} CompID={msg.get_srcComponent()} | "
            f"Type={vehicle_type_str} | Autopilot={autopilot_type_str} | "
            f"Status={system_status_str} | Mode={custom_mode_str} | {armed_status} | "
            f"Base Mode Flags=[{base_mode_str}]")

def format_global_position(msg):
    """Format a GLOBAL_POSITION_INT message in human-readable format."""
    lat = msg.lat / 1e7
    lon = msg.lon / 1e7
    alt_msl = msg.alt / 1000.0
    alt_rel = msg.relative_alt / 1000.0
    hdg = msg.hdg / 100.0 if msg.hdg != 65535 else float('nan')
    vx = msg.vx / 100.0  # cm/s to m/s
    vy = msg.vy / 100.0  # cm/s to m/s
    vz = msg.vz / 100.0  # cm/s to m/s
    
    return (f"POSITION: Lat={lat:.6f}, Lon={lon:.6f}, Alt(MSL)={alt_msl:.1f}m, "
            f"Alt(Rel)={alt_rel:.1f}m, Heading={hdg:.1f}°, "
            f"Velocity(m/s)=[{vx:.1f}, {vy:.1f}, {vz:.1f}]")

def format_attitude(msg):
    """Format an ATTITUDE message in human-readable format."""
    import math
    roll_deg = math.degrees(msg.roll)
    pitch_deg = math.degrees(msg.pitch)
    yaw_deg = math.degrees(msg.yaw)
    
    return (f"ATTITUDE: Roll={roll_deg:.1f}°, Pitch={pitch_deg:.1f}°, Yaw={yaw_deg:.1f}°, "
            f"Roll Rate={msg.rollspeed:.2f} rad/s, Pitch Rate={msg.pitchspeed:.2f} rad/s, "
            f"Yaw Rate={msg.yawspeed:.2f} rad/s")

def format_command_ack(msg):
    """Format a COMMAND_ACK message in human-readable format."""
    cmd_id = msg.command
    result = msg.result
    
    # Get command name
    cmd_name = "UNKNOWN"
    if cmd_id in mavutil.mavlink.enums['MAV_CMD']:
        cmd_name = mavutil.mavlink.enums['MAV_CMD'][cmd_id].name
    
    # Get result name
    result_name = MAV_RESULT_STR.get(result, f"UNKNOWN({result})")
    
    return f"COMMAND_ACK: Command={cmd_name}({cmd_id}), Result={result_name}({result})"

def format_statustext(msg):
    """Format a STATUSTEXT message in human-readable format."""
    severity_val = msg.severity
    severity_str = "UNKNOWN"
    if severity_val in mavutil.mavlink.enums['MAV_SEVERITY']:
        severity_str = mavutil.mavlink.enums['MAV_SEVERITY'][severity_val].name
    
    return f"STATUSTEXT: [{severity_str}] {msg.text}"

def format_sys_status(msg):
    """Format a SYS_STATUS message in human-readable format."""
    voltage = msg.voltage_battery / 1000.0  # mV to V
    current = msg.current_battery / 100.0   # cA to A
    remaining = msg.battery_remaining       # Percent
    
    return (f"SYS_STATUS: Battery={voltage:.2f}V, Current={current:.2f}A, "
            f"Remaining={remaining}%, CPU Load={msg.load/10.0:.1f}%")

def format_vfr_hud(msg):
    """Format a VFR_HUD message in human-readable format."""
    return (f"VFR_HUD: Airspeed={msg.airspeed:.1f}m/s, Groundspeed={msg.groundspeed:.1f}m/s, "
            f"Alt={msg.alt:.1f}m, Climb Rate={msg.climb:.1f}m/s, Heading={msg.heading}°")

def format_gps_raw_int(msg):
    """Format a GPS_RAW_INT message in human-readable format."""
    fix_type_str = "UNKNOWN"
    if msg.fix_type in mavutil.mavlink.enums['GPS_FIX_TYPE']:
        fix_type_str = mavutil.mavlink.enums['GPS_FIX_TYPE'][msg.fix_type].name
    
    lat = msg.lat / 1e7 if msg.lat != 0 else float('nan')
    lon = msg.lon / 1e7 if msg.lon != 0 else float('nan')
    
    return (f"GPS: Fix={fix_type_str}({msg.fix_type}), Satellites={msg.satellites_visible}, "
            f"Lat={lat:.6f}, Lon={lon:.6f}, Alt={msg.alt/1000.0:.1f}m, "
            f"HDOP={msg.eph/100.0:.2f}, VDOP={msg.epv/100.0:.2f}")

# Message formatters dictionary
MESSAGE_FORMATTERS = {
    'HEARTBEAT': format_heartbeat,
    'GLOBAL_POSITION_INT': format_global_position,
    'ATTITUDE': format_attitude,
    'COMMAND_ACK': format_command_ack,
    'STATUSTEXT': format_statustext,
    'SYS_STATUS': format_sys_status,
    'VFR_HUD': format_vfr_hud,
    'GPS_RAW_INT': format_gps_raw_int,
}

def main():
    """Main function to connect to the drone and monitor MAVLink messages."""
    print(f"Connecting to {MAVLINK_CONNECTION_STRING}...")
    
    try:
        # Create the connection
        mav = mavutil.mavlink_connection(
            MAVLINK_CONNECTION_STRING,
            autoreconnect=True,
            source_system=255,
            source_component=0,
            retries=3,
            timeout=10.0
        )
        
        # Wait for the first heartbeat
        print("Waiting for heartbeat...")
        msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=10)
        if not msg:
            print("No heartbeat received. Exiting.")
            return False
        
        print(f"Received heartbeat from system {msg.get_srcSystem()}")
        print(format_heartbeat(msg))
        
        # Set target system and component
        mav.target_system = msg.get_srcSystem()
        mav.target_component = msg.get_srcComponent()
        
        print(f"\nMonitoring MAVLink messages from {MAVLINK_CONNECTION_STRING}...")
        print("Press Ctrl+C to exit\n")
        
        # Track message statistics
        message_counts = {}
        start_time = time.time()
        last_stats_time = start_time
        
        # Main loop to receive and print messages
        while True:
            # Receive message
            msg = mav.recv_match(blocking=True, timeout=1.0)
            
            if msg:
                msg_type = msg.get_type()
                
                # Update message count
                if msg_type not in message_counts:
                    message_counts[msg_type] = 0
                message_counts[msg_type] += 1
                
                # Format and print specific message types
                if msg_type in MESSAGE_FORMATTERS:
                    formatted_msg = MESSAGE_FORMATTERS[msg_type](msg)
                    print(f"{time.strftime('%H:%M:%S')} - {formatted_msg}")
                
                # Print statistics every 10 seconds
                current_time = time.time()
                if current_time - last_stats_time >= 10:
                    elapsed = current_time - start_time
                    total_msgs = sum(message_counts.values())
                    rate = total_msgs / elapsed
                    
                    print("\n--- Message Statistics ---")
                    print(f"Monitoring for {elapsed:.1f} seconds")
                    print(f"Total messages: {total_msgs} ({rate:.1f} msgs/sec)")
                    print("Message counts by type:")
                    for msg_type, count in sorted(message_counts.items(), key=lambda x: x[1], reverse=True):
                        print(f"  {msg_type}: {count}")
                    print("-------------------------\n")
                    
                    last_stats_time = current_time
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'mav' in locals():
            mav.close()

if __name__ == "__main__":
    main()

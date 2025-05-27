"""
Utility functions and constants for MAVLink communication.
"""
from pymavlink import mavutil

# --- MAVLink Enumeration String Maps ---

# MAV_RESULT: Result of a MAVLink command
MAV_RESULT_ENUM = mavutil.mavlink.enums['MAV_RESULT']
MAV_RESULT_STR = {v: k for k, v in MAV_RESULT_ENUM.items()}

# MAV_TYPE: Type of MAV (Micro Air Vehicle)
MAV_TYPE_ENUM = mavutil.mavlink.enums['MAV_TYPE']
MAV_TYPE_STR = {v: k for k, v in MAV_TYPE_ENUM.items()}

# MAV_STATE: System status flags
MAV_STATE_ENUM = mavutil.mavlink.enums['MAV_STATE']
MAV_STATE_STR = {v: k for k, v in MAV_STATE_ENUM.items()}

# MAV_AUTOPILOT: Autopilot type
MAV_AUTOPILOT_ENUM = mavutil.mavlink.enums['MAV_AUTOPILOT']
MAV_AUTOPILOT_STR = {v: k for k, v in MAV_AUTOPILOT_ENUM.items()}

# MAV_MODE_FLAG: Flags for MAV_MODE
MAV_MODE_FLAG_ENUM = mavutil.mavlink.enums['MAV_MODE_FLAG']

# You can add more generic MAVLink enum mappings here as needed.

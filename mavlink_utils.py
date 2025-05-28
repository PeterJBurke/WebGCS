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

# MAV_SEVERITY: Severity of STATUSTEXT message
MAV_SEVERITY_ENUM = mavutil.mavlink.enums['MAV_SEVERITY']
MAV_SEVERITY_STR = {v: k for k, v in MAV_SEVERITY_ENUM.items()}

# You can add more generic MAVLink enum mappings here as needed.

def get_ekf_status_report(flags):
    if not (flags & mavutil.mavlink.MAV_SYS_STATUS_SENSOR_ANGULAR_RATE_CONTROL): return "EKF INIT (Gyro)"
    if not (flags & mavutil.mavlink.MAV_SYS_STATUS_SENSOR_ATTITUDE_STABILIZATION): return "EKF INIT (Att)"
    ekf_flags_bits = flags >> 16
    if not (ekf_flags_bits & mavutil.mavlink.EKF_ATTITUDE): return "EKF Bad Att"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_VELOCITY_HORIZ): return "EKF Bad Vel(H)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_VELOCITY_VERT): return "EKF Bad Vel(V)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_POS_HORIZ_ABS):
        if not (ekf_flags_bits & mavutil.mavlink.EKF_POS_HORIZ_REL): return "EKF Bad Pos(H)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_POS_VERT_ABS): return "EKF Bad Pos(V)"
    if not (ekf_flags_bits & mavutil.mavlink.EKF_PRED_POS_HORIZ_REL): return "EKF Variance (H)"
    return "EKF OK"

"""
WebGCS MAVLink Message Processor
Processes incoming MAVLink messages and extracts telemetry.
"""

import math
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pymavlink import mavutil

logger = logging.getLogger('webgcs.mavlink.processor')


class MessageProcessor:
    """Processes MAVLink messages and extracts telemetry data."""
    
    def __init__(self):
        """Initialize message processor."""
        self._message_handlers: Dict[str, Callable] = {
            'HEARTBEAT': self.process_heartbeat,
            'ATTITUDE': self.process_attitude,
            'GLOBAL_POSITION_INT': self.process_global_position,
            'VFR_HUD': self.process_vfr_hud,
            'SYS_STATUS': self.process_sys_status,
            'BATTERY_STATUS': self.process_battery_status,
            'RC_CHANNELS': self.process_rc_channels,
            'SERVO_OUTPUT_RAW': self.process_servo_output
        }
        
        # Telemetry data cache
        self._telemetry_cache: Dict[str, Any] = {}
        self._last_update = datetime.now()
        
        logger.info("MessageProcessor initialized")
    
    def process_message(self, msg) -> Optional[Dict[str, Any]]:
        """
        Process incoming MAVLink message.
        
        Args:
            msg: MAVLink message object
            
        Returns:
            Processed telemetry data or None if message type not handled
        """
        if msg is None:
            return None
        
        msg_type = msg.get_type()
        handler = self._message_handlers.get(msg_type)
        
        if handler:
            try:
                result = handler(msg)
                if result:
                    # Update cache with new data
                    self._telemetry_cache.update(result)
                    self._telemetry_cache['last_update'] = datetime.now().isoformat()
                    return result
            except Exception as e:
                logger.error(f"Error processing {msg_type} message: {e}")
        else:
            logger.debug(f"Unhandled message type: {msg_type}")
        
        return None
    
    def get_telemetry_snapshot(self) -> Dict[str, Any]:
        """Get current telemetry data snapshot."""
        return self._telemetry_cache.copy()
    
    def process_heartbeat(self, msg) -> Dict[str, Any]:
        """
        Process HEARTBEAT message.
        
        Args:
            msg: HEARTBEAT message
            
        Returns:
            Processed heartbeat data
        """
        # MAVLink flight mode mapping
        flight_modes = {
            0: 'STABILIZE', 1: 'ACRO', 2: 'ALT_HOLD', 3: 'AUTO', 4: 'GUIDED',
            5: 'LOITER', 6: 'RTL', 7: 'CIRCLE', 9: 'LAND', 11: 'DRIFT',
            13: 'SPORT', 14: 'FLIP', 15: 'AUTOTUNE', 16: 'POSHOLD',
            17: 'BRAKE', 18: 'THROW', 19: 'AVOID_ADSB', 20: 'GUIDED_NOGPS'
        }
        
        return {
            'heartbeat': {
                'timestamp': datetime.now().isoformat(),
                'autopilot': msg.autopilot,
                'type': msg.type,
                'system_status': msg.system_status,
                'base_mode': msg.base_mode,
                'custom_mode': msg.custom_mode,
                'mavlink_version': msg.mavlink_version,
                'armed': bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED),
                'guided': bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_GUIDED_ENABLED),
                'manual': bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_MANUAL_INPUT_ENABLED),
                'flight_mode': flight_modes.get(msg.custom_mode, f'UNKNOWN_{msg.custom_mode}')
            }
        }
    
    def process_attitude(self, msg) -> Dict[str, Any]:
        """
        Process ATTITUDE message.
        
        Args:
            msg: ATTITUDE message
            
        Returns:
            Processed attitude data
        """
        return {
            'attitude': {
                'timestamp': datetime.now().isoformat(),
                'roll': math.degrees(msg.roll),          # Convert to degrees
                'pitch': math.degrees(msg.pitch),        # Convert to degrees  
                'yaw': math.degrees(msg.yaw),            # Convert to degrees
                'rollspeed': math.degrees(msg.rollspeed),   # rad/s to deg/s
                'pitchspeed': math.degrees(msg.pitchspeed), # rad/s to deg/s
                'yawspeed': math.degrees(msg.yawspeed)      # rad/s to deg/s
            }
        }
    
    def process_global_position(self, msg) -> Dict[str, Any]:
        """
        Process GLOBAL_POSITION_INT message.
        
        Args:
            msg: GLOBAL_POSITION_INT message
            
        Returns:
            Processed GPS position data
        """
        return {
            'gps': {
                'timestamp': datetime.now().isoformat(),
                'lat': msg.lat / 1e7,           # Convert from 1E7 degrees
                'lon': msg.lon / 1e7,           # Convert from 1E7 degrees
                'alt': msg.alt / 1000.0,        # Convert from mm to meters
                'relative_alt': msg.relative_alt / 1000.0,  # mm to meters
                'vx': msg.vx / 100.0,           # cm/s to m/s
                'vy': msg.vy / 100.0,           # cm/s to m/s
                'vz': msg.vz / 100.0,           # cm/s to m/s
                'hdg': msg.hdg / 100.0,         # centidegrees to degrees
                'time_boot_ms': msg.time_boot_ms
            }
        }
    
    def process_vfr_hud(self, msg) -> Dict[str, Any]:
        """
        Process VFR_HUD message for flight instruments.
        
        Args:
            msg: VFR_HUD message
            
        Returns:
            Processed VFR HUD data
        """
        return {
            'vfr_hud': {
                'timestamp': datetime.now().isoformat(),
                'airspeed': msg.airspeed,        # m/s
                'groundspeed': msg.groundspeed,  # m/s
                'heading': msg.heading,          # degrees
                'throttle': msg.throttle,        # percentage 0-100
                'alt': msg.alt,                  # meters MSL
                'climb': msg.climb               # m/s
            }
        }
    
    def process_sys_status(self, msg) -> Dict[str, Any]:
        """
        Process SYS_STATUS message.
        
        Args:
            msg: SYS_STATUS message
            
        Returns:
            Processed system status data
        """
        return {
            'sys_status': {
                'timestamp': datetime.now().isoformat(),
                'voltage_battery': msg.voltage_battery / 1000.0,  # mV to V
                'current_battery': msg.current_battery / 100.0,   # cA to A
                'battery_remaining': msg.battery_remaining,        # percentage
                'drop_rate_comm': msg.drop_rate_comm / 100.0,     # percentage
                'errors_comm': msg.errors_comm,
                'errors_count1': msg.errors_count1,
                'errors_count2': msg.errors_count2,
                'errors_count3': msg.errors_count3,
                'errors_count4': msg.errors_count4
            }
        }
    
    def process_battery_status(self, msg) -> Dict[str, Any]:
        """
        Process BATTERY_STATUS message.
        
        Args:
            msg: BATTERY_STATUS message
            
        Returns:
            Processed battery status data
        """
        voltages = [v / 1000.0 for v in msg.voltages if v != 65535]  # mV to V, filter invalid
        
        return {
            'battery': {
                'timestamp': datetime.now().isoformat(),
                'id': msg.id,
                'battery_function': msg.battery_function,
                'type': msg.type,
                'temperature': msg.temperature / 100.0,  # centidegrees to degrees
                'voltages': voltages,
                'current_battery': msg.current_battery / 100.0,  # cA to A
                'current_consumed': msg.current_consumed,         # mAh
                'energy_consumed': msg.energy_consumed,           # hJ
                'battery_remaining': msg.battery_remaining        # percentage
            }
        }
    
    def process_rc_channels(self, msg) -> Dict[str, Any]:
        """
        Process RC_CHANNELS message.
        
        Args:
            msg: RC_CHANNELS message
            
        Returns:
            Processed RC channels data
        """
        channels = [
            msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw,
            msg.chan5_raw, msg.chan6_raw, msg.chan7_raw, msg.chan8_raw,
            msg.chan9_raw, msg.chan10_raw, msg.chan11_raw, msg.chan12_raw,
            msg.chan13_raw, msg.chan14_raw, msg.chan15_raw, msg.chan16_raw,
            msg.chan17_raw, msg.chan18_raw
        ]
        
        return {
            'rc_channels': {
                'timestamp': datetime.now().isoformat(),
                'channels': channels,
                'chancount': msg.chancount,
                'rssi': msg.rssi,
                'time_boot_ms': msg.time_boot_ms
            }
        }
    
    def process_servo_output(self, msg) -> Dict[str, Any]:
        """
        Process SERVO_OUTPUT_RAW message.
        
        Args:
            msg: SERVO_OUTPUT_RAW message
            
        Returns:
            Processed servo output data
        """
        servos = [
            msg.servo1_raw, msg.servo2_raw, msg.servo3_raw, msg.servo4_raw,
            msg.servo5_raw, msg.servo6_raw, msg.servo7_raw, msg.servo8_raw,
            msg.servo9_raw, msg.servo10_raw, msg.servo11_raw, msg.servo12_raw,
            msg.servo13_raw, msg.servo14_raw, msg.servo15_raw, msg.servo16_raw
        ]
        
        return {
            'servos': {
                'timestamp': datetime.now().isoformat(),
                'port': msg.port,
                'servo_raw': servos,
                'time_usec': msg.time_usec
            }
        }
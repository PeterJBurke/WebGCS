"""
MAVLink Telemetry Handler for WebGCS
Handles reading and processing telemetry data from drone
File size: Must stay under 150 lines per WebGCS PRD
"""
import time
from src.utils.token_tracker import record_agent_usage


class TelemetryHandler:
    """Handles MAVLink telemetry data collection and processing."""
    
    def __init__(self, connection_handler):
        """Initialize telemetry handler."""
        self.connection_handler = connection_handler
        self.heartbeat_count = 0  # Track heartbeat messages received
        record_agent_usage('mavlink-protocol-agent', 15, 10)
    
    def reset_heartbeat_counter(self):
        """Reset heartbeat counter for new connection."""
        self.heartbeat_count = 0
    
    def get_telemetry_data(self) -> dict:
        """Get current telemetry data from drone."""
        if not self.connection_handler.is_connected():
            return self._get_empty_telemetry()
        
        connection = self.connection_handler.get_connection()
        if not connection:
            return self._get_empty_telemetry()
        
        telemetry = {
            'connected': True,
            'timestamp': time.time(),
            'heartbeat_count': self.heartbeat_count,  # Include heartbeat counter
            'lat': 0,
            'lon': 0,
            'alt': 0,
            'heading': 0,
            'groundspeed': 0,
            'airspeed': 0,
            'battery_voltage': 0,
            'battery_current': 0,
            'battery_remaining': 0,
            'armed': False,
            'mode': 'STABILIZE',
            'gps_fix_type': 0,
            'satellites_visible': 0,
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'vertical_speed': 0
        }
        
        try:
            # Read multiple messages to get comprehensive telemetry
            for _ in range(10):  # Try to read up to 10 messages
                msg = connection.recv_match(blocking=False, timeout=0.05)
                if not msg:
                    break
                    
                self._process_telemetry_message(msg, telemetry)
        
        except Exception as e:
            pass  # Continue with partial telemetry data
        
        record_agent_usage('mavlink-protocol-agent', 25, 20)
        return telemetry
    
    def _process_telemetry_message(self, msg, telemetry):
        """Process individual telemetry message."""
        msg_type = msg.get_type()
        
        if msg_type == 'GLOBAL_POSITION_INT':
            telemetry['lat'] = msg.lat / 1e7  # Convert from 1E7 degrees to degrees
            telemetry['lon'] = msg.lon / 1e7
            telemetry['alt'] = msg.alt / 1000.0  # Convert from mm to m
            telemetry['heading'] = msg.hdg / 100.0  # Convert from cdeg to deg
            telemetry['groundspeed'] = msg.vx / 100.0  # Convert from cm/s to m/s
            telemetry['vertical_speed'] = -msg.vz / 100.0  # Convert from cm/s to m/s
        
        elif msg_type == 'ATTITUDE':
            telemetry['roll'] = msg.roll  # radians
            telemetry['pitch'] = msg.pitch  # radians
            telemetry['yaw'] = msg.yaw  # radians
        
        elif msg_type == 'SYS_STATUS':
            telemetry['battery_voltage'] = msg.voltage_battery / 1000.0  # mV to V
            telemetry['battery_current'] = msg.current_battery / 100.0  # cA to A
            telemetry['battery_remaining'] = msg.battery_remaining  # %
        
        elif msg_type == 'GPS_RAW_INT':
            telemetry['gps_fix_type'] = msg.fix_type
            telemetry['satellites_visible'] = msg.satellites_visible
        
        elif msg_type == 'HEARTBEAT':
            # Increment heartbeat counter each time we receive a heartbeat
            self.heartbeat_count += 1
            telemetry['heartbeat_count'] = self.heartbeat_count
            
            # Determine if armed (MAV_STATE_ACTIVE = 4)
            telemetry['armed'] = (msg.system_status == 4)
            
            # Extract flight mode (ArduPilot copter modes)
            mode_map = {
                0: 'STABILIZE',
                1: 'ACRO', 
                2: 'ALT_HOLD',
                3: 'AUTO',
                4: 'GUIDED',
                5: 'LOITER',
                6: 'RTL',
                7: 'CIRCLE',
                9: 'LAND',
                16: 'POSHOLD',
                17: 'BRAKE',
                18: 'THROW',
                19: 'AVOID_ADSB',
                20: 'GUIDED_NOGPS',
                21: 'SMART_RTL'
            }
            telemetry['mode'] = mode_map.get(msg.custom_mode, 'STABILIZE')
    
    def _get_empty_telemetry(self) -> dict:
        """Return empty telemetry structure when not connected."""
        return {
            'connected': False,
            'timestamp': time.time(),
            'heartbeat_count': 0,  # Reset heartbeat count when disconnected
            'lat': 0,
            'lon': 0,
            'alt': 0,
            'heading': 0,
            'groundspeed': 0,
            'airspeed': 0,
            'battery_voltage': 0,
            'battery_current': 0,
            'battery_remaining': 0,
            'armed': False,
            'mode': 'STABILIZE',
            'gps_fix_type': 0,
            'satellites_visible': 0,
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'vertical_speed': 0
        }
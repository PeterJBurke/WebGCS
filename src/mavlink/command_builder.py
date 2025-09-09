"""
MAVLink Command Builder for WebGCS
Builds and formats MAVLink commands with proper parameters
File size: Must stay under 150 lines per WebGCS PRD
"""
import time
from typing import Dict
from src.utils.token_tracker import record_agent_usage


class CommandBuilder:
    """Builds MAVLink commands with proper formatting."""
    
    # MAVLink command constants
    MAV_CMD_COMPONENT_ARM_DISARM = 400
    MAV_CMD_NAV_TAKEOFF = 22
    MAV_CMD_NAV_LAND = 21
    MAV_CMD_NAV_RETURN_TO_LAUNCH = 20
    MAV_CMD_DO_SET_MODE = 176
    MAV_CMD_NAV_WAYPOINT = 16
    
    # Flight modes
    FLIGHT_MODES = {
        'STABILIZE': 0,
        'ACRO': 1,
        'ALT_HOLD': 2,
        'AUTO': 3,
        'GUIDED': 4,
        'LOITER': 5,
        'RTL': 6,
        'CIRCLE': 7,
        'LAND': 9,
        'BRAKE': 17
    }
    
    def __init__(self, target_system: int = 1, target_component: int = 1):
        """Initialize command builder."""
        self.target_system = target_system
        self.target_component = target_component
        self.command_sequence = 0
        
        record_agent_usage('mavlink-protocol-agent', 25, 20)
    
    def build_command(self, command: int, param1: float = 0, param2: float = 0,
                     param3: float = 0, param4: float = 0, param5: float = 0,
                     param6: float = 0, param7: float = 0) -> Dict:
        """Build generic MAVLink command dictionary."""
        self.command_sequence += 1
        
        command_dict = {
            'command': command,
            'target_system': self.target_system,
            'target_component': self.target_component,
            'confirmation': 0,
            'param1': param1,
            'param2': param2,
            'param3': param3,
            'param4': param4,
            'param5': param5,
            'param6': param6,
            'param7': param7,
            'sequence': self.command_sequence,
            'timestamp': time.time()
        }
        
        record_agent_usage('mavlink-protocol-agent', 20, 15)
        return command_dict
    
    def build_arm_command(self, force_arm: bool = False) -> Dict:
        """Build ARM command."""
        param1 = 1  # ARM
        param2 = 21196 if force_arm else 0  # Force ARM magic number
        
        return self.build_command(
            self.MAV_CMD_COMPONENT_ARM_DISARM,
            param1=param1,
            param2=param2
        )
    
    def build_disarm_command(self, force_disarm: bool = False) -> Dict:
        """Build DISARM command."""
        param1 = 0  # DISARM
        param2 = 21196 if force_disarm else 0  # Force DISARM magic number
        
        return self.build_command(
            self.MAV_CMD_COMPONENT_ARM_DISARM,
            param1=param1,
            param2=param2
        )
    
    def build_takeoff_command(self, altitude: float, pitch: float = 0, yaw: float = float('nan')) -> Dict:
        """Build TAKEOFF command."""
        return self.build_command(
            self.MAV_CMD_NAV_TAKEOFF,
            param1=pitch,     # Minimum pitch
            param4=yaw,       # Yaw angle
            param7=altitude   # Altitude
        )
    
    def build_land_command(self, yaw: float = float('nan'), lat: float = 0, 
                          lon: float = 0, alt: float = 0) -> Dict:
        """Build LAND command."""
        return self.build_command(
            self.MAV_CMD_NAV_LAND,
            param4=yaw,  # Yaw angle
            param5=lat,  # Latitude
            param6=lon,  # Longitude
            param7=alt   # Altitude
        )
    
    def build_rtl_command(self) -> Dict:
        """Build Return to Launch command."""
        return self.build_command(self.MAV_CMD_NAV_RETURN_TO_LAUNCH)
    
    def build_set_mode_command(self, mode: str) -> Dict:
        """Build SET_MODE command."""
        mode_number = self.FLIGHT_MODES.get(mode.upper(), 4)  # Default to GUIDED
        
        return self.build_command(
            self.MAV_CMD_DO_SET_MODE,
            param1=1,           # MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
            param2=mode_number  # Custom mode number
        )
    
    def build_goto_command(self, latitude: float, longitude: float, altitude: float) -> Dict:
        """Build GOTO position command."""
        return self.build_command(
            self.MAV_CMD_NAV_WAYPOINT,
            param1=0,    # Hold time
            param2=0,    # Accept radius
            param3=0,    # Pass radius
            param4=float('nan'),  # Yaw
            param5=latitude,  # Latitude
            param6=longitude,  # Longitude
            param7=altitude   # Altitude
        )
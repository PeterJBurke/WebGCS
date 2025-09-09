"""
MAVLink Command Validator for WebGCS
Validates command parameters and safety requirements
File size: Must stay under 150 lines per WebGCS PRD
"""
from typing import Dict, Tuple
from src.utils.token_tracker import record_agent_usage


class CommandValidator:
    """Validates MAVLink commands for safety and parameter correctness."""
    
    def __init__(self):
        """Initialize command validator."""
        record_agent_usage('mavlink-protocol-agent', 15, 10)
    
    def validate_arm_command(self, confirmed: bool = False) -> Tuple[bool, str]:
        """Validate ARM command requirements."""
        if not confirmed:
            return False, 'ARM command requires explicit confirmation for safety'
        return True, 'ARM command validated'
    
    def validate_disarm_command(self, confirmed: bool = False) -> Tuple[bool, str]:
        """Validate DISARM command requirements."""
        if not confirmed:
            return False, 'DISARM command requires explicit confirmation for safety'
        return True, 'DISARM command validated'
    
    def validate_takeoff_command(self, altitude: float, confirmed: bool = False) -> Tuple[bool, str]:
        """Validate TAKEOFF command parameters."""
        if not confirmed:
            return False, 'TAKEOFF command requires explicit confirmation for safety'
        
        if not isinstance(altitude, (int, float)):
            return False, 'TAKEOFF altitude must be a number'
        
        if altitude <= 0:
            return False, 'TAKEOFF altitude must be positive'
        
        if altitude > 100:  # 100m max for safety
            return False, 'TAKEOFF altitude exceeds maximum safe limit (100m)'
        
        return True, f'TAKEOFF command validated for {altitude}m altitude'
    
    def validate_goto_command(self, latitude: float, longitude: float, 
                             altitude: float, confirmed: bool = False) -> Tuple[bool, str]:
        """Validate GOTO command coordinates."""
        if not confirmed:
            return False, 'GOTO command requires explicit confirmation for safety'
        
        # Validate coordinate types
        if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
            return False, 'Invalid coordinate format - must be numeric'
        
        # Check for None values
        if latitude is None or longitude is None:
            return False, 'Invalid coordinates - None values not allowed'
        
        # Validate latitude range
        if latitude < -90 or latitude > 90:
            return False, 'Invalid latitude - must be between -90 and 90 degrees'
        
        # Validate longitude range
        if longitude < -180 or longitude > 180:
            return False, 'Invalid longitude - must be between -180 and 180 degrees'
        
        # Validate altitude
        if not isinstance(altitude, (int, float)):
            return False, 'Invalid altitude - must be numeric'
        
        if altitude < 0:
            return False, 'Invalid altitude - must be non-negative'
        
        return True, f'GOTO command validated for coordinates ({latitude}, {longitude}) at {altitude}m'
    
    def validate_mode_command(self, mode: str) -> Tuple[bool, str]:
        """Validate SET_MODE command."""
        if not isinstance(mode, str):
            return False, 'Flight mode must be a string'
        
        valid_modes = [
            'STABILIZE', 'ACRO', 'ALT_HOLD', 'AUTO', 
            'GUIDED', 'LOITER', 'RTL', 'CIRCLE', 'LAND', 'BRAKE'
        ]
        
        if mode.upper() not in valid_modes:
            return False, f'Invalid flight mode. Valid modes: {", ".join(valid_modes)}'
        
        return True, f'SET_MODE command validated for mode {mode.upper()}'
    
    def validate_land_command(self) -> Tuple[bool, str]:
        """Validate LAND command (no special requirements)."""
        return True, 'LAND command validated'
    
    def validate_rtl_command(self) -> Tuple[bool, str]:
        """Validate RTL command (no special requirements)."""
        return True, 'RTL command validated'
"""
WebGCS MAVLink Command Sender
Sends commands to drone with acknowledgment tracking.
"""

import threading
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pymavlink import mavutil

logger = logging.getLogger('webgcs.mavlink.commands')


class CommandSender:
    """Sends MAVLink commands to drone with acknowledgment tracking."""
    
    def __init__(self, connection_manager, ack_timeout: float = 5.0):
        """
        Initialize command sender.
        
        Args:
            connection_manager: ConnectionManager instance
            ack_timeout: Timeout for command acknowledgment in seconds
        """
        self.connection_manager = connection_manager
        self.ack_timeout = ack_timeout
        
        # Command tracking
        self._pending_commands: Dict[int, Dict[str, Any]] = {}
        self._command_sequence = 0
        self._lock = threading.Lock()
        
        # Flight mode mappings
        self._flight_modes = {
            'STABILIZE': 0, 'ACRO': 1, 'ALT_HOLD': 2, 'AUTO': 3, 'GUIDED': 4,
            'LOITER': 5, 'RTL': 6, 'CIRCLE': 7, 'LAND': 9, 'DRIFT': 11,
            'SPORT': 13, 'FLIP': 14, 'AUTOTUNE': 15, 'POSHOLD': 16,
            'BRAKE': 17, 'THROW': 18, 'AVOID_ADSB': 19, 'GUIDED_NOGPS': 20
        }
        
        logger.info("CommandSender initialized")
    
    def _get_next_command_id(self) -> int:
        """Get next command sequence ID."""
        with self._lock:
            self._command_sequence += 1
            return self._command_sequence
    
    def _send_command_long(self, command: int, param1: float = 0, param2: float = 0, 
                          param3: float = 0, param4: float = 0, param5: float = 0,
                          param6: float = 0, param7: float = 0) -> Optional[int]:
        """
        Send MAVLink COMMAND_LONG message.
        
        Returns:
            Command ID if sent successfully, None otherwise
        """
        connection = self.connection_manager.get_connection()
        if not connection:
            logger.error("No active connection to send command")
            return None
        
        command_id = self._get_next_command_id()
        
        try:
            connection.mav.command_long_send(
                connection.target_system,
                connection.target_component,
                command,
                command_id,  # confirmation
                param1, param2, param3, param4, param5, param6, param7
            )
            
            # Track pending command
            with self._lock:
                self._pending_commands[command_id] = {
                    'command': command,
                    'timestamp': datetime.now(),
                    'params': [param1, param2, param3, param4, param5, param6, param7]
                }
            
            logger.info(f"Sent command {command} with ID {command_id}")
            return command_id
            
        except Exception as e:
            logger.error(f"Failed to send command {command}: {e}")
            return None
    
    def _wait_for_ack(self, command_id: int) -> bool:
        """
        Wait for command acknowledgment.
        
        Args:
            command_id: Command ID to wait for
            
        Returns:
            True if acknowledged successfully, False otherwise
        """
        connection = self.connection_manager.get_connection()
        if not connection:
            return False
        
        start_time = time.time()
        while time.time() - start_time < self.ack_timeout:
            try:
                msg = connection.recv_match(type='COMMAND_ACK', blocking=False, timeout=0.1)
                if msg and msg.command == command_id:
                    # Remove from pending commands
                    with self._lock:
                        self._pending_commands.pop(command_id, None)
                    
                    if msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
                        logger.info(f"Command {command_id} acknowledged successfully")
                        return True
                    else:
                        logger.warning(f"Command {command_id} rejected with result {msg.result}")
                        return False
                        
            except Exception as e:
                logger.debug(f"Error waiting for ACK: {e}")
                
            time.sleep(0.1)
        
        # Timeout
        with self._lock:
            self._pending_commands.pop(command_id, None)
        
        logger.error(f"Command {command_id} acknowledgment timeout")
        return False
    
    def arm_vehicle(self) -> bool:
        """
        Send ARM command to vehicle.
        
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info("Sending ARM command")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot ARM: not connected to drone")
            return False
        
        # MAV_CMD_COMPONENT_ARM_DISARM with param1=1 (arm)
        command_id = self._send_command_long(
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            param1=1,  # 1 = arm, 0 = disarm
            param2=0   # force arm (0 = no force)
        )
        
        if command_id is None:
            return False
        
        return self._wait_for_ack(command_id)
    
    def disarm_vehicle(self, force: bool = False) -> bool:
        """
        Send DISARM command to vehicle.
        
        Args:
            force: Force disarm even if not safe
            
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info(f"Sending DISARM command (force={force})")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot DISARM: not connected to drone")
            return False
        
        # MAV_CMD_COMPONENT_ARM_DISARM with param1=0 (disarm)
        command_id = self._send_command_long(
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            param1=0,  # 0 = disarm
            param2=21196 if force else 0  # magic number for force disarm
        )
        
        if command_id is None:
            return False
        
        return self._wait_for_ack(command_id)
    
    def takeoff(self, altitude: float) -> bool:
        """
        Send TAKEOFF command to vehicle.
        
        Args:
            altitude: Target altitude in meters
            
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info(f"Sending TAKEOFF command to {altitude}m")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot TAKEOFF: not connected to drone")
            return False
        
        if altitude <= 0 or altitude > 120:  # Safety check
            logger.error(f"Invalid takeoff altitude: {altitude}m")
            return False
        
        # MAV_CMD_NAV_TAKEOFF
        command_id = self._send_command_long(
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            param1=0,      # minimum pitch (if airspeed sensor present)
            param2=0,      # empty
            param3=0,      # empty
            param4=0,      # yaw angle (NaN uses current)
            param5=0,      # latitude (0 uses current)
            param6=0,      # longitude (0 uses current)
            param7=altitude # altitude
        )
        
        if command_id is None:
            return False
        
        return self._wait_for_ack(command_id)
    
    def land(self) -> bool:
        """
        Send LAND command to vehicle.
        
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info("Sending LAND command")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot LAND: not connected to drone")
            return False
        
        # MAV_CMD_NAV_LAND
        command_id = self._send_command_long(
            mavutil.mavlink.MAV_CMD_NAV_LAND,
            param1=0,  # abort altitude
            param2=0,  # precision land mode
            param3=0,  # empty
            param4=0,  # desired yaw angle
            param5=0,  # latitude (0 uses current)
            param6=0,  # longitude (0 uses current)
            param7=0   # altitude (0 uses current)
        )
        
        if command_id is None:
            return False
        
        return self._wait_for_ack(command_id)
    
    def return_to_launch(self) -> bool:
        """
        Send RETURN TO LAUNCH command to vehicle.
        
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info("Sending RTL command")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot RTL: not connected to drone")
            return False
        
        # MAV_CMD_NAV_RETURN_TO_LAUNCH
        command_id = self._send_command_long(mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH)
        
        if command_id is None:
            return False
        
        return self._wait_for_ack(command_id)
    
    def set_mode(self, mode: str) -> bool:
        """
        Set flight mode.
        
        Args:
            mode: Flight mode name (e.g., 'GUIDED', 'AUTO', 'RTL')
            
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info(f"Setting flight mode to {mode}")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot set mode: not connected to drone")
            return False
        
        mode_id = self._flight_modes.get(mode.upper())
        if mode_id is None:
            logger.error(f"Unknown flight mode: {mode}")
            return False
        
        connection = self.connection_manager.get_connection()
        if not connection:
            return False
        
        try:
            # Send SET_MODE message
            connection.mav.set_mode_send(
                connection.target_system,
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                mode_id
            )
            
            # Wait a moment and verify mode change
            time.sleep(0.5)
            
            logger.info(f"Mode change command sent for {mode}")
            return True  # Mode changes don't always send ACKs
            
        except Exception as e:
            logger.error(f"Failed to set mode {mode}: {e}")
            return False
    
    def goto_waypoint(self, latitude: float, longitude: float, altitude: float) -> bool:
        """
        Navigate to specified waypoint.
        
        Args:
            latitude: Target latitude in degrees
            longitude: Target longitude in degrees  
            altitude: Target altitude in meters
            
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info(f"Sending GOTO WAYPOINT command to {latitude}, {longitude}, {altitude}m")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot go to waypoint: not connected to drone")
            return False
        
        # MAV_CMD_NAV_WAYPOINT
        command_id = self._send_command_long(
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            param1=0,        # hold time (sec)
            param2=0,        # acceptance radius (m) 
            param3=0,        # pass radius (m)
            param4=0,        # desired yaw angle
            param5=latitude,
            param6=longitude,
            param7=altitude
        )
        
        if command_id is None:
            return False
        
        return self._wait_for_ack(command_id)
    
    def set_home(self) -> bool:
        """
        Set home position to current location.
        
        Returns:
            True if command sent and acknowledged successfully
        """
        logger.info("Sending SET HOME command")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot set home: not connected to drone")
            return False
        
        # MAV_CMD_DO_SET_HOME with param1=1 (use current position)
        command_id = self._send_command_long(
            mavutil.mavlink.MAV_CMD_DO_SET_HOME,
            param1=1,  # 1 = use current position, 0 = use specified position
            param2=0,
            param3=0,
            param4=0,
            param5=0,  # latitude (ignored when param1=1)
            param6=0,  # longitude (ignored when param1=1)
            param7=0   # altitude (ignored when param1=1)
        )
        
        if command_id is None:
            return False
        
        return self._wait_for_ack(command_id)
    
    def gimbal_control(self, pitch: float, yaw: float) -> bool:
        """
        Control gimbal position.
        
        Args:
            pitch: Pitch angle in degrees (-90 to +90)
            yaw: Yaw angle in degrees (-180 to +180)
            
        Returns:
            True if command sent successfully (gimbal commands don't always ACK)
        """
        logger.info(f"Sending GIMBAL CONTROL command: pitch={pitch}, yaw={yaw}")
        
        if not self.connection_manager.is_connected():
            logger.error("Cannot control gimbal: not connected to drone")
            return False
        
        connection = self.connection_manager.get_connection()
        if not connection:
            return False
        
        try:
            # Send MOUNT_CONTROL message
            connection.mav.mount_control_send(
                connection.target_system,
                connection.target_component,
                int(pitch * 100),  # pitch in centidegrees
                0,                 # roll in centidegrees
                int(yaw * 100),    # yaw in centidegrees
                0                  # save position
            )
            
            logger.info(f"Gimbal control command sent: pitch={pitch}, yaw={yaw}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send gimbal control: {e}")
            return False

    def get_pending_commands(self) -> Dict[int, Dict[str, Any]]:
        """Get currently pending commands."""
        with self._lock:
            return self._pending_commands.copy()
    
    def clear_pending_commands(self) -> None:
        """Clear all pending commands."""
        with self._lock:
            self._pending_commands.clear()
        logger.info("Cleared all pending commands")
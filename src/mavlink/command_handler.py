"""
MAVLink Command Handler for WebGCS
Handles sending commands and waiting for acknowledgments
File size: Must stay under 150 lines per WebGCS PRD
"""
import time
from typing import Optional
from src.utils.token_tracker import record_agent_usage


class CommandHandler:
    """Handles MAVLink command sending and acknowledgment."""
    
    def __init__(self, connection_handler):
        """Initialize command handler."""
        self.connection_handler = connection_handler
        record_agent_usage('mavlink-protocol-agent', 15, 10)
    
    def send_command_long(self, command: int, param1: float = 0, param2: float = 0,
                         param3: float = 0, param4: float = 0, param5: float = 0,
                         param6: float = 0, param7: float = 0) -> dict:
        """Send MAVLink COMMAND_LONG message."""
        if not self.connection_handler.is_connected():
            return {
                'success': False,
                'message': 'Not connected to drone',
                'ack_received': False
            }
        
        connection = self.connection_handler.get_connection()
        if not connection:
            return {
                'success': False,
                'message': 'No active connection',
                'ack_received': False
            }
        
        try:
            # Send COMMAND_LONG message
            connection.mav.command_long_send(
                self.connection_handler.get_system_id(),  # target_system
                1,  # target_component (autopilot)
                command,  # command
                0,  # confirmation
                param1, param2, param3, param4,
                param5, param6, param7
            )
            
            # Wait for acknowledgment with timeout
            start_time = time.time()
            timeout = 5.0  # 5 second timeout
            
            while (time.time() - start_time) < timeout:
                msg = connection.recv_match(type='COMMAND_ACK', blocking=False, timeout=0.1)
                if msg and msg.command == command:
                    record_agent_usage('mavlink-protocol-agent', 20, 15)
                    return {
                        'success': msg.result == 0,  # MAV_RESULT_ACCEPTED = 0
                        'message': f'Command {command} {"accepted" if msg.result == 0 else "rejected"}',
                        'ack_received': True,
                        'result_code': msg.result
                    }
            
            # Timeout occurred
            return {
                'success': False,
                'message': f'Command {command} timed out waiting for ACK',
                'ack_received': False
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error sending command: {str(e)}',
                'ack_received': False
            }
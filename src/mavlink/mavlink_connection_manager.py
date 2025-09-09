"""
MAVLink Connection Manager for WebGCS
Orchestrates connection, command, and telemetry handlers
File size: Must stay under 150 lines per WebGCS PRD
"""
from typing import Optional
from .connection_handler import ConnectionHandler
from .command_handler import CommandHandler
from .telemetry_handler import TelemetryHandler
from src.utils.token_tracker import record_agent_usage


class MAVLinkConnectionManager:
    """Manages MAVLink connection using modular handlers."""
    
    def __init__(self, host: str = "192.168.193.235", port: int = 5678, timeout: int = 10):
        """Initialize MAVLink connection manager."""
        self.connection_handler = ConnectionHandler(host, port, timeout)
        self.command_handler = CommandHandler(self.connection_handler)
        self.telemetry_handler = TelemetryHandler(self.connection_handler)
        
        # For backward compatibility
        self.host = host
        self.port = port
        self.timeout = timeout
        
        record_agent_usage('mavlink-protocol-agent', 20, 15)
    
    def connect(self, host: str = None, port: int = None, return_dict: bool = False):
        """Establish MAVLink connection to drone."""
        result = self.connection_handler.connect(host, port)
        
        # Update our local host/port for compatibility
        if host:
            self.host = host
        if port:
            self.port = port
            
        # Reset heartbeat counter on successful connection
        if result.get('success', False):
            self.telemetry_handler.reset_heartbeat_counter()
            
        record_agent_usage('mavlink-protocol-agent', 15, 10)
        
        # Store detailed result for get_last_connection_result()
        self._last_connection_result = result
        
        # Return dict if explicitly requested, otherwise return boolean for backward compatibility
        if return_dict:
            return result
        else:
            return result.get('success', False)
    
    def disconnect(self) -> bool:
        """Disconnect from drone."""
        # Reset heartbeat counter when disconnecting
        self.telemetry_handler.reset_heartbeat_counter()
        return self.connection_handler.disconnect()
    
    def is_connected(self) -> bool:
        """Check if currently connected to drone."""
        return self.connection_handler.is_connected()
    
    def get_system_id(self) -> Optional[int]:
        """Get drone system ID."""
        return self.connection_handler.get_system_id()
    
    def get_component_id(self) -> Optional[int]:
        """Get drone component ID."""
        return self.connection_handler.get_component_id()
    
    def send_command_long(self, command: int, param1: float = 0, param2: float = 0,
                         param3: float = 0, param4: float = 0, param5: float = 0,
                         param6: float = 0, param7: float = 0) -> dict:
        """Send MAVLink COMMAND_LONG message."""
        return self.command_handler.send_command_long(
            command, param1, param2, param3, param4, param5, param6, param7
        )
    
    def get_telemetry_data(self) -> dict:
        """Get current telemetry data from drone."""
        return self.telemetry_handler.get_telemetry_data()
    
    def get_connection_info(self) -> dict:
        """Get connection information."""
        info = self.connection_handler.get_connection_info()
        # Add compatibility fields
        info.update({
            'host': self.host,
            'port': self.port
        })
        return info
    
    def get_last_connection_result(self) -> dict:
        """Get detailed result from last connection attempt."""
        return getattr(self, '_last_connection_result', {'success': False, 'message': 'No connection attempted'})
    
    # Properties for backward compatibility
    @property
    def connected(self) -> bool:
        """Get connected status."""
        return self.connection_handler.connected
    
    @property
    def system_id(self) -> Optional[int]:
        """Get system ID."""
        return self.connection_handler.system_id
    
    @property
    def component_id(self) -> Optional[int]:
        """Get component ID."""
        return self.connection_handler.component_id
    
    @property
    def connection(self):
        """Get connection object."""
        return self.connection_handler.connection
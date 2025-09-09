"""
MAVLink Connection Handler for WebGCS
Handles basic connection establishment and management
File size: Must stay under 150 lines per WebGCS PRD
"""
import socket
import time
import threading
from typing import Optional
from pymavlink import mavutil
from src.utils.token_tracker import record_agent_usage


class ConnectionHandler:
    """Handles MAVLink connection establishment and basic management."""
    
    def __init__(self, host: str = "192.168.193.235", port: int = 5678, timeout: int = 10):
        """Initialize connection handler."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.connection = None
        self.connected = False
        self.system_id = None
        self.component_id = None
        self._lock = threading.Lock()
        
        record_agent_usage('mavlink-protocol-agent', 20, 15)
    
    def connect(self, host: str = None, port: int = None):
        """Establish MAVLink connection to drone."""
        target_host = host or self.host
        target_port = port or self.port
        
        with self._lock:
            try:
                if host:
                    self.host = host
                if port:
                    self.port = port
                
                # Test TCP connection first
                if not self._test_tcp_connection():
                    return {
                        'success': False,
                        'message': f'Cannot reach {target_host}:{target_port}',
                        'host': target_host,
                        'port': target_port
                    }
                
                # Create MAVLink connection
                connection_string = f"tcp:{target_host}:{target_port}"
                self.connection = mavutil.mavlink_connection(
                    connection_string,
                    timeout=self.timeout
                )
                
                if self.connection:
                    # Wait for heartbeat to confirm connection
                    start_time = time.time()
                    while (time.time() - start_time) < self.timeout:
                        msg = self.connection.recv_match(blocking=False)
                        if msg and msg.get_type() == 'HEARTBEAT':
                            self.system_id = msg.get_srcSystem()
                            self.component_id = msg.get_srcComponent()
                            self.connected = True
                            record_agent_usage('mavlink-protocol-agent', 30, 20)
                            return {
                                'success': True,
                                'message': f'Connected to drone at {target_host}:{target_port}',
                                'host': target_host,
                                'port': target_port,
                                'system_id': self.system_id,
                                'component_id': self.component_id
                            }
                        time.sleep(0.1)
                
                return {
                    'success': False,
                    'message': f'No heartbeat received from {target_host}:{target_port}',
                    'host': target_host,
                    'port': target_port
                }
                
            except Exception as e:
                self.connected = False
                record_agent_usage('mavlink-protocol-agent', 15, 10)
                return {
                    'success': False,
                    'message': f'Connection error: {str(e)}',
                    'host': target_host,
                    'port': target_port
                }
    
    def disconnect(self) -> bool:
        """Disconnect from drone."""
        with self._lock:
            try:
                if self.connection:
                    self.connection.close()
                    self.connection = None
                
                self.connected = False
                self.system_id = None
                self.component_id = None
                
                record_agent_usage('mavlink-protocol-agent', 10, 5)
                return True
                
            except Exception:
                return False
    
    def is_connected(self) -> bool:
        """Check if currently connected to drone."""
        return self.connected
    
    def get_system_id(self) -> Optional[int]:
        """Get drone system ID."""
        return self.system_id
    
    def get_component_id(self) -> Optional[int]:
        """Get drone component ID."""
        return self.component_id
    
    def _test_tcp_connection(self) -> bool:
        """Test if TCP endpoint is reachable."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(self.timeout)
                result = sock.connect_ex((self.host, self.port))
                return result == 0
        except Exception:
            return False
    
    def get_connection_info(self) -> dict:
        """Get connection information."""
        return {
            'host': self.host,
            'port': self.port,
            'connected': self.connected,
            'system_id': self.system_id,
            'component_id': self.component_id
        }
    
    def get_connection(self):
        """Get the MAVLink connection object."""
        return self.connection
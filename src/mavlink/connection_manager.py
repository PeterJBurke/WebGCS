"""
WebGCS MAVLink Connection Manager
Handles connection establishment and maintenance with drone.
"""

import time
import threading
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from pymavlink import mavutil

from .connection_state import ConnectionState, HeartbeatMonitor, ReconnectionManager

logger = logging.getLogger('webgcs.mavlink.connection')


class ConnectionManager:
    """Manages MAVLink connection to drone with heartbeat monitoring and auto-reconnect."""
    
    def __init__(self, host: str, port: int, heartbeat_timeout: int = 30):
        """
        Initialize connection manager.
        
        Args:
            host: Drone TCP host address
            port: Drone TCP port
            heartbeat_timeout: Timeout in seconds for heartbeat monitoring
        """
        self.host = host
        self.port = port
        self.heartbeat_timeout = heartbeat_timeout
        
        # Connection state
        self._connection: Optional[mavutil.mavudp] = None
        self._state = ConnectionState.DISCONNECTED
        self._lock = threading.RLock()
        self._last_heartbeat: Optional[datetime] = None
        
        # State change callbacks
        self._state_callbacks: list[Callable[[str, Dict[str, Any]], None]] = []
        
        # Monitoring components
        self._heartbeat_monitor = HeartbeatMonitor(self, heartbeat_timeout)
        self._reconnection_manager = ReconnectionManager(self)
        
        logger.info(f"ConnectionManager initialized for {host}:{port}")
    
    def add_state_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Add callback for connection state changes."""
        with self._lock:
            self._state_callbacks.append(callback)
    
    def _notify_state_change(self, old_state: str, new_state: str, details: Dict[str, Any] = None):
        """Notify all callbacks of state change."""
        if details is None:
            details = {}
        
        details.update({
            'old_state': old_state,
            'new_state': new_state,
            'timestamp': datetime.now().isoformat(),
            'endpoint': f"{self.host}:{self.port}"
        })
        
        # Update internal state
        with self._lock:
            self._state = new_state
        
        # Notify callbacks
        for callback in self._state_callbacks:
            try:
                callback(new_state, details)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")
    
    def connect(self) -> bool:
        """
        Establish connection to drone.
        
        Returns:
            True if connection successful, False otherwise
        """
        with self._lock:
            if self._state == ConnectionState.CONNECTED:
                logger.warning("Already connected to drone")
                return True
            
            old_state = self._state
            self._notify_state_change(old_state, ConnectionState.CONNECTING)
            
            try:
                # Create MAVLink connection
                connection_string = f"tcp:{self.host}:{self.port}"
                logger.info(f"Connecting to drone at {connection_string}")
                
                self._connection = mavutil.mavlink_connection(
                    connection_string,
                    source_system=255,
                    source_component=0,
                    force_connected=True
                )
                
                # Test connection with timeout
                start_time = time.time()
                while time.time() - start_time < 5.0:  # 5 second timeout
                    try:
                        # Send heartbeat and check for response
                        self._send_heartbeat()
                        msg = self._connection.recv_match(type='HEARTBEAT', blocking=False, timeout=1)
                        if msg:
                            self._last_heartbeat = datetime.now()
                            break
                    except Exception as e:
                        logger.debug(f"Connection test error: {e}")
                        time.sleep(0.1)
                
                if self._last_heartbeat is None:
                    # Connection established but no heartbeat received yet
                    logger.warning("Connection established but no heartbeat received")
                    self._last_heartbeat = datetime.now()  # Set to allow monitoring to start
                
                # Start heartbeat monitoring
                self._heartbeat_monitor.start()
                
                self._notify_state_change(ConnectionState.CONNECTING, ConnectionState.CONNECTED, {
                    'last_heartbeat': self._last_heartbeat.isoformat()
                })
                
                logger.info(f"Successfully connected to drone at {self.host}:{self.port}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to drone: {e}")
                self._cleanup_connection()
                self._notify_state_change(ConnectionState.CONNECTING, ConnectionState.ERROR, {'error': str(e)})
                return False
    
    def disconnect(self) -> None:
        """Disconnect from drone and cleanup resources."""
        with self._lock:
            if self._state == ConnectionState.DISCONNECTED:
                return
            
            old_state = self._state
            logger.info("Disconnecting from drone")
            
            # Stop monitoring
            self._heartbeat_monitor.stop()
            self._reconnection_manager.stop_reconnection()
            
            # Cleanup connection
            self._cleanup_connection()
            
            self._notify_state_change(old_state, ConnectionState.DISCONNECTED)
            logger.info("Disconnected from drone")
    
    def _cleanup_connection(self) -> None:
        """Internal method to cleanup connection resources."""
        # Close MAVLink connection
        if self._connection:
            try:
                self._connection.close()
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            finally:
                self._connection = None
        
        self._last_heartbeat = None
    
    def is_connected(self) -> bool:
        """Check if connected to drone."""
        with self._lock:
            return self._state == ConnectionState.CONNECTED and self._connection is not None
    
    def get_state(self) -> str:
        """Get current connection state."""
        with self._lock:
            return self._state
    
    def get_connection(self) -> Optional[mavutil.mavudp]:
        """Get the MAVLink connection object (thread-safe)."""
        with self._lock:
            return self._connection if self._state == ConnectionState.CONNECTED else None
    
    def get_last_heartbeat(self) -> Optional[datetime]:
        """Get timestamp of last received heartbeat."""
        with self._lock:
            return self._last_heartbeat
    
    def update_heartbeat(self, timestamp: datetime) -> None:
        """Update last heartbeat timestamp."""
        with self._lock:
            self._last_heartbeat = timestamp
    
    def _send_heartbeat(self) -> None:
        """Send heartbeat message to drone."""
        if self._connection:
            try:
                self._connection.mav.heartbeat_send(
                    mavutil.mavlink.MAV_TYPE_GCS,
                    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
                    0, 0, 0
                )
            except Exception as e:
                logger.debug(f"Error sending heartbeat: {e}")
    
    def _handle_connection_loss(self) -> None:
        """Handle detected connection loss."""
        with self._lock:
            if self._state != ConnectionState.CONNECTED:
                return
            
            old_state = self._state
            self._notify_state_change(old_state, ConnectionState.ERROR, {
                'reason': 'heartbeat_timeout',
                'last_heartbeat': self._last_heartbeat.isoformat() if self._last_heartbeat else None
            })
            
            logger.error("Connection lost - starting reconnection process")
            self._reconnection_manager.start_reconnection()
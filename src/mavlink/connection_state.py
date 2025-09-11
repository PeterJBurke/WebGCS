"""
WebGCS MAVLink Connection State Management
Handles connection state tracking and monitoring.
"""

import threading
import time
import logging
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from pymavlink import mavutil

logger = logging.getLogger('webgcs.mavlink.state')


class ConnectionState:
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class HeartbeatMonitor:
    """Monitors heartbeat messages and handles connection loss."""
    
    def __init__(self, connection_manager, heartbeat_timeout: int = 30):
        """Initialize heartbeat monitor."""
        self.connection_manager = connection_manager
        self.heartbeat_timeout = heartbeat_timeout
        self._stop_monitor = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start heartbeat monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitor = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="HeartbeatMonitor",
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Heartbeat monitor started")
    
    def stop(self) -> None:
        """Stop heartbeat monitoring."""
        self._stop_monitor = True
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2)
        logger.info("Heartbeat monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_monitor:
            try:
                if not self.connection_manager.is_connected():
                    break
                
                # Check for heartbeat timeout
                last_heartbeat = self.connection_manager.get_last_heartbeat()
                if last_heartbeat:
                    time_since_heartbeat = datetime.now() - last_heartbeat
                    if time_since_heartbeat.total_seconds() > self.heartbeat_timeout:
                        logger.warning(f"Heartbeat timeout: {time_since_heartbeat.total_seconds():.1f}s")
                        self.connection_manager._handle_connection_loss()
                        break
                
                # Send our heartbeat
                self.connection_manager._send_heartbeat()
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                break


class ReconnectionManager:
    """Handles automatic reconnection with exponential backoff."""
    
    def __init__(self, connection_manager, max_attempts: int = 5, initial_delay: float = 2.0):
        """Initialize reconnection manager."""
        self.connection_manager = connection_manager
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self._stop_reconnect = False
        self._reconnect_thread: Optional[threading.Thread] = None
    
    def start_reconnection(self) -> None:
        """Start reconnection process."""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        
        self._stop_reconnect = False
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop,
            name="ReconnectLoop",
            daemon=True
        )
        self._reconnect_thread.start()
        logger.info("Starting reconnection process")
    
    def stop_reconnection(self) -> None:
        """Stop reconnection process."""
        self._stop_reconnect = True
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            self._reconnect_thread.join(timeout=2)
    
    def _reconnect_loop(self) -> None:
        """Reconnection loop with exponential backoff."""
        attempt = 0
        
        while not self._stop_reconnect and attempt < self.max_attempts:
            attempt += 1
            delay = min(self.initial_delay * (2 ** (attempt - 1)), 30)  # Max 30s delay
            
            self.connection_manager._notify_state_change(
                self.connection_manager.get_state(),
                ConnectionState.RECONNECTING,
                {
                    'attempt': attempt,
                    'max_attempts': self.max_attempts,
                    'delay': delay
                }
            )
            
            logger.info(f"Reconnection attempt {attempt}/{self.max_attempts} in {delay}s")
            
            # Wait with cancellation check
            for _ in range(int(delay * 10)):  # 0.1s intervals
                if self._stop_reconnect:
                    return
                time.sleep(0.1)
            
            if self._stop_reconnect:
                return
            
            # Cleanup and attempt reconnection
            self.connection_manager._cleanup_connection()
            if self.connection_manager.connect():
                logger.info("Reconnection successful")
                return
        
        # All attempts failed
        self.connection_manager._notify_state_change(
            self.connection_manager.get_state(),
            ConnectionState.ERROR,
            {
                'reason': 'reconnection_failed',
                'attempts': attempt
            }
        )
        logger.error("All reconnection attempts failed")
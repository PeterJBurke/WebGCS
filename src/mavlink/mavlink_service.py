"""
WebGCS MAVLink Service
Central service for MAVLink communication coordination.
"""

import threading
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import os

from .connection_manager import ConnectionManager
from .message_processor import MessageProcessor
from .command_sender import CommandSender

logger = logging.getLogger('webgcs.mavlink.service')


class MAVLinkService:
    """Central MAVLink service managing all drone communication."""
    
    def __init__(self, host: str, port: int, socketio_app=None):
        """
        Initialize MAVLink service.
        
        Args:
            host: Drone TCP host address
            port: Drone TCP port
            socketio_app: Optional SocketIO app for real-time updates
        """
        self.host = host
        self.port = port
        self.socketio = socketio_app
        
        # Core components
        heartbeat_timeout = int(os.getenv('HEARTBEAT_TIMEOUT', '30'))
        ack_timeout = float(os.getenv('COMMAND_ACK_TIMEOUT', '10'))
        
        self.connection_manager = ConnectionManager(host, port, heartbeat_timeout)
        self.message_processor = MessageProcessor()
        self.command_sender = CommandSender(self.connection_manager, ack_timeout)
        
        # Message processing
        self._message_thread: Optional[threading.Thread] = None
        self._stop_processing = False
        self._telemetry_callbacks: list[Callable[[Dict[str, Any]], None]] = []
        
        # Telemetry streaming
        self._telemetry_interval = float(os.getenv('TELEMETRY_UPDATE_INTERVAL', '0.1'))  # 10Hz
        self._telemetry_thread: Optional[threading.Thread] = None
        self._stop_telemetry = False
        
        # Setup connection callbacks
        self.connection_manager.add_state_callback(self._on_connection_state_change)
        
        logger.info(f"MAVLinkService initialized for {host}:{port}")
    
    def start(self) -> bool:
        """
        Start the MAVLink service.
        
        Returns:
            True if started successfully
        """
        logger.info("Starting MAVLink service")
        
        # Connect to drone
        if not self.connection_manager.connect():
            logger.error("Failed to connect to drone")
            return False
        
        # Start message processing
        self._start_message_processing()
        
        # Start telemetry streaming
        self._start_telemetry_streaming()
        
        logger.info("MAVLink service started successfully")
        return True
    
    def stop(self) -> None:
        """Stop the MAVLink service."""
        logger.info("Stopping MAVLink service")
        
        # Stop threads
        self._stop_processing = True
        self._stop_telemetry = True
        
        # Wait for threads to finish
        if self._message_thread and self._message_thread.is_alive():
            self._message_thread.join(timeout=2)
        
        if self._telemetry_thread and self._telemetry_thread.is_alive():
            self._telemetry_thread.join(timeout=2)
        
        # Disconnect from drone
        self.connection_manager.disconnect()
        
        logger.info("MAVLink service stopped")
    
    def _start_message_processing(self) -> None:
        """Start message processing thread."""
        if self._message_thread and self._message_thread.is_alive():
            return
        
        self._stop_processing = False
        self._message_thread = threading.Thread(
            target=self._message_processing_loop,
            name="MAVLinkProcessor",
            daemon=True
        )
        self._message_thread.start()
        logger.info("Message processing started")
    
    def _start_telemetry_streaming(self) -> None:
        """Start telemetry streaming thread."""
        if self._telemetry_thread and self._telemetry_thread.is_alive():
            return
        
        self._stop_telemetry = False
        self._telemetry_thread = threading.Thread(
            target=self._telemetry_streaming_loop,
            name="TelemetryStreamer",
            daemon=True
        )
        self._telemetry_thread.start()
        logger.info("Telemetry streaming started")
    
    def _message_processing_loop(self) -> None:
        """Main message processing loop."""
        logger.info("Message processing loop started")
        
        while not self._stop_processing:
            try:
                connection = self.connection_manager.get_connection()
                if not connection:
                    time.sleep(0.1)
                    continue
                
                # Process incoming messages
                msg = connection.recv_match(blocking=False, timeout=0.1)
                if msg:
                    # Update heartbeat timestamp for heartbeat messages
                    if msg.get_type() == 'HEARTBEAT':
                        self.connection_manager.update_heartbeat(datetime.now())
                    
                    # Process message
                    result = self.message_processor.process_message(msg)
                    if result:
                        # Notify telemetry callbacks
                        for callback in self._telemetry_callbacks:
                            try:
                                callback(result)
                            except Exception as e:
                                logger.error(f"Error in telemetry callback: {e}")
                
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
                time.sleep(1.0)  # Back off on error
        
        logger.info("Message processing loop stopped")
    
    def _telemetry_streaming_loop(self) -> None:
        """Telemetry streaming loop for real-time web updates."""
        logger.info("Telemetry streaming loop started")
        
        while not self._stop_telemetry:
            try:
                if self.socketio and self.connection_manager.is_connected():
                    # Get current telemetry snapshot
                    telemetry = self.message_processor.get_telemetry_snapshot()
                    
                    # FIX: Add timestamp for heartbeat display
                    last_heartbeat = self.connection_manager.get_last_heartbeat()
                    telemetry['timestamp'] = last_heartbeat.isoformat() if last_heartbeat else None
                    telemetry['last_heartbeat'] = last_heartbeat.isoformat() if last_heartbeat else None
                    
                    # Add connection status
                    telemetry.update({
                        'connection_status': {
                            'state': self.connection_manager.get_state(),
                            'last_heartbeat': last_heartbeat.isoformat() if last_heartbeat else None,
                            'endpoint': f"{self.host}:{self.port}"
                        }
                    })
                    
                    # Emit to all clients
                    self.socketio.emit('telemetry_update', telemetry)
                    
                    # FIX: Update drone connection status
                    heartbeat_data = telemetry.get('heartbeat', {})
                    self.socketio.emit('system_status', {
                        'mavlink_connected': True,
                        'drone_armed': heartbeat_data.get('armed', False),
                        'flight_mode': heartbeat_data.get('flight_mode', 'UNKNOWN'),
                        'last_heartbeat': last_heartbeat.isoformat() if last_heartbeat else None
                    })
                
                time.sleep(self._telemetry_interval)
                
            except Exception as e:
                logger.error(f"Error in telemetry streaming: {e}")
                time.sleep(1.0)
        
        logger.info("Telemetry streaming loop stopped")
    
    def _on_connection_state_change(self, new_state: str, details: Dict[str, Any]) -> None:
        """Handle connection state changes."""
        logger.info(f"Connection state changed to: {new_state}")
        
        # Emit state change to web clients
        if self.socketio:
            self.socketio.emit('connection_status_update', {
                'state': new_state,
                'details': details,
                'timestamp': datetime.now().isoformat()
            })
    
    def add_telemetry_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add callback for telemetry updates."""
        self._telemetry_callbacks.append(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status."""
        telemetry = self.message_processor.get_telemetry_snapshot()
        
        return {
            'mavlink_connected': self.connection_manager.is_connected(),
            'connection_state': self.connection_manager.get_state(),
            'last_heartbeat': self.connection_manager.get_last_heartbeat().isoformat() if self.connection_manager.get_last_heartbeat() else None,
            'drone_endpoint': f"{self.host}:{self.port}",
            'armed_status': telemetry.get('heartbeat', {}).get('armed', False),
            'flight_mode': telemetry.get('heartbeat', {}).get('flight_mode', 'UNKNOWN'),
            'pending_commands': len(self.command_sender.get_pending_commands()),
            'last_telemetry_update': telemetry.get('last_update'),
            'service_threads': {
                'message_processor': self._message_thread.is_alive() if self._message_thread else False,
                'telemetry_streamer': self._telemetry_thread.is_alive() if self._telemetry_thread else False
            }
        }
    
    # Connection interface methods
    def connect_to_drone(self) -> bool:
        """
        Initiate connection to drone.
        
        Returns:
            True if connection successful
        """
        logger.info("Manual drone connection requested")
        
        # If already connected, return True
        if self.connection_manager.is_connected():
            logger.info("Already connected to drone")
            return True
        
        # If service is not started, start it (which will connect)
        if not self._message_thread or not self._message_thread.is_alive():
            return self.start()
        
        # If service is running but not connected, try to reconnect
        return self.connection_manager.connect()
    
    def disconnect_from_drone(self) -> bool:
        """
        Disconnect from drone.
        
        Returns:
            True always (disconnect operations don't typically fail)
        """
        logger.info("Manual drone disconnection requested")
        
        # Stop telemetry streaming
        self._stop_telemetry = True
        if self._telemetry_thread and self._telemetry_thread.is_alive():
            self._telemetry_thread.join(timeout=2)
        
        # Stop message processing
        self._stop_processing = True
        if self._message_thread and self._message_thread.is_alive():
            self._message_thread.join(timeout=2)
        
        # Disconnect from drone
        self.connection_manager.disconnect()
        
        return True

    # Command interface methods
    def arm_vehicle(self) -> bool:
        """ARM the vehicle."""
        return self.command_sender.arm_vehicle()
    
    def disarm_vehicle(self, force: bool = False) -> bool:
        """DISARM the vehicle."""
        return self.command_sender.disarm_vehicle(force)
    
    def takeoff(self, altitude: float) -> bool:
        """Command vehicle to takeoff."""
        return self.command_sender.takeoff(altitude)
    
    def land(self) -> bool:
        """Command vehicle to land."""
        return self.command_sender.land()
    
    def return_to_launch(self) -> bool:
        """Command vehicle to return to launch."""
        return self.command_sender.return_to_launch()
    
    def set_mode(self, mode: str) -> bool:
        """Set vehicle flight mode."""
        return self.command_sender.set_mode(mode)
    
    def goto_waypoint(self, latitude: float, longitude: float, altitude: float) -> bool:
        """Go to specified waypoint."""
        return self.command_sender.goto_waypoint(latitude, longitude, altitude)
    
    def set_home(self) -> bool:
        """Set home position to current location."""
        return self.command_sender.set_home()
    
    def emergency_stop(self) -> bool:
        """Emergency stop - immediate disarm."""
        return self.command_sender.disarm_vehicle(force=True)
    
    def gimbal_control(self, pitch: float, yaw: float) -> bool:
        """Control gimbal position."""
        return self.command_sender.gimbal_control(pitch, yaw)
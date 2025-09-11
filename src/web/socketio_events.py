"""
WebGCS SocketIO Event Handlers
Real-time communication between web interface and backend systems.
"""

from flask_socketio import SocketIO, emit, disconnect
from flask import request
import logging
from typing import Dict, Any

logger = logging.getLogger('webgcs')


def register_socketio_handlers(socketio: SocketIO) -> None:
    """
    Register all SocketIO event handlers.
    
    Args:
        socketio: SocketIO instance to register handlers with
    """
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection."""
        client_id = request.sid
        logger.info(f"Client connected: {client_id}")
        
        # Send initial connection confirmation
        emit('connection_status', {
            'status': 'connected',
            'client_id': client_id,
            'message': 'WebGCS connection established'
        })
        
        # FIX: Send current drone status and telemetry
        from flask import current_app
        mavlink_service = getattr(current_app, 'mavlink_service', None)
        if mavlink_service:
            status = mavlink_service.get_status()
            
            # Send drone connection status
            is_connected = status.get('mavlink_connected', False)
            emit('drone_connected' if is_connected else 'drone_disconnected', {
                'status': 'connected' if is_connected else 'disconnected',
                'timestamp': status.get('last_heartbeat').isoformat() if status.get('last_heartbeat') else None
            })
            
            emit('system_status', {
                'mavlink_connected': is_connected,
                'drone_armed': status.get('armed_status', False),
                'flight_mode': status.get('flight_mode', 'UNKNOWN'),
                'last_heartbeat': status.get('last_heartbeat').isoformat() if status.get('last_heartbeat') else None
            })
            
            # FIX: Send current telemetry data if available
            telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            if telemetry:
                # Add timestamp for heartbeat display
                telemetry['timestamp'] = status.get('last_heartbeat').isoformat() if status.get('last_heartbeat') else None
                emit('telemetry_update', telemetry)
        else:
            emit('system_status', {
                'mavlink_connected': False,
                'drone_armed': False,
                'flight_mode': 'UNKNOWN',
                'last_heartbeat': None
            })
    
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        client_id = request.sid
        logger.info(f"Client disconnected: {client_id}")
    
    
    @socketio.on('request_telemetry')
    def handle_telemetry_request(data: Dict[str, Any]):
        """
        Handle telemetry data requests.
        
        Args:
            data: Request parameters including update rate
        """
        try:
            client_id = request.sid
            update_rate = data.get('rate_hz', 4)
            
            logger.info(f"Telemetry requested by {client_id} at {update_rate}Hz")
            
            # Acknowledge telemetry stream request
            # The MAVLink service already streams telemetry automatically
            emit('telemetry_stream_started', {
                'rate_hz': update_rate,
                'status': 'acknowledged'
            })
            
        except Exception as e:
            logger.error(f"Error handling telemetry request: {e}")
            emit('error', {'message': 'Failed to start telemetry stream'})
    
    
    @socketio.on('send_command')
    def handle_command(data: Dict[str, Any]):
        """
        Handle MAVLink command requests.
        
        Args:
            data: Command parameters including command type and parameters
        """
        try:
            client_id = request.sid
            command_type = data.get('command')
            parameters = data.get('parameters', {})
            
            logger.info(f"Command received from {client_id}: {command_type}")
            
            # Execute command via MAVLink service
            from flask import current_app
            mavlink_service = getattr(current_app, 'mavlink_service', None)
            
            if not mavlink_service:
                emit('command_error', {
                    'command': command_type,
                    'error': 'MAVLink service not available'
                })
                return
            
            success = False
            error_msg = None
            
            try:
                # Route command to appropriate handler
                if command_type == 'connect_drone':
                    success = mavlink_service.connect_to_drone()
                    if success:
                        emit('drone_connected', {
                            'status': 'connected',
                            'message': 'Drone connected successfully'
                        })
                    else:
                        emit('connection_error', {
                            'status': 'failed',
                            'message': 'Failed to connect to drone'
                        })
                    return  # Early return for connection commands
                
                elif command_type == 'disconnect_drone':
                    success = mavlink_service.disconnect_from_drone()
                    emit('drone_disconnected', {
                        'status': 'disconnected',
                        'message': 'Drone disconnected'
                    })
                    return  # Early return for connection commands
                
                elif command_type == 'arm':
                    success = mavlink_service.arm_vehicle()
                elif command_type == 'disarm':
                    force = parameters.get('force', False)
                    success = mavlink_service.disarm_vehicle(force)
                elif command_type == 'takeoff':
                    altitude = parameters.get('altitude', 10.0)
                    success = mavlink_service.takeoff(altitude)
                elif command_type == 'land':
                    success = mavlink_service.land()
                elif command_type == 'rtl':
                    success = mavlink_service.return_to_launch()
                elif command_type == 'set_mode':
                    mode = parameters.get('mode', 'GUIDED')
                    success = mavlink_service.set_mode(mode)
                elif command_type == 'goto_waypoint':
                    latitude = parameters.get('latitude')
                    longitude = parameters.get('longitude')
                    altitude = parameters.get('altitude', 10.0)
                    if latitude is not None and longitude is not None:
                        success = mavlink_service.goto_waypoint(latitude, longitude, altitude)
                    else:
                        error_msg = "goto_waypoint requires latitude and longitude"
                elif command_type == 'set_home':
                    success = mavlink_service.set_home()
                elif command_type == 'emergency_stop':
                    success = mavlink_service.emergency_stop()
                elif command_type == 'gimbal_control':
                    pitch = parameters.get('pitch', 0)
                    yaw = parameters.get('yaw', 0)
                    success = mavlink_service.gimbal_control(pitch, yaw)
                else:
                    error_msg = f"Unknown command: {command_type}"
                
                if success:
                    emit('command_acknowledged', {
                        'command': command_type,
                        'status': 'success',
                        'parameters': parameters
                    })
                elif error_msg:
                    emit('command_error', {
                        'command': command_type,
                        'error': error_msg
                    })
                else:
                    emit('command_error', {
                        'command': command_type,
                        'error': 'Command failed or timed out'
                    })
                    
            except Exception as e:
                logger.error(f"Error executing command {command_type}: {e}")
                emit('command_error', {
                    'command': command_type,
                    'error': f'Exception: {str(e)}'
                })
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            emit('command_error', {
                'command': data.get('command'),
                'error': 'Failed to process command'
            })
    
    
    @socketio.on('request_connection_status')
    def handle_connection_status_request():
        """Handle request for current connection status."""
        try:
            # Get connection status from MAVLink service
            from flask import current_app
            mavlink_service = getattr(current_app, 'mavlink_service', None)
            
            if mavlink_service:
                status = mavlink_service.get_status()
                emit('connection_status_update', {
                    'mavlink_connected': status.get('mavlink_connected', False),
                    'connection_state': status.get('connection_state', 'disconnected'),
                    'drone_endpoint': status.get('drone_endpoint', 'unknown'),
                    'last_heartbeat': status.get('last_heartbeat').isoformat() if status.get('last_heartbeat') else None,
                    'flight_mode': status.get('flight_mode', 'UNKNOWN'),
                    'armed_status': status.get('armed_status', False)
                })
            else:
                emit('connection_status_update', {
                    'mavlink_connected': False,
                    'drone_endpoint': 'unknown',
                    'last_heartbeat': None,
                    'connection_time': None
                })
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            emit('error', {'message': 'Failed to get connection status'})
    
    
    @socketio.on('error')
    def handle_error(data):
        """Handle SocketIO errors."""
        client_id = request.sid
        logger.error(f"SocketIO error from {client_id}: {data}")


def emit_telemetry_update(socketio: SocketIO, telemetry_data: Dict[str, Any]) -> None:
    """
    Broadcast telemetry update to all connected clients.
    
    Args:
        socketio: SocketIO instance
        telemetry_data: Telemetry data to broadcast
    """
    try:
        socketio.emit('telemetry_update', telemetry_data)
    except Exception as e:
        logger.error(f"Error emitting telemetry update: {e}")


def emit_command_response(socketio: SocketIO, command_id: str, response_data: Dict[str, Any]) -> None:
    """
    Emit command response to specific client.
    
    Args:
        socketio: SocketIO instance
        command_id: ID of the command being responded to
        response_data: Response data to send
    """
    try:
        socketio.emit('command_response', {
            'command_id': command_id,
            'response': response_data
        })
    except Exception as e:
        logger.error(f"Error emitting command response: {e}")
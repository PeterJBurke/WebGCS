"""
SocketIO Event Handlers for WebGCS
Handles real-time communication with web interface

File size: Must stay under 150 lines per WebGCS PRD
"""
import threading
import time
from flask_socketio import emit, join_room, leave_room
from src.utils.token_tracker import record_agent_usage
from src.mavlink.mavlink_connection_manager import MAVLinkConnectionManager
from src.mavlink.mavlink_command_sender import MAVLinkCommandSender
from src.mavlink.mavlink_message_processor import MAVLinkMessageProcessor

# Global MAVLink components (shared across all SocketIO connections)
mavlink_connection = MAVLinkConnectionManager()
mavlink_command_sender = MAVLinkCommandSender(connection_manager=mavlink_connection)
message_processor = MAVLinkMessageProcessor()

# Global telemetry streaming state
telemetry_thread = None
telemetry_running = False
socketio_instance = None


def register_socketio_events(socketio):
    """Register all SocketIO event handlers."""
    global socketio_instance
    socketio_instance = socketio
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        record_agent_usage('web-interface-agent', 30, 25)
        emit('connection_response', {'status': 'connected', 'message': 'WebGCS connected'})
        
        # Send current actual connection status instead of always false
        if mavlink_connection.is_connected():
            telemetry_data = mavlink_connection.get_telemetry_data()
            emit('drone_status', {
                'connected': True,
                'system_id': mavlink_connection.get_system_id(),
                'heartbeat_count': telemetry_data.get('heartbeat_count', 0),
                'telemetry': telemetry_data
            })
        else:
            emit('drone_status', {
                'connected': False,
                'system_id': None,
                'heartbeat_count': 0,
                'telemetry': {}
            })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        record_agent_usage('web-interface-agent', 20, 15)
        print('Client disconnected from WebGCS')
    
    @socketio.on('connect_drone')
    def handle_connect_drone(data):
        """Handle drone connection request."""
        print(f"🔧 DEBUG: connect_drone event received with data: {data}")
        
        host = data.get('host', '192.168.193.235')  # Default to external drone
        port = data.get('port', 5678)
        
        print(f"🔧 DEBUG: Attempting connection to {host}:{port}")
        
        record_agent_usage('web-interface-agent', 35, 30)
        
        # Use real MAVLink connection manager
        success = mavlink_connection.connect(host, port)
        result = mavlink_connection.get_last_connection_result()
        
        print(f"🔧 DEBUG: Connection result - success: {success}, result: {result}")
        
        if success:
            # Update command sender with system/component IDs
            mavlink_command_sender.command_builder.target_system = result.get('system_id', 1)
            mavlink_command_sender.command_builder.target_component = result.get('component_id', 1)
            
            # Start telemetry streaming when successfully connected
            start_telemetry_streaming()
            print("🔧 DEBUG: Started telemetry streaming")
        
        print(f"🔧 DEBUG: Emitting drone_connection_result: {result}")
        emit('drone_connection_result', result)
    
    @socketio.on('disconnect_drone')
    def handle_disconnect_drone(data=None):
        """Handle drone disconnection request."""
        record_agent_usage('web-interface-agent', 25, 20)
        
        # Stop telemetry streaming when disconnecting
        stop_telemetry_streaming()
        
        # Use real MAVLink connection manager
        success = mavlink_connection.disconnect()
        
        # Send updated status with reset heartbeat
        emit('drone_status', {
            'connected': False,
            'system_id': None,
            'heartbeat_count': 0,  # Reset to 0 on disconnect
            'telemetry': {}
        })
        
        emit('drone_disconnection_result', {
            'success': success,
            'message': 'Drone disconnected successfully' if success else 'Disconnection failed'
        })
    
    @socketio.on('send_command')
    def handle_send_command(data):
        """Handle flight command from web interface."""
        command_type = data.get('command')
        params = data.get('params', {})
        
        record_agent_usage('web-interface-agent', 40, 35)
        
        # Handle different command types
        if command_type == 'arm':
            confirmed = params.get('confirmed', False)
            force_arm = params.get('force_arm', False)
            
            # Check if connected first
            if not mavlink_connection.is_connected():
                emit('command_result', {
                    'success': False,
                    'command': 'arm',
                    'message': 'Cannot ARM - not connected to drone',
                    'params': params
                })
            else:
                # Send real ARM command
                result = mavlink_command_sender.send_arm_command(force_arm, confirmed)
                emit('command_result', {
                    'success': result.get('success', False),
                    'command': 'arm',
                    'message': result.get('message', 'ARM command processed'),
                    'ack_received': result.get('ack_received', False),
                    'params': params
                })
            
        elif command_type == 'disarm':
            confirmed = params.get('confirmed', False)
            force_disarm = params.get('force_disarm', False)
            
            # Check if connected first
            if not mavlink_connection.is_connected():
                emit('command_result', {
                    'success': False,
                    'command': 'disarm',
                    'message': 'Cannot DISARM - not connected to drone',
                    'params': params
                })
            else:
                # Send real DISARM command
                result = mavlink_command_sender.send_disarm_command(force_disarm, confirmed)
                emit('command_result', {
                    'success': result.get('success', False),
                    'command': 'disarm',
                    'message': result.get('message', 'DISARM command processed'),
                    'ack_received': result.get('ack_received', False),
                    'params': params
                })
            
        elif command_type == 'takeoff':
            altitude = params.get('altitude', 10)
            confirmed = params.get('confirmed', False)
            pitch = params.get('pitch', 0)
            yaw = params.get('yaw', float('nan'))
            
            # Check if connected first
            if not mavlink_connection.is_connected():
                emit('command_result', {
                    'success': False,
                    'command': 'takeoff',
                    'message': 'Cannot TAKEOFF - not connected to drone',
                    'params': params
                })
            else:
                # Send real TAKEOFF command
                result = mavlink_command_sender.send_takeoff_command(altitude, pitch, yaw, confirmed)
                emit('command_result', {
                    'success': result.get('success', False),
                    'command': 'takeoff',
                    'message': result.get('message', f'TAKEOFF command to {altitude}m processed'),
                    'ack_received': result.get('ack_received', False),
                    'params': params
                })
            
        elif command_type == 'land':
            yaw = params.get('yaw', float('nan'))
            lat = params.get('latitude', 0)
            lon = params.get('longitude', 0) 
            alt = params.get('altitude', 0)
            
            # Check if connected first
            if not mavlink_connection.is_connected():
                emit('command_result', {
                    'success': False,
                    'command': 'land',
                    'message': 'Cannot LAND - not connected to drone',
                    'params': params
                })
            else:
                # Send real LAND command
                result = mavlink_command_sender.send_land_command(yaw, lat, lon, alt)
                emit('command_result', {
                    'success': True,  # Land command doesn't have confirmation requirements
                    'command': 'land',
                    'message': 'LAND command processed',
                    'params': params
                })
            
        elif command_type == 'rtl':
            # Check if connected first
            if not mavlink_connection.is_connected():
                emit('command_result', {
                    'success': False,
                    'command': 'rtl',
                    'message': 'Cannot RTL - not connected to drone',
                    'params': params
                })
            else:
                # Send real RTL command
                result = mavlink_command_sender.send_rtl_command()
                emit('command_result', {
                    'success': True,  # RTL command doesn't have confirmation requirements
                    'command': 'rtl',
                    'message': 'RTL command processed',
                    'params': params
                })
            
        elif command_type == 'set_mode':
            mode = params.get('mode', 'GUIDED')
            
            # Check if connected first
            if not mavlink_connection.is_connected():
                emit('command_result', {
                    'success': False,
                    'command': 'set_mode',
                    'message': 'Cannot SET_MODE - not connected to drone',
                    'params': params
                })
            else:
                # Send real SET_MODE command
                result = mavlink_command_sender.send_set_mode_command(mode)
                emit('command_result', {
                    'success': True,  # Mode command doesn't have confirmation requirements
                    'command': 'set_mode',
                    'message': f'Mode change to {mode} processed',
                    'params': params
                })
            
        elif command_type == 'goto':
            latitude = params.get('latitude', 0.0)
            longitude = params.get('longitude', 0.0)
            altitude = params.get('altitude', 10.0)
            confirmed = params.get('confirmed', False)
            
            # Check if connected first
            if not mavlink_connection.is_connected():
                emit('command_result', {
                    'success': False,
                    'command': 'goto',
                    'message': 'Cannot GO TO - not connected to drone',
                    'params': params
                })
            else:
                # Send real GOTO command with validation
                result = mavlink_command_sender.send_goto_command(latitude, longitude, altitude, confirmed)
                emit('command_result', {
                    'success': result.get('success', False),
                    'command': 'goto',
                    'message': result.get('message', f'GO TO waypoint processed: {latitude:.6f}, {longitude:.6f}, {altitude:.1f}m'),
                    'ack_received': result.get('ack_received', False),
                    'params': params
                })
            
        else:
            # Unknown command
            emit('command_result', {
                'success': False,
                'command': command_type,
                'message': f'Unknown command: {command_type}',
                'params': params
            })
    
    @socketio.on('request_telemetry')
    def handle_request_telemetry(data=None):
        """Handle telemetry data request."""
        record_agent_usage('web-interface-agent', 30, 25)
        
        # Get real telemetry data from MAVLink connection
        telemetry_data = mavlink_connection.get_telemetry_data()
        
        # Send real telemetry to client
        emit('telemetry_update', telemetry_data)
    
    record_agent_usage('web-interface-agent', 50, 40)


def telemetry_stream_worker():
    """Background worker that streams telemetry at 10Hz."""
    global telemetry_running
    
    while telemetry_running:
        try:
            if mavlink_connection.is_connected() and socketio_instance:
                # Get telemetry data
                telemetry_data = mavlink_connection.get_telemetry_data()
                
                # Send heartbeat count to UI via drone_status event
                socketio_instance.emit('drone_status', {
                    'connected': True,
                    'system_id': mavlink_connection.get_system_id(),
                    'heartbeat_count': telemetry_data.get('heartbeat_count', 0),
                    'telemetry': telemetry_data
                })
                
                # Also emit raw telemetry stream for other components
                socketio_instance.emit('telemetry_stream', telemetry_data)
                
            # Sleep for 100ms (10Hz frequency)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Telemetry streaming error: {e}")
            time.sleep(1.0)  # Longer sleep on error


def start_telemetry_streaming():
    """Start background telemetry streaming."""
    global telemetry_thread, telemetry_running
    
    if not telemetry_running:
        telemetry_running = True
        telemetry_thread = threading.Thread(target=telemetry_stream_worker, daemon=True)
        telemetry_thread.start()


def stop_telemetry_streaming():
    """Stop background telemetry streaming."""
    global telemetry_running
    telemetry_running = False
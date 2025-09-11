"""
WebGCS Flask Routes
Main HTTP routes for the web interface.
"""

from flask import Blueprint, render_template, jsonify, request
from flask import current_app as app
import logging

# Create blueprint for main routes
main_bp = Blueprint('main', __name__)
logger = logging.getLogger('webgcs')


@main_bp.route('/')
def index():
    """
    Main application page serving the WebGCS interface.
    
    Returns:
        Rendered HTML template for the main interface
    """
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return jsonify({'error': 'Failed to load interface'}), 500


@main_bp.route('/health')
def health_check():
    """
    Health check endpoint for deployment verification.
    
    Returns:
        JSON response with application status
    """
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'webgcs',
            'version': '1.0.0',
            'drone_endpoint': f"{app.config['DRONE_TCP_ADDRESS']}:{app.config['DRONE_TCP_PORT']}"
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@main_bp.route('/api/config')
def get_config():
    """
    Get client-safe configuration parameters.
    
    Returns:
        JSON response with configuration data
    """
    try:
        safe_config = {
            'heartbeat_timeout': app.config['HEARTBEAT_TIMEOUT'],
            'telemetry_update_interval': app.config['TELEMETRY_UPDATE_INTERVAL'],
            'command_ack_timeout': app.config['COMMAND_ACK_TIMEOUT'],
            'request_stream_rate_hz': app.config['REQUEST_STREAM_RATE_HZ']
        }
        return jsonify(safe_config)
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': 'Failed to get configuration'}), 500


@main_bp.route('/api/status')
def get_status():
    """
    Get current system status including drone connection.
    
    Returns:
        JSON response with system status
    """
    try:
        # Get status from MAVLink service
        mavlink_service = getattr(app, 'mavlink_service', None)
        
        if mavlink_service:
            status = mavlink_service.get_status()
            status_data = {
                'web_server': 'active',
                'mavlink_connection': 'connected' if status.get('mavlink_connected') else 'disconnected',
                'connection_state': status.get('connection_state', 'unknown'),
                'last_heartbeat': status.get('last_heartbeat'),
                'armed_status': status.get('armed_status', False),
                'flight_mode': status.get('flight_mode', 'UNKNOWN'),
                'drone_endpoint': status.get('drone_endpoint'),
                'pending_commands': status.get('pending_commands', 0),
                'service_threads': status.get('service_threads', {})
            }
        else:
            status_data = {
                'web_server': 'active',
                'mavlink_connection': 'service_unavailable',
                'last_heartbeat': None,
                'armed_status': False,
                'flight_mode': 'unknown'
            }
        
        return jsonify(status_data)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500


@main_bp.errorhandler(404)
def not_found(error):
    """
    Handle 404 errors.
    
    Args:
        error: The 404 error instance
        
    Returns:
        JSON error response
    """
    return jsonify({'error': 'Page not found'}), 404


@main_bp.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors.
    
    Args:
        error: The 500 error instance
        
    Returns:
        JSON error response
    """
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
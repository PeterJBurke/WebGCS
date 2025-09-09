"""
Flask Routes for WebGCS
Handles HTTP routes and page rendering

File size: Must stay under 150 lines per WebGCS PRD  
"""
import os
from flask import render_template, jsonify, request
from src.utils.token_tracker import record_agent_usage


def register_routes(app):
    """Register all HTTP routes for the WebGCS application."""
    
    @app.route('/')
    def index():
        """Main WebGCS interface page."""
        record_agent_usage('web-interface-agent', 25, 20)
        # Get drone connection settings from environment
        drone_host = os.environ.get('DRONE_TCP_ADDRESS', '192.168.193.235')
        drone_port = os.environ.get('DRONE_TCP_PORT', '5678')
        return render_template('index.html', 
                             title="WebGCS Drone Control System",
                             drone_host=drone_host,
                             drone_port=drone_port)
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        return jsonify({
            'status': 'healthy',
            'service': 'WebGCS',
            'version': '1.0.0'
        })
    
    @app.route('/api/status')
    def api_status():
        """API status endpoint."""
        return jsonify({
            'api_version': '1.0',
            'endpoints': [
                '/health',
                '/api/status',
                '/api/drone/status',
                '/api/drone/connect',
                '/api/drone/disconnect'
            ]
        })
    
    @app.route('/api/drone/status')
    def drone_status():
        """Get current drone connection status."""
        # This will be connected to actual MAVLink connection later
        return jsonify({
            'connected': False,
            'system_id': None,
            'component_id': None,
            'heartbeat_count': 0,
            'last_heartbeat': None
        })
    
    @app.route('/api/drone/connect', methods=['POST'])
    def drone_connect():
        """Connect to drone endpoint."""
        data = request.get_json() or {}
        host = data.get('host', '127.0.0.1')
        port = data.get('port', 5678)
        
        # This will be implemented with actual MAVLink connection
        record_agent_usage('web-interface-agent', 40, 30)
        
        return jsonify({
            'success': False,
            'message': f'Connection to {host}:{port} not yet implemented',
            'host': host,
            'port': port
        })
    
    @app.route('/api/drone/disconnect', methods=['POST'])
    def drone_disconnect():
        """Disconnect from drone endpoint."""
        record_agent_usage('web-interface-agent', 25, 20)
        
        return jsonify({
            'success': False,
            'message': 'Disconnect not yet implemented'
        })
    
    record_agent_usage('web-interface-agent', 45, 35)
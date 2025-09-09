"""
Flask Application Factory for WebGCS
Creates Flask app with SocketIO integration

File size: Must stay under 150 lines per WebGCS PRD
"""
import os
from flask import Flask, render_template
from flask_socketio import SocketIO
from src.web.routes import register_routes
from src.web.socketio_events import register_socketio_events
from src.utils.token_tracker import record_agent_usage


def create_app(debug=False, host='127.0.0.1', port=5001):
    """Create and configure Flask application with SocketIO."""
    
    # Create Flask application
    app = Flask(__name__, 
                template_folder='../../templates',
                static_folder='../../static')
    
    # Configure application
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'webgcs_development_key')
    app.config['DEBUG'] = debug
    app.config['HOST'] = host
    app.config['PORT'] = port
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", 
                       logger=debug, engineio_logger=debug)
    
    # Store SocketIO instance in app for access in other modules
    app.socketio = socketio
    
    # Register routes
    register_routes(app)
    
    # Register SocketIO event handlers
    register_socketio_events(socketio)
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error="Page not found"), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error="Internal server error"), 500
    
    record_agent_usage('web-interface-agent', 60, 45)
    
    return app


def run_app(app=None, debug=True, host='127.0.0.1', port=5001):
    """Run the WebGCS Flask application."""
    if app is None:
        app = create_app(debug=debug, host=host, port=port)
    
    # Run with SocketIO support
    app.socketio.run(app, debug=debug, host=host, port=port,
                    allow_unsafe_werkzeug=True)
    
    record_agent_usage('web-interface-agent', 30, 25)


if __name__ == "__main__":
    # Create and run app directly
    app = create_app(debug=True)
    run_app(app)
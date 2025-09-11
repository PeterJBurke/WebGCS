"""
WebGCS Flask Application Factory
Creates and configures the Flask-SocketIO application instance.
"""

import os
from pathlib import Path
from flask import Flask
from flask_socketio import SocketIO
from typing import Optional


def create_app(config: Optional[dict] = None) -> tuple[Flask, SocketIO]:
    """
    Create and configure Flask application with SocketIO support.
    
    Args:
        config: Optional configuration dictionary override
        
    Returns:
        tuple: (Flask app instance, SocketIO instance)
    """
    # Get project root directory (two levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    template_dir = project_root / 'templates'
    static_dir = project_root / 'static'
    
    app = Flask(__name__, 
                template_folder=str(template_dir),
                static_folder=str(static_dir))
    
    # Load configuration from environment
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'webgcs_development_key'),
        'WEB_SERVER_HOST': os.getenv('WEB_SERVER_HOST', 'localhost'),
        'WEB_SERVER_PORT': int(os.getenv('WEB_SERVER_PORT', 5002)),
        'DRONE_TCP_ADDRESS': os.getenv('DRONE_TCP_ADDRESS', '192.168.193.235'),
        'DRONE_TCP_PORT': int(os.getenv('DRONE_TCP_PORT', 5678)),
        'HEARTBEAT_TIMEOUT': int(os.getenv('HEARTBEAT_TIMEOUT', 30)),
        'REQUEST_STREAM_RATE_HZ': int(os.getenv('REQUEST_STREAM_RATE_HZ', 4)),
        'COMMAND_ACK_TIMEOUT': int(os.getenv('COMMAND_ACK_TIMEOUT', 10)),
        'TELEMETRY_UPDATE_INTERVAL': float(os.getenv('TELEMETRY_UPDATE_INTERVAL', 0.1))
    })
    
    # Override with provided config if any
    if config:
        app.config.update(config)
    
    # FIX: Enhanced SocketIO configuration for compatibility
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',   # Use eventlet mode for WebSocket compatibility
        logger=True,             # Enable logging for debugging
        engineio_logger=True,    # Enable EngineIO logging for debugging
        ping_timeout=60,         # Increased timeout for better stability
        ping_interval=25,        # Standard ping interval
        allow_upgrades=True,     # Allow protocol upgrades from polling to WebSocket
        transports=['polling', 'websocket']  # Explicit transport configuration
    )
    
    return app, socketio


def register_blueprints(app: Flask) -> None:
    """
    Register Flask blueprints for route organization.
    
    Args:
        app: Flask application instance
    """
    from .routes import main_bp
    app.register_blueprint(main_bp)


def configure_logging(app: Flask) -> None:
    """
    Configure application logging.
    
    Args:
        app: Flask application instance
    """
    import logging
    from src.utils.logger import setup_logger
    
    if not app.debug:
        setup_logger(
            name='webgcs',
            log_file='logs/webgcs.log',
            level=logging.INFO
        )


def initialize_app() -> tuple[Flask, SocketIO]:
    """
    Complete application initialization with all components.
    
    Returns:
        tuple: (Configured Flask app, Configured SocketIO instance)
    """
    app, socketio = create_app()
    
    # Register components
    register_blueprints(app)
    configure_logging(app)
    
    # Register SocketIO event handlers
    from .socketio_events import register_socketio_handlers
    register_socketio_handlers(socketio)
    
    # Initialize MAVLink service
    from src.mavlink.mavlink_service import MAVLinkService
    mavlink_service = MAVLinkService(
        host=app.config['DRONE_TCP_ADDRESS'],
        port=app.config['DRONE_TCP_PORT'],
        socketio_app=socketio
    )
    
    # Attach service to app for access in routes
    app.mavlink_service = mavlink_service
    
    return app, socketio
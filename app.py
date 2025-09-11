#!/usr/bin/env python3
"""
WebGCS Main Application Entry Point
Initializes and runs the Flask-SocketIO web application.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from src.web.app_factory import initialize_app
from src.utils.logger import get_webgcs_logger
from src.utils.token_tracker import track_agent_usage

# Initialize logger
logger = get_webgcs_logger()

def main():
    """Main application entry point."""
    try:
        # Track token usage for coordinator-agent
        track_agent_usage('coordinator-agent', 500, 300, 'Application startup')
        
        logger.info("Starting WebGCS application...")
        
        # Initialize Flask-SocketIO application
        app, socketio = initialize_app()
        
        # Start MAVLink service
        logger.info("Starting MAVLink service...")
        mavlink_service = getattr(app, 'mavlink_service', None)
        if mavlink_service:
            if mavlink_service.start():
                logger.info("MAVLink service started successfully")
            else:
                logger.warning("MAVLink service failed to start - continuing with web interface only")
        else:
            logger.warning("No MAVLink service found - web interface only")
        
        # Get configuration
        host = app.config.get('WEB_SERVER_HOST', 'localhost')
        port = app.config.get('WEB_SERVER_PORT', 5001)
        
        logger.info(f"WebGCS starting on {host}:{port}")
        logger.info(f"Drone endpoint: {app.config.get('DRONE_TCP_ADDRESS')}:{app.config.get('DRONE_TCP_PORT')}")
        
        try:
            # Start the web application
            socketio.run(
                app,
                host=host,
                port=port,
                debug=False,  # Set to False for production
                allow_unsafe_werkzeug=True  # For development only
            )
        finally:
            # Cleanup MAVLink service on shutdown
            if mavlink_service:
                logger.info("Stopping MAVLink service...")
                mavlink_service.stop()
                logger.info("MAVLink service stopped")
        
    except Exception as e:
        logger.error(f"Failed to start WebGCS: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
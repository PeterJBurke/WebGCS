"""
WebGCS Application Entry Point
Initializes and runs the Flask-SocketIO web application.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.web.app_factory import initialize_app
from src.utils.logger import setup_logger


def main():
    """Main application entry point."""
    # Setup logging
    setup_logger(
        name='webgcs',
        log_file='logs/webgcs.log',
        level='INFO'
    )
    
    # Initialize Flask-SocketIO application
    app, socketio = initialize_app()
    
    # Get configuration
    host = app.config['WEB_SERVER_HOST']
    port = app.config['WEB_SERVER_PORT']
    
    print(f"Starting WebGCS on http://{host}:{port}")
    print(f"Drone connection: {app.config['DRONE_TCP_ADDRESS']}:{app.config['DRONE_TCP_PORT']}")
    
    # Start the application
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\nShutting down WebGCS...")
    except Exception as e:
        print(f"Error starting WebGCS: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

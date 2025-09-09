#!/usr/bin/env python3
"""
WebGCS Application Entry Point
Starts the Flask-SocketIO web server for the ground control station
"""
import sys
import os
from dotenv import load_dotenv
from src.web.app_factory import create_app

# Load environment variables from .env file
load_dotenv()

def main():
    """Start the WebGCS web application."""
    
    print("🚁 WebGCS Ground Control Station")
    print("=" * 50)
    print(f"🌐 Web Interface: http://127.0.0.1:5002")
    print(f"🔗 Virtual Drone: 192.168.193.235:5678")
    print("=" * 50)
    print("📋 Features Available:")
    print("  ✅ MAVLink Connection Management")
    print("  ✅ Flight Controls (ARM/DISARM/TAKEOFF)")
    print("  ✅ Navigation & Go To Commands") 
    print("  ✅ Interactive Map with Drone Visualization")
    print("  ✅ Primary Flight Display (VFR HUD)")
    print("  ✅ Real-time Telemetry Streaming")
    print("=" * 50)
    print("🚀 Starting server...")
    
    # Create and run Flask app with SocketIO
    try:
        app = create_app(debug=True, host='127.0.0.1', port=5002)
        app.socketio.run(app, 
                        host='127.0.0.1', 
                        port=5002, 
                        debug=True,
                        allow_unsafe_werkzeug=True,
                        use_reloader=False)  # Disable reloader to prevent double startup
    except KeyboardInterrupt:
        print("\n🛑 WebGCS server stopped")
    except Exception as e:
        print(f"❌ Error starting WebGCS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time

# Create Flask app and SocketIO instance
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'desktop_drone_secret!'
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

# Simple drone state for testing
drone_state = {
    'connected': False,
    'armed': False,
    'mode': 'UNKNOWN',
    'lat': 0.0,
    'lon': 0.0,
    'alt_rel': 0.0
}

# Routes
@app.route('/')
def index():
    return render_template("index.html", version="v2.63-Desktop-TCP-Test")

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/health')
def health_check():
    print("HEALTH CHECK ENDPOINT HIT")
    return "OK", 200

# Simulate telemetry updates
def periodic_telemetry_update():
    """Periodically send telemetry updates to web clients."""
    update_count = 0
    
    while True:
        try:
            socketio.emit('telemetry_update', drone_state)
            update_count += 1
            time.sleep(1)
        except Exception as e:
            print(f"Error in telemetry update: {e}")
            time.sleep(1)

if __name__ == '__main__':
    print("Starting modified WebGCS server on http://0.0.0.0:5000")
    
    # Start telemetry update thread
    telemetry_update_thread = threading.Thread(target=periodic_telemetry_update, daemon=True)
    telemetry_update_thread.start()
    print("Telemetry update thread started")
    
    # Start the Flask-SocketIO server
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        print("Server finished (should not happen if running normally)")
    except Exception as e:
        print(f"Exception during socketio.run: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("socketio.run block finished")

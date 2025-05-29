from flask import Flask, render_template
from flask_socketio import SocketIO
import time

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'simple_test_key'
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

@app.route('/')
def index():
    return "WebGCS Simple Test Server"

@app.route('/health')
def health_check():
    print("HEALTH CHECK ENDPOINT HIT")
    return "OK", 200

if __name__ == '__main__':
    print("Starting simplified WebGCS server on http://0.0.0.0:5000")
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        print("Server finished (should not happen if running normally)")
    except Exception as e:
        print(f"Exception during socketio.run: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("socketio.run block finished")

"""
Simple Flask app to test the WebGCS interface
"""
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'test_key'

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting simple WebGCS test server on localhost:5002")
    socketio.run(app, host='localhost', port=5002, debug=False)
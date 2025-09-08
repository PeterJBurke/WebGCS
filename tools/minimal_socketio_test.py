#!/usr/bin/env python3
"""
Minimal Flask-SocketIO test to diagnose event handler issues
"""
from flask import Flask
from flask_socketio import SocketIO, emit

# Create minimal Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'

# Create SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return '<h1>Minimal SocketIO Test</h1>'

@socketio.on('connect')
def handle_connect():
    print("*** CONNECT EVENT RECEIVED ***")
    emit('test_response', {'message': 'Connected successfully'})

@socketio.on('test_event') 
def handle_test_event():
    print("*** TEST EVENT RECEIVED ***")
    emit('test_response', {'message': 'Test event received'})

@socketio.on('disconnect_drone')
def handle_disconnect_drone():
    print("*** DISCONNECT_DRONE EVENT RECEIVED ***")
    emit('test_response', {'message': 'Disconnect drone event received'})

if __name__ == '__main__':
    print("Starting minimal SocketIO test server on localhost:5002")
    socketio.run(app, host='localhost', port=5002, debug=False)
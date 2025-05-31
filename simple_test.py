#!/usr/bin/env python3
"""
Simple Flask test to verify web server functionality
"""
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import time

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = 'test_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template("index.html", version="v2.63-Test")

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': time.time(),
        'drone_connected': False,
        'drone_mode': 'TEST',
        'drone_armed': False
    })

if __name__ == '__main__':
    print("Starting simple test server on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False) 
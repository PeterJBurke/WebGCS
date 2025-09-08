#!/usr/bin/env python3
"""
Simple SocketIO connection test to verify events work
"""
import socketio
import time

# Create a Socket.IO client
sio = socketio.SimpleClient()

def test_socketio_connection():
    """Test basic SocketIO connection and events"""
    try:
        print("Connecting to SocketIO server...")
        sio.connect('http://localhost:5001')
        print("✅ Connected successfully!")
        
        print("Sending test_event...")
        sio.emit('test_event')
        print("✅ Test event sent")
        
        print("Waiting 3 seconds for server to process test event...")
        time.sleep(3)
        
        print("Sending disconnect_drone event...")
        sio.emit('disconnect_drone')
        print("✅ Disconnect drone event sent")
        
        print("Waiting 3 seconds for server to process disconnect event...")
        time.sleep(3)
        
        print("Disconnecting...")
        sio.disconnect()
        print("✅ Disconnected")
        
        return True
        
    except Exception as e:
        print(f"❌ SocketIO test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 SocketIO Connection Test")
    print("=" * 40)
    
    success = test_socketio_connection()
    exit(0 if success else 1)
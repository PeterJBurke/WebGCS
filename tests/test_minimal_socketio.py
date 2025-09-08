#!/usr/bin/env python3
"""
Test the minimal SocketIO server
"""
import socketio
import time

# Create a Socket.IO client
sio = socketio.SimpleClient()

def test_minimal_socketio():
    """Test minimal SocketIO server"""
    try:
        print("Connecting to minimal SocketIO server...")
        sio.connect('http://localhost:5002')
        print("✅ Connected successfully!")
        
        print("Sending test_event...")
        sio.emit('test_event')
        print("✅ Test event sent")
        
        print("Waiting 2 seconds...")
        time.sleep(2)
        
        print("Sending disconnect_drone event...")
        sio.emit('disconnect_drone')
        print("✅ Disconnect drone event sent")
        
        print("Waiting 2 seconds...")
        time.sleep(2)
        
        print("Disconnecting...")
        sio.disconnect()
        print("✅ Disconnected")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Minimal SocketIO Test")
    print("=" * 40)
    
    success = test_minimal_socketio()
    exit(0 if success else 1)
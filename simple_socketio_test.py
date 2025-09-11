#!/usr/bin/env python3
"""
Simple SocketIO Connection Test for WebGCS
Tests the eventlet fix for connect button popup issue
"""

import socketio
import time
import asyncio

async def test_socketio_connection():
    """Test SocketIO connection with detailed logging"""
    print("🔍 Testing SocketIO connection to WebGCS...")
    
    sio = socketio.AsyncClient(logger=True, engineio_logger=True)
    connected = False
    
    @sio.event
    async def connect():
        nonlocal connected
        connected = True
        print(f"✅ SocketIO Connected! Session ID: {sio.sid}")
        print(f"   Transport: {sio.transport()}")
    
    @sio.event
    async def connect_error(data):
        print(f"❌ SocketIO Connect Error: {data}")
    
    @sio.event
    async def disconnect():
        print("🔌 SocketIO Disconnected")
    
    try:
        start_time = time.time()
        print("Attempting to connect...")
        
        await sio.connect('http://localhost:5002', wait_timeout=10)
        
        connection_time = time.time() - start_time
        print(f"Connection attempt completed in {connection_time:.2f} seconds")
        
        if connected:
            print("✅ SUCCESS: SocketIO connection established!")
            
            # Test sending an event
            print("🔍 Testing event emission...")
            await sio.emit('test_event', {'data': 'test'})
            print("✅ Event sent successfully")
            
            # Wait a bit
            await asyncio.sleep(1)
            
            # Disconnect
            await sio.disconnect()
            print("✅ Disconnected cleanly")
            
            return True
        else:
            print("❌ FAILED: SocketIO connection not established")
            return False
            
    except Exception as e:
        print(f"❌ Exception during connection: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_socketio_connection())
    if result:
        print("\n🎉 SocketIO eventlet fix is working!")
    else:
        print("\n⚠️  SocketIO connection issues detected")
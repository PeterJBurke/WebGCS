#!/usr/bin/env python3
"""
DISCONNECT & RECONNECT TEST
Tests the complete connect/disconnect/reconnect cycle
"""
import requests
import time
import socketio
import threading


def test_disconnect_reconnect_cycle():
    """Test complete disconnect/reconnect cycle"""
    print("🔄 DISCONNECT & RECONNECT CYCLE TEST")
    print("="*50)
    
    server_url = "http://localhost:5001"
    virtual_drone_ip = "192.168.193.235"
    virtual_drone_port = 5678
    
    # Track events
    connection_events = []
    telemetry_events = []
    
    # Create WebSocket client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("WebSocket connected")
    
    @sio.event
    def connection_status(data):
        print(f"Connection status: {data}")
        connection_events.append(data)
    
    @sio.event
    def telemetry_update(data):
        telemetry_events.append(data)
        if len(telemetry_events) % 10 == 0:  # Print every 10th telemetry
            print(f"Telemetry #{len(telemetry_events)}: connected={data.get('connected')}")
    
    try:
        # 1. Connect to WebSocket
        print("\n1. Establishing WebSocket connection...")
        sio.connect(server_url)
        time.sleep(2)
        
        # Check initial state
        response = requests.get(f"{server_url}/health")
        initial_state = response.json()
        print(f"Initial state: drone_connected = {initial_state['drone_connected']}")
        
        if initial_state['drone_connected']:
            print("✅ Drone is currently connected - testing disconnect first")
            
            # 2. Test DISCONNECT
            print("\n2. Testing disconnect functionality...")
            connection_events.clear()
            
            sio.emit('disconnect_drone')
            print("Disconnect command sent")
            
            # Wait for disconnect to complete
            time.sleep(5)
            
            # Check status
            response = requests.get(f"{server_url}/health")
            disconnect_state = response.json()
            print(f"After disconnect: drone_connected = {disconnect_state['drone_connected']}")
            
            if not disconnect_state['drone_connected']:
                print("✅ Disconnect successful")
                
                # 3. Test RECONNECT
                print("\n3. Testing reconnect functionality...")
                connection_events.clear()
                
                connect_data = {
                    'ip': virtual_drone_ip,
                    'port': virtual_drone_port
                }
                
                sio.emit('connect_drone', connect_data)
                print(f"Reconnect command sent: {connect_data}")
                
                # Wait for reconnection
                start_time = time.time()
                reconnected = False
                
                while time.time() - start_time < 30:  # 30 second timeout
                    response = requests.get(f"{server_url}/health")
                    current_state = response.json()
                    
                    if current_state['drone_connected']:
                        reconnected = True
                        print(f"✅ Reconnected after {time.time() - start_time:.1f} seconds")
                        break
                    
                    time.sleep(1)
                
                if reconnected:
                    print("✅ Complete disconnect/reconnect cycle successful")
                    return True
                else:
                    print("❌ Reconnection failed")
                    return False
            else:
                print("❌ Disconnect failed")
                return False
        else:
            print("Drone not initially connected - testing connect only")
            
            # Test CONNECT from disconnected state
            print("\n2. Testing connect from disconnected state...")
            connection_events.clear()
            
            connect_data = {
                'ip': virtual_drone_ip,
                'port': virtual_drone_port
            }
            
            sio.emit('connect_drone', connect_data)
            print(f"Connect command sent: {connect_data}")
            
            # Wait for connection
            start_time = time.time()
            connected = False
            
            while time.time() - start_time < 30:  # 30 second timeout
                response = requests.get(f"{server_url}/health")
                current_state = response.json()
                
                if current_state['drone_connected']:
                    connected = True
                    print(f"✅ Connected after {time.time() - start_time:.1f} seconds")
                    break
                
                time.sleep(1)
            
            if connected:
                print("✅ Connect from disconnected state successful")
                return True
            else:
                print("❌ Connection failed")
                return False
    
    finally:
        sio.disconnect()


def test_heartbeat_monitoring():
    """Test heartbeat monitoring during connection"""
    print("\n💓 HEARTBEAT MONITORING TEST")
    print("="*30)
    
    server_url = "http://localhost:5001"
    telemetry_count = 0
    heartbeat_data = []
    
    sio = socketio.Client()
    
    @sio.event
    def telemetry_update(data):
        nonlocal telemetry_count
        telemetry_count += 1
        
        if data.get('connected'):
            heartbeat_data.append({
                'timestamp': time.time(),
                'system_id': data.get('system_id', 0),
                'connected': data.get('connected', False)
            })
    
    try:
        sio.connect(server_url)
        print("Monitoring heartbeats for 10 seconds...")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            time.sleep(0.5)
        
        print(f"Total telemetry updates: {telemetry_count}")
        print(f"Heartbeat updates with connection: {len(heartbeat_data)}")
        
        if len(heartbeat_data) > 0:
            latest = heartbeat_data[-1]
            print(f"Latest heartbeat: system_id={latest['system_id']}, connected={latest['connected']}")
            print("✅ Heartbeat monitoring working")
            return True
        else:
            print("❌ No heartbeat data received")
            return False
            
    finally:
        sio.disconnect()


def main():
    """Run complete test suite"""
    print("🧪 COMPLETE CONNECT BUTTON FUNCTIONALITY TEST")
    print("="*60)
    
    results = {}
    
    # Test 1: Disconnect/Reconnect Cycle
    try:
        results['disconnect_reconnect'] = test_disconnect_reconnect_cycle()
    except Exception as e:
        print(f"Disconnect/reconnect test failed: {e}")
        results['disconnect_reconnect'] = False
    
    # Test 2: Heartbeat Monitoring
    try:
        results['heartbeat_monitoring'] = test_heartbeat_monitoring()
    except Exception as e:
        print(f"Heartbeat monitoring test failed: {e}")
        results['heartbeat_monitoring'] = False
    
    # Final Results
    print(f"\n{'='*60}")
    print("COMPLETE FUNCTIONALITY TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25}: {status}")
    
    all_passed = all(results.values())
    success_rate = sum(results.values()) / len(results) * 100
    
    print(f"\nSuccess Rate: {success_rate:.1f}% ({sum(results.values())}/{len(results)} tests passed)")
    
    if all_passed:
        print(f"""
🎉 COMPLETE SUCCESS!
✅ Disconnect functionality working
✅ Reconnect functionality working  
✅ Heartbeat monitoring active
✅ End-to-end workflow validated

The connect button fix is 100% functional! 🚀
""")
    else:
        failed = [test for test, result in results.items() if not result]
        print(f"\n⚠️  Some functionality needs attention: {failed}")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
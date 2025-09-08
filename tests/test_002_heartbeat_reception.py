"""
TEST-002: Heartbeat Reception Test
Tests receiving and processing HEARTBEAT messages from virtual drone

This test MUST FAIL initially (Red phase) - mavlink_message_processor does not exist yet
"""
import time
import threading
import pytest


def test_heartbeat_reception():
    """Test receiving and processing heartbeat messages"""
    
    from mavlink_connection_manager import connect_mavlink, get_mavlink_connection, disconnect_mavlink
    # Import will fail initially - this is expected (RED PHASE)
    from mavlink_message_processor import process_heartbeat
    
    # Clean up any existing connection
    disconnect_mavlink()
    
    # Test setup
    drone_state = {
        'connected': False, 
        'system_id': 0, 
        'component_id': 0, 
        'armed': False,
        'mode': 'UNKNOWN'
    }
    drone_state_lock = threading.Lock()
    heartbeat_received = threading.Event()
    
    def mock_log_callback(command, params=None, details=None):
        print(f"LOG: {command} - {details}")
    
    def mock_socketio_instance():
        pass
    
    # Connect to virtual drone
    connection_string = "tcp:192.168.193.235:5678"
    connect_mavlink(drone_state, drone_state_lock, connection_string)
    connection = get_mavlink_connection()
    
    assert connection is not None, "Connection must be established first"
    
    print("Waiting for heartbeat messages...")
    start_time = time.time()
    
    # Listen for heartbeat messages
    while time.time() - start_time < 15:  # 15 second timeout
        try:
            msg = connection.recv_match(type='HEARTBEAT', timeout=1.0)
            if msg:
                print(f"Received HEARTBEAT from system {msg.get_srcSystem()}")
                
                # Process heartbeat using message processor
                state_changed = process_heartbeat(
                    msg, 
                    drone_state, 
                    drone_state_lock, 
                    connection,
                    mock_log_callback,
                    mock_socketio_instance
                )
                
                if state_changed:
                    heartbeat_received.set()
                    break
                    
        except Exception as e:
            print(f"Error receiving heartbeat: {e}")
        
        time.sleep(0.1)
    
    # PASS CRITERIA (ALL must be true):
    assert heartbeat_received.is_set(), "Must receive and process heartbeat within 15 seconds"
    
    with drone_state_lock:
        assert drone_state['connected'] == True, f"drone_state.connected is {drone_state['connected']} (must be True)"
        assert drone_state['system_id'] > 0, f"System ID is {drone_state['system_id']} (must be >0)"
        assert drone_state['component_id'] > 0, f"Component ID is {drone_state['component_id']} (must be >0)"
        assert drone_state['mode'] != 'UNKNOWN', f"Flight mode is {drone_state['mode']} (must not be UNKNOWN)"
    
    elapsed_time = time.time() - start_time
    print(f"✓ Heartbeat processed successfully in {elapsed_time:.2f}s")
    print(f"✓ System ID: {drone_state['system_id']}")
    print(f"✓ Component ID: {drone_state['component_id']}")
    print(f"✓ Flight Mode: {drone_state['mode']}")
    print(f"✓ Armed Status: {drone_state['armed']}")


if __name__ == "__main__":
    test_heartbeat_reception()
    print("TEST-002 PASSED: Heartbeat reception successful")
"""
TEST-003: Message Processing Test  
Tests processing of GLOBAL_POSITION_INT messages

This test should PASS since mavlink_message_processor.py already exists with this functionality
"""
import time
import threading
import pytest


def test_global_position_processing():
    """Test processing GLOBAL_POSITION_INT messages"""
    
    from mavlink_connection_manager import connect_mavlink, get_mavlink_connection, disconnect_mavlink
    from mavlink_message_processor import process_global_position_int
    
    # Clean up any existing connection
    disconnect_mavlink()
    
    # Test setup
    drone_state = {
        'connected': False,
        'lat': 0.0, 
        'lon': 0.0, 
        'alt_rel': 0.0,
        'alt_abs': 0.0,
        'heading': 0.0,
        'vx': 0.0, 'vy': 0.0, 'vz': 0.0
    }
    drone_state_lock = threading.Lock()
    position_updated = threading.Event()
    
    def mock_log_callback(command, params=None, details=None):
        print(f"LOG: {command} - {details}")
    
    def mock_socketio_instance():
        pass
    
    # Connect to virtual drone
    connection_string = "tcp:192.168.193.235:5678"
    connect_mavlink(drone_state, drone_state_lock, connection_string)
    connection = get_mavlink_connection()
    
    assert connection is not None, "Connection must be established first"
    
    print("Waiting for GLOBAL_POSITION_INT messages...")
    start_time = time.time()
    
    # Monitor for position updates
    while time.time() - start_time < 30:  # 30 second timeout
        try:
            msg = connection.recv_match(type='GLOBAL_POSITION_INT', timeout=1.0)
            if msg:
                print(f"Received GLOBAL_POSITION_INT: lat={msg.lat/1e7:.6f}, lon={msg.lon/1e7:.6f}")
                
                # Process position message
                state_changed = process_global_position_int(
                    msg,
                    drone_state,
                    drone_state_lock, 
                    connection,
                    mock_log_callback,
                    mock_socketio_instance
                )
                
                if state_changed:
                    with drone_state_lock:
                        if drone_state['lat'] != 0.0 or drone_state['lon'] != 0.0:
                            position_updated.set()
                            break
                            
        except Exception as e:
            print(f"Error receiving position: {e}")
        
        time.sleep(0.1)
    
    # PASS CRITERIA (ALL must be true):
    assert position_updated.is_set(), "Position data must be received and processed within 30 seconds"
    
    with drone_state_lock:
        assert -90 <= drone_state['lat'] <= 90, f"Latitude {drone_state['lat']} outside valid range"
        assert -180 <= drone_state['lon'] <= 180, f"Longitude {drone_state['lon']} outside valid range"
        assert drone_state['alt_rel'] is not None, "Relative altitude must be populated"
        assert drone_state['alt_abs'] is not None, "Absolute altitude must be populated"
    
    elapsed_time = time.time() - start_time
    print(f"✓ Position data processed in {elapsed_time:.2f}s")
    print(f"✓ Latitude: {drone_state['lat']:.6f}")
    print(f"✓ Longitude: {drone_state['lon']:.6f}")
    print(f"✓ Altitude (rel): {drone_state['alt_rel']:.1f}m")
    print(f"✓ Altitude (abs): {drone_state['alt_abs']:.1f}m")
    print(f"✓ Heading: {drone_state['heading']:.1f}°")


if __name__ == "__main__":
    test_global_position_processing()
    print("TEST-003 PASSED: Position message processing successful")
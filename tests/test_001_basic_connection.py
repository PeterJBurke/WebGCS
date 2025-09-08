"""
TEST-001: Basic MAVLink Connection Test
Tests connection to virtual drone at 192.168.193.235:5678

This test MUST FAIL initially (Red phase) - mavlink_connection_manager does not exist yet
"""
import time
import threading
import pytest


def test_mavlink_basic_connection():
    """Test basic MAVLink connection to virtual drone"""
    
    # Import will fail initially - this is expected (RED PHASE)
    from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    
    # Test setup
    drone_state = {'connected': False}
    drone_state_lock = threading.Lock()
    connection_string = "tcp:192.168.193.235:5678"
    
    print(f"Attempting connection to {connection_string}")
    
    # Execute connection
    start_time = time.time()
    connect_mavlink(drone_state, drone_state_lock, connection_string)
    connection = get_mavlink_connection()
    connection_time = time.time() - start_time
    
    # PASS CRITERIA (ALL must be true):
    assert connection is not None, "Connection object must not be None"
    assert connection_time < 5.0, f"Connection took {connection_time:.2f}s (>5s limit)"
    assert hasattr(connection, 'target_system'), "Connection must have target_system attribute"
    assert connection.target_system > 0, f"Target system ID is {connection.target_system} (must be >0)"
    
    print(f"✓ Connection successful in {connection_time:.2f}s")
    print(f"✓ Target System ID: {connection.target_system}")
    
    # FAIL CRITERIA (ANY causes failure):
    # - Connection timeout after 5 seconds
    # - Connection object is None
    # - No target_system attribute
    # - target_system is 0 or negative
    # - Exception during connection process


if __name__ == "__main__":
    test_mavlink_basic_connection()
    print("TEST-001 PASSED: Basic connection successful")
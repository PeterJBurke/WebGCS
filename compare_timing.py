#!/usr/bin/env python3
"""
Compare timing between direct heartbeat reception vs app.py approach
"""

import time
import threading
from pymavlink import mavutil
from config import MAVLINK_CONNECTION_STRING

def test_direct_heartbeat():
    """Test direct heartbeat reception like testheartbeatFIXED.py"""
    print("=== TESTING DIRECT HEARTBEAT APPROACH ===")
    
    connection = mavutil.mavlink_connection(MAVLINK_CONNECTION_STRING)
    connection.wait_heartbeat()
    
    last_mode = None
    heartbeat_count = 0
    
    while heartbeat_count < 10:  # Test 10 heartbeats
        start_time = time.time()
        msg = connection.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
        receive_time = time.time()
        
        if msg:
            heartbeat_count += 1
            current_mode = msg.custom_mode
            
            if last_mode != current_mode:
                print(f"[DIRECT] MODE CHANGE #{heartbeat_count}: {last_mode} -> {current_mode} in {(receive_time - start_time)*1000:.2f}ms")
                last_mode = current_mode
            else:
                print(f"[DIRECT] Heartbeat #{heartbeat_count}: Mode {current_mode} in {(receive_time - start_time)*1000:.2f}ms")
    
    connection.close()
    print("=== DIRECT TEST COMPLETE ===\n")

def test_app_approach():
    """Test app.py approach with all messages"""
    print("=== TESTING APP.PY APPROACH (with improvements) ===")
    
    connection = mavutil.mavlink_connection(
        MAVLINK_CONNECTION_STRING,
        autoreconnect=True,
        source_system=255,
        source_component=0
    )
    connection.wait_heartbeat()
    
    last_mode = None
    heartbeat_count = 0
    other_messages = 0
    
    while heartbeat_count < 10:  # Test 10 heartbeats
        start_time = time.time()
        msg = connection.recv_match(blocking=False, timeout=0.01)  # Using improved timeout
        receive_time = time.time()
        
        if msg:
            msg_type = msg.get_type()
            
            if msg_type == 'HEARTBEAT':
                heartbeat_count += 1
                current_mode = msg.custom_mode
                
                if last_mode != current_mode:
                    print(f"[APP] MODE CHANGE #{heartbeat_count}: {last_mode} -> {current_mode} in {(receive_time - start_time)*1000:.2f}ms (other msgs: {other_messages})")
                    last_mode = current_mode
                    other_messages = 0  # Reset counter
                else:
                    print(f"[APP] Heartbeat #{heartbeat_count}: Mode {current_mode} in {(receive_time - start_time)*1000:.2f}ms (other msgs: {other_messages})")
                    other_messages = 0  # Reset counter
            else:
                other_messages += 1
        else:
            time.sleep(0.01)  # Brief sleep like in improved app.py
    
    connection.close()
    print("=== APP TEST COMPLETE ===\n")

if __name__ == "__main__":
    print("Comparing heartbeat timing approaches...\n")
    
    # Test direct approach first
    test_direct_heartbeat()
    
    # Wait a moment
    time.sleep(2)
    
    # Test app approach
    test_app_approach()
    
    print("Comparison complete. The app.py approach should now be much faster!") 
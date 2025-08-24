#!/usr/bin/env python3
"""
Test heartbeat processing timing specifically
"""

import time
import threading
from pymavlink import mavutil
from config import MAVLINK_CONNECTION_STRING, AP_CUSTOM_MODES

def measure_heartbeat_timing():
    """Measure heartbeat reception and processing time"""
    print("=== HEARTBEAT TIMING TEST ===")
    print(f"Connecting to: {MAVLINK_CONNECTION_STRING}")
    
    # Create connection
    connection = mavutil.mavlink_connection(
        MAVLINK_CONNECTION_STRING,
        autoreconnect=True,
        source_system=255,
        source_component=0
    )
    
    print("Waiting for initial heartbeat...")
    connection.wait_heartbeat()
    print(f"Connected to system {connection.target_system}")
    
    heartbeat_count = 0
    last_mode = None
    total_times = []
    processing_times = []
    
    print("\nMeasuring heartbeat processing times...")
    print("Format: [Count] Mode | Reception: X.XXms | Processing: X.XXms | Total: X.XXms")
    print("-" * 80)
    
    try:
        while heartbeat_count < 20:  # Test 20 heartbeats
            # Measure reception time
            start_time = time.time()
            msg = connection.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
            reception_time = time.time()
            
            if msg:
                # Measure processing time
                process_start = time.time()
                
                # Simulate the processing that happens in app.py
                heartbeat_count += 1
                current_mode = msg.custom_mode
                
                # Convert to mode name (like in process_heartbeat)
                mode_name = "UNKNOWN"
                for name, mode_id in AP_CUSTOM_MODES.items():
                    if mode_id == current_mode:
                        mode_name = name
                        break
                
                # Check armed status
                armed = (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0
                armed_str = "ARMED" if armed else "DISARMED"
                
                # Simulate some state updates
                system_status = msg.system_status
                autopilot = msg.autopilot
                vehicle_type = msg.type
                
                process_end = time.time()
                
                # Calculate timings
                reception_ms = (reception_time - start_time) * 1000
                processing_ms = (process_end - process_start) * 1000
                total_ms = (process_end - start_time) * 1000
                
                total_times.append(total_ms)
                processing_times.append(processing_ms)
                
                # Print timing info
                mode_change_indicator = "***" if last_mode != current_mode else "   "
                print(f"{mode_change_indicator}[{heartbeat_count:3d}] {mode_name:12s} | "
                      f"Reception: {reception_ms:6.2f}ms | "
                      f"Processing: {processing_ms:6.2f}ms | "
                      f"Total: {total_ms:6.2f}ms")
                
                if last_mode != current_mode:
                    print(f"    MODE CHANGE: {last_mode} -> {current_mode} ({mode_name})")
                    last_mode = current_mode
            else:
                print("Timeout waiting for heartbeat")
                
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    connection.close()
    
    # Print statistics
    if total_times:
        avg_total = sum(total_times) / len(total_times)
        max_total = max(total_times)
        min_total = min(total_times)
        
        avg_processing = sum(processing_times) / len(processing_times)
        max_processing = max(processing_times)
        min_processing = min(processing_times)
        
        print("\n" + "=" * 80)
        print("TIMING STATISTICS:")
        print(f"Total heartbeats tested: {len(total_times)}")
        print(f"Average total time: {avg_total:.2f}ms")
        print(f"Min/Max total time: {min_total:.2f}ms / {max_total:.2f}ms")
        print(f"Average processing time: {avg_processing:.2f}ms")
        print(f"Min/Max processing time: {min_processing:.2f}ms / {max_processing:.2f}ms")
        
        if max_total > 10:
            print(f"WARNING: Some heartbeats took over 10ms to process!")
        if avg_total > 5:
            print(f"WARNING: Average processing time is high ({avg_total:.2f}ms)")
        else:
            print("Processing times look good!")
    
    print("=" * 80)

if __name__ == "__main__":
    measure_heartbeat_timing() 
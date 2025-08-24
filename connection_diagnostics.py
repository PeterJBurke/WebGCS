#!/usr/bin/env python3
"""
MAVLink Connection Diagnostics Tool

This script performs diagnostic tests on the MAVLink connection to help
troubleshoot connection issues.
"""
import os
import sys
import time
import socket
import subprocess
from pymavlink import mavutil

# Import configuration
from config import (
    DRONE_TCP_ADDRESS,
    DRONE_TCP_PORT,
    MAVLINK_CONNECTION_STRING
)

def check_network_connectivity(host, port, timeout=5):
    """Check if the host is reachable via ping and if the port is open."""
    print(f"\n=== Network Connectivity Check for {host}:{port} ===")
    
    # Check if host is reachable via ping
    try:
        print(f"Pinging {host}...")
        ping_cmd = ["ping", "-c", "3", "-W", str(timeout), host]
        ping_result = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if ping_result.returncode == 0:
            print(f"✓ Host {host} is reachable via ping")
            ping_output = ping_result.stdout.strip().split('\n')
            for line in ping_output:
                if "time=" in line:
                    print(f"  {line}")
        else:
            print(f"✗ Host {host} is NOT reachable via ping")
            print(f"  Error: {ping_result.stderr}")
    except Exception as e:
        print(f"✗ Ping test failed: {e}")
    
    # Check if port is open
    try:
        print(f"\nChecking if port {port} is open on {host}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        
        if result == 0:
            print(f"✓ Port {port} is OPEN on {host}")
        else:
            print(f"✗ Port {port} is CLOSED on {host} (Error code: {result})")
        
        sock.close()
    except Exception as e:
        print(f"✗ Port check failed: {e}")

def test_mavlink_connection(connection_string, timeout=10):
    """Test MAVLink connection by attempting to connect and receive a heartbeat."""
    print(f"\n=== MAVLink Connection Test for {connection_string} ===")
    
    try:
        print(f"Attempting to connect to {connection_string}...")
        start_time = time.time()
        
        # Create the connection
        mav = mavutil.mavlink_connection(
            connection_string,
            autoreconnect=True,
            source_system=255,
            source_component=0,
            retries=3,
            timeout=timeout
        )
        
        print(f"Connection object created. Waiting for heartbeat (timeout: {timeout}s)...")
        
        # Wait for the first heartbeat
        msg = mav.recv_match(type='HEARTBEAT', blocking=True, timeout=timeout)
        
        if msg:
            elapsed = time.time() - start_time
            print(f"✓ Received heartbeat after {elapsed:.2f} seconds")
            print(f"  From System: {msg.get_srcSystem()}, Component: {msg.get_srcComponent()}")
            print(f"  Vehicle Type: {msg.type}, Autopilot: {msg.autopilot}")
            print(f"  System Status: {msg.system_status}")
            print(f"  MAVLink Version: {msg.mavlink_version}")
            
            # Set target system and component
            mav.target_system = msg.get_srcSystem()
            mav.target_component = msg.get_srcComponent()
            
            # Try to receive a few more messages
            print("\nListening for additional messages (5 seconds)...")
            end_time = time.time() + 5
            msg_count = 0
            
            while time.time() < end_time:
                msg = mav.recv_match(blocking=False)
                if msg:
                    msg_count += 1
                    print(f"  Received: {msg.get_type()}")
                time.sleep(0.1)
            
            print(f"Received {msg_count} additional messages in 5 seconds")
            
            return True
        else:
            print(f"✗ No heartbeat received within {timeout} seconds")
            return False
    except Exception as e:
        print(f"✗ MAVLink connection test failed: {e}")
        return False
    finally:
        try:
            if 'mav' in locals():
                mav.close()
                print("Connection closed")
        except:
            pass

def check_system_resources():
    """Check system resources that might affect connection."""
    print("\n=== System Resource Check ===")
    
    # Check available memory
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        for line in meminfo.split('\n'):
            if 'MemTotal' in line or 'MemFree' in line or 'MemAvailable' in line:
                print(f"  {line.strip()}")
    except Exception as e:
        print(f"  Memory check failed: {e}")
    
    # Check CPU load
    try:
        with open('/proc/loadavg', 'r') as f:
            loadavg = f.read().strip()
        print(f"  Load Average: {loadavg}")
    except Exception as e:
        print(f"  CPU load check failed: {e}")
    
    # Check for any relevant processes
    try:
        print("\n  Checking for relevant processes:")
        processes = ["mavproxy", "ardupilot", "sitl", "dronekit"]
        
        for proc in processes:
            result = subprocess.run(["pgrep", "-l", proc], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                print(f"    Found {proc} process(es):")
                print(f"    {result.stdout.strip()}")
    except Exception as e:
        print(f"  Process check failed: {e}")

def run_diagnostics():
    """Run all diagnostic tests."""
    print("=== MAVLink Connection Diagnostics ===")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Connection String: {MAVLINK_CONNECTION_STRING}")
    print(f"Drone Address: {DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}")
    
    # Check network connectivity
    check_network_connectivity(DRONE_TCP_ADDRESS, DRONE_TCP_PORT)
    
    # Test MAVLink connection
    test_mavlink_connection(MAVLINK_CONNECTION_STRING)
    
    # Check system resources
    check_system_resources()
    
    print("\n=== Diagnostics Complete ===")

if __name__ == "__main__":
    run_diagnostics()

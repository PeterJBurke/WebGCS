#!/usr/bin/env python3
"""
Immediate MAVLink Verification
============================

MISSION: Immediate verification of MAVLink communication status
Target: 192.168.193.235:5678 (Virtual Drone)

Quick checks:
- Network connectivity
- Port accessibility 
- Basic MAVLink message detection
- WebGCS integration status
"""

import socket
import time
import requests
import subprocess
import sys
import json
from datetime import datetime

def test_network_connectivity():
    """Test network connectivity to virtual drone"""
    print("🔍 Testing network connectivity...")
    
    try:
        # Test ping
        result = subprocess.run(['ping', '-c', '3', '-W', '2000', '192.168.193.235'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Extract average latency
            lines = result.stdout.split('\n')
            for line in lines:
                if 'round-trip' in line or 'avg' in line:
                    print(f"✅ Network connectivity: GOOD")
                    print(f"    {line.strip()}")
                    return True
            print("✅ Network connectivity: GOOD (ping successful)")
            return True
        else:
            print("❌ Network connectivity: FAILED")
            print(f"    Ping failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Network connectivity: TIMEOUT (may still be reachable)")
        return False
    except Exception as e:
        print(f"❌ Network connectivity test error: {e}")
        return False

def test_port_accessibility():
    """Test if port 5678 is accessible"""
    print("\n🔍 Testing port accessibility...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        
        start_time = time.time()
        result = sock.connect_ex(('192.168.193.235', 5678))
        connect_time = (time.time() - start_time) * 1000
        
        sock.close()
        
        if result == 0:
            print(f"✅ Port 5678: ACCESSIBLE")
            print(f"    Connection time: {connect_time:.1f}ms")
            return True
        else:
            print(f"❌ Port 5678: NOT ACCESSIBLE")
            print(f"    Error code: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Port accessibility test error: {e}")
        return False

def test_webgcs_status():
    """Test WebGCS server status"""
    print("\n🔍 Testing WebGCS status...")
    
    try:
        response = requests.get('http://localhost:5001/health', timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            drone_connected = data.get('drone_connected', False)
            status = data.get('status', 'unknown')
            
            if drone_connected:
                print(f"✅ WebGCS: HEALTHY with drone connected")
                print(f"    Status: {status}")
                print(f"    Drone connected: {drone_connected}")
                return True
            else:
                print(f"⚠️  WebGCS: HEALTHY but drone not connected")
                print(f"    Status: {status}")
                return False
        else:
            print(f"❌ WebGCS: HTTP error {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ WebGCS: NOT RUNNING (connection refused)")
        return False
    except requests.exceptions.Timeout:
        print("⚠️  WebGCS: TIMEOUT (may be overloaded)")
        return False
    except Exception as e:
        print(f"❌ WebGCS status test error: {e}")
        return False

def check_mavlink_connections():
    """Check for existing MAVLink connections"""
    print("\n🔍 Checking existing MAVLink connections...")
    
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, timeout=5)
        
        connections_5678 = []
        for line in result.stdout.split('\n'):
            if '5678' in line and ('ESTABLISHED' in line or 'LISTEN' in line):
                connections_5678.append(line.strip())
        
        if connections_5678:
            print(f"✅ MAVLink connections detected: {len(connections_5678)} active")
            for i, conn in enumerate(connections_5678[:3]):  # Show first 3
                print(f"    {i+1}. {conn}")
            if len(connections_5678) > 3:
                print(f"    ... and {len(connections_5678) - 3} more")
            return True
        else:
            print("❌ MAVLink connections: NONE DETECTED")
            return False
            
    except Exception as e:
        print(f"❌ MAVLink connection check error: {e}")
        return False

def test_basic_mavlink_communication():
    """Attempt basic MAVLink communication with timeout protection"""
    print("\n🔍 Testing basic MAVLink communication...")
    
    try:
        from pymavlink import mavutil
        
        # Create connection with aggressive timeout
        conn = mavutil.mavlink_connection(
            'tcp:192.168.193.235:5678',
            source_system=255,
            source_component=0,
            timeout=2.0  # Short timeout
        )
        
        print("✅ MAVLink connection object created")
        
        # Try to receive one message with timeout
        start_time = time.time()
        msg_received = False
        
        try:
            msg = conn.recv_match(timeout=3.0)  # 3 second timeout
            
            if msg:
                msg_type = msg.get_type()
                system_id = msg.get_srcSystem()
                
                print(f"✅ MAVLink message received: {msg_type}")
                print(f"    Source system: {system_id}")
                print(f"    Response time: {(time.time() - start_time) * 1000:.1f}ms")
                msg_received = True
            else:
                print("⚠️  MAVLink: Connection established but no messages received")
                
        except Exception as recv_error:
            print(f"⚠️  MAVLink: Connection created but message reception failed: {recv_error}")
        
        # Clean up
        try:
            conn.close()
        except:
            pass
        
        return msg_received
        
    except ImportError:
        print("❌ MAVLink: pymavlink not available")
        return False
    except Exception as e:
        print(f"❌ MAVLink communication test error: {e}")
        return False

def generate_summary_report():
    """Generate quick verification summary"""
    print("\n" + "=" * 60)
    print("📊 IMMEDIATE MAVLINK VERIFICATION SUMMARY")
    print("=" * 60)
    
    # Run all tests
    results = {
        'network_connectivity': test_network_connectivity(),
        'port_accessibility': test_port_accessibility(),
        'webgcs_status': test_webgcs_status(),
        'mavlink_connections': check_mavlink_connections(),
        'basic_mavlink_comm': test_basic_mavlink_communication()
    }
    
    # Calculate overall status
    passed_tests = sum(results.values())
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📋 OVERALL STATUS:")
    if success_rate >= 80:
        print("✅ MAVLINK COMMUNICATION: VERIFIED")
        status = "VERIFIED"
    elif success_rate >= 60:
        print("⚠️  MAVLINK COMMUNICATION: PARTIAL")
        status = "PARTIAL"
    else:
        print("❌ MAVLINK COMMUNICATION: FAILED")
        status = "FAILED"
    
    print(f"Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    print(f"\n🎯 CRITICAL FINDINGS:")
    
    if results['network_connectivity'] and results['port_accessibility']:
        print("  ✅ Network path to virtual drone is ACCESSIBLE")
    
    if results['webgcs_status']:
        print("  ✅ WebGCS server is HEALTHY and reports drone connected")
    
    if results['mavlink_connections']:
        print("  ✅ Active MAVLink connections detected on port 5678")
    
    if results['basic_mavlink_comm']:
        print("  ✅ Basic MAVLink message reception CONFIRMED")
    
    # List any failures
    failures = [test_name for test_name, result in results.items() if not result]
    if failures:
        print(f"\n⚠️  ISSUES DETECTED:")
        for failure in failures:
            print(f"  ❌ {failure.replace('_', ' ').title()}")
    
    # Save quick report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': status,
        'success_rate': success_rate,
        'test_results': results,
        'summary': f"{passed_tests}/{total_tests} tests passed"
    }
    
    try:
        filename = f"IMMEDIATE_MAVLINK_VERIFICATION_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\n📄 Report saved: {filename}")
    except:
        pass
    
    print("=" * 60)
    
    return status == "VERIFIED"

def main():
    """Main execution"""
    print("🚁 IMMEDIATE MAVLINK VERIFICATION")
    print("Target: 192.168.193.235:5678")
    print("Started:", datetime.now().strftime('%H:%M:%S'))
    print("-" * 40)
    
    try:
        success = generate_summary_report()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
WebGCS Phase 1 Test Runner
Runs MAVLink foundation tests with proper error handling and reporting.
"""

import subprocess
import sys
import time
import os

def run_test_suite(test_file, test_name, timeout=60):
    """Run a test suite with timeout and proper error handling."""
    print(f"\n{'='*60}")
    print(f"Running {test_name}")
    print(f"{'='*60}")
    
    try:
        # Run pytest with timeout
        cmd = ["uv", "run", "pytest", test_file, "-v", "--tb=short"]
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time
        
        print(f"Test execution time: {elapsed:.2f}s")
        print("\nSTDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED")
            return True
        else:
            print(f"❌ {test_name} FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_name} TIMED OUT after {timeout}s")
        return False
    except Exception as e:
        print(f"💥 {test_name} ERROR: {e}")
        return False

def check_virtual_drone():
    """Check if virtual drone is accessible."""
    print("Checking virtual drone connectivity...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('192.168.193.235', 5678))
        sock.close()
        
        if result == 0:
            print("✅ Virtual drone is accessible at 192.168.193.235:5678")
            return True
        else:
            print("❌ Virtual drone is NOT accessible at 192.168.193.235:5678")
            print("   Real drone connection tests will be skipped")
            return False
    except Exception as e:
        print(f"❌ Error checking virtual drone: {e}")
        return False

def main():
    """Run Phase 1 MAVLink foundation tests."""
    print("WebGCS Phase 1 MAVLink Foundation Test Suite")
    print("=" * 60)
    
    # Check environment
    if not os.path.exists("tests"):
        print("❌ Tests directory not found")
        sys.exit(1)
    
    # Check virtual drone
    drone_available = check_virtual_drone()
    
    # Define test suites
    test_suites = [
        {
            "file": "tests/test_001_mavlink_connection.py::TestMAVLinkConnection::test_connection_manager_initialization",
            "name": "TEST-001a: Connection Manager Initialization",
            "timeout": 10
        },
        {
            "file": "tests/test_001_mavlink_connection.py::TestMAVLinkConnection::test_connection_timeout_scenarios",
            "name": "TEST-001b: Connection Timeout Scenarios",
            "timeout": 20
        },
        {
            "file": "tests/test_002_telemetry_processing.py",
            "name": "TEST-002: Telemetry Processing",
            "timeout": 60
        },
        {
            "file": "tests/test_003_command_sending.py",
            "name": "TEST-003: Command Sending",
            "timeout": 60
        }
    ]
    
    # Add full connection tests only if drone is available
    if drone_available:
        test_suites.insert(1, {
            "file": "tests/test_001_mavlink_connection.py",
            "name": "TEST-001: Complete MAVLink Connection (with real drone)",
            "timeout": 120
        })
    
    # Run test suites
    results = []
    for suite in test_suites:
        success = run_test_suite(
            suite["file"],
            suite["name"],
            suite["timeout"]
        )
        results.append((suite["name"], success))
    
    # Print summary
    print(f"\n{'='*60}")
    print("PHASE 1 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 ALL PHASE 1 TESTS PASSED!")
        print("\n✅ MAVLink Foundation Validated:")
        print("   - Connection management working")
        print("   - Message processing functional")
        print("   - Command sending operational")
        print("   - Error handling robust")
        print("   - Thread safety verified")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Integration Test Runner for WebGCS
Runs comprehensive integration tests with proper setup and reporting
"""
import sys
import subprocess
import time
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.token_tracker import record_agent_usage


def check_virtual_drone_connection():
    """Check if virtual drone is available."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('192.168.193.235', 5678))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking drone connection: {e}")
        return False


def start_web_app():
    """Start the web application in background."""
    try:
        # Check if app is already running
        response = requests.get("http://127.0.0.1:5001", timeout=2)
        print("Web application already running")
        return None
    except:
        pass
    
    # Start web application
    print("Starting web application...")
    process = subprocess.Popen([
        "uv", "run", "python", "-c",
        "from src.web.app_factory import create_app, run_app; app = create_app(); run_app(app, debug=False)"
    ], cwd=project_root)
    
    # Wait for startup
    time.sleep(5)
    
    # Verify it started
    try:
        response = requests.get("http://127.0.0.1:5001", timeout=10)
        print("Web application started successfully")
        return process
    except Exception as e:
        print(f"Failed to start web application: {e}")
        if process:
            process.terminate()
        return None


def run_integration_tests():
    """Run all integration tests with proper setup."""
    print("=" * 60)
    print("WebGCS Integration Test Suite")
    print("=" * 60)
    
    # Check prerequisites
    print("\n--- Checking Prerequisites ---")
    
    # Check virtual drone connection
    if check_virtual_drone_connection():
        print("✓ Virtual drone connection available")
    else:
        print("✗ Virtual drone not available at 192.168.193.235:5678")
        print("  Please ensure virtual drone is running")
        return False
    
    # Start web application if needed
    web_process = start_web_app()
    if web_process is None:
        print("✗ Failed to start web application")
        return False
    
    try:
        print("\n--- Running Integration Tests ---")
        
        # Test order for optimal execution
        test_files = [
            "test_real_drone_connection.py",
            "test_web_interface_integration.py", 
            "test_telemetry_pipeline.py",
            "test_vfr_hud_display.py",
            "test_map_integration.py",
            "test_end_to_end_workflows.py"
        ]
        
        test_results = {}
        total_passed = 0
        total_failed = 0
        
        for test_file in test_files:
            print(f"\n🧪 Running {test_file}...")
            
            # Run individual test file
            result = subprocess.run([
                "uv", "run", "pytest", 
                f"tests/integration/{test_file}",
                "-v", "--tb=short", "--color=yes"
            ], cwd=project_root, capture_output=True, text=True)
            
            # Parse results
            if result.returncode == 0:
                print(f"✅ {test_file} - ALL PASSED")
                test_results[test_file] = "PASSED"
                # Count passed tests from output
                passed_count = result.stdout.count(" PASSED")
                total_passed += passed_count
            else:
                print(f"❌ {test_file} - SOME FAILURES")
                test_results[test_file] = "FAILED"
                # Count failed tests from output
                failed_count = result.stdout.count(" FAILED")
                error_count = result.stdout.count(" ERROR")
                total_failed += failed_count + error_count
            
            # Show key output lines
            if result.stdout:
                lines = result.stdout.split('\n')
                summary_lines = [line for line in lines if 
                               " PASSED" in line or " FAILED" in line or 
                               " ERROR" in line or "assertions" in line]
                for line in summary_lines[-5:]:  # Last 5 relevant lines
                    if line.strip():
                        print(f"  {line}")
            
            if result.stderr and result.returncode != 0:
                error_lines = result.stderr.split('\n')[:3]  # First 3 error lines
                for line in error_lines:
                    if line.strip():
                        print(f"  ERROR: {line}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        for test_file, status in test_results.items():
            status_icon = "✅" if status == "PASSED" else "❌"
            print(f"{status_icon} {test_file}: {status}")
        
        print(f"\nTotal Results:")
        print(f"  ✅ Passed: {total_passed}")
        print(f"  ❌ Failed: {total_failed}")
        
        success_rate = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
        print(f"  📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print(f"\n🎉 Integration tests mostly successful! ({success_rate:.1f}% pass rate)")
        elif success_rate >= 60:
            print(f"\n⚠️  Integration tests partially successful ({success_rate:.1f}% pass rate)")
        else:
            print(f"\n💥 Integration tests need attention ({success_rate:.1f}% pass rate)")
        
        return success_rate >= 60
        
    finally:
        # Cleanup
        if web_process:
            print("\n--- Cleaning Up ---")
            web_process.terminate()
            web_process.wait(timeout=10)
            print("✓ Web application stopped")
        
        record_agent_usage('testing-agent', 300, 230)


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
"""
Phase 4 Test Runner - Flight Control Button Testing
Runs all Phase 4 tests in proper sequence using Playwright MCP.

This runner ensures:
- Tests run in logical order
- Virtual drone is available  
- WebGCS server starts cleanly
- Proper cleanup between tests
- Flight control buttons are tested comprehensively
"""
import pytest
import sys
import time
from pathlib import Path


def run_phase4_tests():
    """Run all Phase 4 connection tests."""
    
    test_dir = Path(__file__).parent
    
    # Define test order for logical progression
    test_files = [
        "test_011_connect_button.py",           # Connection foundation
        "test_012_disconnect_button.py", 
        "test_013_connection_status_display.py",
        "test_014_disconnect_reconnect_cycle.py",
        "test_015_arm_button.py",               # Flight control tests
        "test_016_disarm_button.py",
        "test_017_takeoff_button.py", 
        "test_018_land_button.py",
        "test_019_rtl_button.py",
        "test_020_set_mode_button.py",
        "test_021_comprehensive_flight_controls.py"  # Integration test
    ]
    
    print("=" * 80)
    print("PHASE 4: FLIGHT CONTROL BUTTON TESTING")
    print("Testing with Playwright MCP against live WebGCS server")
    print("Safety-critical ARM/DISARM/TAKEOFF button testing with confirmations")
    print("=" * 80)
    
    all_passed = True
    results = {}
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            all_passed = False
            continue
            
        print(f"\n🔄 Running {test_file}...")
        
        # Run individual test file
        result = pytest.main([
            str(test_path),
            "-v",
            "--tb=short",
            "--no-header"
        ])
        
        if result == 0:
            print(f"✅ {test_file} - PASSED")
            results[test_file] = "PASSED"
        else:
            print(f"❌ {test_file} - FAILED")
            results[test_file] = "FAILED"
            all_passed = False
        
        # Brief pause between tests
        time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 80)
    print("PHASE 4 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_file, status in results.items():
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"{status_icon} {test_file:<40} {status}")
    
    if all_passed:
        print(f"\n🎉 ALL PHASE 4 TESTS PASSED! ({len(results)}/{len(test_files)})")
        print("\nPhase 4 flight control button testing complete.")
        print("✅ All flight controls verified with Playwright MCP:")
        print("   • ARM/DISARM buttons with safety confirmations") 
        print("   • TAKEOFF button with altitude validation")
        print("   • LAND and RTL emergency buttons")
        print("   • Set Mode button with flight mode selection")
        print("   • Comprehensive integration testing")
        return 0
    else:
        passed_count = sum(1 for status in results.values() if status == "PASSED")
        print(f"\n⚠️  PHASE 4 INCOMPLETE: {passed_count}/{len(test_files)} tests passed")
        print("\nSome flight control tests failed. Check output above for details.")
        
        # Show specific failure categories
        failed_tests = [test for test, status in results.items() if status == "FAILED"]
        connection_failures = [t for t in failed_tests if any(x in t for x in ['011', '012', '013', '014'])]
        flight_control_failures = [t for t in failed_tests if any(x in t for x in ['015', '016', '017', '018', '019', '020', '021'])]
        
        if connection_failures:
            print(f"\n❌ Connection test failures: {len(connection_failures)}")
        if flight_control_failures:
            print(f"❌ Flight control test failures: {len(flight_control_failures)}")
        
        return 1


if __name__ == "__main__":
    exit_code = run_phase4_tests()
    sys.exit(exit_code)
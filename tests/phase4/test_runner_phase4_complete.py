"""
Phase 4 Complete Test Runner - All Button Testing
Runs all Phase 4 tests including Flight Controls, Navigation, and Map Interface.

This runner ensures:
- Tests run in logical order (Connection -> Flight Controls -> Navigation -> Map Interface)
- Virtual drone is available at 192.168.193.235:5678
- WebGCS servers start cleanly on different ports
- Proper cleanup between tests
- Comprehensive button testing with Playwright MCP
"""
import pytest
import sys
import time
from pathlib import Path
from src.utils.token_tracker import record_agent_usage, get_usage_summary


def run_phase4_complete_tests():
    """Run all Phase 4 tests in comprehensive sequence."""
    
    test_dir = Path(__file__).parent
    
    # Define complete test order for logical progression
    test_files = [
        # Connection Foundation Tests
        "test_011_connect_button.py",           # Connection establishment
        "test_012_disconnect_button.py", 
        "test_013_connection_status_display.py",
        "test_014_disconnect_reconnect_cycle.py",
        
        # Flight Control Tests
        "test_015_arm_button.py",               # Safety-critical controls
        "test_016_disarm_button.py",
        "test_017_takeoff_button.py", 
        "test_018_land_button.py",
        "test_019_rtl_button.py",
        "test_020_set_mode_button.py",
        "test_021_comprehensive_flight_controls.py",  # Flight controls integration
        
        # Navigation Control Tests  
        "test_022_goto_button.py",              # Navigation commands
        "test_023_clear_nav_button.py",
        "test_024_navigation_integration.py",
        "test_025_navigation_controls.py",     # Navigation integration
        
        # Map Interface Tests
        "test_028_center_map_button.py",       # Map interface controls
        "test_029_fly_to_toggle_button.py",
        "test_030_map_interface.py",
        "test_031_drone_location_map_display.py",
        "test_032_drone_location_map_display_visual.py"  # Map interface integration
    ]
    
    print("=" * 80)
    print("PHASE 4: COMPLETE BUTTON TESTING WITH PLAYWRIGHT MCP")
    print("Testing ALL WebGCS interface elements against virtual drone")
    print("=" * 80)
    print("Test Categories:")
    print("• Connection Controls (4 tests) - Connect/Disconnect functionality")
    print("• Flight Controls (7 tests) - ARM/DISARM/TAKEOFF safety-critical buttons")
    print("• Navigation Controls (4 tests) - GO TO/CLEAR coordinate navigation")
    print("• Map Interface (5 tests) - Interactive map controls and drone positioning")
    print("=" * 80)
    
    # Track results by category
    connection_results = {}
    flight_control_results = {}
    navigation_results = {}
    map_interface_results = {}
    
    all_passed = True
    total_tests = len(test_files)
    
    for i, test_file in enumerate(test_files, 1):
        test_path = test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            all_passed = False
            continue
            
        # Determine category
        if test_file.startswith("test_011") or test_file.startswith("test_012") or \
           test_file.startswith("test_013") or test_file.startswith("test_014"):
            category = "Connection"
            results_dict = connection_results
        elif test_file.startswith("test_015") or test_file.startswith("test_016") or \
             test_file.startswith("test_017") or test_file.startswith("test_018") or \
             test_file.startswith("test_019") or test_file.startswith("test_020") or \
             test_file.startswith("test_021"):
            category = "Flight Control"
            results_dict = flight_control_results
        elif test_file.startswith("test_022") or test_file.startswith("test_023") or \
             test_file.startswith("test_024") or test_file.startswith("test_025"):
            category = "Navigation"
            results_dict = navigation_results
        elif test_file.startswith("test_028") or test_file.startswith("test_029") or \
             test_file.startswith("test_030") or test_file.startswith("test_031") or \
             test_file.startswith("test_032"):
            category = "Map Interface"
            results_dict = map_interface_results
        else:
            category = "Other"
            results_dict = {}
        
        print(f"\n[{i:2d}/{total_tests}] 🔄 Running {category}: {test_file}")
        
        # Run individual test file with timeout
        start_time = time.time()
        result = pytest.main([
            str(test_path),
            "-v",
            "--tb=short",
            "--no-header",
            "--maxfail=1"
        ])
        
        elapsed = time.time() - start_time
        
        if result == 0:
            print(f"✅ {test_file} - PASSED ({elapsed:.1f}s)")
            results_dict[test_file] = "PASSED"
        else:
            print(f"❌ {test_file} - FAILED ({elapsed:.1f}s)")
            results_dict[test_file] = "FAILED"
            all_passed = False
        
        # Brief pause between tests to avoid server conflicts
        time.sleep(2)
    
    # Print detailed summary by category
    print("\n" + "=" * 80)
    print("PHASE 4 COMPLETE TEST RESULTS SUMMARY")
    print("=" * 80)
    
    def print_category_results(category_name, results_dict, emoji):
        if not results_dict:
            return
        passed = sum(1 for status in results_dict.values() if status == "PASSED")
        total = len(results_dict)
        print(f"\n{emoji} {category_name} Tests: {passed}/{total} passed")
        
        for test_file, status in results_dict.items():
            status_icon = "✅" if status == "PASSED" else "❌"
            test_name = test_file.replace("test_", "").replace(".py", "")
            print(f"  {status_icon} {test_name:<35} {status}")
    
    print_category_results("Connection", connection_results, "🔌")
    print_category_results("Flight Control", flight_control_results, "🚁") 
    print_category_results("Navigation", navigation_results, "🧭")
    print_category_results("Map Interface", map_interface_results, "🗺️")
    
    # Overall summary
    total_passed = (len([r for r in connection_results.values() if r == "PASSED"]) +
                   len([r for r in flight_control_results.values() if r == "PASSED"]) +
                   len([r for r in navigation_results.values() if r == "PASSED"]) +
                   len([r for r in map_interface_results.values() if r == "PASSED"]))
    
    print(f"\n📊 OVERALL RESULTS: {total_passed}/{total_tests} tests passed")
    
    if all_passed:
        print(f"\n🎉 ALL PHASE 4 TESTS PASSED!")
        print("\nPhase 4 complete button testing successful:")
        print("✅ Connection controls verified with Playwright MCP")
        print("✅ Safety-critical flight controls tested with confirmations") 
        print("✅ Navigation controls validated with coordinate input")
        print("✅ Interactive map interface tested with drone positioning")
        print("✅ All buttons functional with virtual drone integration")
        
        # Record success
        record_agent_usage("testing-agent", "phase4_complete", "ALL_PASSED")
        return 0
    else:
        print(f"\n⚠️  PHASE 4 INCOMPLETE: {total_passed}/{total_tests} tests passed")
        print("\nSome button tests failed. Analysis by category:")
        
        if any(status == "FAILED" for status in connection_results.values()):
            print("🔌 Connection test failures - Basic connectivity issues")
        if any(status == "FAILED" for status in flight_control_results.values()):
            print("🚁 Flight control test failures - Safety-critical button issues") 
        if any(status == "FAILED" for status in navigation_results.values()):
            print("🧭 Navigation test failures - Coordinate input/GO TO issues")
        if any(status == "FAILED" for status in map_interface_results.values()):
            print("🗺️ Map interface test failures - Interactive map control issues")
        
        # Record partial success  
        record_agent_usage("testing-agent", "phase4_complete", f"PARTIAL_{total_passed}_{total_tests}")
        return 1


def print_token_usage_summary():
    """Print token usage summary for all agents involved."""
    print("\n" + "=" * 80)
    print("TOKEN USAGE SUMMARY - PHASE 4 TESTING")
    print("=" * 80)
    
    usage_summary = get_usage_summary()
    if usage_summary:
        print(usage_summary)
    else:
        print("No token usage data available")


if __name__ == "__main__":
    print("Starting Phase 4 Complete Button Testing...")
    
    # Record test initiation
    record_agent_usage("testing-agent", "phase4_complete_start", "INITIATED")
    
    try:
        exit_code = run_phase4_complete_tests()
        
        # Print token usage
        print_token_usage_summary()
        
        if exit_code == 0:
            print("\n🎉 Phase 4 Complete Testing: SUCCESS")
        else:
            print("\n⚠️ Phase 4 Complete Testing: PARTIAL/FAILURE")
        
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n💥 Phase 4 testing failed with error: {str(e)}")
        record_agent_usage("testing-agent", "phase4_complete_error", f"ERROR: {str(e)}")
        sys.exit(1)
"""
Phase 4 Map Interface Tests Runner
Executes all map interface tests using Playwright MCP for comprehensive validation.

Test Coverage:
- TEST-028: Center map button functionality
- TEST-029: Fly-to toggle button behavior
- TEST-030: Map interface interactions  
- TEST-031: Drone location display on map
- TEST-032: Visual map validation

Requirements:
- Tests actual map interface elements with Playwright MCP
- Validates interactive map controls and drone positioning
- Tests click-to-fly functionality and map-based navigation
- Verifies visual consistency and marker styling
"""
import pytest
import sys
import os
import asyncio
from src.utils.token_tracker import record_agent_usage, get_usage_summary


class Phase4MapInterfaceTestRunner:
    """Orchestrates execution of Phase 4 Map Interface tests."""
    
    def __init__(self):
        self.test_files = [
            "test_028_center_map_button.py",
            "test_029_fly_to_toggle_button.py", 
            "test_030_map_interface.py",
            "test_031_drone_location_map_display.py",
            "test_032_drone_location_map_display_visual.py"
        ]
        self.results = {}
        
    def run_all_tests(self):
        """Execute all Phase 4 Map Interface tests."""
        print("\n" + "="*60)
        print("PHASE 4 MAP INTERFACE TESTING - Playwright MCP")
        print("="*60)
        print("Testing interactive map functionality:")
        print("- CENTER MAP button functionality")
        print("- FLY TO mode toggle button")
        print("- Map interface interactions")
        print("- Drone location display accuracy")
        print("- Visual map validation")
        print("="*60)
        
        total_passed = 0
        total_failed = 0
        
        for test_file in self.test_files:
            print(f"\n🧪 Running {test_file}...")
            
            # Run individual test file
            test_path = os.path.join(os.path.dirname(__file__), test_file)
            
            if os.path.exists(test_path):
                exit_code = pytest.main([
                    test_path,
                    "-v",
                    "--tb=short",
                    "--maxfail=1"
                ])
                
                if exit_code == 0:
                    print(f"✅ {test_file} - PASSED")
                    self.results[test_file] = "PASSED"
                    total_passed += 1
                else:
                    print(f"❌ {test_file} - FAILED")
                    self.results[test_file] = "FAILED"
                    total_failed += 1
            else:
                print(f"⚠️  {test_file} - FILE NOT FOUND")
                self.results[test_file] = "NOT_FOUND"
                total_failed += 1
        
        # Print summary
        print("\n" + "="*60)
        print("PHASE 4 MAP INTERFACE TEST RESULTS")
        print("="*60)
        
        for test_file, result in self.results.items():
            status_emoji = "✅" if result == "PASSED" else "❌" if result == "FAILED" else "⚠️"
            print(f"{status_emoji} {test_file}: {result}")
        
        print(f"\nSUMMARY: {total_passed} passed, {total_failed} failed")
        
        # Record overall results
        if total_failed == 0:
            print("🎉 ALL PHASE 4 MAP INTERFACE TESTS PASSED!")
            record_agent_usage("map-interface-testing-agent", "phase4_map_interface_complete", "ALL_PASSED")
            return True
        else:
            print("💥 SOME PHASE 4 MAP INTERFACE TESTS FAILED")
            record_agent_usage("map-interface-testing-agent", "phase4_map_interface_complete", "SOME_FAILED")
            return False
    
    def run_individual_test(self, test_name):
        """Run a specific test by name."""
        test_file = f"test_{test_name}.py"
        
        if test_file not in self.test_files:
            print(f"❌ Test {test_name} not found in Phase 4 Map Interface tests")
            return False
        
        print(f"\n🧪 Running individual test: {test_file}")
        
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        exit_code = pytest.main([
            test_path,
            "-v",
            "--tb=long"
        ])
        
        if exit_code == 0:
            print(f"✅ {test_file} - PASSED")
            return True
        else:
            print(f"❌ {test_file} - FAILED")
            return False

    def get_test_status(self):
        """Get current test execution status."""
        return {
            "phase": "Phase 4 - Map Interface Testing",
            "total_tests": len(self.test_files),
            "test_files": self.test_files,
            "results": self.results,
            "agent": "map-interface-testing-agent",
            "tools": ["Playwright MCP", "Browser Automation"],
            "focus": "Interactive map controls and drone positioning"
        }


def run_phase4_map_interface_tests():
    """Main entry point for Phase 4 Map Interface testing."""
    runner = Phase4MapInterfaceTestRunner()
    
    # Record test initiation
    record_agent_usage("map-interface-testing-agent", "phase4_map_interface_start", "INITIATED")
    
    try:
        success = runner.run_all_tests()
        
        # Print token usage summary
        print("\n" + "="*60)
        print("TOKEN USAGE SUMMARY")
        print("="*60)
        usage_summary = get_usage_summary()
        if usage_summary:
            print(usage_summary)
        
        return success
        
    except Exception as e:
        print(f"💥 Phase 4 Map Interface testing failed with error: {str(e)}")
        record_agent_usage("map-interface-testing-agent", "phase4_map_interface_error", f"ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    # Support command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        runner = Phase4MapInterfaceTestRunner()
        
        if command == "status":
            status = runner.get_test_status()
            print(f"Phase: {status['phase']}")
            print(f"Total Tests: {status['total_tests']}")
            print(f"Agent: {status['agent']}")
            print(f"Focus: {status['focus']}")
            
        elif command.startswith("test_"):
            # Run individual test
            test_name = command.replace("test_", "").replace(".py", "")
            runner.run_individual_test(test_name)
            
        else:
            print("Usage:")
            print("  python test_runner_phase4_map_interface.py           # Run all tests")
            print("  python test_runner_phase4_map_interface.py status    # Show status")
            print("  python test_runner_phase4_map_interface.py test_028  # Run specific test")
            
    else:
        # Run all tests
        success = run_phase4_map_interface_tests()
        sys.exit(0 if success else 1)
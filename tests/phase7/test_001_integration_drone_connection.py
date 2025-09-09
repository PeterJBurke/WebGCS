"""
Phase 7 Integration Test: Drone Connection Integration
Runs comprehensive drone connection tests as part of Phase 7
"""
import pytest
import subprocess
import sys


class TestIntegrationDroneConnection:
    """Phase 7 integration test for drone connections."""
    
    def test_run_drone_connection_integration_tests(self):
        """Run all drone connection integration tests."""
        
        # Run the working drone connection tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/integration/test_real_drone_connection.py",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd="/Users/peterburke/Documents/Code/WebGCS6")
        
        print("=== Drone Connection Integration Test Results ===")
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check if tests passed (return code 0 means success)
        assert result.returncode == 0, f"Drone connection tests should pass. Return code: {result.returncode}"
        
        # Verify at least the basic connection test passed
        assert "test_mavlink_connection_establishment PASSED" in result.stdout
        
        # Count passed tests
        passed_count = result.stdout.count("PASSED")
        skipped_count = result.stdout.count("SKIPPED")
        
        print(f"📊 Integration Test Results: {passed_count} passed, {skipped_count} skipped")
        
        # At least one test should pass (connection establishment)
        assert passed_count >= 1, "At least one integration test should pass"
        
        print("✅ Phase 7 Drone Connection Integration Tests: PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
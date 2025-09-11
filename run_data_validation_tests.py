#!/usr/bin/env python3
"""
Data Validation Test Suite Runner
Executes comprehensive MAVLink data flow validation tests to identify connection issues.
"""

import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_validation_tests.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

class DataValidationTestRunner:
    """Runs systematic data validation tests to diagnose MAVLink issues."""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        
    def run_test_suite(self):
        """Run all data validation tests."""
        logger.info("=" * 60)
        logger.info("STARTING DATA VALIDATION TEST SUITE")
        logger.info("=" * 60)
        logger.info(f"Test suite started at: {self.start_time}")
        logger.info("")
        
        # Test sequence designed to systematically expose data flow issues
        test_sequence = [
            ("TEST-011", "Real MAVLink Connection Validation", "tests/test_011_real_mavlink_connection.py"),
            ("TEST-012", "Telemetry Data Flow Validation", "tests/test_012_telemetry_data_flow.py"),
            ("TEST-013", "HUD Data Display Validation", "tests/test_013_hud_data_display.py"),
            ("TEST-014", "Map Data Display Validation", "tests/test_014_map_data_display.py"),
        ]
        
        overall_success = True
        
        for test_id, test_name, test_file in test_sequence:
            logger.info(f"Running {test_id}: {test_name}")
            logger.info("-" * 50)
            
            success, details = self._run_single_test(test_file)
            
            self.test_results[test_id] = {
                'name': test_name,
                'file': test_file,
                'success': success,
                'details': details,
                'timestamp': datetime.now()
            }
            
            if success:
                logger.info(f"✅ {test_id} PASSED: {test_name}")
            else:
                logger.error(f"❌ {test_id} FAILED: {test_name}")
                logger.error(f"   Failure details: {details}")
                overall_success = False
            
            logger.info("")
            time.sleep(2)  # Brief pause between tests
        
        self._generate_final_report(overall_success)
        
        if not overall_success:
            logger.error("❌ DATA VALIDATION TESTS REVEALED CRITICAL ISSUES")
            logger.error("   Review test failures above to identify data flow problems")
            return False
        else:
            logger.info("✅ ALL DATA VALIDATION TESTS PASSED")
            return True
    
    def _run_single_test(self, test_file: str) -> tuple[bool, str]:
        """Run a single test file and return success status and details."""
        try:
            # Ensure WebGCS is running
            self._ensure_webgcs_running()
            
            # Run the test
            cmd = [sys.executable, "-m", "pytest", test_file, "-v", "-x", "--tb=short"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout per test
                cwd=Path.cwd()
            )
            
            success = result.returncode == 0
            
            if success:
                details = "All test assertions passed"
            else:
                # Extract failure details from pytest output
                details = self._extract_failure_details(result.stdout, result.stderr)
            
            return success, details
            
        except subprocess.TimeoutExpired:
            return False, "Test timed out after 2 minutes"
        except Exception as e:
            return False, f"Test execution error: {str(e)}"
    
    def _extract_failure_details(self, stdout: str, stderr: str) -> str:
        """Extract meaningful failure details from test output."""
        # Look for assertion failures and error messages
        output = stdout + "\n" + stderr
        lines = output.split('\n')
        
        failure_lines = []
        in_failure = False
        
        for line in lines:
            if 'FAILED:' in line or 'AssertionError:' in line:
                in_failure = True
                failure_lines.append(line)
            elif in_failure and (line.startswith('    ') or line.startswith('>')):
                failure_lines.append(line)
            elif in_failure and line.strip() == '':
                continue
            elif in_failure:
                break
        
        if failure_lines:
            return '\n'.join(failure_lines[:10])  # First 10 relevant lines
        else:
            # Fallback to last few lines of output
            return '\n'.join(lines[-10:])
    
    def _ensure_webgcs_running(self):
        """Ensure WebGCS is running for tests."""
        try:
            import requests
            response = requests.get('http://localhost:5002', timeout=5)
            if response.status_code == 200:
                return  # WebGCS is running
        except:
            pass
        
        # Start WebGCS if not running
        logger.info("Starting WebGCS for testing...")
        subprocess.Popen([
            sys.executable, "main.py"
        ], cwd=Path.cwd())
        
        # Wait for startup
        time.sleep(8)
        
        # Verify it started
        try:
            import requests
            response = requests.get('http://localhost:5002', timeout=10)
            if response.status_code != 200:
                raise Exception("WebGCS did not start properly")
        except Exception as e:
            raise Exception(f"Failed to start WebGCS: {e}")
    
    def _generate_final_report(self, overall_success: bool):
        """Generate final test report."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        logger.info("=" * 60)
        logger.info("DATA VALIDATION TEST SUITE RESULTS")
        logger.info("=" * 60)
        logger.info(f"Test suite completed at: {end_time}")
        logger.info(f"Total duration: {duration}")
        logger.info("")
        
        # Summary by test
        for test_id, result in self.test_results.items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            logger.info(f"{status} {test_id}: {result['name']}")
            if not result['success']:
                logger.info(f"    Issue: {result['details'][:100]}...")
        
        logger.info("")
        logger.info("CRITICAL FINDINGS:")
        logger.info("-" * 40)
        
        if overall_success:
            logger.info("✅ All data validation tests passed")
            logger.info("✅ MAVLink data flow is working correctly")
            logger.info("✅ Virtual drone connection successful")
            logger.info("✅ Real telemetry data flowing to UI components")
        else:
            logger.error("❌ Data validation tests revealed critical issues:")
            
            failed_tests = [t for t in self.test_results.values() if not t['success']]
            
            if any('TCP' in t['details'] or 'connection' in t['details'] for t in failed_tests):
                logger.error("   • Virtual drone not running on 192.168.193.235:5678")
                logger.error("   • Backend cannot establish MAVLink connection")
            
            if any('heartbeat' in t['details'].lower() for t in failed_tests):
                logger.error("   • No real MAVLink heartbeat messages received")
                logger.error("   • Heartbeat counter not incrementing")
            
            if any('telemetry' in t['details'].lower() for t in failed_tests):
                logger.error("   • No real telemetry data flowing to UI")
                logger.error("   • HUD showing placeholder/default values")
            
            if any('map' in t['details'].lower() or 'loading' in t['details'].lower()):
                logger.error("   • Map stuck in loading state")
                logger.error("   • No real position data reaching map component")
        
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("-" * 40)
        
        if not overall_success:
            logger.error("1. ⚠️ START VIRTUAL DRONE: Ensure virtual drone running on 192.168.193.235:5678")
            logger.error("2. ⚠️ VERIFY MAVLINK CONNECTION: Check backend actually connects to drone")
            logger.error("3. ⚠️ FIX DATA FLOW: Ensure real telemetry flows from drone to UI")
            logger.error("4. ⚠️ UPDATE UI COMPONENTS: Fix placeholder data in HUD and map")
            logger.error("5. ⚠️ RE-RUN TESTS: Validate fixes with this test suite")
        else:
            logger.info("1. ✅ Data validation complete - system working correctly")
            logger.info("2. ✅ Ready for operational use with virtual drone")
            logger.info("3. ✅ All UI components displaying real data")
        
        logger.info("=" * 60)
        
        # Save detailed report
        self._save_detailed_report()
    
    def _save_detailed_report(self):
        """Save detailed test report to file."""
        report_file = f"DATA_VALIDATION_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w') as f:
            f.write("# Data Validation Test Report\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n")
            f.write(f"**Duration:** {datetime.now() - self.start_time}\n\n")
            
            f.write("## Test Results Summary\n\n")
            for test_id, result in self.test_results.items():
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                f.write(f"### {test_id}: {result['name']}\n")
                f.write(f"**Status:** {status}\n")
                f.write(f"**File:** `{result['file']}`\n")
                f.write(f"**Timestamp:** {result['timestamp'].isoformat()}\n")
                
                if not result['success']:
                    f.write(f"**Failure Details:**\n```\n{result['details']}\n```\n")
                
                f.write("\n")
            
            f.write("## Critical Issues Identified\n\n")
            failed_tests = [t for t in self.test_results.values() if not t['success']]
            
            if failed_tests:
                f.write("The following critical issues were identified:\n\n")
                for i, test in enumerate(failed_tests, 1):
                    f.write(f"{i}. **{test['name']}**: {test['details'][:200]}...\n")
            else:
                f.write("No critical issues identified. All tests passed.\n")
        
        logger.info(f"Detailed report saved to: {report_file}")


def main():
    """Main execution function."""
    runner = DataValidationTestRunner()
    
    try:
        success = runner.run_test_suite()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
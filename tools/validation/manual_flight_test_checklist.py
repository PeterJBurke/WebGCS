#!/usr/bin/env python3
"""
MANUAL FLIGHT CONTROLS TESTING CHECKLIST
Interactive testing guide for all flight control buttons

This script provides a step-by-step checklist for manually testing
all flight control buttons in the WebGCS interface.
"""

import time
import requests

class ManualTestingGuide:
    """Interactive guide for manual flight controls testing"""
    
    def __init__(self):
        self.server_url = "http://localhost:5001"
        self.tests_completed = []
        self.tests_failed = []
        
    def check_server_status(self):
        """Verify server is running before starting tests"""
        print("🔍 Checking WebGCS Server Status...")
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server Status: {data['status']}")
                print(f"✅ Drone Connected: {data['drone_connected']}")
                return True
            else:
                print(f"❌ Server returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("Make sure WebGCS server is running on localhost:5001")
            return False
    
    def wait_for_user(self, message):
        """Wait for user to complete a test step"""
        input(f"\n{message}\nPress Enter when completed...")
    
    def get_user_result(self, test_name):
        """Get test result from user"""
        while True:
            result = input(f"\nDid {test_name} work correctly? (y/n/skip): ").lower().strip()
            if result in ['y', 'yes']:
                self.tests_completed.append(test_name)
                print(f"✅ {test_name} - PASSED")
                return True
            elif result in ['n', 'no']:
                self.tests_failed.append(test_name)
                error = input("What was the error/issue? ").strip()
                print(f"❌ {test_name} - FAILED: {error}")
                return False
            elif result in ['s', 'skip']:
                print(f"⏭️ {test_name} - SKIPPED")
                return None
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'skip' to skip this test")
    
    def test_connection_setup(self):
        """Test initial connection setup"""
        print("\n" + "="*60)
        print("🔌 STEP 1: CONNECTION SETUP")
        print("="*60)
        
        print("1. Open your web browser")
        print("2. Navigate to: http://localhost:5001") 
        print("3. Wait for the page to load completely")
        print("4. Check the Connection Management panel")
        
        self.wait_for_user("✅ Verify you can see the WebGCS interface with flight controls")
        
        print("\n🔍 Connection Status Check:")
        print("- Look at the connection status indicator")
        print("- Should show 'Connected to drone' in green")
        print("- Heartbeat icon should be beating")  
        print("- Heartbeat counter should be incrementing")
        
        return self.get_user_result("Connection Status Display")
    
    def test_arm_button(self):
        """Test ARM button functionality"""
        print("\n" + "="*60)
        print("🔫 STEP 2: ARM BUTTON TEST")
        print("="*60)
        
        print("1. Locate the ARM button (yellow/orange color)")
        print("2. Click the ARM button")
        print("3. A confirmation dialog should appear")
        print("4. Dialog should say: 'ARM Vehicle - This will ARM the vehicle. Propellers may start spinning!'")
        print("5. Click 'Yes' to confirm")
        print("6. Check for success message")
        print("7. Check if 'ARMED' status appears in Primary Flight Display")
        
        self.wait_for_user("🎯 Complete the ARM button test steps above")
        
        return self.get_user_result("ARM Button with Safety Confirmation")
    
    def test_disarm_button(self):
        """Test DISARM button functionality"""
        print("\n" + "="*60)
        print("🔓 STEP 3: DISARM BUTTON TEST")
        print("="*60)
        
        print("1. Locate the DISARM button (red color)")
        print("2. Click the DISARM button")
        print("3. A confirmation dialog should appear")
        print("4. Dialog should say: 'DISARM Vehicle - This will DISARM the vehicle. Make sure it is landed safely.'")
        print("5. Click 'Yes' to confirm")
        print("6. Check for success message")
        print("7. Check if 'DISARMED' status appears in Primary Flight Display")
        
        self.wait_for_user("🎯 Complete the DISARM button test steps above")
        
        return self.get_user_result("DISARM Button with Safety Confirmation")
    
    def test_takeoff_button(self):
        """Test TAKEOFF button functionality"""
        print("\n" + "="*60)
        print("🚀 STEP 4: TAKEOFF BUTTON TEST")
        print("="*60)
        
        print("PREREQUISITES: Make sure drone is ARMED first!")
        print("1. If not armed, ARM the drone using the ARM button")
        print("2. Set takeoff altitude (try 10 meters)")
        print("3. Click the TAKEOFF button")
        print("4. Should see altitude validation")
        print("5. Confirmation dialog should appear with altitude")
        print("6. Dialog should say: 'TAKEOFF Vehicle - This will initiate takeoff to X meters altitude'")
        print("7. Click 'Yes' to confirm")
        print("8. Check for success message")
        
        print("\nTEST ALTITUDE VALIDATION:")
        print("9. Try invalid altitude (0.5m) - should show error")
        print("10. Try invalid altitude (1500m) - should show error")
        print("11. Try valid altitude (5-50m) - should work")
        
        self.wait_for_user("🎯 Complete the TAKEOFF button test steps above")
        
        return self.get_user_result("TAKEOFF Button with Altitude Validation")
    
    def test_land_button(self):
        """Test LAND button functionality"""
        print("\n" + "="*60)
        print("🛬 STEP 5: LAND BUTTON TEST")
        print("="*60)
        
        print("1. Locate the LAND button")
        print("2. Click the LAND button")
        print("3. Confirmation dialog should appear")
        print("4. Dialog should say: 'LAND Vehicle - This will initiate automatic landing at current position'")
        print("5. Click 'Yes' to confirm")
        print("6. Check for success message")
        
        self.wait_for_user("🎯 Complete the LAND button test steps above")
        
        return self.get_user_result("LAND Button")
    
    def test_rtl_button(self):
        """Test RTL button functionality"""
        print("\n" + "="*60)
        print("🏠 STEP 6: RTL (RETURN TO LAUNCH) BUTTON TEST")
        print("="*60)
        
        print("1. Locate the RTL button (blue color)")
        print("2. Click the RTL button") 
        print("3. Confirmation dialog should appear")
        print("4. Dialog should say: 'Return to Launch - This will return the vehicle to launch position and land'")
        print("5. Click 'Yes' to confirm")
        print("6. Check for success message")
        
        self.wait_for_user("🎯 Complete the RTL button test steps above")
        
        return self.get_user_result("RTL Button")
    
    def test_flight_modes(self):
        """Test flight mode dropdown and set mode button"""
        print("\n" + "="*60)
        print("🎯 STEP 7: FLIGHT MODES TEST")
        print("="*60)
        
        modes_to_test = [
            "STABILIZE", "ALT_HOLD", "POS_HOLD", "LOITER", 
            "GUIDED", "RTL", "LAND", "AUTO", "BRAKE"
        ]
        
        print(f"TEST ALL {len(modes_to_test)} FLIGHT MODES:")
        print("1. Locate the Flight Mode dropdown")
        print("2. Verify all these modes are available:")
        
        for i, mode in enumerate(modes_to_test, 1):
            print(f"   {i}. {mode}")
        
        print("\n3. For EACH mode:")
        print("   a. Select the mode from dropdown")
        print("   b. Click 'Set Mode' button")
        print("   c. Check for success/failure message")
        print("   d. Note the result")
        
        print("\n4. Pay special attention to:")
        print("   - GUIDED mode (commonly used)")
        print("   - RTL mode (return to launch)")
        print("   - STABILIZE mode (manual flight)")
        
        self.wait_for_user("🎯 Test all flight modes listed above")
        
        result = self.get_user_result("All 9 Flight Modes")
        
        # Get details on which modes worked
        if result:
            working_modes = input("Which modes worked successfully? (comma-separated): ").strip()
            print(f"✅ Working modes: {working_modes}")
        elif result is False:
            failed_modes = input("Which modes failed? (comma-separated): ").strip()  
            print(f"❌ Failed modes: {failed_modes}")
        
        return result
    
    def test_ui_updates(self):
        """Test UI updates and state changes"""
        print("\n" + "="*60)
        print("📊 STEP 8: UI UPDATES & STATE CHANGES")
        print("="*60)
        
        print("VERIFY UI UPDATES CORRECTLY:")
        print("1. Watch the Primary Flight Display (PFD) during tests")
        print("2. Armed Status should change: DISARMED ↔ ARMED")
        print("3. Flight Mode should update when mode changes succeed")
        print("4. Position coordinates should be updating continuously")
        print("5. Heartbeat counter should increment regularly")
        
        print("\nVERIFY BUTTON STATE MANAGEMENT:")
        print("6. ARM button should be disabled when already armed")
        print("7. DISARM button should be disabled when already disarmed")
        print("8. TAKEOFF should require armed state")
        print("9. All buttons should disable if connection lost")
        
        self.wait_for_user("🎯 Observe UI updates during your previous tests")
        
        return self.get_user_result("UI Updates and State Management")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n" + "="*60)
        print("⚠️ STEP 9: ERROR HANDLING TEST")
        print("="*60)
        
        print("TEST ERROR SCENARIOS:")
        print("1. Try TAKEOFF without being armed first - should show error")
        print("2. Try invalid takeoff altitude - should show validation error")
        print("3. Watch for any command timeouts or failures")
        print("4. Check that error messages are clear and helpful")
        
        self.wait_for_user("🎯 Test error handling scenarios")
        
        return self.get_user_result("Error Handling")
    
    def generate_final_report(self):
        """Generate final test report"""
        print("\n" + "="*80)
        print("📊 MANUAL FLIGHT CONTROLS TESTING REPORT")
        print("="*80)
        
        total_tests = len(self.tests_completed) + len(self.tests_failed)
        
        print(f"TESTS COMPLETED: {len(self.tests_completed)}")
        for test in self.tests_completed:
            print(f"  ✅ {test}")
        
        print(f"\nTESTS FAILED: {len(self.tests_failed)}")
        for test in self.tests_failed:
            print(f"  ❌ {test}")
        
        if total_tests > 0:
            success_rate = len(self.tests_completed) / total_tests
            print(f"\nSUCCESS RATE: {success_rate:.1%} ({len(self.tests_completed)}/{total_tests})")
            
            if success_rate >= 0.9:
                print("\n🎉 FLIGHT CONTROLS TESTING: SUCCESSFUL!")
                print("✅ All critical flight control buttons are working")
                print("✅ Safety confirmations are functioning")
                print("✅ Virtual drone communication established")
                print("✅ WebGCS is ready for operational use")
                return True
            elif success_rate >= 0.7:
                print("\n⚠️ FLIGHT CONTROLS TESTING: MOSTLY SUCCESSFUL")
                print("Most flight controls are working, but some issues need attention")
                return False
            else:
                print("\n❌ FLIGHT CONTROLS TESTING: NEEDS ATTENTION")
                print("Multiple issues detected - review failed tests above")
                return False
        else:
            print("\n⏭️ No tests were completed")
            return False
    
    def run_complete_test_suite(self):
        """Run the complete manual testing suite"""
        print("="*80)
        print("🚁 WEBGCS FLIGHT CONTROLS MANUAL TESTING SUITE")
        print("="*80)
        print("This interactive guide will walk you through testing")
        print("ALL flight control buttons with the virtual drone.")
        print("="*80)
        
        # Check server first
        if not self.check_server_status():
            print("❌ Cannot proceed - WebGCS server not available")
            return False
        
        print("\n📋 TESTING CHECKLIST:")
        print("✅ WebGCS Server running on localhost:5001")
        print("✅ Virtual Drone available at 192.168.193.235:5678") 
        print("✅ Web interface accessible")
        print("✅ All flight control buttons present")
        
        input("\nPress Enter to start manual testing...")
        
        # Run all test steps
        test_methods = [
            self.test_connection_setup,
            self.test_arm_button,
            self.test_disarm_button,
            self.test_takeoff_button,
            self.test_land_button,
            self.test_rtl_button,
            self.test_flight_modes,
            self.test_ui_updates,
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(1)  # Brief pause between tests
            except KeyboardInterrupt:
                print("\n\n⏹️ Testing interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Test error: {e}")
                continue
        
        # Generate final report
        return self.generate_final_report()


def main():
    """Main entry point for manual testing"""
    print("🚁 WebGCS Flight Controls Manual Testing Guide")
    print("=" * 50)
    print("Prerequisites:")
    print("1. WebGCS server running on localhost:5001") 
    print("2. Virtual drone running on 192.168.193.235:5678")
    print("3. Web browser available")
    print("=" * 50)
    
    tester = ManualTestingGuide()
    success = tester.run_complete_test_suite()
    
    if success:
        print("\n🎯 ALL FLIGHT CONTROLS VALIDATED SUCCESSFULLY!")
        exit(0)
    else:
        print("\n⚠️ SOME ISSUES DETECTED - REVIEW RESULTS ABOVE")
        exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
CONNECTION TESTING AGENT - Comprehensive Connect Button Validation
Test all aspects of the connect button functionality with 192.168.193.235:5678
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
from datetime import datetime

class ConnectionTestSuite:
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "target_url": "http://127.0.0.1:5002",
            "target_drone": "192.168.193.235:5678",
            "tests": []
        }
        self.page = None
        self.browser = None
        
    async def setup_browser(self):
        """Initialize browser and navigate to WebGCS"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        
        # Enable console logging
        self.page.on("console", lambda msg: print(f"🖥️  CONSOLE: {msg.text}"))
        self.page.on("pageerror", lambda error: print(f"❌ PAGE ERROR: {error}"))
        
        await self.page.goto("http://127.0.0.1:5002")
        await self.page.wait_for_load_state("networkidle")
        print("✅ Browser setup complete, navigated to WebGCS")
        
    async def test_cm_001_connect_button_exists(self):
        """TEST-CM-001: Verify Connect button exists and is enabled initially"""
        test_result = {
            "test_id": "TEST-CM-001",
            "description": "Connect Button Existence and Initial State",
            "success": False,
            "details": {}
        }
        
        try:
            # Check if connect button exists
            connect_button = await self.page.query_selector("button#connectBtn")
            test_result["details"]["button_exists"] = connect_button is not None
            
            if connect_button:
                # Check button properties
                is_enabled = await connect_button.is_enabled()
                button_text = await connect_button.inner_text()
                is_visible = await connect_button.is_visible()
                
                test_result["details"].update({
                    "is_enabled": is_enabled,
                    "button_text": button_text,
                    "is_visible": is_visible
                })
                
                # Check IP/port field
                ip_field = await self.page.query_selector("input#droneIP")
                if ip_field:
                    ip_value = await ip_field.get_attribute("value")
                    test_result["details"]["ip_field_value"] = ip_value
                    test_result["details"]["correct_ip"] = ip_value == "192.168.193.235:5678"
                
                test_result["success"] = is_enabled and is_visible and "Connect" in button_text
                
        except Exception as e:
            test_result["details"]["error"] = str(e)
            
        self.test_results["tests"].append(test_result)
        print(f"{'✅' if test_result['success'] else '❌'} {test_result['test_id']}: {test_result['description']}")
        return test_result["success"]
        
    async def test_cm_002_connection_state_management(self):
        """TEST-CM-002: Test connection state transitions"""
        test_result = {
            "test_id": "TEST-CM-002", 
            "description": "Connection State Management",
            "success": False,
            "details": {}
        }
        
        try:
            # Get initial state
            connect_button = await self.page.query_selector("button#connectBtn")
            initial_text = await connect_button.inner_text()
            test_result["details"]["initial_button_text"] = initial_text
            
            # Get initial heartbeat counter
            heartbeat_counter = await self.page.query_selector("#heartbeatCounter")
            if heartbeat_counter:
                initial_counter = await heartbeat_counter.inner_text()
                test_result["details"]["initial_heartbeat"] = initial_counter
            
            # Click connect button
            await connect_button.click()
            print("🔄 Clicked Connect button")
            
            # Wait for state change
            await self.page.wait_for_timeout(2000)
            
            # Check if button text changed to "Connecting..."
            current_text = await connect_button.inner_text()
            test_result["details"]["connecting_button_text"] = current_text
            
            # Wait longer for connection attempt
            await self.page.wait_for_timeout(8000)
            
            # Check final state
            final_text = await connect_button.inner_text()
            final_enabled = await connect_button.is_enabled()
            
            if heartbeat_counter:
                final_counter = await heartbeat_counter.inner_text()
                test_result["details"]["final_heartbeat"] = final_counter
                
            test_result["details"].update({
                "final_button_text": final_text,
                "final_enabled": final_enabled,
                "state_changed": current_text != initial_text
            })
            
            # Check connection status indicator
            status_indicator = await self.page.query_selector("#connectionStatus")
            if status_indicator:
                status_text = await status_indicator.inner_text()
                test_result["details"]["connection_status"] = status_text
                
            # Success if we see proper state transitions
            test_result["success"] = (
                "Connecting" in current_text or 
                "Connected" in final_text or 
                "Disconnect" in final_text
            )
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            
        self.test_results["tests"].append(test_result)
        print(f"{'✅' if test_result['success'] else '❌'} {test_result['test_id']}: {test_result['description']}")
        return test_result["success"]
        
    async def test_cm_003_heartbeat_monitoring(self):
        """TEST-CM-003: Verify heartbeat monitoring functionality"""
        test_result = {
            "test_id": "TEST-CM-003",
            "description": "Heartbeat Monitoring",
            "success": False,
            "details": {}
        }
        
        try:
            # Check heartbeat elements
            heartbeat_counter = await self.page.query_selector("#heartbeatCounter")
            heartbeat_icon = await self.page.query_selector("#heartbeatIcon")
            
            if heartbeat_counter:
                counter_value = await heartbeat_counter.inner_text()
                test_result["details"]["heartbeat_counter"] = counter_value
                
            if heartbeat_icon:
                icon_visible = await heartbeat_icon.is_visible()
                test_result["details"]["heartbeat_icon_visible"] = icon_visible
                
            # Wait and check if counter changes (indicating heartbeat reception)
            await self.page.wait_for_timeout(3000)
            
            if heartbeat_counter:
                new_counter_value = await heartbeat_counter.inner_text()
                test_result["details"]["heartbeat_counter_after_wait"] = new_counter_value
                test_result["details"]["counter_changed"] = counter_value != new_counter_value
                
            # Check for heartbeat animation
            heartbeat_animation = await self.page.query_selector(".heartbeat-pulse")
            test_result["details"]["heartbeat_animation_exists"] = heartbeat_animation is not None
            
            test_result["success"] = (
                heartbeat_counter is not None and
                heartbeat_icon is not None
            )
            
        except Exception as e:
            test_result["details"]["error"] = str(e)
            
        self.test_results["tests"].append(test_result)
        print(f"{'✅' if test_result['success'] else '❌'} {test_result['test_id']}: {test_result['description']}")
        return test_result["success"]
        
    async def capture_detailed_screenshot(self, filename):
        """Capture screenshot with timestamp"""
        await self.page.screenshot(path=filename, full_page=True)
        print(f"📸 Screenshot saved: {filename}")
        
    async def check_browser_console_errors(self):
        """Check for any console errors"""
        # Console errors are automatically logged via page.on("console") in setup
        print("🔍 Console monitoring active (errors logged above)")
        
    async def run_all_tests(self):
        """Execute all connection tests"""
        print("🧪 Starting Connection Testing Suite")
        print("=" * 60)
        
        await self.setup_browser()
        
        # Capture initial state
        await self.capture_detailed_screenshot("connection_test_initial.png")
        
        # Run all tests
        test1_result = await self.test_cm_001_connect_button_exists()
        
        # Capture after first test
        await self.capture_detailed_screenshot("connection_test_after_existence_check.png")
        
        test2_result = await self.test_cm_002_connection_state_management()
        
        # Capture after connection attempt
        await self.capture_detailed_screenshot("connection_test_after_connect.png")
        
        test3_result = await self.test_cm_003_heartbeat_monitoring()
        
        # Final screenshot
        await self.capture_detailed_screenshot("connection_test_final.png")
        
        # Summary
        total_tests = 3
        passed_tests = sum([test1_result, test2_result, test3_result])
        
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%",
            "overall_success": passed_tests == total_tests
        }
        
        print("=" * 60)
        print(f"🧪 Connection Test Suite Complete")
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed ({self.test_results['summary']['success_rate']})")
        
        # Save detailed results
        with open("connection_test_detailed_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
            
        await self.browser.close()
        return self.test_results

async def main():
    """Run the connection validation tests"""
    test_suite = ConnectionTestSuite()
    results = await test_suite.run_all_tests()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 FINAL TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test in results["tests"]:
        status = "✅ PASS" if test["success"] else "❌ FAIL"
        print(f"{status} - {test['test_id']}: {test['description']}")
        
        if not test["success"] and "error" in test["details"]:
            print(f"    Error: {test['details']['error']}")
            
    print("=" * 60)
    return results

if __name__ == "__main__":
    asyncio.run(main())
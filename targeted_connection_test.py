#!/usr/bin/env python3
"""
Targeted WebGCS Connection Test
Focus on connection functionality with actual element IDs
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


class TargetedConnectionTest:
    def __init__(self):
        self.test_url = "http://127.0.0.1:5002"
        self.virtual_drone_ip = "192.168.193.235"
        self.virtual_drone_port = "5678"
        self.results = {
            "test_start_time": datetime.now().isoformat(),
            "tests": [],
            "screenshots": []
        }
        self.screenshots_dir = Path("targeted_test_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    async def log_test_result(self, test_name: str, passed: bool, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.results["tests"].append(result)
        print(f"{'✓' if passed else '✗'} {test_name}: {details}")
        if error:
            print(f"  Error: {error}")
    
    async def take_screenshot(self, page, name: str):
        """Take screenshot for documentation"""
        screenshot_path = self.screenshots_dir / f"{name}_{int(time.time())}.png"
        await page.screenshot(path=str(screenshot_path))
        self.results["screenshots"].append(str(screenshot_path))
        return screenshot_path
    
    async def test_exact_elements(self, page):
        """Test exact elements from HTML template"""
        print("\n=== EXACT ELEMENT TESTING ===")
        
        # Connection elements (from HTML template)
        elements_to_check = {
            "IP Input": "#drone-host",
            "Port Input": "#drone-port", 
            "Connect Button": "#connect-btn",
            "Disconnect Button": "#disconnect-btn",
            "Connection Status": "#connection-status",
            "Heartbeat Counter": "#heartbeat-counter",
            "PFD Canvas": "#pfd-canvas",
            "PFD Display": "#pfd-display",
            "Map Display": "#map-display",
            "Navigation Latitude": "#nav-lat",
            "Navigation Longitude": "#nav-lon",
            "Navigation Altitude": "#nav-alt",
            "Go To Button": "#goto-btn",
            "ARM Button": "#arm-btn",
            "DISARM Button": "#disarm-btn",
            "TAKEOFF Button": "#takeoff-btn",
            "LAND Button": "#land-btn",
            "RTL Button": "#rtl-btn"
        }
        
        for element_name, selector in elements_to_check.items():
            try:
                element = page.locator(selector)
                count = await element.count()
                is_visible = await element.is_visible() if count > 0 else False
                
                await self.log_test_result(
                    f"{element_name} Present",
                    count > 0,
                    f"Element {'found and ' + ('visible' if is_visible else 'hidden') if count > 0 else 'not found'}"
                )
                
            except Exception as e:
                await self.log_test_result(
                    f"{element_name} Check",
                    False,
                    error=str(e)
                )
    
    async def test_ip_port_functionality(self, page):
        """Test IP and Port input functionality"""
        print("\n=== IP/PORT INPUT TESTING ===")
        
        try:
            # Get IP input field
            ip_field = page.locator("#drone-host")
            port_field = page.locator("#drone-port")
            
            # Check current values
            current_ip = await ip_field.input_value()
            current_port = await port_field.input_value()
            
            await self.log_test_result(
                "Current IP Value",
                True,
                f"IP field contains: '{current_ip}'"
            )
            
            await self.log_test_result(
                "Current Port Value", 
                True,
                f"Port field contains: '{current_port}'"
            )
            
            # Set values to virtual drone
            await ip_field.fill(self.virtual_drone_ip)
            await port_field.fill(self.virtual_drone_port)
            
            # Verify values were set
            new_ip = await ip_field.input_value()
            new_port = await port_field.input_value()
            
            await self.log_test_result(
                "IP Value Updated",
                new_ip == self.virtual_drone_ip,
                f"Expected: '{self.virtual_drone_ip}', Got: '{new_ip}'"
            )
            
            await self.log_test_result(
                "Port Value Updated",
                new_port == self.virtual_drone_port,
                f"Expected: '{self.virtual_drone_port}', Got: '{new_port}'"
            )
            
        except Exception as e:
            await self.log_test_result(
                "IP/Port Functionality Test",
                False,
                error=str(e)
            )
    
    async def test_connect_button_detailed(self, page):
        """Detailed connect button testing"""
        print("\n=== CONNECT BUTTON DETAILED TESTING ===")
        
        try:
            connect_btn = page.locator("#connect-btn")
            disconnect_btn = page.locator("#disconnect-btn")
            status_element = page.locator("#connection-status")
            
            # Check initial states
            connect_enabled = not await connect_btn.is_disabled()
            disconnect_enabled = not await disconnect_btn.is_disabled()
            initial_status = await status_element.text_content()
            
            await self.log_test_result(
                "Initial Connect Button State",
                connect_enabled,
                f"Connect button enabled: {connect_enabled}"
            )
            
            await self.log_test_result(
                "Initial Disconnect Button State",
                not disconnect_enabled,  # Should be disabled initially
                f"Disconnect button disabled: {not disconnect_enabled}"
            )
            
            await self.log_test_result(
                "Initial Connection Status",
                "Disconnected" in initial_status,
                f"Status text: '{initial_status}'"
            )
            
            # Take screenshot before clicking
            await self.take_screenshot(page, "before_connect_click")
            
            # Click connect button
            await connect_btn.click()
            
            # Wait for potential state changes
            await page.wait_for_timeout(2000)
            
            # Check states after click
            connect_enabled_after = not await connect_btn.is_disabled()
            disconnect_enabled_after = not await disconnect_btn.is_disabled()
            status_after = await status_element.text_content()
            
            await self.log_test_result(
                "Connect Button State After Click",
                not connect_enabled_after or "Connecting" in status_after or "Connected" in status_after,
                f"Button enabled: {connect_enabled_after}, Status: '{status_after}'"
            )
            
            # Take screenshot after clicking
            await self.take_screenshot(page, "after_connect_click")
            
            # Wait longer for connection attempt
            await page.wait_for_timeout(5000)
            
            # Check final states
            final_status = await status_element.text_content()
            final_connect_enabled = not await connect_btn.is_disabled()
            final_disconnect_enabled = not await disconnect_btn.is_disabled()
            
            await self.log_test_result(
                "Connection Attempt Result",
                "Connected" in final_status or "Connecting" in final_status or final_status != initial_status,
                f"Final status: '{final_status}'"
            )
            
            # Take final screenshot
            await self.take_screenshot(page, "final_connection_state")
            
        except Exception as e:
            await self.log_test_result(
                "Connect Button Detailed Test",
                False,
                error=str(e)
            )
    
    async def test_heartbeat_functionality(self, page):
        """Test heartbeat counter functionality"""
        print("\n=== HEARTBEAT TESTING ===")
        
        try:
            heartbeat_element = page.locator("#heartbeat-counter")
            
            # Get initial heartbeat count
            initial_text = await heartbeat_element.text_content()
            
            await self.log_test_result(
                "Heartbeat Element Present",
                "❤️" in initial_text and "Heartbeat" in initial_text,
                f"Heartbeat text: '{initial_text}'"
            )
            
            # Wait and check if heartbeat changes (indicating live updates)
            await page.wait_for_timeout(3000)
            
            after_wait_text = await heartbeat_element.text_content()
            
            await self.log_test_result(
                "Heartbeat Text Format",
                "❤️" in after_wait_text and "Heartbeat" in after_wait_text,
                f"After wait text: '{after_wait_text}'"
            )
            
            # Check if heartbeat count changed
            heartbeat_changed = initial_text != after_wait_text
            await self.log_test_result(
                "Heartbeat Count Updates",
                heartbeat_changed,
                f"Heartbeat {'changed' if heartbeat_changed else 'unchanged'}: '{initial_text}' -> '{after_wait_text}'"
            )
            
        except Exception as e:
            await self.log_test_result(
                "Heartbeat Functionality Test",
                False,
                error=str(e)
            )
    
    async def test_console_errors(self, page):
        """Monitor console for JavaScript errors"""
        print("\n=== CONSOLE ERROR TESTING ===")
        
        console_messages = []
        
        def handle_console_message(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location
            })
        
        page.on("console", handle_console_message)
        
        # Trigger some interactions to generate console activity
        try:
            connect_btn = page.locator("#connect-btn")
            await connect_btn.click()
            await page.wait_for_timeout(2000)
        except:
            pass
        
        # Analyze console messages
        errors = [msg for msg in console_messages if msg["type"] == "error"]
        warnings = [msg for msg in console_messages if msg["type"] == "warning"]
        logs = [msg for msg in console_messages if msg["type"] == "log"]
        
        await self.log_test_result(
            "JavaScript Errors",
            len(errors) == 0,
            f"Found {len(errors)} errors, {len(warnings)} warnings, {len(logs)} log messages"
        )
        
        if errors:
            for error in errors[:3]:  # Show first 3 errors
                print(f"  ERROR: {error['text']}")
    
    async def run_targeted_test(self):
        """Run all targeted tests"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                # Set viewport for consistent testing
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Load the website
                await page.goto(self.test_url, wait_until="networkidle", timeout=15000)
                
                # Take initial screenshot
                await self.take_screenshot(page, "initial_state")
                
                # Run all targeted tests
                await self.test_exact_elements(page)
                await self.test_ip_port_functionality(page)
                await self.test_connect_button_detailed(page)
                await self.test_heartbeat_functionality(page)
                await self.test_console_errors(page)
                
                await browser.close()
                
        except Exception as e:
            await self.log_test_result(
                "Test Runner",
                False,
                error=str(e)
            )
    
    def generate_report(self):
        """Generate final test report"""
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"] if test["passed"])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.results["test_end_time"] = datetime.now().isoformat()
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": round(pass_rate, 2)
        }
        
        # Save detailed results
        results_file = f"targeted_connection_test_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        print("\n" + "="*70)
        print("TARGETED WEBGCS CONNECTION TEST REPORT")
        print("="*70)
        print(f"Test URL: {self.test_url}")
        print(f"Virtual Drone: {self.virtual_drone_ip}:{self.virtual_drone_port}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Results saved: {results_file}")
        print(f"Screenshots saved in: {self.screenshots_dir}/")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for test in self.results["tests"]:
                if not test["passed"]:
                    print(f"  ✗ {test['test_name']}: {test['error'] or test['details']}")
        
        print("\n" + "="*70)
        
        return self.results


async def main():
    """Main test execution"""
    print("Starting Targeted WebGCS Connection Test...")
    print(f"Target URL: http://127.0.0.1:5002")
    print(f"Virtual Drone: 192.168.193.235:5678")
    print("-" * 70)
    
    tester = TargetedConnectionTest()
    await tester.run_targeted_test()
    results = tester.generate_report()
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
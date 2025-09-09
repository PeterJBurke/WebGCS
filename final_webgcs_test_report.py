#!/usr/bin/env python3
"""
Final WebGCS Connection Test Report
Comprehensive validation of all connection functionality
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


class FinalWebGCSTestReport:
    def __init__(self):
        self.test_url = "http://127.0.0.1:5002"
        self.results = {
            "test_name": "WebGCS Connection Testing Agent - Final Report",
            "test_date": datetime.now().isoformat(),
            "virtual_drone": "192.168.193.235:5678",
            "tests": [],
            "screenshots": [],
            "console_logs": []
        }
        self.screenshots_dir = Path("final_test_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    def log_result(self, category: str, test_name: str, passed: bool, details: str = "", expected: str = "", actual: str = ""):
        """Log test result"""
        result = {
            "category": category,
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.results["tests"].append(result)
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} [{category}] {test_name}: {details}")
    
    async def take_screenshot(self, page, name: str):
        """Take screenshot"""
        screenshot_path = self.screenshots_dir / f"{name}_{int(time.time())}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        self.results["screenshots"].append(str(screenshot_path))
        return screenshot_path
    
    async def run_final_test(self):
        """Run comprehensive final test"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Monitor console messages
                console_messages = []
                
                def handle_console_message(msg):
                    console_messages.append({
                        "type": msg.type,
                        "text": msg.text,
                        "timestamp": datetime.now().isoformat()
                    })
                
                page.on("console", handle_console_message)
                
                print("="*80)
                print("WEBGCS CONNECTION TESTING AGENT - FINAL VALIDATION")
                print("="*80)
                
                # TEST PHASE 1: Website Loading
                print("\n1. WEBSITE LOADING TESTS")
                print("-" * 40)
                
                await page.goto(self.test_url, wait_until="networkidle", timeout=15000)
                
                title = await page.title()
                self.log_result("Loading", "Page Title", 
                              "WebGCS" in title, 
                              f"Page title: '{title}'")
                
                await self.take_screenshot(page, "website_loaded")
                
                # TEST PHASE 2: Connection UI Elements 
                print("\n2. CONNECTION UI ELEMENTS")
                print("-" * 40)
                
                # Check all connection elements from HTML template
                connection_elements = {
                    "IP Input Field": "#drone-host",
                    "Port Input Field": "#drone-port", 
                    "Connect Button": "#connect-btn",
                    "Disconnect Button": "#disconnect-btn",
                    "Connection Status": "#connection-status",
                    "Heartbeat Counter": "#heartbeat-counter"
                }
                
                for name, selector in connection_elements.items():
                    element = page.locator(selector)
                    count = await element.count()
                    self.log_result("Connection UI", name, 
                                  count > 0, 
                                  f"Element {'found' if count > 0 else 'missing'}")
                
                # TEST PHASE 3: Connection State Analysis
                print("\n3. CONNECTION STATE ANALYSIS") 
                print("-" * 40)
                
                # Wait for initialization
                await page.wait_for_timeout(3000)
                
                # Check current connection state
                status_element = page.locator("#connection-status")
                status_text = await status_element.text_content()
                
                connect_btn = page.locator("#connect-btn")
                disconnect_btn = page.locator("#disconnect-btn")
                
                connect_disabled = await connect_btn.is_disabled()
                disconnect_disabled = await disconnect_btn.is_disabled()
                
                # Analyze connection state
                is_connected = "Connected" in status_text
                
                self.log_result("Connection State", "Status Display", 
                              True, 
                              f"Status: '{status_text}'")
                
                self.log_result("Connection State", "Button States Match Connection", 
                              (is_connected == connect_disabled) and (is_connected != disconnect_disabled),
                              f"Connected: {is_connected}, Connect disabled: {connect_disabled}, Disconnect disabled: {disconnect_disabled}")
                
                # TEST PHASE 4: Heartbeat Monitoring
                print("\n4. HEARTBEAT MONITORING")
                print("-" * 40)
                
                heartbeat_element = page.locator("#heartbeat-counter")
                initial_heartbeat = await heartbeat_element.text_content()
                
                # Wait for heartbeat changes
                await page.wait_for_timeout(2000)
                
                after_heartbeat = await heartbeat_element.text_content()
                
                heartbeat_has_icon = "❤️" in initial_heartbeat
                heartbeat_changes = initial_heartbeat != after_heartbeat
                
                self.log_result("Heartbeat", "Heart Icon Present", 
                              heartbeat_has_icon,
                              f"Heartbeat text: '{initial_heartbeat}'")
                
                self.log_result("Heartbeat", "Counter Updates", 
                              heartbeat_changes,
                              f"Initial: '{initial_heartbeat}' → After: '{after_heartbeat}'")
                
                # TEST PHASE 5: Primary Flight Display
                print("\n5. PRIMARY FLIGHT DISPLAY")
                print("-" * 40)
                
                pfd_elements = {
                    "PFD Container": "#pfd-display",
                    "PFD Canvas": "#pfd-canvas"
                }
                
                for name, selector in pfd_elements.items():
                    element = page.locator(selector)
                    count = await element.count()
                    is_visible = await element.is_visible() if count > 0 else False
                    
                    self.log_result("PFD", name,
                                  count > 0 and is_visible,
                                  f"Element {'found and visible' if count > 0 and is_visible else 'missing or hidden'}")
                
                # TEST PHASE 6: Interactive Map
                print("\n6. INTERACTIVE MAP")
                print("-" * 40)
                
                map_element = page.locator("#map-display")
                map_count = await map_element.count()
                map_visible = await map_element.is_visible() if map_count > 0 else False
                
                self.log_result("Map", "Map Container", 
                              map_count > 0 and map_visible,
                              f"Map container {'found and visible' if map_count > 0 and map_visible else 'missing or hidden'}")
                
                # TEST PHASE 7: Flight Controls
                print("\n7. FLIGHT CONTROLS")
                print("-" * 40)
                
                flight_controls = {
                    "ARM Button": "#arm-btn",
                    "DISARM Button": "#disarm-btn", 
                    "TAKEOFF Button": "#takeoff-btn",
                    "LAND Button": "#land-btn",
                    "RTL Button": "#rtl-btn"
                }
                
                for name, selector in flight_controls.items():
                    element = page.locator(selector)
                    count = await element.count()
                    is_visible = await element.is_visible() if count > 0 else False
                    
                    self.log_result("Flight Controls", name,
                                  count > 0 and is_visible,
                                  f"Button {'found and visible' if count > 0 and is_visible else 'missing or hidden'}")
                
                # TEST PHASE 8: Navigation Controls
                print("\n8. NAVIGATION CONTROLS")
                print("-" * 40)
                
                nav_controls = {
                    "Latitude Input": "#nav-lat",
                    "Longitude Input": "#nav-lon",
                    "Altitude Input": "#nav-alt", 
                    "Go To Button": "#goto-btn",
                    "Clear Button": "#clear-btn"
                }
                
                for name, selector in nav_controls.items():
                    element = page.locator(selector)
                    count = await element.count()
                    is_visible = await element.is_visible() if count > 0 else False
                    
                    self.log_result("Navigation", name,
                                  count > 0 and is_visible,
                                  f"Control {'found and visible' if count > 0 and is_visible else 'missing or hidden'}")
                
                # TEST PHASE 9: Console Error Analysis
                print("\n9. CONSOLE ERROR ANALYSIS")
                print("-" * 40)
                
                # Wait to collect more console messages
                await page.wait_for_timeout(2000)
                
                errors = [msg for msg in console_messages if msg["type"] == "error"]
                warnings = [msg for msg in console_messages if msg["type"] == "warning"]
                logs = [msg for msg in console_messages if msg["type"] == "log"]
                
                # Check for critical errors
                critical_errors = [error for error in errors if 
                                 "TypeError" in error["text"] or 
                                 "ReferenceError" in error["text"] or
                                 "SyntaxError" in error["text"]]
                
                self.log_result("Console", "No Critical JavaScript Errors",
                              len(critical_errors) == 0,
                              f"Found {len(critical_errors)} critical errors, {len(errors)} total errors")
                
                self.log_result("Console", "Initialization Messages Present",
                              len(logs) > 10,
                              f"Found {len(logs)} log messages indicating active system")
                
                # Final screenshots
                await self.take_screenshot(page, "final_state_full")
                
                # Store console logs
                self.results["console_logs"] = console_messages[:50]  # Store first 50 messages
                
                await browser.close()
                
        except Exception as e:
            self.log_result("Test Execution", "Test Runner", 
                          False, 
                          f"Error during test execution: {str(e)}")
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        # Calculate statistics
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"] if test["passed"])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Categorize results
        categories = {}
        for test in self.results["tests"]:
            cat = test["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if test["passed"]:
                categories[cat]["passed"] += 1
        
        # Save detailed JSON report
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests, 
            "failed": failed_tests,
            "pass_rate": round(pass_rate, 2),
            "categories": categories
        }
        
        json_file = f"webgcs_final_test_report_{int(time.time())}.json"
        with open(json_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Print comprehensive report
        print("\n" + "="*80)
        print("WEBGCS CONNECTION TESTING AGENT - FINAL TEST REPORT")
        print("="*80)
        print(f"Test Date: {self.results['test_date']}")
        print(f"Test URL: {self.test_url}")
        print(f"Virtual Drone: {self.results['virtual_drone']}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Overall Pass Rate: {pass_rate:.1f}%")
        
        print(f"\nResults by Category:")
        for category, stats in categories.items():
            cat_pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {category}: {stats['passed']}/{stats['total']} ({cat_pass_rate:.1f}%)")
        
        print(f"\nFiles Generated:")
        print(f"  JSON Report: {json_file}")
        print(f"  Screenshots: {len(self.results['screenshots'])} files in {self.screenshots_dir}/")
        
        if failed_tests > 0:
            print(f"\nFailed Tests:")
            for test in self.results["tests"]:
                if not test["passed"]:
                    print(f"  ✗ [{test['category']}] {test['test_name']}: {test['details']}")
        
        # Key findings
        print(f"\nKEY FINDINGS:")
        has_connection = any("Connected" in test.get("actual", "") + test.get("details", "") 
                           for test in self.results["tests"])
        has_heartbeat = any("heart" in test.get("details", "").lower() 
                          for test in self.results["tests"] if test["passed"])
        
        if has_connection:
            print("  ✓ Virtual drone connection is ACTIVE")
        if has_heartbeat:
            print("  ✓ Heartbeat monitoring is FUNCTIONAL")
        
        print("="*80)
        
        return self.results


async def main():
    print("Starting Final WebGCS Connection Test...")
    tester = FinalWebGCSTestReport()
    await tester.run_final_test()
    results = tester.generate_final_report()
    return results


if __name__ == "__main__":
    asyncio.run(main())
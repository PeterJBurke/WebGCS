#!/usr/bin/env python3
"""
Comprehensive WebGCS Functionality Test
Connection Testing Agent - Validates all connection and UI functionality
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


class WebGCSFunctionalityTest:
    def __init__(self):
        self.test_url = "http://127.0.0.1:5002"
        self.virtual_drone_ip = "192.168.193.235"
        self.virtual_drone_port = "5678"
        self.results = {
            "test_start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0
            }
        }
        self.screenshots_dir = Path("test_screenshots")
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
        return screenshot_path
    
    async def test_website_loading(self, page):
        """TEST-CM-001: Website Loading and Basic Elements"""
        try:
            print("\n=== TEST-CM-001: Website Loading ===")
            
            # Load the website
            await page.goto(self.test_url, wait_until="networkidle", timeout=10000)
            await self.take_screenshot(page, "website_loaded")
            
            # Check page title
            title = await page.title()
            await self.log_test_result(
                "Website Title Check",
                "WebGCS" in title,
                f"Page title: '{title}'"
            )
            
            # Check for main container
            main_container = await page.locator("#main-container, .main-container, body").count()
            await self.log_test_result(
                "Main Container Present",
                main_container > 0,
                "Main container element found"
            )
            
        except Exception as e:
            await self.log_test_result(
                "Website Loading",
                False,
                error=str(e)
            )
    
    async def test_connection_elements(self, page):
        """TEST-CM-002: Connection UI Elements"""
        try:
            print("\n=== TEST-CM-002: Connection Elements ===")
            
            # Look for connect button with various possible selectors
            connect_selectors = [
                "#connect-btn",
                "#connectBtn", 
                "button:has-text('Connect')",
                "input[value='Connect']",
                "[data-action='connect']",
                ".connect-button"
            ]
            
            connect_button = None
            for selector in connect_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        connect_button = button
                        break
                except:
                    continue
            
            if connect_button:
                await self.log_test_result(
                    "Connect Button Found",
                    True,
                    "Connect button located in UI"
                )
                
                # Check if button is enabled
                is_enabled = not await connect_button.is_disabled()
                await self.log_test_result(
                    "Connect Button Enabled",
                    is_enabled,
                    f"Button enabled state: {is_enabled}"
                )
            else:
                await self.log_test_result(
                    "Connect Button Found",
                    False,
                    "Connect button not found with any selector"
                )
            
            # Look for IP/Port input fields
            ip_selectors = [
                "#ip-address",
                "#droneIp",
                "input[placeholder*='IP']",
                "input[name*='ip']",
                "#ip"
            ]
            
            ip_field = None
            for selector in ip_selectors:
                try:
                    field = page.locator(selector)
                    if await field.count() > 0:
                        ip_field = field
                        break
                except:
                    continue
            
            if ip_field:
                ip_value = await ip_field.input_value()
                await self.log_test_result(
                    "IP Address Field",
                    self.virtual_drone_ip in ip_value or ip_value == "",
                    f"IP field value: '{ip_value}'"
                )
            
            # Look for port field
            port_selectors = [
                "#port",
                "#dronePort", 
                "input[placeholder*='Port']",
                "input[name*='port']"
            ]
            
            port_field = None
            for selector in port_selectors:
                try:
                    field = page.locator(selector)
                    if await field.count() > 0:
                        port_field = field
                        break
                except:
                    continue
            
            if port_field:
                port_value = await port_field.input_value()
                await self.log_test_result(
                    "Port Field",
                    self.virtual_drone_port in port_value or port_value == "",
                    f"Port field value: '{port_value}'"
                )
            
        except Exception as e:
            await self.log_test_result(
                "Connection Elements Check",
                False,
                error=str(e)
            )
    
    async def test_pfd_display(self, page):
        """TEST-CM-003: PFD Display Elements"""
        try:
            print("\n=== TEST-CM-003: PFD Display ===")
            
            # Look for PFD container
            pfd_selectors = [
                "#pfd",
                "#pfd-container",
                ".pfd",
                ".primary-flight-display",
                "canvas#pfd"
            ]
            
            pfd_found = False
            for selector in pfd_selectors:
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        pfd_found = True
                        break
                except:
                    continue
            
            await self.log_test_result(
                "PFD Display Present",
                pfd_found,
                "Primary Flight Display container found" if pfd_found else "PFD not found"
            )
            
            # Look for telemetry indicators
            telemetry_indicators = [
                "altitude", "airspeed", "heading", "gps", "battery"
            ]
            
            for indicator in telemetry_indicators:
                selectors = [
                    f"#{indicator}",
                    f".{indicator}",
                    f"[data-telemetry='{indicator}']",
                    f"*:has-text('{indicator.title()}')"
                ]
                
                found = False
                for selector in selectors:
                    try:
                        element = page.locator(selector)
                        if await element.count() > 0:
                            found = True
                            break
                    except:
                        continue
                
                await self.log_test_result(
                    f"Telemetry {indicator.title()} Indicator",
                    found,
                    f"{indicator.title()} indicator {'found' if found else 'not found'}"
                )
            
        except Exception as e:
            await self.log_test_result(
                "PFD Display Check",
                False,
                error=str(e)
            )
    
    async def test_map_display(self, page):
        """TEST-CM-004: Map Display Elements"""
        try:
            print("\n=== TEST-CM-004: Map Display ===")
            
            # Look for map container
            map_selectors = [
                "#map",
                "#mapContainer",
                ".map-container",
                ".leaflet-container",
                "#interactive-map"
            ]
            
            map_found = False
            for selector in map_selectors:
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        map_found = True
                        break
                except:
                    continue
            
            await self.log_test_result(
                "Map Container Present",
                map_found,
                "Map container found" if map_found else "Map container not found"
            )
            
        except Exception as e:
            await self.log_test_result(
                "Map Display Check",
                False,
                error=str(e)
            )
    
    async def test_flight_controls(self, page):
        """TEST-CM-005: Flight Control Buttons"""
        try:
            print("\n=== TEST-CM-005: Flight Controls ===")
            
            # Flight control buttons to look for
            control_buttons = {
                "ARM": ["#arm-btn", "#armBtn", "button:has-text('ARM')", "[data-action='arm']"],
                "DISARM": ["#disarm-btn", "#disarmBtn", "button:has-text('DISARM')", "[data-action='disarm']"],
                "TAKEOFF": ["#takeoff-btn", "#takeoffBtn", "button:has-text('TAKEOFF')", "[data-action='takeoff']"],
                "LAND": ["#land-btn", "#landBtn", "button:has-text('LAND')", "[data-action='land']"],
                "RTL": ["#rtl-btn", "#rtlBtn", "button:has-text('RTL')", "[data-action='rtl']"]
            }
            
            for button_name, selectors in control_buttons.items():
                found = False
                for selector in selectors:
                    try:
                        element = page.locator(selector)
                        if await element.count() > 0:
                            found = True
                            break
                    except:
                        continue
                
                await self.log_test_result(
                    f"{button_name} Button Present",
                    found,
                    f"{button_name} button {'found' if found else 'not found'}"
                )
            
        except Exception as e:
            await self.log_test_result(
                "Flight Controls Check",
                False,
                error=str(e)
            )
    
    async def test_navigation_controls(self, page):
        """TEST-CM-006: Navigation Controls"""
        try:
            print("\n=== TEST-CM-006: Navigation Controls ===")
            
            # Navigation elements to look for
            nav_elements = {
                "Latitude Input": ["#latitude", "#lat", "input[placeholder*='Lat']"],
                "Longitude Input": ["#longitude", "#lng", "input[placeholder*='Lon']"],
                "Altitude Input": ["#altitude", "#alt", "input[placeholder*='Alt']"],
                "Go To Button": ["#goto-btn", "#goToBtn", "button:has-text('Go')", "[data-action='goto']"]
            }
            
            for element_name, selectors in nav_elements.items():
                found = False
                for selector in selectors:
                    try:
                        element = page.locator(selector)
                        if await element.count() > 0:
                            found = True
                            break
                    except:
                        continue
                
                await self.log_test_result(
                    element_name,
                    found,
                    f"{element_name} {'found' if found else 'not found'}"
                )
            
        except Exception as e:
            await self.log_test_result(
                "Navigation Controls Check",
                False,
                error=str(e)
            )
    
    async def test_connection_functionality(self, page):
        """TEST-CM-007: Connection Button Click Test"""
        try:
            print("\n=== TEST-CM-007: Connection Functionality ===")
            
            # Find connect button
            connect_selectors = [
                "#connect-btn",
                "#connectBtn", 
                "button:has-text('Connect')",
                "input[value='Connect']",
                "[data-action='connect']",
                ".connect-button"
            ]
            
            connect_button = None
            for selector in connect_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        connect_button = button
                        break
                except:
                    continue
            
            if connect_button:
                # Take screenshot before clicking
                await self.take_screenshot(page, "before_connect_click")
                
                # Set IP and port if fields exist
                ip_field = None
                port_field = None
                
                for selector in ["#ip-address", "#droneIp", "input[placeholder*='IP']"]:
                    try:
                        field = page.locator(selector)
                        if await field.count() > 0:
                            ip_field = field
                            break
                    except:
                        continue
                
                for selector in ["#port", "#dronePort", "input[placeholder*='Port']"]:
                    try:
                        field = page.locator(selector)
                        if await field.count() > 0:
                            port_field = field
                            break
                    except:
                        continue
                
                if ip_field:
                    await ip_field.fill(self.virtual_drone_ip)
                if port_field:
                    await port_field.fill(self.virtual_drone_port)
                
                # Click connect button
                await connect_button.click()
                
                # Wait a moment for connection attempt
                await page.wait_for_timeout(3000)
                
                # Take screenshot after clicking
                await self.take_screenshot(page, "after_connect_click")
                
                # Check for connection status changes
                button_text = await connect_button.text_content() or await connect_button.get_attribute("value") or ""
                
                connection_attempted = (
                    "Connecting" in button_text or 
                    "Connected" in button_text or
                    "Disconnect" in button_text or
                    await connect_button.is_disabled()
                )
                
                await self.log_test_result(
                    "Connect Button Click Response",
                    connection_attempted,
                    f"Button text after click: '{button_text}'"
                )
                
                # Look for heartbeat indicators
                heartbeat_selectors = [
                    ".heartbeat",
                    "#heartbeat",
                    "*:has-text('❤️')",
                    ".heart-icon",
                    "[data-heartbeat]"
                ]
                
                heartbeat_found = False
                for selector in heartbeat_selectors:
                    try:
                        element = page.locator(selector)
                        if await element.count() > 0:
                            heartbeat_found = True
                            break
                    except:
                        continue
                
                await self.log_test_result(
                    "Heartbeat Indicator",
                    heartbeat_found,
                    "Heartbeat indicator found" if heartbeat_found else "No heartbeat indicator found"
                )
                
            else:
                await self.log_test_result(
                    "Connect Button Click Test",
                    False,
                    "Connect button not found, cannot test click functionality"
                )
                
        except Exception as e:
            await self.log_test_result(
                "Connection Functionality Test",
                False,
                error=str(e)
            )
    
    async def test_status_indicators(self, page):
        """TEST-CM-008: Status Indicators"""
        try:
            print("\n=== TEST-CM-008: Status Indicators ===")
            
            # Connection status indicators
            status_selectors = [
                "#connection-status",
                ".connection-status", 
                "#status",
                ".status-indicator"
            ]
            
            status_found = False
            for selector in status_selectors:
                try:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        status_found = True
                        break
                except:
                    continue
            
            await self.log_test_result(
                "Connection Status Indicator",
                status_found,
                "Connection status indicator found" if status_found else "No status indicator found"
            )
            
            # Look for system status elements
            system_elements = [
                "GPS", "Battery", "Armed", "Mode", "Altitude", "Speed"
            ]
            
            for element in system_elements:
                found = False
                selectors = [
                    f"*:has-text('{element}')",
                    f"#{element.lower()}",
                    f".{element.lower()}-status"
                ]
                
                for selector in selectors:
                    try:
                        elem = page.locator(selector)
                        if await elem.count() > 0:
                            found = True
                            break
                    except:
                        continue
                
                await self.log_test_result(
                    f"{element} Status Element",
                    found,
                    f"{element} status {'found' if found else 'not found'}"
                )
            
        except Exception as e:
            await self.log_test_result(
                "Status Indicators Check",
                False,
                error=str(e)
            )
    
    async def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                page = await browser.new_page()
                
                # Set viewport for consistent testing
                await page.set_viewport_size({"width": 1920, "height": 1080})
                
                # Run all test phases
                await self.test_website_loading(page)
                await self.test_connection_elements(page)
                await self.test_pfd_display(page)
                await self.test_map_display(page)
                await self.test_flight_controls(page)
                await self.test_navigation_controls(page)
                await self.test_connection_functionality(page)
                await self.test_status_indicators(page)
                
                # Final screenshot
                await self.take_screenshot(page, "final_test_state")
                
                await browser.close()
                
        except Exception as e:
            await self.log_test_result(
                "Test Runner",
                False,
                error=str(e)
            )
    
    def generate_report(self):
        """Generate final test report"""
        # Calculate summary
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"] if test["passed"])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "pass_rate": round(pass_rate, 2)
        }
        
        self.results["test_end_time"] = datetime.now().isoformat()
        
        # Save detailed results
        results_file = f"webgcs_functionality_test_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("WebGCS COMPREHENSIVE FUNCTIONALITY TEST REPORT")
        print("="*60)
        print(f"Test URL: {self.test_url}")
        print(f"Virtual Drone: {self.virtual_drone_ip}:{self.virtual_drone_port}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Results saved: {results_file}")
        print("Screenshots saved in: test_screenshots/")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for test in self.results["tests"]:
                if not test["passed"]:
                    print(f"  ✗ {test['test_name']}: {test['error'] or test['details']}")
        
        print("\n" + "="*60)
        
        return self.results


async def main():
    """Main test execution"""
    print("Starting WebGCS Comprehensive Functionality Test...")
    print(f"Target URL: http://127.0.0.1:5002")
    print(f"Virtual Drone: 192.168.193.235:5678")
    print("-" * 60)
    
    tester = WebGCSFunctionalityTest()
    await tester.run_comprehensive_test()
    results = tester.generate_report()
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
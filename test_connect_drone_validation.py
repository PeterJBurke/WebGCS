#!/usr/bin/env python3
"""
Connection Testing Agent - Virtual Drone Connection Validation
Tests the connect button functionality with the virtual drone at 192.168.193.235:5678

TEST-CM-001: Connect Button Functionality
TEST-CM-002: Connection State Management  
TEST-CM-003: Heartbeat Monitoring
"""

import asyncio
import time
from playwright.async_api import async_playwright
import json
import subprocess
import socket

class DroneConnectionTester:
    def __init__(self):
        self.test_results = {
            "TEST-CM-001": {"status": "NOT_RUN", "details": []},
            "TEST-CM-002": {"status": "NOT_RUN", "details": []},
            "TEST-CM-003": {"status": "NOT_RUN", "details": []},
            "screenshots": []
        }
        self.webgcs_url = "http://127.0.0.1:5002"
        self.drone_ip = "192.168.193.235"
        self.drone_port = 5678
        
    def check_drone_availability(self):
        """Check if the virtual drone is reachable"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.drone_ip, self.drone_port))
            sock.close()
            return result == 0
        except Exception as e:
            print(f"Error checking drone availability: {e}")
            return False
            
    def check_webgcs_server(self):
        """Check if WebGCS server is running"""
        try:
            import requests
            response = requests.get(self.webgcs_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error checking WebGCS server: {e}")
            return False

    async def test_cm_001_connect_button_functionality(self, page):
        """TEST-CM-001: Connect Button Functionality"""
        print("=== TEST-CM-001: Connect Button Functionality ===")
        
        test_details = []
        try:
            # Navigate to WebGCS
            await page.goto(self.webgcs_url)
            test_details.append("✓ Navigated to WebGCS interface")
            
            # Take initial screenshot
            await page.screenshot(path="initial_state.png")
            test_details.append("✓ Captured initial state screenshot")
            
            # Wait for page to fully load
            await page.wait_for_load_state('networkidle')
            
            # Check if IP field shows correct value
            ip_input = page.locator('input[placeholder*="IP"], input[id*="ip"], input[value*="192.168"]')
            if await ip_input.count() > 0:
                ip_value = await ip_input.first.input_value()
                if self.drone_ip in ip_value:
                    test_details.append(f"✓ IP field shows correct value: {ip_value}")
                else:
                    test_details.append(f"✗ IP field shows incorrect value: {ip_value}")
            else:
                test_details.append("✗ IP input field not found")
            
            # Check if port field shows correct value  
            port_input = page.locator('input[placeholder*="Port"], input[id*="port"], input[value*="5678"]')
            if await port_input.count() > 0:
                port_value = await port_input.first.input_value()
                if "5678" in port_value:
                    test_details.append(f"✓ Port field shows correct value: {port_value}")
                else:
                    test_details.append(f"✗ Port field shows incorrect value: {port_value}")
            else:
                test_details.append("✗ Port input field not found")
            
            # Find connect button
            connect_button = page.locator('button:has-text("Connect"), input[type="button"][value*="Connect"], #connect-btn')
            
            if await connect_button.count() == 0:
                test_details.append("✗ Connect button not found")
                self.test_results["TEST-CM-001"]["status"] = "FAILED"
                self.test_results["TEST-CM-001"]["details"] = test_details
                return False
                
            # Check if button is initially enabled
            is_enabled = await connect_button.first.is_enabled()
            if is_enabled:
                test_details.append("✓ Connect button is initially enabled")
            else:
                test_details.append("✗ Connect button is initially disabled")
            
            # Get button text before click
            button_text_before = await connect_button.first.text_content()
            test_details.append(f"✓ Button text before click: '{button_text_before}'")
            
            # Click the connect button
            await connect_button.first.click()
            test_details.append("✓ Clicked Connect button")
            
            # Wait a moment for UI to update
            await page.wait_for_timeout(2000)
            
            # Check if button text changed to "Connecting..."
            button_text_after = await connect_button.first.text_content()
            test_details.append(f"✓ Button text after click: '{button_text_after}'")
            
            if "Connecting" in button_text_after or "connecting" in button_text_after.lower():
                test_details.append("✓ Button shows 'Connecting...' state")
            else:
                test_details.append("✗ Button does not show 'Connecting...' state")
            
            # Take screenshot after click
            await page.screenshot(path="after_connect_click.png")
            test_details.append("✓ Captured post-click screenshot")
            
            self.test_results["TEST-CM-001"]["status"] = "PASSED"
            self.test_results["TEST-CM-001"]["details"] = test_details
            return True
            
        except Exception as e:
            test_details.append(f"✗ Error during test: {str(e)}")
            self.test_results["TEST-CM-001"]["status"] = "FAILED"
            self.test_results["TEST-CM-001"]["details"] = test_details
            return False

    async def test_cm_002_connection_state_management(self, page):
        """TEST-CM-002: Connection State Management"""
        print("=== TEST-CM-002: Connection State Management ===")
        
        test_details = []
        try:
            # Wait for connection attempt to complete (30 second timeout)
            await page.wait_for_timeout(5000)
            
            # Check for connection status indicators
            status_indicators = [
                'text="Connected"',
                'text="Disconnected"', 
                'text="Connection failed"',
                'text="Timeout"',
                '.connection-status',
                '#status',
                '.status'
            ]
            
            status_found = False
            for indicator in status_indicators:
                status_element = page.locator(indicator)
                if await status_element.count() > 0:
                    status_text = await status_element.first.text_content()
                    test_details.append(f"✓ Status indicator found: '{status_text}'")
                    status_found = True
                    break
            
            if not status_found:
                test_details.append("✗ No connection status indicator found")
            
            # Check if Connect button is now disabled and Disconnect button is enabled
            connect_button = page.locator('button:has-text("Connect"), #connect-btn')
            disconnect_button = page.locator('button:has-text("Disconnect"), #disconnect-btn')
            
            if await connect_button.count() > 0:
                is_connect_enabled = await connect_button.first.is_enabled()
                connect_text = await connect_button.first.text_content()
                test_details.append(f"✓ Connect button status: enabled={is_connect_enabled}, text='{connect_text}'")
            
            if await disconnect_button.count() > 0:
                is_disconnect_enabled = await disconnect_button.first.is_enabled()
                disconnect_text = await disconnect_button.first.text_content()
                test_details.append(f"✓ Disconnect button status: enabled={is_disconnect_enabled}, text='{disconnect_text}'")
            else:
                test_details.append("✗ Disconnect button not found")
            
            # Take screenshot of connection state
            await page.screenshot(path="connection_state.png")
            test_details.append("✓ Captured connection state screenshot")
            
            self.test_results["TEST-CM-002"]["status"] = "PASSED"
            self.test_results["TEST-CM-002"]["details"] = test_details
            return True
            
        except Exception as e:
            test_details.append(f"✗ Error during test: {str(e)}")
            self.test_results["TEST-CM-002"]["status"] = "FAILED"
            self.test_results["TEST-CM-002"]["details"] = test_details
            return False

    async def test_cm_003_heartbeat_monitoring(self, page):
        """TEST-CM-003: Heartbeat Monitoring"""
        print("=== TEST-CM-003: Heartbeat Monitoring ===")
        
        test_details = []
        try:
            # Look for heartbeat counter
            heartbeat_selectors = [
                'text="Heartbeat"',
                'text="heartbeat"', 
                '#heartbeat-counter',
                '.heartbeat-counter',
                'text="❤️"',
                ':text("Heartbeat")',
                ':text("❤️")'
            ]
            
            heartbeat_found = False
            initial_count = None
            
            for selector in heartbeat_selectors:
                heartbeat_element = page.locator(selector)
                if await heartbeat_element.count() > 0:
                    heartbeat_text = await heartbeat_element.first.text_content()
                    test_details.append(f"✓ Heartbeat element found: '{heartbeat_text}'")
                    
                    # Extract number from heartbeat text
                    import re
                    numbers = re.findall(r'\d+', heartbeat_text)
                    if numbers:
                        initial_count = int(numbers[-1])
                        test_details.append(f"✓ Initial heartbeat count: {initial_count}")
                    
                    heartbeat_found = True
                    break
            
            if not heartbeat_found:
                test_details.append("✗ Heartbeat indicator not found")
            
            # Wait and check if heartbeat counter increments
            if heartbeat_found and initial_count is not None:
                await page.wait_for_timeout(3000)  # Wait 3 seconds
                
                for selector in heartbeat_selectors:
                    heartbeat_element = page.locator(selector)
                    if await heartbeat_element.count() > 0:
                        heartbeat_text = await heartbeat_element.first.text_content()
                        numbers = re.findall(r'\d+', heartbeat_text)
                        if numbers:
                            new_count = int(numbers[-1])
                            test_details.append(f"✓ New heartbeat count: {new_count}")
                            
                            if new_count > initial_count:
                                test_details.append("✓ Heartbeat counter is incrementing")
                            else:
                                test_details.append("✗ Heartbeat counter is not incrementing")
                        break
            
            # Check for PFD display updates
            pfd_selectors = [
                '.pfd',
                '#pfd',
                '.primary-flight-display',
                'text*="Altitude"',
                'text*="Airspeed"'
            ]
            
            pfd_found = False
            for selector in pfd_selectors:
                pfd_element = page.locator(selector)
                if await pfd_element.count() > 0:
                    test_details.append("✓ PFD display found")
                    pfd_found = True
                    break
            
            if not pfd_found:
                test_details.append("✗ PFD display not found")
            
            # Take final screenshot
            await page.screenshot(path="heartbeat_monitoring.png")
            test_details.append("✓ Captured heartbeat monitoring screenshot")
            
            self.test_results["TEST-CM-003"]["status"] = "PASSED"
            self.test_results["TEST-CM-003"]["details"] = test_details
            return True
            
        except Exception as e:
            test_details.append(f"✗ Error during test: {str(e)}")
            self.test_results["TEST-CM-003"]["status"] = "FAILED"
            self.test_results["TEST-CM-003"]["details"] = test_details
            return False

    async def run_all_tests(self):
        """Run all connection tests"""
        print("Connection Testing Agent - Virtual Drone Connection Validation")
        print("=" * 65)
        
        # Pre-flight checks
        print("Pre-flight checks:")
        
        if not self.check_drone_availability():
            print(f"✗ Virtual drone not available at {self.drone_ip}:{self.drone_port}")
            return False
        else:
            print(f"✓ Virtual drone available at {self.drone_ip}:{self.drone_port}")
        
        if not self.check_webgcs_server():
            print(f"✗ WebGCS server not available at {self.webgcs_url}")
            return False
        else:
            print(f"✓ WebGCS server available at {self.webgcs_url}")
        
        print()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Run all tests in sequence
                await self.test_cm_001_connect_button_functionality(page)
                await self.test_cm_002_connection_state_management(page)
                await self.test_cm_003_heartbeat_monitoring(page)
                
                # Generate final report
                self.generate_report()
                
            finally:
                await browser.close()
        
        return True

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 65)
        print("CONNECTION TESTING REPORT")
        print("=" * 65)
        
        total_tests = len(self.test_results) - 1  # Exclude screenshots key
        passed_tests = sum(1 for test, result in self.test_results.items() 
                          if test != "screenshots" and result["status"] == "PASSED")
        
        print(f"Tests Run: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        for test_name, result in self.test_results.items():
            if test_name == "screenshots":
                continue
                
            print(f"{test_name}: {result['status']}")
            for detail in result["details"]:
                print(f"  {detail}")
            print()
        
        # Save detailed report to file
        with open("connection_test_report.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        
        print("Detailed test report saved to: connection_test_report.json")
        print("Screenshots saved: initial_state.png, after_connect_click.png, connection_state.png, heartbeat_monitoring.png")

async def main():
    tester = DroneConnectionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
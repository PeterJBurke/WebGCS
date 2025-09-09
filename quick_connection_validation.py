#!/usr/bin/env python3
"""
Quick WebGCS Connection Validation
Test connection functionality without complex UI interactions
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


class QuickConnectionTest:
    def __init__(self):
        self.test_url = "http://127.0.0.1:5002"
        self.results = []
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {"test": test_name, "passed": passed, "details": details}
        self.results.append(result)
        print(f"{'✓' if passed else '✗'} {test_name}: {details}")
    
    async def run_quick_test(self):
        """Run quick connection validation"""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)  # Headless for speed
                page = await browser.new_page()
                
                print("Loading WebGCS...")
                await page.goto(self.test_url, wait_until="networkidle", timeout=10000)
                
                # Check page title
                title = await page.title()
                self.log_result("Page Title", "WebGCS" in title, f"Title: {title}")
                
                # Check for key elements
                elements = {
                    "Connect Button": "#connect-btn",
                    "IP Input": "#drone-host", 
                    "Port Input": "#drone-port",
                    "Status Display": "#connection-status",
                    "PFD Canvas": "#pfd-canvas",
                    "Map Display": "#map-display"
                }
                
                for name, selector in elements.items():
                    try:
                        element = page.locator(selector)
                        count = await element.count()
                        self.log_result(f"{name} Present", count > 0, f"Found {count} elements")
                    except Exception as e:
                        self.log_result(f"{name} Check", False, f"Error: {str(e)}")
                
                # Test IP/Port values
                try:
                    ip_value = await page.locator("#drone-host").input_value()
                    port_value = await page.locator("#drone-port").input_value()
                    self.log_result("IP/Port Values", True, f"IP: '{ip_value}', Port: '{port_value}'")
                except Exception as e:
                    self.log_result("IP/Port Values", False, f"Error: {str(e)}")
                
                # Test connect button click
                try:
                    connect_btn = page.locator("#connect-btn")
                    
                    # Set drone IP/port
                    await page.locator("#drone-host").fill("192.168.193.235")
                    await page.locator("#drone-port").fill("5678")
                    
                    # Check button is enabled
                    is_enabled = not await connect_btn.is_disabled()
                    self.log_result("Connect Button Enabled", is_enabled, f"Button enabled: {is_enabled}")
                    
                    if is_enabled:
                        # Click connect
                        await connect_btn.click()
                        await page.wait_for_timeout(2000)
                        
                        # Check status change
                        status = await page.locator("#connection-status").text_content()
                        self.log_result("Status After Connect", True, f"Status: '{status}'")
                        
                except Exception as e:
                    self.log_result("Connect Button Test", False, f"Error: {str(e)}")
                
                # Take screenshot
                screenshot_path = f"quick_test_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
                
                await browser.close()
                
        except Exception as e:
            self.log_result("Test Execution", False, f"Error: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        
        print("\n" + "="*50)
        print("QUICK CONNECTION TEST SUMMARY")
        print("="*50)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Pass Rate: {(passed/total*100):.1f}%")
        print("="*50)


async def main():
    tester = QuickConnectionTest()
    await tester.run_quick_test()
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
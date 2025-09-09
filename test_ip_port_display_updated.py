#!/usr/bin/env python3
"""
TEST-CM-ENV-001: Environment Variable Display Test (Updated)
Test that the website properly displays IP address and port from .env file
"""

import asyncio
import os
from playwright.async_api import async_playwright
import json
from datetime import datetime

class IPPortDisplayTest:
    def __init__(self):
        self.test_url = "http://127.0.0.1:5001"  # Default from .env
        self.fallback_url = "http://127.0.0.1:5002"  # User mentioned this port
        self.results = {
            "test_id": "TEST-CM-ENV-001",
            "test_name": "IP/Port Display from Environment Variables",
            "timestamp": datetime.now().isoformat(),
            "expected_ip": "192.168.193.235",
            "expected_port": "5678",
            "actual_ip": None,
            "actual_port": None,
            "tests_passed": 0,
            "tests_failed": 0,
            "details": []
        }

    async def run_test(self):
        print("🧪 TEST-CM-ENV-001: Environment Variable Display Test")
        print("=" * 60)
        
        # First check .env file values
        await self.verify_env_file()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context(
                viewport={"width": 1400, "height": 900}
            )
            page = await context.new_page()
            
            # Try primary URL first, then fallback
            success = await self.try_connect_url(page, self.test_url)
            if not success:
                print(f"⚠️  Primary URL {self.test_url} failed, trying fallback...")
                success = await self.try_connect_url(page, self.fallback_url)
                if success:
                    self.test_url = self.fallback_url
            
            if not success:
                self.add_failure("URL_ACCESS", "Cannot access either URL")
                await browser.close()
                return
            
            # Wait for page to fully load
            await page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(2)  # Extra wait
            
            # Test IP field value
            await self.test_ip_field_value(page)
            
            # Test Port field value  
            await self.test_port_field_value(page)
            
            # Take screenshot showing the values
            await self.take_verification_screenshot(page)
            
            # Report exact values found
            await self.report_displayed_values(page)
            
            await browser.close()
        
        # Generate test report
        self.generate_report()

    async def verify_env_file(self):
        """Verify .env file contains expected values"""
        try:
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    env_content = f.read()
                
                has_ip = "DRONE_TCP_ADDRESS=192.168.193.235" in env_content
                has_port = "DRONE_TCP_PORT=5678" in env_content
                
                if has_ip and has_port:
                    self.add_success("ENV_FILE", "Environment file contains correct IP and Port")
                    print(f"✅ .env file contains: IP=192.168.193.235, Port=5678")
                else:
                    self.add_failure("ENV_FILE", f"Environment file missing values. Has IP: {has_ip}, Has Port: {has_port}")
            else:
                self.add_failure("ENV_FILE", ".env file not found")
        except Exception as e:
            self.add_failure("ENV_FILE", f"Error reading .env file: {str(e)}")

    async def try_connect_url(self, page, url):
        """Try to connect to a URL and return success status"""
        try:
            print(f"🔍 Trying to connect to {url}...")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            if response and response.status == 200:
                print(f"✅ Successfully connected to {url}")
                return True
            else:
                status = response.status if response else "No response"
                print(f"❌ HTTP {status} from {url}")
                return False
        except Exception as e:
            print(f"❌ Failed to connect to {url}: {str(e)}")
            return False

    async def test_ip_field_value(self, page):
        """Test that IP field displays correct value from .env"""
        try:
            print("\n🧪 Testing IP field value...")
            
            # Wait for connection panel to load - using class selector
            await page.wait_for_selector('.connection-panel', timeout=10000)
            
            # Look for the specific IP input field
            ip_field = await page.query_selector('#drone-host')
            
            if ip_field:
                ip_value = await ip_field.get_attribute('value')
                self.results["actual_ip"] = ip_value
                print(f"📍 Found IP field (#drone-host) with value: '{ip_value}'")
                
                if ip_value == "192.168.193.235":
                    self.add_success("IP_FIELD", f"IP field displays correct value: {ip_value}")
                    print("✅ IP field shows correct value from .env file")
                else:
                    self.add_failure("IP_FIELD", f"IP field shows '{ip_value}', expected '192.168.193.235'")
                    print(f"❌ IP field shows '{ip_value}', expected '192.168.193.235'")
            else:
                self.add_failure("IP_FIELD", "IP field (#drone-host) not found")
                print("❌ Could not locate IP field (#drone-host)")
                
        except Exception as e:
            self.add_failure("IP_FIELD", f"Error testing IP field: {str(e)}")

    async def test_port_field_value(self, page):
        """Test that Port field displays correct value from .env"""
        try:
            print("\n🧪 Testing Port field value...")
            
            # Look for the specific Port input field
            port_field = await page.query_selector('#drone-port')
            
            if port_field:
                port_value = await port_field.get_attribute('value')
                self.results["actual_port"] = port_value
                print(f"🔌 Found Port field (#drone-port) with value: '{port_value}'")
                
                if port_value == "5678":
                    self.add_success("PORT_FIELD", f"Port field displays correct value: {port_value}")
                    print("✅ Port field shows correct value from .env file")
                else:
                    self.add_failure("PORT_FIELD", f"Port field shows '{port_value}', expected '5678'")
                    print(f"❌ Port field shows '{port_value}', expected '5678'")
            else:
                self.add_failure("PORT_FIELD", "Port field (#drone-port) not found")
                print("❌ Could not locate Port field (#drone-port)")
                
        except Exception as e:
            self.add_failure("PORT_FIELD", f"Error testing Port field: {str(e)}")

    async def report_displayed_values(self, page):
        """Report the exact values displayed on the page"""
        try:
            print(f"\n📋 EXACT VALUES DISPLAYED:")
            print(f"   IP Address Field: '{self.results['actual_ip']}'")
            print(f"   Port Field: '{self.results['actual_port']}'")
            
            # Also check page source for template variable passing
            page_content = await page.content()
            if "192.168.193.235" in page_content and "5678" in page_content:
                self.add_success("TEMPLATE_VALUES", "Expected values found in page content")
                print("✅ Both expected values found in page HTML")
            else:
                self.add_failure("TEMPLATE_VALUES", "Expected values not found in page content")
                print("❌ Expected values not found in page HTML")
                
        except Exception as e:
            print(f"Error checking displayed values: {str(e)}")

    async def take_verification_screenshot(self, page):
        """Take screenshot showing IP/Port field values"""
        try:
            print("\n📸 Taking verification screenshot...")
            
            # Highlight connection panel and input fields
            await page.evaluate("""
                const panel = document.querySelector('.connection-panel');
                if (panel) {
                    panel.style.border = '3px solid #00ff00';
                    panel.style.backgroundColor = '#f0f8ff';
                    panel.style.padding = '15px';
                }
                
                // Highlight IP and Port input fields specifically
                const ipField = document.querySelector('#drone-host');
                const portField = document.querySelector('#drone-port');
                
                if (ipField) {
                    ipField.style.border = '3px solid #ff6600';
                    ipField.style.backgroundColor = '#fff8f0';
                    ipField.style.fontSize = '16px';
                    ipField.style.padding = '5px';
                }
                
                if (portField) {
                    portField.style.border = '3px solid #ff6600';
                    portField.style.backgroundColor = '#fff8f0';
                    portField.style.fontSize = '16px'; 
                    portField.style.padding = '5px';
                }
                
                // Add labels to make values obvious
                if (ipField && portField) {
                    const label = document.createElement('div');
                    label.innerHTML = `<strong>CURRENT VALUES:</strong><br/>IP: ${ipField.value}<br/>Port: ${portField.value}`;
                    label.style.cssText = 'position:fixed;top:10px;right:10px;background:#ffff00;padding:10px;border:2px solid #000;font-size:14px;z-index:9999;';
                    document.body.appendChild(label);
                }
            """)
            
            await asyncio.sleep(2)  # Let highlighting take effect
            
            screenshot_path = "ip_port_verification_final.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            
            self.add_success("SCREENSHOT", f"Verification screenshot saved: {screenshot_path}")
            print(f"✅ Screenshot saved: {screenshot_path}")
            
        except Exception as e:
            self.add_failure("SCREENSHOT", f"Error taking screenshot: {str(e)}")

    def add_success(self, test_component, message):
        """Add successful test result"""
        self.results["tests_passed"] += 1
        self.results["details"].append({
            "component": test_component,
            "status": "PASS",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def add_failure(self, test_component, message):
        """Add failed test result"""
        self.results["tests_failed"] += 1
        self.results["details"].append({
            "component": test_component,
            "status": "FAIL", 
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def generate_report(self):
        """Generate comprehensive test report"""
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        pass_rate = (self.results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 FINAL TEST REPORT: IP/Port Display from Environment Variables")
        print("=" * 60)
        print(f"🌐 Test URL: {self.test_url}")
        print(f"✅ Tests Passed: {self.results['tests_passed']}")
        print(f"❌ Tests Failed: {self.results['tests_failed']}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        
        print(f"\n🎯 EXPECTED vs ACTUAL VALUES:")
        print(f"   Expected IP: {self.results['expected_ip']}")
        print(f"   Actual IP:   {self.results['actual_ip']}")
        print(f"   Expected Port: {self.results['expected_port']}")
        print(f"   Actual Port:   {self.results['actual_port']}")
        
        # Summary judgment
        ip_correct = self.results["actual_ip"] == self.results["expected_ip"]
        port_correct = self.results["actual_port"] == self.results["expected_port"]
        
        print(f"\n📋 VALUE VERIFICATION:")
        print(f"   IP Correct:   {'✅' if ip_correct else '❌'}")
        print(f"   Port Correct: {'✅' if port_correct else '❌'}")
        
        print(f"\n📝 Test Details:")
        for detail in self.results["details"]:
            status_emoji = "✅" if detail["status"] == "PASS" else "❌"
            print(f"   {status_emoji} {detail['component']}: {detail['message']}")
        
        # Save results to JSON
        report_file = "ip_port_display_final_results.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Full results saved to: {report_file}")
        
        # Final verdict
        if ip_correct and port_correct:
            print(f"\n🎉 SUCCESS: Website correctly displays IP={self.results['actual_ip']} and Port={self.results['actual_port']} from .env file!")
        else:
            print(f"\n⚠️  ISSUE: Website displays IP={self.results['actual_ip']}, Port={self.results['actual_port']} but expected IP=192.168.193.235, Port=5678")
            if not ip_correct:
                print(f"    🚨 IP field shows '{self.results['actual_ip']}' instead of '192.168.193.235'")
            if not port_correct:
                print(f"    🚨 Port field shows '{self.results['actual_port']}' instead of '5678'")

async def main():
    """Run the IP/Port display test"""
    tester = IPPortDisplayTest()
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())
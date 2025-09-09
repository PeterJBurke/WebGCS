#!/usr/bin/env python3
"""
TEST-CM-ENV-001: Environment Variable Display Test
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
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            context = await browser.new_context(
                viewport={"width": 1200, "height": 800}
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
            
            # Test IP field value
            await self.test_ip_field_value(page)
            
            # Test Port field value
            await self.test_port_field_value(page)
            
            # Take screenshot showing the values
            await self.take_verification_screenshot(page)
            
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
            response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            if response.status == 200:
                print(f"✅ Successfully connected to {url}")
                return True
            else:
                print(f"❌ HTTP {response.status} from {url}")
                return False
        except Exception as e:
            print(f"❌ Failed to connect to {url}: {str(e)}")
            return False

    async def test_ip_field_value(self, page):
        """Test that IP field displays correct value from .env"""
        try:
            print("\n🧪 Testing IP field value...")
            
            # Wait for connection panel to load
            await page.wait_for_selector('#connection-panel', timeout=10000)
            
            # Look for IP input field - try multiple selectors
            ip_selectors = [
                'input[placeholder*="IP"]',
                'input[placeholder*="address"]', 
                'input#ip',
                'input#address',
                'input[name="ip"]',
                'input[name="address"]',
                '#connection-panel input[type="text"]:first-of-type'
            ]
            
            ip_field = None
            ip_value = None
            
            for selector in ip_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        ip_field = elements[0]
                        ip_value = await ip_field.get_attribute('value')
                        if ip_value:
                            break
                except:
                    continue
            
            if ip_field and ip_value:
                print(f"📍 Found IP field with value: '{ip_value}'")
                
                if ip_value == "192.168.193.235":
                    self.add_success("IP_FIELD", f"IP field displays correct value: {ip_value}")
                    print("✅ IP field shows correct value from .env file")
                else:
                    self.add_failure("IP_FIELD", f"IP field shows '{ip_value}', expected '192.168.193.235'")
                    print(f"❌ IP field shows '{ip_value}', expected '192.168.193.235'")
            else:
                # Fallback: check if value is in the page content
                page_content = await page.content()
                if "192.168.193.235" in page_content:
                    self.add_success("IP_FIELD", "IP address found in page content")
                    print("✅ IP address found in page content")
                else:
                    self.add_failure("IP_FIELD", "IP field not found or has no value")
                    print("❌ Could not locate IP field or determine its value")
                
        except Exception as e:
            self.add_failure("IP_FIELD", f"Error testing IP field: {str(e)}")

    async def test_port_field_value(self, page):
        """Test that Port field displays correct value from .env"""
        try:
            print("\n🧪 Testing Port field value...")
            
            # Look for Port input field - try multiple selectors
            port_selectors = [
                'input[placeholder*="Port"]',
                'input[placeholder*="port"]',
                'input#port',
                'input[name="port"]',
                '#connection-panel input[type="text"]:last-of-type',
                '#connection-panel input[type="number"]'
            ]
            
            port_field = None
            port_value = None
            
            for selector in port_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        port_field = elements[0]
                        port_value = await port_field.get_attribute('value')
                        if port_value:
                            break
                except:
                    continue
            
            if port_field and port_value:
                print(f"🔌 Found Port field with value: '{port_value}'")
                
                if port_value == "5678":
                    self.add_success("PORT_FIELD", f"Port field displays correct value: {port_value}")
                    print("✅ Port field shows correct value from .env file")
                else:
                    self.add_failure("PORT_FIELD", f"Port field shows '{port_value}', expected '5678'")
                    print(f"❌ Port field shows '{port_value}', expected '5678'")
            else:
                # Fallback: check if value is in the page content
                page_content = await page.content()
                if "5678" in page_content:
                    self.add_success("PORT_FIELD", "Port number found in page content")
                    print("✅ Port number found in page content")
                else:
                    self.add_failure("PORT_FIELD", "Port field not found or has no value")
                    print("❌ Could not locate Port field or determine its value")
                
        except Exception as e:
            self.add_failure("PORT_FIELD", f"Error testing Port field: {str(e)}")

    async def take_verification_screenshot(self, page):
        """Take screenshot showing IP/Port field values"""
        try:
            print("\n📸 Taking verification screenshot...")
            
            # Highlight connection panel
            await page.evaluate("""
                const panel = document.querySelector('#connection-panel');
                if (panel) {
                    panel.style.border = '3px solid #00ff00';
                    panel.style.backgroundColor = '#f0f8ff';
                }
                
                // Highlight input fields
                const inputs = document.querySelectorAll('#connection-panel input');
                inputs.forEach(input => {
                    input.style.border = '2px solid #ff6600';
                    input.style.backgroundColor = '#fff8f0';
                });
            """)
            
            await asyncio.sleep(1)  # Let highlighting take effect
            
            screenshot_path = "ip_port_verification_screenshot.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            
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
        print("📊 TEST REPORT: IP/Port Display from Environment Variables")
        print("=" * 60)
        print(f"✅ Tests Passed: {self.results['tests_passed']}")
        print(f"❌ Tests Failed: {self.results['tests_failed']}")
        print(f"📈 Pass Rate: {pass_rate:.1f}%")
        print(f"🌐 Test URL: {self.test_url}")
        
        print(f"\n🎯 Expected Values:")
        print(f"   IP Address: {self.results['expected_ip']}")
        print(f"   Port: {self.results['expected_port']}")
        
        print(f"\n📝 Test Details:")
        for detail in self.results["details"]:
            status_emoji = "✅" if detail["status"] == "PASS" else "❌"
            print(f"   {status_emoji} {detail['component']}: {detail['message']}")
        
        # Save results to JSON
        report_file = "ip_port_display_test_results.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Full results saved to: {report_file}")
        
        # Final verdict
        if self.results["tests_failed"] == 0:
            print(f"\n🎉 SUCCESS: Website correctly displays IP/Port from .env file!")
        else:
            print(f"\n⚠️  ISSUES FOUND: Website may not be displaying .env values correctly")

async def main():
    """Run the IP/Port display test"""
    tester = IPPortDisplayTest()
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())
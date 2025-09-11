#!/usr/bin/env python3
"""
FINAL VALIDATION TEST - SocketIO Compatibility Fixes
================================================================

Test the connect button after SocketIO compatibility fixes implemented
by the web-interface-agent.

CRITICAL VALIDATION POINTS:
1. SocketIO Connection Validation
2. Browser Connection Test
3. Connect Button Functionality  
4. End-to-End Validation

Expected: Connect button should work without "Not connected to WebGCS server" popup
"""

import asyncio
import json
import time
import requests
from playwright.async_api import async_playwright

class FinalValidationTest:
    def __init__(self):
        self.base_url = "http://localhost:5002"
        self.results = {
            "test_name": "FINAL VALIDATION - SocketIO Compatibility Fixes",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "socketio_connection": None,
            "browser_connection": None,
            "connect_button": None,
            "end_to_end": None,
            "overall_success": False
        }
    
    def test_socketio_endpoint(self):
        """Test SocketIO endpoint compatibility"""
        print("\n=== STEP 1: SocketIO Connection Validation ===")
        
        try:
            # Test SocketIO endpoint
            response = requests.get(f"{self.base_url}/socket.io/?EIO=4&transport=polling", timeout=10)
            
            if response.status_code == 200:
                response_text = response.text
                print(f"✅ SocketIO endpoint responding: {response.status_code}")
                print(f"Response: {response_text[:100]}...")
                
                # Check for session ID and proper format
                if '"sid"' in response_text and '"upgrades"' in response_text:
                    print("✅ Proper SocketIO session negotiation")
                    self.results["socketio_connection"] = {
                        "status": "SUCCESS",
                        "details": "SocketIO endpoint responding with proper session data",
                        "response": response_text[:200]
                    }
                    return True
                else:
                    print("❌ Invalid SocketIO response format")
                    self.results["socketio_connection"] = {
                        "status": "FAILED",
                        "details": "Invalid response format",
                        "response": response_text[:200]
                    }
                    return False
            else:
                print(f"❌ SocketIO endpoint error: {response.status_code}")
                self.results["socketio_connection"] = {
                    "status": "FAILED",
                    "details": f"HTTP {response.status_code}",
                    "response": response.text[:200]
                }
                return False
                
        except Exception as e:
            print(f"❌ SocketIO connection failed: {e}")
            self.results["socketio_connection"] = {
                "status": "FAILED",
                "details": str(e),
                "response": None
            }
            return False

    async def test_browser_connection(self):
        """Test browser SocketIO connection"""
        print("\n=== STEP 2: Browser Connection Test ===")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set up console logging
                console_logs = []
                def on_console(msg):
                    console_logs.append(f"{msg.type}: {msg.text}")
                page.on("console", on_console)
                
                # Navigate to the site
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")
                
                # Wait for SocketIO connection
                await asyncio.sleep(3)
                
                # Check WebGCS connection status
                connected = await page.evaluate("window.WebGCS ? window.WebGCS.connected : false")
                print(f"WebGCS.connected: {connected}")
                
                # Check for connection messages
                success_found = any("Connected to WebGCS server" in log for log in console_logs)
                error_found = any("unsupported version" in log.lower() for log in console_logs)
                
                print(f"✅ Connection success message found: {success_found}")
                print(f"❌ Version error found: {error_found}")
                
                # Print recent console logs
                print("\nRecent console logs:")
                for log in console_logs[-10:]:
                    print(f"  {log}")
                
                if connected and success_found and not error_found:
                    print("✅ Browser SocketIO connection successful")
                    self.results["browser_connection"] = {
                        "status": "SUCCESS",
                        "connected": connected,
                        "success_message": success_found,
                        "error_message": error_found,
                        "console_logs": console_logs[-5:]
                    }
                    browser_success = True
                else:
                    print("❌ Browser SocketIO connection issues")
                    self.results["browser_connection"] = {
                        "status": "FAILED",
                        "connected": connected,
                        "success_message": success_found,
                        "error_message": error_found,
                        "console_logs": console_logs[-5:]
                    }
                    browser_success = False
                
                await browser.close()
                return browser_success
                
        except Exception as e:
            print(f"❌ Browser connection test failed: {e}")
            self.results["browser_connection"] = {
                "status": "FAILED",
                "details": str(e),
                "console_logs": []
            }
            return False

    async def test_connect_button_functionality(self):
        """Test connect button functionality"""
        print("\n=== STEP 3: Connect Button Functionality ===")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set up console and alert monitoring
                console_logs = []
                alerts = []
                
                def on_console(msg):
                    console_logs.append(f"{msg.type}: {msg.text}")
                
                def on_dialog(dialog):
                    alerts.append(dialog.message)
                    dialog.accept()
                
                page.on("console", on_console)
                page.on("dialog", on_dialog)
                
                # Navigate to the site
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)  # Wait for SocketIO connection
                
                # Find and click connect button
                connect_button = page.locator("#connect-drone-btn")
                if not await connect_button.is_visible():
                    print("❌ Connect button not found")
                    self.results["connect_button"] = {
                        "status": "FAILED",
                        "details": "Connect button not found",
                        "alerts": alerts,
                        "console_logs": console_logs[-5:]
                    }
                    await browser.close()
                    return False
                
                button_text = await connect_button.text_content()
                print(f"Connect button found: '{button_text}'")
                
                # Click the connect button
                await connect_button.click()
                await asyncio.sleep(2)  # Wait for response
                
                # Check for the dreaded popup
                popup_found = any("Not connected to WebGCS server" in alert for alert in alerts)
                
                print(f"❌ 'Not connected to WebGCS server' popup: {popup_found}")
                print(f"Total alerts: {len(alerts)}")
                
                if alerts:
                    for i, alert in enumerate(alerts):
                        print(f"  Alert {i+1}: {alert}")
                
                # Check button state after click
                await asyncio.sleep(1)
                new_button_text = await connect_button.text_content()
                print(f"Button text after click: '{new_button_text}'")
                
                # Look for connection attempt in logs
                connection_attempt = any("connect_drone" in log for log in console_logs)
                print(f"Connection attempt detected: {connection_attempt}")
                
                # Print recent logs
                print("\nRecent console logs:")
                for log in console_logs[-10:]:
                    print(f"  {log}")
                
                if not popup_found and connection_attempt:
                    print("✅ Connect button functionality working")
                    self.results["connect_button"] = {
                        "status": "SUCCESS",
                        "popup_found": popup_found,
                        "connection_attempt": connection_attempt,
                        "button_state_change": button_text != new_button_text,
                        "alerts": alerts,
                        "console_logs": console_logs[-5:]
                    }
                    button_success = True
                else:
                    print("❌ Connect button functionality issues")
                    self.results["connect_button"] = {
                        "status": "FAILED",
                        "popup_found": popup_found,
                        "connection_attempt": connection_attempt,
                        "button_state_change": button_text != new_button_text,
                        "alerts": alerts,
                        "console_logs": console_logs[-5:]
                    }
                    button_success = False
                
                await browser.close()
                return button_success
                
        except Exception as e:
            print(f"❌ Connect button test failed: {e}")
            self.results["connect_button"] = {
                "status": "FAILED",
                "details": str(e),
                "alerts": [],
                "console_logs": []
            }
            return False

    async def test_end_to_end_validation(self):
        """Test complete end-to-end validation"""
        print("\n=== STEP 4: End-to-End Validation ===")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                console_logs = []
                def on_console(msg):
                    console_logs.append(f"{msg.type}: {msg.text}")
                page.on("console", on_console)
                
                # Navigate and wait for full load
                await page.goto(self.base_url)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(5)  # Extended wait for SocketIO
                
                # Comprehensive validation
                validations = {}
                
                # 1. Check SocketIO connection
                connected = await page.evaluate("window.WebGCS ? window.WebGCS.connected : false")
                validations["socketio_connected"] = connected
                
                # 2. Check for SocketIO object
                socket_exists = await page.evaluate("typeof window.WebGCS.socket !== 'undefined'")
                validations["socket_object_exists"] = socket_exists
                
                # 3. Test debug function
                debug_result = await page.evaluate("window.debugSocketIO ? window.debugSocketIO() : 'function not found'")
                validations["debug_function"] = debug_result
                
                # 4. Check connection indicator
                status_text = await page.text_content("#connection-status")
                validations["connection_status"] = status_text
                
                print(f"SocketIO Connected: {validations['socketio_connected']}")
                print(f"Socket Object Exists: {validations['socket_object_exists']}")
                print(f"Connection Status: {validations['connection_status']}")
                print(f"Debug Function: {validations['debug_function']}")
                
                # Success criteria
                success_criteria = [
                    validations["socketio_connected"],
                    validations["socket_object_exists"],
                    "Connected" in str(validations.get("connection_status", ""))
                ]
                
                all_success = all(success_criteria)
                
                if all_success:
                    print("✅ End-to-End validation successful")
                    self.results["end_to_end"] = {
                        "status": "SUCCESS",
                        "validations": validations,
                        "console_logs": console_logs[-5:]
                    }
                    e2e_success = True
                else:
                    print("❌ End-to-End validation issues")
                    self.results["end_to_end"] = {
                        "status": "FAILED",
                        "validations": validations,
                        "success_criteria": success_criteria,
                        "console_logs": console_logs[-5:]
                    }
                    e2e_success = False
                
                await browser.close()
                return e2e_success
                
        except Exception as e:
            print(f"❌ End-to-end validation failed: {e}")
            self.results["end_to_end"] = {
                "status": "FAILED",
                "details": str(e),
                "console_logs": []
            }
            return False

    async def run_validation(self):
        """Run complete validation test suite"""
        print("=" * 60)
        print("FINAL VALIDATION TEST - SocketIO Compatibility Fixes")
        print("=" * 60)
        
        # Run all tests
        socketio_ok = self.test_socketio_endpoint()
        browser_ok = await self.test_browser_connection()
        button_ok = await self.test_connect_button_functionality()
        e2e_ok = await self.test_end_to_end_validation()
        
        # Overall assessment
        overall_success = all([socketio_ok, browser_ok, button_ok, e2e_ok])
        self.results["overall_success"] = overall_success
        
        print("\n" + "=" * 60)
        print("FINAL VALIDATION SUMMARY")
        print("=" * 60)
        print(f"✅ SocketIO Connection: {'PASS' if socketio_ok else 'FAIL'}")
        print(f"✅ Browser Connection: {'PASS' if browser_ok else 'FAIL'}")
        print(f"✅ Connect Button: {'PASS' if button_ok else 'FAIL'}")
        print(f"✅ End-to-End: {'PASS' if e2e_ok else 'FAIL'}")
        print("-" * 60)
        print(f"🎯 OVERALL RESULT: {'SUCCESS' if overall_success else 'FAILED'}")
        print("=" * 60)
        
        if overall_success:
            print("\n🎉 SocketIO compatibility fixes have RESOLVED the connect button issue!")
            print("✅ Connect button should now work without 'Not connected to WebGCS server' popup")
        else:
            print("\n⚠️  SocketIO compatibility fixes need additional work")
            print("❌ Connect button issues may still persist")
        
        # Save detailed results
        with open("FINAL_VALIDATION_RESULTS.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        return overall_success

async def main():
    """Main test execution"""
    tester = FinalValidationTest()
    success = await tester.run_validation()
    exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
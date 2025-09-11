#!/usr/bin/env python3
"""
COMPREHENSIVE REAL BROWSER CONNECT BUTTON TEST

This test opens a real browser, loads the actual website at http://localhost:5002,
and captures exactly what happens when the connect button is clicked.

CRITICAL OBJECTIVES:
1. Open actual browser (visible, not headless)
2. Monitor JavaScript console in real-time
3. Capture ALL popups/alerts/dialogs with exact text
4. Take screenshots before and after click
5. Log exact state of all connection variables
6. Handle any errors or timeouts that occur
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright


class RealBrowserConnectTest:
    def __init__(self):
        self.console_messages = []
        self.dialog_messages = []
        self.network_messages = []
        self.error_messages = []
        self.test_results = {}
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {message}")
        
    async def handle_console_message(self, msg):
        """Capture all console messages"""
        message = f"[{msg.type.upper()}] {msg.text}"
        self.console_messages.append(message)
        self.log(f"CONSOLE: {message}")
        
        # Check for specific connection-related messages
        if "connect" in msg.text.lower() or "socket" in msg.text.lower():
            self.log(f"CONNECTION-RELATED CONSOLE: {message}")
    
    async def handle_dialog(self, dialog):
        """Handle popups/alerts/dialogs"""
        dialog_info = {
            "type": dialog.type,
            "message": dialog.message,
            "default_value": dialog.default_value
        }
        self.dialog_messages.append(dialog_info)
        self.log(f"DIALOG DETECTED - Type: {dialog.type}, Message: '{dialog.message}'")
        
        # Accept the dialog to continue
        await dialog.accept()
        self.log("Dialog accepted")
        
    async def handle_request(self, request):
        """Monitor network requests"""
        if "socket.io" in request.url or "connect" in request.url:
            self.network_messages.append(f"REQUEST: {request.method} {request.url}")
            self.log(f"NETWORK REQUEST: {request.method} {request.url}")
            
    async def handle_response(self, response):
        """Monitor network responses"""
        if "socket.io" in response.url or "connect" in response.url:
            self.network_messages.append(f"RESPONSE: {response.status} {response.url}")
            self.log(f"NETWORK RESPONSE: {response.status} {response.url}")
    
    async def capture_page_state(self, page, label):
        """Capture complete page state"""
        self.log(f"=== CAPTURING {label} STATE ===")
        
        state = {}
        
        # Check JavaScript environment
        try:
            state['window_webgcs'] = await page.evaluate("typeof window.WebGCS")
            state['window_io'] = await page.evaluate("typeof window.io")
            state['webgcs_connected'] = await page.evaluate("window.WebGCS?.connected")
            state['socket_connected'] = await page.evaluate("window.WebGCS?.socket?.connected")
            state['socket_id'] = await page.evaluate("window.WebGCS?.socket?.id")
            state['connection_manager_exists'] = await page.evaluate("typeof ConnectionManager")
        except Exception as e:
            state['javascript_error'] = str(e)
            self.log(f"JavaScript evaluation error: {e}")
        
        # Check button state
        try:
            button = page.locator("#connect-drone-btn")
            if await button.count() > 0:
                state['button_text'] = await button.text_content()
                state['button_enabled'] = await button.is_enabled()
                state['button_visible'] = await button.is_visible()
            else:
                state['button_exists'] = False
        except Exception as e:
            state['button_error'] = str(e)
            
        # Check connection status elements
        try:
            status_element = page.locator("#connection-status")
            if await status_element.count() > 0:
                state['connection_status_text'] = await status_element.text_content()
        except Exception as e:
            state['status_error'] = str(e)
            
        # Log all state information
        for key, value in state.items():
            self.log(f"{label} - {key}: {value}")
            
        return state

    async def run_test(self):
        """Run the comprehensive browser test"""
        self.log("Starting comprehensive real browser connect button test")
        
        async with async_playwright() as p:
            # Launch visible browser for real testing
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500,  # Slow down for visibility
                args=['--disable-web-security', '--allow-running-insecure-content']
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True
            )
            
            page = await context.new_page()
            
            # Set up event handlers
            page.on("console", self.handle_console_message)
            page.on("dialog", self.handle_dialog)
            page.on("request", self.handle_request)
            page.on("response", self.handle_response)
            
            try:
                # Navigate to the website
                self.log("=== OPENING WEBSITE ===")
                await page.goto("http://localhost:5002", wait_until="networkidle", timeout=10000)
                
                # Wait for page to fully load
                await page.wait_for_timeout(2000)
                
                # Take initial screenshot
                await page.screenshot(path="before_click.png", full_page=True)
                self.log("Initial screenshot saved: before_click.png")
                
                # Capture pre-click state
                pre_state = await self.capture_page_state(page, "PRE-CLICK")
                self.test_results['pre_click_state'] = pre_state
                
                # Find the connect button
                self.log("=== LOCATING CONNECT BUTTON ===")
                button = page.locator("#connect-drone-btn")
                
                if await button.count() == 0:
                    self.log("ERROR: Connect button not found!")
                    self.test_results['error'] = "Connect button not found"
                    return
                
                # Wait for button to be ready
                await button.wait_for(state="visible", timeout=5000)
                
                self.log("=== CLICKING CONNECT BUTTON ===")
                
                # Record exact time of click
                click_time = datetime.now()
                self.test_results['click_time'] = click_time.isoformat()
                
                # Click the button
                await button.click()
                self.log("Button clicked!")
                
                # Wait and monitor what happens
                self.log("=== MONITORING POST-CLICK BEHAVIOR ===")
                await page.wait_for_timeout(8000)  # Wait 8 seconds to see what happens
                
                # Take post-click screenshot
                await page.screenshot(path="after_click.png", full_page=True)
                self.log("Post-click screenshot saved: after_click.png")
                
                # Capture post-click state
                post_state = await self.capture_page_state(page, "POST-CLICK")
                self.test_results['post_click_state'] = post_state
                
                # Wait a bit more to catch any delayed reactions
                await page.wait_for_timeout(3000)
                
                # Final state capture
                final_state = await self.capture_page_state(page, "FINAL")
                self.test_results['final_state'] = final_state
                
            except Exception as e:
                self.error_messages.append(str(e))
                self.log(f"TEST ERROR: {e}")
                self.test_results['test_error'] = str(e)
                
            finally:
                # Keep browser open for manual inspection
                self.log("=== TEST COMPLETE - Browser will remain open for 30 seconds ===")
                await page.wait_for_timeout(30000)
                await browser.close()
        
        # Compile final results
        self.test_results.update({
            'console_messages': self.console_messages,
            'dialog_messages': self.dialog_messages,
            'network_messages': self.network_messages,
            'error_messages': self.error_messages,
            'test_completed': True,
            'test_duration_seconds': (datetime.now() - click_time).total_seconds() if 'click_time' in self.test_results else 0
        })
        
        return self.test_results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.log("=== GENERATING COMPREHENSIVE TEST REPORT ===")
        
        report = {
            "test_name": "Real Browser Connect Button Test",
            "test_timestamp": datetime.now().isoformat(),
            "summary": {
                "console_messages_count": len(self.console_messages),
                "dialogs_detected": len(self.dialog_messages),
                "network_requests": len(self.network_messages),
                "errors_encountered": len(self.error_messages)
            },
            "detailed_results": self.test_results
        }
        
        # Save to file
        with open("real_browser_test_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        self.log("Report saved to: real_browser_test_report.json")
        
        # Print summary
        print("\n" + "="*80)
        print("REAL BROWSER TEST SUMMARY")
        print("="*80)
        print(f"Console Messages: {len(self.console_messages)}")
        print(f"Dialogs Detected: {len(self.dialog_messages)}")
        print(f"Network Messages: {len(self.network_messages)}")
        print(f"Errors: {len(self.error_messages)}")
        
        if self.dialog_messages:
            print("\nDIALOGS DETECTED:")
            for dialog in self.dialog_messages:
                print(f"  - Type: {dialog['type']}, Message: '{dialog['message']}'")
        
        if self.console_messages:
            print("\nCONSOLE MESSAGES:")
            for msg in self.console_messages[-10:]:  # Show last 10
                print(f"  - {msg}")
        
        if self.error_messages:
            print("\nERRORS:")
            for error in self.error_messages:
                print(f"  - {error}")
        
        print("="*80)
        
        return report


async def main():
    """Main test execution"""
    test = RealBrowserConnectTest()
    
    try:
        results = await test.run_test()
        report = test.generate_report()
        
        print("\nTest completed successfully!")
        print("Check the following files:")
        print("- before_click.png (screenshot before button click)")
        print("- after_click.png (screenshot after button click)")
        print("- real_browser_test_report.json (complete test report)")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
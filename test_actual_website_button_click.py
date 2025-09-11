#!/usr/bin/env python3
"""
TEST: Real Website Connect Button Diagnosis
TEST NAME: test_actual_website_button_click.py

CRITICAL INVESTIGATION: Diagnose the exact issue with the connect button
showing "Not connected to WebGCS server" popup when clicked.

REAL WORLD TESTING:
- Navigate to ACTUAL website at http://localhost:5002
- Check SocketIO connection state before and after button click
- Capture exact error messages and JavaScript state
- Identify where the connection validation fails

EXPECTED FINDING: window.WebGCS.connected is false when button is clicked
"""

import asyncio
import time
import pytest
import os
import sys
import subprocess
import signal
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    print("❌ Playwright not available. Install with: pip install playwright")
    sys.exit(1)

class RealWebsiteButtonTest:
    """Test the actual website connect button functionality"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.server_process = None
        
    async def setup(self):
        """Setup browser and navigate to actual website"""
        print("🚀 Setting up browser for real website testing...")
        
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Show browser to see what happens
            args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
        )
        
        self.context = await self.browser.new_context()
        
        # Enable console logging to capture JavaScript errors
        self.page = await self.context.new_page()
        
        # Capture console messages
        self.console_messages = []
        self.page.on("console", lambda msg: self.console_messages.append(f"[{msg.type}] {msg.text}"))
        
        # Capture JavaScript errors
        self.js_errors = []
        self.page.on("pageerror", lambda error: self.js_errors.append(str(error)))
        
        # Capture dialog alerts (the popup we're investigating)
        self.dialogs = []
        
        async def handle_dialog(dialog):
            dialog_info = {
                'type': dialog.type,
                'message': dialog.message,
                'default_value': dialog.default_value
            }
            print(f"🚨 DIALOG CAPTURED: {dialog_info}")
            self.dialogs.append(dialog_info)
            await dialog.accept()  # Close the dialog
            
        self.page.on("dialog", handle_dialog)
        
    async def navigate_to_website(self):
        """Navigate to the actual website"""
        print("🌐 Navigating to http://localhost:5002...")
        
        try:
            response = await self.page.goto("http://localhost:5002", wait_until="networkidle")
            print(f"✅ Page loaded with status: {response.status}")
            
            # Wait for page to be fully loaded
            await self.page.wait_for_load_state("domcontentloaded")
            await self.page.wait_for_timeout(2000)  # Give time for JavaScript to initialize
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load website: {e}")
            return False
            
    async def analyze_initial_state(self):
        """Analyze the initial JavaScript state before clicking"""
        print("\n🔍 ANALYZING INITIAL STATE...")
        
        # Check if window.WebGCS exists
        webgcs_exists = await self.page.evaluate("typeof window.WebGCS !== 'undefined'")
        print(f"window.WebGCS exists: {webgcs_exists}")
        
        if webgcs_exists:
            # Check all WebGCS properties
            webgcs_state = await self.page.evaluate("""
                ({
                    connected: window.WebGCS.connected,
                    droneConnected: window.WebGCS.droneConnected,
                    socket: window.WebGCS.socket ? {
                        connected: window.WebGCS.socket.connected,
                        id: window.WebGCS.socket.id,
                        readyState: window.WebGCS.socket.readyState
                    } : null,
                    modules: {
                        connection: typeof window.WebGCS.modules?.connection,
                        controls: typeof window.WebGCS.modules?.controls
                    }
                })
            """)
            
            print("📊 WebGCS State:")
            for key, value in webgcs_state.items():
                print(f"  {key}: {value}")
                
            return webgcs_state
        else:
            print("❌ window.WebGCS not found - this is the problem!")
            return None
            
    async def check_connect_button(self):
        """Check the connect button state"""
        print("\n🔘 CHECKING CONNECT BUTTON...")
        
        # Find the connect button
        connect_button = await self.page.query_selector("#connect-drone-btn")
        if connect_button:
            button_text = await connect_button.text_content()
            button_disabled = await connect_button.is_disabled()
            button_visible = await connect_button.is_visible()
            
            print(f"Button found: text='{button_text}', disabled={button_disabled}, visible={button_visible}")
            return True
        else:
            print("❌ Connect button not found!")
            return False
            
    async def click_connect_button_and_monitor(self):
        """Click the connect button and monitor what happens"""
        print("\n🎯 CLICKING CONNECT BUTTON...")
        
        # Clear previous dialogs
        self.dialogs.clear()
        self.console_messages.clear()
        self.js_errors.clear()
        
        # Get state just before clicking
        pre_click_state = await self.page.evaluate("""
            ({
                connected: window.WebGCS?.connected,
                socket_connected: window.WebGCS?.socket?.connected,
                timestamp: Date.now()
            })
        """)
        print(f"Pre-click state: {pre_click_state}")
        
        # Click the button
        try:
            await self.page.click("#connect-drone-btn")
            print("✅ Button clicked successfully")
            
            # Wait a moment for any dialogs or state changes
            await self.page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"❌ Failed to click button: {e}")
            return False
            
        # Check state after clicking
        post_click_state = await self.page.evaluate("""
            ({
                connected: window.WebGCS?.connected,
                socket_connected: window.WebGCS?.socket?.connected,
                timestamp: Date.now()
            })
        """)
        print(f"Post-click state: {post_click_state}")
        
        return True
        
    async def analyze_results(self):
        """Analyze what happened after the button click"""
        print("\n📋 ANALYSIS RESULTS:")
        
        # Check for dialogs (the popup we're investigating)
        if self.dialogs:
            print("🚨 DIALOGS FOUND:")
            for dialog in self.dialogs:
                print(f"  Type: {dialog['type']}")
                print(f"  Message: '{dialog['message']}'")
                
                # This is the key finding!
                if "Not connected to WebGCS server" in dialog['message']:
                    print("🎯 FOUND THE EXACT ISSUE!")
                    print("   This confirms window.WebGCS.connected is false when button is clicked")
        else:
            print("✅ No dialogs appeared")
            
        # Check console messages
        if self.console_messages:
            print("\n📝 CONSOLE MESSAGES:")
            for msg in self.console_messages[-10:]:  # Last 10 messages
                print(f"  {msg}")
                
        # Check JavaScript errors
        if self.js_errors:
            print("\n💥 JAVASCRIPT ERRORS:")
            for error in self.js_errors:
                print(f"  {error}")
                
    async def run_comprehensive_diagnosis(self):
        """Run the complete diagnostic test"""
        print("🔬 STARTING COMPREHENSIVE CONNECT BUTTON DIAGNOSIS")
        print("=" * 60)
        
        try:
            # Setup browser
            await self.setup()
            
            # Navigate to website
            if not await self.navigate_to_website():
                return False
                
            # Analyze initial state
            initial_state = await self.analyze_initial_state()
            
            # Check button exists
            if not await self.check_connect_button():
                return False
                
            # Click button and monitor
            if not await self.click_connect_button_and_monitor():
                return False
                
            # Analyze results
            await self.analyze_results()
            
            # DIAGNOSIS CONCLUSION
            print("\n" + "=" * 60)
            print("🏁 DIAGNOSIS CONCLUSION:")
            
            if self.dialogs and any("Not connected to WebGCS server" in d['message'] for d in self.dialogs):
                print("✅ CONFIRMED: The exact issue is reproduced!")
                print("📍 ROOT CAUSE: window.WebGCS.connected is false when button is clicked")
                print("🔧 SOLUTION NEEDED: SocketIO connection is not establishing properly")
                print("   The SocketIO 'connect' event is not firing to set window.WebGCS.connected = true")
                
                # Check why SocketIO isn't connecting
                if initial_state and initial_state.get('socket'):
                    socket_state = initial_state['socket']
                    print(f"   Socket state: {socket_state}")
                    if not socket_state['connected']:
                        print("   ❌ SocketIO socket is not connected to server")
                        print("   💡 Check if Flask-SocketIO server is running properly")
                else:
                    print("   ❌ No socket object found - SocketIO not initialized")
                    print("   💡 Check if connection.js is loading and initializing properly")
                    
                return True
            else:
                print("❓ Unexpected behavior - no popup appeared")
                return False
                
        except Exception as e:
            print(f"💥 Test failed with exception: {e}")
            return False
            
        finally:
            if self.browser:
                await self.browser.close()
                
    async def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()

async def main():
    """Main test execution"""
    print("🧪 REAL WEBSITE CONNECT BUTTON DIAGNOSIS")
    print("Testing actual website at http://localhost:5002")
    print("This will identify exactly why the connect button shows the popup")
    
    # Check if website is running
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:5002", timeout=2)
        print("✅ Website is running at localhost:5002")
    except Exception:
        print("❌ Website is not running at localhost:5002")
        print("   Please start the website first with: PYTHONPATH=. uv run python main.py")
        return False
        
    # Run the test
    test = RealWebsiteButtonTest()
    
    try:
        success = await test.run_comprehensive_diagnosis()
        
        if success:
            print("\n🎉 DIAGNOSIS COMPLETE!")
            print("The test successfully identified the exact issue with the connect button.")
            return True
        else:
            print("\n❌ DIAGNOSIS INCOMPLETE")
            print("The test could not reproduce or identify the issue.")
            return False
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        return False
    finally:
        await test.cleanup()

if __name__ == "__main__":
    # Run the async test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
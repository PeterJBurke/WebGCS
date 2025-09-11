import asyncio
from playwright.async_api import async_playwright
import time

async def test_user_alert_popup():
    """Test specifically for the alert popup the user reports seeing"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Visible to see exactly what user sees
            slow_mo=1000     # Slow to see each action clearly
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track dialogs (alerts/popups) specifically
        alerts_captured = []
        
        # Capture ONLY alerts/popups (not console messages)
        async def capture_alert(dialog):
            alert_message = dialog.message
            alert_type = dialog.type
            alerts_captured.append({
                'type': alert_type,
                'message': alert_message,
                'timestamp': time.time()
            })
            print(f"\n🚨 ALERT DETECTED: {alert_type}")
            print(f"📝 ALERT MESSAGE: {alert_message}")
            
            # Accept the alert (like user clicking OK)
            await dialog.accept()
        
        page.on("dialog", capture_alert)
        
        try:
            print("🌐 Opening http://localhost:5002")
            await page.goto("http://localhost:5002", wait_until="networkidle")
            
            # Wait for page to fully load
            print("⏳ Waiting for page to fully load...")
            await page.wait_for_timeout(5000)
            
            # Check if connect button exists and is visible
            print("🔍 Looking for connect button...")
            connect_button = page.locator("#connect-drone-btn")
            await connect_button.wait_for(state="visible", timeout=10000)
            
            button_text = await connect_button.text_content()
            is_enabled = await connect_button.is_enabled()
            print(f"✅ Found button: '{button_text}' (enabled: {is_enabled})")
            
            # Check WebGCS connection status BEFORE clicking
            webgcs_connected_before = await page.evaluate("window.WebGCS?.connected")
            socket_connected_before = await page.evaluate("window.WebGCS?.socket?.connected")
            
            print(f"📊 BEFORE click - WebGCS connected: {webgcs_connected_before}")
            print(f"📊 BEFORE click - Socket connected: {socket_connected_before}")
            
            # Clear any existing alerts
            alerts_captured.clear()
            
            print("\n👆 CLICKING CONNECT BUTTON...")
            await connect_button.click()
            
            # Wait for potential alert to appear
            print("⏳ Waiting for potential alert...")
            await page.wait_for_timeout(3000)
            
            # Check status AFTER clicking
            webgcs_connected_after = await page.evaluate("window.WebGCS?.connected")
            socket_connected_after = await page.evaluate("window.WebGCS?.socket?.connected")
            
            print(f"📊 AFTER click - WebGCS connected: {webgcs_connected_after}")
            print(f"📊 AFTER click - Socket connected: {socket_connected_after}")
            
            # Report results
            print("\n" + "="*60)
            print("🔍 ALERT POPUP TEST RESULTS")
            print("="*60)
            
            if alerts_captured:
                print(f"🚨 ALERTS FOUND: {len(alerts_captured)}")
                for i, alert in enumerate(alerts_captured, 1):
                    print(f"   Alert {i}:")
                    print(f"     Type: {alert['type']}")  
                    print(f"     Message: '{alert['message']}'")
                    
                    # Check for the specific message user reported
                    if "Not connected to WebGCS server" in alert['message']:
                        print(f"   ❌ FOUND THE USER'S PROBLEM: Alert says '{alert['message']}'")
                        return False  # Test fails - user's issue reproduced
                    
            else:
                print("✅ NO ALERTS DETECTED")
                
            # Final validation
            if not socket_connected_after:
                print("❌ TEST REVEALS PROBLEM: Socket not connected after click")
                return False
                
            if not webgcs_connected_after:
                print("❌ TEST REVEALS PROBLEM: WebGCS not connected after click")
                return False
                
            print("✅ TEST PASSED: No alert popup, connection successful")
            return True
            
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            return False
            
        finally:
            print("\n⏳ Keeping browser open for 5 seconds to observe...")
            await page.wait_for_timeout(5000)
            await browser.close()

# Run the test
if __name__ == "__main__":
    result = asyncio.run(test_user_alert_popup())
    print(f"\n{'✅ PASS' if result else '❌ FAIL'}: Alert popup test")
    exit(0 if result else 1)
import asyncio
from playwright.async_api import async_playwright
import time

async def test_real_user_behavior():
    """Test exactly what a real user does - open page and click button immediately"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser like real user
            slow_mo=100      # Normal speed
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track ALL alerts that appear
        alerts_found = []
        
        async def capture_alert(dialog):
            alert_message = dialog.message
            alerts_found.append(alert_message)
            print(f"\n🚨 USER SEES THIS ALERT: '{alert_message}'")
            await dialog.accept()
        
        page.on("dialog", capture_alert)
        
        try:
            print("🌐 User opens website...")
            await page.goto("http://localhost:5002", wait_until="domcontentloaded")
            
            print("⏱️  User waits just 1 second (impatient user behavior)...")
            await page.wait_for_timeout(1000)
            
            print("🔍 User looks for connect button...")
            connect_button = page.locator("#connect-drone-btn")
            
            # Wait for button to be visible but not necessarily for full connection
            await connect_button.wait_for(state="visible", timeout=5000)
            
            print("👆 User clicks connect button immediately!")
            await connect_button.click()
            
            print("⏳ Waiting to see what happens...")
            await page.wait_for_timeout(3000)
            
            print("\n" + "="*60)
            print("👤 REAL USER EXPERIENCE:")
            print("="*60)
            
            if alerts_found:
                print(f"❌ USER SAW {len(alerts_found)} ALERT(S):")
                for i, alert in enumerate(alerts_found, 1):
                    print(f"   Alert {i}: '{alert}'")
                    
                    # Check for the specific alert user reported
                    if "Not connected to WebGCS server" in alert:
                        print("   ⚠️  THIS IS THE EXACT PROBLEM USER REPORTED!")
                        
                    if "Connection to WebGCS server lost" in alert:
                        print("   ⚠️  THIS IS THE NEW MESSAGE - STILL SHOWING ERROR!")
                        
                return False  # Still has popup issue
            else:
                print("✅ NO ALERTS - User experience is good!")
                return True
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False
            
        finally:
            print("\n⏳ Keeping browser open to observe...")
            await page.wait_for_timeout(5000)
            await browser.close()

async def test_with_longer_wait():
    """Test with user who waits longer before clicking"""
    
    print("\n" + "="*60) 
    print("Testing with patient user who waits longer...")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()
        
        alerts_found = []
        
        async def capture_alert(dialog):
            alert_message = dialog.message
            alerts_found.append(alert_message)
            print(f"🚨 PATIENT USER SEES: '{alert_message}'")
            await dialog.accept()
        
        page.on("dialog", capture_alert)
        
        try:
            print("🌐 Patient user opens website...")
            await page.goto("http://localhost:5002", wait_until="networkidle")
            
            print("⏱️  Patient user waits 10 seconds...")
            await page.wait_for_timeout(10000)
            
            # Check connection status before clicking
            socket_connected = await page.evaluate("window.WebGCS?.socket?.connected")
            webgcs_connected = await page.evaluate("window.WebGCS?.connected")
            
            print(f"📊 Connection status after wait: Socket={socket_connected}, WebGCS={webgcs_connected}")
            
            connect_button = page.locator("#connect-drone-btn")
            await connect_button.click()
            
            await page.wait_for_timeout(3000)
            
            if alerts_found:
                print(f"❌ Even patient user saw alerts: {alerts_found}")
                return False
            else:
                print("✅ Patient user had no issues!")
                return True
                
        finally:
            await browser.close()

# Run both tests
if __name__ == "__main__":
    print("🧪 Testing Real User Behavior vs Fix")
    print("="*60)
    
    # Test impatient user (like reported issue)
    result1 = asyncio.run(test_real_user_behavior())
    
    # Test patient user 
    result2 = asyncio.run(test_with_longer_wait())
    
    print("\n📋 FINAL RESULTS:")
    print(f"Impatient user (1s wait): {'✅ Good' if result1 else '❌ Still has popup'}")
    print(f"Patient user (10s wait): {'✅ Good' if result2 else '❌ Still has popup'}")
    
    if not result1:
        print("\n⚠️  THE FIX DIDN'T WORK - User still sees popup!")
        print("Need to investigate further...")
    else:
        print("\n✅ THE FIX WORKED - No more popup!")
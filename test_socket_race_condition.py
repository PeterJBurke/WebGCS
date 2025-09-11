import asyncio
from playwright.async_api import async_playwright
import time

async def test_socket_race_condition():
    """Test for race condition where socket appears connected but isn't when button is clicked"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        alerts_captured = []
        
        async def capture_alert(dialog):
            alert_message = dialog.message
            alerts_captured.append(alert_message)
            print(f"🚨 ALERT: {alert_message}")
            await dialog.accept()
        
        page.on("dialog", capture_alert)
        
        try:
            print("🌐 Opening fresh browser tab to http://localhost:5002")
            await page.goto("http://localhost:5002", wait_until="domcontentloaded")
            
            # Wait just a short time - not full networkidle to simulate user clicking quickly
            print("⏱️  Quick wait (simulating impatient user)...")
            await page.wait_for_timeout(2000)
            
            print("🔍 Checking socket connection status...")
            
            # Check multiple times to catch race conditions
            for i in range(3):
                socket_connected = await page.evaluate("window.WebGCS?.socket?.connected")
                webgcs_exists = await page.evaluate("!!window.WebGCS")
                socket_exists = await page.evaluate("!!window.WebGCS?.socket")
                
                print(f"  Check {i+1}: WebGCS exists: {webgcs_exists}, Socket exists: {socket_exists}, Connected: {socket_connected}")
                await page.wait_for_timeout(500)
            
            # Find and click button immediately
            print("👆 Clicking connect button immediately...")
            connect_button = page.locator("#connect-drone-btn")
            await connect_button.wait_for(state="visible", timeout=5000)
            await connect_button.click()
            
            # Wait for alert
            print("⏳ Waiting for potential alert...")
            await page.wait_for_timeout(2000)
            
            # Check results
            if alerts_captured:
                for alert in alerts_captured:
                    if "Not connected to WebGCS server" in alert:
                        print(f"✅ REPRODUCED USER'S BUG: Found alert '{alert}'")
                        return True
                        
            print("❌ Could not reproduce the race condition")
            return False
            
        except Exception as e:
            print(f"❌ TEST ERROR: {e}")
            return False
            
        finally:
            await page.wait_for_timeout(3000)
            await browser.close()

async def test_with_server_restart():
    """Test by restarting server to trigger connection issues"""
    print("🔄 Testing with server restart scenario...")
    
    # Kill server to create disconnect condition
    import subprocess
    subprocess.run(["pkill", "-f", "python main.py"], capture_output=True)
    
    await asyncio.sleep(2)
    
    # Start browser while server is down
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        alerts_captured = []
        
        async def capture_alert(dialog):
            alert_message = dialog.message
            alerts_captured.append(alert_message)
            print(f"🚨 DISCONNECTED ALERT: {alert_message}")
            await dialog.accept()
        
        page.on("dialog", capture_alert)
        
        try:
            print("🌐 Opening page while server is DOWN...")
            await page.goto("http://localhost:5002", timeout=10000, wait_until="domcontentloaded")
            
            # Wait a bit, then try to click 
            await page.wait_for_timeout(3000)
            
            print("👆 Trying to click connect button with server down...")
            connect_button = page.locator("#connect-drone-btn")
            if await connect_button.is_visible():
                await connect_button.click()
                await page.wait_for_timeout(2000)
                
                if alerts_captured:
                    for alert in alerts_captured:
                        if "Not connected to WebGCS server" in alert:
                            print(f"✅ REPRODUCED DISCONNECT SCENARIO: '{alert}'")
                            return True
                            
        except Exception as e:
            print(f"Expected error with server down: {e}")
            
        finally:
            await browser.close()
            
    return False

# Run both tests
if __name__ == "__main__":
    print("=" * 60)
    print("Testing Socket Race Condition Scenarios")
    print("=" * 60)
    
    result1 = asyncio.run(test_socket_race_condition())
    result2 = asyncio.run(test_with_server_restart())
    
    if result1 or result2:
        print("\n✅ SUCCESS: Reproduced the user's alert popup issue!")
        exit(1)  # Exit 1 means we found the bug
    else:
        print("\n❌ Could not reproduce the alert popup issue")
        exit(0)
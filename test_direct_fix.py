import asyncio
from playwright.async_api import async_playwright

async def test_direct_fix():
    """Direct test without browser cache interference"""
    
    async with async_playwright() as p:
        # Use incognito mode to avoid cache
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Clear any existing data
        await context.clear_cookies()
        
        alerts = []
        
        async def capture_alert(dialog):
            alerts.append(dialog.message)
            print(f"🚨 ALERT: {dialog.message}")
            await dialog.accept()
        
        page.on("dialog", capture_alert)
        
        # Monitor console for errors
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            if msg.type == 'error':
                print(f"❌ CONSOLE ERROR: {msg.text}")
            elif 'connect' in msg.text.lower():
                print(f"🔗 CONNECTION: {msg.text}")
        
        page.on("console", handle_console)
        
        try:
            print("🆕 Opening fresh browser session...")
            await page.goto("http://localhost:5002", wait_until="domcontentloaded")
            
            # Check what version actually loaded
            version_check = await page.evaluate("""
                () => {
                    const scriptTags = Array.from(document.getElementsByTagName('script'));
                    const socketIOScript = scriptTags.find(script => script.src && script.src.includes('socket.io'));
                    return socketIOScript ? socketIOScript.src : 'not found';
                }
            """)
            print(f"📦 SocketIO version loading: {version_check}")
            
            print("⏳ Waiting for initialization...")
            await page.wait_for_timeout(15000)  # Wait 15 seconds for full init
            
            # Check connection state
            connection_state = await page.evaluate("""
                () => {
                    return {
                        webGCSExists: typeof window.WebGCS !== 'undefined',
                        socketExists: window.WebGCS?.socket !== undefined,
                        socketConnected: window.WebGCS?.socket?.connected || false,
                        webGCSConnected: window.WebGCS?.connected || false,
                        socketId: window.WebGCS?.socket?.id || null,
                        ioExists: typeof io !== 'undefined'
                    };
                }
            """)
            
            print(f"📊 Connection state after 15s wait:")
            for key, value in connection_state.items():
                print(f"   {key}: {value}")
            
            # Only click if connection looks good
            if connection_state['socketConnected']:
                print("✅ Connection established! Testing button click...")
                button = page.locator("#connect-drone-btn")
                await button.click()
                await page.wait_for_timeout(2000)
            else:
                print("❌ Connection not established, clicking anyway to test...")
                button = page.locator("#connect-drone-btn")
                await button.click()
                await page.wait_for_timeout(2000)
            
            print(f"\n📋 RESULTS:")
            print(f"Alerts shown: {len(alerts)}")
            for alert in alerts:
                print(f"   - {alert}")
                
            if not alerts:
                print("✅ SUCCESS: No alerts shown to user!")
                return True
            else:
                print("❌ FAILED: User still sees alerts")
                return False
                
        finally:
            await page.wait_for_timeout(3000)
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_direct_fix())
    print(f"\nFinal result: {'✅ FIXED' if result else '❌ STILL BROKEN'}")
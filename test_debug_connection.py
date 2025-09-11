import asyncio
from playwright.async_api import async_playwright

async def debug_connection_issue():
    """Debug what's happening with the SocketIO connection"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Capture console messages
        console_messages = []
        
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            print(f"CONSOLE [{msg.type}]: {msg.text}")
        
        page.on("console", handle_console)
        
        # Capture network requests
        def handle_request(request):
            if 'socket.io' in request.url:
                print(f"NETWORK REQUEST: {request.method} {request.url}")
        
        def handle_response(response):
            if 'socket.io' in response.url:
                print(f"NETWORK RESPONSE: {response.status} {response.url}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        try:
            print("🌐 Opening page and watching for connection issues...")
            await page.goto("http://localhost:5002", wait_until="domcontentloaded")
            
            print("\n⏳ Waiting and checking JavaScript state every 2 seconds...")
            
            for i in range(6):  # Check 6 times over 12 seconds
                await page.wait_for_timeout(2000)
                
                # Check if JavaScript objects exist
                webgcs_exists = await page.evaluate("typeof window.WebGCS !== 'undefined'")
                io_exists = await page.evaluate("typeof io !== 'undefined'")
                socket_exists = await page.evaluate("window.WebGCS?.socket !== undefined")
                socket_connected = await page.evaluate("window.WebGCS?.socket?.connected")
                webgcs_connected = await page.evaluate("window.WebGCS?.connected")
                
                print(f"\n🔍 Check {i+1} ({i*2+2}s):")
                print(f"  WebGCS object exists: {webgcs_exists}")
                print(f"  SocketIO 'io' exists: {io_exists}")
                print(f"  Socket object exists: {socket_exists}")
                print(f"  Socket connected: {socket_connected}")
                print(f"  WebGCS connected: {webgcs_connected}")
                
                if socket_exists and socket_connected:
                    print("  ✅ Connection established!")
                    break
                elif not io_exists:
                    print("  ❌ SocketIO library not loaded!")
                elif not webgcs_exists:
                    print("  ❌ WebGCS not initialized!")
                elif not socket_exists:
                    print("  ❌ Socket not created!")
                else:
                    print("  ⏳ Still trying to connect...")
            
            print("\n📋 FINAL DIAGNOSIS:")
            print("="*50)
            
            # Final check
            final_webgcs = await page.evaluate("typeof window.WebGCS !== 'undefined'")
            final_io = await page.evaluate("typeof io !== 'undefined'")
            final_socket = await page.evaluate("window.WebGCS?.socket !== undefined")
            final_connected = await page.evaluate("window.WebGCS?.socket?.connected")
            
            if not final_io:
                print("❌ PROBLEM: SocketIO library failed to load")
                print("   - Check if CDN is accessible")
                print("   - Check network connectivity")
                
            elif not final_webgcs:
                print("❌ PROBLEM: WebGCS object not initialized")
                print("   - Check if main.js is loaded")
                print("   - Check for JavaScript errors")
                
            elif not final_socket:
                print("❌ PROBLEM: Socket object not created")
                print("   - Check connection.js initialization")
                print("   - Check if ConnectionManager is created")
                
            elif not final_connected:
                print("❌ PROBLEM: Socket exists but not connected")
                print("   - Check server is running on correct port")
                print("   - Check for CORS or networking issues")
                
            else:
                print("✅ Connection appears to be working")
            
            # Show recent console messages
            print(f"\n📝 Console messages ({len(console_messages)} total):")
            for msg in console_messages[-10:]:
                print(f"   {msg}")
            
        finally:
            await page.wait_for_timeout(3000)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_connection_issue())
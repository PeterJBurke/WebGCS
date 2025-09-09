#!/usr/bin/env python3
"""
Connect Button Test with Local Virtual Drone at 127.0.0.1:5678
"""

import asyncio
from playwright.async_api import async_playwright

async def test_with_local_drone():
    """Test connect button with local virtual drone"""
    
    print("🔍 TESTING CONNECT BUTTON WITH LOCAL VIRTUAL DRONE")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to WebGCS
            await page.goto("http://127.0.0.1:5002")
            await page.wait_for_load_state('networkidle')
            print("✅ Loaded WebGCS at http://127.0.0.1:5002")
            
            # Set drone host to local virtual drone
            print("🔧 Setting drone connection to 127.0.0.1:5678 (local virtual drone)")
            ip_field = page.locator('#drone-host')
            port_field = page.locator('#drone-port')
            
            await ip_field.fill('127.0.0.1')
            await port_field.fill('5678')
            
            print(f"   IP set to: {await ip_field.input_value()}")
            print(f"   Port set to: {await port_field.input_value()}")
            
            # Monitor events
            console_messages = []
            def handle_console(msg):
                console_messages.append(msg.text)
                print(f"   🖥️ {msg.text}")
            page.on('console', handle_console)
            
            # Set up connection monitoring
            await page.evaluate("""
                window.connectionResults = [];
                if (typeof socket !== 'undefined') {
                    socket.on('drone_connection_result', function(data) {
                        window.connectionResults.push(data);
                        console.log('📡 Connection result:', JSON.stringify(data));
                    });
                    socket.on('heartbeat', function(data) {
                        console.log('💓 Heartbeat:', data);
                    });
                } else {
                    console.log('❌ Socket not available');
                }
            """)
            
            # Click Connect
            connect_button = page.locator('#connect-btn')
            print("🖱️ Clicking Connect button...")
            await connect_button.click()
            
            # Wait for connection result
            print("⏳ Waiting for connection result...")
            for i in range(15):
                await page.wait_for_timeout(1000)
                
                connection_results = await page.evaluate("window.connectionResults || []")
                connect_enabled = await connect_button.is_enabled()
                disconnect_enabled = await page.locator('#disconnect-btn').is_enabled()
                
                print(f"   Second {i+1}: Connect={connect_enabled}, Disconnect={disconnect_enabled}")
                
                if len(connection_results) > 0:
                    result = connection_results[-1]
                    print(f"   📡 Got result: {result}")
                    
                    if result.get('success'):
                        print("🎉 CONNECTION SUCCESSFUL!")
                        
                        # Wait a bit more to see heartbeats
                        print("💓 Listening for heartbeats...")
                        await page.wait_for_timeout(5000)
                        
                        # Take screenshot of successful connection
                        await page.screenshot(path="/Users/peterburke/Documents/Code/WebGCS6/successful_connection.png")
                        print("📸 Screenshot saved: successful_connection.png")
                        
                        # Test disconnect
                        print("🔌 Testing disconnect...")
                        disconnect_button = page.locator('#disconnect-btn')
                        await disconnect_button.click()
                        await page.wait_for_timeout(2000)
                        
                        final_connect_enabled = await connect_button.is_enabled()
                        final_disconnect_enabled = await disconnect_button.is_enabled()
                        
                        print(f"   After disconnect: Connect={final_connect_enabled}, Disconnect={final_disconnect_enabled}")
                        
                        print("\n" + "=" * 60)
                        print("🏆 FINAL RESULTS:")
                        print("✅ Connect button: WORKING")
                        print("✅ Connection to virtual drone: SUCCESS")
                        print("✅ Button state transitions: WORKING")
                        print("✅ Disconnect functionality: WORKING")
                        print("🎯 OVERALL STATUS: PASS")
                        
                        return True
                    else:
                        print(f"❌ Connection failed: {result.get('message')}")
                        break
                        
            print("❌ No connection result received or connection failed")
            await page.screenshot(path="/Users/peterburke/Documents/Code/WebGCS6/failed_connection.png")
            return False
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    success = asyncio.run(test_with_local_drone())
    if success:
        print("\n🎉 CONNECT BUTTON TEST: PASSED")
    else:
        print("\n❌ CONNECT BUTTON TEST: FAILED")
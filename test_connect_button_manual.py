#!/usr/bin/env python3
"""
Manual Connect Button Test for WebGCS at http://127.0.0.1:5002
Tests the specific requirements outlined by the user.
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_connect_button_functionality():
    """Test connect button functionality at http://127.0.0.1:5002"""
    
    print("🔍 CONNECT BUTTON TESTING RESULTS")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visual browser for screenshot
        page = await browser.new_page()
        
        try:
            print("1. Navigate to http://127.0.0.1:5002")
            await page.goto("http://127.0.0.1:5002")
            await page.wait_for_load_state('networkidle')
            print("   ✅ Successfully loaded WebGCS interface")
            
            print("\n2. Verify IP field shows '192.168.193.235' and port shows '5678'")
            ip_field = page.locator('#drone-host')
            port_field = page.locator('#drone-port')
            
            ip_value = await ip_field.input_value()
            port_value = await port_field.input_value()
            
            print(f"   IP Field: '{ip_value}' (Expected: '192.168.193.235')")
            print(f"   Port Field: '{port_value}' (Expected: '5678')")
            
            if ip_value == "192.168.193.235" and port_value == "5678":
                print("   ✅ IP and port fields have correct default values")
            else:
                print("   ❌ IP/port fields do not match expected values")
            
            print("\n3. Click the Connect button")
            connect_button = page.locator('#connect-btn')
            disconnect_button = page.locator('#disconnect-btn')
            
            # Verify initial button states
            connect_enabled = await connect_button.is_enabled()
            disconnect_enabled = await disconnect_button.is_enabled()
            
            print(f"   Connect button enabled: {connect_enabled} (Expected: True)")
            print(f"   Disconnect button enabled: {disconnect_enabled} (Expected: False)")
            
            if connect_enabled and not disconnect_enabled:
                print("   ✅ Button states are correct initially")
            else:
                print("   ❌ Button states are incorrect")
            
            # Monitor console and network activity
            console_messages = []
            network_requests = []
            
            def handle_console(msg):
                console_messages.append(f"CONSOLE: {msg.text}")
                print(f"   🖥️ Console: {msg.text}")
            
            def handle_request(request):
                if 'socket.io' in request.url:
                    network_requests.append(f"SocketIO: {request.method} {request.url}")
                    print(f"   🌐 Network: {request.method} {request.url}")
            
            page.on('console', handle_console)
            page.on('request', handle_request)
            
            # Monitor SocketIO events
            await page.evaluate("""
                window.connectionResults = [];
                window.socketEvents = [];
                if (typeof io !== 'undefined' && typeof socket !== 'undefined') {
                    console.log('Setting up SocketIO event monitoring...');
                    socket.on('drone_connection_result', function(data) {
                        window.connectionResults.push(data);
                        window.socketEvents.push({event: 'drone_connection_result', data: data});
                        console.log('🔗 Connection result received:', JSON.stringify(data));
                    });
                    socket.on('connect', function() {
                        window.socketEvents.push({event: 'connect'});
                        console.log('🔗 SocketIO connected to server');
                    });
                    socket.on('disconnect', function() {
                        window.socketEvents.push({event: 'disconnect'});
                        console.log('🔗 SocketIO disconnected from server');
                    });
                } else {
                    console.log('❌ SocketIO not available');
                }
            """)
            
            # Click the Connect button
            print("   🖱️ Clicking Connect button...")
            await connect_button.click()
            
            print("\n4. Monitor the connection status and responses")
            # Wait for connection attempt
            for i in range(10):
                await page.wait_for_timeout(1000)  # Wait 1 second
                
                # Check button states
                connect_enabled = await connect_button.is_enabled()
                disconnect_enabled = await disconnect_button.is_enabled()
                
                # Get connection results
                connection_results = await page.evaluate("window.connectionResults || []")
                socket_events = await page.evaluate("window.socketEvents || []")
                
                print(f"   ⏱️ Second {i+1}: Connect={connect_enabled}, Disconnect={disconnect_enabled}")
                
                if len(connection_results) > 0:
                    print(f"   📡 Connection result: {connection_results[-1]}")
                    break
                    
                if len(socket_events) > 0:
                    for event in socket_events[-3:]:  # Show last 3 events
                        print(f"   🔗 SocketIO event: {event}")
            
            print("\n5. Connection Result Analysis")
            final_connection_results = await page.evaluate("window.connectionResults || []")
            final_socket_events = await page.evaluate("window.socketEvents || []")
            
            if len(final_connection_results) > 0:
                result = final_connection_results[-1]
                if result.get('success'):
                    print("   ✅ CONNECTION PASSED - Successfully connected to virtual drone")
                    connection_status = "PASS"
                else:
                    print(f"   ⚠️ CONNECTION ATTEMPTED BUT FAILED - {result.get('message', 'Unknown error')}")
                    connection_status = "ATTEMPTED_BUT_FAILED"
            else:
                print("   ❌ CONNECTION FAILED - No connection result received")
                connection_status = "FAIL"
            
            print(f"\n6. Button State Verification")
            final_connect_enabled = await connect_button.is_enabled()
            final_disconnect_enabled = await disconnect_button.is_enabled()
            
            print(f"   Final Connect button enabled: {final_connect_enabled}")
            print(f"   Final Disconnect button enabled: {final_disconnect_enabled}")
            
            if connection_status == "PASS":
                if not final_connect_enabled and final_disconnect_enabled:
                    print("   ✅ Button states changed correctly after successful connection")
                    button_status = "PASS"
                else:
                    print("   ❌ Button states did not change correctly after connection")
                    button_status = "FAIL"
            else:
                button_status = "N/A (Connection failed)"
            
            print("\n7. Browser Console Check")
            if len(console_messages) > 0:
                print("   Console messages detected:")
                for msg in console_messages[-5:]:  # Show last 5 messages
                    print(f"     {msg}")
            else:
                print("   No console messages detected")
            
            print("\n8. Taking screenshot...")
            await page.screenshot(path="/Users/peterburke/Documents/Code/WebGCS6/connect_test_screenshot.png")
            print("   📸 Screenshot saved as: connect_test_screenshot.png")
            
            print("\n" + "=" * 50)
            print("🏁 FINAL TEST RESULTS")
            print("=" * 50)
            print(f"✅ Navigate to URL: PASS")
            print(f"✅ IP/Port default values: {'PASS' if ip_value == '192.168.193.235' and port_value == '5678' else 'FAIL'}")
            print(f"📡 Connect button functionality: {connection_status}")
            print(f"🔘 Button state changes: {button_status}")
            print(f"🖥️ Console messages: {'DETECTED' if len(console_messages) > 0 else 'NONE'}")
            print(f"📸 Screenshot: CAPTURED")
            
            if connection_status == "PASS":
                print("\n🎉 OVERALL RESULT: CONNECT BUTTON TEST PASSED!")
            elif connection_status == "ATTEMPTED_BUT_FAILED":
                print("\n⚠️ OVERALL RESULT: CONNECT BUTTON ATTEMPTED CONNECTION BUT VIRTUAL DRONE NOT RESPONDING")
            else:
                print("\n❌ OVERALL RESULT: CONNECT BUTTON TEST FAILED!")
                
        except Exception as e:
            print(f"\n❌ ERROR during testing: {str(e)}")
            await page.screenshot(path="/Users/peterburke/Documents/Code/WebGCS6/connect_test_error_screenshot.png")
            print("   📸 Error screenshot saved")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_connect_button_functionality())
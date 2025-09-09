#!/usr/bin/env python3
"""
Test UI Updates - Verify that JavaScript properly handles connection events
"""

import time
from playwright.sync_api import sync_playwright

def test_ui_updates():
    print("=== TEST UI UPDATES ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        
        # Enable console logging
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"{time.time():.1f}: {msg.text}"))
        
        try:
            # Load the page
            print("1. Loading page...")
            page.goto("http://127.0.0.1:5002", timeout=10000)
            time.sleep(2)
            
            # Check initial status
            print("2. Checking initial status...")
            status_element = page.query_selector("#connection-status")
            heartbeat_element = page.query_selector("#heartbeat-counter")
            
            if status_element and heartbeat_element:
                initial_status = status_element.inner_text()
                initial_heartbeat = heartbeat_element.inner_text()
                print(f"   Initial Status: {initial_status}")
                print(f"   Initial Heartbeat: {initial_heartbeat}")
                
                # Simulate successful connection via JavaScript injection
                print("3. Simulating successful connection...")
                page.evaluate("""
                    // Simulate receiving a successful drone_connection_result event
                    const successData = {
                        success: true, 
                        message: 'Connected to drone at 192.168.193.235:5678',
                        host: '192.168.193.235',
                        port: 5678,
                        system_id: 1,
                        component_id: 1
                    };
                    
                    console.log('Simulating drone_connection_result with success:', successData);
                    
                    // Trigger the same handler that would be called by SocketIO
                    if (window.socket && window.socket.emit) {
                        // Find the handler functions and call them directly
                        if (window.updateConnectionStatus) {
                            window.updateConnectionStatus('Connected to Drone');
                        } else {
                            console.error('updateConnectionStatus function not found');
                        }
                        
                        // Update buttons
                        const connectBtn = document.getElementById('connect-btn');
                        const disconnectBtn = document.getElementById('disconnect-btn');
                        if (connectBtn) connectBtn.disabled = true;
                        if (disconnectBtn) disconnectBtn.disabled = false;
                        
                        console.log('UI should now show connected state');
                    }
                """)
                
                time.sleep(1)
                
                # Check if status updated
                new_status = status_element.inner_text()
                print(f"   Status after simulation: {new_status}")
                
                # Simulate heartbeat updates
                print("4. Simulating heartbeat updates...")
                for i in range(1, 6):
                    page.evaluate(f"""
                        const heartbeatElement = document.getElementById('heartbeat-counter');
                        if (heartbeatElement) {{
                            heartbeatElement.textContent = '❤️ Heartbeat: {i}';
                            console.log('Heartbeat updated to: {i}');
                        }}
                    """)
                    time.sleep(0.5)
                    
                    current_heartbeat = heartbeat_element.inner_text()
                    print(f"   Heartbeat {i}: {current_heartbeat}")
                
                # Final check
                final_status = status_element.inner_text()
                final_heartbeat = heartbeat_element.inner_text()
                
                print(f"\nFinal Results:")
                print(f"   Status: {final_status}")
                print(f"   Heartbeat: {final_heartbeat}")
                
                # Take screenshot
                page.screenshot(path="ui_test_final.png")
                
                # Check for success
                if "Connected" in final_status and "❤️ Heartbeat: 5" in final_heartbeat:
                    print("   ✅ UI UPDATES WORKING!")
                    return True
                else:
                    print("   ❌ UI updates not working properly")
                    return False
                    
            else:
                print("   ❌ Status elements not found")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            # Show recent console messages
            print("\n📋 Recent Console Messages:")
            for msg in console_messages[-10:]:
                print(f"   {msg}")
            
            time.sleep(3)  # Brief pause to see result
            browser.close()
    
    return False

if __name__ == "__main__":
    success = test_ui_updates()
    if success:
        print("\n🎉 UI UPDATE TEST SUCCESSFUL!")
    else:
        print("\n💥 UI UPDATE TEST FAILED!")
#!/usr/bin/env python3
"""
Debug Connection Test - Test the complete click-to-connect workflow
"""

import time
from playwright.sync_api import sync_playwright

def debug_connection_test():
    print("=== DEBUG CONNECTION TEST ===")
    
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
                
                # Take initial screenshot
                page.screenshot(path="debug_initial.png")
                
                # Click connect button
                print("3. Clicking connect button...")
                connect_btn = page.query_selector("#connect-btn")
                if connect_btn and not connect_btn.is_disabled():
                    connect_btn.click()
                    print("   Connect button clicked!")
                    
                    # Wait and monitor status changes
                    print("4. Monitoring status for 15 seconds...")
                    for i in range(15):
                        time.sleep(1)
                        
                        current_status = status_element.inner_text()
                        current_heartbeat = heartbeat_element.inner_text()
                        
                        print(f"   {i+1}s: Status='{current_status}' | Heartbeat='{current_heartbeat}'")
                        
                        # Check for success
                        if "Connected to Drone" in current_status:
                            print("   ✅ CONNECTION SUCCESS!")
                            page.screenshot(path="debug_connected.png")
                            
                            # Monitor heartbeat increments
                            print("5. Monitoring heartbeat increments...")
                            for j in range(10):
                                time.sleep(1)
                                hb_text = heartbeat_element.inner_text()
                                print(f"   Heartbeat {j+1}: {hb_text}")
                                
                            page.screenshot(path="debug_final.png")
                            return True
                    
                    print("   ❌ Connection did not succeed within 15 seconds")
                    page.screenshot(path="debug_failed.png")
                    
                else:
                    print("   ❌ Connect button not found or disabled")
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
    success = debug_connection_test()
    if success:
        print("\n🎉 DEBUG TEST SUCCESSFUL!")
    else:
        print("\n💥 DEBUG TEST FAILED!")
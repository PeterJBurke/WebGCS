#!/usr/bin/env python3
"""
Quick UI Test - Check if the connection status now displays correctly
"""

import time
from playwright.sync_api import sync_playwright

def quick_ui_test():
    print("=== QUICK UI TEST ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Load the page
            print("Loading page...")
            page.goto("http://127.0.0.1:5002", timeout=10000)
            
            # Wait for initial load
            time.sleep(3)
            
            # Check connection status
            status_element = page.query_selector("#connection-status")
            heartbeat_element = page.query_selector("#heartbeat-counter")
            
            if status_element and heartbeat_element:
                status_text = status_element.inner_text()
                heartbeat_text = heartbeat_element.inner_text()
                
                print(f"Connection Status: {status_text}")
                print(f"Heartbeat Counter: {heartbeat_text}")
                
                if "Connected" in status_text and "Heartbeat:" in heartbeat_text:
                    print("✅ SUCCESS: UI shows connected status with heartbeat!")
                    
                    # Take a screenshot
                    page.screenshot(path="ui_fixed_success.png")
                    print("Screenshot saved: ui_fixed_success.png")
                    
                    return True
                else:
                    print("❌ ISSUE: UI status not showing connection properly")
                    return False
            else:
                print("❌ ERROR: Could not find status elements")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            time.sleep(2)  # Brief pause to see result
            browser.close()

if __name__ == "__main__":
    success = quick_ui_test()
    if success:
        print("\n🎉 UI FIX SUCCESSFUL!")
    else:
        print("\n💥 UI FIX FAILED!")
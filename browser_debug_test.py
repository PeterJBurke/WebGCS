#!/usr/bin/env python3
"""
Browser Debug Test - Check browser console for JavaScript errors
"""

import time
from playwright.sync_api import sync_playwright

def test_browser_console():
    """Check for JavaScript console errors and network issues"""
    
    print("=== BROWSER DEBUG TEST ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context()
        
        # Collect console messages
        console_messages = []
        network_errors = []
        
        page = context.new_page()
        
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            print(f"Console [{msg.type}]: {msg.text}")
            
        def handle_request_failed(request):
            network_errors.append(f"Request failed: {request.url} - {request.failure}")
            print(f"Network error: {request.url} - {request.failure}")
        
        page.on("console", handle_console)
        page.on("requestfailed", handle_request_failed)
        
        try:
            # Load the page
            print("\n1. Loading website...")
            response = page.goto("http://127.0.0.1:5002", timeout=30000)
            print(f"Page loaded with status: {response.status}")
            
            # Wait for elements to be ready
            time.sleep(2)
            
            # Check if SocketIO is connected
            print("\n2. Checking SocketIO connection status...")
            socketio_status = page.evaluate("() => { return typeof socket !== 'undefined' && socket.connected; }")
            print(f"SocketIO connected: {socketio_status}")
            
            # Check if elements exist
            print("\n3. Checking page elements...")
            elements_to_check = [
                "#drone-host",
                "#drone-port", 
                "#connect-btn",
                "#connection-status",
                "#heartbeat-counter"
            ]
            
            for element_id in elements_to_check:
                element = page.query_selector(element_id)
                if element:
                    value = ""
                    if element_id in ["#drone-host", "#drone-port"]:
                        value = f" (value: {element.input_value()})"
                    elif element_id in ["#connection-status", "#heartbeat-counter"]:
                        value = f" (text: {element.inner_text()})"
                    print(f"  ✅ {element_id} found{value}")
                else:
                    print(f"  ❌ {element_id} NOT found")
            
            # Try to click connect and see what happens
            print("\n4. Testing connect button click...")
            connect_btn = page.query_selector("#connect-btn")
            if connect_btn:
                print(f"Connect button enabled: {not connect_btn.is_disabled()}")
                
                # Set up console monitoring for network activity
                print("Clicking connect button...")
                connect_btn.click()
                
                # Wait and monitor for 10 seconds
                for i in range(10):
                    time.sleep(1)
                    print(f"  Monitoring... {i+1}s")
                    
                    # Check connection status
                    status_element = page.query_selector("#connection-status")
                    if status_element:
                        status_text = status_element.inner_text()
                        print(f"    Status: {status_text}")
                
            else:
                print("Connect button not found!")
            
            # Show summary
            print(f"\n=== SUMMARY ===")
            print(f"Console messages: {len(console_messages)}")
            for msg in console_messages[-10:]:  # Last 10 messages
                print(f"  {msg}")
                
            print(f"Network errors: {len(network_errors)}")
            for error in network_errors:
                print(f"  {error}")
                
        except Exception as e:
            print(f"❌ Error during test: {e}")
        finally:
            # Keep browser open for manual inspection
            print("\nBrowser will remain open for 10 seconds for manual inspection...")
            time.sleep(10)
            browser.close()

if __name__ == "__main__":
    test_browser_console()
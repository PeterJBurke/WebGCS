#!/usr/bin/env python3
"""
Test script to verify disconnect button functionality
1. Load the website
2. Press the disconnect button
3. Read the console of the browser
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException

def setup_chrome_driver():
    """Setup Chrome driver with console logging enabled"""
    options = Options()
    options.add_argument('--headless')  # Run in background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Enable logging
    options.add_argument('--enable-logging')
    options.add_argument('--log-level=0')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'driver': 'ALL', 'performance': 'ALL'})
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except WebDriverException as e:
        print(f"Failed to create Chrome driver: {e}")
        print("Trying with system Chrome...")
        # Try without specifying service
        return webdriver.Chrome(options=options)

def test_disconnect_button():
    """Main test function"""
    driver = None
    test_results = {
        'success': False,
        'console_logs': [],
        'errors': [],
        'button_found': False,
        'button_clicked': False,
        'disconnect_message_found': False,
        'javascript_errors': []
    }
    
    try:
        print("🚀 Starting disconnect button test...")
        
        # Step 1: Setup browser driver
        print("1️⃣ Setting up Chrome driver...")
        driver = setup_chrome_driver()
        print("   ✅ Chrome driver initialized")
        
        # Step 2: Load the website
        print("2️⃣ Loading WebGCS website...")
        driver.get("http://localhost:5001")
        print("   ✅ Website loaded")
        
        # Wait for page to fully load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)  # Additional wait for JavaScript initialization
        
        # Get initial console logs
        initial_logs = driver.get_log('browser')
        print(f"   📋 Initial console logs: {len(initial_logs)} entries")
        
        # Step 3: Find the disconnect button
        print("3️⃣ Looking for disconnect button...")
        try:
            disconnect_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "disconnect-btn"))
            )
            test_results['button_found'] = True
            print("   ✅ Disconnect button found")
            
            # Check if button is visible and enabled
            is_visible = disconnect_btn.is_displayed()
            is_enabled = disconnect_btn.is_enabled()
            print(f"   🔍 Button visible: {is_visible}, enabled: {is_enabled}")
            
        except TimeoutException:
            test_results['errors'].append("Disconnect button not found")
            print("   ❌ Disconnect button not found!")
            return test_results
        
        # Step 4: Click the disconnect button
        print("4️⃣ Clicking disconnect button...")
        try:
            # Force click using JavaScript to ensure it works
            driver.execute_script("document.getElementById('disconnect-btn').click();")
            test_results['button_clicked'] = True
            print("   ✅ Disconnect button clicked")
            
            # Wait a moment for any effects
            time.sleep(2)
            
        except Exception as e:
            test_results['errors'].append(f"Failed to click disconnect button: {str(e)}")
            print(f"   ❌ Failed to click button: {e}")
        
        # Step 5: Capture console logs after clicking
        print("5️⃣ Capturing console logs...")
        time.sleep(1)  # Wait for logs to appear
        
        console_logs = driver.get_log('browser')
        test_results['console_logs'] = []
        
        for log_entry in console_logs:
            log_data = {
                'timestamp': log_entry['timestamp'],
                'level': log_entry['level'],
                'message': log_entry['message'],
                'source': log_entry.get('source', 'unknown')
            }
            test_results['console_logs'].append(log_data)
            
            # Check for specific messages
            message = log_entry['message'].lower()
            if 'disconnect' in message and ('clicked' in message or 'button' in message):
                test_results['disconnect_message_found'] = True
            
            # Track JavaScript errors
            if log_entry['level'] == 'SEVERE':
                test_results['javascript_errors'].append(log_data)
        
        print(f"   📋 Total console logs captured: {len(console_logs)}")
        print(f"   🔍 Disconnect message found: {test_results['disconnect_message_found']}")
        print(f"   ⚠️  JavaScript errors: {len(test_results['javascript_errors'])}")
        
        # Step 6: Check for server-side disconnect request
        print("6️⃣ Checking page state...")
        
        # Check if there are any network requests or state changes
        try:
            # Get WebSocket connection status from the page
            connection_status = driver.execute_script("""
                return {
                    websocket_ready: window.WebGCS && window.WebGCS.socket ? window.WebGCS.socket.connected : false,
                    connection_manager_found: !!window.ConnectionManager,
                    debug_info: window.WebGCS ? {
                        socket_exists: !!window.WebGCS.socket,
                        drone_connected: window.WebGCS.droneConnected
                    } : null
                };
            """)
            
            test_results['page_state'] = connection_status
            print(f"   🔍 Page state: {connection_status}")
            
        except Exception as e:
            test_results['errors'].append(f"Failed to get page state: {str(e)}")
        
        # Determine overall success
        test_results['success'] = (
            test_results['button_found'] and 
            test_results['button_clicked'] and
            len(test_results['javascript_errors']) == 0
        )
        
        print(f"   {'✅' if test_results['success'] else '❌'} Test result: {'SUCCESS' if test_results['success'] else 'FAILED'}")
        
    except Exception as e:
        test_results['errors'].append(f"Test execution error: {str(e)}")
        print(f"❌ Test failed with error: {e}")
        
    finally:
        if driver:
            driver.quit()
            print("🧹 Browser driver closed")
    
    return test_results

def print_detailed_results(results):
    """Print detailed test results"""
    print("\n" + "="*60)
    print("DETAILED TEST RESULTS")
    print("="*60)
    
    print(f"✅ Button Found: {results['button_found']}")
    print(f"✅ Button Clicked: {results['button_clicked']}")
    print(f"✅ Disconnect Message Found: {results['disconnect_message_found']}")
    print(f"❌ JavaScript Errors: {len(results.get('javascript_errors', []))}")
    print(f"🎯 Overall Success: {results['success']}")
    
    if results.get('errors'):
        print(f"\n🚨 ERRORS ({len(results['errors'])}):")
        for i, error in enumerate(results['errors'], 1):
            print(f"  {i}. {error}")
    
    if results.get('javascript_errors'):
        print(f"\n⚠️  JAVASCRIPT ERRORS ({len(results['javascript_errors'])}):")
        for i, error in enumerate(results['javascript_errors'], 1):
            print(f"  {i}. [{error['level']}] {error['message']}")
    
    print(f"\n📋 CONSOLE LOGS ({len(results.get('console_logs', []))}):")
    for i, log in enumerate(results.get('console_logs', [])[:10], 1):  # Show first 10 logs
        level_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "SEVERE": "❌"}.get(log['level'], "📝")
        print(f"  {i}. {level_emoji} [{log['level']}] {log['message']}")
    
    if len(results.get('console_logs', [])) > 10:
        print(f"  ... and {len(results['console_logs']) - 10} more logs")
    
    if results.get('page_state'):
        print(f"\n🔍 PAGE STATE:")
        page_state = results['page_state']
        for key, value in page_state.items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    print("🧪 WebGCS Disconnect Button Test")
    print("="*40)
    
    results = test_disconnect_button()
    print_detailed_results(results)
    
    # Save results to file
    with open('disconnect_button_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: disconnect_button_test_results.json")
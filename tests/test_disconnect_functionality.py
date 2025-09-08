#!/usr/bin/env python3
"""
Comprehensive disconnect test that verifies the drone actually gets disconnected.
1. Load the website
2. Connect to drone
3. Click disconnect button  
4. Verify drone is actually disconnected
"""

import time
import json
import requests
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
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
        return webdriver.Chrome(options=options)
    except WebDriverException:
        return webdriver.Chrome(options=options)

class ServerLogMonitor:
    """Monitor server logs for disconnect events"""
    def __init__(self):
        self.logs = []
        self.monitoring = False
        
    def start_monitoring(self):
        self.monitoring = True
        self.logs = []
        
    def stop_monitoring(self):
        self.monitoring = False
        
    def add_log(self, message):
        if self.monitoring:
            self.logs.append({
                'timestamp': time.time(),
                'message': message
            })

def check_server_health():
    """Check if server is responsive"""
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def test_full_disconnect_functionality():
    """Comprehensive test for disconnect functionality"""
    driver = None
    server_monitor = ServerLogMonitor()
    
    test_results = {
        'success': False,
        'steps': [],
        'server_health_before': None,
        'server_health_after': None,
        'connection_state_before': None,
        'connection_state_after': None,
        'button_clicked': False,
        'disconnect_events': [],
        'server_logs': [],
        'errors': []
    }
    
    def add_step(step, success, details=""):
        test_results['steps'].append({
            'step': step,
            'success': success,
            'details': details,
            'timestamp': time.time()
        })
        status = "✅" if success else "❌"
        print(f"  {status} {step}" + (f": {details}" if details else ""))
    
    try:
        print("🧪 Comprehensive Disconnect Functionality Test")
        print("="*60)
        
        # Step 1: Check server health
        print("1️⃣ Checking server health...")
        health_ok, health_data = check_server_health()
        test_results['server_health_before'] = health_data
        add_step("Server health check", health_ok, f"Health data: {health_data}")
        
        if not health_ok:
            test_results['errors'].append("Server not responding")
            return test_results
        
        # Step 2: Setup browser
        print("2️⃣ Setting up browser...")
        driver = setup_chrome_driver()
        add_step("Browser setup", True, "Chrome driver initialized")
        
        # Step 3: Load website
        print("3️⃣ Loading website...")
        driver.get("http://localhost:5001")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)  # Wait for JavaScript initialization
        add_step("Website loaded", True, "Page loaded and JS initialized")
        
        # Step 4: Check initial connection state
        print("4️⃣ Checking initial connection state...")
        initial_state = driver.execute_script("""
            return {
                websocket_connected: window.WebGCS && window.WebGCS.socket ? window.WebGCS.socket.connected : false,
                drone_connected: window.WebGCS ? window.WebGCS.droneConnected : false,
                connection_status_text: document.getElementById('connection-status') ? 
                    document.getElementById('connection-status').textContent : 'Not found',
                heartbeat_count: document.getElementById('heartbeat-counter') ? 
                    document.getElementById('heartbeat-counter').textContent : '0'
            };
        """)
        test_results['connection_state_before'] = initial_state
        add_step("Initial state captured", True, f"State: {initial_state}")
        
        # Step 5: Connect to drone first (if not already connected)
        print("5️⃣ Ensuring drone connection...")
        if not initial_state.get('drone_connected', False):
            try:
                connect_btn = driver.find_element(By.ID, "connect-btn")
                if connect_btn.is_enabled():
                    connect_btn.click()
                    add_step("Connect button clicked", True, "Attempting to connect to drone")
                    
                    # Wait for connection to establish
                    for i in range(10):  # Wait up to 10 seconds
                        time.sleep(1)
                        state = driver.execute_script("return window.WebGCS ? window.WebGCS.droneConnected : false;")
                        if state:
                            break
                    
                    connected = driver.execute_script("return window.WebGCS ? window.WebGCS.droneConnected : false;")
                    add_step("Drone connection established", connected, f"Connected: {connected}")
                else:
                    add_step("Connect button not available", False, "Button disabled or not found")
            except Exception as e:
                add_step("Connection attempt failed", False, str(e))
        else:
            add_step("Drone already connected", True, "Skipping connection step")
        
        # Step 6: Start monitoring for disconnect events
        print("6️⃣ Starting disconnect monitoring...")
        server_monitor.start_monitoring()
        
        # Get current connection state
        pre_disconnect_state = driver.execute_script("""
            return {
                websocket_connected: window.WebGCS && window.WebGCS.socket ? window.WebGCS.socket.connected : false,
                drone_connected: window.WebGCS ? window.WebGCS.droneConnected : false,
                connection_status_text: document.getElementById('connection-status') ? 
                    document.getElementById('connection-status').textContent : 'Not found',
                heartbeat_count: document.getElementById('heartbeat-counter') ? 
                    document.getElementById('heartbeat-counter').textContent : '0'
            };
        """)
        add_step("Pre-disconnect state captured", True, f"State: {pre_disconnect_state}")
        
        # Step 7: Click disconnect button
        print("7️⃣ Clicking disconnect button...")
        try:
            disconnect_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "disconnect-btn"))
            )
            
            # Force click using JavaScript to ensure it works
            driver.execute_script("document.getElementById('disconnect-btn').click();")
            test_results['button_clicked'] = True
            add_step("Disconnect button clicked", True, "Button click executed")
            
        except Exception as e:
            test_results['errors'].append(f"Failed to click disconnect button: {str(e)}")
            add_step("Disconnect button click", False, str(e))
            return test_results
        
        # Step 8: Wait and monitor for disconnect events
        print("8️⃣ Monitoring disconnect events...")
        disconnect_detected = False
        
        for i in range(10):  # Monitor for up to 10 seconds
            time.sleep(1)
            
            # Check browser console for disconnect messages
            console_logs = driver.get_log('browser')
            for log in console_logs:
                message = log.get('message', '').lower()
                if 'disconnect' in message:
                    test_results['disconnect_events'].append({
                        'source': 'browser_console',
                        'message': log['message'],
                        'timestamp': log['timestamp']
                    })
                    if not disconnect_detected:
                        disconnect_detected = True
                        add_step("Disconnect event detected in console", True, log['message'])
            
            # Check current connection state
            current_state = driver.execute_script("""
                return {
                    websocket_connected: window.WebGCS && window.WebGCS.socket ? window.WebGCS.socket.connected : false,
                    drone_connected: window.WebGCS ? window.WebGCS.droneConnected : false,
                    connection_status_text: document.getElementById('connection-status') ? 
                        document.getElementById('connection-status').textContent : 'Not found',
                    heartbeat_count: document.getElementById('heartbeat-counter') ? 
                        document.getElementById('heartbeat-counter').textContent : '0'
                };
            """)
            
            # Check if drone is actually disconnected
            if not current_state.get('drone_connected', True):
                add_step("Drone disconnection verified", True, f"Final state: {current_state}")
                test_results['connection_state_after'] = current_state
                break
            elif current_state.get('connection_status_text', '').lower().find('disconnect') >= 0:
                add_step("Disconnect status detected in UI", True, current_state.get('connection_status_text'))
                test_results['connection_state_after'] = current_state
                break
        else:
            # Timeout - capture final state
            final_state = driver.execute_script("""
                return {
                    websocket_connected: window.WebGCS && window.WebGCS.socket ? window.WebGCS.socket.connected : false,
                    drone_connected: window.WebGCS ? window.WebGCS.droneConnected : false,
                    connection_status_text: document.getElementById('connection-status') ? 
                        document.getElementById('connection-status').textContent : 'Not found',
                    heartbeat_count: document.getElementById('heartbeat-counter') ? 
                        document.getElementById('heartbeat-counter').textContent : '0'
                };
            """)
            test_results['connection_state_after'] = final_state
            add_step("Timeout waiting for disconnect", False, f"Final state: {final_state}")
        
        # Step 9: Check server health after disconnect
        print("9️⃣ Checking server health after disconnect...")
        health_ok_after, health_data_after = check_server_health()
        test_results['server_health_after'] = health_data_after
        add_step("Server health after disconnect", health_ok_after, f"Health data: {health_data_after}")
        
        # Step 10: Evaluate overall success
        print("🔟 Evaluating test results...")
        
        success_criteria = [
            test_results['button_clicked'],
            len(test_results['disconnect_events']) > 0,  # Some disconnect event occurred
            # Check if connection state actually changed
            test_results.get('connection_state_after', {}).get('drone_connected', True) != 
            test_results.get('connection_state_before', {}).get('drone_connected', False)
        ]
        
        test_results['success'] = all(success_criteria)
        add_step("Overall test evaluation", test_results['success'], 
                f"Success criteria met: {sum(success_criteria)}/{len(success_criteria)}")
        
    except Exception as e:
        test_results['errors'].append(f"Test execution error: {str(e)}")
        add_step("Test execution", False, str(e))
        
    finally:
        server_monitor.stop_monitoring()
        if driver:
            driver.quit()
    
    return test_results

def print_comprehensive_results(results):
    """Print detailed test results"""
    print("\n" + "="*80)
    print("COMPREHENSIVE DISCONNECT TEST RESULTS")
    print("="*80)
    
    # Overall status
    status_emoji = "✅" if results['success'] else "❌"
    print(f"{status_emoji} OVERALL RESULT: {'SUCCESS' if results['success'] else 'FAILED'}")
    
    # Steps summary
    print(f"\n📋 TEST STEPS ({len(results['steps'])}):")
    for i, step in enumerate(results['steps'], 1):
        status = "✅" if step['success'] else "❌"
        print(f"  {i:2d}. {status} {step['step']}")
        if step.get('details'):
            print(f"      {step['details']}")
    
    # Connection state analysis
    print(f"\n🔍 CONNECTION STATE ANALYSIS:")
    before = results.get('connection_state_before', {})
    after = results.get('connection_state_after', {})
    
    print(f"  BEFORE: WebSocket={before.get('websocket_connected', 'N/A')}, "
          f"Drone={before.get('drone_connected', 'N/A')}, "
          f"Status='{before.get('connection_status_text', 'N/A')}'")
    
    print(f"  AFTER:  WebSocket={after.get('websocket_connected', 'N/A')}, "
          f"Drone={after.get('drone_connected', 'N/A')}, "
          f"Status='{after.get('connection_status_text', 'N/A')}'")
    
    # Disconnect events
    print(f"\n📡 DISCONNECT EVENTS ({len(results.get('disconnect_events', []))}):")
    for i, event in enumerate(results.get('disconnect_events', []), 1):
        print(f"  {i}. [{event['source']}] {event['message']}")
    
    # Errors
    if results.get('errors'):
        print(f"\n🚨 ERRORS ({len(results['errors'])}):")
        for i, error in enumerate(results['errors'], 1):
            print(f"  {i}. {error}")
    
    # Server health
    health_before = results.get('server_health_before')
    health_after = results.get('server_health_after')
    print(f"\n🏥 SERVER HEALTH:")
    print(f"  Before: {health_before}")
    print(f"  After:  {health_after}")

if __name__ == "__main__":
    print("🧪 WebGCS Comprehensive Disconnect Test")
    print("="*50)
    
    results = test_full_disconnect_functionality()
    print_comprehensive_results(results)
    
    # Save results
    with open('comprehensive_disconnect_test.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to: comprehensive_disconnect_test.json")
    
    # Return appropriate exit code
    exit(0 if results['success'] else 1)
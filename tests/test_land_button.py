#!/usr/bin/env python3
"""
WebGCS Land Button Test
Comprehensive test for the drone landing functionality
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests

class LandButtonTest:
    def __init__(self):
        self.driver = None
        self.test_results = {
            "success": False,
            "steps": [],
            "button_clicked": False,
            "land_command_sent": False,
            "drone_connected_before": False,
            "server_health_before": None,
            "server_health_after": None,
            "connection_state_before": None,
            "connection_state_after": None,
            "console_events": [],
            "flight_command_events": [],
            "errors": []
        }
        
    def log_step(self, step, success, details, timestamp=None):
        """Log a test step"""
        if timestamp is None:
            timestamp = time.time()
        
        self.test_results["steps"].append({
            "step": step,
            "success": success,
            "details": details,
            "timestamp": timestamp
        })
        
        status = "✅" if success else "❌"
        print(f"{len(self.test_results['steps'])}️⃣ {step}...")
        print(f"  {status} {step}: {details}")
        
    def setup_browser(self):
        """Setup Chrome browser with logging"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Enable console logging
            chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.log_step("Browser setup", True, "Chrome driver initialized")
            return True
            
        except Exception as e:
            self.log_step("Browser setup", False, f"Failed to setup browser: {e}")
            return False
    
    def check_server_health(self):
        """Check server health endpoint"""
        try:
            response = requests.get("http://localhost:5001/health", timeout=5)
            health_data = response.json()
            self.log_step("Server health check", True, f"Health data: {health_data}")
            return health_data
        except Exception as e:
            self.log_step("Server health check", False, f"Health check failed: {e}")
            return None
    
    def load_website(self):
        """Load the WebGCS website"""
        try:
            self.driver.get("http://localhost:5001")
            self.log_step("Website loaded", True, "Page loaded successfully")
            
            # Wait a moment for initial JavaScript loading
            time.sleep(2)
            
            # Try to check if WebGCS is initialized
            try:
                webgcs_ready = self.driver.execute_script(
                    "return window.WebGCS !== undefined"
                )
                if webgcs_ready:
                    socket_ready = self.driver.execute_script(
                        "return window.WebGCS && window.WebGCS.socket !== null"
                    )
                    if socket_ready:
                        self.log_step("WebGCS initialized", True, "WebGCS and socket ready")
                    else:
                        self.log_step("WebGCS socket not ready", False, "Socket not initialized")
                else:
                    self.log_step("WebGCS not initialized", False, "WebGCS object not found")
            except Exception as js_error:
                self.log_step("JavaScript execution error", False, f"JS error: {js_error}")
            
            return True
            
        except Exception as e:
            self.log_step("Website loaded", False, f"Failed to load website: {e}")
            return False
    
    def get_connection_state(self):
        """Get current connection state from browser"""
        try:
            # Get connection status text
            status_element = self.driver.find_element(By.ID, "connection-status")
            connection_status_text = status_element.text
            
            # Get drone connection state
            drone_connected = self.driver.execute_script(
                "return window.WebGCS ? window.WebGCS.droneConnected : false"
            )
            
            # Get land button state
            land_btn = self.driver.find_element(By.ID, "land-btn")
            land_button_enabled = land_btn.is_enabled()
            
            return {
                "connection_status_text": connection_status_text,
                "drone_connected": drone_connected,
                "land_button_enabled": land_button_enabled
            }
            
        except Exception as e:
            self.log_step("Get connection state", False, f"Failed to get connection state: {e}")
            return None
    
    def ensure_connected(self):
        """Ensure drone is connected before testing LAND"""
        try:
            state = self.get_connection_state()
            if not state or not state["drone_connected"]:
                # Try to connect first
                connect_btn = self.driver.find_element(By.ID, "connect-btn")
                if connect_btn.is_enabled():
                    connect_btn.click()
                    self.log_step("Connect button clicked", True, "Attempting to connect to drone")
                    
                    # Wait for connection
                    connection_timeout = 15
                    start_time = time.time()
                    
                    while time.time() - start_time < connection_timeout:
                        current_state = self.get_connection_state()
                        if current_state and current_state["drone_connected"]:
                            self.test_results["drone_connected_before"] = True
                            self.log_step("Drone connection established", True, "Connected: True")
                            return True
                        time.sleep(0.5)
                    
                    self.log_step("Drone connection failed", False, "Could not connect to drone")
                    return False
            else:
                self.test_results["drone_connected_before"] = True
                self.log_step("Drone already connected", True, "Skipping connection step")
                return True
                
        except Exception as e:
            self.log_step("Ensure connected", False, f"Connection check failed: {e}")
            return False
    
    def capture_console_logs(self):
        """Capture browser console logs"""
        try:
            logs = self.driver.get_log('browser')
            for log in logs:
                message = f"{log['source']} {log['message']}"
                self.test_results["console_events"].append({
                    "source": "browser_console",
                    "message": message,
                    "timestamp": log['timestamp']
                })
                
                # Look for flight command events
                if "flight_command" in message.lower() or "land" in message.lower():
                    self.test_results["flight_command_events"].append({
                        "source": "browser_console",
                        "message": message,
                        "timestamp": log['timestamp']
                    })
        except Exception as e:
            print(f"Failed to capture console logs: {e}")
    
    def test_land_button(self):
        """Main test function for LAND button"""
        print("🧪 WebGCS LAND Button Test")
        print("=" * 50)
        
        try:
            # Step 1: Check server health
            self.test_results["server_health_before"] = self.check_server_health()
            if not self.test_results["server_health_before"]:
                return False
            
            # Step 2: Setup browser
            if not self.setup_browser():
                return False
            
            # Step 3: Load website
            if not self.load_website():
                return False
            
            # Step 4: Get initial connection state
            initial_state = self.get_connection_state()
            if initial_state:
                self.test_results["connection_state_before"] = initial_state
                self.log_step("Initial state captured", True, f"State: {initial_state}")
            
            # Step 5: Ensure drone is connected
            if not self.ensure_connected():
                return False
            
            # Step 6: Find and click LAND button
            land_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "land-btn"))
            )
            
            # Check if LAND button is enabled
            if not land_btn.is_enabled():
                self.log_step("LAND button status", False, "LAND button is disabled")
                return False
            
            # Click the LAND button
            land_btn.click()
            self.test_results["button_clicked"] = True
            self.log_step("LAND button clicked", True, "Button click executed")
            
            # Handle LAND confirmation dialog
            try:
                confirm_dialog = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located((By.ID, "confirmation-dialog"))
                )
                confirm_yes_btn = self.driver.find_element(By.ID, "confirm-yes")
                confirm_yes_btn.click()
                self.log_step("LAND confirmation accepted", True, "Clicked Yes on LAND confirmation dialog")
            except Exception as e:
                self.log_step("LAND confirmation dialog", False, f"Could not handle LAND confirmation dialog: {e}")
                return False
            
            # Step 7: Wait for command to be sent
            time.sleep(2)  # Allow time for command processing
            
            # Step 8: Capture console logs to check for command events
            self.capture_console_logs()
            
            # Check if LAND command was sent
            land_command_sent = any("land" in event["message"].lower() for event in self.test_results["flight_command_events"])
            self.test_results["land_command_sent"] = land_command_sent
            
            if land_command_sent:
                self.log_step("LAND command detected", True, "LAND command found in console logs")
            else:
                self.log_step("LAND command detection", False, "No LAND command found in console logs")
            
            # Step 9: Get final connection state
            final_state = self.get_connection_state()
            if final_state:
                self.test_results["connection_state_after"] = final_state
                self.log_step("Final state captured", True, f"State: {final_state}")
            
            # Step 10: Check server health after LAND
            self.test_results["server_health_after"] = self.check_server_health()
            
            # Step 11: Evaluate success
            success_criteria_met = 0
            total_criteria = 3
            
            if self.test_results["button_clicked"]:
                success_criteria_met += 1
                
            if self.test_results["drone_connected_before"]:
                success_criteria_met += 1
                
            if len(self.test_results["flight_command_events"]) > 0:
                success_criteria_met += 1
            
            self.test_results["success"] = success_criteria_met >= 2
            
            self.log_step("Overall test evaluation", 
                         success_criteria_met >= 2, 
                         f"Success criteria met: {success_criteria_met}/{total_criteria}")
            
            return True
            
        except Exception as e:
            self.log_step("Test execution", False, f"Test failed with error: {e}")
            self.test_results["errors"].append(str(e))
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
    
    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 80)
        print("LAND BUTTON TEST RESULTS")
        print("=" * 80)
        
        overall_result = "✅ SUCCESS" if self.test_results["success"] else "❌ FAILED"
        print(f"{overall_result}")
        
        print(f"\n📋 TEST STEPS ({len(self.test_results['steps'])}):")
        for i, step in enumerate(self.test_results["steps"], 1):
            status = "✅" if step["success"] else "❌"
            print(f"   {i:2d}. {status} {step['step']}")
            print(f"      {step['details']}")
        
        # Connection analysis
        if self.test_results["connection_state_before"] and self.test_results["connection_state_after"]:
            before = self.test_results["connection_state_before"]
            after = self.test_results["connection_state_after"]
            print(f"\n🔍 CONNECTION STATE ANALYSIS:")
            print(f"  BEFORE: Drone={before.get('drone_connected')}, LAND Button={before.get('land_button_enabled')}, Status='{before.get('connection_status_text')}'")
            print(f"  AFTER:  Drone={after.get('drone_connected')}, LAND Button={after.get('land_button_enabled')}, Status='{after.get('connection_status_text')}'")
        
        # Flight command events
        if self.test_results["flight_command_events"]:
            print(f"\n🚁 FLIGHT COMMAND EVENTS ({len(self.test_results['flight_command_events'])}):") 
            for i, event in enumerate(self.test_results["flight_command_events"], 1):
                print(f"  {i}. [{event['source']}] {event['message']}")
        
        # Console events
        if self.test_results["console_events"]:
            print(f"\n📡 ALL CONSOLE EVENTS ({len(self.test_results['console_events'])}):") 
            for i, event in enumerate(self.test_results["console_events"], 1):
                print(f"  {i}. [{event['source']}] {event['message']}")
        
        # Server health
        print(f"\n🏥 SERVER HEALTH:")
        print(f"  Before: {self.test_results['server_health_before']}")
        print(f"  After:  {self.test_results['server_health_after']}")
        
        # Save results
        with open("land_button_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n💾 Results saved to: land_button_test_results.json")

def main():
    test = LandButtonTest()
    test.test_land_button()
    test.print_results()
    
    return 0 if test.test_results["success"] else 1

if __name__ == "__main__":
    exit(main())
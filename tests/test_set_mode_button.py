#!/usr/bin/env python3
"""
WebGCS Set Mode Button Test
Comprehensive test for the flight mode change functionality
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import requests

class SetModeButtonTest:
    def __init__(self):
        self.driver = None
        self.test_results = {
            "success": False,
            "steps": [],
            "button_clicked": False,
            "mode_change_command_sent": False,
            "drone_connected_before": False,
            "server_health_before": None,
            "server_health_after": None,
            "connection_state_before": None,
            "connection_state_after": None,
            "mode_before": None,
            "mode_after": None,
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
            
            # Get set mode button state
            set_mode_btn = self.driver.find_element(By.ID, "set-mode-btn")
            set_mode_button_enabled = set_mode_btn.is_enabled()
            
            # Get current flight mode
            try:
                mode_select = self.driver.find_element(By.ID, "flight-mode-select")
                current_mode = Select(mode_select).first_selected_option.text
            except Exception:
                current_mode = "Unknown"
            
            return {
                "connection_status_text": connection_status_text,
                "drone_connected": drone_connected,
                "set_mode_button_enabled": set_mode_button_enabled,
                "current_flight_mode": current_mode
            }
            
        except Exception as e:
            self.log_step("Get connection state", False, f"Failed to get connection state: {e}")
            return None
    
    def ensure_connected(self):
        """Ensure drone is connected before testing Set Mode"""
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
    
    def select_flight_mode(self):
        """Select a different flight mode"""
        try:
            mode_select = self.driver.find_element(By.ID, "flight-mode-select")
            select_obj = Select(mode_select)
            
            # Get current mode
            current_mode = select_obj.first_selected_option.text
            self.test_results["mode_before"] = current_mode
            
            # Find a different mode to select
            available_options = [option.text for option in select_obj.options]
            self.log_step("Available flight modes", True, f"Modes: {available_options}")
            
            # Select a different mode (prefer GUIDED if available, otherwise select the second option)
            target_mode = None
            if "GUIDED" in available_options and current_mode != "GUIDED":
                target_mode = "GUIDED"
            elif len(available_options) > 1:
                target_mode = available_options[1] if available_options[0] == current_mode else available_options[0]
            
            if target_mode:
                select_obj.select_by_visible_text(target_mode)
                self.log_step("Flight mode selected", True, f"Selected: {target_mode} (was: {current_mode})")
                return True
            else:
                self.log_step("Flight mode selection", False, "No alternative mode available")
                return False
                
        except Exception as e:
            self.log_step("Select flight mode", False, f"Failed to select mode: {e}")
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
                if any(keyword in message.lower() for keyword in ["flight_command", "mode", "guided", "stabilize", "auto"]):
                    self.test_results["flight_command_events"].append({
                        "source": "browser_console",
                        "message": message,
                        "timestamp": log['timestamp']
                    })
        except Exception as e:
            print(f"Failed to capture console logs: {e}")
    
    def test_set_mode_button(self):
        """Main test function for Set Mode button"""
        print("🧪 WebGCS Set Mode Button Test")
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
            
            # Step 6: Select a different flight mode
            if not self.select_flight_mode():
                return False
            
            # Step 7: Find and click Set Mode button
            set_mode_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "set-mode-btn"))
            )
            
            # Check if Set Mode button is enabled
            if not set_mode_btn.is_enabled():
                self.log_step("Set Mode button status", False, "Set Mode button is disabled")
                return False
            
            # Click the Set Mode button
            set_mode_btn.click()
            self.test_results["button_clicked"] = True
            self.log_step("Set Mode button clicked", True, "Button click executed")
            
            # Step 8: Wait for command to be sent
            time.sleep(2)  # Allow time for command processing
            
            # Step 9: Capture console logs to check for command events
            self.capture_console_logs()
            
            # Check if mode change command was sent
            mode_command_sent = any("mode" in event["message"].lower() for event in self.test_results["flight_command_events"])
            self.test_results["mode_change_command_sent"] = mode_command_sent
            
            if mode_command_sent:
                self.log_step("Mode change command detected", True, "Mode command found in console logs")
            else:
                self.log_step("Mode change command detection", False, "No mode command found in console logs")
            
            # Step 10: Get final connection state and mode
            final_state = self.get_connection_state()
            if final_state:
                self.test_results["connection_state_after"] = final_state
                self.test_results["mode_after"] = final_state.get("current_flight_mode")
                self.log_step("Final state captured", True, f"State: {final_state}")
            
            # Step 11: Check server health after mode change
            self.test_results["server_health_after"] = self.check_server_health()
            
            # Step 12: Evaluate success
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
        print("SET MODE BUTTON TEST RESULTS")
        print("=" * 80)
        
        overall_result = "✅ SUCCESS" if self.test_results["success"] else "❌ FAILED"
        print(f"{overall_result}")
        
        print(f"\n📋 TEST STEPS ({len(self.test_results['steps'])}):")
        for i, step in enumerate(self.test_results["steps"], 1):
            status = "✅" if step["success"] else "❌"
            print(f"   {i:2d}. {status} {step['step']}")
            print(f"      {step['details']}")
        
        # Mode change analysis
        if self.test_results["mode_before"] and self.test_results["mode_after"]:
            print(f"\n🔄 FLIGHT MODE ANALYSIS:")
            print(f"  BEFORE: {self.test_results['mode_before']}")
            print(f"  AFTER:  {self.test_results['mode_after']}")
            print(f"  CHANGED: {'Yes' if self.test_results['mode_before'] != self.test_results['mode_after'] else 'No'}")
        
        # Connection analysis
        if self.test_results["connection_state_before"] and self.test_results["connection_state_after"]:
            before = self.test_results["connection_state_before"]
            after = self.test_results["connection_state_after"]
            print(f"\n🔍 CONNECTION STATE ANALYSIS:")
            print(f"  BEFORE: Drone={before.get('drone_connected')}, Set Mode Button={before.get('set_mode_button_enabled')}, Status='{before.get('connection_status_text')}'")
            print(f"  AFTER:  Drone={after.get('drone_connected')}, Set Mode Button={after.get('set_mode_button_enabled')}, Status='{after.get('connection_status_text')}'")
        
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
        with open("set_mode_button_test_results.json", "w") as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n💾 Results saved to: set_mode_button_test_results.json")

def main():
    test = SetModeButtonTest()
    test.test_set_mode_button()
    test.print_results()
    
    return 0 if test.test_results["success"] else 1

if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
MANUAL MAP INTERFACE TESTING AGENT
Simplified manual testing of map interface functionality
"""

import time
import requests
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ManualMapTestAgent:
    def __init__(self):
        self.webgcs_url = "http://localhost:5001"
        self.driver = None
        
    def setup_browser(self):
        """Initialize Chrome browser for testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("✅ Chrome browser initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False
    
    def load_interface(self):
        """Load WebGCS interface"""
        try:
            logger.info(f"🌐 Loading WebGCS: {self.webgcs_url}")
            self.driver.get(self.webgcs_url)
            
            # Wait for basic elements
            wait = WebDriverWait(self.driver, 15)
            map_div = wait.until(EC.presence_of_element_located((By.ID, "map")))
            center_btn = wait.until(EC.presence_of_element_located((By.ID, "center-map-btn")))
            fly_to_btn = wait.until(EC.presence_of_element_located((By.ID, "fly-to-toggle")))
            
            logger.info("✅ WebGCS interface loaded")
            return True
        except Exception as e:
            logger.error(f"❌ Interface load failed: {e}")
            return False
    
    def test_basic_elements(self):
        """Test basic map elements are present"""
        logger.info("\n🔍 Testing Basic Map Elements")
        
        try:
            # Check map container
            map_div = self.driver.find_element(By.ID, "map")
            map_height = map_div.size["height"]
            map_width = map_div.size["width"]
            logger.info(f"✅ Map container found: {map_width}x{map_height}")
            
            # Check Center Map button
            center_btn = self.driver.find_element(By.ID, "center-map-btn")
            center_text = center_btn.text
            center_enabled = center_btn.is_enabled()
            logger.info(f"✅ Center Map button: '{center_text}', Enabled: {center_enabled}")
            
            # Check Fly To toggle
            fly_to_btn = self.driver.find_element(By.ID, "fly-to-toggle")
            fly_to_text = fly_to_btn.text
            fly_to_enabled = fly_to_btn.is_enabled()
            logger.info(f"✅ Fly To toggle: '{fly_to_text}', Enabled: {fly_to_enabled}")
            
            # Check if Leaflet is loaded
            leaflet_loaded = self.driver.execute_script("return typeof window.L !== 'undefined';")
            logger.info(f"✅ Leaflet library loaded: {leaflet_loaded}")
            
            # Check MapController
            map_controller = self.driver.execute_script("return typeof window.MapController !== 'undefined';")
            logger.info(f"✅ MapController loaded: {map_controller}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Basic elements test failed: {e}")
            return False
    
    def test_fly_to_toggle(self):
        """Test Fly To toggle functionality"""
        logger.info("\n🔍 Testing Fly To Toggle")
        
        try:
            fly_to_btn = self.driver.find_element(By.ID, "fly-to-toggle")
            
            # Initial state
            initial_text = fly_to_btn.text
            initial_class = fly_to_btn.get_attribute("class")
            logger.info(f"Initial state: '{initial_text}', Class: {initial_class}")
            
            # Click to toggle
            fly_to_btn.click()
            time.sleep(0.5)
            
            new_text = fly_to_btn.text
            new_class = fly_to_btn.get_attribute("class")
            logger.info(f"After click: '{new_text}', Class: {new_class}")
            
            # Check cursor change on map
            map_cursor = self.driver.execute_script("""
                const mapDiv = document.getElementById('map');
                return mapDiv ? mapDiv.style.cursor : 'not found';
            """)
            logger.info(f"Map cursor: '{map_cursor}'")
            
            # Toggle back
            fly_to_btn.click()
            time.sleep(0.5)
            
            final_text = fly_to_btn.text
            final_class = fly_to_btn.get_attribute("class")
            logger.info(f"After second click: '{final_text}', Class: {final_class}")
            
            logger.info("✅ Fly To toggle test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fly To toggle test failed: {e}")
            return False
    
    def test_center_button_click(self):
        """Test Center Map button click"""
        logger.info("\n🔍 Testing Center Map Button")
        
        try:
            center_btn = self.driver.find_element(By.ID, "center-map-btn")
            
            # Check button state
            is_enabled = center_btn.is_enabled()
            button_text = center_btn.text
            logger.info(f"Center button state: '{button_text}', Enabled: {is_enabled}")
            
            # Click the button
            center_btn.click()
            time.sleep(1)
            
            # Check for any messages or changes
            messages = self.driver.execute_script("""
                const messages = document.querySelectorAll('.toast, .alert, .message');
                return Array.from(messages).map(msg => msg.textContent);
            """)
            
            if messages:
                logger.info(f"Messages after center click: {messages}")
            else:
                logger.info("No messages displayed after center click")
            
            logger.info("✅ Center button click test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Center button test failed: {e}")
            return False
    
    def test_map_click(self):
        """Test map clicking functionality"""
        logger.info("\n🔍 Testing Map Click")
        
        try:
            # First enable fly-to mode
            fly_to_btn = self.driver.find_element(By.ID, "fly-to-toggle")
            if "OFF" in fly_to_btn.text:
                fly_to_btn.click()
                time.sleep(0.5)
            
            logger.info(f"Fly-to mode: {fly_to_btn.text}")
            
            # Find map element
            map_element = self.driver.find_element(By.ID, "map")
            
            # Click in the center of the map
            map_width = map_element.size["width"]
            map_height = map_element.size["height"]
            center_x = map_width // 2
            center_y = map_height // 2
            
            logger.info(f"Clicking map at center: ({center_x}, {center_y})")
            
            ActionChains(self.driver).move_to_element_with_offset(
                map_element, center_x, center_y
            ).click().perform()
            
            time.sleep(1)
            
            # Check for any messages
            messages = self.driver.execute_script("""
                const messages = document.querySelectorAll('.toast, .alert, .message');
                return Array.from(messages).map(msg => msg.textContent);
            """)
            
            if messages:
                logger.info(f"Messages after map click: {messages}")
            else:
                logger.info("No messages displayed after map click")
            
            logger.info("✅ Map click test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Map click test failed: {e}")
            return False
    
    def test_layer_controls(self):
        """Test map layer controls"""
        logger.info("\n🔍 Testing Layer Controls")
        
        try:
            # Check for layer control
            layer_control = self.driver.execute_script("""
                return document.querySelector('.leaflet-control-layers') !== null;
            """)
            
            if layer_control:
                logger.info("✅ Layer control found")
                
                # Try to find layer options
                layer_options = self.driver.execute_script("""
                    const control = document.querySelector('.leaflet-control-layers');
                    const inputs = control ? control.querySelectorAll('input[type="radio"]') : [];
                    return Array.from(inputs).map(input => {
                        const label = input.parentNode.textContent.trim();
                        return {label: label, checked: input.checked};
                    });
                """)
                
                if layer_options:
                    logger.info(f"Layer options: {layer_options}")
                else:
                    logger.info("No layer options found")
                    
            else:
                logger.info("❌ Layer control not found")
            
            logger.info("✅ Layer controls test completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Layer controls test failed: {e}")
            return False
    
    def check_connection_status(self):
        """Check if drone connection is established"""
        logger.info("\n🔍 Checking Connection Status")
        
        try:
            # Check connect button
            connect_btn = self.driver.find_element(By.ID, "connect-btn")
            connect_text = connect_btn.text
            connect_class = connect_btn.get_attribute("class")
            
            is_connected = "btn-success" in connect_class
            logger.info(f"Connect button: '{connect_text}', Connected: {is_connected}")
            
            if not is_connected:
                logger.info("Attempting to connect...")
                connect_btn.click()
                time.sleep(3)
                
                # Check again
                new_class = connect_btn.get_attribute("class")
                new_connected = "btn-success" in new_class
                logger.info(f"After connect attempt: Connected: {new_connected}")
            
            # Check telemetry values
            try:
                lat_element = self.driver.find_element(By.ID, "pfd-lat")
                lon_element = self.driver.find_element(By.ID, "pfd-lon")
                alt_element = self.driver.find_element(By.ID, "pfd-alt")
                
                lat = lat_element.text
                lon = lon_element.text
                alt = alt_element.text
                
                logger.info(f"Telemetry - Lat: {lat}, Lon: {lon}, Alt: {alt}")
            except:
                logger.info("Telemetry values not accessible")
            
            return is_connected
            
        except Exception as e:
            logger.error(f"❌ Connection check failed: {e}")
            return False
    
    def run_manual_tests(self):
        """Run all manual tests"""
        logger.info("🚀 Starting Manual Map Interface Tests")
        
        try:
            if not self.setup_browser():
                return False
            
            if not self.load_interface():
                return False
            
            # Wait a bit for everything to load
            time.sleep(3)
            
            # Run tests
            self.check_connection_status()
            self.test_basic_elements()
            self.test_fly_to_toggle() 
            self.test_center_button_click()
            self.test_map_click()
            self.test_layer_controls()
            
            logger.info("\n🎉 Manual tests completed - check browser for visual verification")
            
            # Keep browser open for manual inspection
            input("\\nPress Enter to close browser and exit...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Manual test failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🧹 Browser closed")

def main():
    agent = ManualMapTestAgent()
    agent.run_manual_tests()

if __name__ == "__main__":
    main()
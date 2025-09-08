#!/usr/bin/env python3
"""
Quick script to take a screenshot of the WebGCS interface
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def take_screenshot():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1600,1200")
    
    try:
        # Create webdriver instance
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to WebGCS interface
        print("Loading WebGCS interface...")
        driver.get("http://localhost:5001")
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "main-container")))
        
        # Take screenshot
        screenshot_path = "webgcs_interface_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved as: {screenshot_path}")
        
        return screenshot_path
        
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None
        
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    take_screenshot()
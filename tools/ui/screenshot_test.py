#!/usr/bin/env python3
"""
Screenshot test HTML file directly
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def take_screenshot():
    # Get current directory
    current_dir = os.getcwd()
    html_file = f"file://{current_dir}/test_layout.html"
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1600,1600")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    try:
        # Create webdriver instance
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to test HTML file
        print(f"Loading test HTML file: {html_file}")
        driver.get(html_file)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "main-container"))
        )
        
        # Set window size to capture full page
        driver.set_window_size(1600, 1200)
        
        # Scroll to make sure all content is loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.execute_script("window.scrollTo(0, 0);")
        
        # Get full page dimensions
        total_width = driver.execute_script("return document.body.scrollWidth")
        total_height = driver.execute_script("return document.body.scrollHeight")
        
        # Set window to capture full content
        driver.set_window_size(max(1600, total_width), max(1400, total_height + 200))
        
        # Take screenshot
        screenshot_path = "webgcs_layout_full_screenshot.png"
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
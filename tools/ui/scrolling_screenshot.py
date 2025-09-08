#!/usr/bin/env python3
"""
Take multiple screenshots scrolling down the interface
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def take_scrolling_screenshots():
    # Get current directory
    current_dir = os.getcwd()
    html_file = f"file://{current_dir}/test_layout.html"
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1600,800")
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
        
        # Get total height
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        
        print(f"Total height: {total_height}, Viewport height: {viewport_height}")
        
        # Take screenshots scrolling down
        scroll_position = 0
        screenshot_num = 1
        
        while scroll_position < total_height:
            # Scroll to position
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            
            # Take screenshot
            screenshot_path = f"webgcs_scroll_{screenshot_num}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot {screenshot_num} saved as: {screenshot_path}")
            
            # Move to next position
            scroll_position += viewport_height - 100  # Overlap a bit
            screenshot_num += 1
            
            if screenshot_num > 5:  # Safety limit
                break
        
        # Take one final full screenshot
        driver.execute_script("window.scrollTo(0, 0);")
        driver.set_window_size(1600, min(total_height + 100, 3000))
        driver.save_screenshot("webgcs_complete_layout.png")
        print("Complete layout screenshot saved as: webgcs_complete_layout.png")
        
        return True
        
    except Exception as e:
        print(f"Error taking screenshots: {e}")
        return False
        
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    take_scrolling_screenshots()
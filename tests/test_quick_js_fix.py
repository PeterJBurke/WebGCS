#!/usr/bin/env python3
"""
Quick Test: JavaScript Error Fix Verification
Tests if the JavaScript error in connection-manager.js line 344 is fixed
"""
import pytest
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_javascript_error_fix():
    """Test that JavaScript error on line 344 is fixed"""
    server_url = "http://localhost:5001"
    
    # Initialize Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Verify server is running
        response = requests.get(f"{server_url}/health", timeout=5)
        assert response.status_code == 200
        
        # Load the page
        print("Loading WebGCS interface...")
        driver.get(server_url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "connect-btn"))
        )
        
        # Give page time to run JavaScript
        time.sleep(2)
        
        # Check for JavaScript errors
        logs = driver.get_log('browser')
        js_errors = [log for log in logs if log['level'] == 'SEVERE' and 'connection-manager.js' in log['message']]
        
        print(f"JavaScript errors found: {len(js_errors)}")
        for error in js_errors:
            print(f"  {error['level']}: {error['message']}")
        
        # Filter out favicon error (not related to our fix)
        connection_js_errors = [log for log in js_errors if 'connection-manager.js' in log['message']]
        
        assert len(connection_js_errors) == 0, f"JavaScript errors still present: {connection_js_errors}"
        
        print("✅ JavaScript error fix verified - no connection-manager.js errors found")
        
    finally:
        driver.quit()


if __name__ == "__main__":
    test_javascript_error_fix()
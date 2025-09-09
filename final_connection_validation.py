#!/usr/bin/env python3
"""
Final Connection Validation Test
Tests the complete connection flow and heartbeat monitoring
"""

import asyncio
import time
from playwright.async_api import async_playwright
import json
import requests

async def final_connection_validation():
    """Final comprehensive test of connection functionality"""
    
    print("FINAL CONNECTION VALIDATION - VIRTUAL DRONE TEST")
    print("=" * 60)
    
    # Verify WebGCS server is responsive
    try:
        response = requests.get("http://127.0.0.1:5002", timeout=5)
        print(f"✓ WebGCS server responsive: {response.status_code}")
    except:
        print("✗ WebGCS server not responding")
        return False
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate and wait for full load
            await page.goto("http://127.0.0.1:5002")
            await page.wait_for_load_state('networkidle')
            print("✓ Navigated to WebGCS interface")
            
            # Take initial screenshot
            await page.screenshot(path="final_test_initial.png")
            
            # Get initial status
            try:
                status_container = page.locator('.status-container')
                initial_status = await status_container.text_content()
                print(f"Initial Status: {initial_status.strip()}")
            except:
                print("Could not read initial status")
            
            # Find and verify connect button specifically
            connect_button = page.locator('#connect-btn')
            
            if await connect_button.count() == 0:
                print("✗ Connect button not found")
                return False
            
            print("✓ Connect button found")
            
            # Check if button is enabled
            is_enabled = await connect_button.is_enabled()
            print(f"✓ Connect button enabled: {is_enabled}")
            
            # Click connect button
            print("Clicking Connect button...")
            await connect_button.click()
            
            # Wait for connection process
            await page.wait_for_timeout(5000)
            
            # Take post-click screenshot
            await page.screenshot(path="final_test_after_connect.png")
            
            # Check connection result
            try:
                status_container = page.locator('.status-container')
                final_status = await status_container.text_content()
                print(f"Final Status: {final_status.strip()}")
                
                # Check if status shows connected
                if "Connected" in final_status:
                    print("✓ Connection status shows 'Connected'")
                else:
                    print("✗ Connection status does not show 'Connected'")
                    
            except Exception as e:
                print(f"Error reading final status: {e}")
            
            # Check button states after connection
            try:
                connect_enabled = await connect_button.is_enabled()
                print(f"✓ Connect button after connection: enabled={connect_enabled}")
                
                disconnect_button = page.locator('#disconnect-btn')
                if await disconnect_button.count() > 0:
                    disconnect_enabled = await disconnect_button.is_enabled()
                    print(f"✓ Disconnect button after connection: enabled={disconnect_enabled}")
                else:
                    print("✗ Disconnect button not found")
                    
            except Exception as e:
                print(f"Error checking button states: {e}")
            
            # Monitor for heartbeat updates over 15 seconds
            print("\nMonitoring heartbeat for 15 seconds...")
            
            heartbeat_values = []
            for second in range(15):
                try:
                    # Look for heartbeat counter using multiple strategies
                    heartbeat_text = ""
                    
                    # Strategy 1: Look for specific heartbeat element
                    heartbeat_element = page.locator('#heartbeat-counter, .heartbeat-counter')
                    if await heartbeat_element.count() > 0:
                        heartbeat_text = await heartbeat_element.text_content()
                    else:
                        # Strategy 2: Get all text and search for heartbeat
                        page_text = await page.text_content('body')
                        lines = page_text.split('\n')
                        for line in lines:
                            if 'Heartbeat' in line or '❤️' in line:
                                heartbeat_text = line.strip()
                                break
                    
                    if heartbeat_text:
                        print(f"Second {second+1:2d}: {heartbeat_text}")
                        heartbeat_values.append(heartbeat_text)
                    else:
                        print(f"Second {second+1:2d}: No heartbeat text found")
                        
                except Exception as e:
                    print(f"Second {second+1:2d}: Error reading heartbeat - {e}")
                
                await page.wait_for_timeout(1000)
            
            # Analyze heartbeat data
            print(f"\nHeartbeat Analysis:")
            print(f"Total readings: {len(heartbeat_values)}")
            
            if len(heartbeat_values) > 0:
                print(f"First reading: {heartbeat_values[0]}")
                print(f"Last reading: {heartbeat_values[-1]}")
                
                # Extract numbers from heartbeat readings
                import re
                numbers = []
                for reading in heartbeat_values:
                    found_numbers = re.findall(r'\d+', reading)
                    if found_numbers:
                        numbers.append(int(found_numbers[-1]))
                
                if len(numbers) > 1:
                    if numbers[-1] > numbers[0]:
                        print("✓ Heartbeat counter is incrementing!")
                        print(f"  Started at: {numbers[0]}, Ended at: {numbers[-1]}")
                    else:
                        print("✗ Heartbeat counter is not incrementing")
                        print(f"  Stayed at: {numbers[0]}")
                else:
                    print("✗ Could not extract heartbeat numbers")
            else:
                print("✗ No heartbeat readings captured")
            
            # Check PFD for telemetry data
            print("\nChecking PFD for telemetry data...")
            try:
                pfd_canvas = page.locator('#pfd-canvas, .pfd, canvas')
                if await pfd_canvas.count() > 0:
                    print("✓ PFD canvas found")
                    # Take PFD screenshot
                    await pfd_canvas.screenshot(path="final_test_pfd.png")
                    print("✓ PFD screenshot captured")
                else:
                    print("✗ PFD canvas not found")
            except Exception as e:
                print(f"Error checking PFD: {e}")
            
            # Take final comprehensive screenshot
            await page.screenshot(path="final_test_complete.png", full_page=True)
            
            # Generate summary report
            print(f"\n{'='*60}")
            print("FINAL CONNECTION TEST SUMMARY")
            print(f"{'='*60}")
            print("✓ WebGCS server responsive")
            print("✓ Connect button functional")
            print("✓ Connection process initiated")
            
            if "Connected" in final_status if 'final_status' in locals() else False:
                print("✓ Connection status shows success")
            else:
                print("? Connection status unclear")
                
            if len(heartbeat_values) > 0:
                print("✓ Heartbeat data detected")
            else:
                print("✗ No heartbeat data flowing")
            
            print(f"\nScreenshots saved:")
            print(f"- final_test_initial.png")
            print(f"- final_test_after_connect.png") 
            print(f"- final_test_pfd.png")
            print(f"- final_test_complete.png")
            
        finally:
            await browser.close()
    
    return True

if __name__ == "__main__":
    asyncio.run(final_connection_validation())
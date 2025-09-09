#!/usr/bin/env python3
"""
Detailed Connection Test - Focus on heartbeat and telemetry validation
"""

import asyncio
import time
from playwright.async_api import async_playwright
import json

async def detailed_connection_test():
    """Run detailed connection test focusing on telemetry and heartbeat"""
    
    print("DETAILED CONNECTION TEST WITH VIRTUAL DRONE")
    print("=" * 55)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            # Navigate to WebGCS
            await page.goto("http://127.0.0.1:5002")
            print("✓ Navigated to WebGCS interface")
            
            # Wait for page to load
            await page.wait_for_load_state('networkidle')
            
            # Take initial screenshot
            await page.screenshot(path="detailed_test_initial.png")
            print("✓ Captured initial state")
            
            # Check current connection status
            try:
                status_text = await page.locator('.status-container, .connection-status, #status').first.text_content(timeout=2000)
                print(f"Initial status: {status_text.strip()}")
            except:
                print("Status element not found")
            
            # Find and click connect button
            connect_button = page.locator('button:has-text("Connect"), #connect-btn')
            
            if await connect_button.count() > 0:
                print("✓ Found Connect button")
                await connect_button.first.click()
                print("✓ Clicked Connect button")
                
                # Wait for connection to establish
                await page.wait_for_timeout(3000)
                
                # Take screenshot after connection attempt
                await page.screenshot(path="detailed_test_after_connect.png")
                print("✓ Captured post-connection state")
                
                # Check connection status
                try:
                    status_text = await page.locator('.status-container').first.text_content()
                    print(f"Connection status after click: {status_text.strip()}")
                except:
                    print("Could not find status text")
                
                # Check button states
                try:
                    connect_enabled = await connect_button.first.is_enabled()
                    print(f"Connect button enabled: {connect_enabled}")
                    
                    disconnect_button = page.locator('button:has-text("Disconnect"), #disconnect-btn')
                    if await disconnect_button.count() > 0:
                        disconnect_enabled = await disconnect_button.first.is_enabled()
                        print(f"Disconnect button enabled: {disconnect_enabled}")
                    else:
                        print("Disconnect button not found")
                except Exception as e:
                    print(f"Error checking button states: {e}")
                
                # Monitor heartbeat for 10 seconds
                print("\nMonitoring heartbeat for 10 seconds...")
                
                for i in range(10):
                    try:
                        # Look for heartbeat text containing numbers
                        heartbeat_element = await page.query_selector_all('text[contains(., "Heartbeat")], text[contains(., "❤️")]')
                        if not heartbeat_element:
                            # Try alternative selectors
                            all_text = await page.content()
                            if "Heartbeat" in all_text or "❤️" in all_text:
                                print(f"Second {i+1}: Heartbeat text found in page content")
                            else:
                                print(f"Second {i+1}: No heartbeat text found")
                        else:
                            heartbeat_text = await heartbeat_element[0].text_content()
                            print(f"Second {i+1}: {heartbeat_text.strip()}")
                    except Exception as e:
                        print(f"Second {i+1}: Error reading heartbeat - {e}")
                    
                    await page.wait_for_timeout(1000)
                
                # Check for PFD/telemetry data
                print("\nChecking for telemetry data...")
                
                # Look for common telemetry elements
                telemetry_selectors = [
                    'text="Altitude"',
                    'text="Airspeed"', 
                    'text="Heading"',
                    'text="Battery"',
                    '.pfd',
                    '#pfd',
                    '.telemetry'
                ]
                
                for selector in telemetry_selectors:
                    try:
                        elements = page.locator(selector)
                        count = await elements.count()
                        if count > 0:
                            text = await elements.first.text_content()
                            print(f"✓ Found {selector}: {text.strip()}")
                    except:
                        pass
                
                # Take final screenshot
                await page.screenshot(path="detailed_test_final.png")
                print("✓ Captured final state")
                
                # Get full page content for analysis
                page_content = await page.content()
                
                # Count occurrences of key terms
                heartbeat_count = page_content.count("Heartbeat") + page_content.count("❤️")
                connected_count = page_content.count("Connected")
                telemetry_indicators = ["Altitude", "Airspeed", "Heading", "Battery", "GPS"]
                telemetry_count = sum(page_content.count(term) for term in telemetry_indicators)
                
                print(f"\nPage Analysis:")
                print(f"Heartbeat mentions: {heartbeat_count}")
                print(f"Connected mentions: {connected_count}")
                print(f"Telemetry indicators: {telemetry_count}")
                
            else:
                print("✗ Connect button not found")
            
        finally:
            await browser.close()
    
    return True

if __name__ == "__main__":
    asyncio.run(detailed_connection_test())
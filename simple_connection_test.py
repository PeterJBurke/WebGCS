#!/usr/bin/env python3
"""
Simple Connection Test for WebGCS
Focus: Connect button -> Monitor heartbeats
"""
import time
import asyncio
from playwright.async_api import async_playwright

async def run_simple_test():
    """Test connection and heartbeat increment."""
    
    print("🔥 SIMPLE CONNECTION TEST")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        print("🌐 Loading http://127.0.0.1:5002")
        await page.goto("http://127.0.0.1:5002")
        await page.wait_for_load_state("networkidle")
        print("✅ Page loaded")
        
        # Take initial screenshot
        await page.screenshot(path="simple_test_initial.png")
        print("📸 Initial screenshot saved")
        
        print("\n🔍 Checking UI elements")
        
        # Check connect button
        connect_btn = page.locator("#connect-btn")
        print(f"Connect button found: {await connect_btn.count() > 0}")
        
        # Check initial heartbeat
        heartbeat = page.locator("#heartbeat-counter")
        if await heartbeat.count() > 0:
            initial_text = await heartbeat.inner_text()
            print(f"Initial heartbeat: {initial_text}")
        
        # Check initial status  
        status = page.locator("#connection-status")
        if await status.count() > 0:
            initial_status = await status.inner_text()
            print(f"Initial status: {initial_status}")
        
        print("\n⚡ Clicking Connect button")
        await connect_btn.click()
        print("✅ Connect button clicked")
        
        # Wait and monitor for 20 seconds
        print("\n⏱️ Monitoring for 30 seconds...")
        for i in range(30):
            await page.wait_for_timeout(1000)
            
            # Check status
            if await status.count() > 0:
                current_status = await status.inner_text()
                
            # Check heartbeat
            if await heartbeat.count() > 0:
                current_heartbeat = await heartbeat.inner_text()
                
            print(f"[{i+1}s] Status: {current_status} | Heartbeat: {current_heartbeat}")
        
        # Final screenshot
        await page.screenshot(path="simple_test_final.png")
        print("📸 Final screenshot saved")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_simple_test())
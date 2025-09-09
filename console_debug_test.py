#!/usr/bin/env python3
"""
Console Debug Test - Capture JavaScript errors and logs
"""
import asyncio
from playwright.async_api import async_playwright


async def debug_console():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capture console messages
        console_messages = []
        
        def handle_console_message(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text,
                "location": str(msg.location) if msg.location else "unknown"
            })
            print(f"CONSOLE [{msg.type.upper()}]: {msg.text}")
        
        page.on("console", handle_console_message)
        
        # Capture page errors
        def handle_page_error(error):
            print(f"PAGE ERROR: {error}")
        
        page.on("pageerror", handle_page_error)
        
        print("Loading WebGCS and monitoring console...")
        await page.goto("http://127.0.0.1:5002", wait_until="networkidle")
        
        # Wait a bit to see initialization messages
        await page.wait_for_timeout(3000)
        
        # Check button states
        connect_btn = page.locator("#connect-btn")
        is_disabled = await connect_btn.is_disabled()
        
        print(f"\nConnect button disabled: {is_disabled}")
        
        # Try to click the button to see what happens
        if not is_disabled:
            print("Clicking connect button...")
            await connect_btn.click()
            await page.wait_for_timeout(3000)
        else:
            print("Button is disabled, cannot click")
        
        # Show all console messages
        print(f"\nTotal console messages: {len(console_messages)}")
        for msg in console_messages:
            print(f"  [{msg['type']}] {msg['text']}")
        
        await page.screenshot(path="console_debug.png")
        print("Screenshot saved: console_debug.png")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_console())
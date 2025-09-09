#!/usr/bin/env python3
"""
Manual IP/Port Display Verification
Simple test to verify and screenshot the IP/Port fields as requested by user
"""

import asyncio
from playwright.async_api import async_playwright

async def main():
    print("🧪 Manual IP/Port Verification Test")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={"width": 1200, "height": 800}
        )
        page = await context.new_page()
        
        # Navigate to the website  
        print("🌐 Navigating to http://127.0.0.1:5002")
        await page.goto("http://127.0.0.1:5002", wait_until="networkidle")
        
        # Wait for page to fully load
        await asyncio.sleep(3)
        
        # Get IP and Port field values
        ip_field = await page.query_selector('#drone-host')
        port_field = await page.query_selector('#drone-port')
        
        if ip_field and port_field:
            ip_value = await ip_field.get_attribute('value')
            port_value = await port_field.get_attribute('value')
            
            print(f"📍 IP Field Value: '{ip_value}'")
            print(f"🔌 Port Field Value: '{port_value}'")
            
            # Highlight the fields for screenshot
            await page.evaluate("""
                const ipField = document.querySelector('#drone-host');
                const portField = document.querySelector('#drone-port');
                const panel = document.querySelector('.connection-panel');
                
                if (panel) {
                    panel.style.border = '3px solid #00AA00';
                    panel.style.padding = '20px';
                    panel.style.backgroundColor = '#f8fff8';
                }
                
                if (ipField) {
                    ipField.style.border = '3px solid #ff6600';
                    ipField.style.backgroundColor = '#fff8f0';
                    ipField.style.fontSize = '18px';
                    ipField.style.padding = '8px';
                    ipField.style.fontWeight = 'bold';
                }
                
                if (portField) {
                    portField.style.border = '3px solid #ff6600';
                    portField.style.backgroundColor = '#fff8f0';
                    portField.style.fontSize = '18px';
                    portField.style.padding = '8px';
                    portField.style.fontWeight = 'bold';
                }
                
                // Add a clear label
                const label = document.createElement('div');
                label.innerHTML = `<strong>✅ VERIFICATION:</strong><br/>
                                  IP: ${ipField ? ipField.value : 'NOT FOUND'}<br/>
                                  Port: ${portField ? portField.value : 'NOT FOUND'}<br/>
                                  From .env file: 192.168.193.235:5678`;
                label.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #ffff00;
                    padding: 15px;
                    border: 3px solid #000;
                    font-size: 16px;
                    z-index: 9999;
                    box-shadow: 0 0 10px rgba(0,0,0,0.5);
                    border-radius: 5px;
                `;
                document.body.appendChild(label);
            """)
            
            await asyncio.sleep(2)
            
            # Take screenshot
            screenshot_path = "manual_ip_port_verification.png"
            await page.screenshot(path=screenshot_path, full_page=False)
            
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Report results
            print("\n" + "=" * 50)
            print("📊 VERIFICATION RESULTS:")
            print("=" * 50)
            
            if ip_value == "192.168.193.235" and port_value == "5678":
                print("🎉 SUCCESS: Website shows correct IP and Port from .env file!")
                print(f"   ✅ IP Field: {ip_value} (CORRECT)")
                print(f"   ✅ Port Field: {port_value} (CORRECT)")
            else:
                print("⚠️  ISSUE: Values don't match .env file")
                print(f"   IP Field: {ip_value} (Expected: 192.168.193.235)")
                print(f"   Port Field: {port_value} (Expected: 5678)")
        else:
            print("❌ Could not find IP/Port fields")
        
        await asyncio.sleep(3)  # Keep browser open briefly
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
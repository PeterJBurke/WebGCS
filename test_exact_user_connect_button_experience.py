import asyncio
from playwright.async_api import async_playwright, TimeoutError
import json
import time

async def test_exact_user_connect_button_experience():
    """Test exactly what user experiences when clicking connect button"""
    
    async with async_playwright() as p:
        # Launch browser EXACTLY like user (visible, normal speed)
        browser = await p.chromium.launch(
            headless=False,  # User can see
            slow_mo=500      # Normal human speed
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # Track ALL messages that appear
        console_messages = []
        dialogs_captured = []
        
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        
        # Capture ANY popup/alert/dialog EXACTLY like user sees
        async def capture_dialog(dialog):
            message = dialog.message
            dialog_type = dialog.type
            dialogs_captured.append({
                'type': dialog_type,
                'message': message,
                'timestamp': time.time()
            })
            print(f"\n🚨 USER SEES DIALOG: {dialog_type}")
            print(f"📝 MESSAGE: {message}")
            
            # Accept the dialog (like user clicking OK)
            await dialog.accept()
        
        page.on("dialog", capture_dialog)
        
        try:
            print("🌐 Opening http://localhost:5002 (exactly like user)")
            
            # Go to website EXACTLY like user
            await page.goto("http://localhost:5002", wait_until="networkidle")
            
            print("⏳ Waiting for page to load completely...")
            await page.wait_for_timeout(3000)  # Wait like user would
            
            # Take screenshot of what user sees
            await page.screenshot(path="user_sees_before_click.png", full_page=True)
            print("📸 Screenshot taken: user_sees_before_click.png")
            
            print("🔍 Looking for connect button...")
            
            # Find button EXACTLY where user looks
            try:
                connect_button = page.locator("#connect-drone-btn")
                await connect_button.wait_for(state="visible", timeout=5000)
                
                button_text = await connect_button.text_content()
                is_enabled = await connect_button.is_enabled()
                
                print(f"✅ Found button with text: '{button_text}'")
                print(f"✅ Button enabled: {is_enabled}")
                
                # Check what user sees before clicking
                webgcs_connected = await page.evaluate("window.WebGCS?.connected")
                socket_connected = await page.evaluate("window.WebGCS?.socket?.connected") 
                
                print(f"📊 WebGCS connected: {webgcs_connected}")
                print(f"📊 Socket connected: {socket_connected}")
                
            except TimeoutError:
                print("❌ Connect button not found!")
                await page.screenshot(path="button_not_found.png")
                return
            
            print("👆 Clicking connect button (EXACTLY like user does)...")
            
            # Click EXACTLY like user would
            await connect_button.click()
            
            print("⏳ Waiting to see what happens (like user waits)...")
            
            # Wait and watch what happens (like user would)
            await page.wait_for_timeout(5000)
            
            # Take screenshot of what happens after click
            await page.screenshot(path="user_sees_after_click.png", full_page=True)
            print("📸 Screenshot taken: user_sees_after_click.png")
            
            # Check final state
            final_button_text = await connect_button.text_content()
            final_webgcs_connected = await page.evaluate("window.WebGCS?.connected")
            final_socket_connected = await page.evaluate("window.WebGCS?.socket?.connected")
            
            print(f"📊 Final button text: '{final_button_text}'")
            print(f"📊 Final WebGCS connected: {final_webgcs_connected}")
            print(f"📊 Final socket connected: {final_socket_connected}")
            
            # Report what user experienced
            print("\n" + "="*50)
            print("📋 EXACT USER EXPERIENCE REPORT")
            print("="*50)
            
            if dialogs_captured:
                print("🚨 USER SAW THESE POPUPS/DIALOGS:")
                for dialog in dialogs_captured:
                    print(f"   Type: {dialog['type']}")
                    print(f"   Message: {dialog['message']}")
            else:
                print("✅ NO popups or dialogs appeared")
            
            print(f"\n📝 Console messages ({len(console_messages)} total):")
            for msg in console_messages[-10:]:  # Show last 10
                print(f"   {msg}")
                
            print(f"\n🔄 Button behavior:")
            print(f"   Before: '{button_text}' -> After: '{final_button_text}'")
            
            # Save detailed report
            report = {
                'user_experience': {
                    'popups_appeared': len(dialogs_captured) > 0,
                    'popup_messages': dialogs_captured,
                    'button_changed': button_text != final_button_text,
                    'connection_established': final_webgcs_connected,
                    'console_messages': console_messages
                }
            }
            
            with open('exact_user_experience_report.json', 'w') as f:
                json.dump(report, f, indent=2)
                
            print("\n💾 Detailed report saved: exact_user_experience_report.json")
            
        finally:
            print("\n⏳ Keeping browser open for 10 seconds so you can see...")
            await page.wait_for_timeout(10000)
            await browser.close()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_exact_user_connect_button_experience())
#!/usr/bin/env python3
"""
Final Connection Test - Validates all requirements
"""
import time
import asyncio
from playwright.async_api import async_playwright

async def run_final_test():
    """Run the final comprehensive test."""
    
    print("🚀 FINAL CONNECTION TEST - COMPREHENSIVE VALIDATION")
    print("=" * 70)
    
    results = {
        'website_loads': False,
        'ip_shows_localhost': False,
        'port_shows_5678': False,
        'initial_status_disconnected': False,
        'initial_heartbeat_zero': False,
        'connect_button_responds': False,
        'status_changes_to_connected': False,
        'heartbeat_increments': False,
        'heartbeat_reaches_target': False,
        'test_status': 'UNKNOWN'
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        print("1️⃣ Loading website at http://127.0.0.1:5002")
        await page.goto("http://127.0.0.1:5002")
        await page.wait_for_load_state("networkidle")
        results['website_loads'] = True
        print("✅ Website loaded successfully")
        
        print("\n2️⃣ Checking initial UI state")
        # Check IP field
        ip_field = page.locator("#drone-host")
        ip_value = await ip_field.input_value()
        if ip_value == "127.0.0.1":
            results['ip_shows_localhost'] = True
            print(f"✅ IP field correct: {ip_value}")
        else:
            print(f"❌ IP field incorrect: {ip_value}")
        
        # Check port field
        port_field = page.locator("#drone-port")
        port_value = await port_field.input_value()
        if port_value == "5678":
            results['port_shows_5678'] = True
            print(f"✅ Port field correct: {port_value}")
        else:
            print(f"❌ Port field incorrect: {port_value}")
        
        # Check initial status
        status_elem = page.locator("#connection-status")
        initial_status = await status_elem.inner_text()
        if "Disconnected" in initial_status:
            results['initial_status_disconnected'] = True
            print(f"✅ Initial status correct: {initial_status}")
        else:
            print(f"❌ Initial status incorrect: {initial_status}")
        
        # Check initial heartbeat
        heartbeat_elem = page.locator("#heartbeat-counter")
        initial_heartbeat = await heartbeat_elem.inner_text()
        if "❤️ Heartbeat: 0" in initial_heartbeat:
            results['initial_heartbeat_zero'] = True
            print(f"✅ Initial heartbeat correct: {initial_heartbeat}")
        else:
            print(f"❌ Initial heartbeat incorrect: {initial_heartbeat}")
        
        # Take initial screenshot
        await page.screenshot(path="final_test_initial_state.png")
        print("📸 Initial state screenshot saved")
        
        print("\n3️⃣ Clicking Connect button")
        connect_btn = page.locator("#connect-btn")
        await connect_btn.click()
        results['connect_button_responds'] = True
        print("✅ Connect button clicked")
        
        # Wait a moment for connection
        await page.wait_for_timeout(2000)
        
        print("\n4️⃣ Monitoring connection status")
        current_status = await status_elem.inner_text()
        if "Connected" in current_status and "Disconnected" not in current_status:
            results['status_changes_to_connected'] = True
            print(f"✅ Status changed to: {current_status}")
        else:
            print(f"⚠️ Status: {current_status}")
        
        print("\n5️⃣ Monitoring heartbeat for 15 seconds...")
        initial_count = 0
        max_count = 0
        
        for i in range(15):
            await page.wait_for_timeout(1000)
            
            current_heartbeat = await heartbeat_elem.inner_text()
            
            # Extract count from heartbeat text
            import re
            match = re.search(r'Heartbeat:\s*(\d+)', current_heartbeat)
            if match:
                count = int(match.group(1))
                if i == 0:
                    initial_count = count
                max_count = max(max_count, count)
                
                if count > initial_count:
                    results['heartbeat_increments'] = True
                    if count >= 5:  # Ensure we see multiple increments
                        results['heartbeat_reaches_target'] = True
                
                print(f"[{i+1:2d}s] {current_heartbeat} (count: {count})")
            else:
                print(f"[{i+1:2d}s] {current_heartbeat}")
        
        # Take final screenshot
        await page.screenshot(path="final_test_completed.png")
        print("📸 Final state screenshot saved")
        
        await browser.close()
    
    # Determine final test result
    all_pass = all([
        results['website_loads'],
        results['ip_shows_localhost'],
        results['port_shows_5678'],
        results['initial_status_disconnected'],
        results['initial_heartbeat_zero'],
        results['connect_button_responds'],
        results['status_changes_to_connected'],
        results['heartbeat_increments'],
        results['heartbeat_reaches_target']
    ])
    
    if all_pass:
        results['test_status'] = 'PASS'
    else:
        results['test_status'] = 'FAIL'
    
    return results

def print_final_report(results):
    """Print the final test report."""
    print("\n" + "=" * 70)
    print("🏆 FINAL CONNECTION TEST REPORT")
    print("=" * 70)
    print(f"🎯 Overall Status: {results['test_status']}")
    print("\n📋 Detailed Results:")
    
    checks = [
        ('Website loads successfully', 'website_loads'),
        ('IP field shows "127.0.0.1"', 'ip_shows_localhost'),
        ('Port field shows "5678"', 'port_shows_5678'),
        ('Initial status shows "Disconnected"', 'initial_status_disconnected'),
        ('Initial heartbeat shows "❤️ Heartbeat: 0"', 'initial_heartbeat_zero'),
        ('Connect button responds when clicked', 'connect_button_responds'),
        ('Connection status updates to "Connected"', 'status_changes_to_connected'),
        ('Heartbeat counter increments', 'heartbeat_increments'),
        ('Heartbeat reaches target count (≥5)', 'heartbeat_reaches_target')
    ]
    
    for desc, key in checks:
        status = "✅ PASS" if results[key] else "❌ FAIL"
        print(f"  {status} - {desc}")
    
    print("\n📊 Summary:")
    passed = sum(1 for _, key in checks if results[key])
    total = len(checks)
    print(f"  Passed: {passed}/{total}")
    print(f"  Success Rate: {(passed/total*100):.1f}%")
    
    if results['test_status'] == 'PASS':
        print("\n🎉 ALL TESTS PASSED! Connection and heartbeat monitoring is working correctly.")
    else:
        print(f"\n🔧 {total-passed} tests failed. Review the results above.")
    
    print("=" * 70)

async def main():
    """Main test execution."""
    results = await run_final_test()
    print_final_report(results)
    
    # Return appropriate exit code
    return 0 if results['test_status'] == 'PASS' else 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
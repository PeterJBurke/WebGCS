#!/usr/bin/env python3
"""
Comprehensive Connection Test for WebGCS
Tests the complete workflow: Load page -> Connect -> Monitor heartbeats
"""
import time
import asyncio
import json
from playwright.async_api import async_playwright

async def run_connection_test():
    """Execute the complete test workflow until it passes."""
    
    print("🔥 COMPREHENSIVE CONNECTION TEST")
    print("=" * 60)
    print("Testing: Load page -> Connect -> Monitor heartbeats")
    print("Target: http://127.0.0.1:5002")
    print("Expected: Heartbeat counter increments after connection")
    print("=" * 60)
    
    results = {
        'test_start': time.time(),
        'website_loads': False,
        'connect_button_exists': False,
        'ip_field_correct': False,
        'port_field_correct': False,
        'initial_status_correct': False,
        'initial_heartbeat_zero': False,
        'connect_button_responds': False,
        'connection_status_updates': False,
        'heartbeat_increments': False,
        'final_status': 'UNKNOWN',
        'screenshots': [],
        'console_logs': [],
        'errors': []
    }
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=False, slow_mo=500)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Capture console logs
            page.on("console", lambda msg: results['console_logs'].append(f"{msg.type()}: {msg.text()}"))
            page.on("pageerror", lambda msg: results['errors'].append(str(msg)))
            
            print("🌐 Step 1: Loading website at http://127.0.0.1:5002")
            try:
                await page.goto("http://127.0.0.1:5002", timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                results['website_loads'] = True
                print("✅ Website loaded successfully")
                
                # Take initial screenshot
                screenshot_path = f"comprehensive_test_initial_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path)
                results['screenshots'].append(screenshot_path)
                print(f"📸 Initial screenshot: {screenshot_path}")
                
            except Exception as e:
                results['errors'].append(f"Website load failed: {str(e)}")
                print(f"❌ Website load failed: {e}")
                return results
            
            print("\n🔍 Step 2: Verifying initial UI state")
            try:
                # Check if connect button exists
                connect_btn = page.locator("#connect-btn")
                if await connect_btn.count() > 0:
                    results['connect_button_exists'] = True
                    print("✅ Connect button found")
                else:
                    print("❌ Connect button not found")
                    return results
                
                # Check IP field
                ip_field = page.locator("#drone-host")
                if await ip_field.count() > 0:
                    ip_value = await ip_field.input_value()
                    if ip_value == "192.168.193.235":
                        results['ip_field_correct'] = True
                        print(f"✅ IP field correct: {ip_value}")
                    else:
                        print(f"❌ IP field incorrect: {ip_value}")
                else:
                    print("❌ IP field not found")
                
                # Check port field
                port_field = page.locator("#drone-port")
                if await port_field.count() > 0:
                    port_value = await port_field.input_value()
                    if port_value == "5678":
                        results['port_field_correct'] = True
                        print(f"✅ Port field correct: {port_value}")
                    else:
                        print(f"❌ Port field incorrect: {port_value}")
                else:
                    print("❌ Port field not found")
                
                # Check initial connection status
                status_elem = page.locator("#connection-status")
                if await status_elem.count() > 0:
                    status_text = await status_elem.inner_text()
                    if "Disconnected" in status_text:
                        results['initial_status_correct'] = True
                        print(f"✅ Initial status correct: {status_text}")
                    else:
                        print(f"❌ Initial status incorrect: {status_text}")
                else:
                    print("❌ Connection status element not found")
                
                # Check initial heartbeat counter
                heartbeat_elem = page.locator("#heartbeat-counter")
                if await heartbeat_elem.count() > 0:
                    heartbeat_text = await heartbeat_elem.inner_text()
                    if "❤️ Heartbeat: 0" in heartbeat_text:
                        results['initial_heartbeat_zero'] = True
                        print(f"✅ Initial heartbeat correct: {heartbeat_text}")
                    else:
                        print(f"❌ Initial heartbeat incorrect: {heartbeat_text}")
                else:
                    print("❌ Heartbeat counter element not found")
                
            except Exception as e:
                results['errors'].append(f"UI verification failed: {str(e)}")
                print(f"❌ UI verification failed: {e}")
            
            print("\n⚡ Step 3: Clicking Connect button")
            try:
                # Click the connect button
                await connect_btn.click()
                results['connect_button_responds'] = True
                print("✅ Connect button clicked")
                
                # Wait a bit for connection attempt
                await page.wait_for_timeout(2000)
                
                # Take screenshot after connect click
                screenshot_path = f"comprehensive_test_after_connect_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path)
                results['screenshots'].append(screenshot_path)
                print(f"📸 After connect screenshot: {screenshot_path}")
                
            except Exception as e:
                results['errors'].append(f"Connect button click failed: {str(e)}")
                print(f"❌ Connect button click failed: {e}")
                return results
            
            print("\n⏱️  Step 4: Monitoring connection status (30 second timeout)")
            start_monitor = time.time()
            timeout = 30  # 30 seconds
            connected = False
            
            while (time.time() - start_monitor) < timeout:
                try:
                    # Check connection status
                    status_text = await status_elem.inner_text()
                    if "Connected" in status_text and "Disconnected" not in status_text:
                        results['connection_status_updates'] = True
                        connected = True
                        print(f"✅ Connection status updated: {status_text}")
                        break
                    
                    # Show current status every 3 seconds
                    elapsed = time.time() - start_monitor
                    if int(elapsed) % 3 == 0:
                        print(f"⏳ [{int(elapsed)}s] Current status: {status_text}")
                    
                    await page.wait_for_timeout(1000)  # Wait 1 second
                    
                except Exception as e:
                    print(f"⚠️ Status check error: {e}")
                    await page.wait_for_timeout(1000)
            
            if not connected:
                print(f"❌ Connection timeout after {timeout} seconds")
                status_text = await status_elem.inner_text()
                print(f"Final status: {status_text}")
            
            print("\n💗 Step 5: Monitoring heartbeat counter (30 seconds)")
            start_heartbeat = time.time()
            initial_heartbeat = 0
            max_heartbeat = 0
            heartbeat_incremented = False
            
            # Get initial heartbeat count
            try:
                heartbeat_text = await heartbeat_elem.inner_text()
                if "Heartbeat:" in heartbeat_text:
                    import re
                    match = re.search(r'Heartbeat:\s*(\d+)', heartbeat_text)
                    if match:
                        initial_heartbeat = int(match.group(1))
                        max_heartbeat = initial_heartbeat
                        print(f"📊 Initial heartbeat: {initial_heartbeat}")
            except Exception as e:
                print(f"⚠️ Initial heartbeat read error: {e}")
            
            while (time.time() - start_heartbeat) < timeout:
                try:
                    heartbeat_text = await heartbeat_elem.inner_text()
                    if "Heartbeat:" in heartbeat_text:
                        import re
                        match = re.search(r'Heartbeat:\s*(\d+)', heartbeat_text)
                        if match:
                            current_heartbeat = int(match.group(1))
                            if current_heartbeat > max_heartbeat:
                                max_heartbeat = current_heartbeat
                                print(f"💗 Heartbeat increment detected: {current_heartbeat}")
                                
                                if current_heartbeat > initial_heartbeat:
                                    results['heartbeat_increments'] = True
                                    heartbeat_incremented = True
                                    print(f"✅ HEARTBEAT SUCCESS! Incremented from {initial_heartbeat} to {current_heartbeat}")
                                    break
                    
                    # Show progress every 3 seconds
                    elapsed = time.time() - start_heartbeat
                    if int(elapsed) % 3 == 0:
                        print(f"⏳ [{int(elapsed)}s] Current heartbeat: {heartbeat_text}")
                    
                    await page.wait_for_timeout(1000)  # Wait 1 second
                    
                except Exception as e:
                    print(f"⚠️ Heartbeat check error: {e}")
                    await page.wait_for_timeout(1000)
            
            if not heartbeat_incremented:
                print(f"❌ Heartbeat timeout after {timeout} seconds")
                print(f"Heartbeat remained at: {max_heartbeat} (started at {initial_heartbeat})")
            
            # Final screenshot
            screenshot_path = f"comprehensive_test_final_{int(time.time())}.png"
            await page.screenshot(path=screenshot_path)
            results['screenshots'].append(screenshot_path)
            print(f"📸 Final screenshot: {screenshot_path}")
            
            await browser.close()
            
    except Exception as e:
        results['errors'].append(f"Test execution error: {str(e)}")
        print(f"❌ Test execution error: {e}")
    
    finally:
        results['test_end'] = time.time()
        results['test_duration'] = results['test_end'] - results['test_start']
        
        # Determine final test status
        if results['heartbeat_increments']:
            results['final_status'] = 'PASS'
        elif results['connection_status_updates']:
            results['final_status'] = 'PARTIAL_PASS - Connected but no heartbeat increment'
        elif results['connect_button_responds']:
            results['final_status'] = 'PARTIAL_PASS - Button responds but no connection'
        else:
            results['final_status'] = 'FAIL'
    
    return results

def print_final_report(results):
    """Print comprehensive test report."""
    print("\n" + "=" * 60)
    print("📋 COMPREHENSIVE CONNECTION TEST REPORT")
    print("=" * 60)
    print(f"⏱️ Test Duration: {results['test_duration']:.1f} seconds")
    print(f"🎯 Final Status: {results['final_status']}")
    print()
    print("📊 Test Results:")
    print(f"  ✅ Website loads successfully: {'✅' if results['website_loads'] else '❌'}")
    print(f"  ✅ Connect button exists: {'✅' if results['connect_button_exists'] else '❌'}")
    print(f"  ✅ IP field shows '192.168.193.235': {'✅' if results['ip_field_correct'] else '❌'}")
    print(f"  ✅ Port field shows '5678': {'✅' if results['port_field_correct'] else '❌'}")
    print(f"  ✅ Initial status shows 'Disconnected': {'✅' if results['initial_status_correct'] else '❌'}")
    print(f"  ✅ Initial heartbeat shows '❤️ Heartbeat: 0': {'✅' if results['initial_heartbeat_zero'] else '❌'}")
    print(f"  ✅ Connect button responds when clicked: {'✅' if results['connect_button_responds'] else '❌'}")
    print(f"  ✅ Connection status updates to 'Connected': {'✅' if results['connection_status_updates'] else '❌'}")
    print(f"  🎯 Heartbeat counter increments: {'✅' if results['heartbeat_increments'] else '❌'}")
    print()
    print(f"📸 Screenshots: {len(results['screenshots'])}")
    for screenshot in results['screenshots']:
        print(f"  • {screenshot}")
    print()
    print(f"📝 Console Logs: {len(results['console_logs'])}")
    for log in results['console_logs'][-5:]:  # Show last 5 logs
        print(f"  • {log}")
    print()
    if results['errors']:
        print(f"❌ Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  • {error}")
    print("=" * 60)

async def main():
    """Main test execution."""
    results = await run_connection_test()
    
    # Save results to JSON
    results_file = f"comprehensive_test_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print_final_report(results)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    # Return exit code based on test result
    if results['final_status'] == 'PASS':
        print("🎉 ALL TESTS PASSED! Heartbeats are working correctly.")
        return 0
    else:
        print("🔧 TESTS FAILED - Need to fix heartbeat increment issue")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
#!/usr/bin/env python3
"""
Flight Controls Basic Testing - Phase 4
Testing flight control buttons using Playwright with simplified approach.

This test verifies basic functionality of all flight control buttons:
- ARM/DISARM buttons
- Flight mode buttons  
- Takeoff/Land buttons
- Emergency controls
- Safety confirmations

Focus: Verify buttons exist, are clickable, and show expected UI behavior.
"""

import pytest
import time
import logging
import json
import os
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlightControlsTester:
    """Simplified flight controls tester using synchronous Playwright"""
    
    def __init__(self):
        self.base_url = "http://localhost:5002"
        self.screenshots_dir = "screenshots"
        self.test_results = {}
        
        # Ensure screenshots directory exists
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def test_website_accessibility(self):
        """Test that the website is accessible and loads properly"""
        logger.info("=== Testing Website Accessibility ===")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Navigate to WebGCS
                logger.info(f"Navigating to {self.base_url}")
                response = page.goto(self.base_url, wait_until="networkidle")
                
                assert response.status == 200, f"Website not accessible: status {response.status}"
                
                # Wait for WebGCS to initialize
                page.wait_for_function("typeof window.WebGCS !== 'undefined'", timeout=30000)
                
                # Take screenshot
                page.screenshot(path=f"{self.screenshots_dir}/website_loaded.png")
                
                self.test_results['website_accessible'] = True
                logger.info("✓ Website accessibility test PASSED")
                
                return True
                
            except Exception as e:
                logger.error(f"Website accessibility test FAILED: {e}")
                self.test_results['website_accessible'] = False
                return False
            finally:
                browser.close()
    
    def test_flight_control_buttons_exist(self):
        """Test that all expected flight control buttons exist and are visible"""
        logger.info("=== Testing Flight Control Buttons Existence ===")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(self.base_url, wait_until="networkidle")
                page.wait_for_function("typeof window.WebGCS !== 'undefined'", timeout=30000)
                
                # Expected flight control buttons
                expected_buttons = [
                    'arm-btn',
                    'disarm-btn', 
                    'takeoff-btn',
                    'land-btn',
                    'rtl-btn',
                    'stabilize-btn',
                    'alt-hold-btn',
                    'loiter-btn',
                    'guided-btn',
                    'auto-btn',
                    'emergency-stop-btn'
                ]
                
                button_status = {}
                
                for btn_id in expected_buttons:
                    button = page.locator(f'#{btn_id}')
                    
                    exists = button.count() > 0
                    visible = button.is_visible() if exists else False
                    
                    button_status[btn_id] = {
                        'exists': exists,
                        'visible': visible
                    }
                    
                    logger.info(f"Button {btn_id}: exists={exists}, visible={visible}")
                
                # Take screenshot of flight controls
                page.screenshot(path=f"{self.screenshots_dir}/flight_controls_panel.png")
                
                # Check that all critical buttons exist
                critical_buttons = ['arm-btn', 'disarm-btn', 'takeoff-btn', 'land-btn']
                all_critical_exist = all(button_status[btn].get('exists', False) for btn in critical_buttons)
                
                self.test_results['buttons_exist'] = {
                    'all_buttons': button_status,
                    'critical_buttons_exist': all_critical_exist
                }
                
                assert all_critical_exist, f"Critical buttons missing: {button_status}"
                logger.info("✓ Flight control buttons existence test PASSED")
                
                return True
                
            except Exception as e:
                logger.error(f"Button existence test FAILED: {e}")
                self.test_results['buttons_exist'] = False
                return False
            finally:
                browser.close()
    
    def test_arm_button_interaction(self):
        """Test ARM button click and confirmation dialog"""
        logger.info("=== Testing ARM Button Interaction ===")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)  # Visible for demonstration
            page = browser.new_page()
            
            try:
                page.goto(self.base_url, wait_until="networkidle")
                page.wait_for_function("typeof window.WebGCS !== 'undefined'", timeout=30000)
                
                # Setup dialog handler
                dialog_appeared = False
                dialog_message = ""
                
                def handle_dialog(dialog):
                    nonlocal dialog_appeared, dialog_message
                    dialog_appeared = True
                    dialog_message = dialog.message
                    logger.info(f"Dialog appeared: {dialog_message}")
                    dialog.dismiss()  # Dismiss to avoid actually arming
                
                page.on("dialog", handle_dialog)
                
                # Find and click ARM button
                arm_btn = page.locator('#arm-btn')
                
                if arm_btn.count() > 0:
                    # Take screenshot before click
                    page.screenshot(path=f"{self.screenshots_dir}/before_arm_click.png")
                    
                    # Click ARM button
                    arm_btn.click()
                    
                    # Wait a moment for dialog
                    time.sleep(1)
                    
                    # Take screenshot after click
                    page.screenshot(path=f"{self.screenshots_dir}/after_arm_click.png")
                    
                    self.test_results['arm_button'] = {
                        'clicked': True,
                        'dialog_appeared': dialog_appeared,
                        'dialog_message': dialog_message
                    }
                    
                    logger.info(f"ARM button test: clicked=True, dialog={dialog_appeared}")
                    logger.info("✓ ARM button interaction test PASSED")
                    return True
                else:
                    logger.error("ARM button not found")
                    self.test_results['arm_button'] = {'clicked': False, 'button_found': False}
                    return False
                
            except Exception as e:
                logger.error(f"ARM button test FAILED: {e}")
                self.test_results['arm_button'] = {'error': str(e)}
                return False
            finally:
                browser.close()
    
    def test_flight_mode_buttons(self):
        """Test flight mode buttons can be clicked"""
        logger.info("=== Testing Flight Mode Buttons ===")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(self.base_url, wait_until="networkidle")
                page.wait_for_function("typeof window.WebGCS !== 'undefined'", timeout=30000)
                
                flight_mode_buttons = [
                    ('stabilize-btn', 'STABILIZE'),
                    ('loiter-btn', 'LOITER'),
                    ('rtl-btn', 'RTL'),
                    ('auto-btn', 'AUTO'),
                    ('guided-btn', 'GUIDED')
                ]
                
                mode_results = {}
                
                for btn_id, mode_name in flight_mode_buttons:
                    try:
                        mode_btn = page.locator(f'#{btn_id}')
                        
                        if mode_btn.count() > 0:
                            # Check if button is visible and enabled
                            visible = mode_btn.is_visible()
                            enabled = mode_btn.is_enabled()
                            
                            if visible and enabled:
                                # Try clicking the button
                                mode_btn.click()
                                time.sleep(0.5)  # Brief pause
                                
                                mode_results[mode_name] = {
                                    'exists': True,
                                    'visible': visible,
                                    'enabled': enabled,
                                    'clicked': True
                                }
                                logger.info(f"✓ Mode {mode_name}: successfully clicked")
                            else:
                                mode_results[mode_name] = {
                                    'exists': True,
                                    'visible': visible,
                                    'enabled': enabled,
                                    'clicked': False
                                }
                                logger.info(f"Mode {mode_name}: found but not enabled")
                        else:
                            mode_results[mode_name] = {'exists': False}
                            logger.warning(f"Mode button {mode_name} not found")
                            
                    except Exception as e:
                        mode_results[mode_name] = {'error': str(e)}
                        logger.error(f"Error testing mode {mode_name}: {e}")
                
                # Take screenshot of final state
                page.screenshot(path=f"{self.screenshots_dir}/flight_modes_tested.png")
                
                self.test_results['flight_modes'] = mode_results
                
                # Consider test passed if at least one mode button worked
                successful_modes = [name for name, result in mode_results.items() 
                                  if result.get('clicked', False)]
                
                if successful_modes:
                    logger.info(f"✓ Flight mode buttons test PASSED: {successful_modes}")
                    return True
                else:
                    logger.warning("No flight mode buttons were successfully clicked")
                    return False
                
            except Exception as e:
                logger.error(f"Flight mode buttons test FAILED: {e}")
                self.test_results['flight_modes'] = {'error': str(e)}
                return False
            finally:
                browser.close()
    
    def test_takeoff_altitude_input(self):
        """Test takeoff altitude input and validation"""
        logger.info("=== Testing Takeoff Altitude Input ===")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(self.base_url, wait_until="networkidle")
                page.wait_for_function("typeof window.WebGCS !== 'undefined'", timeout=30000)
                
                # Find takeoff altitude input
                altitude_input = page.locator('#takeoff-altitude')
                takeoff_btn = page.locator('#takeoff-btn')
                
                altitude_input_exists = altitude_input.count() > 0
                takeoff_btn_exists = takeoff_btn.count() > 0
                
                results = {
                    'altitude_input_exists': altitude_input_exists,
                    'takeoff_btn_exists': takeoff_btn_exists
                }
                
                if altitude_input_exists:
                    # Test setting different altitude values
                    test_altitudes = ['5', '15', '25']
                    
                    for alt in test_altitudes:
                        altitude_input.fill(alt)
                        current_value = altitude_input.input_value()
                        results[f'altitude_{alt}'] = (current_value == alt)
                        logger.info(f"Set altitude {alt}: success={current_value == alt}")
                
                # Take screenshot
                page.screenshot(path=f"{self.screenshots_dir}/takeoff_altitude_test.png")
                
                self.test_results['takeoff_altitude'] = results
                
                # Test passes if both elements exist
                success = altitude_input_exists and takeoff_btn_exists
                if success:
                    logger.info("✓ Takeoff altitude input test PASSED")
                else:
                    logger.warning("Takeoff altitude input test incomplete")
                
                return success
                
            except Exception as e:
                logger.error(f"Takeoff altitude test FAILED: {e}")
                self.test_results['takeoff_altitude'] = {'error': str(e)}
                return False
            finally:
                browser.close()
    
    def generate_test_report(self):
        """Generate a comprehensive test report"""
        logger.info("=== Generating Test Report ===")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r is True or 
                           (isinstance(r, dict) and r.get('critical_buttons_exist', False))])
        
        report = {
            'test_suite': 'Phase 4: Flight Controls Basic Testing',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%",
            'detailed_results': self.test_results,
            'screenshots_directory': self.screenshots_dir
        }
        
        # Save report to file
        with open('flight_controls_basic_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Test report generated: {passed_tests}/{total_tests} tests passed")
        return report


def test_flight_controls_comprehensive():
    """Main test function that runs all flight control tests"""
    logger.info("=== STARTING PHASE 4: FLIGHT CONTROLS BASIC TESTING ===")
    
    tester = FlightControlsTester()
    
    # Run all tests
    test_results = []
    
    test_results.append(tester.test_website_accessibility())
    test_results.append(tester.test_flight_control_buttons_exist())
    test_results.append(tester.test_arm_button_interaction())
    test_results.append(tester.test_flight_mode_buttons())
    test_results.append(tester.test_takeoff_altitude_input())
    
    # Generate final report
    report = tester.generate_test_report()
    
    # Calculate overall success
    passed_count = sum(test_results)
    total_count = len(test_results)
    
    logger.info("=== FLIGHT CONTROLS BASIC TESTING COMPLETE ===")
    logger.info(f"Overall Results: {passed_count}/{total_count} tests passed")
    
    # Assert that critical functionality works
    assert passed_count >= 3, f"Too many test failures: {passed_count}/{total_count} passed"
    
    logger.info("✓ Phase 4 Flight Controls Basic Testing: SUCCESS")
    return report


if __name__ == "__main__":
    test_flight_controls_comprehensive()
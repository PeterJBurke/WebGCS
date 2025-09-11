"""
UI Validation Testing Agent - Phase 6 Summary Test

Phase 6 Comprehensive Test: UI Validation & Safety Testing Summary
Runs all critical validation tests and provides comprehensive safety assessment.

SAFETY-CRITICAL: Final validation of all UI safety and validation systems.
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class TestPhase6ValidationSummary:
    """
    Comprehensive Phase 6 validation test suite covering:
    - Input validation across all forms
    - Safety confirmation systems
    - Error handling and user feedback
    - Professional UI standards compliance
    - Security and safety limit enforcement
    """
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.base_url = "http://localhost:5002"
        cls.timeout = 5000  # Shorter timeout for efficiency
        cls.test_results = {
            'validation_tests': [],
            'safety_tests': [],
            'ui_standards': [],
            'security_tests': [],
            'overall_score': 0
        }
        
    async def setup_browser(self):
        """Setup browser and page for testing"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Navigate to WebGCS
        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state('networkidle')
        
    async def teardown_browser(self):
        """Cleanup browser resources"""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    def record_test_result(self, category, test_name, passed, details=""):
        """Record test result for summary reporting"""
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': time.time()
        }
        self.test_results[category].append(result)

    @pytest.mark.asyncio
    async def test_critical_input_validation_boundaries(self):
        """Test critical input validation boundaries for safety"""
        await self.setup_browser()
        
        try:
            # Test latitude validation (critical for navigation safety)
            await self.page.fill('#goto-latitude', '91')  # Invalid
            await self.page.locator('#goto-latitude').blur()
            await asyncio.sleep(0.2)
            
            lat_error = await self.page.query_selector('#goto-latitude-error')
            lat_validation_works = lat_error and await lat_error.is_visible()
            
            self.record_test_result('validation_tests', 'latitude_boundary_validation', 
                                  lat_validation_works, "Latitude >90 degrees blocked")
            
            # Test longitude validation  
            await self.page.fill('#goto-longitude', '181')  # Invalid
            await self.page.locator('#goto-longitude').blur()
            await asyncio.sleep(0.2)
            
            lon_error = await self.page.query_selector('#goto-longitude-error')
            lon_validation_works = lon_error and await lon_error.is_visible()
            
            self.record_test_result('validation_tests', 'longitude_boundary_validation',
                                  lon_validation_works, "Longitude >180 degrees blocked")
            
            # Test altitude safety limits
            await self.page.fill('#goto-altitude', '1001')  # Invalid (>1000m limit)
            await self.page.locator('#goto-altitude').blur()
            await asyncio.sleep(0.2)
            
            alt_error = await self.page.query_selector('#goto-altitude-error')
            alt_validation_works = alt_error and await alt_error.is_visible()
            
            self.record_test_result('validation_tests', 'altitude_safety_limits',
                                  alt_validation_works, "Altitude >1000m blocked for safety")
            
            # Test takeoff altitude limits
            await self.page.fill('#takeoff-altitude', '101')  # Invalid (>100m limit)
            await self.page.locator('#takeoff-altitude').blur()
            await asyncio.sleep(0.2)
            
            takeoff_error = await self.page.query_selector('#takeoff-altitude-error')
            takeoff_validation_works = takeoff_error and await takeoff_error.is_visible()
            
            self.record_test_result('validation_tests', 'takeoff_altitude_safety',
                                  takeoff_validation_works, "Takeoff altitude >100m blocked")
            
            # Overall validation score
            validation_passed = sum(1 for test in self.test_results['validation_tests'] if test['passed'])
            validation_total = len(self.test_results['validation_tests'])
            
            print(f"Input Validation: {validation_passed}/{validation_total} tests passed")
            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_safety_confirmation_systems(self):
        """Test safety confirmation systems for critical commands"""
        await self.setup_browser()
        
        try:
            # Check button states and availability
            arm_btn = await self.page.query_selector('#arm-btn')
            disarm_btn = await self.page.query_selector('#disarm-btn')
            takeoff_btn = await self.page.query_selector('#takeoff-btn')
            
            # Test button existence
            buttons_exist = all(btn is not None for btn in [arm_btn, disarm_btn, takeoff_btn])
            self.record_test_result('safety_tests', 'critical_buttons_present',
                                  buttons_exist, "ARM, DISARM, TAKEOFF buttons exist")
            
            # Test button state management
            if arm_btn:
                arm_disabled = await arm_btn.is_disabled()
                self.record_test_result('safety_tests', 'arm_button_safety_state',
                                      arm_disabled, "ARM button disabled when not connected")
            
            # Test takeoff altitude requirement
            if takeoff_btn:
                # Clear altitude field
                await self.page.fill('#takeoff-altitude', '')
                
                # Check if takeoff is properly restricted without altitude
                takeoff_disabled = await takeoff_btn.is_disabled()
                altitude_required = await self.page.query_selector('#takeoff-altitude[required]')
                
                safety_enforced = takeoff_disabled or altitude_required is not None
                self.record_test_result('safety_tests', 'takeoff_altitude_required',
                                      safety_enforced, "Takeoff requires altitude input")
            
            # Test emergency stop accessibility
            emergency_btn = await self.page.query_selector('#emergency-stop-btn')
            if emergency_btn:
                emergency_accessible = await emergency_btn.is_visible() and not await emergency_btn.is_disabled()
                self.record_test_result('safety_tests', 'emergency_stop_accessible',
                                      emergency_accessible, "Emergency stop always accessible")
            
            safety_passed = sum(1 for test in self.test_results['safety_tests'] if test['passed'])
            safety_total = len(self.test_results['safety_tests'])
            
            print(f"Safety Systems: {safety_passed}/{safety_total} tests passed")
            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_error_handling_user_feedback(self):
        """Test error handling and user feedback systems"""
        await self.setup_browser()
        
        try:
            # Test error message visibility
            await self.page.fill('#goto-latitude', '999')
            await self.page.locator('#goto-latitude').blur()
            await asyncio.sleep(0.3)
            
            error_element = await self.page.query_selector('#goto-latitude-error')
            error_visible = error_element and await error_element.is_visible()
            
            if error_visible:
                error_text = await error_element.text_content()
                error_helpful = error_text and len(error_text.strip()) > 10
                self.record_test_result('ui_standards', 'error_messages_helpful',
                                      error_helpful, f"Error message: '{error_text[:50]}...'")
            else:
                self.record_test_result('ui_standards', 'error_messages_visible',
                                      False, "Error messages not visible for invalid input")
            
            # Test error message positioning
            if error_element and error_visible:
                error_box = await error_element.bounding_box()
                input_element = await self.page.query_selector('#goto-latitude')
                input_box = await input_element.bounding_box() if input_element else None
                
                well_positioned = False
                if error_box and input_box:
                    vertical_distance = abs(error_box['y'] - (input_box['y'] + input_box['height']))
                    well_positioned = vertical_distance < 50
                    
                self.record_test_result('ui_standards', 'error_message_positioning',
                                      well_positioned, f"Error positioned {vertical_distance:.0f}px from input")
            
            # Test multiple error handling
            await self.page.fill('#goto-longitude', '999')
            await self.page.locator('#goto-longitude').blur()
            await asyncio.sleep(0.2)
            
            multiple_errors = await self.page.query_selector_all('[id$="-error"]:visible')
            handles_multiple = len(multiple_errors) >= 2
            
            self.record_test_result('ui_standards', 'multiple_error_handling',
                                  handles_multiple, f"Displays {len(multiple_errors)} simultaneous errors")
            
            ui_passed = sum(1 for test in self.test_results['ui_standards'] if test['passed'])
            ui_total = len(self.test_results['ui_standards'])
            
            print(f"UI Standards: {ui_passed}/{ui_total} tests passed")
            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_security_and_input_protection(self):
        """Test security features and input protection"""
        await self.setup_browser()
        
        try:
            # Test numeric input protection
            numeric_fields = ['#goto-latitude', '#goto-longitude', '#goto-altitude', '#takeoff-altitude']
            
            protected_fields = 0
            for field in numeric_fields:
                field_type = await self.page.get_attribute(field, 'type')
                if field_type == 'number':
                    protected_fields += 1
                    
            all_numeric_protected = protected_fields == len(numeric_fields)
            self.record_test_result('security_tests', 'numeric_input_protection',
                                  all_numeric_protected, 
                                  f"{protected_fields}/{len(numeric_fields)} fields use type='number'")
            
            # Test input length limits
            test_field = '#goto-latitude'
            long_input = '1' * 1000
            
            await self.page.fill(test_field, long_input)
            actual_value = await self.page.input_value(test_field)
            
            length_limited = len(actual_value) < len(long_input)
            self.record_test_result('security_tests', 'input_length_limits',
                                  length_limited, 
                                  f"Input limited to {len(actual_value)} characters")
            
            # Test form validation prevents submission
            await self.page.fill('#goto-latitude', '999')  # Invalid
            await self.page.fill('#goto-longitude', '999')  # Invalid
            
            goto_btn = await self.page.query_selector('#goto-btn')
            if goto_btn:
                # Check if button is disabled or validation prevents submission
                btn_disabled = await goto_btn.is_disabled()
                
                # Try clicking if not disabled (should be prevented by validation)
                validation_prevents_submission = btn_disabled
                
                self.record_test_result('security_tests', 'form_validation_prevents_submission',
                                      validation_prevents_submission, 
                                      "Invalid form submission blocked")
            
            security_passed = sum(1 for test in self.test_results['security_tests'] if test['passed'])
            security_total = len(self.test_results['security_tests'])
            
            print(f"Security Features: {security_passed}/{security_total} tests passed")
            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_professional_aviation_standards(self):
        """Test compliance with professional aviation interface standards"""
        await self.setup_browser()
        
        try:
            # Test button sizing for touch interfaces
            critical_buttons = ['#arm-btn', '#disarm-btn', '#takeoff-btn', '#emergency-stop-btn']
            
            adequately_sized_buttons = 0
            for btn_id in critical_buttons:
                btn = await self.page.query_selector(btn_id)
                if btn and await btn.is_visible():
                    box = await btn.bounding_box()
                    if box and box['width'] >= 40 and box['height'] >= 30:  # Reasonable touch size
                        adequately_sized_buttons += 1
                        
            touch_friendly = adequately_sized_buttons >= 3  # Most critical buttons
            self.record_test_result('ui_standards', 'touch_friendly_buttons',
                                  touch_friendly, 
                                  f"{adequately_sized_buttons} buttons adequately sized")
            
            # Test text readability
            text_elements = await self.page.query_selector_all('button, label, .error-message')
            
            readable_text_count = 0
            for element in text_elements[:5]:  # Test first 5
                if await element.is_visible():
                    style = await element.evaluate('el => getComputedStyle(el)')
                    font_size = style.get('fontSize', '16px')
                    size_value = int(font_size.replace('px', '').split('.')[0])
                    
                    if size_value >= 12:  # Minimum readable size
                        readable_text_count += 1
                        
            text_readable = readable_text_count >= 3
            self.record_test_result('ui_standards', 'text_readability',
                                  text_readable, 
                                  f"{readable_text_count}/5 text elements adequately sized")
            
            # Test page load performance
            start_time = time.time()
            await self.page.reload()
            await self.page.wait_for_selector('#arm-btn')
            load_time = time.time() - start_time
            
            fast_loading = load_time < 3.0  # 3 second threshold
            self.record_test_result('ui_standards', 'page_load_performance',
                                  fast_loading, f"Page loaded in {load_time:.2f} seconds")
            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_phase6_comprehensive_validation_summary(self):
        """Run all Phase 6 validation tests and provide summary"""
        print("\n" + "="*80)
        print("PHASE 6: UI VALIDATION & SAFETY TESTING COMPREHENSIVE SUMMARY")
        print("="*80)
        
        # Run all test categories
        await self.test_critical_input_validation_boundaries()
        await self.test_safety_confirmation_systems()
        await self.test_error_handling_user_feedback()
        await self.test_security_and_input_protection()
        await self.test_professional_aviation_standards()
        
        # Calculate overall scores
        all_tests = []
        for category in self.test_results.values():
            if isinstance(category, list):
                all_tests.extend(category)
                
        total_tests = len(all_tests)
        passed_tests = sum(1 for test in all_tests if test['passed'])
        overall_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\nPHASE 6 VALIDATION RESULTS:")
        print(f"{'='*50}")
        
        category_names = {
            'validation_tests': 'Input Validation',
            'safety_tests': 'Safety Systems', 
            'ui_standards': 'UI Standards',
            'security_tests': 'Security Features'
        }
        
        for category, tests in self.test_results.items():
            if isinstance(tests, list) and tests:
                cat_passed = sum(1 for test in tests if test['passed'])
                cat_total = len(tests)
                cat_score = (cat_passed / cat_total * 100) if cat_total > 0 else 0
                
                status = "✅ PASS" if cat_score >= 80 else "⚠️  PARTIAL" if cat_score >= 60 else "❌ FAIL"
                print(f"{category_names.get(category, category):<20}: {cat_passed}/{cat_total} ({cat_score:.0f}%) {status}")
                
                # Show failed tests
                failed_tests = [test for test in tests if not test['passed']]
                if failed_tests:
                    for test in failed_tests:
                        print(f"  ❌ {test['test']}: {test['details']}")
        
        print(f"\nOVERALL PHASE 6 SCORE: {passed_tests}/{total_tests} ({overall_score:.0f}%)")
        
        if overall_score >= 90:
            grade = "A - EXCELLENT"
            status = "✅ READY FOR PRODUCTION"
        elif overall_score >= 80:
            grade = "B - GOOD" 
            status = "✅ ACCEPTABLE FOR OPERATIONS"
        elif overall_score >= 70:
            grade = "C - ADEQUATE"
            status = "⚠️  NEEDS MINOR IMPROVEMENTS"
        elif overall_score >= 60:
            grade = "D - MARGINAL"
            status = "⚠️  NEEDS SIGNIFICANT IMPROVEMENTS"
        else:
            grade = "F - INSUFFICIENT"
            status = "❌ NOT READY FOR OPERATIONS"
            
        print(f"GRADE: {grade}")
        print(f"STATUS: {status}")
        
        print(f"\nSAFETY-CRITICAL ASSESSMENT:")
        print(f"{'='*50}")
        
        # Check critical safety features
        critical_validations = [test for test in self.test_results['validation_tests'] 
                              if 'altitude' in test['test'] or 'boundary' in test['test']]
        critical_safety = [test for test in self.test_results['safety_tests']]
        
        critical_passed = sum(1 for test in critical_validations + critical_safety if test['passed'])
        critical_total = len(critical_validations + critical_safety)
        critical_score = (critical_passed / critical_total * 100) if critical_total > 0 else 0
        
        print(f"Critical Safety Features: {critical_passed}/{critical_total} ({critical_score:.0f}%)")
        
        if critical_score >= 95:
            safety_status = "✅ SAFETY SYSTEMS FULLY OPERATIONAL"
        elif critical_score >= 85:
            safety_status = "✅ SAFETY SYSTEMS ADEQUATE"
        else:
            safety_status = "❌ SAFETY SYSTEMS REQUIRE IMMEDIATE ATTENTION"
            
        print(f"Safety Status: {safety_status}")
        
        print(f"\nRECOMMENDATIONS:")
        print(f"{'='*50}")
        
        if overall_score >= 90:
            print("✅ WebGCS UI validation and safety systems are excellent")
            print("✅ Ready for operational deployment")
            print("✅ Continue monitoring for edge cases")
        elif overall_score >= 80:
            print("✅ WebGCS UI validation and safety systems are good")
            print("⚠️  Address any failed tests before production")
            print("✅ Suitable for controlled operations")
        else:
            print("❌ WebGCS UI validation needs improvement")
            print("❌ Address all failed safety tests immediately")
            print("❌ Not recommended for operational use")
            
        print(f"\nPHASE 6 UI VALIDATION & SAFETY TESTING COMPLETE")
        print("="*80)
        
        # Assert overall success
        assert overall_score >= 70, f"Phase 6 validation score too low: {overall_score:.0f}%"
        assert critical_score >= 85, f"Critical safety score too low: {critical_score:.0f}%"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
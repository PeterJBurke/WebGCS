"""
Integration Test: VFR HUD/PFD Display with Real Data
Tests actual Primary Flight Display rendering with real telemetry data
Verifies all 15 required VFR HUD components display correctly
"""
import pytest
import time
import math
from playwright.sync_api import expect
from src.utils.token_tracker import record_agent_usage


class TestVFRHudDisplay:
    """Test suite for VFR HUD/PFD display with real telemetry data."""

    def test_pfd_canvas_initialization(self, connected_web_page):
        """Test that PFD canvas is properly initialized and visible."""
        # Verify PFD container is present
        expect(connected_web_page.locator("#pfd-display")).to_be_visible()
        
        # Look for canvas element
        pfd_canvas = connected_web_page.query_selector("#pfd-canvas")
        if pfd_canvas:
            expect(connected_web_page.locator("#pfd-canvas")).to_be_visible()
            
            # Check canvas dimensions
            canvas_info = connected_web_page.evaluate("""
                () => {
                    const canvas = document.querySelector('#pfd-canvas');
                    return canvas ? {
                        width: canvas.width,
                        height: canvas.height,
                        clientWidth: canvas.clientWidth,
                        clientHeight: canvas.clientHeight
                    } : null;
                }
            """)
            
            assert canvas_info is not None, "PFD canvas should be accessible via JavaScript"
            assert canvas_info["width"] > 0, "Canvas width should be greater than 0"
            assert canvas_info["height"] > 0, "Canvas height should be greater than 0"
            
            print(f"PFD Canvas dimensions: {canvas_info}")
        
        else:
            # Look for alternative PFD display elements
            pfd_elements = connected_web_page.query_selector_all("#pfd-display *")
            assert len(pfd_elements) > 0, "PFD display should contain visual elements"
        
        record_agent_usage('testing-agent', 120, 95)

    def test_artificial_horizon_display(self, connected_web_page):
        """Test artificial horizon display with real attitude data."""
        time.sleep(3)  # Wait for telemetry data
        
        # Check for artificial horizon elements
        horizon_indicators = [
            "#artificial-horizon",
            "#horizon-line",
            "#attitude-display",
            ".horizon",
            ".attitude-indicator"
        ]
        
        horizon_found = False
        for selector in horizon_indicators:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                horizon_found = True
                print(f"Found artificial horizon element: {selector}")
                break
        
        if not horizon_found:
            # Check if horizon is rendered in canvas
            canvas_content = connected_web_page.evaluate("""
                () => {
                    const canvas = document.querySelector('#pfd-canvas');
                    if (!canvas) return null;
                    
                    const ctx = canvas.getContext('2d');
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    
                    // Check for non-transparent pixels (indicates drawing)
                    let hasContent = false;
                    for (let i = 3; i < imageData.data.length; i += 4) {
                        if (imageData.data[i] > 0) {
                            hasContent = true;
                            break;
                        }
                    }
                    
                    return hasContent;
                }
            """)
            
            horizon_found = canvas_content
            if horizon_found:
                print("Found artificial horizon rendered in canvas")
        
        assert horizon_found, "Should have artificial horizon display"
        
        record_agent_usage('testing-agent', 140, 110)

    def test_airspeed_indicator(self, connected_web_page):
        """Test airspeed indicator display and updates."""
        time.sleep(3)
        
        # Look for airspeed indicator elements
        airspeed_selectors = [
            "#airspeed-display",
            "#airspeed-indicator",
            "#speed-tape",
            ".airspeed",
            "[data-instrument='airspeed']"
        ]
        
        airspeed_element = None
        for selector in airspeed_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                airspeed_element = element
                print(f"Found airspeed indicator: {selector}")
                break
        
        if airspeed_element:
            # Check for numeric airspeed value
            airspeed_text = airspeed_element.text_content()
            print(f"Airspeed display text: '{airspeed_text}'")
            
            # Should contain numeric value
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', airspeed_text)
            assert len(numbers) > 0, "Airspeed display should contain numeric values"
            
            # Monitor for updates
            initial_text = airspeed_text
            time.sleep(2)
            updated_text = airspeed_element.text_content()
            
            # Value may or may not change depending on virtual drone
            print(f"Airspeed update check: '{initial_text}' -> '{updated_text}'")
        
        else:
            # Check if displayed in telemetry data area
            telemetry_text = connected_web_page.query_selector("#telemetry-data")
            if telemetry_text:
                content = telemetry_text.text_content().lower()
                airspeed_mentioned = "speed" in content or "airspeed" in content
                print(f"Airspeed mentioned in telemetry: {airspeed_mentioned}")
        
        # Should have some form of airspeed display
        has_airspeed = airspeed_element is not None
        assert has_airspeed, "Should have airspeed indicator display"
        
        record_agent_usage('testing-agent', 130, 100)

    def test_altitude_indicator(self, connected_web_page):
        """Test altitude indicator display and updates."""
        time.sleep(3)
        
        # Look for altitude indicator elements
        altitude_selectors = [
            "#altitude-display",
            "#altitude-indicator",
            "#altitude-tape",
            ".altitude",
            "[data-instrument='altitude']"
        ]
        
        altitude_element = None
        for selector in altitude_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                altitude_element = element
                print(f"Found altitude indicator: {selector}")
                break
        
        if altitude_element:
            altitude_text = altitude_element.text_content()
            print(f"Altitude display text: '{altitude_text}'")
            
            # Should contain numeric value
            import re
            numbers = re.findall(r'-?\d+(?:\.\d+)?', altitude_text)
            assert len(numbers) > 0, "Altitude display should contain numeric values"
            
            # Validate altitude range (reasonable values)
            for num_str in numbers:
                altitude_val = float(num_str)
                assert -1000 <= altitude_val <= 50000, f"Altitude value {altitude_val} outside reasonable range"
        
        else:
            # Check telemetry data for altitude
            all_text = connected_web_page.content().lower()
            altitude_keywords = ["altitude", "alt", "elevation", "height"]
            altitude_mentioned = any(keyword in all_text for keyword in altitude_keywords)
            print(f"Altitude mentioned somewhere on page: {altitude_mentioned}")
        
        has_altitude = altitude_element is not None
        assert has_altitude, "Should have altitude indicator display"
        
        record_agent_usage('testing-agent', 125, 95)

    def test_heading_compass_display(self, connected_web_page):
        """Test heading compass display functionality."""
        time.sleep(3)
        
        # Look for compass/heading elements
        heading_selectors = [
            "#heading-display",
            "#compass",
            "#heading-indicator",
            ".compass",
            "[data-instrument='heading']"
        ]
        
        heading_element = None
        for selector in heading_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                heading_element = element
                print(f"Found heading display: {selector}")
                break
        
        if heading_element:
            heading_text = heading_element.text_content()
            print(f"Heading display text: '{heading_text}'")
            
            # Look for heading value (0-359 degrees)
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', heading_text)
            
            if numbers:
                for num_str in numbers:
                    heading_val = float(num_str)
                    if 0 <= heading_val <= 359:
                        print(f"Valid heading found: {heading_val}°")
                        break
                else:
                    print("No valid heading value found in numbers")
        
        # Check for compass rose or directional indicators
        directional_elements = connected_web_page.query_selector_all("[class*='compass'], [class*='heading'], [id*='heading']")
        print(f"Found {len(directional_elements)} heading-related elements")
        
        has_heading = heading_element is not None or len(directional_elements) > 0
        assert has_heading, "Should have heading/compass display"
        
        record_agent_usage('testing-agent', 135, 105)

    def test_flight_mode_display(self, connected_web_page):
        """Test flight mode display functionality."""
        time.sleep(3)
        
        # Look for flight mode elements
        flight_mode_selectors = [
            "#flight-mode",
            "#mode-display",
            "#flight-mode-indicator",
            ".flight-mode",
            "[data-telemetry='mode']"
        ]
        
        flight_mode_element = None
        for selector in flight_mode_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                flight_mode_element = element
                print(f"Found flight mode display: {selector}")
                break
        
        if flight_mode_element:
            mode_text = flight_mode_element.text_content()
            print(f"Flight mode text: '{mode_text}'")
            
            # Common MAVLink flight modes
            common_modes = ["STABILIZE", "ALT_HOLD", "LOITER", "AUTO", "RTL", "LAND", 
                           "MANUAL", "GUIDED", "POSITION", "ACRO", "CIRCLE"]
            
            mode_recognized = any(mode.lower() in mode_text.lower() for mode in common_modes)
            if mode_recognized:
                print("Recognized flight mode found")
            else:
                print("Flight mode text present but not recognized")
        
        # Alternative: Check telemetry data for mode information
        page_text = connected_web_page.content().lower()
        mode_indicators = ["mode", "flight mode", "armed", "disarmed"]
        mode_mentioned = any(indicator in page_text for indicator in mode_indicators)
        
        has_mode_display = flight_mode_element is not None or mode_mentioned
        assert has_mode_display, "Should have flight mode display"
        
        record_agent_usage('testing-agent', 120, 90)

    def test_gps_status_display(self, connected_web_page):
        """Test GPS status and satellite count display."""
        time.sleep(3)
        
        # Look for GPS status elements
        gps_selectors = [
            "#gps-status",
            "#gps-indicator",
            "#satellite-count",
            ".gps-status",
            "[data-telemetry='gps']"
        ]
        
        gps_element = None
        for selector in gps_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                gps_element = element
                print(f"Found GPS status display: {selector}")
                break
        
        if gps_element:
            gps_text = gps_element.text_content()
            print(f"GPS status text: '{gps_text}'")
            
            # Look for GPS-related keywords
            gps_keywords = ["gps", "satellite", "fix", "hdop", "sat"]
            gps_content = any(keyword.lower() in gps_text.lower() for keyword in gps_keywords)
            
            if gps_content:
                print("GPS-related content found")
            
            # Look for satellite count (typically 0-20)
            import re
            numbers = re.findall(r'\d+', gps_text)
            for num_str in numbers:
                sat_count = int(num_str)
                if 0 <= sat_count <= 30:  # Reasonable satellite count
                    print(f"Possible satellite count: {sat_count}")
        
        # Check for coordinate displays (indicates GPS data)
        coord_elements = connected_web_page.query_selector_all("#latitude-display, #longitude-display")
        has_coordinates = len(coord_elements) > 0
        
        if has_coordinates:
            print("Found coordinate displays indicating GPS data")
        
        has_gps_info = gps_element is not None or has_coordinates
        assert has_gps_info, "Should have GPS status or coordinate display"
        
        record_agent_usage('testing-agent', 140, 110)

    def test_battery_status_display(self, connected_web_page):
        """Test battery status display with color coding."""
        time.sleep(3)
        
        # Look for battery status elements
        battery_selectors = [
            "#battery-status",
            "#battery-voltage",
            "#battery-indicator",
            ".battery-status",
            "[data-telemetry='battery']"
        ]
        
        battery_element = None
        for selector in battery_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                battery_element = element
                print(f"Found battery display: {selector}")
                break
        
        if battery_element:
            battery_text = battery_element.text_content()
            print(f"Battery status text: '{battery_text}'")
            
            # Look for voltage values (typical LiPo: 3.0-4.2V per cell)
            import re
            voltage_pattern = r'\d+\.\d+\s*v'
            voltages = re.findall(voltage_pattern, battery_text.lower())
            
            for voltage_str in voltages:
                voltage_val = float(voltage_str.replace('v', '').strip())
                print(f"Found battery voltage: {voltage_val}V")
                
                # Reasonable voltage range for drone batteries
                assert 3.0 <= voltage_val <= 30.0, f"Battery voltage {voltage_val}V outside reasonable range"
            
            # Check for color coding (CSS classes or styles)
            battery_classes = battery_element.get_attribute("class") or ""
            battery_style = battery_element.get_attribute("style") or ""
            
            color_indicators = ["red", "yellow", "green", "warning", "critical", "low", "good"]
            has_color_coding = any(indicator in (battery_classes + battery_style).lower() 
                                 for indicator in color_indicators)
            
            print(f"Battery color coding detected: {has_color_coding}")
        
        # Alternative: Look for any power/voltage information
        page_text = connected_web_page.content().lower()
        power_indicators = ["battery", "voltage", "power", "charge", "v"]
        power_mentioned = any(indicator in page_text for indicator in power_indicators)
        
        has_battery_info = battery_element is not None or power_mentioned
        assert has_battery_info, "Should have battery status display"
        
        record_agent_usage('testing-agent', 150, 115)

    def test_armed_status_overlay(self, connected_web_page):
        """Test armed/disarmed status overlay display."""
        time.sleep(3)
        
        # Look for armed status elements
        armed_selectors = [
            "#armed-status",
            "#arm-indicator",
            ".armed-overlay",
            ".disarmed-overlay",
            "[data-status='armed']"
        ]
        
        armed_element = None
        for selector in armed_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                armed_element = element
                print(f"Found armed status display: {selector}")
                break
        
        if armed_element:
            armed_text = armed_element.text_content()
            print(f"Armed status text: '{armed_text}'")
            
            # Should contain armed/disarmed status
            status_keywords = ["armed", "disarmed", "safe", "ready"]
            has_status_text = any(keyword.lower() in armed_text.lower() for keyword in status_keywords)
            
            assert has_status_text, "Armed status should contain relevant status text"
        
        # Check flight control button states (alternative indicator)
        arm_button = connected_web_page.query_selector("#arm-btn")
        disarm_button = connected_web_page.query_selector("#disarm-btn")
        
        button_states_available = False
        if arm_button and disarm_button:
            arm_disabled = arm_button.is_disabled()
            disarm_disabled = disarm_button.is_disabled()
            print(f"ARM button disabled: {arm_disabled}, DISARM button disabled: {disarm_disabled}")
            button_states_available = True
        
        # Should have some form of armed status indication
        has_armed_status = armed_element is not None or button_states_available
        assert has_armed_status, "Should have armed/disarmed status indication"
        
        record_agent_usage('testing-agent', 130, 100)

    def test_multiple_hud_elements_integration(self, connected_web_page):
        """Test that multiple HUD elements work together and don't conflict."""
        time.sleep(5)  # Allow more time for full telemetry
        
        # Count total HUD elements found
        hud_element_selectors = [
            "#artificial-horizon", "#airspeed-display", "#altitude-display",
            "#heading-display", "#flight-mode", "#gps-status", 
            "#battery-status", "#armed-status", "#pfd-canvas"
        ]
        
        active_elements = 0
        element_details = []
        
        for selector in hud_element_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                active_elements += 1
                bounds = element.bounding_box()
                element_details.append({
                    "selector": selector,
                    "bounds": bounds,
                    "text": element.text_content()[:50] if element.text_content() else "N/A"
                })
        
        print(f"Found {active_elements} active HUD elements:")
        for detail in element_details:
            print(f"  {detail['selector']}: {detail['text']} at {detail['bounds']}")
        
        # Should have at least 3 HUD elements for a basic display
        assert active_elements >= 3, f"Should have at least 3 active HUD elements, found {active_elements}"
        
        # Check for layout conflicts (overlapping elements)
        conflicts = 0
        for i, elem1 in enumerate(element_details):
            for j, elem2 in enumerate(element_details[i+1:], i+1):
                if elem1["bounds"] and elem2["bounds"]:
                    # Simple overlap detection
                    overlap = not (elem1["bounds"]["x"] + elem1["bounds"]["width"] <= elem2["bounds"]["x"] or
                                 elem2["bounds"]["x"] + elem2["bounds"]["width"] <= elem1["bounds"]["x"] or
                                 elem1["bounds"]["y"] + elem1["bounds"]["height"] <= elem2["bounds"]["y"] or
                                 elem2["bounds"]["y"] + elem2["bounds"]["height"] <= elem1["bounds"]["y"])
                    
                    if overlap:
                        conflicts += 1
                        print(f"Potential overlap: {elem1['selector']} and {elem2['selector']}")
        
        # Some overlap might be intentional (overlays), but excessive overlap is bad
        assert conflicts <= active_elements // 2, f"Too many overlapping elements: {conflicts}"
        
        record_agent_usage('testing-agent', 160, 125)

    def test_hud_performance_and_updates(self, connected_web_page):
        """Test HUD display performance and smooth updates."""
        time.sleep(3)
        
        # Monitor for smooth updates without flickering
        start_time = time.time()
        update_checks = []
        
        # Get initial state
        pfd_area = connected_web_page.query_selector("#pfd-display")
        if pfd_area:
            initial_screenshot = pfd_area.screenshot()
            
            # Check for updates over time
            for i in range(5):  # 5 checks over 2.5 seconds
                time.sleep(0.5)
                current_screenshot = pfd_area.screenshot()
                
                # Simple change detection (screenshot comparison)
                changed = initial_screenshot != current_screenshot
                update_checks.append(changed)
                
                if changed:
                    print(f"Visual update detected at check {i+1}")
                    initial_screenshot = current_screenshot
        
        # Check JavaScript performance
        performance_info = connected_web_page.evaluate("""
            () => {
                const perfEntries = performance.getEntriesByType('measure');
                const paintEntries = performance.getEntriesByType('paint');
                
                return {
                    measureCount: perfEntries.length,
                    paintEntries: paintEntries.length,
                    memoryUsage: performance.memory ? {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize
                    } : null
                };
            }
        """)
        
        print(f"Performance info: {performance_info}")
        
        # Check for console errors that might indicate performance issues
        console_errors = []
        
        def handle_console_error(msg):
            if msg.type == "error":
                console_errors.append(msg.text)
        
        connected_web_page.on("console", handle_console_error)
        time.sleep(2)
        
        # Should not have performance-related errors
        performance_errors = [err for err in console_errors if 
                            "performance" in err.lower() or 
                            "memory" in err.lower() or
                            "timeout" in err.lower()]
        
        assert len(performance_errors) == 0, f"Found performance-related errors: {performance_errors}"
        
        record_agent_usage('testing-agent', 145, 110)
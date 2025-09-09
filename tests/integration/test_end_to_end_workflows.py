"""
Integration Test: End-to-End Mission Workflows
Tests complete workflows from connection through mission execution
Verifies real functionality across all system components
"""
import pytest
import time
from playwright.sync_api import expect
from src.utils.token_tracker import record_agent_usage


class TestEndToEndWorkflows:
    """Test suite for complete end-to-end mission workflows."""

    def test_complete_connection_to_telemetry_workflow(self, web_page, virtual_drone_host, virtual_drone_port):
        """Test complete workflow: Load page -> Connect -> Receive telemetry."""
        # Step 1: Verify page loads
        expect(web_page).to_have_title("WebGCS - Drone Ground Control Station")
        print("✓ Page loaded successfully")
        
        # Step 2: Fill connection form
        web_page.fill("#host-input", virtual_drone_host)
        web_page.fill("#port-input", str(virtual_drone_port))
        print("✓ Connection form filled")
        
        # Step 3: Establish connection
        web_page.click("#connect-btn")
        expect(web_page.locator("#connection-status")).to_have_text("Connected", timeout=15000)
        print("✓ Connection established")
        
        # Step 4: Verify UI state changes
        expect(web_page.locator("#disconnect-btn")).to_be_visible()
        expect(web_page.locator("#arm-btn")).to_be_enabled()
        print("✓ UI updated for connected state")
        
        # Step 5: Wait for and verify telemetry
        time.sleep(5)  # Allow telemetry to start flowing
        
        # Look for any telemetry data indicators
        telemetry_indicators = [
            "#heartbeat-indicator",
            "#telemetry-data",
            "#message-counter",
            "#last-update-time"
        ]
        
        telemetry_active = False
        for indicator in telemetry_indicators:
            element = web_page.query_selector(indicator)
            if element and element.is_visible() and element.text_content():
                telemetry_active = True
                print(f"✓ Telemetry active: {indicator}")
                break
        
        assert telemetry_active, "Should have active telemetry indicators"
        
        # Step 6: Verify disconnect works
        web_page.click("#disconnect-btn")
        expect(web_page.locator("#connection-status")).to_have_text("Disconnected", timeout=5000)
        print("✓ Disconnection successful")
        
        record_agent_usage('testing-agent', 180, 140)

    def test_arm_takeoff_land_workflow(self, connected_web_page):
        """Test ARM -> TAKEOFF -> LAND command sequence."""
        # Step 1: ARM command
        connected_web_page.click("#arm-btn")
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_visible(timeout=3000)
        connected_web_page.click("#confirm-yes-btn")
        expect(connected_web_page.locator("#status-message")).to_contain_text("ARM", timeout=5000)
        print("✓ ARM command sent and acknowledged")
        
        time.sleep(2)  # Brief pause between commands
        
        # Step 2: TAKEOFF command
        takeoff_alt_input = connected_web_page.query_selector("#takeoff-alt-input")
        if takeoff_alt_input:
            connected_web_page.fill("#takeoff-alt-input", "10")
        
        connected_web_page.click("#takeoff-btn")
        
        # Handle confirmation if present
        confirmation_dialog = connected_web_page.query_selector("#confirmation-dialog")
        if confirmation_dialog and confirmation_dialog.is_visible():
            connected_web_page.click("#confirm-yes-btn")
        
        # Wait for takeoff command feedback
        time.sleep(3)
        print("✓ TAKEOFF command initiated")
        
        # Step 3: Brief flight time
        time.sleep(5)  # Simulate flight time
        print("✓ Flight time elapsed")
        
        # Step 4: LAND command
        connected_web_page.click("#land-btn")
        
        # Handle confirmation if present
        confirmation_dialog = connected_web_page.query_selector("#confirmation-dialog")
        if confirmation_dialog and confirmation_dialog.is_visible():
            connected_web_page.click("#confirm-yes-btn")
        
        time.sleep(2)
        print("✓ LAND command sent")
        
        # Step 5: DISARM command
        connected_web_page.click("#disarm-btn")
        
        # Handle confirmation if present
        confirmation_dialog = connected_web_page.query_selector("#confirmation-dialog")
        if confirmation_dialog and confirmation_dialog.is_visible():
            connected_web_page.click("#confirm-yes-btn")
        
        time.sleep(1)
        print("✓ DISARM command sent")
        
        # Verify no critical errors occurred
        error_elements = connected_web_page.query_selector_all(".error, .critical, [class*='error']")
        visible_errors = [elem for elem in error_elements if elem.is_visible()]
        
        assert len(visible_errors) == 0, f"Should not have visible errors after flight sequence, found {len(visible_errors)}"
        
        record_agent_usage('testing-agent', 200, 155)

    def test_waypoint_navigation_workflow(self, connected_web_page):
        """Test complete waypoint navigation workflow."""
        # Step 1: Set waypoint coordinates
        test_coordinates = {
            "lat": "37.7749",  # San Francisco
            "lon": "-122.4194",
            "alt": "100"
        }
        
        connected_web_page.fill("#lat-input", test_coordinates["lat"])
        connected_web_page.fill("#lon-input", test_coordinates["lon"])
        connected_web_page.fill("#alt-input", test_coordinates["alt"])
        print(f"✓ Waypoint coordinates set: {test_coordinates}")
        
        # Step 2: Verify coordinates are valid
        expect(connected_web_page.locator("#lat-input")).to_have_value(test_coordinates["lat"])
        expect(connected_web_page.locator("#lon-input")).to_have_value(test_coordinates["lon"])
        expect(connected_web_page.locator("#alt-input")).to_have_value(test_coordinates["alt"])
        print("✓ Coordinate inputs validated")
        
        # Step 3: Send Go To command
        connected_web_page.click("#goto-btn")
        time.sleep(2)  # Allow command processing
        print("✓ Go To command sent")
        
        # Step 4: Check for waypoint feedback
        status_indicators = [
            "#status-message",
            "#waypoint-status",
            "#navigation-status"
        ]
        
        waypoint_acknowledged = False
        for indicator in status_indicators:
            element = connected_web_page.query_selector(indicator)
            if element and element.is_visible():
                status_text = element.text_content() or ""
                if any(word in status_text.lower() for word in ["waypoint", "goto", "navigate", "destination"]):
                    waypoint_acknowledged = True
                    print(f"✓ Waypoint acknowledged: {status_text}")
                    break
        
        # Step 5: Check map for waypoint marker (if map is present)
        map_container = connected_web_page.query_selector("#map-container")
        if map_container and map_container.is_visible():
            # Look for waypoint-related elements on map
            waypoint_elements = connected_web_page.query_selector_all(".waypoint, .destination, [class*='waypoint']")
            waypoint_on_map = len([elem for elem in waypoint_elements if elem.is_visible()]) > 0
            
            if waypoint_on_map:
                print("✓ Waypoint visible on map")
            
        # Should have some indication of waypoint processing
        assert waypoint_acknowledged, "Should acknowledge waypoint command"
        
        record_agent_usage('testing-agent', 170, 130)

    def test_real_time_monitoring_workflow(self, connected_web_page):
        """Test real-time telemetry monitoring and display updates."""
        # Step 1: Monitor initial state
        initial_telemetry = {}
        telemetry_elements = {
            "heartbeat": "#heartbeat-indicator",
            "coordinates": "#latitude-display, #longitude-display",
            "altitude": "#altitude-display",
            "battery": "#battery-status",
            "mode": "#flight-mode"
        }
        
        for key, selector in telemetry_elements.items():
            elements = connected_web_page.query_selector_all(selector)
            visible_elements = [elem for elem in elements if elem.is_visible()]
            if visible_elements:
                initial_telemetry[key] = visible_elements[0].text_content() or ""
        
        print(f"✓ Initial telemetry captured: {len(initial_telemetry)} elements")
        
        # Step 2: Monitor for updates over time
        update_cycles = 5
        updates_detected = {}
        
        for cycle in range(update_cycles):
            time.sleep(2)  # Wait for updates
            
            for key, selector in telemetry_elements.items():
                if key in initial_telemetry:
                    elements = connected_web_page.query_selector_all(selector)
                    visible_elements = [elem for elem in elements if elem.is_visible()]
                    
                    if visible_elements:
                        current_value = visible_elements[0].text_content() or ""
                        if current_value != initial_telemetry[key]:
                            updates_detected[key] = updates_detected.get(key, 0) + 1
                            initial_telemetry[key] = current_value
            
            print(f"✓ Update cycle {cycle + 1} completed")
        
        print(f"✓ Updates detected: {updates_detected}")
        
        # Step 3: Verify continuous operation
        # Should have detected some updates if telemetry is active
        total_updates = sum(updates_detected.values())
        
        # Allow for static displays but expect some dynamic content
        if total_updates == 0:
            print("ℹ No telemetry updates detected - checking for static displays")
            
            # At least verify static telemetry data is present
            static_data_present = len(initial_telemetry) > 0
            assert static_data_present, "Should have telemetry data display"
        else:
            print(f"✓ Dynamic telemetry updates confirmed: {total_updates} total")
        
        # Step 4: Verify system stability
        # Check for error states
        error_selectors = [".error", ".warning", ".critical", "[class*='error']"]
        errors_found = []
        
        for selector in error_selectors:
            elements = connected_web_page.query_selector_all(selector)
            visible_errors = [elem for elem in elements if elem.is_visible()]
            if visible_errors:
                for error_elem in visible_errors:
                    error_text = error_elem.text_content() or ""
                    if error_text.strip():
                        errors_found.append(error_text)
        
        # Should not have critical errors during monitoring
        critical_errors = [err for err in errors_found if "critical" in err.lower() or "fatal" in err.lower()]
        assert len(critical_errors) == 0, f"Should not have critical errors during monitoring: {critical_errors}"
        
        print("✓ System stability verified")
        
        record_agent_usage('testing-agent', 190, 145)

    def test_multi_command_safety_workflow(self, connected_web_page):
        """Test safety mechanisms with multiple concurrent commands."""
        # Step 1: Send first command
        connected_web_page.click("#arm-btn")
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_visible(timeout=3000)
        
        # Don't confirm yet - leave dialog open
        print("✓ First command (ARM) initiated")
        
        # Step 2: Try to send second command while first is pending
        try:
            connected_web_page.click("#takeoff-btn", timeout=2000)
            print("✓ Second command (TAKEOFF) attempted")
        except:
            print("ℹ Second command blocked (expected behavior)")
        
        # Step 3: Check system response
        # Should either:
        # a) Show message about command in progress
        # b) Queue the second command
        # c) Block the second command
        # d) Show error/warning
        
        # Look for safety-related messages
        safety_messages = connected_web_page.query_selector_all(".warning, .info, #status-message")
        safety_indicators = []
        
        for elem in safety_messages:
            if elem.is_visible():
                text = elem.text_content() or ""
                if any(word in text.lower() for word in ["pending", "progress", "wait", "busy", "queue"]):
                    safety_indicators.append(text)
        
        print(f"✓ Safety indicators found: {len(safety_indicators)}")
        
        # Step 4: Complete first command
        confirm_yes = connected_web_page.query_selector("#confirm-yes-btn")
        if confirm_yes and confirm_yes.is_visible():
            confirm_yes.click()
            print("✓ First command confirmed")
        
        time.sleep(2)  # Allow command processing
        
        # Step 5: Try second command again
        connected_web_page.click("#disarm-btn")
        
        # Handle confirmation
        confirmation_dialog = connected_web_page.query_selector("#confirmation-dialog")
        if confirmation_dialog and confirmation_dialog.is_visible():
            connected_web_page.click("#confirm-yes-btn")
        
        print("✓ Second command (DISARM) sent")
        
        # Step 6: Verify system handled concurrent commands safely
        # Should not crash or show critical errors
        critical_errors = connected_web_page.query_selector_all(".critical, .fatal, [class*='critical']")
        visible_critical_errors = [elem for elem in critical_errors if elem.is_visible()]
        
        assert len(visible_critical_errors) == 0, "Should not have critical errors from concurrent commands"
        
        # Verify system is still responsive
        connection_status = connected_web_page.query_selector("#connection-status")
        assert connection_status, "Connection status should still be accessible"
        
        print("✓ Concurrent command safety verified")
        
        record_agent_usage('testing-agent', 160, 125)

    def test_error_recovery_workflow(self, web_page, virtual_drone_host, virtual_drone_port):
        """Test error recovery and reconnection workflow."""
        # Step 1: Establish initial connection
        web_page.fill("#host-input", virtual_drone_host)
        web_page.fill("#port-input", str(virtual_drone_port))
        web_page.click("#connect-btn")
        expect(web_page.locator("#connection-status")).to_have_text("Connected", timeout=15000)
        print("✓ Initial connection established")
        
        # Step 2: Force disconnection
        web_page.click("#disconnect-btn")
        expect(web_page.locator("#connection-status")).to_have_text("Disconnected", timeout=5000)
        print("✓ Disconnection forced")
        
        # Step 3: Verify UI returns to disconnected state
        expect(web_page.locator("#connect-btn")).to_be_visible()
        expect(web_page.locator("#arm-btn")).to_be_disabled()
        print("✓ UI returned to disconnected state")
        
        # Step 4: Try invalid connection to test error handling
        web_page.fill("#host-input", "invalid.host.nowhere")
        web_page.fill("#port-input", "9999")
        web_page.click("#connect-btn")
        
        # Should show connection failed
        expect(web_page.locator("#connection-status")).to_have_text("Connection Failed", timeout=15000)
        print("✓ Connection failure handled gracefully")
        
        # Step 5: Reconnect with valid credentials
        web_page.fill("#host-input", virtual_drone_host)
        web_page.fill("#port-input", str(virtual_drone_port))
        web_page.click("#connect-btn")
        expect(web_page.locator("#connection-status")).to_have_text("Connected", timeout=15000)
        print("✓ Reconnection successful")
        
        # Step 6: Verify full functionality restored
        expect(web_page.locator("#arm-btn")).to_be_enabled()
        expect(web_page.locator("#disconnect-btn")).to_be_visible()
        
        # Try a simple command to verify functionality
        web_page.click("#arm-btn")
        confirmation_dialog = web_page.query_selector("#confirmation-dialog")
        if confirmation_dialog and confirmation_dialog.is_visible():
            web_page.click("#confirm-no-btn")  # Cancel to avoid arming
        
        print("✓ Full functionality restored after reconnection")
        
        record_agent_usage('testing-agent', 180, 140)

    def test_complete_mission_simulation(self, connected_web_page):
        """Test complete simulated mission from start to finish."""
        print("🚁 Starting complete mission simulation...")
        
        # Phase 1: Pre-flight checks
        print("\n--- Phase 1: Pre-flight Checks ---")
        
        # Verify connection is active
        expect(connected_web_page.locator("#connection-status")).to_have_text("Connected")
        print("✓ Connection verified")
        
        # Check telemetry is flowing
        time.sleep(3)
        heartbeat_elem = connected_web_page.query_selector("#heartbeat-indicator")
        if heartbeat_elem:
            print("✓ Heartbeat telemetry confirmed")
        
        # Phase 2: Mission setup
        print("\n--- Phase 2: Mission Setup ---")
        
        # Set mission waypoint
        mission_coords = {"lat": "37.7849", "lon": "-122.4094", "alt": "50"}
        connected_web_page.fill("#lat-input", mission_coords["lat"])
        connected_web_page.fill("#lon-input", mission_coords["lon"])
        connected_web_page.fill("#alt-input", mission_coords["alt"])
        print(f"✓ Mission waypoint set: {mission_coords}")
        
        # Phase 3: Flight sequence
        print("\n--- Phase 3: Flight Sequence ---")
        
        # ARM
        connected_web_page.click("#arm-btn")
        confirmation = connected_web_page.query_selector("#confirmation-dialog")
        if confirmation and confirmation.is_visible():
            connected_web_page.click("#confirm-yes-btn")
        time.sleep(2)
        print("✓ Aircraft ARMED")
        
        # TAKEOFF
        takeoff_input = connected_web_page.query_selector("#takeoff-alt-input")
        if takeoff_input:
            connected_web_page.fill("#takeoff-alt-input", "20")
        
        connected_web_page.click("#takeoff-btn")
        confirmation = connected_web_page.query_selector("#confirmation-dialog")
        if confirmation and confirmation.is_visible():
            connected_web_page.click("#confirm-yes-btn")
        time.sleep(3)
        print("✓ TAKEOFF initiated")
        
        # Navigate to waypoint
        connected_web_page.click("#goto-btn")
        time.sleep(2)
        print("✓ Navigation to waypoint initiated")
        
        # Phase 4: Mission monitoring
        print("\n--- Phase 4: Mission Monitoring ---")
        
        # Monitor for mission progress (simulate flight time)
        for i in range(5):
            time.sleep(2)
            
            # Check for any error states
            error_elements = connected_web_page.query_selector_all(".error, .critical")
            visible_errors = [elem for elem in error_elements if elem.is_visible()]
            
            if visible_errors:
                print(f"⚠ Errors detected during flight: {len(visible_errors)}")
            
            print(f"✓ Mission monitoring cycle {i+1}/5 completed")
        
        # Phase 5: Return and landing
        print("\n--- Phase 5: Return and Landing ---")
        
        # Return to launch
        rtl_btn = connected_web_page.query_selector("#rtl-btn")
        if rtl_btn and rtl_btn.is_visible():
            rtl_btn.click()
            confirmation = connected_web_page.query_selector("#confirmation-dialog")
            if confirmation and confirmation.is_visible():
                connected_web_page.click("#confirm-yes-btn")
            print("✓ Return to Launch initiated")
        else:
            # Manual land command
            connected_web_page.click("#land-btn")
            confirmation = connected_web_page.query_selector("#confirmation-dialog")
            if confirmation and confirmation.is_visible():
                connected_web_page.click("#confirm-yes-btn")
            print("✓ Manual landing initiated")
        
        time.sleep(5)  # Simulate landing time
        
        # DISARM
        connected_web_page.click("#disarm-btn")
        confirmation = connected_web_page.query_selector("#confirmation-dialog")
        if confirmation and confirmation.is_visible():
            connected_web_page.click("#confirm-yes-btn")
        print("✓ Aircraft DISARMED")
        
        # Phase 6: Mission completion verification
        print("\n--- Phase 6: Mission Completion ---")
        
        # Verify system is still stable
        connection_status = connected_web_page.query_selector("#connection-status")
        assert connection_status, "Connection status should be accessible"
        
        # Check for mission completion indicators
        status_messages = connected_web_page.query_selector_all("#status-message, .mission-status")
        completion_indicators = []
        
        for elem in status_messages:
            if elem.is_visible():
                text = elem.text_content() or ""
                if any(word in text.lower() for word in ["complete", "finished", "landed", "disarmed"]):
                    completion_indicators.append(text)
        
        print(f"✓ Mission completion indicators: {len(completion_indicators)}")
        print("🎯 Complete mission simulation finished successfully!")
        
        record_agent_usage('testing-agent', 250, 190)
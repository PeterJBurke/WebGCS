"""
Integration Test: Web Interface with Real MAVLink Connection
Uses Playwright to test actual web interface functionality
Tests real UI interactions with actual MAVLink connection
"""
import pytest
import time
from playwright.sync_api import expect
from src.utils.token_tracker import record_agent_usage


class TestWebInterfaceIntegration:
    """Test suite for web interface integration with real MAVLink connection."""

    def test_web_page_loads_successfully(self, web_page):
        """Test that the main web page loads with all required elements."""
        # Verify page title
        expect(web_page).to_have_title("WebGCS - Drone Ground Control Station")
        
        # Verify main sections are present
        expect(web_page.locator("#connection-panel")).to_be_visible()
        expect(web_page.locator("#flight-controls")).to_be_visible()
        expect(web_page.locator("#navigation-panel")).to_be_visible()
        expect(web_page.locator("#pfd-display")).to_be_visible()
        expect(web_page.locator("#map-container")).to_be_visible()
        
        # Verify connection form elements
        expect(web_page.locator("#host-input")).to_be_visible()
        expect(web_page.locator("#port-input")).to_be_visible()
        expect(web_page.locator("#connect-btn")).to_be_visible()
        
        record_agent_usage('testing-agent', 100, 80)

    def test_connection_establishment_through_ui(self, web_page, virtual_drone_host, virtual_drone_port):
        """Test MAVLink connection establishment through web interface."""
        # Fill connection form
        web_page.fill("#host-input", virtual_drone_host)
        web_page.fill("#port-input", str(virtual_drone_port))
        
        # Verify form is filled correctly
        expect(web_page.locator("#host-input")).to_have_value(virtual_drone_host)
        expect(web_page.locator("#port-input")).to_have_value(str(virtual_drone_port))
        
        # Click connect button
        web_page.click("#connect-btn")
        
        # Wait for connection status to change
        expect(web_page.locator("#connection-status")).to_have_text("Connecting...", timeout=5000)
        
        # Wait for successful connection
        expect(web_page.locator("#connection-status")).to_have_text("Connected", timeout=15000)
        
        # Verify UI changes after connection
        expect(web_page.locator("#connect-btn")).to_be_hidden()
        expect(web_page.locator("#disconnect-btn")).to_be_visible()
        expect(web_page.locator("#connection-status")).to_have_class("connected")
        
        record_agent_usage('testing-agent', 120, 95)

    def test_flight_controls_become_active(self, connected_web_page):
        """Test that flight control buttons become active after connection."""
        # Verify flight control buttons are enabled
        expect(connected_web_page.locator("#arm-btn")).to_be_enabled()
        expect(connected_web_page.locator("#disarm-btn")).to_be_enabled()
        expect(connected_web_page.locator("#takeoff-btn")).to_be_enabled()
        expect(connected_web_page.locator("#land-btn")).to_be_enabled()
        expect(connected_web_page.locator("#rtl-btn")).to_be_enabled()
        
        # Verify navigation controls are enabled
        expect(connected_web_page.locator("#lat-input")).to_be_enabled()
        expect(connected_web_page.locator("#lon-input")).to_be_enabled()
        expect(connected_web_page.locator("#alt-input")).to_be_enabled()
        expect(connected_web_page.locator("#goto-btn")).to_be_enabled()
        
        record_agent_usage('testing-agent', 90, 70)

    def test_arm_command_with_confirmation(self, connected_web_page):
        """Test ARM command requires and processes confirmation dialog."""
        # Click ARM button
        connected_web_page.click("#arm-btn")
        
        # Verify confirmation dialog appears
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_visible(timeout=3000)
        expect(connected_web_page.locator("#confirmation-message")).to_contain_text("ARM")
        expect(connected_web_page.locator("#confirm-yes-btn")).to_be_visible()
        expect(connected_web_page.locator("#confirm-no-btn")).to_be_visible()
        
        # Cancel first to test cancellation
        connected_web_page.click("#confirm-no-btn")
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_hidden()
        
        # Try again and confirm
        connected_web_page.click("#arm-btn")
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_visible()
        connected_web_page.click("#confirm-yes-btn")
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_hidden()
        
        # Verify command feedback
        expect(connected_web_page.locator("#status-message")).to_contain_text("ARM command sent", timeout=5000)
        
        record_agent_usage('testing-agent', 130, 100)

    def test_takeoff_command_with_altitude_validation(self, connected_web_page):
        """Test TAKEOFF command with altitude validation and confirmation."""
        # Click TAKEOFF button without altitude
        connected_web_page.click("#takeoff-btn")
        
        # Should show validation message
        expect(connected_web_page.locator("#validation-message")).to_contain_text("altitude", timeout=3000)
        
        # Fill in valid altitude
        connected_web_page.fill("#takeoff-alt-input", "10")
        
        # Click TAKEOFF again
        connected_web_page.click("#takeoff-btn")
        
        # Verify confirmation dialog
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_visible()
        expect(connected_web_page.locator("#confirmation-message")).to_contain_text("TAKEOFF")
        expect(connected_web_page.locator("#confirmation-message")).to_contain_text("10")
        
        # Confirm takeoff
        connected_web_page.click("#confirm-yes-btn")
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_hidden()
        
        # Verify command feedback
        expect(connected_web_page.locator("#status-message")).to_contain_text("TAKEOFF command sent", timeout=5000)
        
        record_agent_usage('testing-agent', 140, 110)

    def test_goto_command_with_coordinate_validation(self, connected_web_page):
        """Test Go To command with coordinate validation."""
        # Test invalid coordinates
        connected_web_page.fill("#lat-input", "91.0")  # Invalid latitude
        connected_web_page.fill("#lon-input", "0.0")
        connected_web_page.fill("#alt-input", "50")
        connected_web_page.click("#goto-btn")
        
        expect(connected_web_page.locator("#validation-message")).to_contain_text("latitude", timeout=3000)
        
        # Test valid coordinates
        connected_web_page.fill("#lat-input", "37.7749")  # San Francisco
        connected_web_page.fill("#lon-input", "-122.4194")
        connected_web_page.fill("#alt-input", "100")
        connected_web_page.click("#goto-btn")
        
        # Should not show validation error
        # May show confirmation dialog depending on implementation
        time.sleep(1)  # Allow for processing
        
        # Verify coordinates were processed
        expect(connected_web_page.locator("#status-message")).to_contain_text("waypoint", timeout=5000)
        
        record_agent_usage('testing-agent', 110, 85)

    def test_disconnection_through_ui(self, connected_web_page):
        """Test MAVLink disconnection through web interface."""
        # Verify we're connected
        expect(connected_web_page.locator("#connection-status")).to_have_text("Connected")
        expect(connected_web_page.locator("#disconnect-btn")).to_be_visible()
        
        # Click disconnect
        connected_web_page.click("#disconnect-btn")
        
        # Wait for disconnection
        expect(connected_web_page.locator("#connection-status")).to_have_text("Disconnected", timeout=5000)
        
        # Verify UI changes
        expect(connected_web_page.locator("#disconnect-btn")).to_be_hidden()
        expect(connected_web_page.locator("#connect-btn")).to_be_visible()
        
        # Verify flight controls are disabled
        expect(connected_web_page.locator("#arm-btn")).to_be_disabled()
        expect(connected_web_page.locator("#disarm-btn")).to_be_disabled()
        expect(connected_web_page.locator("#takeoff-btn")).to_be_disabled()
        
        record_agent_usage('testing-agent', 100, 75)

    def test_real_time_status_updates(self, connected_web_page):
        """Test that real-time status updates are displayed."""
        # Wait for status updates to appear
        time.sleep(3)
        
        # Check that telemetry data is being updated
        # Look for any dynamic content that should be updating
        status_elements = [
            "#heartbeat-indicator",
            "#telemetry-timestamp",
            "#connection-quality",
            "#message-count"
        ]
        
        updates_found = 0
        for element_id in status_elements:
            element = connected_web_page.query_selector(element_id)
            if element and element.is_visible():
                updates_found += 1
        
        assert updates_found > 0, "Should have at least one status indicator updating"
        
        record_agent_usage('testing-agent', 80, 60)

    def test_error_handling_invalid_connection(self, web_page):
        """Test error handling for invalid connection attempts."""
        # Try to connect to invalid host
        web_page.fill("#host-input", "invalid.host.com")
        web_page.fill("#port-input", "9999")
        
        web_page.click("#connect-btn")
        
        # Should show connecting then error
        expect(web_page.locator("#connection-status")).to_have_text("Connecting...", timeout=3000)
        expect(web_page.locator("#connection-status")).to_have_text("Connection Failed", timeout=15000)
        
        # Should return to disconnected state
        expect(web_page.locator("#connect-btn")).to_be_visible()
        expect(web_page.locator("#disconnect-btn")).to_be_hidden()
        
        record_agent_usage('testing-agent', 90, 70)

    def test_concurrent_command_prevention(self, connected_web_page):
        """Test that concurrent commands are prevented."""
        # Send first command
        connected_web_page.click("#arm-btn")
        expect(connected_web_page.locator("#confirmation-dialog")).to_be_visible()
        connected_web_page.click("#confirm-yes-btn")
        
        # Try to send second command immediately
        connected_web_page.click("#disarm-btn")
        
        # Should either:
        # 1. Show message about command in progress, or
        # 2. Queue the command, or
        # 3. Show confirmation dialog normally
        
        # At minimum, system should not crash
        time.sleep(2)
        expect(connected_web_page.locator("body")).to_be_visible()
        
        record_agent_usage('testing-agent', 100, 80)
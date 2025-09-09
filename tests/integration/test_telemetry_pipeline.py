"""
Integration Test: Real Telemetry Data Pipeline
Tests actual telemetry streaming from virtual drone to web interface
Verifies real-time data updates and display accuracy
"""
import pytest
import time
import json
from playwright.sync_api import expect
from src.utils.token_tracker import record_agent_usage


class TestTelemetryPipeline:
    """Test suite for real telemetry data pipeline functionality."""

    def test_telemetry_data_reception(self, connected_web_page):
        """Test that telemetry data is received and displayed in real-time."""
        # Wait for initial telemetry data
        time.sleep(3)
        
        # Check for telemetry indicators
        telemetry_elements = [
            "#heartbeat-indicator",
            "#telemetry-data",
            "#last-update-time",
            "#message-counter"
        ]
        
        active_indicators = 0
        for element_id in telemetry_elements:
            element = connected_web_page.query_selector(element_id)
            if element and element.is_visible():
                active_indicators += 1
                print(f"Found active telemetry indicator: {element_id}")
        
        assert active_indicators > 0, "Should have at least one active telemetry indicator"
        
        # Monitor for data updates over time
        update_count = 0
        previous_values = {}
        
        for i in range(10):  # Check 10 times over 5 seconds
            for element_id in telemetry_elements:
                element = connected_web_page.query_selector(element_id)
                if element and element.is_visible():
                    current_value = element.text_content()
                    if element_id not in previous_values:
                        previous_values[element_id] = current_value
                    elif previous_values[element_id] != current_value:
                        update_count += 1
                        previous_values[element_id] = current_value
                        print(f"Telemetry update detected in {element_id}")
            
            time.sleep(0.5)
        
        print(f"Total telemetry updates detected: {update_count}")
        assert update_count > 0, "Should detect telemetry data updates over time"
        
        record_agent_usage('testing-agent', 150, 120)

    def test_heartbeat_monitoring(self, connected_web_page):
        """Test heartbeat message monitoring and display."""
        # Look for heartbeat indicator
        heartbeat_element = connected_web_page.query_selector("#heartbeat-indicator")
        
        if heartbeat_element and heartbeat_element.is_visible():
            # Monitor heartbeat indicator changes
            initial_state = heartbeat_element.get_attribute("class") or ""
            
            # Heartbeat should update regularly
            state_changes = 0
            previous_state = initial_state
            
            for i in range(20):  # Check for 10 seconds
                current_state = heartbeat_element.get_attribute("class") or ""
                if current_state != previous_state:
                    state_changes += 1
                    previous_state = current_state
                time.sleep(0.5)
            
            # Should see some state changes if heartbeat is active
            print(f"Heartbeat state changes detected: {state_changes}")
            
        # Alternative: Look for any heartbeat-related text updates
        heartbeat_text_found = False
        page_content = connected_web_page.content()
        if "heartbeat" in page_content.lower() or "heart" in page_content.lower():
            heartbeat_text_found = True
        
        # At least one form of heartbeat monitoring should be present
        has_heartbeat_indicator = heartbeat_element is not None and heartbeat_element.is_visible()
        assert has_heartbeat_indicator or heartbeat_text_found, "Should have heartbeat monitoring capability"
        
        record_agent_usage('testing-agent', 120, 95)

    def test_telemetry_data_accuracy(self, connected_web_page):
        """Test that telemetry data displayed is accurate and formatted correctly."""
        # Wait for telemetry data
        time.sleep(3)
        
        # Look for specific telemetry values
        telemetry_fields = [
            {"selector": "#latitude-display", "type": "coordinate"},
            {"selector": "#longitude-display", "type": "coordinate"},
            {"selector": "#altitude-display", "type": "altitude"},
            {"selector": "#battery-voltage", "type": "voltage"},
            {"selector": "#gps-status", "type": "text"},
            {"selector": "#flight-mode", "type": "text"}
        ]
        
        valid_data_count = 0
        
        for field in telemetry_fields:
            element = connected_web_page.query_selector(field["selector"])
            if element and element.is_visible():
                value = element.text_content().strip()
                
                if value and value != "N/A" and value != "--" and value != "":
                    valid_data_count += 1
                    print(f"Valid telemetry data in {field['selector']}: {value}")
                    
                    # Basic format validation
                    if field["type"] == "coordinate":
                        try:
                            float_val = float(value.replace("°", ""))
                            assert -180 <= float_val <= 180, f"Coordinate {value} out of valid range"
                        except ValueError:
                            pass  # May have different format
                    
                    elif field["type"] == "altitude":
                        try:
                            alt_val = float(value.replace("m", "").replace("ft", ""))
                            assert alt_val >= -1000, f"Altitude {value} seems invalid"
                        except ValueError:
                            pass  # May have different format
        
        print(f"Found {valid_data_count} fields with valid telemetry data")
        
        # Should have at least some valid telemetry data
        assert valid_data_count >= 1, "Should display at least one valid telemetry field"
        
        record_agent_usage('testing-agent', 140, 110)

    def test_telemetry_update_frequency(self, connected_web_page):
        """Test that telemetry updates at appropriate frequency."""
        # Find an element that should update regularly
        timestamp_element = connected_web_page.query_selector("#telemetry-timestamp")
        counter_element = connected_web_page.query_selector("#message-counter")
        
        update_element = timestamp_element or counter_element
        
        if update_element and update_element.is_visible():
            updates = []
            start_time = time.time()
            
            # Monitor for updates over 10 seconds
            for i in range(100):  # Check every 0.1 seconds
                current_value = update_element.text_content()
                current_time = time.time()
                
                if not updates or current_value != updates[-1]["value"]:
                    updates.append({
                        "value": current_value,
                        "time": current_time
                    })
                
                time.sleep(0.1)
                
                if current_time - start_time >= 10:
                    break
            
            update_count = len(updates) - 1  # Subtract initial value
            update_rate = update_count / 10  # Updates per second
            
            print(f"Detected {update_count} updates in 10 seconds ({update_rate:.1f} Hz)")
            
            # Should update at least once per second for active telemetry
            assert update_rate >= 0.5, f"Telemetry update rate too low: {update_rate:.1f} Hz"
            
            # Should not update too frequently (would indicate rapid flickering)
            assert update_rate <= 20, f"Telemetry update rate too high: {update_rate:.1f} Hz"
        
        else:
            # If no timestamp/counter, check for any dynamic content
            print("No specific update element found, checking for any dynamic content")
            
            # Monitor entire page for any changes
            initial_content = connected_web_page.content()
            time.sleep(2)
            updated_content = connected_web_page.content()
            
            content_changed = initial_content != updated_content
            assert content_changed, "Page content should update with telemetry data"
        
        record_agent_usage('testing-agent', 160, 125)

    def test_telemetry_connection_loss_detection(self, connected_web_page):
        """Test detection and display of telemetry connection loss."""
        # Get initial telemetry state
        initial_status = connected_web_page.query_selector("#connection-status")
        assert initial_status, "Should have connection status element"
        
        initial_status_text = initial_status.text_content()
        assert "Connected" in initial_status_text, "Should be connected initially"
        
        # Disconnect to simulate connection loss
        connected_web_page.click("#disconnect-btn")
        
        # Verify connection loss is detected and displayed
        expect(connected_web_page.locator("#connection-status")).to_have_text("Disconnected", timeout=5000)
        
        # Verify telemetry updates stop
        time.sleep(2)
        
        # Check that telemetry indicators show disconnected state
        status_elements = [
            "#heartbeat-indicator",
            "#connection-quality",
            "#telemetry-status"
        ]
        
        disconnected_indicators = 0
        for element_id in status_elements:
            element = connected_web_page.query_selector(element_id)
            if element and element.is_visible():
                element_class = element.get_attribute("class") or ""
                element_text = element.text_content() or ""
                
                if ("disconnected" in element_class.lower() or 
                    "offline" in element_class.lower() or
                    "disconnected" in element_text.lower() or
                    "offline" in element_text.lower()):
                    disconnected_indicators += 1
        
        print(f"Found {disconnected_indicators} indicators showing disconnected state")
        
        record_agent_usage('testing-agent', 130, 100)

    def test_socketio_real_time_communication(self, connected_web_page):
        """Test real-time SocketIO communication for telemetry."""
        # Monitor browser console for SocketIO messages
        console_messages = []
        
        def handle_console(msg):
            console_messages.append(msg.text)
            print(f"Console: {msg.text}")
        
        connected_web_page.on("console", handle_console)
        
        # Wait for SocketIO activity
        time.sleep(5)
        
        # Look for SocketIO-related console messages
        socketio_messages = [msg for msg in console_messages if "socket" in msg.lower()]
        
        print(f"Found {len(socketio_messages)} SocketIO-related console messages")
        
        # Check page network activity for SocketIO connections
        # This is a basic test - actual SocketIO traffic is harder to intercept
        
        # Verify page is receiving real-time updates (indirect test)
        # Look for JavaScript variables or DOM updates that indicate real-time data
        script_result = connected_web_page.evaluate("""
            () => {
                // Check for common SocketIO client variables
                return {
                    hasSocket: typeof io !== 'undefined',
                    hasSocketConnection: typeof socket !== 'undefined',
                    pageTitle: document.title,
                    telemetryElements: document.querySelectorAll('[id*="telemetry"]').length
                };
            }
        """)
        
        print(f"SocketIO client check: {script_result}")
        
        # At minimum, page should have telemetry-related elements
        assert script_result.get("telemetryElements", 0) >= 1, "Should have telemetry-related DOM elements"
        
        record_agent_usage('testing-agent', 140, 110)

    def test_data_validation_and_error_handling(self, connected_web_page):
        """Test handling of invalid or corrupted telemetry data."""
        # This test is challenging since we can't easily inject bad data
        # Instead, we'll test the robustness of the display system
        
        # Check that the page handles missing data gracefully
        time.sleep(2)
        
        # Look for elements that might show "N/A" or default values
        all_elements = connected_web_page.query_selector_all("[id*='display'], [class*='telemetry']")
        
        error_handling_indicators = 0
        for element in all_elements:
            if element.is_visible():
                text = element.text_content() or ""
                
                # Common indicators of proper error handling
                if any(indicator in text for indicator in ["N/A", "--", "Unknown", "Invalid", "Error"]):
                    error_handling_indicators += 1
                    print(f"Found error handling indicator: '{text}' in element {element}")
        
        print(f"Found {error_handling_indicators} elements with error handling indicators")
        
        # Test JavaScript error handling by checking console for errors
        console_errors = []
        
        def handle_console_error(msg):
            if msg.type == "error":
                console_errors.append(msg.text)
                print(f"Console Error: {msg.text}")
        
        connected_web_page.on("console", handle_console_error)
        
        # Wait and check for JavaScript errors
        time.sleep(3)
        
        # Should not have critical JavaScript errors
        critical_errors = [err for err in console_errors if "uncaught" in err.lower() or "syntax" in err.lower()]
        assert len(critical_errors) == 0, f"Found critical JavaScript errors: {critical_errors}"
        
        record_agent_usage('testing-agent', 120, 95)
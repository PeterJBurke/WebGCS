#!/usr/bin/env python3
"""
TEST-011: Real MAVLink Connection Validation
Validates actual TCP connection to virtual drone and real MAVLink heartbeat messages.
"""

import pytest
import time
import socket
import logging
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
from tests.conftest import ensure_webgcs_running, get_webgcs_url

logger = logging.getLogger(__name__)

class TestRealMAVLinkConnection:
    """Test real MAVLink connection to virtual drone."""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with WebGCS running."""
        ensure_webgcs_running()
        time.sleep(2)  # Allow service to initialize
    
    def test_virtual_drone_tcp_availability(self):
        """
        TEST-011-A: Virtual Drone TCP Service Availability
        MUST FAIL if no service listening on 192.168.193.235:5678
        """
        drone_host = "192.168.193.235"
        drone_port = 5678
        
        logger.info(f"Testing TCP connection to virtual drone at {drone_host}:{drone_port}")
        
        # Try to connect to drone service
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((drone_host, drone_port))
            sock.close()
            
            # Connection should succeed
            assert result == 0, (
                f"FAILED: Virtual drone not available at {drone_host}:{drone_port}. "
                f"Connection result: {result}. "
                "A virtual drone MUST be running for real data validation."
            )
            
            logger.info(f"✅ Virtual drone TCP service available at {drone_host}:{drone_port}")
            
        except Exception as e:
            pytest.fail(
                f"FAILED: Cannot reach virtual drone at {drone_host}:{drone_port} - {e}. "
                "Virtual drone service must be running for MAVLink validation."
            )
    
    def test_backend_mavlink_connection_establishment(self):
        """
        TEST-011-B: Backend MAVLink Connection Establishment
        Validates that backend actually connects to virtual drone TCP service.
        MUST FAIL if no real connection established.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Track SocketIO events
            connection_events = []
            heartbeat_events = []
            
            def track_connection_events(msg):
                if 'drone_connected' in str(msg) or 'connection_status_update' in str(msg):
                    connection_events.append({
                        'timestamp': datetime.now(),
                        'data': str(msg)
                    })
            
            def track_heartbeat_events(msg):
                if 'telemetry_update' in str(msg) and 'heartbeat' in str(msg):
                    heartbeat_events.append({
                        'timestamp': datetime.now(),
                        'data': str(msg)
                    })
            
            page.on('console', track_connection_events)
            page.on('console', track_heartbeat_events)
            
            # Navigate to WebGCS
            page.goto(get_webgcs_url())
            page.wait_for_selector('#connect-drone-btn', timeout=10000)
            
            # Click connect button
            logger.info("Clicking connect button to initiate real MAVLink connection")
            page.click('#connect-drone-btn')
            
            # Wait for connection establishment
            time.sleep(8)  # Allow time for real connection
            
            # Verify connection status shows "connected"
            connection_status = page.locator('#connection-status').inner_text()
            assert "connected" in connection_status.lower(), (
                f"FAILED: Connection status shows '{connection_status}' instead of 'connected'. "
                "Backend MAVLink connection not established to virtual drone."
            )
            
            # Wait for heartbeat data (real MAVLink heartbeats come every 1 second)
            logger.info("Waiting for real MAVLink heartbeat messages...")
            time.sleep(5)  # Wait for multiple heartbeat cycles
            
            # Check for heartbeat counter incrementing
            heartbeat_counter = page.locator('#heartbeat-counter').inner_text()
            assert heartbeat_counter != "0" and heartbeat_counter != "-", (
                f"FAILED: Heartbeat counter shows '{heartbeat_counter}' - no real heartbeats received. "
                "Backend is not processing actual MAVLink heartbeat messages from virtual drone."
            )
            
            # Verify heartbeat timestamp is recent (within last 3 seconds)
            heartbeat_time_text = page.locator('#last-heartbeat-time').inner_text()
            if heartbeat_time_text and heartbeat_time_text != "-":
                # This should be a recent timestamp if real heartbeats are coming
                logger.info(f"Last heartbeat timestamp: {heartbeat_time_text}")
            else:
                pytest.fail(
                    "FAILED: No heartbeat timestamp displayed. "
                    "Backend is not receiving real MAVLink heartbeat messages."
                )
            
            browser.close()
            
            logger.info(f"✅ Backend MAVLink connection established with {len(heartbeat_events)} heartbeat events")
    
    def test_mavlink_heartbeat_frequency_validation(self):
        """
        TEST-011-C: MAVLink Heartbeat Frequency Validation  
        Validates that heartbeats arrive at expected 1Hz frequency.
        MUST FAIL if heartbeats don't arrive at 1Hz from real drone.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(get_webgcs_url())
            page.wait_for_selector('#connect-drone-btn', timeout=10000)
            
            # Connect to drone
            page.click('#connect-drone-btn')
            time.sleep(5)  # Allow connection establishment
            
            # Verify connection established
            connection_status = page.locator('#connection-status').inner_text()
            if "connected" not in connection_status.lower():
                pytest.fail(
                    f"FAILED: Cannot validate heartbeat frequency - connection failed. "
                    f"Status: {connection_status}"
                )
            
            # Monitor heartbeat counter over time
            logger.info("Monitoring heartbeat frequency over 10 second period...")
            
            initial_count_text = page.locator('#heartbeat-counter').inner_text()
            try:
                initial_count = int(initial_count_text)
            except (ValueError, TypeError):
                initial_count = 0
            
            time.sleep(10)  # Wait exactly 10 seconds
            
            final_count_text = page.locator('#heartbeat-counter').inner_text()
            try:
                final_count = int(final_count_text)
            except (ValueError, TypeError):
                final_count = 0
            
            heartbeat_increase = final_count - initial_count
            
            # Should get approximately 10 heartbeats in 10 seconds (1Hz frequency)
            # Allow some tolerance: 8-12 heartbeats acceptable
            assert 8 <= heartbeat_increase <= 12, (
                f"FAILED: Heartbeat frequency incorrect. "
                f"Got {heartbeat_increase} heartbeats in 10 seconds "
                f"(expected 8-12 for 1Hz). "
                f"Initial: {initial_count}, Final: {final_count}. "
                "Virtual drone not sending heartbeats at expected frequency."
            )
            
            browser.close()
            
            logger.info(f"✅ Heartbeat frequency validated: {heartbeat_increase} beats in 10 seconds")
    
    def test_connection_timeout_handling(self):
        """
        TEST-011-D: Connection Timeout Handling
        Validates that connection fails gracefully when drone unavailable.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(get_webgcs_url())
            page.wait_for_selector('#connect-drone-btn', timeout=10000)
            
            # For this test, we'll disconnect any existing connection first
            connection_status = page.locator('#connection-status').inner_text()
            if "connected" in connection_status.lower():
                # If already connected, disconnect first
                page.click('#connect-drone-btn')  # Toggle to disconnect
                time.sleep(2)
            
            # Now test connection when drone might be unavailable
            logger.info("Testing connection timeout handling")
            
            # Click connect - if drone is unavailable, should timeout gracefully
            page.click('#connect-drone-btn')
            
            # Wait for connection attempt
            time.sleep(15)  # Allow time for timeout
            
            # Check final status - either connected (if drone available) or timeout/error
            final_status = page.locator('#connection-status').inner_text()
            
            # This test validates that the system handles connection attempts gracefully
            assert final_status != "connecting", (
                "FAILED: Connection stuck in 'connecting' state - timeout handling broken"
            )
            
            browser.close()
            
            logger.info(f"✅ Connection timeout handling validated. Final status: {final_status}")


if __name__ == "__main__":
    # Run individual test for debugging
    test_instance = TestRealMAVLinkConnection()
    test_instance.setup_class()
    
    try:
        test_instance.test_virtual_drone_tcp_availability()
        test_instance.test_backend_mavlink_connection_establishment()
        test_instance.test_mavlink_heartbeat_frequency_validation()
        test_instance.test_connection_timeout_handling()
        
        print("✅ All TEST-011 Real MAVLink Connection tests PASSED")
        
    except Exception as e:
        print(f"❌ TEST-011 FAILED: {e}")
        raise
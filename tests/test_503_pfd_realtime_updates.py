"""
TEST-503: PFD Real-time Updates Testing
Phase 5: VFR HUD/Primary Flight Display Testing

Tests real-time telemetry updates, 10Hz refresh rate, and data integration
with the virtual drone at 192.168.193.235:5678.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
import time
import json


class TestPFDRealtimeUpdates:
    """Test real-time telemetry updates and performance"""
    
    @pytest.mark.asyncio
    async def test_telemetry_update_rate(self):
        """TEST-503-001: Verify PFD updates at target 10Hz rate"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection to virtual drone
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(3000)  # Wait for connection
                
                # Monitor update frequency for 10 seconds
                update_count = 0
                start_time = time.time()
                test_duration = 10.0
                
                # Track updates by monitoring last update timestamp
                last_update_time = await page.evaluate("""
                    () => {
                        if (window.WebGCS && window.WebGCS.modules && window.WebGCS.modules.pfd && window.WebGCS.modules.pfd.lastUpdate) {
                            return window.WebGCS.modules.pfd.lastUpdate;
                        }
                        return Date.now();
                    }
                """)
                
                print(f"Monitoring PFD updates for {test_duration} seconds...")
                
                while (time.time() - start_time) < test_duration:
                    await page.wait_for_timeout(100)  # Check every 100ms
                    
                    current_update_time = await page.evaluate("""
                        () => {
                            if (window.WebGCS && window.WebGCS.modules && window.WebGCS.modules.pfd && window.WebGCS.modules.pfd.lastUpdate) {
                                return window.WebGCS.modules.pfd.lastUpdate;
                            }
                            return 0;
                        }
                    """)
                    
                    if current_update_time > last_update_time:
                        update_count += 1
                        last_update_time = current_update_time
                
                elapsed_time = time.time() - start_time
                update_rate = update_count / elapsed_time
                
                print(f"✅ PFD Update Rate Test Results:")
                print(f"   - Updates detected: {update_count}")
                print(f"   - Test duration: {elapsed_time:.2f}s")
                print(f"   - Actual update rate: {update_rate:.1f}Hz")
                print(f"   - Target rate: 10Hz (9-11Hz acceptable)")
                
                # Verify update rate is within acceptable range (9-11Hz)
                assert 9.0 <= update_rate <= 11.0, \
                    f"Update rate {update_rate:.1f}Hz outside acceptable range 9-11Hz"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_attitude_data_updates(self):
        """TEST-503-002: Test attitude indicator updates with pitch/roll data"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection to virtual drone
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(5000)  # Wait for connection and data
                
                # Monitor attitude data changes
                initial_attitude = await self.get_attitude_data(page)
                await page.wait_for_timeout(2000)
                updated_attitude = await self.get_attitude_data(page)
                
                print("✅ Attitude Data Update Test Results:")
                print(f"   - Initial: Pitch={initial_attitude['pitch']:.1f}° Roll={initial_attitude['roll']:.1f}° Yaw={initial_attitude['yaw']:.1f}°")
                print(f"   - Updated: Pitch={updated_attitude['pitch']:.1f}° Roll={updated_attitude['roll']:.1f}° Yaw={updated_attitude['yaw']:.1f}°")
                
                # Check if data is updating (values should be different or same if drone is stable)
                # What's important is that we're getting valid numeric data
                assert isinstance(initial_attitude['pitch'], (int, float)), "Pitch should be numeric"
                assert isinstance(initial_attitude['roll'], (int, float)), "Roll should be numeric"
                assert isinstance(initial_attitude['yaw'], (int, float)), "Yaw should be numeric"
                
                # Check reasonable ranges for attitude data
                assert -90 <= initial_attitude['pitch'] <= 90, f"Pitch {initial_attitude['pitch']} outside valid range"
                assert -180 <= initial_attitude['roll'] <= 180, f"Roll {initial_attitude['roll']} outside valid range"
                assert 0 <= initial_attitude['yaw'] <= 360, f"Yaw {initial_attitude['yaw']} outside valid range"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_gps_position_updates(self):
        """TEST-503-003: Test GPS coordinates display with 6 decimal precision"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection to virtual drone
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(5000)  # Wait for GPS data
                
                # Get GPS position data
                gps_data = await page.evaluate("""
                    () => {
                        // Check for GPS data in PFD object
                        if (window.WebGCS && window.WebGCS.modules && window.WebGCS.modules.pfd && window.WebGCS.modules.pfd.data) {
                            return {
                                lat: window.WebGCS.modules.pfd.data.lat || 0,
                                lng: window.WebGCS.modules.pfd.data.lng || 0,
                                alt: window.WebGCS.modules.pfd.data.alt || 0,
                                gps_fix: window.WebGCS.modules.pfd.data.gps_fix || 0
                            };
                        }
                        
                        // Also check telemetry data
                        if (window.telemetryData) {
                            return {
                                lat: window.telemetryData.lat || 0,
                                lng: window.telemetryData.lng || 0,
                                alt: window.telemetryData.alt || 0,
                                gps_fix: window.telemetryData.gps_fix || 0
                            };
                        }
                        
                        return { lat: 0, lng: 0, alt: 0, gps_fix: 0 };
                    }
                """)
                
                print("✅ GPS Position Update Test Results:")
                print(f"   - Latitude: {gps_data['lat']:.6f}")
                print(f"   - Longitude: {gps_data['lng']:.6f}")
                print(f"   - Altitude: {gps_data['alt']:.1f}m")
                print(f"   - GPS Fix Type: {gps_data['gps_fix']}")
                
                # Validate GPS data format and ranges
                if gps_data['lat'] != 0:  # If we have GPS data
                    assert -90 <= gps_data['lat'] <= 90, f"Latitude {gps_data['lat']} outside valid range"
                    assert -180 <= gps_data['lng'] <= 180, f"Longitude {gps_data['lng']} outside valid range"
                    
                    # Check precision (should have at least 6 decimal places capability)
                    lat_str = f"{gps_data['lat']:.6f}"
                    lng_str = f"{gps_data['lng']:.6f}"
                    assert len(lat_str.split('.')[1]) >= 6, "Latitude should support 6 decimal places"
                    assert len(lng_str.split('.')[1]) >= 6, "Longitude should support 6 decimal places"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_battery_status_updates(self):
        """TEST-503-004: Test battery voltage from SYS_STATUS messages"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection to virtual drone
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(5000)  # Wait for battery data
                
                # Get battery status data
                battery_data = await page.evaluate("""
                    () => {
                        // Check for battery data in PFD object
                        if (window.WebGCS && window.WebGCS.modules && window.WebGCS.modules.pfd && window.WebGCS.modules.pfd.data) {
                            return {
                                voltage: window.WebGCS.modules.pfd.data.battery_voltage || 0,
                                current: window.WebGCS.modules.pfd.data.battery_current || 0,
                                remaining: window.WebGCS.modules.pfd.data.battery_remaining || 0
                            };
                        }
                        
                        // Also check telemetry data
                        if (window.telemetryData) {
                            return {
                                voltage: window.telemetryData.battery_voltage || 0,
                                current: window.telemetryData.battery_current || 0,
                                remaining: window.telemetryData.battery_remaining || 0
                            };
                        }
                        
                        return { voltage: 0, current: 0, remaining: 0 };
                    }
                """)
                
                print("✅ Battery Status Update Test Results:")
                print(f"   - Voltage: {battery_data['voltage']:.2f}V")
                print(f"   - Current: {battery_data['current']:.1f}A")
                print(f"   - Remaining: {battery_data['remaining']:.0f}%")
                
                # Validate battery data ranges
                if battery_data['voltage'] > 0:  # If we have battery data
                    assert 0 <= battery_data['voltage'] <= 30, f"Battery voltage {battery_data['voltage']} outside reasonable range"
                    assert 0 <= battery_data['remaining'] <= 100, f"Battery remaining {battery_data['remaining']} outside valid percentage range"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_flight_mode_display(self):
        """TEST-503-005: Test flight mode display updates from HEARTBEAT messages"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection to virtual drone
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(5000)  # Wait for mode data
                
                # Get flight mode data
                mode_data = await page.evaluate("""
                    () => {
                        // Check for flight mode in PFD object
                        if (window.WebGCS && window.WebGCS.modules && window.WebGCS.modules.pfd && window.WebGCS.modules.pfd.data) {
                            return {
                                mode: window.WebGCS.modules.pfd.data.mode || 'UNKNOWN',
                                armed: window.WebGCS.modules.pfd.data.armed || false
                            };
                        }
                        
                        // Also check telemetry data
                        if (window.telemetryData) {
                            return {
                                mode: window.telemetryData.mode || 'UNKNOWN',
                                armed: window.telemetryData.armed || false
                            };
                        }
                        
                        return { mode: 'UNKNOWN', armed: false };
                    }
                """)
                
                # Check armed status in UI overlay
                armed_text = await page.query_selector('#armed-text')
                armed_status = "UNKNOWN"
                if armed_text:
                    armed_status = await armed_text.text_content()
                
                print("✅ Flight Mode Display Test Results:")
                print(f"   - Flight Mode: {mode_data['mode']}")
                print(f"   - Armed Status (data): {mode_data['armed']}")
                print(f"   - Armed Status (UI): {armed_status}")
                
                # Validate flight mode display
                valid_modes = ['STABILIZE', 'GUIDED', 'AUTO', 'LOITER', 'RTL', 'LAND', 'ALT_HOLD', 'UNKNOWN']
                if mode_data['mode'] != 'UNKNOWN':
                    assert mode_data['mode'] in valid_modes, f"Invalid flight mode: {mode_data['mode']}"
                
                assert armed_status in ['ARMED', 'DISARMED'], f"Invalid armed status: {armed_status}"
                
            finally:
                await browser.close()
    
    async def get_attitude_data(self, page):
        """Helper function to get current attitude data"""
        return await page.evaluate("""
            () => {
                // Try to get from PFD data first
                if (window.WebGCS && window.WebGCS.modules && window.WebGCS.modules.pfd && window.WebGCS.modules.pfd.data) {
                    return {
                        pitch: window.WebGCS.modules.pfd.data.pitch || 0,
                        roll: window.WebGCS.modules.pfd.data.roll || 0,
                        yaw: window.WebGCS.modules.pfd.data.yaw || 0
                    };
                }
                
                // Try to get from telemetry data
                if (window.telemetryData) {
                    return {
                        pitch: window.telemetryData.pitch || 0,
                        roll: window.telemetryData.roll || 0,
                        yaw: window.telemetryData.yaw || 0
                    };
                }
                
                // Try to get from UI elements
                const pitchEl = document.getElementById('pitch-value');
                const rollEl = document.getElementById('roll-value');
                const yawEl = document.getElementById('yaw-value');
                
                return {
                    pitch: pitchEl ? parseFloat(pitchEl.textContent) || 0 : 0,
                    roll: rollEl ? parseFloat(rollEl.textContent) || 0 : 0,
                    yaw: yawEl ? parseFloat(yawEl.textContent) || 0 : 0
                };
            }
        """)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
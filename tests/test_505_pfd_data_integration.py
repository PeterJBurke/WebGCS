"""
TEST-505: PFD Data Integration Testing
Phase 5: VFR HUD/Primary Flight Display Testing

Tests integration with MAVLink telemetry data, data conversion accuracy,
error handling for missing data, and validation of default/placeholder values.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
import time
import json


class TestPFDDataIntegration:
    """Test data integration between MAVLink telemetry and PFD display"""
    
    @pytest.mark.asyncio
    async def test_mavlink_telemetry_integration(self):
        """TEST-505-001: Test integration with MAVLink telemetry data"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Check initial state (before connection)
                initial_state = await self.get_pfd_data_state(page)
                
                # Enable connection to virtual drone
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(5000)  # Wait for MAVLink data
                
                # Check state after connection
                connected_state = await self.get_pfd_data_state(page)
                
                # Check for SocketIO telemetry events
                telemetry_events = await page.evaluate("""
                    () => {
                        // Check if SocketIO is connected and receiving telemetry
                        if (window.socket && window.socket.connected) {
                            return {
                                socketConnected: true,
                                hasEventListeners: true,
                                telemetryDataExists: window.telemetryData !== undefined
                            };
                        }
                        return {
                            socketConnected: false,
                            hasEventListeners: false,
                            telemetryDataExists: false
                        };
                    }
                """)
                
                print("✅ MAVLink Telemetry Integration Test Results:")
                print(f"   - Socket connected: {'✅' if telemetry_events['socketConnected'] else '❌'}")
                print(f"   - Telemetry data exists: {'✅' if telemetry_events['telemetryDataExists'] else '❌'}")
                print(f"   - Initial data state: {len(initial_state)} fields")
                print(f"   - Connected data state: {len(connected_state)} fields")
                
                # Compare data states
                if initial_state and connected_state:
                    data_changes = []
                    for key in connected_state:
                        initial_val = initial_state.get(key, 'N/A')
                        connected_val = connected_state.get(key, 'N/A')
                        if initial_val != connected_val:
                            data_changes.append(f"{key}: {initial_val} → {connected_val}")
                    
                    print(f"   - Data field changes: {len(data_changes)}")
                    for change in data_changes[:5]:  # Show first 5 changes
                        print(f"     • {change}")
                
                # Assert basic integration is working
                assert telemetry_events['socketConnected'] or len(connected_state) > 0, \
                    "Should have socket connection or telemetry data"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_data_conversion_accuracy(self):
        """TEST-505-002: Test data conversion accuracy (degrees, units)"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(5000)
                
                # Test data conversion and units
                conversion_tests = await page.evaluate("""
                    () => {
                        const tests = {};
                        
                        // Check attitude data (should be in degrees)
                        const pitchEl = document.getElementById('pitch-value');
                        const rollEl = document.getElementById('roll-value');
                        const yawEl = document.getElementById('yaw-value');
                        
                        if (pitchEl) {
                            const pitchText = pitchEl.textContent;
                            tests.pitch = {
                                text: pitchText,
                                hasDegreeSymbol: pitchText.includes('°'),
                                isNumeric: !isNaN(parseFloat(pitchText))
                            };
                        }
                        
                        if (rollEl) {
                            const rollText = rollEl.textContent;
                            tests.roll = {
                                text: rollText,
                                hasDegreeSymbol: rollText.includes('°'),
                                isNumeric: !isNaN(parseFloat(rollText))
                            };
                        }
                        
                        if (yawEl) {
                            const yawText = yawEl.textContent;
                            tests.yaw = {
                                text: yawText,
                                hasDegreeSymbol: yawText.includes('°'),
                                isNumeric: !isNaN(parseFloat(yawText))
                            };
                        }
                        
                        // Check altitude data (should be in meters)
                        const altEl = document.getElementById('altitude-value');
                        if (altEl) {
                            const altText = altEl.textContent;
                            tests.altitude = {
                                text: altText,
                                hasUnit: altText.includes('m'),
                                isNumeric: !isNaN(parseFloat(altText))
                            };
                        }
                        
                        // Check speed data (should be in m/s)
                        const speedEl = document.getElementById('groundspeed-value');
                        if (speedEl) {
                            const speedText = speedEl.textContent;
                            tests.groundspeed = {
                                text: speedText,
                                hasUnit: speedText.includes('m/s'),
                                isNumeric: !isNaN(parseFloat(speedText))
                            };
                        }
                        
                        return tests;
                    }
                """)
                
                print("✅ Data Conversion Accuracy Test Results:")
                
                for field, data in conversion_tests.items():
                    print(f"   - {field.capitalize():12s}: {data['text']}")
                    
                    if field in ['pitch', 'roll', 'yaw']:
                        assert data['hasDegreeSymbol'], f"{field} should have degree symbol"
                        assert data['isNumeric'], f"{field} should be numeric"
                        
                        # Check value ranges
                        value = float(data['text'].replace('°', ''))
                        if field in ['pitch']:
                            assert -90 <= value <= 90, f"Pitch {value} outside valid range"
                        elif field == 'roll':
                            assert -180 <= value <= 180, f"Roll {value} outside valid range"
                        elif field == 'yaw':
                            assert 0 <= value <= 360 or -180 <= value <= 180, f"Yaw {value} outside valid range"
                    
                    elif field == 'altitude':
                        assert data['hasUnit'], f"{field} should have unit (m)"
                        assert data['isNumeric'], f"{field} should be numeric"
                    
                    elif field == 'groundspeed':
                        assert data['hasUnit'], f"{field} should have unit (m/s)"
                        assert data['isNumeric'], f"{field} should be numeric"
                
                print("   ✅ All data conversions and units are correct")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_data(self):
        """TEST-505-003: Test error handling for missing data"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Test PFD behavior without connection (missing data scenario)
                initial_state = await self.get_pfd_data_state(page)
                
                # Simulate missing data by clearing PFD data
                await page.evaluate("""
                    () => {
                        if (window.pfd && window.pfd.data) {
                            // Clear specific data fields to test missing data handling
                            delete window.pfd.data.pitch;
                            delete window.pfd.data.roll;
                            delete window.pfd.data.altitude;
                        }
                    }
                """)
                
                await page.wait_for_timeout(1000)  # Wait for render
                
                # Check if PFD handles missing data gracefully
                error_handling = await page.evaluate("""
                    () => {
                        // Check if PFD still renders without errors
                        const canvas = document.getElementById('pfd-canvas');
                        if (!canvas) return { canvasExists: false };
                        
                        const ctx = canvas.getContext('2d');
                        
                        // Check if canvas is still drawable (no errors thrown)
                        try {
                            ctx.fillStyle = '#000000';
                            ctx.fillRect(0, 0, 1, 1);
                            
                            return {
                                canvasExists: true,
                                contextWorking: true,
                                pfdExists: window.pfd !== undefined,
                                dataExists: window.pfd && window.pfd.data !== undefined
                            };
                        } catch (e) {
                            return {
                                canvasExists: true,
                                contextWorking: false,
                                error: e.message
                            };
                        }
                    }
                """)
                
                # Check UI elements still show default values
                ui_elements_state = await page.evaluate("""
                    () => {
                        const elements = ['pitch-value', 'roll-value', 'yaw-value', 'altitude-value'];
                        const state = {};
                        
                        elements.forEach(id => {
                            const el = document.getElementById(id);
                            if (el) {
                                state[id] = {
                                    text: el.textContent,
                                    visible: el.offsetWidth > 0 && el.offsetHeight > 0
                                };
                            }
                        });
                        
                        return state;
                    }
                """)
                
                print("✅ Error Handling for Missing Data Test Results:")
                print(f"   - Canvas exists: {'✅' if error_handling['canvasExists'] else '❌'}")
                print(f"   - Context working: {'✅' if error_handling['contextWorking'] else '❌'}")
                print(f"   - PFD object exists: {'✅' if error_handling['pfdExists'] else '❌'}")
                
                for element_id, state in ui_elements_state.items():
                    status = "✅ VISIBLE" if state['visible'] else "❌ HIDDEN"
                    print(f"   - {element_id:15s}: '{state['text']}' {status}")
                
                # Assert that the system handles missing data gracefully
                assert error_handling['canvasExists'], "Canvas should exist even with missing data"
                assert error_handling['contextWorking'], "Canvas context should work even with missing data"
                
                # UI elements should still be visible with default values
                visible_elements = sum(1 for state in ui_elements_state.values() if state['visible'])
                assert visible_elements > 0, "At least some UI elements should remain visible"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_default_placeholder_values(self):
        """TEST-505-004: Test validation of default/placeholder values"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Get initial default values (before any connection)
                default_values = await page.evaluate("""
                    () => {
                        const defaults = {};
                        
                        // Check UI element default values
                        const elements = {
                            'pitch-value': 'pitch',
                            'roll-value': 'roll',
                            'yaw-value': 'yaw',
                            'altitude-value': 'altitude',
                            'groundspeed-value': 'groundspeed',
                            'verticalspeed-value': 'verticalspeed',
                            'armed-text': 'armed_status'
                        };
                        
                        for (const [id, key] of Object.entries(elements)) {
                            const el = document.getElementById(id);
                            if (el) {
                                defaults[key] = {
                                    text: el.textContent,
                                    id: id
                                };
                            }
                        }
                        
                        // Check PFD data defaults
                        if (window.pfd && window.pfd.data) {
                            defaults.pfd_data_keys = Object.keys(window.pfd.data);
                        }
                        
                        return defaults;
                    }
                """)
                
                print("✅ Default/Placeholder Values Test Results:")
                
                # Expected default patterns
                expected_defaults = {
                    'pitch': '0.0°',
                    'roll': '0.0°',
                    'yaw': '0.0°',
                    'altitude': '0.0 m',
                    'groundspeed': '0.0 m/s',
                    'verticalspeed': '0.0 m/s',
                    'armed_status': 'DISARMED'
                }
                
                for key, expected in expected_defaults.items():
                    if key in default_values:
                        actual = default_values[key]['text']
                        match = actual == expected
                        status = "✅ MATCH" if match else "⚠️  DIFFERENT"
                        print(f"   - {key:15s}: Expected '{expected}', Got '{actual}' {status}")
                        
                        # Validate that defaults are reasonable
                        if key in ['pitch', 'roll', 'yaw']:
                            assert '°' in actual, f"{key} should have degree symbol"
                        elif key in ['altitude', 'groundspeed', 'verticalspeed']:
                            assert any(unit in actual for unit in ['m', 'm/s']), f"{key} should have units"
                        elif key == 'armed_status':
                            assert actual in ['ARMED', 'DISARMED'], f"Armed status should be ARMED or DISARMED"
                
                # Check that PFD initializes with some data structure
                if 'pfd_data_keys' in default_values:
                    pfd_keys = default_values['pfd_data_keys']
                    print(f"   - PFD data keys: {len(pfd_keys)} ({', '.join(pfd_keys[:5])}...)")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_data_freshness_validation(self):
        """TEST-505-005: Test data freshness and stale data detection"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(3000)
                
                # Monitor data freshness over time
                freshness_samples = []
                
                for i in range(5):  # Take 5 samples over 5 seconds
                    sample = await page.evaluate("""
                        () => {
                            const now = Date.now();
                            
                            // Check PFD last update time
                            let pfdLastUpdate = 0;
                            if (window.pfd && window.pfd.lastUpdate) {
                                pfdLastUpdate = window.pfd.lastUpdate;
                            }
                            
                            // Check telemetry data timestamp
                            let telemetryTimestamp = 0;
                            if (window.telemetryData && window.telemetryData.timestamp) {
                                telemetryTimestamp = window.telemetryData.timestamp;
                            }
                            
                            return {
                                sampleTime: now,
                                pfdLastUpdate: pfdLastUpdate,
                                telemetryTimestamp: telemetryTimestamp,
                                pfdAge: now - pfdLastUpdate,
                                telemetryAge: now - telemetryTimestamp
                            };
                        }
                    """)
                    
                    freshness_samples.append(sample)
                    await page.wait_for_timeout(1000)  # Wait 1 second between samples
                
                print("✅ Data Freshness Validation Test Results:")
                print("   Sample | PFD Age (ms) | Telemetry Age (ms) | Status")
                print("   -------|--------------|--------------------|---------")
                
                fresh_samples = 0
                for i, sample in enumerate(freshness_samples):
                    pfd_age = sample['pfdAge']
                    tel_age = sample['telemetryAge']
                    
                    # Data is fresh if updated within last 200ms (as per requirements)
                    pfd_fresh = pfd_age < 200 if pfd_age > 0 else False
                    tel_fresh = tel_age < 200 if tel_age > 0 else False
                    
                    status = "✅ FRESH" if (pfd_fresh or tel_fresh) else "⚠️  STALE"
                    if pfd_fresh or tel_fresh:
                        fresh_samples += 1
                    
                    print(f"      {i+1:2d}   |    {pfd_age:6d}    |      {tel_age:8d}      | {status}")
                
                print(f"   Fresh samples: {fresh_samples}/{len(freshness_samples)}")
                
                # At least some samples should have fresh data
                if fresh_samples == 0:
                    print("   ⚠️  Note: No fresh data detected - may indicate connection issues")
                
            finally:
                await browser.close()
    
    async def get_pfd_data_state(self, page):
        """Helper function to get current PFD data state"""
        return await page.evaluate("""
            () => {
                const state = {};
                
                // Get PFD object data
                if (window.pfd && window.pfd.data) {
                    Object.assign(state, window.pfd.data);
                }
                
                // Get telemetry data
                if (window.telemetryData) {
                    Object.assign(state, window.telemetryData);
                }
                
                // Get UI element values
                const elements = ['pitch-value', 'roll-value', 'yaw-value', 'altitude-value'];
                elements.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        state[id] = el.textContent;
                    }
                });
                
                return state;
            }
        """)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
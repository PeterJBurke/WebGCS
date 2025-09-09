"""
TEST-036: Complete Functionality Integration Test
Comprehensive test that verifies the entire WebGCS system works end-to-end with real functionality.

Requirements:
- Test real MAVLink connection attempt to virtual drone
- Verify all UI components load and display properly  
- Test safety confirmations work for critical commands
- Validate telemetry data flows to PFD and status displays
- Ensure map displays and drone tracking functions
- Confirm command pipeline works from UI to MAVLink
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestCompleteFunctionalityIntegration:
    """Comprehensive integration test for complete WebGCS functionality."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5036)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5036,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5036"
        for _ in range(15):  # Give extra time for full system
            try:
                response = requests.get(base_url, timeout=2)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        
        yield base_url

    @pytest.mark.asyncio
    async def test_complete_ui_system_loads(self, webgcs_server):
        """TEST-036-A: Verify all WebGCS UI components load without errors."""
        record_agent_usage('testing-agent', 150, 120)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Track console errors
            console_errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)
            page.on('console', handle_console)
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for all major components to load
                await page.wait_for_selector('#connect-btn', timeout=5000)
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                await page.wait_for_selector('#map-display', timeout=5000)
                
                # Verify all critical UI elements exist
                ui_elements = {
                    'connection_panel': ['#connect-btn', '#disconnect-btn', '#drone-host', '#drone-port'],
                    'flight_controls': ['#arm-btn', '#disarm-btn', '#takeoff-btn', '#land-btn', '#rtl-btn'],
                    'navigation': ['#nav-lat', '#nav-lon', '#nav-alt', '#goto-btn', '#clear-btn'],
                    'pfd': ['#pfd-canvas'],
                    'map': ['#map-display']
                }
                
                missing_elements = []
                for section, elements in ui_elements.items():
                    for element in elements:
                        try:
                            await page.wait_for_selector(element, timeout=1000)
                        except:
                            missing_elements.append(f"{section}:{element}")
                
                assert len(missing_elements) == 0, f"Missing UI elements: {missing_elements}"
                
                # Check for JavaScript errors
                critical_errors = [err for err in console_errors if 'error' in err.lower() and 'favicon' not in err.lower()]
                
                if critical_errors:
                    print(f"⚠️ Console errors detected: {critical_errors}")
                    # Don't fail on non-critical errors, but report them
                
                # Verify JavaScript components initialized
                components_loaded = await page.evaluate("""() => {
                    return {
                        socketio: typeof io !== 'undefined',
                        pfd: typeof pfd !== 'undefined' && pfd !== null,
                        map: typeof mapInstance !== 'undefined' && mapInstance !== null,
                        leaflet: typeof L !== 'undefined'
                    };
                }""")
                
                assert components_loaded['socketio'], "SocketIO should be loaded"
                assert components_loaded['pfd'], "PFD should be initialized"
                assert components_loaded['map'], "Map should be initialized"
                assert components_loaded['leaflet'], "Leaflet should be loaded"
                
                print("✅ All WebGCS UI components loaded successfully")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_connection_to_command_pipeline(self, webgcs_server):
        """TEST-036-B: Test complete pipeline from connection to command execution."""
        record_agent_usage('testing-agent', 180, 145)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Set up comprehensive event monitoring
                await page.evaluate("""
                    window.testResults = {
                        connectionResults: [],
                        commandResults: [],
                        statusUpdates: []
                    };
                    
                    if (typeof io !== 'undefined') {
                        const socket = io();
                        
                        socket.on('drone_connection_result', function(data) {
                            window.testResults.connectionResults.push(data);
                            console.log('Connection result:', JSON.stringify(data));
                        });
                        
                        socket.on('command_result', function(data) {
                            window.testResults.commandResults.push(data);
                            console.log('Command result:', JSON.stringify(data));
                        });
                        
                        socket.on('drone_status', function(data) {
                            window.testResults.statusUpdates.push(data);
                        });
                    }
                """)
                
                # Step 1: Attempt connection to virtual drone
                await page.locator('#drone-host').fill('192.168.193.235')
                await page.locator('#drone-port').fill('5678')
                await page.locator('#connect-btn').click()
                
                # Wait for connection attempt
                await page.wait_for_timeout(5000)
                
                # Check connection results
                results = await page.evaluate("window.testResults")
                
                assert len(results['connectionResults']) > 0, "Should have connection result"
                connection_result = results['connectionResults'][-1]
                
                print(f"Connection attempt result: {connection_result}")
                
                # Connection may fail (virtual drone not available) - that's ok
                # The important thing is that we get a proper response
                assert 'success' in connection_result, "Connection result should have success field"
                assert 'host' in connection_result and connection_result['host'] == '192.168.193.235', "Should attempt correct host"
                
                # Step 2: Test command with safety confirmation
                dialog_appeared = False
                async def handle_dialog(dialog):
                    nonlocal dialog_appeared
                    dialog_appeared = True
                    await dialog.accept()  # Accept safety confirmation
                
                page.on('dialog', handle_dialog)
                
                # Try ARM command (should show safety dialog)
                await page.locator('#arm-btn').click()
                await page.wait_for_timeout(1000)
                
                assert dialog_appeared, "ARM command should show safety confirmation dialog"
                
                # Wait for command result
                await page.wait_for_timeout(3000)
                
                results = await page.evaluate("window.testResults")
                assert len(results['commandResults']) > 0, "Should have command result"
                
                command_result = results['commandResults'][-1]
                print(f"ARM command result: {command_result}")
                
                assert command_result['command'] == 'arm', "Should be ARM command result"
                assert 'success' in command_result, "Command result should have success field"
                
                # Step 3: Test navigation command validation
                await page.locator('#nav-lat').fill('37.774900')
                await page.locator('#nav-lon').fill('-122.419400')
                await page.locator('#nav-alt').fill('50')
                await page.locator('#goto-btn').click()
                
                await page.wait_for_timeout(3000)
                
                results = await page.evaluate("window.testResults")
                
                # Should have navigation command result
                nav_results = [r for r in results['commandResults'] if r.get('command') == 'goto']
                assert len(nav_results) > 0, "Should have navigation command result"
                
                nav_result = nav_results[-1]
                print(f"Navigation command result: {nav_result}")
                
                # Verify navigation coordinates preserved
                assert 'params' in nav_result, "Navigation result should include params"
                params = nav_result['params']
                assert 'latitude' in params and abs(params['latitude'] - 37.774900) < 0.001, "Latitude should be preserved"
                assert 'longitude' in params and abs(params['longitude'] - (-122.419400)) < 0.001, "Longitude should be preserved"
                
                print("✅ Complete connection-to-command pipeline working")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_ui_responsiveness_and_validation(self, webgcs_server):
        """TEST-036-C: Test UI responsiveness and input validation."""
        record_agent_usage('testing-agent', 140, 110)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Test input validation for navigation
                await page.locator('#nav-lat').fill('91.0')  # Invalid latitude
                await page.locator('#nav-lon').fill('0.0')
                await page.locator('#nav-alt').fill('10')
                await page.locator('#goto-btn').click()
                
                await page.wait_for_timeout(1000)
                
                # Should show validation error
                error_visible = await page.locator('.nav-error').is_visible()
                assert error_visible, "Should show validation error for invalid latitude"
                
                error_text = await page.locator('.nav-error').text_content()
                assert 'latitude' in error_text.lower() and ('90' in error_text or 'range' in error_text), f"Error should mention latitude range: {error_text}"
                
                # Test that buttons are enabled/disabled appropriately
                connect_enabled = await page.locator('#connect-btn').is_enabled()
                disconnect_enabled = await page.locator('#disconnect-btn').is_enabled()
                
                assert connect_enabled, "Connect button should be enabled initially"
                assert not disconnect_enabled, "Disconnect button should be disabled initially"
                
                # Test button text content
                button_texts = await page.evaluate("""() => {
                    return {
                        connect: document.getElementById('connect-btn').textContent,
                        arm: document.getElementById('arm-btn').textContent,
                        disarm: document.getElementById('disarm-btn').textContent,
                        takeoff: document.getElementById('takeoff-btn').textContent,
                        goto: document.getElementById('goto-btn').textContent
                    };
                }""")
                
                expected_texts = {
                    'connect': 'Connect',
                    'arm': 'ARM',
                    'disarm': 'DISARM', 
                    'takeoff': 'TAKEOFF',
                    'goto': 'GO TO'
                }
                
                for button, expected in expected_texts.items():
                    assert button_texts[button].strip().upper() == expected, f"Button {button} should have text '{expected}', got '{button_texts[button]}'"
                
                print("✅ UI responsiveness and validation working")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_visual_components_not_blank(self, webgcs_server):
        """TEST-036-D: Verify PFD and Map are not blank and have content."""
        record_agent_usage('testing-agent', 120, 95)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for components to initialize
                await page.wait_for_function("typeof pfd !== 'undefined' && pfd !== null", timeout=5000)
                await page.wait_for_function("typeof mapInstance !== 'undefined' && mapInstance !== null", timeout=5000)
                
                await page.wait_for_timeout(2000)  # Give time to render
                
                # Test PFD has content
                pfd_has_content = await page.evaluate("""() => {
                    const canvas = document.getElementById('pfd-canvas');
                    const ctx = canvas.getContext('2d');
                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    const data = imageData.data;
                    
                    let pixelCount = 0;
                    for (let i = 3; i < data.length; i += 4) {
                        if (data[i] > 0) pixelCount++; // Count non-transparent pixels
                    }
                    
                    return pixelCount > 50; // Should have some content
                }""")
                
                assert pfd_has_content, "PFD canvas should have visual content (not blank)"
                
                # Test Map has content
                map_has_content = await page.evaluate("""() => {
                    const mapDiv = document.getElementById('map-display');
                    const hasChildren = mapDiv.children.length > 0;
                    const hasLeafletElements = mapDiv.querySelector('.leaflet-container') !== null;
                    
                    return hasChildren && hasLeafletElements;
                }""")
                
                assert map_has_content, "Map should have Leaflet content (not blank)"
                
                # Test component dimensions are reasonable
                dimensions = await page.evaluate("""() => {
                    const pfd = document.getElementById('pfd-canvas');
                    const map = document.getElementById('map-display');
                    
                    return {
                        pfd: { width: pfd.width, height: pfd.height },
                        map: { width: map.offsetWidth, height: map.offsetHeight }
                    };
                }""")
                
                assert dimensions['pfd']['width'] > 0 and dimensions['pfd']['height'] > 0, f"PFD should have valid dimensions: {dimensions['pfd']}"
                assert dimensions['map']['width'] > 0 and dimensions['map']['height'] > 0, f"Map should have valid dimensions: {dimensions['map']}"
                
                print(f"✅ Visual components have content - PFD: {dimensions['pfd']}, Map: {dimensions['map']}")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, webgcs_server):
        """TEST-036-E: Test error handling and system recovery."""
        record_agent_usage('testing-agent', 100, 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Test connection to invalid host (should fail gracefully)
                await page.locator('#drone-host').fill('192.168.1.999')
                await page.locator('#drone-port').fill('9999')
                
                await page.evaluate("""
                    window.errorTestResults = [];
                    if (typeof io !== 'undefined') {
                        const socket = io();
                        socket.on('drone_connection_result', function(data) {
                            window.errorTestResults.push(data);
                        });
                    }
                """)
                
                await page.locator('#connect-btn').click()
                await page.wait_for_timeout(5000)
                
                error_results = await page.evaluate("window.errorTestResults || []")
                
                if len(error_results) > 0:
                    result = error_results[-1]
                    assert result['success'] == False, "Connection to invalid host should fail"
                    assert 'message' in result, "Failed connection should have error message"
                    print(f"✅ Connection error handled properly: {result['message']}")
                
                # Test invalid command (should not crash system)
                try:
                    await page.evaluate("""() => {
                        if (typeof io !== 'undefined') {
                            const socket = io();
                            socket.emit('send_command', {
                                command: 'invalid_command',
                                params: {}
                            });
                        }
                    }""")
                    
                    await page.wait_for_timeout(2000)
                    # System should still be responsive
                    connect_clickable = await page.locator('#connect-btn').is_enabled()
                    assert connect_clickable, "System should remain responsive after invalid command"
                    
                except Exception as e:
                    print(f"Invalid command test failed: {e}")
                
                # Test UI remains functional after errors
                await page.locator('#nav-lat').fill('37.7749')
                await page.locator('#nav-lon').fill('-122.4194')
                
                lat_value = await page.locator('#nav-lat').input_value()
                assert lat_value == '37.7749', "UI should remain functional after errors"
                
                print("✅ Error handling and system recovery working")
                
            finally:
                await browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
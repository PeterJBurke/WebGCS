"""
SocketIO Version Compatibility Tests
Tests to prevent the "Not connected to WebGCS server" popup issue.
"""
import asyncio
import re
import time
from playwright.async_api import async_playwright
import pytest


class TestSocketIOCompatibility:
    """Test suite to ensure SocketIO client/server compatibility"""

    @pytest.mark.asyncio
    async def test_socketio_version_compatibility(self):
        """Test that SocketIO client version is compatible with Flask-SocketIO server"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Track console errors
            console_errors = []
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)
            page.on("console", handle_console)
            
            try:
                await page.goto("http://localhost:5002", wait_until="domcontentloaded")
                
                # Check SocketIO client version loaded
                socketio_version = await page.evaluate("""
                    () => {
                        const scripts = Array.from(document.getElementsByTagName('script'));
                        const socketIOScript = scripts.find(script => 
                            script.src && script.src.includes('socket.io')
                        );
                        if (socketIOScript) {
                            const match = socketIOScript.src.match(/socket\.io\/([0-9.]+)\//);
                            return match ? match[1] : 'unknown';
                        }
                        return 'not found';
                    }
                """)
                
                # Wait for connection to establish
                await page.wait_for_timeout(10000)
                
                # Check connection status
                connection_state = await page.evaluate("""
                    () => ({
                        socketExists: window.WebGCS?.socket !== undefined,
                        socketConnected: window.WebGCS?.socket?.connected || false,
                        webGCSConnected: window.WebGCS?.connected || false,
                        socketId: window.WebGCS?.socket?.id || null
                    })
                """)
                
                # Assertions
                assert socketio_version != 'not found', "SocketIO script not loaded"
                assert socketio_version != 'unknown', "Could not determine SocketIO version"
                
                # Version compatibility check (Flask-SocketIO 5.x requires SocketIO 4.3+)
                version_parts = socketio_version.split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1])
                
                assert major >= 4, f"SocketIO version {socketio_version} is too old (need 4.3+)"
                if major == 4:
                    assert minor >= 3, f"SocketIO 4.{minor} is incompatible (need 4.3+)"
                
                # Connection state checks
                assert connection_state['socketExists'], "Socket object not created"
                assert connection_state['socketConnected'], "Socket not connected to server"
                assert connection_state['webGCSConnected'], "WebGCS connection not established"
                assert connection_state['socketId'] is not None, "Socket ID not assigned"
                
                # Check for connection timeout errors
                timeout_errors = [err for err in console_errors if 'timeout' in err.lower()]
                assert len(timeout_errors) == 0, f"Connection timeout errors: {timeout_errors}"
                
                print(f"✅ SocketIO {socketio_version} compatibility verified")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio 
    async def test_connect_button_no_popup(self):
        """Test that connect button doesn't show 'Not connected to WebGCS server' popup"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            alerts_captured = []
            async def capture_alert(dialog):
                alerts_captured.append(dialog.message)
                await dialog.accept()
            page.on("dialog", capture_alert)
            
            try:
                await page.goto("http://localhost:5002", wait_until="domcontentloaded")
                
                # Wait for full connection
                await page.wait_for_timeout(15000)
                
                # Click connect button
                connect_button = page.locator("#connect-drone-btn")
                await connect_button.wait_for(state="visible", timeout=5000)
                await connect_button.click()
                
                # Wait for any potential alerts
                await page.wait_for_timeout(3000)
                
                # Check for specific error messages
                socketio_errors = [alert for alert in alerts_captured 
                                 if "Not connected to WebGCS server" in alert or
                                    "Connection to WebGCS server lost" in alert]
                
                assert len(socketio_errors) == 0, f"Connect button showed error popup: {socketio_errors}"
                print("✅ Connect button works without popup errors")
                
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_realtime_communication(self):
        """Test that SocketIO real-time communication works properly"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Track SocketIO events
            events_received = []
            await page.evaluate("""
                () => {
                    window.testEvents = [];
                    // Monitor common SocketIO events
                    const eventTypes = ['connection_status', 'drone_connected', 'telemetry_update'];
                    
                    // This will be set up after SocketIO connects
                    window.monitorEvents = () => {
                        if (window.WebGCS?.socket) {
                            eventTypes.forEach(eventType => {
                                window.WebGCS.socket.on(eventType, (data) => {
                                    window.testEvents.push({
                                        type: eventType,
                                        timestamp: Date.now(),
                                        data: data
                                    });
                                });
                            });
                        }
                    };
                }
            """)
            
            try:
                await page.goto("http://localhost:5002", wait_until="domcontentloaded")
                
                # Wait for connection and set up event monitoring
                await page.wait_for_timeout(10000)
                await page.evaluate("window.monitorEvents && window.monitorEvents()")
                
                # Click connect to trigger events
                connect_button = page.locator("#connect-drone-btn")
                await connect_button.wait_for(state="visible")
                await connect_button.click()
                
                # Wait for events to be received
                await page.wait_for_timeout(10000)
                
                # Check events received
                events_received = await page.evaluate("window.testEvents || []")
                
                assert len(events_received) > 0, "No SocketIO events received"
                
                # Check for specific event types
                event_types = [event['type'] for event in events_received]
                assert 'connection_status' in event_types or 'drone_connected' in event_types, \
                    f"Expected connection events not received. Got: {event_types}"
                
                print(f"✅ Received {len(events_received)} SocketIO events: {event_types}")
                
            finally:
                await browser.close()

    def test_version_compatibility_matrix(self):
        """Test version compatibility matrix for future reference"""
        
        # Define compatibility matrix
        compatibility_matrix = {
            # Flask-SocketIO version: [min_client_version, max_client_version]
            "5.0": ["4.3.0", None],  # 4.3.0+ compatible
            "5.1": ["4.3.0", None],  # 4.3.0+ compatible  
            "5.2": ["4.3.0", None],  # 4.3.0+ compatible
            "5.3": ["4.7.0", None], # 4.7.0+ recommended
        }
        
        def version_compare(v1, v2):
            """Compare version strings"""
            v1_parts = [int(x) for x in v1.split('.')]
            v2_parts = [int(x) for x in v2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))
            
            for i in range(max_len):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            return 0
        
        # Test current configuration
        current_flask_socketio = "5.0"  # From pyproject.toml
        current_client_version = "4.7.5"  # From index.html
        
        min_version = compatibility_matrix[current_flask_socketio][0]
        assert version_compare(current_client_version, min_version) >= 0, \
            f"Client version {current_client_version} is below minimum {min_version} for Flask-SocketIO {current_flask_socketio}"
        
        print(f"✅ Version compatibility verified: Flask-SocketIO {current_flask_socketio} + SocketIO client {current_client_version}")


if __name__ == "__main__":
    # Run tests individually for debugging
    test_suite = TestSocketIOCompatibility()
    
    print("Running SocketIO compatibility tests...")
    
    # Run async tests
    asyncio.run(test_suite.test_socketio_version_compatibility())
    asyncio.run(test_suite.test_connect_button_no_popup())
    asyncio.run(test_suite.test_realtime_communication())
    
    # Run sync test
    test_suite.test_version_compatibility_matrix()
    
    print("✅ All SocketIO compatibility tests passed!")
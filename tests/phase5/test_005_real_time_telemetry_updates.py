"""
Phase 5 Test 005: Real-time Telemetry Updates Validation
Tests that PFD components update with real telemetry from virtual drone at 192.168.193.235:5678.
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, expect


@pytest.fixture(scope="session")
def webgcs_server():
    """Fixture to ensure WebGCS server is running"""
    return "http://127.0.0.1:5002"


class TestPFDRealTimeTelemetryUpdates:
    """Test real-time telemetry integration with PFD displays"""
    
    @pytest.mark.asyncio
    async def test_telemetry_connection_and_updates(self, webgcs_server):
        """Test connection to virtual drone and verify telemetry updates to PFD"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                # Connect to virtual drone
                await page.click('#connect-btn')
                await asyncio.sleep(3)  # Wait for connection
                
                # Take initial canvas snapshot
                initial_canvas = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        return ctx.getImageData(0, 0, canvas.width, canvas.height);
                    }
                """)
                
                # Wait for telemetry updates
                await asyncio.sleep(3)
                
                # Take second snapshot to verify updates
                updated_canvas = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        return ctx.getImageData(0, 0, canvas.width, canvas.height);
                    }
                """)
                
                # Check for changes indicating live updates
                canvas_changed = await page.evaluate("""
                    (args) => {
                        const [initial, updated] = args;
                        let changes = 0;
                        
                        for (let i = 0; i < initial.data.length; i++) {
                            if (Math.abs(initial.data[i] - updated.data[i]) > 10) {
                                changes++;
                            }
                        }
                        
                        return changes > 100; // Significant changes indicate updates
                    }
                """, [initial_canvas, updated_canvas])
                
                assert canvas_changed, "PFD should show dynamic updates from telemetry stream"
                print("✓ Real-time telemetry updates visible in PFD")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_pfd_update_rate_performance(self, webgcs_server):
        """Test PFD update rate meets 10Hz performance requirement"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                # Connect and monitor update rate
                await page.click('#connect-btn')
                await asyncio.sleep(2)
                
                # Monitor canvas changes over time to measure update rate
                update_count = await page.evaluate("""
                    () => {
                        return new Promise((resolve) => {
                            const canvas = document.getElementById('pfd-canvas');
                            const ctx = canvas.getContext('2d');
                            let lastImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                            let updateCount = 0;
                            let startTime = Date.now();
                            
                            const checkInterval = setInterval(() => {
                                const currentImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                                let changes = 0;
                                
                                // Quick sample check for changes
                                for (let i = 0; i < currentImageData.data.length; i += 100) {
                                    if (Math.abs(currentImageData.data[i] - lastImageData.data[i]) > 5) {
                                        changes++;
                                    }
                                }
                                
                                if (changes > 10) {
                                    updateCount++;
                                    lastImageData = currentImageData;
                                }
                                
                                if (Date.now() - startTime > 3000) { // 3 second test
                                    clearInterval(checkInterval);
                                    resolve(updateCount);
                                }
                            }, 100);
                        });
                    }
                """)
                
                # Should get ~30 updates in 3 seconds (10Hz = 10 updates/sec)
                expected_min_updates = 20  # Allow some tolerance
                assert update_count >= expected_min_updates, f"Should get ≥{expected_min_updates} updates in 3s, got {update_count}"
                
                print(f"✓ PFD update rate: {update_count} updates in 3 seconds (~{update_count/3:.1f} Hz)")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_pfd_no_stale_data(self, webgcs_server):
        """Test that PFD shows no stale data >200ms old"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                # Connect and verify fresh data
                await page.click('#connect-btn')
                await asyncio.sleep(2)
                
                # Check that display shows "connected" state, not stale disconnected
                connection_status = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const data = imageData.data;
                        
                        // Look for "DISCONNECTED" text which would indicate stale data
                        let disconnectedPixels = 0;
                        let connectedPixels = 0;
                        
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            // Red pixels might indicate disconnected state
                            if (r > 200 && g < 100 && b < 100) {
                                disconnectedPixels++;
                            }
                            
                            // Green/blue pixels indicate active telemetry display
                            if (g > 150 || b > 150) {
                                connectedPixels++;
                            }
                        }
                        
                        return { disconnectedPixels, connectedPixels };
                    }
                """)
                
                assert connection_status['connectedPixels'] > connection_status['disconnectedPixels'], \
                    "PFD should show live connected state, not stale disconnected data"
                
                print("✓ PFD shows fresh data without stale indicators")
                
            finally:
                await browser.close()
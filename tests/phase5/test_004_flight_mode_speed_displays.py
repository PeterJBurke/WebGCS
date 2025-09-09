"""
Phase 5 Test 004: Flight Mode and Speed Displays Validation  
Tests flight mode display and airspeed/groundspeed readouts.
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, expect


@pytest.fixture(scope="session")
def webgcs_server():
    """Fixture to ensure WebGCS server is running"""
    return "http://127.0.0.1:5002"


class TestPFDFlightModeSpeedDisplays:
    """Test flight mode and speed display components"""
    
    @pytest.mark.asyncio
    async def test_flight_mode_display(self, webgcs_server):
        """Test flight mode display (#14) visibility"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Flight mode is typically displayed near top or with other status info
                # Check for mode text in upper area
                mode_display = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        
                        // Check multiple areas where flight mode might be displayed
                        let totalModePixels = 0;
                        
                        // Top left area
                        const topLeft = ctx.getImageData(10, 10, 150, 30);
                        // Top center area  
                        const topCenter = ctx.getImageData(canvas.width/2 - 75, 70, 150, 30);
                        // Status area
                        const statusArea = ctx.getImageData(10, 100, 200, 30);
                        
                        const areas = [topLeft, topCenter, statusArea];
                        
                        for (let area of areas) {
                            const data = area.data;
                            for (let i = 0; i < data.length; i += 4) {
                                const r = data[i];
                                const g = data[i + 1];  
                                const b = data[i + 2];
                                
                                // Look for text pixels
                                if (r > 150 || g > 150 || b > 150) {
                                    totalModePixels++;
                                }
                            }
                        }
                        
                        return totalModePixels;
                    }
                """)
                
                assert mode_display > 20, f"Should show flight mode display, got {mode_display} mode pixels"
                print("✓ Flight mode display visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_airspeed_groundspeed_readouts(self, webgcs_server):
        """Test airspeed/groundspeed readouts (#15) at bottom left"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for GS (groundspeed) display at bottom left
                speed_display = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(10, canvas.height - 40, 150, 25);
                        const data = imageData.data;
                        
                        let speedPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 150 || g > 150 || b > 150) {
                                speedPixels++;
                            }
                        }
                        
                        return speedPixels;
                    }
                """)
                
                assert speed_display > 10, f"Should show speed readouts, got {speed_display} speed pixels"
                print("✓ Airspeed/groundspeed readouts visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_aircraft_reference_symbol(self, webgcs_server):
        """Test aircraft reference symbol (#9) at center of artificial horizon"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for aircraft symbol at center
                aircraft_symbol = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const centerX = canvas.width / 2;
                        const centerY = canvas.height / 2;
                        
                        // Check center area for aircraft reference symbol
                        const imageData = ctx.getImageData(centerX - 30, centerY - 15, 60, 30);
                        const data = imageData.data;
                        
                        let symbolPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            // Look for white/yellow aircraft symbol
                            if ((r > 200 && g > 200 && b > 200) || (r > 200 && g > 200 && b < 100)) {
                                symbolPixels++;
                            }
                        }
                        
                        return symbolPixels;
                    }
                """)
                
                assert aircraft_symbol > 10, f"Should show aircraft reference symbol, got {aircraft_symbol} symbol pixels"
                print("✓ Aircraft reference symbol visible")
                
            finally:
                await browser.close()
"""
Phase 5 Test 002: Status Indicators Validation
Tests armed status, battery, GPS, and telemetry link indicators.
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, expect


@pytest.fixture(scope="session")
def webgcs_server():
    """Fixture to ensure WebGCS server is running"""
    return "http://127.0.0.1:5002"


class TestPFDStatusIndicators:
    """Test PFD status indicators for proper rendering and updates"""
    
    @pytest.mark.asyncio
    async def test_armed_status_display(self, webgcs_server):
        """Test armed/disarmed status overlay (#10) visibility"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for ARMED/DISARMED text in top center
                armed_status = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(canvas.width/2 - 60, 10, 120, 40);
                        const data = imageData.data;
                        
                        let textPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            // Look for white/green text pixels
                            if ((r > 200 && g > 200 && b > 200) || (g > 150 && r < 100 && b < 100)) {
                                textPixels++;
                            }
                        }
                        
                        return textPixels;
                    }
                """)
                
                assert armed_status > 10, f"Should show ARMED/DISARMED text, got {armed_status} text pixels"
                print("✓ Armed status overlay visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_battery_status_display(self, webgcs_server):
        """Test battery status with color coding display"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for battery text in bottom left
                battery_status = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(10, canvas.height - 80, 200, 30);
                        const data = imageData.data;
                        
                        let textPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            // Look for text pixels (white, green, or red)
                            if (r > 150 || g > 150 || (r > 150 && g < 100 && b < 100)) {
                                textPixels++;
                            }
                        }
                        
                        return textPixels;
                    }
                """)
                
                assert battery_status > 10, f"Should show battery status, got {battery_status} text pixels"
                print("✓ Battery status display visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_gps_status_display(self, webgcs_server):
        """Test GPS fix status and satellite count display"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for GPS text in bottom left
                gps_status = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(10, canvas.height - 60, 150, 25);
                        const data = imageData.data;
                        
                        let textPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 150 || g > 150 || b > 150) {
                                textPixels++;
                            }
                        }
                        
                        return textPixels;
                    }
                """)
                
                assert gps_status > 10, f"Should show GPS status, got {gps_status} text pixels"
                print("✓ GPS status display visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_telemetry_link_quality(self, webgcs_server):
        """Test telemetry link quality indicator (#5) in top right"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for LINK text in top right
                link_status = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(canvas.width - 80, 10, 70, 40);
                        const data = imageData.data;
                        
                        let textPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 150 || g > 150 || b > 150) {
                                textPixels++;
                            }
                        }
                        
                        return textPixels;
                    }
                """)
                
                assert link_status > 10, f"Should show telemetry link status, got {link_status} text pixels"
                print("✓ Telemetry link quality indicator visible")
                
            finally:
                await browser.close()
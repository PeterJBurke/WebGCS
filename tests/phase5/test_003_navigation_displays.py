"""
Phase 5 Test 003: Navigation Displays Validation
Tests heading compass, bank angle, GPS time, and navigation indicators.
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, expect


@pytest.fixture(scope="session")
def webgcs_server():
    """Fixture to ensure WebGCS server is running"""
    return "http://127.0.0.1:5002"


class TestPFDNavigationDisplays:
    """Test PFD navigation and time displays"""
    
    @pytest.mark.asyncio
    async def test_bank_angle_indicator(self, webgcs_server):
        """Test bank angle indicator arc (±60°) (#4) at top center"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for bank angle arc at top center
                bank_arc_data = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const centerX = canvas.width / 2;
                        const checkY = canvas.height / 2 - 100;
                        
                        // Sample arc area for white lines
                        const imageData = ctx.getImageData(centerX - 100, checkY - 20, 200, 40);
                        const data = imageData.data;
                        
                        let arcPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            // Look for white arc lines
                            if (r > 200 && g > 200 && b > 200) {
                                arcPixels++;
                            }
                        }
                        
                        return arcPixels;
                    }
                """)
                
                assert bank_arc_data > 20, f"Should show bank angle arc, got {bank_arc_data} arc pixels"
                print("✓ Bank angle indicator arc visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_gps_time_display(self, webgcs_server):
        """Test GPS time display (UTC) (#6) in top right"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for UTC time in top right
                utc_display = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(canvas.width - 140, 40, 120, 25);
                        const data = imageData.data;
                        
                        let timePixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 150 || g > 150 || b > 150) {
                                timePixels++;
                            }
                        }
                        
                        return timePixels;
                    }
                """)
                
                assert utc_display > 10, f"Should show GPS UTC time, got {utc_display} time pixels"
                print("✓ GPS UTC time display visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_crosstrack_turn_rate_display(self, webgcs_server):
        """Test crosstrack error & turn rate (#2) display at top center"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for XTK display in top center area
                xtk_display = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(canvas.width/2 + 40, 40, 100, 25);
                        const data = imageData.data;
                        
                        let xtkPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 150 || g > 150 || b > 150) {
                                xtkPixels++;
                            }
                        }
                        
                        return xtkPixels;
                    }
                """)
                
                assert xtk_display > 5, f"Should show crosstrack error, got {xtk_display} XTK pixels"
                print("✓ Crosstrack error display visible")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_distance_waypoint_display(self, webgcs_server):
        """Test distance to waypoint (#13) display at bottom right"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for waypoint distance in bottom right
                wp_display = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(canvas.width - 100, canvas.height - 40, 80, 25);
                        const data = imageData.data;
                        
                        let wpPixels = 0;
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 150 || g > 150 || b > 150) {
                                wpPixels++;
                            }
                        }
                        
                        return wpPixels;
                    }
                """)
                
                assert wp_display > 5, f"Should show waypoint distance, got {wp_display} WP pixels"
                print("✓ Distance to waypoint display visible")
                
            finally:
                await browser.close()
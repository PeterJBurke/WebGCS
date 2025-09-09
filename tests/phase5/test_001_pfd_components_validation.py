"""
Phase 5 Test 001: PFD Core Components Validation
Tests the 15 required VFR HUD components for proper rendering and visibility.
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, expect
import time


@pytest.fixture(scope="session")
def webgcs_server():
    """Fixture to ensure WebGCS server is running"""
    # Assume server is already running at http://127.0.0.1:5002
    return "http://127.0.0.1:5002"


class TestPFDCoreComponents:
    """Test core PFD VFR HUD components for proper rendering"""
    
    @pytest.mark.asyncio
    async def test_pfd_canvas_exists_and_initializes(self, webgcs_server):
        """Test that PFD canvas element exists and initializes properly"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Wait for PFD canvas
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                pfd_canvas = page.locator('#pfd-canvas')
                
                # Verify canvas exists and is visible
                await expect(pfd_canvas).to_be_visible()
                
                # Check canvas dimensions (800x600)
                canvas_width = await pfd_canvas.evaluate('el => el.width')
                canvas_height = await pfd_canvas.evaluate('el => el.height')
                
                assert canvas_width == 800, f"Canvas width should be 800px, got {canvas_width}"
                assert canvas_height == 600, f"Canvas height should be 600px, got {canvas_height}"
                
                print("✓ PFD Canvas initialized with correct dimensions")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_artificial_horizon_rendering(self, webgcs_server):
        """Test artificial horizon (component #8) renders properly"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                # Wait for PFD to render
                await asyncio.sleep(2)
                
                # Check for horizon rendering (blue sky, brown ground colors)
                horizon_data = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const data = imageData.data;
                        
                        let bluePixels = 0;
                        let brownPixels = 0;
                        
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            // Blue sky detection (more blue than red/green)
                            if (b > r + 20 && b > g + 20 && b > 100) {
                                bluePixels++;
                            }
                            
                            // Brown ground detection (more red/green, less blue)
                            if (r > 50 && g > 30 && b < 30 && r > b + 20) {
                                brownPixels++;
                            }
                        }
                        
                        return { bluePixels, brownPixels };
                    }
                """)
                
                assert horizon_data['bluePixels'] > 100, f"Should have blue sky pixels, got {horizon_data['bluePixels']}"
                assert horizon_data['brownPixels'] > 100, f"Should have brown ground pixels, got {horizon_data['brownPixels']}"
                
                print("✓ Artificial horizon rendering with sky/ground colors")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_airspeed_altitude_tapes(self, webgcs_server):
        """Test airspeed tape (left, #1) and altitude tape (right, #7) rendering"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                await asyncio.sleep(2)
                
                # Check for tape indicators on left and right edges
                tape_data = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const data = imageData.data;
                        
                        let leftEdgePixels = 0;
                        let rightEdgePixels = 0;
                        
                        // Check left edge (airspeed tape)
                        for (let y = 100; y < canvas.height - 100; y += 10) {
                            for (let x = 0; x < 80; x += 5) {
                                const idx = (y * canvas.width + x) * 4;
                                const r = data[idx];
                                const g = data[idx + 1];
                                const b = data[idx + 2];
                                
                                // Non-black pixels indicate content
                                if (r > 10 || g > 10 || b > 10) {
                                    leftEdgePixels++;
                                }
                            }
                        }
                        
                        // Check right edge (altitude tape)
                        for (let y = 100; y < canvas.height - 100; y += 10) {
                            for (let x = canvas.width - 80; x < canvas.width; x += 5) {
                                const idx = (y * canvas.width + x) * 4;
                                const r = data[idx];
                                const g = data[idx + 1];
                                const b = data[idx + 2];
                                
                                if (r > 10 || g > 10 || b > 10) {
                                    rightEdgePixels++;
                                }
                            }
                        }
                        
                        return { leftEdgePixels, rightEdgePixels };
                    }
                """)
                
                assert tape_data['leftEdgePixels'] > 20, f"Should have airspeed tape content, got {tape_data['leftEdgePixels']} pixels"
                assert tape_data['rightEdgePixels'] > 20, f"Should have altitude tape content, got {tape_data['rightEdgePixels']} pixels"
                
                print("✓ Airspeed and altitude tapes rendering")
                
            finally:
                await browser.close()
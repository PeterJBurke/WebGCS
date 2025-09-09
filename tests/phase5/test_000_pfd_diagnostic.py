"""
Diagnostic test to understand what's being rendered on PFD canvas
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, expect


@pytest.fixture(scope="session")
def webgcs_server():
    """Fixture to ensure WebGCS server is running"""
    return "http://127.0.0.1:5002"


class TestPFDDiagnostic:
    """Diagnostic tests to understand PFD rendering"""
    
    @pytest.mark.asyncio
    async def test_pfd_canvas_diagnostic(self, webgcs_server):
        """Diagnostic test to see what's being rendered"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                # Wait for any JavaScript initialization
                await asyncio.sleep(3)
                
                # Get canvas content analysis
                canvas_analysis = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        if (!canvas) return { error: "Canvas not found" };
                        
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const data = imageData.data;
                        
                        let totalPixels = data.length / 4;
                        let nonBlackPixels = 0;
                        let colorBreakdown = { black: 0, white: 0, red: 0, green: 0, blue: 0, other: 0 };
                        
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 10 || g > 10 || b > 10) {
                                nonBlackPixels++;
                                
                                // Categorize colors
                                if (r > 200 && g > 200 && b > 200) colorBreakdown.white++;
                                else if (r > 150 && g < 100 && b < 100) colorBreakdown.red++;
                                else if (g > 150 && r < 100 && b < 100) colorBreakdown.green++;
                                else if (b > 150 && r < 100 && g < 100) colorBreakdown.blue++;
                                else colorBreakdown.other++;
                            } else {
                                colorBreakdown.black++;
                            }
                        }
                        
                        return {
                            canvasSize: `${canvas.width}x${canvas.height}`,
                            totalPixels,
                            nonBlackPixels,
                            contentDensity: (nonBlackPixels / totalPixels * 100).toFixed(2),
                            colorBreakdown,
                            pfdExists: !!window.pfd,
                            pfdConstructor: typeof PrimaryFlightDisplay !== 'undefined'
                        };
                    }
                """)
                
                print(f"🔍 PFD Canvas Diagnostic Results:")
                print(f"   Canvas Size: {canvas_analysis['canvasSize']}")
                print(f"   Total Pixels: {canvas_analysis['totalPixels']:,}")
                print(f"   Non-black Pixels: {canvas_analysis['nonBlackPixels']:,}")
                print(f"   Content Density: {canvas_analysis['contentDensity']}%")
                print(f"   PFD Instance Exists: {canvas_analysis['pfdExists']}")
                print(f"   PFD Constructor Available: {canvas_analysis['pfdConstructor']}")
                print(f"   Color Breakdown:")
                for color, count in canvas_analysis['colorBreakdown'].items():
                    if count > 0:
                        print(f"     {color}: {count:,} pixels")
                
                # Check if PFD methods are being called
                pfd_methods = await page.evaluate("""
                    () => {
                        if (!window.pfd) return { error: "No PFD instance" };
                        
                        return {
                            hasUpdate: typeof window.pfd.update === 'function',
                            hasRender: typeof window.pfd.render === 'function',
                            hasDrawArtificialHorizon: typeof window.pfd.drawArtificialHorizon === 'function',
                            telemetryData: window.pfd.telemetry || null,
                            lastUpdate: window.pfd.lastUpdate || null
                        };
                    }
                """)
                
                print(f"   PFD Methods Available:")
                if 'error' in pfd_methods:
                    print(f"     {pfd_methods['error']}")
                else:
                    for method, available in pfd_methods.items():
                        print(f"     {method}: {available}")
                
                # Test manual PFD render call
                render_result = await page.evaluate("""
                    () => {
                        if (!window.pfd) return "No PFD instance";
                        
                        try {
                            window.pfd.render();
                            return "Render called successfully";
                        } catch (e) {
                            return `Render failed: ${e.message}`;
                        }
                    }
                """)
                
                print(f"   Manual Render Test: {render_result}")
                
                # Basic assertion - canvas should exist and have some basic properties
                assert canvas_analysis['canvasSize'] == '800x600', "Canvas should be 800x600"
                assert canvas_analysis['totalPixels'] == 800 * 600, "Total pixel count should match canvas size"
                
                print("✅ PFD diagnostic completed")
                
            finally:
                await browser.close()
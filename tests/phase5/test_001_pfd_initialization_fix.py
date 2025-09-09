"""
Test to force PFD initialization and validate rendering
"""
import pytest
import asyncio
from playwright.async_api import async_playwright, expect


@pytest.fixture(scope="session")
def webgcs_server():
    """Fixture to ensure WebGCS server is running"""
    return "http://127.0.0.1:5002"


class TestPFDInitializationFix:
    """Test PFD initialization and force rendering"""
    
    @pytest.mark.asyncio
    async def test_force_pfd_initialization(self, webgcs_server):
        """Force PFD initialization and test rendering"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                # Force PFD initialization
                init_result = await page.evaluate("""
                    () => {
                        try {
                            // Check if canvas exists
                            const canvas = document.getElementById('pfd-canvas');
                            if (!canvas) return { error: "Canvas not found" };
                            
                            // Check if PFD constructor exists
                            if (typeof PrimaryFlightDisplay === 'undefined') {
                                return { error: "PrimaryFlightDisplay constructor not available" };
                            }
                            
                            // Force create PFD instance
                            window.pfd = new PrimaryFlightDisplay('pfd-canvas');
                            
                            // Call render immediately
                            window.pfd.render();
                            
                            return { 
                                success: true, 
                                pfdCreated: !!window.pfd,
                                canvasWidth: canvas.width,
                                canvasHeight: canvas.height
                            };
                        } catch (e) {
                            return { error: e.message, stack: e.stack };
                        }
                    }
                """)
                
                print(f"🔧 Force PFD Initialization Result: {init_result}")
                
                if 'error' in init_result:
                    pytest.fail(f"PFD initialization failed: {init_result['error']}")
                
                # Wait a moment for rendering
                await asyncio.sleep(2)
                
                # Check content after forced initialization
                content_analysis = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const data = imageData.data;
                        
                        let totalPixels = data.length / 4;
                        let nonBlackPixels = 0;
                        let redPixels = 0;
                        let whitePixels = 0;
                        let bluePixels = 0;
                        
                        for (let i = 0; i < data.length; i += 4) {
                            const r = data[i];
                            const g = data[i + 1];
                            const b = data[i + 2];
                            
                            if (r > 10 || g > 10 || b > 10) {
                                nonBlackPixels++;
                                
                                if (r > 150 && g < 100 && b < 100) redPixels++;
                                if (r > 200 && g > 200 && b > 200) whitePixels++;  
                                if (b > r + 30 && b > g + 30) bluePixels++;
                            }
                        }
                        
                        return {
                            totalPixels,
                            nonBlackPixels,
                            contentDensity: (nonBlackPixels / totalPixels * 100).toFixed(2),
                            redPixels,
                            whitePixels,
                            bluePixels
                        };
                    }
                """)
                
                print(f"📊 Content Analysis After Forced Init:")
                print(f"   Non-black pixels: {content_analysis['nonBlackPixels']:,}")
                print(f"   Content density: {content_analysis['contentDensity']}%")
                print(f"   Red pixels: {content_analysis['redPixels']:,}")
                print(f"   White pixels: {content_analysis['whitePixels']:,}")
                print(f"   Blue pixels: {content_analysis['bluePixels']:,}")
                
                # Assertions for working PFD
                assert content_analysis['nonBlackPixels'] > 1000, f"Should have substantial content, got {content_analysis['nonBlackPixels']} pixels"
                assert float(content_analysis['contentDensity']) > 1.0, f"Should have >1% content density, got {content_analysis['contentDensity']}%"
                
                print("✅ PFD initialization and rendering working after manual init")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_pfd_components_after_init(self, webgcs_server):
        """Test individual VFR components after proper initialization"""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=5000)
                
                # Force initialization and render
                await page.evaluate("""
                    () => {
                        window.pfd = new PrimaryFlightDisplay('pfd-canvas');
                        window.pfd.render();
                    }
                """)
                
                await asyncio.sleep(1)
                
                # Test specific VFR components
                component_test = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        const ctx = canvas.getContext('2d');
                        
                        // Sample key areas for VFR components
                        const areas = {
                            // Left airspeed tape
                            airspeedTape: ctx.getImageData(0, 150, 80, 200),
                            // Right altitude tape  
                            altitudeTape: ctx.getImageData(canvas.width - 80, 150, 70, 200),
                            // Center artificial horizon
                            artificialHorizon: ctx.getImageData(canvas.width/2 - 100, canvas.height/2 - 50, 200, 100),
                            // Top armed status
                            armedStatus: ctx.getImageData(canvas.width/2 - 60, 10, 120, 40),
                            // Bottom left battery status
                            batteryStatus: ctx.getImageData(10, canvas.height - 80, 200, 30)
                        };
                        
                        const results = {};
                        
                        for (const [name, imageData] of Object.entries(areas)) {
                            const data = imageData.data;
                            let pixelCount = 0;
                            
                            for (let i = 0; i < data.length; i += 4) {
                                const r = data[i];
                                const g = data[i + 1];
                                const b = data[i + 2];
                                
                                if (r > 20 || g > 20 || b > 20) {
                                    pixelCount++;
                                }
                            }
                            
                            results[name] = pixelCount;
                        }
                        
                        return results;
                    }
                """)
                
                print(f"🎯 VFR Component Detection:")
                for component, pixels in component_test.items():
                    status = "✅" if pixels > 20 else "❌"
                    print(f"   {status} {component}: {pixels} pixels")
                
                # Count components with sufficient content
                working_components = sum(1 for pixels in component_test.values() if pixels > 20)
                
                print(f"📈 Working Components: {working_components}/5")
                
                assert working_components >= 3, f"Should have at least 3 working VFR components, got {working_components}"
                
            finally:
                await browser.close()
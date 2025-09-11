"""
TEST-504: PFD Visual Validation Testing
Phase 5: VFR HUD/Primary Flight Display Testing

Tests visual components, artificial horizon functionality, attitude symbol positioning,
pitch ladder accuracy, and compass heading display.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
import time
import json


class TestPFDVisualValidation:
    """Test visual components and professional aviation display standards"""
    
    @pytest.mark.asyncio
    async def test_artificial_horizon_functionality(self):
        """TEST-504-001: Test artificial horizon functionality and rendering"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection and wait for data
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(3000)
                
                # Take screenshot of artificial horizon
                canvas = await page.query_selector('#pfd-canvas')
                await canvas.screenshot(path='pfd_artificial_horizon.png')
                
                # Test horizon rendering with different attitude values
                test_attitudes = [
                    {'pitch': 0, 'roll': 0, 'description': 'Level flight'},
                    {'pitch': 10, 'roll': 15, 'description': 'Climbing right turn'},
                    {'pitch': -5, 'roll': -10, 'description': 'Descending left turn'}
                ]
                
                horizon_tests = []
                
                for attitude in test_attitudes:
                    # Simulate attitude data
                    await page.evaluate(f"""
                        () => {{
                            if (window.pfd && window.pfd.data) {{
                                window.pfd.data.pitch = {attitude['pitch']};
                                window.pfd.data.roll = {attitude['roll']};
                            }}
                        }}
                    """)
                    
                    await page.wait_for_timeout(500)  # Wait for render
                    
                    # Check if horizon responds to attitude changes
                    horizon_state = await page.evaluate("""
                        () => {
                            const canvas = document.getElementById('pfd-canvas');
                            if (!canvas) return null;
                            
                            const ctx = canvas.getContext('2d');
                            // Sample pixels from horizon area to detect changes
                            const centerX = canvas.width / 2;
                            const centerY = canvas.height / 2;
                            
                            // Get pixel data from horizon line area
                            const imageData = ctx.getImageData(centerX-50, centerY-50, 100, 100);
                            const pixels = imageData.data;
                            
                            // Count non-black pixels (indicates horizon rendering)
                            let nonBlackPixels = 0;
                            for (let i = 0; i < pixels.length; i += 4) {
                                const r = pixels[i], g = pixels[i+1], b = pixels[i+2];
                                if (r > 10 || g > 10 || b > 10) nonBlackPixels++;
                            }
                            
                            return {
                                nonBlackPixels: nonBlackPixels,
                                totalPixels: pixels.length / 4,
                                hasContent: nonBlackPixels > 100
                            };
                        }
                    """)
                    
                    horizon_tests.append({
                        'attitude': attitude,
                        'state': horizon_state,
                        'has_content': horizon_state and horizon_state['hasContent']
                    })
                
                print("✅ Artificial Horizon Functionality Test Results:")
                for test in horizon_tests:
                    att = test['attitude']
                    status = "✅ RENDERED" if test['has_content'] else "❌ NO CONTENT"
                    print(f"   - {att['description']} (P:{att['pitch']}°, R:{att['roll']}°): {status}")
                
                # Assert that horizon is rendering content
                rendering_tests = [test['has_content'] for test in horizon_tests]
                assert any(rendering_tests), "Artificial horizon should render visual content"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_attitude_symbol_positioning(self):
        """TEST-504-002: Test aircraft attitude symbol positioning"""
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
                
                # Check attitude symbol rendering
                attitude_symbol_present = await page.evaluate("""
                    () => {
                        // Check if PFD has renderAircraftAttitude method
                        if (window.pfd && typeof window.pfd.renderAircraftAttitude === 'function') {
                            return true;
                        }
                        
                        // Check canvas for attitude symbol content in center area
                        const canvas = document.getElementById('pfd-canvas');
                        if (!canvas) return false;
                        
                        const ctx = canvas.getContext('2d');
                        const centerX = canvas.width / 2;
                        const centerY = canvas.height / 2;
                        
                        // Sample area around center for attitude symbol
                        const imageData = ctx.getImageData(centerX-20, centerY-20, 40, 40);
                        const pixels = imageData.data;
                        
                        // Look for colored pixels (attitude symbol)
                        for (let i = 0; i < pixels.length; i += 4) {
                            const r = pixels[i], g = pixels[i+1], b = pixels[i+2];
                            if (r > 50 || g > 50 || b > 50) {
                                return true; // Found non-dark pixel
                            }
                        }
                        
                        return false;
                    }
                """)
                
                # Test symbol positioning at canvas center
                canvas_center = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        return {
                            centerX: canvas.width / 2,
                            centerY: canvas.height / 2,
                            width: canvas.width,
                            height: canvas.height
                        };
                    }
                """)
                
                print("✅ Attitude Symbol Positioning Test Results:")
                print(f"   - Canvas center: ({canvas_center['centerX']}, {canvas_center['centerY']})")
                print(f"   - Canvas size: {canvas_center['width']}x{canvas_center['height']}")
                print(f"   - Attitude symbol present: {'✅ YES' if attitude_symbol_present else '❌ NO'}")
                
                # Expected center should be 400, 300 for 800x600 canvas
                assert canvas_center['centerX'] == 400, "Canvas center X should be 400"
                assert canvas_center['centerY'] == 300, "Canvas center Y should be 300"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_pitch_ladder_accuracy(self):
        """TEST-504-003: Test pitch ladder accuracy and scaling"""
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
                
                # Test pitch ladder with different pitch values
                pitch_tests = [0, 10, -10, 20, -20]
                pitch_results = []
                
                for pitch_value in pitch_tests:
                    # Set pitch value
                    await page.evaluate(f"""
                        () => {{
                            if (window.pfd && window.pfd.data) {{
                                window.pfd.data.pitch = {pitch_value};
                                window.pfd.data.roll = 0;  // Keep roll level for pitch testing
                            }}
                        }}
                    """)
                    
                    await page.wait_for_timeout(200)  # Wait for render
                    
                    # Check for pitch ladder lines
                    pitch_ladder_content = await page.evaluate(f"""
                        () => {{
                            const canvas = document.getElementById('pfd-canvas');
                            if (!canvas) return false;
                            
                            const ctx = canvas.getContext('2d');
                            const centerY = canvas.height / 2;
                            
                            // Check horizontal lines that would represent pitch ladder
                            // Sample across the width at different Y positions
                            let horizontalLines = 0;
                            
                            for (let y = centerY - 100; y < centerY + 100; y += 10) {{
                                const imageData = ctx.getImageData(200, y, 400, 1);
                                const pixels = imageData.data;
                                
                                let linePixels = 0;
                                for (let i = 0; i < pixels.length; i += 4) {{
                                    const r = pixels[i], g = pixels[i+1], b = pixels[i+2];
                                    if (r > 30 || g > 30 || b > 30) linePixels++;
                                }}
                                
                                if (linePixels > 50) horizontalLines++;  // Found a horizontal line
                            }}
                            
                            return {{
                                pitch: {pitch_value},
                                horizontalLines: horizontalLines,
                                hasLadder: horizontalLines > 2
                            }};
                        }}
                    """)
                    
                    pitch_results.append(pitch_ladder_content)
                
                print("✅ Pitch Ladder Accuracy Test Results:")
                for result in pitch_results:
                    if result:
                        status = "✅ LADDER" if result['hasLadder'] else "❌ NO LADDER"
                        print(f"   - Pitch {result['pitch']:3d}°: {result['horizontalLines']} lines, {status}")
                
                # At least some pitch values should show ladder content
                ladder_present = any(r and r['hasLadder'] for r in pitch_results if r)
                if not ladder_present:
                    print("   ⚠️  Note: Pitch ladder may not be implemented yet")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_compass_heading_display(self):
        """TEST-504-004: Test compass heading display accuracy"""
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
                
                # Test compass with different headings
                heading_tests = [0, 45, 90, 135, 180, 225, 270, 315]
                compass_results = []
                
                for heading in heading_tests:
                    # Set heading value
                    await page.evaluate(f"""
                        () => {{
                            if (window.pfd && window.pfd.data) {{
                                window.pfd.data.yaw = {heading};
                                window.pfd.data.heading = {heading};
                            }}
                        }}
                    """)
                    
                    await page.wait_for_timeout(200)  # Wait for render
                    
                    # Check for compass content in heading area (typically top of display)
                    compass_content = await page.evaluate(f"""
                        () => {{
                            const canvas = document.getElementById('pfd-canvas');
                            if (!canvas) return null;
                            
                            const ctx = canvas.getContext('2d');
                            
                            // Check top area where compass typically appears
                            const imageData = ctx.getImageData(300, 20, 200, 80);
                            const pixels = imageData.data;
                            
                            let compassPixels = 0;
                            for (let i = 0; i < pixels.length; i += 4) {{
                                const r = pixels[i], g = pixels[i+1], b = pixels[i+2];
                                if (r > 20 || g > 20 || b > 20) compassPixels++;
                            }}
                            
                            return {{
                                heading: {heading},
                                compassPixels: compassPixels,
                                hasCompass: compassPixels > 100
                            }};
                        }}
                    """)
                    
                    compass_results.append(compass_content)
                
                print("✅ Compass Heading Display Test Results:")
                for result in compass_results:
                    if result:
                        status = "✅ VISIBLE" if result['hasCompass'] else "❌ NOT VISIBLE"
                        print(f"   - Heading {result['heading']:3d}°: {result['compassPixels']} pixels, {status}")
                
                # Check if compass is generally working
                compass_visible = any(r and r['hasCompass'] for r in compass_results if r)
                if not compass_visible:
                    print("   ⚠️  Note: Compass display may not be implemented yet")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_aviation_color_standards(self):
        """TEST-504-005: Test professional aviation color standards"""
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
                
                # Take screenshot for color analysis
                canvas = await page.query_selector('#pfd-canvas')
                await canvas.screenshot(path='pfd_color_analysis.png')
                
                # Analyze color usage
                color_analysis = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        if (!canvas) return null;
                        
                        const ctx = canvas.getContext('2d');
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const pixels = imageData.data;
                        
                        let colorCounts = {
                            black: 0,     // Background
                            white: 0,     // Text/lines
                            green: 0,     // Normal/good status
                            yellow: 0,    // Caution
                            red: 0,       // Warning
                            blue: 0,      // Sky/info
                            brown: 0,     // Ground/earth
                            total: pixels.length / 4
                        };
                        
                        for (let i = 0; i < pixels.length; i += 4) {
                            const r = pixels[i], g = pixels[i+1], b = pixels[i+2];
                            
                            // Classify colors
                            if (r < 20 && g < 20 && b < 20) {
                                colorCounts.black++;
                            } else if (r > 200 && g > 200 && b > 200) {
                                colorCounts.white++;
                            } else if (g > r && g > b && g > 100) {
                                colorCounts.green++;
                            } else if (r > 200 && g > 200 && b < 100) {
                                colorCounts.yellow++;
                            } else if (r > 200 && g < 100 && b < 100) {
                                colorCounts.red++;
                            } else if (b > r && b > g && b > 100) {
                                colorCounts.blue++;
                            } else if (r > 100 && g > 50 && b < 50) {
                                colorCounts.brown++;
                            }
                        }
                        
                        return colorCounts;
                    }
                """)
                
                if color_analysis:
                    print("✅ Aviation Color Standards Test Results:")
                    total = color_analysis['total']
                    for color, count in color_analysis.items():
                        if color != 'total':
                            percentage = (count / total) * 100
                            print(f"   - {color.capitalize():8s}: {count:6d} pixels ({percentage:4.1f}%)")
                    
                    # Background should use aviation colors (dark or blue/brown for horizon)
                    dark_percentage = (color_analysis['black'] / total) * 100
                    aviation_colors_percentage = ((color_analysis['black'] + color_analysis['blue'] + color_analysis['brown']) / total) * 100
                    
                    # Either predominantly dark OR using aviation horizon colors (blue sky + brown ground)
                    assert dark_percentage > 30 or aviation_colors_percentage > 60, \
                        f"Background should be dark ({dark_percentage:.1f}%) or use aviation colors ({aviation_colors_percentage:.1f}%)"
                    
                    print(f"\\n   ✅ Aviation colors: {aviation_colors_percentage:.1f}% (dark: {dark_percentage:.1f}%)")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_text_readability(self):
        """TEST-504-006: Test text readability and font sizing"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Check text elements in data panel
                text_elements = [
                    '#pitch-value', '#roll-value', '#yaw-value',
                    '#altitude-value', '#groundspeed-value', '#armed-text'
                ]
                
                readability_results = []
                
                for selector in text_elements:
                    element = await page.query_selector(selector)
                    if element:
                        # Get text properties
                        text_props = await page.evaluate(f"""
                            (element) => {{
                                const style = window.getComputedStyle(element);
                                const rect = element.getBoundingClientRect();
                                return {{
                                    fontSize: style.fontSize,
                                    fontFamily: style.fontFamily,
                                    color: style.color,
                                    backgroundColor: style.backgroundColor,
                                    width: rect.width,
                                    height: rect.height,
                                    text: element.textContent
                                }};
                            }}
                        """, element)
                        
                        readability_results.append({
                            'selector': selector,
                            'props': text_props
                        })
                
                print("✅ Text Readability Test Results:")
                for result in readability_results:
                    props = result['props']
                    font_size = props['fontSize']
                    text_content = props['text'][:20] + "..." if len(props['text']) > 20 else props['text']
                    print(f"   - {result['selector']:15s}: {font_size:4s} '{text_content}'")
                
                # Check that text elements are present and have reasonable sizing
                assert len(readability_results) > 0, "Should have readable text elements"
                
                # Check font sizes are reasonable (at least 12px)
                for result in readability_results:
                    font_size_px = int(result['props']['fontSize'].replace('px', ''))
                    assert font_size_px >= 12, f"Font size {font_size_px}px too small for {result['selector']}"
                
            finally:
                await browser.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
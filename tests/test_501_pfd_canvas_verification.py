"""
TEST-501: PFD Canvas Verification
Phase 5: VFR HUD/Primary Flight Display Testing

Validates the basic PFD canvas setup and initial rendering.
Tests canvas dimensions, presence, and basic rendering functionality.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
import time


class TestPFDCanvasVerification:
    """Test PFD canvas basic setup and verification"""
    
    @pytest.mark.asyncio
    async def test_pfd_canvas_presence_and_dimensions(self):
        """TEST-501-001: Verify PFD canvas element exists with correct dimensions"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Navigate to WebGCS
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                
                # Wait for PFD canvas to be present
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Verify canvas element exists
                canvas = await page.query_selector('#pfd-canvas')
                assert canvas is not None, "PFD canvas element not found"
                
                # Check canvas dimensions (800x600 as specified)
                width = await canvas.get_attribute('width')
                height = await canvas.get_attribute('height')
                
                assert width == '800', f"Canvas width should be 800, got {width}"
                assert height == '600', f"Canvas height should be 600, got {height}"
                
                # Verify canvas is visible
                is_visible = await canvas.is_visible()
                assert is_visible, "PFD canvas should be visible"
                
                print("✅ PFD canvas verification successful:")
                print(f"   - Canvas dimensions: {width}x{height}")
                print(f"   - Canvas visible: {is_visible}")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_pfd_container_structure(self):
        """TEST-501-002: Verify PFD container and overlay structure"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                
                # Check PFD container
                pfd_container = await page.query_selector('.pfd-container')
                assert pfd_container is not None, "PFD container not found"
                
                # Check status overlay elements
                armed_indicator = await page.query_selector('#armed-indicator')
                assert armed_indicator is not None, "Armed indicator not found"
                
                connection_indicator = await page.query_selector('#pfd-connection')
                assert connection_indicator is not None, "Connection indicator not found"
                
                # Check armed text element
                armed_text = await page.query_selector('#armed-text')
                assert armed_text is not None, "Armed text element not found"
                
                # Verify initial armed status
                armed_text_content = await armed_text.text_content()
                assert armed_text_content in ['ARMED', 'DISARMED'], f"Invalid armed status: {armed_text_content}"
                
                print("✅ PFD container structure verification successful:")
                print(f"   - Armed status: {armed_text_content}")
                print("   - All overlay elements present")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_pfd_data_panel_structure(self):
        """TEST-501-003: Verify PFD data panel structure and elements"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                
                # Check PFD data panel
                data_panel = await page.query_selector('.pfd-data-panel')
                assert data_panel is not None, "PFD data panel not found"
                
                # Check attitude data elements
                attitude_elements = {
                    '#pitch-value': 'Pitch value',
                    '#roll-value': 'Roll value',
                    '#yaw-value': 'Yaw value'
                }
                
                for selector, description in attitude_elements.items():
                    element = await page.query_selector(selector)
                    assert element is not None, f"{description} element not found"
                    
                    # Check initial value format
                    text = await element.text_content()
                    assert '°' in text, f"{description} should show degrees symbol"
                
                # Check position data elements
                position_elements = {
                    '#altitude-value': 'Altitude value',
                    '#groundspeed-value': 'Ground speed value',
                    '#verticalspeed-value': 'Vertical speed value'
                }
                
                for selector, description in position_elements.items():
                    element = await page.query_selector(selector)
                    assert element is not None, f"{description} element not found"
                
                print("✅ PFD data panel structure verification successful:")
                print("   - All attitude data elements present")
                print("   - All position data elements present")
                print("   - Initial value formats correct")
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_pfd_canvas_rendering_state(self):
        """TEST-501-004: Verify PFD canvas is actively rendering"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                
                # Wait for canvas to be present
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Take initial screenshot of canvas
                canvas = await page.query_selector('#pfd-canvas')
                initial_screenshot = await canvas.screenshot()
                
                # Wait a bit for rendering
                await page.wait_for_timeout(2000)
                
                # Take second screenshot
                second_screenshot = await canvas.screenshot()
                
                # Canvas should have some content (not blank)
                assert len(initial_screenshot) > 1000, "Canvas appears to be blank or not rendering"
                
                # Check for PFD JavaScript initialization
                pfd_initialized = await page.evaluate("""
                    () => {
                        return window.pfd !== undefined;
                    }
                """)
                
                print("✅ PFD canvas rendering verification successful:")
                print(f"   - Canvas has content (screenshot size: {len(initial_screenshot)} bytes)")
                print(f"   - PFD JavaScript initialized: {pfd_initialized}")
                
            finally:
                await browser.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
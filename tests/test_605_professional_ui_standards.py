"""
UI Validation Testing Agent - Professional UI Standards Tests

Phase 6 Test 5: Professional Aviation Interface Standards Testing
Tests aviation interface standards, accessibility, and responsive design using Playwright MCP.

SAFETY-CRITICAL: Ensures UI meets professional aviation standards for operational safety.
"""

import pytest
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

class TestProfessionalUIStandards:
    """
    Tests professional aviation interface standards:
    - Aviation color coding (green=safe, yellow=caution, red=danger)
    - Text contrast and readability standards
    - Button sizing for touch interfaces
    - Keyboard navigation and accessibility
    - Responsive design across resolutions
    - Component scaling and layout consistency
    """
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.base_url = "http://localhost:5002"
        cls.timeout = 10000
        
    async def setup_browser(self, viewport_size=(1920, 1080)):
        """Setup browser and page for testing"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(viewport={'width': viewport_size[0], 'height': viewport_size[1]})
        self.page = await self.context.new_page()
        
        # Navigate to WebGCS
        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state('networkidle')
        
    async def teardown_browser(self):
        """Cleanup browser resources"""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    def parse_color(self, color_string):
        """Parse CSS color string to RGB values"""
        if not color_string:
            return None
            
        # Handle rgb() format
        if 'rgb(' in color_string:
            values = color_string.replace('rgb(', '').replace(')', '').split(',')
            return tuple(int(v.strip()) for v in values)
            
        # Handle rgba() format
        if 'rgba(' in color_string:
            values = color_string.replace('rgba(', '').replace(')', '').split(',')
            return tuple(int(v.strip()) for v in values[:3])  # Ignore alpha
            
        return None

    def calculate_contrast_ratio(self, fg_color, bg_color):
        """Calculate color contrast ratio"""
        if not fg_color or not bg_color:
            return 1.0
            
        def luminance(rgb):
            """Calculate relative luminance"""
            r, g, b = [c/255.0 for c in rgb]
            
            def adjust(c):
                if c <= 0.03928:
                    return c / 12.92
                else:
                    return ((c + 0.055) / 1.055) ** 2.4
                    
            return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
            
        l1 = luminance(fg_color)
        l2 = luminance(bg_color)
        
        if l1 > l2:
            return (l1 + 0.05) / (l2 + 0.05)
        else:
            return (l2 + 0.05) / (l1 + 0.05)

    @pytest.mark.asyncio
    async def test_aviation_color_coding_standards(self):
        """Test that UI follows aviation color coding standards"""
        await self.setup_browser()
        
        try:
            # Test status indicators for proper color coding
            status_elements = await self.page.query_selector_all('.status, .connection-status, [class*="success"], [class*="error"], [class*="warning"]')
            
            for element in status_elements:
                if await element.is_visible():
                    element_class = await element.get_attribute('class')
                    style = await element.evaluate('el => getComputedStyle(el)')
                    
                    color = style.get('color', '')
                    bg_color = style.get('backgroundColor', '')
                    
                    print(f"Status element class: {element_class}")
                    print(f"Colors - text: {color}, background: {bg_color}")
                    
                    # Check aviation color standards
                    if 'success' in (element_class or '').lower() or 'connected' in (element_class or '').lower():
                        # Should use green for safe/success states
                        color_rgb = self.parse_color(color) or self.parse_color(bg_color)
                        if color_rgb:
                            r, g, b = color_rgb
                            # Green should have higher green component
                            assert g > r and g > b, "Success states should use green color"
                            
                    elif 'error' in (element_class or '').lower() or 'danger' in (element_class or '').lower():
                        # Should use red for error/danger states
                        color_rgb = self.parse_color(color) or self.parse_color(bg_color)
                        if color_rgb:
                            r, g, b = color_rgb
                            # Red should have higher red component
                            assert r > g and r > b, "Error states should use red color"
                            
                    elif 'warning' in (element_class or '').lower() or 'caution' in (element_class or '').lower():
                        # Should use yellow/orange for warning states
                        color_rgb = self.parse_color(color) or self.parse_color(bg_color)
                        if color_rgb:
                            r, g, b = color_rgb
                            # Yellow/orange should have high red and green, low blue
                            assert r > b and g > b, "Warning states should use yellow/orange color"
                            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_text_contrast_readability_standards(self):
        """Test that text meets WCAG contrast ratio standards (4.5:1 minimum)"""
        await self.setup_browser()
        
        try:
            # Test critical text elements
            text_elements = await self.page.query_selector_all('button, .error-message, .status, label, input, .navigation-value, .pfd-value')
            
            contrast_failures = []
            
            for element in text_elements[:10]:  # Test first 10 to avoid timeout
                if await element.is_visible():
                    style = await element.evaluate('el => getComputedStyle(el)')
                    
                    text_color = style.get('color', '')
                    bg_color = style.get('backgroundColor', '')
                    
                    # Get parent background if element has transparent background
                    if not bg_color or bg_color == 'rgba(0, 0, 0, 0)':
                        parent_style = await element.evaluate('el => getComputedStyle(el.parentElement)')
                        bg_color = parent_style.get('backgroundColor', 'rgb(255, 255, 255)')
                        
                    text_rgb = self.parse_color(text_color)
                    bg_rgb = self.parse_color(bg_color)
                    
                    if text_rgb and bg_rgb:
                        contrast_ratio = self.calculate_contrast_ratio(text_rgb, bg_rgb)
                        
                        element_text = await element.text_content()
                        element_tag = await element.evaluate('el => el.tagName')
                        
                        print(f"{element_tag}: '{element_text[:20]}...' - Contrast: {contrast_ratio:.2f}")
                        
                        # WCAG AA standard: 4.5:1 for normal text, 3:1 for large text
                        font_size = style.get('fontSize', '16px')
                        size_value = int(font_size.replace('px', '').split('.')[0])
                        
                        required_contrast = 3.0 if size_value >= 18 else 4.5
                        
                        if contrast_ratio < required_contrast:
                            contrast_failures.append({
                                'element': element_tag,
                                'text': element_text[:50] if element_text else '',
                                'contrast': contrast_ratio,
                                'required': required_contrast,
                                'text_color': text_color,
                                'bg_color': bg_color
                            })
                            
            # Report contrast failures
            if contrast_failures:
                print(f"\nContrast ratio failures ({len(contrast_failures)}):")
                for failure in contrast_failures:
                    print(f"  {failure['element']}: {failure['contrast']:.2f} < {failure['required']} required")
                    
                # For safety-critical aviation UI, contrast must be adequate
                assert len(contrast_failures) == 0, f"Found {len(contrast_failures)} contrast ratio failures"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_button_sizing_touch_interface_standards(self):
        """Test that buttons meet touch interface sizing standards (44px minimum)"""
        await self.setup_browser()
        
        try:
            # Test all interactive buttons
            buttons = await self.page.query_selector_all('button, input[type="submit"], input[type="button"], .btn')
            
            sizing_failures = []
            
            for button in buttons:
                if await button.is_visible():
                    button_box = await button.bounding_box()
                    button_text = await button.text_content()
                    button_id = await button.get_attribute('id')
                    
                    if button_box:
                        width = button_box['width']
                        height = button_box['height']
                        
                        print(f"Button '{button_text or button_id}': {width}x{height}px")
                        
                        # Touch interface standards: minimum 44x44px
                        min_size = 44
                        
                        if width < min_size or height < min_size:
                            sizing_failures.append({
                                'text': button_text or button_id or 'unnamed',
                                'size': f"{width}x{height}",
                                'width': width,
                                'height': height
                            })
                            
            # Critical buttons should meet touch standards
            if sizing_failures:
                print(f"\nButton sizing failures ({len(sizing_failures)}):")
                for failure in sizing_failures:
                    print(f"  '{failure['text']}': {failure['size']} < 44x44px required")
                    
                # For safety-critical operations, buttons must be adequately sized
                critical_failures = [f for f in sizing_failures if any(word in f['text'].lower() 
                                    for word in ['arm', 'disarm', 'takeoff', 'emergency', 'land'])]
                                    
                assert len(critical_failures) == 0, f"Critical buttons must meet touch sizing standards"
                
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_keyboard_navigation_accessibility(self):
        """Test keyboard navigation and accessibility features"""
        await self.setup_browser()
        
        try:
            # Test tab navigation through interface
            await self.page.keyboard.press('Tab')
            
            # Track focusable elements
            focusable_elements = []
            
            for i in range(20):  # Test first 20 tab stops
                focused_element = await self.page.evaluate('document.activeElement')
                
                if focused_element:
                    tag_name = await self.page.evaluate('document.activeElement.tagName')
                    element_id = await self.page.evaluate('document.activeElement.id')
                    element_class = await self.page.evaluate('document.activeElement.className')
                    
                    focus_info = f"{tag_name}#{element_id}.{element_class}"
                    
                    if focus_info not in focusable_elements:
                        focusable_elements.append(focus_info)
                        print(f"Tab {i+1}: {focus_info}")
                        
                        # Check focus indicator visibility
                        style = await self.page.evaluate('getComputedStyle(document.activeElement)')
                        outline = style.get('outline', '')
                        outline_color = style.get('outlineColor', '')
                        box_shadow = style.get('boxShadow', '')
                        
                        has_focus_indicator = (outline and outline != 'none') or \
                                            (outline_color and outline_color != 'transparent') or \
                                            (box_shadow and box_shadow != 'none')
                                            
                        if not has_focus_indicator:
                            print(f"  Warning: No visible focus indicator for {focus_info}")
                            
                await self.page.keyboard.press('Tab')
                await asyncio.sleep(0.1)
                
            # Should have reasonable number of focusable elements
            assert len(focusable_elements) >= 5, "Should have adequate keyboard navigation"
            
            # Test escape key handling
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(0.1)
            
            print(f"Found {len(focusable_elements)} focusable elements")
            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_responsive_design_multiple_resolutions(self):
        """Test responsive design across different screen resolutions"""
        test_resolutions = [
            (1920, 1080),  # Full HD
            (1366, 768),   # Common laptop
            (1024, 768),   # Small laptop/tablet
            (768, 1024),   # Tablet portrait
        ]
        
        for width, height in test_resolutions:
            await self.setup_browser((width, height))
            
            try:
                print(f"\nTesting resolution: {width}x{height}")
                
                # Check that critical elements are visible
                critical_elements = ['#arm-btn', '#disarm-btn', '#takeoff-btn', '#goto-btn']
                
                for element_id in critical_elements:
                    element = await self.page.query_selector(element_id)
                    if element:
                        is_visible = await element.is_visible()
                        box = await element.bounding_box()
                        
                        if box:
                            in_viewport = (box['x'] >= 0 and box['y'] >= 0 and 
                                         box['x'] + box['width'] <= width and 
                                         box['y'] + box['height'] <= height)
                                         
                            print(f"  {element_id}: visible={is_visible}, in_viewport={in_viewport}")
                            
                            # Critical elements must be accessible at all resolutions
                            assert is_visible, f"{element_id} must be visible at {width}x{height}"
                            assert in_viewport, f"{element_id} must be in viewport at {width}x{height}"
                            
                # Check for horizontal scrolling (should be minimal)
                scroll_width = await self.page.evaluate('document.body.scrollWidth')
                viewport_width = width
                
                has_horizontal_scroll = scroll_width > viewport_width
                if has_horizontal_scroll:
                    print(f"  Warning: Horizontal scroll detected ({scroll_width} > {viewport_width})")
                    
                # Check text readability (not too small)
                text_elements = await self.page.query_selector_all('button, label, .navigation-value')
                
                for element in text_elements[:5]:  # Check first 5
                    if await element.is_visible():
                        style = await element.evaluate('el => getComputedStyle(el)')
                        font_size = style.get('fontSize', '16px')
                        size_value = int(font_size.replace('px', '').split('.')[0])
                        
                        # Text should remain readable (min 12px)
                        assert size_value >= 12, f"Text too small at {width}x{height}: {size_value}px"
                        
            finally:
                await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_component_scaling_layout_consistency(self):
        """Test that components scale consistently and maintain layout"""
        await self.setup_browser()
        
        try:
            # Test PFD canvas scaling
            pfd_canvas = await self.page.query_selector('#pfd-canvas')
            if pfd_canvas:
                canvas_box = await pfd_canvas.bounding_box()
                print(f"PFD Canvas: {canvas_box['width']}x{canvas_box['height']}")
                
                # Should maintain aspect ratio
                aspect_ratio = canvas_box['width'] / canvas_box['height']
                expected_ratio = 800 / 600  # From reference images
                
                ratio_diff = abs(aspect_ratio - expected_ratio)
                assert ratio_diff < 0.1, "PFD should maintain proper aspect ratio"
                
            # Test navigation panel layout
            nav_inputs = await self.page.query_selector_all('#goto-latitude, #goto-longitude, #goto-altitude')
            
            if len(nav_inputs) >= 2:
                # Check alignment
                boxes = []
                for input_field in nav_inputs:
                    box = await input_field.bounding_box()
                    if box:
                        boxes.append(box)
                        
                if len(boxes) >= 2:
                    # Check vertical alignment
                    x_positions = [box['x'] for box in boxes]
                    x_variance = max(x_positions) - min(x_positions)
                    
                    print(f"Navigation input alignment variance: {x_variance}px")
                    
                    # Should be well-aligned (within 10px)
                    assert x_variance <= 10, "Navigation inputs should be properly aligned"
                    
            # Test button group consistency
            button_groups = [
                ['#arm-btn', '#disarm-btn'],
                ['#stabilize-btn', '#alt-hold-btn', '#loiter-btn'],
                ['#guided-btn', '#rtl-btn', '#auto-btn', '#land-btn']
            ]
            
            for group in button_groups:
                group_buttons = []
                for btn_id in group:
                    btn = await self.page.query_selector(btn_id)
                    if btn and await btn.is_visible():
                        box = await btn.bounding_box()
                        if box:
                            group_buttons.append(box)
                            
                if len(group_buttons) >= 2:
                    # Check consistent sizing within group
                    heights = [box['height'] for box in group_buttons]
                    height_variance = max(heights) - min(heights)
                    
                    print(f"Button group height variance: {height_variance}px")
                    
                    # Buttons in group should have consistent height
                    assert height_variance <= 5, "Buttons in group should have consistent height"
                    
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_professional_typography_standards(self):
        """Test typography meets professional aviation standards"""
        await self.setup_browser()
        
        try:
            # Check font choices for different element types
            element_types = [
                ('button', 'button'),
                ('.navigation-value', 'navigation data'),
                ('.pfd-value', 'flight data'),
                ('label', 'form labels'),
                ('.error-message', 'error messages')
            ]
            
            for selector, description in element_types:
                elements = await self.page.query_selector_all(selector)
                
                if elements:
                    element = elements[0]  # Test first element of each type
                    if await element.is_visible():
                        style = await element.evaluate('el => getComputedStyle(el)')
                        
                        font_family = style.get('fontFamily', '')
                        font_size = style.get('fontSize', '')
                        font_weight = style.get('fontWeight', '')
                        line_height = style.get('lineHeight', '')
                        
                        print(f"{description}: {font_family}, {font_size}, weight {font_weight}")
                        
                        # Font size should be reasonable
                        size_value = int(font_size.replace('px', '').split('.')[0])
                        assert size_value >= 12, f"{description} font too small: {size_value}px"
                        assert size_value <= 24, f"{description} font too large: {size_value}px"
                        
                        # Should use readable fonts (no decorative fonts for data)
                        if 'data' in description or 'navigation' in description:
                            # Data should use monospace or sans-serif for clarity
                            acceptable_fonts = ['monospace', 'sans-serif', 'Arial', 'Helvetica', 'Monaco', 'Courier']
                            has_readable_font = any(font in font_family for font in acceptable_fonts)
                            assert has_readable_font, f"{description} should use readable font family"
                            
        finally:
            await self.teardown_browser()

    @pytest.mark.asyncio
    async def test_loading_performance_standards(self):
        """Test that interface loads within professional performance standards"""
        await self.setup_browser()
        
        try:
            # Measure page load performance
            start_time = time.time()
            
            # Wait for all critical elements to be ready
            critical_elements = [
                '#arm-btn', '#disarm-btn', '#takeoff-btn',
                '#goto-latitude', '#goto-longitude', '#goto-altitude',
                '#pfd-canvas'
            ]
            
            for element_id in critical_elements:
                await self.page.wait_for_selector(element_id, timeout=5000)
                
            end_time = time.time()
            load_time = end_time - start_time
            
            print(f"Critical elements load time: {load_time:.2f} seconds")
            
            # Should load within reasonable time for safety-critical application
            assert load_time < 5.0, "Interface should load within 5 seconds"
            
            # Test JavaScript responsiveness
            js_start = time.time()
            await self.page.evaluate('1 + 1')  # Simple JS execution test
            js_end = time.time()
            js_time = js_end - js_start
            
            print(f"JavaScript responsiveness: {js_time*1000:.1f}ms")
            
            # Should be responsive
            assert js_time < 0.1, "JavaScript should be responsive"
            
        finally:
            await self.teardown_browser()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
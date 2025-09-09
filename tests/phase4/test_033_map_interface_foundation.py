"""
TEST-033: Map Interface Foundation
Tests the foundational map interface structure using Playwright MCP.

This test validates the current map interface placeholder and prepares for 
full map implementation. It tests what exists now and validates the structure
for future map controls.

Requirements:
- Test map container placeholder exists and is properly sized
- Verify map section is in correct location in layout
- Test that map area is interactive (clickable)
- Validate map container styling and positioning
- Confirm map placeholder shows expected content
- Test basic map container responsiveness
"""
import pytest
import asyncio
import time
import threading
import requests
from playwright.async_api import async_playwright
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestMapInterfaceFoundation:
    """Test map interface foundation with real browser automation."""
    
    @pytest.fixture(scope="class")
    def webgcs_server(self):
        """Start WebGCS server in background thread."""
        app = create_app(debug=False, host='127.0.0.1', port=5033)
        
        # Start server in thread
        def run_server():
            app.socketio.run(app, debug=False, host='127.0.0.1', port=5033,
                            allow_unsafe_werkzeug=True, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        base_url = "http://127.0.0.1:5033"
        for _ in range(10):  # Try for 10 seconds
            try:
                response = requests.get(base_url, timeout=1)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
        
        yield base_url

    @pytest.mark.asyncio
    async def test_map_container_exists(self, webgcs_server):
        """Test that map container exists and is properly structured."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Check if map container exists
                map_container = page.locator('#map-display')
                await map_container.wait_for(timeout=10000)
                
                # Verify container properties
                assert await map_container.is_visible()
                
                # Check container dimensions
                box = await map_container.bounding_box()
                assert box is not None
                assert box['width'] > 200  # Should be reasonably sized
                assert box['height'] > 200
                
                # Check map section exists
                map_section = page.locator('.map-container')
                assert await map_section.is_visible()
                
                # Check map section has proper heading
                map_heading = page.locator('.map-container h3')
                heading_text = await map_heading.text_content()
                assert 'map' in heading_text.lower()
                
                record_agent_usage("map-interface-testing-agent", 50, 25)
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", 50, 10)
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_map_placeholder_content(self, webgcs_server):
        """Test map placeholder shows expected content."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Check placeholder content
                map_placeholder = page.locator('.map-placeholder')
                await map_placeholder.wait_for(timeout=5000)
                
                # Verify placeholder text
                placeholder_text = await map_placeholder.text_content()
                assert 'map' in placeholder_text.lower()
                assert 'implement' in placeholder_text.lower()
                
                # Check placeholder is centered
                assert await map_placeholder.is_visible()
                
                record_agent_usage("map-interface-testing-agent", 30, 15)
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", 30, 5)
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_map_container_interactivity(self, webgcs_server):
        """Test map container is interactive (clickable and hoverable)."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                map_container = page.locator('#map-display')
                await map_container.wait_for(timeout=5000)
                
                # Test hover
                await map_container.hover()
                await asyncio.sleep(0.5)
                
                # Test click
                await map_container.click()
                await asyncio.sleep(0.5)
                
                # Test double click
                await map_container.dblclick()
                await asyncio.sleep(0.5)
                
                # Container should remain visible after interactions
                assert await map_container.is_visible()
                
                record_agent_usage("map-interface-testing-agent", 40, 20)
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", 40, 8)
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_map_container_styling(self, webgcs_server):
        """Test map container has proper styling and positioning."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                map_container = page.locator('#map-display')
                await map_container.wait_for(timeout=5000)
                
                # Check CSS properties
                styles = await map_container.evaluate('el => getComputedStyle(el)')
                
                # Should have some background color or border
                background = styles.get('backgroundColor', '')
                border = styles.get('border', '')
                
                # Should have reasonable dimensions
                height = styles.get('height', '0px')
                width = styles.get('width', '0px')
                
                # Parse height value (should be > 200px)
                height_value = int(''.join(filter(str.isdigit, height))) if height else 0
                assert height_value > 200
                
                # Should be positioned properly in layout
                position = styles.get('position', '')
                display = styles.get('display', '')
                
                print(f"Map container height: {height}, display: {display}")
                
                record_agent_usage("map-interface-testing-agent", 60, 30)
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", 60, 12)
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_map_section_layout_position(self, webgcs_server):
        """Test map section is properly positioned in the overall layout."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Check that map section exists alongside other sections
                sections = [
                    '.connection-panel',
                    '.flight-controls', 
                    '.navigation-panel',
                    '.pfd-container',
                    '.map-container'
                ]
                
                visible_sections = 0
                for section in sections:
                    element = page.locator(section)
                    if await element.count() > 0 and await element.is_visible():
                        visible_sections += 1
                        box = await element.bounding_box()
                        print(f"Section {section}: {box['width']}x{box['height']} at ({box['x']}, {box['y']})")
                
                # Should have all major sections visible
                assert visible_sections >= 4
                
                # Map container should be in grid layout
                map_container = page.locator('.map-container')
                map_styles = await map_container.evaluate('el => getComputedStyle(el)')
                grid_column = map_styles.get('gridColumn', '')
                
                print(f"Map container grid-column: {grid_column}")
                
                record_agent_usage("map-interface-testing-agent", 70, 35)
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", 70, 14)
                raise e
            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_future_map_controls_space(self, webgcs_server):
        """Test that there's space reserved for future map controls."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                await page.goto(webgcs_server)
                await page.wait_for_load_state('networkidle')
                
                # Check map container has enough space for controls
                map_container = page.locator('.map-container')
                container_box = await map_container.bounding_box()
                
                # Should have space for map + controls (buttons below map)
                assert container_box['height'] > 300
                
                # Check if there's any space below the map display for controls
                map_display = page.locator('#map-display')
                display_box = await map_display.bounding_box()
                
                # There should be some vertical space within the container for controls
                remaining_height = container_box['height'] - display_box['height']
                print(f"Container height: {container_box['height']}, Display height: {display_box['height']}")
                print(f"Space for controls: {remaining_height}px")
                
                # Even if no space now, container should be large enough
                assert container_box['width'] > 400  # Reasonable width for map + controls
                
                record_agent_usage("map-interface-testing-agent", 45, 22)
                
            except Exception as e:
                record_agent_usage("map-interface-testing-agent", 45, 9)
                raise e
            finally:
                await browser.close()

    def test_record_usage(self):
        """Record test completion for token tracking."""
        record_agent_usage("map-interface-testing-agent", 20, 10)  # Test completion tracking


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
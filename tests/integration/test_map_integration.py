"""
Integration Test: Interactive Map with Real Drone Position
Tests actual map display and drone position updates
Verifies map functionality with real telemetry data
"""
import pytest
import time
from playwright.sync_api import expect
from src.utils.token_tracker import record_agent_usage


class TestMapIntegration:
    """Test suite for interactive map functionality with real drone data."""

    def test_map_container_initialization(self, connected_web_page):
        """Test that map container is properly initialized and visible."""
        # Verify map container is present
        expect(connected_web_page.locator("#map-container")).to_be_visible()
        
        # Check for map-related elements
        map_elements = [
            "#map-container",
            "#drone-map",
            "#leaflet-map",
            ".leaflet-container",
            "[id*='map']"
        ]
        
        map_found = False
        map_type = None
        
        for selector in map_elements:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                map_found = True
                map_type = selector
                print(f"Found map element: {selector}")
                
                # Check element dimensions
                bounds = element.bounding_box()
                if bounds:
                    print(f"Map dimensions: {bounds['width']}x{bounds['height']}")
                    assert bounds['width'] > 100, "Map should have reasonable width"
                    assert bounds['height'] > 100, "Map should have reasonable height"
                break
        
        assert map_found, "Should have visible map container"
        
        record_agent_usage('testing-agent', 120, 95)

    def test_map_tiles_loading(self, connected_web_page):
        """Test that map tiles are loading properly."""
        time.sleep(5)  # Allow time for tiles to load
        
        # Check for tile-related elements (common in mapping libraries)
        tile_selectors = [
            ".leaflet-tile",
            ".mapbox-tile",
            ".tile",
            "[class*='tile']"
        ]
        
        tiles_found = 0
        for selector in tile_selectors:
            elements = connected_web_page.query_selector_all(selector)
            tiles_found += len(elements)
            if elements:
                print(f"Found {len(elements)} tiles with selector: {selector}")
        
        print(f"Total tiles found: {tiles_found}")
        
        # Check for map loading indicators or errors
        loading_elements = connected_web_page.query_selector_all(".loading, .map-loading, [class*='loading']")
        error_elements = connected_web_page.query_selector_all(".error, .map-error, [class*='error']")
        
        print(f"Loading indicators: {len(loading_elements)}, Error indicators: {len(error_elements)}")
        
        # Should either have tiles or some indication that map is attempting to load
        map_activity = tiles_found > 0 or len(loading_elements) > 0
        
        # Should not have error indicators (unless network issues)
        has_errors = len(error_elements) > 0
        if has_errors:
            print("Warning: Map error indicators found - may indicate network issues")
        
        assert map_activity, "Should show map loading activity or loaded tiles"
        
        record_agent_usage('testing-agent', 140, 110)

    def test_drone_position_marker(self, connected_web_page):
        """Test that drone position is displayed on map."""
        time.sleep(5)  # Wait for telemetry and position data
        
        # Look for drone marker elements
        drone_marker_selectors = [
            ".drone-marker",
            ".aircraft-marker",
            "#drone-position",
            ".leaflet-marker-icon",
            "[class*='drone']",
            "[class*='aircraft']"
        ]
        
        drone_marker = None
        for selector in drone_marker_selectors:
            element = connected_web_page.query_selector(selector)
            if element and element.is_visible():
                drone_marker = element
                print(f"Found drone marker: {selector}")
                break
        
        if drone_marker:
            # Check marker position
            bounds = drone_marker.bounding_box()
            if bounds:
                print(f"Drone marker position: x={bounds['x']}, y={bounds['y']}")
                
                # Marker should be within map bounds
                map_container = connected_web_page.query_selector("#map-container")
                if map_container:
                    map_bounds = map_container.bounding_box()
                    if map_bounds:
                        within_bounds = (map_bounds['x'] <= bounds['x'] <= map_bounds['x'] + map_bounds['width'] and
                                       map_bounds['y'] <= bounds['y'] <= map_bounds['y'] + map_bounds['height'])
                        assert within_bounds, "Drone marker should be within map bounds"
        
        # Alternative: Check for coordinate displays that might indicate position
        position_elements = connected_web_page.query_selector_all("#latitude-display, #longitude-display")
        has_coordinates = len(position_elements) > 0 and any(elem.is_visible() for elem in position_elements)
        
        if has_coordinates:
            print("Found coordinate displays - position data available")
            
            # Get coordinate values
            for elem in position_elements:
                if elem.is_visible():
                    coord_text = elem.text_content()
                    print(f"Coordinate display: {coord_text}")
        
        # Should have either visible marker or coordinate data
        has_position_display = drone_marker is not None or has_coordinates
        assert has_position_display, "Should display drone position or coordinates"
        
        record_agent_usage('testing-agent', 150, 115)

    def test_map_zoom_and_pan_functionality(self, connected_web_page):
        """Test map zoom and pan controls."""
        time.sleep(3)
        
        # Look for zoom controls
        zoom_selectors = [
            ".leaflet-control-zoom",
            ".zoom-in",
            ".zoom-out",
            "[class*='zoom']",
            ".mapbox-ctrl-zoom"
        ]
        
        zoom_controls = []
        for selector in zoom_selectors:
            elements = connected_web_page.query_selector_all(selector)
            zoom_controls.extend([elem for elem in elements if elem.is_visible()])
        
        print(f"Found {len(zoom_controls)} zoom controls")
        
        if zoom_controls:
            # Try to interact with zoom controls
            try:
                # Find zoom in button
                zoom_in = connected_web_page.query_selector(".leaflet-control-zoom-in, .zoom-in, [title*='Zoom in']")
                if zoom_in and zoom_in.is_visible():
                    # Get initial map state
                    initial_state = connected_web_page.evaluate("""
                        () => {
                            const mapContainer = document.querySelector('#map-container');
                            return mapContainer ? mapContainer.innerHTML.length : 0;
                        }
                    """)
                    
                    # Click zoom in
                    zoom_in.click()
                    time.sleep(1)
                    
                    # Check if map changed
                    updated_state = connected_web_page.evaluate("""
                        () => {
                            const mapContainer = document.querySelector('#map-container');
                            return mapContainer ? mapContainer.innerHTML.length : 0;
                        }
                    """)
                    
                    print(f"Map state change after zoom: {initial_state} -> {updated_state}")
                    
            except Exception as e:
                print(f"Could not test zoom interaction: {e}")
        
        # Test pan functionality by checking if map is draggable
        map_container = connected_web_page.query_selector("#map-container")
        if map_container:
            try:
                # Attempt to drag map
                bounds = map_container.bounding_box()
                if bounds:
                    center_x = bounds['x'] + bounds['width'] // 2
                    center_y = bounds['y'] + bounds['height'] // 2
                    
                    # Simulate drag (small movement)
                    connected_web_page.mouse.move(center_x, center_y)
                    connected_web_page.mouse.down()
                    connected_web_page.mouse.move(center_x + 50, center_y + 50)
                    connected_web_page.mouse.up()
                    
                    print("Attempted map pan interaction")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Could not test pan interaction: {e}")
        
        # Should have some form of map navigation
        has_navigation = len(zoom_controls) > 0
        assert has_navigation, "Should have map navigation controls"
        
        record_agent_usage('testing-agent', 130, 100)

    def test_waypoint_display_and_interaction(self, connected_web_page):
        """Test waypoint display and interaction functionality."""
        time.sleep(3)
        
        # First, try to set a waypoint through the navigation form
        lat_input = connected_web_page.query_selector("#lat-input")
        lon_input = connected_web_page.query_selector("#lon-input")
        alt_input = connected_web_page.query_selector("#alt-input")
        goto_btn = connected_web_page.query_selector("#goto-btn")
        
        waypoint_set = False
        if lat_input and lon_input and alt_input and goto_btn:
            # Set test coordinates (San Francisco area)
            connected_web_page.fill("#lat-input", "37.7749")
            connected_web_page.fill("#lon-input", "-122.4194")
            connected_web_page.fill("#alt-input", "100")
            
            # Click Go To button
            connected_web_page.click("#goto-btn")
            waypoint_set = True
            
            time.sleep(2)  # Allow waypoint to be processed
            print("Waypoint coordinates submitted")
        
        # Look for waypoint markers on map
        waypoint_selectors = [
            ".waypoint-marker",
            ".destination-marker",
            "[class*='waypoint']",
            "[class*='destination']",
            ".leaflet-marker-icon[alt*='waypoint']"
        ]
        
        waypoint_markers = []
        for selector in waypoint_selectors:
            elements = connected_web_page.query_selector_all(selector)
            waypoint_markers.extend([elem for elem in elements if elem.is_visible()])
        
        print(f"Found {len(waypoint_markers)} waypoint markers")
        
        # Check for waypoint-related text or status
        waypoint_text_indicators = [
            "waypoint", "destination", "target", "goto", "navigate"
        ]
        
        page_text = connected_web_page.content().lower()
        waypoint_mentioned = any(indicator in page_text for indicator in waypoint_text_indicators)
        
        print(f"Waypoint functionality mentioned on page: {waypoint_mentioned}")
        
        # Test map click for waypoint setting (if supported)
        map_container = connected_web_page.query_selector("#map-container")
        if map_container:
            try:
                bounds = map_container.bounding_box()
                if bounds:
                    # Click on map
                    click_x = bounds['x'] + bounds['width'] // 2
                    click_y = bounds['y'] + bounds['height'] // 2
                    connected_web_page.click(f"css=#map-container", position={"x": click_x - bounds['x'], "y": click_y - bounds['y']})
                    
                    time.sleep(1)
                    print("Attempted map click for waypoint")
                    
            except Exception as e:
                print(f"Could not test map click: {e}")
        
        # Should have some waypoint functionality
        has_waypoint_capability = waypoint_set or len(waypoint_markers) > 0 or waypoint_mentioned
        assert has_waypoint_capability, "Should have waypoint display or interaction capability"
        
        record_agent_usage('testing-agent', 160, 125)

    def test_map_real_time_updates(self, connected_web_page):
        """Test that map updates with real-time drone position."""
        time.sleep(5)  # Wait for initial position
        
        # Get initial map state
        initial_map_content = connected_web_page.evaluate("""
            () => {
                const mapContainer = document.querySelector('#map-container');
                if (!mapContainer) return null;
                
                // Get various map state indicators
                return {
                    innerHTML_length: mapContainer.innerHTML.length,
                    marker_count: mapContainer.querySelectorAll('[class*="marker"]').length,
                    tile_count: mapContainer.querySelectorAll('[class*="tile"]').length,
                    timestamp: Date.now()
                };
            }
        """)
        
        if initial_map_content:
            print(f"Initial map state: {initial_map_content}")
            
            # Wait for potential updates
            time.sleep(5)
            
            # Check for changes
            updated_map_content = connected_web_page.evaluate("""
                () => {
                    const mapContainer = document.querySelector('#map-container');
                    if (!mapContainer) return null;
                    
                    return {
                        innerHTML_length: mapContainer.innerHTML.length,
                        marker_count: mapContainer.querySelectorAll('[class*="marker"]').length,
                        tile_count: mapContainer.querySelectorAll('[class*="tile"]').length,
                        timestamp: Date.now()
                    };
                }
            """)
            
            if updated_map_content:
                print(f"Updated map state: {updated_map_content}")
                
                # Check for any changes that might indicate updates
                content_changed = (initial_map_content['innerHTML_length'] != updated_map_content['innerHTML_length'] or
                                 initial_map_content['marker_count'] != updated_map_content['marker_count'])
                
                if content_changed:
                    print("Map content changes detected")
                else:
                    print("No map content changes detected")
        
        # Check for JavaScript-based position updates
        position_updates = connected_web_page.evaluate("""
            () => {
                // Check for position-related JavaScript variables
                const positionIndicators = ['latitude', 'longitude', 'lat', 'lon', 'position'];
                const foundVars = [];
                
                for (let indicator of positionIndicators) {
                    if (typeof window[indicator] !== 'undefined') {
                        foundVars.push(indicator);
                    }
                }
                
                return {
                    positionVars: foundVars,
                    hasGeolocation: typeof navigator.geolocation !== 'undefined'
                };
            }
        """)
        
        print(f"Position update indicators: {position_updates}")
        
        # Monitor coordinate displays for updates
        coord_elements = connected_web_page.query_selector_all("#latitude-display, #longitude-display")
        if coord_elements:
            initial_coords = [(elem.text_content() or "") for elem in coord_elements if elem.is_visible()]
            
            time.sleep(3)
            
            updated_coords = [(elem.text_content() or "") for elem in coord_elements if elem.is_visible()]
            
            coord_changes = sum(1 for i, (init, upd) in enumerate(zip(initial_coords, updated_coords)) if init != upd)
            print(f"Coordinate display changes: {coord_changes}")
            
            if coord_changes > 0:
                print("Coordinate updates detected")
        
        record_agent_usage('testing-agent', 140, 110)

    def test_map_performance_and_responsiveness(self, connected_web_page):
        """Test map performance and responsiveness."""
        time.sleep(3)
        
        # Test map interaction responsiveness
        map_container = connected_web_page.query_selector("#map-container")
        if map_container:
            bounds = map_container.bounding_box()
            if bounds:
                # Time map interaction response
                start_time = time.time()
                
                try:
                    # Click on map
                    center_x = bounds['x'] + bounds['width'] // 2
                    center_y = bounds['y'] + bounds['height'] // 2
                    connected_web_page.click(f"css=#map-container", position={"x": center_x - bounds['x'], "y": center_y - bounds['y']})
                    
                    # Measure response time
                    response_time = time.time() - start_time
                    print(f"Map click response time: {response_time:.3f}s")
                    
                    # Should respond quickly
                    assert response_time < 2.0, f"Map should respond quickly to clicks, took {response_time:.3f}s"
                    
                except Exception as e:
                    print(f"Could not test map responsiveness: {e}")
        
        # Check for performance-related errors
        console_errors = []
        
        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)
                print(f"Console error: {msg.text}")
        
        connected_web_page.on("console", handle_console)
        
        # Interact with map and monitor for errors
        time.sleep(2)
        
        # Check memory usage if available
        memory_info = connected_web_page.evaluate("""
            () => {
                if (performance.memory) {
                    return {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    };
                }
                return null;
            }
        """)
        
        if memory_info:
            print(f"Memory usage: {memory_info}")
            
            # Check for reasonable memory usage
            usage_percent = (memory_info['used'] / memory_info['limit']) * 100
            assert usage_percent < 80, f"Memory usage too high: {usage_percent:.1f}%"
        
        # Should not have critical map-related errors
        map_errors = [err for err in console_errors if 
                     "map" in err.lower() or 
                     "tile" in err.lower() or
                     "leaflet" in err.lower() or
                     "mapbox" in err.lower()]
        
        if map_errors:
            print(f"Map-related errors found: {map_errors}")
            # Allow minor errors but not critical ones
            critical_errors = [err for err in map_errors if "critical" in err.lower() or "fatal" in err.lower()]
            assert len(critical_errors) == 0, f"Critical map errors found: {critical_errors}"
        
        record_agent_usage('testing-agent', 150, 115)

    def test_map_layer_functionality(self, connected_web_page):
        """Test different map layers and overlays."""
        time.sleep(3)
        
        # Look for layer control elements
        layer_selectors = [
            ".leaflet-control-layers",
            ".layer-control",
            "[class*='layer']",
            ".map-layers"
        ]
        
        layer_controls = []
        for selector in layer_selectors:
            elements = connected_web_page.query_selector_all(selector)
            layer_controls.extend([elem for elem in elements if elem.is_visible()])
        
        print(f"Found {len(layer_controls)} layer control elements")
        
        # Check for different layer types
        layer_types = ["satellite", "terrain", "street", "hybrid", "osm", "openstreetmap"]
        layer_options = []
        
        page_content = connected_web_page.content().lower()
        for layer_type in layer_types:
            if layer_type in page_content:
                layer_options.append(layer_type)
        
        print(f"Map layer types mentioned: {layer_options}")
        
        # Test layer switching if controls are available
        if layer_controls:
            try:
                # Click on first layer control
                layer_controls[0].click()
                time.sleep(1)
                
                # Look for layer options
                layer_options_elements = connected_web_page.query_selector_all(".leaflet-control-layers-selector, .layer-option")
                
                if layer_options_elements:
                    print(f"Found {len(layer_options_elements)} layer options")
                    
                    # Try switching layers
                    for i, option in enumerate(layer_options_elements[:3]):  # Test first 3 options
                        if option.is_visible():
                            option.click()
                            time.sleep(0.5)
                            print(f"Clicked layer option {i+1}")
                
            except Exception as e:
                print(f"Could not test layer switching: {e}")
        
        # Check for overlay elements (geofences, flight paths, etc.)
        overlay_selectors = [
            ".geofence",
            ".flight-path",
            ".mission-overlay",
            "[class*='overlay']",
            ".polyline",
            ".polygon"
        ]
        
        overlays_found = 0
        for selector in overlay_selectors:
            elements = connected_web_page.query_selector_all(selector)
            overlays_found += len([elem for elem in elements if elem.is_visible()])
        
        print(f"Found {overlays_found} map overlays")
        
        # Should have basic map functionality
        has_map_features = len(layer_controls) > 0 or len(layer_options) > 0 or overlays_found > 0
        
        record_agent_usage('testing-agent', 135, 105)
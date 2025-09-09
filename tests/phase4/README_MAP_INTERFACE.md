# Phase 4 Map Interface Testing

## Overview

This directory contains comprehensive tests for WebGCS map interface functionality using Playwright MCP. The tests validate interactive map controls, drone positioning accuracy, and map-based navigation commands.

## Test Coverage

### Map Interface Tests (TEST-028 to TEST-033)

#### Foundation Test (Implemented)
- **TEST-033**: `test_033_map_interface_foundation.py` - ✅ WORKING
  - Tests current map container placeholder structure
  - Validates map section layout and positioning
  - Verifies basic map container interactivity
  - Confirms space allocation for future map controls

#### Core Map Interface Tests (Ready for Implementation)
- **TEST-028**: `test_028_center_map_button.py` - Awaiting CENTER MAP button implementation
  - Tests CENTER MAP button functionality
  - Validates map centering on drone position
  - Tests button behavior during connection states
  
- **TEST-029**: `test_029_fly_to_toggle_button.py` - Awaiting FLY TO toggle implementation
  - Tests FLY TO mode toggle button (ON/OFF states)
  - Validates click-to-fly functionality on map
  - Tests toggle visual feedback and persistence

- **TEST-030**: `test_030_map_interface.py` - Awaiting full map implementation
  - Tests comprehensive map interactions
  - Validates zoom controls (levels 2-22)
  - Tests layer switching (Street/Satellite)
  - Tests map pan and drag functionality

- **TEST-031**: `test_031_drone_location_map_display.py` - Awaiting drone marker implementation
  - Tests drone marker positioning accuracy
  - Validates marker updates with telemetry
  - Tests heading indicator functionality
  - Tests marker behavior during connection cycles

- **TEST-032**: `test_032_drone_location_map_display_visual.py` - Awaiting visual implementation
  - Tests drone marker styling (blue per PRD)
  - Tests home marker styling (green per PRD)
  - Tests target marker styling (red per PRD)
  - Tests flight path trail visualization
  - Tests marker animations and visual consistency

## Required Map Interface Components

Based on the WebGCS PRD and test specifications, the following components need implementation:

### HTML Elements Needed
```html
<!-- Map Controls -->
<button id="center-map-btn">Center Map</button>
<button id="fly-to-toggle-btn">Fly To: OFF</button>

<!-- Map Layers -->
<button id="street-layer" data-layer="street">Street</button>
<button id="satellite-layer" data-layer="satellite">Satellite</button>

<!-- Zoom Controls (or use Leaflet defaults) -->
<button class="map-zoom-in">+</button>
<button class="map-zoom-out">-</button>

<!-- Offline Maps Panel -->
<div id="offline-maps-panel" class="offline-maps-panel" style="display: none;">
  <button id="download-tiles-btn">Download Tiles</button>
</div>
<button id="offline-maps-toggle">Offline Maps</button>
```

### JavaScript Implementation Needed
```javascript
// Map initialization with Leaflet
const map = L.map('map-display').setView([37.7749, -122.4194], 13);

// Drone marker (blue)
const droneMarker = L.marker([lat, lon], {
  icon: L.divIcon({
    className: 'drone-marker blue-marker',
    html: '<div class="aircraft-icon"></div>'
  })
});

// Home marker (green)  
const homeMarker = L.marker([homeLat, homeLon], {
  icon: L.divIcon({
    className: 'home-marker green-marker',
    html: '<div class="home-icon"></div>'
  })
});

// Target marker (red, pulsing)
const targetMarker = L.marker([targetLat, targetLon], {
  icon: L.divIcon({
    className: 'target-marker red-marker pulsing',
    html: '<div class="target-icon"></div>'
  })
});

// Center Map functionality
document.getElementById('center-map-btn').addEventListener('click', function() {
  if (droneMarker) {
    map.setView(droneMarker.getLatLng(), map.getZoom());
  }
});

// Fly To toggle functionality
let flyToMode = false;
document.getElementById('fly-to-toggle-btn').addEventListener('click', function() {
  flyToMode = !flyToMode;
  this.textContent = flyToMode ? 'Fly To: ON' : 'Fly To: OFF';
  this.classList.toggle('active', flyToMode);
});

// Click-to-fly functionality
map.on('click', function(e) {
  if (flyToMode) {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;
    
    // Create/update target marker
    if (targetMarker) {
      targetMarker.setLatLng(e.latlng);
    }
    
    // Send navigation command
    socket.emit('send_command', {
      command: 'MAV_CMD_NAV_WAYPOINT',
      params: [0, 0, 0, 0, lat, lon, alt]
    });
  }
});
```

### CSS Styling Needed
```css
/* Map markers per PRD requirements */
.drone-marker.blue-marker {
  background-color: blue;
  border-radius: 50%;
}

.home-marker.green-marker {
  background-color: green;
  border-radius: 50%;
}

.target-marker.red-marker {
  background-color: red;
  border-radius: 50%;
}

.target-marker.pulsing {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
  100% { opacity: 1; transform: scale(1); }
}

/* Map controls */
#center-map-btn, #fly-to-toggle-btn {
  margin: 5px;
  padding: 8px 16px;
  border: 1px solid #ccc;
  background: #f8f9fa;
  cursor: pointer;
}

#fly-to-toggle-btn.active {
  background: #28a745;
  color: white;
}
```

## Test Execution

### Run Foundation Test (Working Now)
```bash
# Test current map structure
uv run python -m pytest tests/phase4/test_033_map_interface_foundation.py -v

# Quick validation
uv run python -m pytest tests/phase4/test_033_map_interface_foundation.py::TestMapInterfaceFoundation::test_map_container_exists -v
```

### Run Full Map Interface Tests (After Implementation)
```bash
# Run all map interface tests
uv run python tests/phase4/test_runner_phase4_map_interface.py

# Run specific test category
uv run python -m pytest tests/phase4/test_028_center_map_button.py -v
uv run python -m pytest tests/phase4/test_029_fly_to_toggle_button.py -v
uv run python -m pytest tests/phase4/test_030_map_interface.py -v
uv run python -m pytest tests/phase4/test_031_drone_location_map_display.py -v
uv run python -m pytest tests/phase4/test_032_drone_location_map_display_visual.py -v

# Run complete Phase 4 including map tests
uv run python tests/phase4/test_runner_phase4_complete.py
```

## Integration with WebGCS Architecture

### File Structure Integration
```
static/js/
├── map-controller.js           # Main map functionality (needs creation)
├── map-markers.js             # Drone/home/target markers (needs creation)
├── map-controls.js            # Center/fly-to controls (needs creation)
└── main.js                    # Import map modules

templates/
├── index.html                 # Add map control buttons
└── components/
    └── map_controls.html      # Map control panel (needs creation)
```

### Integration Points

1. **Telemetry Updates**: Map markers should update with `drone_status` SocketIO events
2. **Navigation Commands**: Click-to-fly should use existing `send_command` SocketIO event
3. **Connection State**: Map controls should respect drone connection status
4. **Coordinate Validation**: Use existing navigation input validation logic

## Current Status

- ✅ **Foundation Test**: Validates current HTML structure and layout
- ⏳ **Core Tests**: Ready for implementation, waiting for map interface components
- 📋 **Requirements**: Detailed component specifications provided above
- 🧪 **Test Coverage**: Comprehensive Playwright MCP tests for all map functionality

## Next Steps

1. Implement map controls in HTML template
2. Create map-controller.js with Leaflet integration
3. Add drone marker positioning with telemetry updates
4. Implement click-to-fly functionality
5. Add visual styling for markers and controls
6. Run full test suite to validate implementation

The tests are designed to be robust and will work once the map interface components are implemented according to the specifications above.
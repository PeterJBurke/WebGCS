/**
 * MAP INTERFACE CONSOLE TESTING SCRIPT
 * Run this in browser console to test map functionality
 */

// Test Map Interface Functionality
function testMapInterface() {
    console.log('🔍 TESTING MAP INTERFACE FUNCTIONALITY');
    console.log('=====================================');
    
    const results = {
        tests: [],
        passed: 0,
        failed: 0
    };
    
    function addTest(name, passed, details) {
        results.tests.push({ name, passed, details });
        if (passed) {
            results.passed++;
            console.log(`✅ ${name}: PASSED - ${details}`);
        } else {
            results.failed++;
            console.log(`❌ ${name}: FAILED - ${details}`);
        }
    }
    
    // TEST 1: Check Leaflet Library
    const leafletLoaded = typeof window.L !== 'undefined';
    addTest(
        'Leaflet Library', 
        leafletLoaded, 
        leafletLoaded ? `Version: ${L.version}` : 'Leaflet not found'
    );
    
    // TEST 2: Check MapController Module
    const mapControllerLoaded = typeof window.MapController !== 'undefined';
    addTest(
        'MapController Module',
        mapControllerLoaded,
        mapControllerLoaded ? 'MapController object found' : 'MapController not found'
    );
    
    // TEST 3: Check Map Container
    const mapDiv = document.getElementById('map');
    const mapContainerExists = mapDiv !== null;
    addTest(
        'Map Container',
        mapContainerExists,
        mapContainerExists ? `Size: ${mapDiv.offsetWidth}x${mapDiv.offsetHeight}` : 'Map div not found'
    );
    
    // TEST 4: Check Map Instance
    const mapInstance = mapDiv && mapDiv._leaflet_id ? window.L.map._map || mapDiv._leaflet : null;
    const mapInstanceExists = mapInstance !== null;
    addTest(
        'Map Instance',
        mapInstanceExists,
        mapInstanceExists ? `Leaflet ID: ${mapDiv._leaflet_id}` : 'Map not initialized'
    );
    
    // TEST 5: Check Center Map Button
    const centerBtn = document.getElementById('center-map-btn');
    const centerBtnExists = centerBtn !== null && centerBtn.offsetParent !== null;
    addTest(
        'Center Map Button',
        centerBtnExists,
        centerBtnExists ? `Text: "${centerBtn.textContent}", Enabled: ${!centerBtn.disabled}` : 'Button not found or hidden'
    );
    
    // TEST 6: Check Fly To Toggle
    const flyToBtn = document.getElementById('fly-to-toggle');
    const flyToBtnExists = flyToBtn !== null && flyToBtn.offsetParent !== null;
    addTest(
        'Fly To Toggle',
        flyToBtnExists,
        flyToBtnExists ? `Text: "${flyToBtn.textContent}", Active: ${flyToBtn.getAttribute('data-active')}` : 'Button not found or hidden'
    );
    
    // TEST 7: Check WebGCS Integration
    const webgcsExists = typeof window.WebGCS !== 'undefined';
    const mapModuleRegistered = webgcsExists && window.WebGCS.modules && window.WebGCS.modules.MapController;
    addTest(
        'WebGCS Integration',
        mapModuleRegistered,
        mapModuleRegistered ? 'MapController registered in WebGCS' : 'MapController not in WebGCS.modules'
    );
    
    // TEST 8: Map Functionality Tests (if map exists)
    if (mapInstance) {
        try {
            const currentCenter = mapInstance.getCenter();
            const currentZoom = mapInstance.getZoom();
            addTest(
                'Map API Access',
                true,
                `Center: [${currentCenter.lat.toFixed(4)}, ${currentCenter.lng.toFixed(4)}], Zoom: ${currentZoom}`
            );
            
            // Test map bounds
            const bounds = mapInstance.getBounds();
            addTest(
                'Map Bounds',
                bounds !== null,
                `North: ${bounds.getNorth().toFixed(4)}, South: ${bounds.getSouth().toFixed(4)}`
            );
            
        } catch (error) {
            addTest('Map API Access', false, `Error: ${error.message}`);
        }
    }
    
    // TEST 9: Check for Markers
    if (mapInstance) {
        let markerCount = 0;
        mapInstance.eachLayer(function(layer) {
            if (layer instanceof L.Marker) {
                markerCount++;
            }
        });
        addTest(
            'Map Markers',
            true,
            `Found ${markerCount} markers on map`
        );
    }
    
    // TEST 10: Check Layer Control
    const layerControl = document.querySelector('.leaflet-control-layers');
    const layerControlExists = layerControl !== null;
    addTest(
        'Layer Control',
        layerControlExists,
        layerControlExists ? 'Layer control found' : 'Layer control not found'
    );
    
    // Print summary
    console.log('\\n📊 TEST SUMMARY');
    console.log('================');
    console.log(`Total Tests: ${results.tests.length}`);
    console.log(`✅ Passed: ${results.passed}`);
    console.log(`❌ Failed: ${results.failed}`);
    console.log(`Success Rate: ${((results.passed / results.tests.length) * 100).toFixed(1)}%`);
    
    return results;
}

// Test individual map functions
function testMapFunctions() {
    console.log('\\n🔧 TESTING MAP FUNCTIONS');
    console.log('=========================');
    
    // Test Center Map
    if (window.MapController && typeof window.MapController.centerMap === 'function') {
        console.log('Testing centerMap function...');
        try {
            window.MapController.centerMap();
            console.log('✅ centerMap executed successfully');
        } catch (error) {
            console.log(`❌ centerMap failed: ${error.message}`);
        }
    }
    
    // Test Fly To Toggle
    if (window.MapController && typeof window.MapController.isFlyToActive === 'function') {
        console.log(`Current fly-to status: ${window.MapController.isFlyToActive()}`);
    }
    
    // Test Map Bounds
    if (window.MapController && typeof window.MapController.getMapBounds === 'function') {
        try {
            const bounds = window.MapController.getMapBounds();
            console.log('Map bounds:', bounds);
        } catch (error) {
            console.log(`❌ getMapBounds failed: ${error.message}`);
        }
    }
    
    // Test Telemetry Integration
    if (window.WebGCS && window.WebGCS.telemetryData) {
        console.log('Current telemetry:', {
            lat: window.WebGCS.telemetryData.lat,
            lon: window.WebGCS.telemetryData.lon,
            heading: window.WebGCS.telemetryData.heading,
            connected: window.WebGCS.telemetryData.connected
        });
    }
}

// Simulate map click
function simulateMapClick(lat = 37.776, lng = -122.418) {
    console.log(`\\n🖱️  SIMULATING MAP CLICK AT [${lat}, ${lng}]`);
    
    const mapDiv = document.getElementById('map');
    if (!mapDiv) {
        console.log('❌ Map container not found');
        return;
    }
    
    if (!mapDiv._leaflet_id) {
        console.log('❌ Map not initialized');
        return;
    }
    
    // Get map instance
    const map = L.map._map || mapDiv._leaflet;
    if (!map) {
        console.log('❌ Could not access map instance');
        return;
    }
    
    try {
        // Convert lat/lng to pixel coordinates
        const point = map.latLngToContainerPoint([lat, lng]);
        console.log(`Pixel coordinates: x=${point.x}, y=${point.y}`);
        
        // Create and dispatch click event
        const clickEvent = new MouseEvent('click', {
            bubbles: true,
            cancelable: true,
            clientX: point.x,
            clientY: point.y
        });
        
        mapDiv.dispatchEvent(clickEvent);
        console.log('✅ Map click event dispatched');
        
        // Also trigger the Leaflet click event directly
        map.fire('click', {
            latlng: L.latLng(lat, lng),
            layerPoint: point,
            containerPoint: point
        });
        console.log('✅ Leaflet click event fired');
        
    } catch (error) {
        console.log(`❌ Click simulation failed: ${error.message}`);
    }
}

// Button click tests
function testButtonClicks() {
    console.log('\\n🔘 TESTING BUTTON CLICKS');
    console.log('==========================');
    
    // Test Center Map button
    const centerBtn = document.getElementById('center-map-btn');
    if (centerBtn) {
        console.log('Clicking Center Map button...');
        centerBtn.click();
        console.log('✅ Center Map button clicked');
    } else {
        console.log('❌ Center Map button not found');
    }
    
    // Test Fly To toggle
    const flyToBtn = document.getElementById('fly-to-toggle');
    if (flyToBtn) {
        const initialState = flyToBtn.textContent;
        console.log(`Initial Fly-To state: ${initialState}`);
        
        flyToBtn.click();
        setTimeout(() => {
            const newState = flyToBtn.textContent;
            console.log(`New Fly-To state: ${newState}`);
            console.log('✅ Fly To toggle clicked');
        }, 100);
    } else {
        console.log('❌ Fly To button not found');
    }
}

// Export functions for manual testing
window.mapTest = {
    testMapInterface,
    testMapFunctions,
    simulateMapClick,
    testButtonClicks
};

console.log('🚀 Map testing functions loaded!');
console.log('Run mapTest.testMapInterface() to start testing');
console.log('Available functions:');
console.log('- mapTest.testMapInterface()  // Complete interface test');
console.log('- mapTest.testMapFunctions()  // Test map functions');
console.log('- mapTest.simulateMapClick()  // Simulate map click');
console.log('- mapTest.testButtonClicks()  // Test button clicks');
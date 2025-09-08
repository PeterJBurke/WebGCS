/**
 * WebGCS Map Controller Module
 * Handles Leaflet map integration with drone positioning and click-to-fly
 */

window.MapController = (function() {
    'use strict';
    
    // Private variables
    let map = null;
    let markers = {};
    let layers = {};
    let flyToMode = false;
    let isConnected = false;
    let currentPosition = { lat: 0, lon: 0 };
    let homePosition = { lat: 0, lon: 0 };
    
    // DOM elements
    let elements = {};
    
    // Map configuration
    const MAP_CONFIG = {
        defaultCenter: [37.7749, -122.4194], // San Francisco
        defaultZoom: 10,
        minZoom: 2,
        maxZoom: 22
    };
    
    /**
     * Initialize Map Controller
     */
    function initialize() {
        console.log('Initializing Map Controller...');
        
        // Cache DOM elements
        cacheElements();
        
        // Initialize map
        initializeMap();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize UI state
        updateControlsState();
        
        console.log('Map Controller initialized');
    }
    
    /**
     * Cache DOM Elements
     */
    function cacheElements() {
        elements = {
            mapDiv: document.getElementById('map'),
            centerMapBtn: document.getElementById('center-map-btn'),
            flyToToggle: document.getElementById('fly-to-toggle'),
            offlineMapsToggle: document.getElementById('offline-maps-toggle')
        };
        
        // Check for missing elements
        Object.entries(elements).forEach(([key, element]) => {
            if (!element) {
                console.warn(`Map Controller: Element '${key}' not found`);
            }
        });
    }
    
    /**
     * Initialize Leaflet Map
     */
    function initializeMap() {
        if (!elements.mapDiv) {
            console.error('Map container not found');
            return;
        }
        
        try {
            // Create map instance
            map = L.map(elements.mapDiv, {
                center: MAP_CONFIG.defaultCenter,
                zoom: MAP_CONFIG.defaultZoom,
                minZoom: MAP_CONFIG.minZoom,
                maxZoom: MAP_CONFIG.maxZoom,
                zoomControl: true
            });
            
            // Add base layers
            addBaseLayers();
            
            // Add layer control
            addLayerControl();
            
            // Initialize markers
            initializeMarkers();
            
            // Setup map event listeners
            setupMapEvents();
            
            console.log('Leaflet map initialized');
        } catch (error) {
            console.error('Failed to initialize map:', error);
            if (elements.mapDiv) {
                elements.mapDiv.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Map initialization failed</div>';
            }
        }
    }
    
    /**
     * Add Base Map Layers
     */
    function addBaseLayers() {
        // OpenStreetMap layer
        layers.street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        });
        
        // Satellite layer (Esri World Imagery)
        layers.satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© Esri, Maxar, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community',
            maxZoom: 19
        });
        
        // Add default layer
        layers.street.addTo(map);
    }
    
    /**
     * Add Layer Control
     */
    function addLayerControl() {
        const baseLayers = {
            "Street Map": layers.street,
            "Satellite": layers.satellite
        };
        
        const layerControl = L.control.layers(baseLayers, null, {
            position: 'topleft',
            collapsed: false
        });
        
        layerControl.addTo(map);
    }
    
    /**
     * Initialize Map Markers
     */
    function initializeMarkers() {
        // Drone marker (blue arrow)
        const droneIcon = L.divIcon({
            html: '<div style="transform: rotate(0deg); color: #007bff; font-size: 24px;">▲</div>',
            className: 'drone-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        
        markers.drone = L.marker(MAP_CONFIG.defaultCenter, { 
            icon: droneIcon,
            title: 'Drone Position'
        });
        
        // Home marker (green house)
        const homeIcon = L.divIcon({
            html: '<div style="color: #28a745; font-size: 20px;">🏠</div>',
            className: 'home-marker',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        
        markers.home = L.marker(MAP_CONFIG.defaultCenter, {
            icon: homeIcon,
            title: 'Home Position'
        });
        
        // Target marker (red bullseye with pulse animation)
        const targetIcon = L.divIcon({
            html: '<div style="color: #dc3545; font-size: 20px;" class="pulse-animation">🎯</div>',
            className: 'target-marker',
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        
        markers.target = L.marker(MAP_CONFIG.defaultCenter, {
            icon: targetIcon,
            title: 'Navigation Target'
        });
        
        // Add CSS for pulse animation
        addPulseAnimation();
    }
    
    /**
     * Add Pulse Animation CSS
     */
    function addPulseAnimation() {
        if (!document.getElementById('map-animations')) {
            const style = document.createElement('style');
            style.id = 'map-animations';
            style.textContent = `
                @keyframes pulse {
                    0% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.2); opacity: 0.7; }
                    100% { transform: scale(1); opacity: 1; }
                }
                .pulse-animation {
                    animation: pulse 2s infinite;
                }
                .drone-marker {
                    transition: transform 0.3s ease;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    /**
     * Setup Map Event Listeners
     */
    function setupMapEvents() {
        if (!map) return;
        
        // Map click event
        map.on('click', handleMapClick);
        
        // Map move events for updating offline maps area
        map.on('moveend zoomend', handleMapViewChange);
    }
    
    /**
     * Setup UI Event Listeners
     */
    function setupEventListeners() {
        // Center map button
        if (elements.centerMapBtn) {
            elements.centerMapBtn.addEventListener('click', centerMap);
        }
        
        // Fly to toggle button
        if (elements.flyToToggle) {
            elements.flyToToggle.addEventListener('click', toggleFlyToMode);
        }
        
        // Offline maps toggle button
        if (elements.offlineMapsToggle) {
            elements.offlineMapsToggle.addEventListener('click', toggleOfflineMapsPanel);
        }
        
        // Listen for global events
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('telemetry_updated', handleTelemetryUpdate);
            window.WebGCS.eventBus.addEventListener('connection_changed', handleConnectionChange);
        }
    }
    
    /**
     * Handle Map Click
     */
    function handleMapClick(event) {
        const { lat, lng } = event.latlng;
        
        console.log(`Map clicked at: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
        
        // Emit map click event for other modules
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.dispatchEvent(new CustomEvent('map_clicked', {
                detail: { lat, lon: lng }
            }));
        }
        
        // Handle fly-to mode
        if (flyToMode) {
            setTarget(lat, lng);
            
            // Auto-execute navigation if connected
            if (isConnected && window.WebGCS?.modules?.NavigationControls?.setCoordinates) {
                window.WebGCS.modules.NavigationControls.setCoordinates(lat, lng);
                window.WebGCS?.showMessage(`Target set: ${lat.toFixed(6)}, ${lng.toFixed(6)}`, 'info');
            }
        }
    }
    
    /**
     * Handle Map View Change
     */
    function handleMapViewChange() {
        // Update offline maps area if panel is open
        if (window.WebGCS?.modules?.OfflineMaps?.updateCurrentMapView) {
            window.WebGCS.modules.OfflineMaps.updateCurrentMapView(map.getBounds(), map.getZoom());
        }
    }
    
    /**
     * Center Map on Drone
     */
    function centerMap() {
        if (!map) return;
        
        if (isConnected && currentPosition.lat !== 0 && currentPosition.lon !== 0) {
            map.setView([currentPosition.lat, currentPosition.lon], map.getZoom());
            window.WebGCS?.showMessage('Map centered on drone', 'info');
        } else {
            window.WebGCS?.showMessage('No drone position available', 'warning');
        }
    }
    
    /**
     * Toggle Fly-To Mode
     */
    function toggleFlyToMode() {
        flyToMode = !flyToMode;
        
        if (elements.flyToToggle) {
            elements.flyToToggle.setAttribute('data-active', flyToMode.toString());
            elements.flyToToggle.textContent = flyToMode ? 'Fly To: ON' : 'Fly To: OFF';
            elements.flyToToggle.className = flyToMode 
                ? 'btn btn-success' 
                : 'btn btn-secondary';
        }
        
        // Update map cursor
        if (map && elements.mapDiv) {
            elements.mapDiv.style.cursor = flyToMode ? 'crosshair' : '';
        }
        
        const status = flyToMode ? 'enabled' : 'disabled';
        window.WebGCS?.showMessage(`Fly-to mode ${status}`, 'info');
        
        console.log('Fly-to mode:', flyToMode);
    }
    
    /**
     * Toggle Offline Maps Panel
     */
    function toggleOfflineMapsPanel() {
        const panel = document.getElementById('offline-maps-panel');
        if (panel) {
            panel.classList.toggle('active');
        }
    }
    
    /**
     * Update Drone Position
     */
    function updateDronePosition(lat, lon, heading = 0) {
        if (!map || !markers.drone) return;
        
        // Check if this is the first valid position (drone was at 0,0 or unset)
        const isFirstValidPosition = (currentPosition.lat === 0 && currentPosition.lon === 0) || 
                                   (Math.abs(currentPosition.lat) < 0.001 && Math.abs(currentPosition.lon) < 0.001);
        
        currentPosition = { lat, lon };
        
        // Update marker position
        markers.drone.setLatLng([lat, lon]);
        
        // Update drone icon rotation based on heading
        const droneIcon = L.divIcon({
            html: `<div style="transform: rotate(${heading}deg); color: #007bff; font-size: 24px;">▲</div>`,
            className: 'drone-marker',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        markers.drone.setIcon(droneIcon);
        
        // Add to map if not already added
        if (!map.hasLayer(markers.drone)) {
            markers.drone.addTo(map);
        }
        
        // **FIX: Auto-center map on drone location when first valid position is received**
        if (isFirstValidPosition && lat !== 0 && lon !== 0) {
            console.log(`Auto-centering map on drone position: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
            map.setView([lat, lon], 15); // Zoom level 15 for good detail
        }
        
        // Update tooltip (with safety check)
        try {
            if (markers.drone && markers.drone.setTooltip) {
                markers.drone.setTooltip(`Drone: ${lat.toFixed(6)}, ${lon.toFixed(6)}<br>Heading: ${heading.toFixed(1)}°`);
            }
        } catch (error) {
            console.error('Error setting drone tooltip:', error);
        }
    }
    
    /**
     * Update Home Position
     */
    function updateHomePosition(lat, lon) {
        if (!map || !markers.home) return;
        
        homePosition = { lat, lon };
        
        // Update marker position
        markers.home.setLatLng([lat, lon]);
        
        // Add to map if not already added
        if (!map.hasLayer(markers.home)) {
            markers.home.addTo(map);
        }
        
        // Update tooltip
        markers.home.setTooltip(`Home: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
    }
    
    /**
     * Set Navigation Target
     */
    function setTarget(lat, lon) {
        if (!map || !markers.target) return;
        
        // Update marker position
        markers.target.setLatLng([lat, lon]);
        
        // Add to map if not already added
        if (!map.hasLayer(markers.target)) {
            markers.target.addTo(map);
        }
        
        // Update tooltip
        markers.target.setTooltip(`Target: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
        
        console.log(`Target set at: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
    }
    
    /**
     * Clear Navigation Target
     */
    function clearTarget() {
        if (map && markers.target && map.hasLayer(markers.target)) {
            map.removeLayer(markers.target);
        }
    }
    
    /**
     * Update Controls State
     */
    function updateControlsState() {
        if (elements.centerMapBtn) {
            elements.centerMapBtn.disabled = false; // Always enabled
        }
        
        if (elements.flyToToggle) {
            elements.flyToToggle.disabled = false; // Always enabled
        }
        
        if (elements.offlineMapsToggle) {
            elements.offlineMapsToggle.disabled = false; // Always enabled
        }
    }
    
    /**
     * Get Map Bounds
     */
    function getMapBounds() {
        if (!map) return null;
        
        const bounds = map.getBounds();
        return {
            north: bounds.getNorth(),
            south: bounds.getSouth(),
            east: bounds.getEast(),
            west: bounds.getWest(),
            zoom: map.getZoom()
        };
    }
    
    /**
     * Event Handlers
     */
    function handleTelemetryUpdate(event) {
        const data = event.detail || event;
        
        if (!data) return;
        
        // Update drone position
        if (data.lat && data.lon) {
            const heading = data.heading || 0;
            updateDronePosition(data.lat, data.lon, heading);
        }
        
        // Update home position if available
        if (data.home_lat && data.home_lon) {
            updateHomePosition(data.home_lat, data.home_lon);
        }
    }
    
    function handleConnectionChange(event) {
        const data = event.detail || event;
        isConnected = data ? data.connected : false;
        
        if (!isConnected) {
            // Hide markers on disconnect
            if (map && markers.drone && map.hasLayer(markers.drone)) {
                map.removeLayer(markers.drone);
            }
            if (map && markers.home && map.hasLayer(markers.home)) {
                map.removeLayer(markers.home);
            }
        }
    }
    
    /**
     * Handle Window Resize
     */
    function handleResize() {
        if (map) {
            // Trigger map resize
            setTimeout(() => {
                map.invalidateSize();
            }, 100);
        }
    }
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        
        // Map control methods
        centerMap: centerMap,
        setTarget: setTarget,
        clearTarget: clearTarget,
        getMapBounds: getMapBounds,
        
        // State getters
        isFlyToActive: () => flyToMode,
        getCurrentPosition: () => ({ ...currentPosition }),
        getHomePosition: () => ({ ...homePosition }),
        getMap: () => map,
        
        // Module lifecycle callbacks
        onTelemetryUpdate: handleTelemetryUpdate,
        onConnectionChange: handleConnectionChange,
        onResize: handleResize
    };
})();
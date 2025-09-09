/**
 * Interactive Map for WebGCS
 * Provides real-time drone tracking and click-to-navigate functionality
 * File size: Must stay under 200 lines per WebGCS PRD
 */

class InteractiveMap {
    constructor(mapId) {
        this.mapElement = document.getElementById(mapId);
        this.map = null;
        this.droneMarker = null;
        this.waypointMarkers = [];
        this.telemetryData = {};
        this.isConnected = false;
        
        // Default map center (can be updated with drone position)
        this.defaultLat = 37.7749;
        this.defaultLon = -122.4194;
        
        this.initializeMap();
        this.initializeTelemetry();
    }
    
    initializeMap() {
        // Create Leaflet map
        this.map = L.map(this.mapElement.id).setView([this.defaultLat, this.defaultLon], 15);
        
        // Add OpenStreetMap tiles (works offline if cached)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        // Add map click handler for navigation
        this.map.on('click', (e) => this.handleMapClick(e));
        
        // Add scale control
        L.control.scale().addTo(this.map);
    }
    
    initializeTelemetry() {
        // Listen for telemetry updates
        if (typeof socket !== 'undefined') {
            socket.on('telemetry_stream', (data) => {
                this.telemetryData = data;
                this.isConnected = data.connected;
                this.updateDronePosition();
            });
        }
    }
    
    updateDronePosition() {
        if (!this.isConnected || !this.telemetryData.lat || !this.telemetryData.lon) {
            return;
        }
        
        const lat = this.telemetryData.lat;
        const lon = this.telemetryData.lon;
        const heading = this.telemetryData.heading || 0;
        const altitude = this.telemetryData.alt || 0;
        const armed = this.telemetryData.armed || false;
        
        // Create or update drone marker
        if (!this.droneMarker) {
            // Create custom drone icon
            const droneIcon = L.divIcon({
                className: 'drone-marker',
                html: this.createDroneIconHTML(heading, armed),
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
            
            this.droneMarker = L.marker([lat, lon], { icon: droneIcon })
                .addTo(this.map)
                .bindPopup(`
                    <b>Drone Position</b><br>
                    Lat: ${lat.toFixed(6)}<br>
                    Lon: ${lon.toFixed(6)}<br>
                    Alt: ${altitude.toFixed(1)}m<br>
                    Hdg: ${heading.toFixed(1)}°<br>
                    Status: ${armed ? 'ARMED' : 'DISARMED'}
                `);
        } else {
            // Update existing marker
            this.droneMarker.setLatLng([lat, lon]);
            this.droneMarker.setIcon(L.divIcon({
                className: 'drone-marker',
                html: this.createDroneIconHTML(heading, armed),
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            }));
            
            // Update popup
            this.droneMarker.setPopupContent(`
                <b>Drone Position</b><br>
                Lat: ${lat.toFixed(6)}<br>
                Lon: ${lon.toFixed(6)}<br>
                Alt: ${altitude.toFixed(1)}m<br>
                Hdg: ${heading.toFixed(1)}°<br>
                Status: ${armed ? 'ARMED' : 'DISARMED'}
            `);
        }
        
        // Auto-center map on first position update
        if (!this.hasInitialPosition) {
            this.map.setView([lat, lon], 17);
            this.hasInitialPosition = true;
        }
    }
    
    createDroneIconHTML(heading, armed) {
        const color = armed ? '#ff0000' : '#00ff00';
        const transform = `rotate(${heading}deg)`;
        
        return `
            <div style="
                width: 100%; 
                height: 100%; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                transform: ${transform};
            ">
                <div style="
                    width: 0; 
                    height: 0; 
                    border-left: 10px solid transparent;
                    border-right: 10px solid transparent;
                    border-bottom: 20px solid ${color};
                "></div>
            </div>
        `;
    }
    
    handleMapClick(e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;
        
        // Create temporary waypoint marker
        const waypointMarker = L.marker([lat, lon])
            .addTo(this.map)
            .bindPopup(`
                <b>Waypoint</b><br>
                Lat: ${lat.toFixed(6)}<br>
                Lon: ${lon.toFixed(6)}<br>
                <button onclick="window.mapInstance.navigateToWaypoint(${lat}, ${lon})">Go To</button>
                <button onclick="window.mapInstance.removeWaypoint(this)">Remove</button>
            `)
            .openPopup();
        
        this.waypointMarkers.push(waypointMarker);
        
        // Auto-populate navigation fields if they exist
        this.populateNavigationFields(lat, lon);
    }
    
    populateNavigationFields(lat, lon) {
        const latField = document.getElementById('nav-lat');
        const lonField = document.getElementById('nav-lon');
        
        if (latField && lonField) {
            latField.value = lat.toFixed(6);
            lonField.value = lon.toFixed(6);
        }
    }
    
    navigateToWaypoint(lat, lon) {
        // Send navigation command via existing navigation system
        if (typeof socket !== 'undefined') {
            const altitude = document.getElementById('nav-alt')?.value || 10;
            
            // Use the existing navigation button click handler
            const gotoBtn = document.getElementById('goto-btn');
            if (gotoBtn) {
                // Populate fields and trigger navigation
                this.populateNavigationFields(lat, lon);
                gotoBtn.click();
            }
        }
    }
    
    removeWaypoint(markerReference) {
        // Find and remove the marker (simplified approach)
        this.waypointMarkers.forEach((marker, index) => {
            if (marker.getPopup().getElement().contains(markerReference)) {
                this.map.removeLayer(marker);
                this.waypointMarkers.splice(index, 1);
            }
        });
    }
    
    clearAllWaypoints() {
        this.waypointMarkers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.waypointMarkers = [];
    }
    
    centerOnDrone() {
        if (this.droneMarker) {
            const pos = this.droneMarker.getLatLng();
            this.map.setView([pos.lat, pos.lng], 17);
        }
    }
    
    setMapStyle(style) {
        // Allow switching between map styles
        const styles = {
            'street': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            'satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'terrain': 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png'
        };
        
        if (styles[style]) {
            // Remove existing tile layer and add new one
            this.map.eachLayer(layer => {
                if (layer instanceof L.TileLayer) {
                    this.map.removeLayer(layer);
                }
            });
            
            L.tileLayer(styles[style], {
                attribution: '© Map providers',
                maxZoom: 19
            }).addTo(this.map);
        }
    }
    
    getMapInfo() {
        return {
            center: this.map.getCenter(),
            zoom: this.map.getZoom(),
            dronePosition: this.droneMarker ? this.droneMarker.getLatLng() : null,
            waypointCount: this.waypointMarkers.length,
            connected: this.isConnected
        };
    }
}

// Global map instance
let mapInstance = null;

// Make it available globally for popup buttons
window.mapInstance = null;

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('map-display')) {
        mapInstance = new InteractiveMap('map-display');
        window.mapInstance = mapInstance;
    }
});

// Add map control buttons if they exist
document.addEventListener('DOMContentLoaded', function() {
    // Add center on drone button functionality
    const centerBtn = document.getElementById('center-drone-btn');
    if (centerBtn && mapInstance) {
        centerBtn.addEventListener('click', () => mapInstance.centerOnDrone());
    }
    
    // Add clear waypoints button functionality
    const clearBtn = document.getElementById('clear-waypoints-btn');
    if (clearBtn && mapInstance) {
        clearBtn.addEventListener('click', () => mapInstance.clearAllWaypoints());
    }
});
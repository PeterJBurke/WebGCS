/**
 * WebGCS Navigation Controls Module
 * Handles coordinate-based navigation and Go To commands
 */

window.NavigationControls = (function() {
    'use strict';
    
    // Private variables
    let isConnected = false;
    let currentPosition = { lat: 0, lon: 0, alt: 0 };
    
    // DOM elements
    let elements = {};
    
    /**
     * Initialize Navigation Controls
     */
    function initialize() {
        console.log('Initializing Navigation Controls...');
        
        // Cache DOM elements
        cacheElements();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize UI state
        updateControlsState();
        
        console.log('Navigation Controls initialized');
    }
    
    /**
     * Cache DOM Elements
     */
    function cacheElements() {
        elements = {
            navLat: document.getElementById('nav-lat'),
            navLon: document.getElementById('nav-lon'),
            navAlt: document.getElementById('nav-alt'),
            gotoBtn: document.getElementById('goto-btn'),
            clearNavBtn: document.getElementById('clear-nav-btn'),
            requestFenceBtn: document.getElementById('request-fence-btn'),
            requestMissionBtn: document.getElementById('request-mission-btn')
        };
        
        // Check for missing elements
        Object.entries(elements).forEach(([key, element]) => {
            if (!element) {
                console.warn(`Navigation Controls: Element '${key}' not found`);
            }
        });
    }
    
    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // Go To button
        if (elements.gotoBtn) {
            elements.gotoBtn.addEventListener('click', handleGoTo);
        }
        
        // Clear navigation button
        if (elements.clearNavBtn) {
            elements.clearNavBtn.addEventListener('click', handleClearNav);
        }
        
        // Request buttons
        if (elements.requestFenceBtn) {
            elements.requestFenceBtn.addEventListener('click', handleRequestFence);
        }
        
        if (elements.requestMissionBtn) {
            elements.requestMissionBtn.addEventListener('click', handleRequestMission);
        }
        
        // Input validation
        if (elements.navLat) {
            elements.navLat.addEventListener('input', validateLatitudeInput);
            elements.navLat.addEventListener('blur', formatLatitudeInput);
        }
        
        if (elements.navLon) {
            elements.navLon.addEventListener('input', validateLongitudeInput);
            elements.navLon.addEventListener('blur', formatLongitudeInput);
        }
        
        if (elements.navAlt) {
            elements.navAlt.addEventListener('input', validateAltitudeInput);
        }
        
        // Listen for global events
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('telemetry_updated', handleTelemetryUpdate);
            window.WebGCS.eventBus.addEventListener('connection_changed', handleConnectionChange);
            window.WebGCS.eventBus.addEventListener('command_result', handleCommandResult);
        }
        
        // Listen for map click events (for fly-to functionality)
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('map_clicked', handleMapClick);
        }
    }
    
    /**
     * Handle Go To Command
     */
    function handleGoTo() {
        if (!isConnected) {
            window.WebGCS?.showMessage('Not connected to drone', 'error');
            return;
        }
        
        // Get and validate coordinates
        const coords = getNavigationCoordinates();
        if (!coords) return;
        
        // Confirm navigation command
        const message = `Navigate to:\nLat: ${coords.lat.toFixed(6)}\nLon: ${coords.lon.toFixed(6)}\nAlt: ${coords.alt}m AGL`;
        
        if (window.WebGCS?.showConfirmation) {
            window.WebGCS.showConfirmation('Navigate to Coordinates', message, (confirmed) => {
                if (confirmed) {
                    executeGoToCommand(coords);
                } else {
                    window.WebGCS.showMessage('Navigation command cancelled', 'info');
                }
            });
        } else {
            if (confirm(`Navigate to Coordinates\n\n${message}`)) {
                executeGoToCommand(coords);
            }
        }
    }
    
    /**
     * Execute Go To Command
     */
    function executeGoToCommand(coords) {
        console.log('Executing Go To command:', coords);
        
        // Disable button during command execution
        if (elements.gotoBtn) {
            elements.gotoBtn.disabled = true;
            elements.gotoBtn.textContent = 'Sending...';
        }
        
        // Send goto command
        if (window.WebGCS?.sendCommand) {
            window.WebGCS.sendCommand('goto', {
                lat: coords.lat,
                lon: coords.lon,
                alt: coords.alt
            });
        }
        
        // Update map target if map controller exists
        if (window.WebGCS?.modules?.MapController?.setTarget) {
            window.WebGCS.modules.MapController.setTarget(coords.lat, coords.lon);
        }
        
        // Show progress message
        window.WebGCS?.showMessage(`Navigating to ${coords.lat.toFixed(6)}, ${coords.lon.toFixed(6)}`, 'info');
    }
    
    /**
     * Handle Clear Navigation
     */
    function handleClearNav() {
        if (elements.navLat) elements.navLat.value = '';
        if (elements.navLon) elements.navLon.value = '';
        if (elements.navAlt) elements.navAlt.value = '10';
        
        // Clear map target
        if (window.WebGCS?.modules?.MapController?.clearTarget) {
            window.WebGCS.modules.MapController.clearTarget();
        }
        
        window.WebGCS?.showMessage('Navigation inputs cleared', 'info');
    }
    
    /**
     * Handle Request Fence
     */
    function handleRequestFence() {
        if (!isConnected) {
            window.WebGCS?.showMessage('Not connected to drone', 'error');
            return;
        }
        
        console.log('Requesting geofence from vehicle...');
        
        // Disable button during request
        if (elements.requestFenceBtn) {
            elements.requestFenceBtn.disabled = true;
            elements.requestFenceBtn.textContent = 'Requesting...';
        }
        
        // Send request fence command
        if (window.WebGCS?.sendCommand) {
            window.WebGCS.sendCommand('request_fence');
        }
        
        window.WebGCS?.showMessage('Requesting geofence data...', 'info');
    }
    
    /**
     * Handle Request Mission
     */
    function handleRequestMission() {
        if (!isConnected) {
            window.WebGCS?.showMessage('Not connected to drone', 'error');
            return;
        }
        
        console.log('Requesting mission from vehicle...');
        
        // Disable button during request
        if (elements.requestMissionBtn) {
            elements.requestMissionBtn.disabled = true;
            elements.requestMissionBtn.textContent = 'Requesting...';
        }
        
        // Send request mission command
        if (window.WebGCS?.sendCommand) {
            window.WebGCS.sendCommand('request_mission');
        }
        
        window.WebGCS?.showMessage('Requesting mission data...', 'info');
    }
    
    /**
     * Get and Validate Navigation Coordinates
     */
    function getNavigationCoordinates() {
        const latStr = elements.navLat?.value?.trim();
        const lonStr = elements.navLon?.value?.trim();
        const altStr = elements.navAlt?.value?.trim() || '10';
        
        // Check if coordinates are provided
        if (!latStr || !lonStr) {
            window.WebGCS?.showMessage('Please enter latitude and longitude coordinates', 'error');
            return null;
        }
        
        // Parse and validate coordinates
        const lat = parseFloat(latStr);
        const lon = parseFloat(lonStr);
        const alt = parseFloat(altStr);
        
        // Validate latitude
        if (isNaN(lat) || lat < -90 || lat > 90) {
            window.WebGCS?.showMessage('Latitude must be between -90 and 90 degrees', 'error');
            elements.navLat?.focus();
            return null;
        }
        
        // Validate longitude
        if (isNaN(lon) || lon < -180 || lon > 180) {
            window.WebGCS?.showMessage('Longitude must be between -180 and 180 degrees', 'error');
            elements.navLon?.focus();
            return null;
        }
        
        // Validate altitude
        if (isNaN(alt) || alt < -100 || alt > 5000) {
            window.WebGCS?.showMessage('Altitude must be between -100 and 5000 meters', 'error');
            elements.navAlt?.focus();
            return null;
        }
        
        return { lat, lon, alt };
    }
    
    /**
     * Input Validation Functions
     */
    function validateLatitudeInput(event) {
        const lat = parseFloat(event.target.value);
        if (event.target.value && (isNaN(lat) || lat < -90 || lat > 90)) {
            event.target.setCustomValidity('Latitude must be between -90 and 90 degrees');
        } else {
            event.target.setCustomValidity('');
        }
    }
    
    function validateLongitudeInput(event) {
        const lon = parseFloat(event.target.value);
        if (event.target.value && (isNaN(lon) || lon < -180 || lon > 180)) {
            event.target.setCustomValidity('Longitude must be between -180 and 180 degrees');
        } else {
            event.target.setCustomValidity('');
        }
    }
    
    function validateAltitudeInput(event) {
        const alt = parseFloat(event.target.value);
        if (event.target.value && (isNaN(alt) || alt < -100 || alt > 5000)) {
            event.target.setCustomValidity('Altitude must be between -100 and 5000 meters');
        } else {
            event.target.setCustomValidity('');
        }
    }
    
    function formatLatitudeInput(event) {
        const lat = parseFloat(event.target.value);
        if (!isNaN(lat) && lat >= -90 && lat <= 90) {
            event.target.value = lat.toFixed(6);
        }
    }
    
    function formatLongitudeInput(event) {
        const lon = parseFloat(event.target.value);
        if (!isNaN(lon) && lon >= -180 && lon <= 180) {
            event.target.value = lon.toFixed(6);
        }
    }
    
    /**
     * Update Controls State
     */
    function updateControlsState() {
        const buttonsConfig = [
            { element: elements.gotoBtn, enabled: isConnected },
            { element: elements.clearNavBtn, enabled: true },
            { element: elements.requestFenceBtn, enabled: isConnected },
            { element: elements.requestMissionBtn, enabled: isConnected }
        ];
        
        buttonsConfig.forEach(({ element, enabled }) => {
            if (element && !element.textContent.includes('...')) {
                element.disabled = !enabled;
            }
        });
        
        // Enable/disable inputs
        const inputs = [elements.navLat, elements.navLon, elements.navAlt];
        inputs.forEach(input => {
            if (input) {
                input.disabled = false; // Navigation inputs always enabled
            }
        });
    }
    
    /**
     * Set Coordinates from External Source
     */
    function setCoordinates(lat, lon, alt = null) {
        if (elements.navLat) {
            elements.navLat.value = lat.toFixed(6);
        }
        if (elements.navLon) {
            elements.navLon.value = lon.toFixed(6);
        }
        if (alt !== null && elements.navAlt) {
            elements.navAlt.value = alt.toString();
        }
        
        console.log(`Navigation coordinates set to: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
    }
    
    /**
     * Event Handlers
     */
    function handleTelemetryUpdate(event) {
        const data = event.detail || event;
        if (data) {
            currentPosition = {
                lat: data.lat || 0,
                lon: data.lon || 0,
                alt: data.alt_rel || 0
            };
        }
    }
    
    function handleConnectionChange(event) {
        const data = event.detail || event;
        isConnected = data ? data.connected : false;
        updateControlsState();
    }
    
    function handleCommandResult(event) {
        const result = event.detail;
        const command = result.command;
        
        // Re-enable buttons after command completion
        if (command === 'goto' && elements.gotoBtn) {
            elements.gotoBtn.disabled = !isConnected;
            elements.gotoBtn.textContent = 'Go To';
        }
        
        if (command === 'request_fence' && elements.requestFenceBtn) {
            elements.requestFenceBtn.disabled = !isConnected;
            elements.requestFenceBtn.textContent = 'Request Fence';
            
            if (result.success) {
                window.WebGCS?.showMessage('Geofence data received', 'success');
                // TODO: Display fence data on map
            } else {
                window.WebGCS?.showMessage(`Fence request failed: ${result.error}`, 'error');
            }
        }
        
        if (command === 'request_mission' && elements.requestMissionBtn) {
            elements.requestMissionBtn.disabled = !isConnected;
            elements.requestMissionBtn.textContent = 'Request Mission';
            
            if (result.success) {
                window.WebGCS?.showMessage('Mission data received', 'success');
                // TODO: Display mission waypoints on map
            } else {
                window.WebGCS?.showMessage(`Mission request failed: ${result.error}`, 'error');
            }
        }
        
        if (command === 'goto') {
            if (result.success) {
                window.WebGCS?.showMessage('Go To command sent successfully', 'success');
            } else {
                window.WebGCS?.showMessage(`Go To failed: ${result.error}`, 'error');
            }
        }
    }
    
    function handleMapClick(event) {
        const { lat, lon } = event.detail;
        
        // Check if fly-to mode is active
        if (window.WebGCS?.modules?.MapController?.isFlyToActive?.()) {
            setCoordinates(lat, lon);
            window.WebGCS?.showMessage(`Coordinates set from map: ${lat.toFixed(6)}, ${lon.toFixed(6)}`, 'info');
        }
    }
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        
        // Coordinate management
        setCoordinates: setCoordinates,
        getCoordinates: getNavigationCoordinates,
        getCurrentPosition: () => ({ ...currentPosition }),
        
        // State getters
        isConnected: () => isConnected,
        
        // Module lifecycle callbacks
        onTelemetryUpdate: handleTelemetryUpdate,
        onConnectionChange: handleConnectionChange,
        onResize: () => {
            // Handle responsive layout changes if needed
        }
    };
})();
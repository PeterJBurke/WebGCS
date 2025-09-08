/**
 * WebGCS Main Application Module
 * Coordinates all modules and manages global application state
 */

// Global Application State
window.WebGCS = {
    socket: null,
    isConnected: false,
    droneConnected: false,
    modules: {},
    telemetryData: {
        connected: false,
        armed: false,
        mode: 'UNKNOWN',
        lat: 0.0,
        lon: 0.0,
        alt_rel: 0.0,
        alt_abs: 0.0,
        heading: 0.0,
        vx: 0.0,
        vy: 0.0,
        vz: 0.0,
        system_id: 0,
        component_id: 0,
        system_status: 0,
        battery_voltage: 0.0,
        current: 0.0,
        gps_fix_type: 0,
        satellites_visible: 0,
        hdop: 99.9
    },
    eventBus: new EventTarget()
};

/**
 * Safe JSON stringify that handles circular references
 */
window.WebGCS.safeStringify = function(obj, space = 2) {
    const seen = new WeakSet();
    return JSON.stringify(obj, function(key, val) {
        if (val != null && typeof val === "object") {
            if (seen.has(val)) {
                return '[Circular Reference]';
            }
            seen.add(val);
        }
        return val;
    }, space);
};

/**
 * Initialize WebGCS Application
 */
function initializeWebGCS() {
    console.log('Initializing WebGCS v2.0...');
    
    // Initialize SocketIO connection
    initializeSocket();
    
    // Initialize all modules
    initializeModules();
    
    // Setup global event listeners
    setupGlobalEvents();
    
    // Setup confirmation dialog
    setupConfirmationDialog();
    
    console.log('WebGCS initialization complete');
}

/**
 * Initialize SocketIO Connection
 */
function initializeSocket() {
    try {
        WebGCS.socket = io();
        
        WebGCS.socket.on('connect', handleSocketConnect);
        WebGCS.socket.on('disconnect', handleSocketDisconnect);
        WebGCS.socket.on('connect_error', handleSocketError);
        WebGCS.socket.on('telemetry_update', handleTelemetryUpdate);
        WebGCS.socket.on('command_result', handleCommandResult);
        WebGCS.socket.on('connection_status', handleConnectionStatus);
        
        console.log('SocketIO initialized');
    } catch (error) {
        console.error('SocketIO initialization failed:', error);
        showMessage('SocketIO connection failed', 'error');
    }
}

/**
 * Initialize All Application Modules
 */
function initializeModules() {
    const modules = [
        'ConnectionManager',
        'TelemetryDisplay', 
        'FlightControls',
        'NavigationControls',
        'MapController',
        'OfflineMaps',
        'AudioManager',
        'MessageLogger'
    ];
    
    modules.forEach(moduleName => {
        try {
            if (window[moduleName] && typeof window[moduleName].initialize === 'function') {
                window[moduleName].initialize();
                WebGCS.modules[moduleName] = window[moduleName];
                console.log(`${moduleName} initialized`);
            }
        } catch (error) {
            console.error(`Failed to initialize ${moduleName}:`, error);
        }
    });
}

/**
 * Setup Global Event Listeners
 */
function setupGlobalEvents() {
    // Listen for module events
    WebGCS.eventBus.addEventListener('telemetry_updated', (event) => {
        // Broadcast telemetry updates to all modules
        Object.values(WebGCS.modules).forEach(module => {
            if (module.onTelemetryUpdate) {
                module.onTelemetryUpdate(event.detail);
            }
        });
    });
    
    WebGCS.eventBus.addEventListener('connection_changed', (event) => {
        // Broadcast connection status changes
        Object.values(WebGCS.modules).forEach(module => {
            if (module.onConnectionChange) {
                module.onConnectionChange(event.detail);
            }
        });
    });
    
    // Handle keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Handle window resize for responsive layout
    window.addEventListener('resize', handleWindowResize);
}

/**
 * Setup Confirmation Dialog
 */
function setupConfirmationDialog() {
    const dialog = document.getElementById('confirmation-dialog');
    const yesBtn = document.getElementById('confirm-yes');
    const noBtn = document.getElementById('confirm-no');
    
    if (!dialog || !yesBtn || !noBtn) return;
    
    yesBtn.addEventListener('click', () => {
        dialog.classList.remove('active');
        if (window.confirmationCallback) {
            window.confirmationCallback(true);
            window.confirmationCallback = null;
        }
    });
    
    noBtn.addEventListener('click', () => {
        dialog.classList.remove('active');
        if (window.confirmationCallback) {
            window.confirmationCallback(false);
            window.confirmationCallback = null;
        }
    });
    
    // Close on outside click
    dialog.addEventListener('click', (e) => {
        if (e.target === dialog) {
            dialog.classList.remove('active');
            if (window.confirmationCallback) {
                window.confirmationCallback(false);
                window.confirmationCallback = null;
            }
        }
    });
}

/**
 * Socket Event Handlers
 */
function handleSocketConnect() {
    console.log('Connected to WebGCS server');
    WebGCS.isConnected = true;
    
    // Update WebSocket status
    const statusElement = document.getElementById('websocket-status');
    if (statusElement) {
        statusElement.textContent = 'WebSocket: Connected';
        statusElement.className = 'websocket-status ws-connected';
    }
    
    // Update backend status
    const backendStatusElement = document.getElementById('backend-status');
    if (backendStatusElement) {
        backendStatusElement.textContent = 'Backend Connected';
        backendStatusElement.className = 'status-indicator backend-connected';
    }
    
    // Notify modules
    WebGCS.eventBus.dispatchEvent(new CustomEvent('websocket_connected'));
    showMessage('Connected to WebGCS server', 'info');
}

function handleSocketDisconnect() {
    console.log('Disconnected from WebGCS server');
    WebGCS.isConnected = false;
    WebGCS.droneConnected = false;
    
    // Update WebSocket status
    const statusElement = document.getElementById('websocket-status');
    if (statusElement) {
        statusElement.textContent = 'WebSocket: Disconnected';
        statusElement.className = 'websocket-status ws-disconnected';
    }
    
    // Update backend status
    const backendStatusElement = document.getElementById('backend-status');
    if (backendStatusElement) {
        backendStatusElement.textContent = 'Backend Disconnected';
        backendStatusElement.className = 'status-indicator disconnected';
    }
    
    // Notify modules
    WebGCS.eventBus.dispatchEvent(new CustomEvent('websocket_disconnected'));
    showMessage('Disconnected from WebGCS server', 'warning');
}

function handleSocketError(error) {
    console.error('Socket connection error:', error);
    
    const statusElement = document.getElementById('websocket-status');
    if (statusElement) {
        statusElement.textContent = 'WebSocket: Error';
        statusElement.className = 'websocket-status ws-disconnected';
    }
    
    showMessage('WebSocket connection error', 'error');
}

function handleTelemetryUpdate(data) {
    // Update global telemetry state
    Object.assign(WebGCS.telemetryData, data);
    
    // Check for connection status change
    const wasConnected = WebGCS.droneConnected;
    WebGCS.droneConnected = data.connected;
    
    if (wasConnected !== WebGCS.droneConnected) {
        WebGCS.eventBus.dispatchEvent(new CustomEvent('connection_changed', {
            detail: { connected: WebGCS.droneConnected }
        }));
    }
    
    // Broadcast telemetry update
    WebGCS.eventBus.dispatchEvent(new CustomEvent('telemetry_updated', {
        detail: data
    }));
}

function handleCommandResult(result) {
    console.log('Command result:', result);
    
    // Show result message
    const message = result.success 
        ? `Command ${result.command} succeeded`
        : `Command ${result.command} failed: ${result.error}`;
    const type = result.success ? 'info' : 'error';
    
    showMessage(message, type);
    
    // Notify modules
    WebGCS.eventBus.dispatchEvent(new CustomEvent('command_result', {
        detail: result
    }));
}

function handleConnectionStatus(status) {
    console.log('Connection status:', status);
    
    // Show status message
    const message = status.message || `Connection ${status.status}`;
    const type = status.status === 'connected' ? 'success' : 
                 status.status === 'error' ? 'error' : 'info';
    
    showMessage(message, type);
    
    // Notify connection manager module
    WebGCS.eventBus.dispatchEvent(new CustomEvent('connection_status', {
        detail: status
    }));
}

/**
 * Handle Keyboard Shortcuts
 */
function handleKeyboardShortcuts(event) {
    // Only handle shortcuts if not typing in input
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }
    
    // Ctrl/Cmd + shortcuts
    if (event.ctrlKey || event.metaKey) {
        switch (event.key.toLowerCase()) {
            case 'c':
                event.preventDefault();
                if (WebGCS.modules.MapController && WebGCS.modules.MapController.centerMap) {
                    WebGCS.modules.MapController.centerMap();
                }
                break;
            case 'm':
                event.preventDefault();
                toggleOfflineMapsPanel();
                break;
        }
    }
    
    // Function key shortcuts
    switch (event.key) {
        case 'F1':
            event.preventDefault();
            showMessage('Keyboard shortcuts: Ctrl+C (Center Map), Ctrl+M (Toggle Offline Maps)', 'info');
            break;
        case 'Escape':
            event.preventDefault();
            // Close any open modals/panels
            const modal = document.querySelector('.modal.active');
            if (modal) {
                modal.classList.remove('active');
            }
            const panel = document.querySelector('.offline-maps-panel.active');
            if (panel) {
                panel.classList.remove('active');
            }
            break;
    }
}

/**
 * Handle Window Resize
 */
function handleWindowResize() {
    // Notify modules about resize
    Object.values(WebGCS.modules).forEach(module => {
        if (module.onResize) {
            module.onResize();
        }
    });
}

/**
 * Global Utility Functions
 */

/**
 * Show confirmation dialog
 */
function showConfirmation(title, message, callback) {
    const dialog = document.getElementById('confirmation-dialog');
    const titleElement = document.getElementById('confirm-title');
    const messageElement = document.getElementById('confirm-message');
    
    if (!dialog || !titleElement || !messageElement) return;
    
    titleElement.textContent = title;
    messageElement.textContent = message;
    dialog.classList.add('active');
    
    window.confirmationCallback = callback;
}

/**
 * Show status message
 */
function showMessage(message, type = 'info') {
    if (WebGCS.modules.MessageLogger && WebGCS.modules.MessageLogger.addMessage) {
        WebGCS.modules.MessageLogger.addMessage(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

/**
 * Send command to server
 */
function sendCommand(command, params = {}) {
    if (!WebGCS.socket || !WebGCS.isConnected) {
        showMessage('Not connected to server', 'error');
        return false;
    }
    
    console.log('Sending command:', command, params);
    
    WebGCS.socket.emit('flight_command', {
        command: command,
        params: params,
        timestamp: Date.now()
    });
    
    return true;
}

/**
 * Toggle offline maps panel
 */
function toggleOfflineMapsPanel() {
    const panel = document.getElementById('offline-maps-panel');
    if (panel) {
        panel.classList.toggle('active');
    }
}

/**
 * Format coordinate for display
 */
function formatCoordinate(value, decimals = 6) {
    return parseFloat(value).toFixed(decimals);
}

/**
 * Format altitude for display
 */
function formatAltitude(value, unit = 'm') {
    return `${parseFloat(value).toFixed(1)} ${unit}`;
}

/**
 * Format heading for display
 */
function formatHeading(value) {
    return `${parseFloat(value).toFixed(1)}°`;
}

/**
 * Format voltage for display
 */
function formatVoltage(value) {
    return `${parseFloat(value).toFixed(1)} V`;
}

/**
 * Format current for display
 */
function formatCurrent(value) {
    return `${parseFloat(value).toFixed(1)} A`;
}

// Expose global functions
window.WebGCS.showConfirmation = showConfirmation;
window.WebGCS.showMessage = showMessage;
window.WebGCS.sendCommand = sendCommand;
window.WebGCS.formatCoordinate = formatCoordinate;
window.WebGCS.formatAltitude = formatAltitude;
window.WebGCS.formatHeading = formatHeading;
window.WebGCS.formatVoltage = formatVoltage;
window.WebGCS.formatCurrent = formatCurrent;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeWebGCS);
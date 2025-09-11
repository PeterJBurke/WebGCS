/**
 * WebGCS Main JavaScript Module
 * Central coordination and initialization for the web interface.
 */

// Global state management
window.WebGCS = {
    socket: null,
    connected: false,
    droneConnected: false,
    telemetryData: {},
    config: {
        updateInterval: 100, // 10Hz updates
        reconnectInterval: 5000,
        commandTimeout: 5000
    },
    modules: {}
};

/**
 * Initialize the WebGCS application
 */
function initializeWebGCS() {
    console.log('Initializing WebGCS...');
    
    // Load configuration first
    loadConfiguration();
    
    // Initialize SocketIO connection
    initializeSocket();
    
    // Initialize UI components
    initializeUI();
    
    // Set up periodic tasks
    setupPeriodicTasks();
    
    console.log('WebGCS initialization complete');
}

/**
 * Initialize SocketIO connection
 */
function initializeSocket() {
    if (typeof window.ConnectionManager !== 'undefined') {
        const connectionManager = new window.ConnectionManager();
        window.WebGCS.modules.connection = connectionManager;
        
        // Add connection status monitoring
        connectionManager.on('connected', () => {
            console.log('📡 WebGCS connection established');
            updateConnectionStatus();
        });
        
        connectionManager.on('disconnected', () => {
            console.log('📡 WebGCS connection lost');
            updateConnectionStatus();
        });
        
        connectionManager.on('connection_error', (error) => {
            console.error('📡 Connection error:', error);
            updateConnectionStatus();
        });

        // Initialize connection
        connectionManager.initialize();
    } else {
        console.warn('ConnectionManager not available');
    }
}

/**
 * Load application configuration
 */
async function loadConfiguration() {
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            window.WebGCS.config.droneHost = data.config?.drone_host || '192.168.193.235';
            window.WebGCS.config.dronePort = data.config?.drone_port || 5678;
        }
    } catch (error) {
        console.warn('Could not load configuration:', error);
    }
}

/**
 * Initialize UI components
 */
function initializeUI() {
    // Initialize telemetry display
    if (typeof window.TelemetryDisplay !== 'undefined') {
        window.WebGCS.modules.telemetry = new window.TelemetryDisplay();
        window.WebGCS.modules.telemetry.initialize();
    }
    
    // Initialize flight controls
    if (typeof window.FlightControls !== 'undefined') {
        window.WebGCS.modules.controls = new window.FlightControls();
        window.WebGCS.modules.controls.initialize();
    }
    
    // Initialize PFD
    if (typeof window.PrimaryFlightDisplay !== 'undefined') {
        window.WebGCS.modules.pfd = new window.PrimaryFlightDisplay();
        window.WebGCS.modules.pfd.initialize();
    }
    
    // Initialize validation
    if (typeof window.InputValidation !== 'undefined') {
        window.WebGCS.modules.validation = new window.InputValidation();
        window.WebGCS.modules.validation.initialize();
    }
    
    console.log('UI components initialized');
}

/**
 * Setup periodic tasks
 */
function setupPeriodicTasks() {
    // Connection status check every 5 seconds
    setInterval(() => {
        updateConnectionStatus();
    }, 5000);
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus() {
    const statusElement = document.getElementById('connection-status');
    if (!statusElement) return;
    
    const socket = window.WebGCS.socket;
    const connected = socket && socket.connected;
    const droneConnected = window.WebGCS.droneConnected;
    
    let status = 'Disconnected';
    let className = 'disconnected';
    
    if (connected && droneConnected) {
        status = 'Connected to Drone';
        className = 'connected';
    } else if (connected) {
        status = 'Server Connected';
        className = 'partial';
    }
    
    statusElement.textContent = status;
    statusElement.className = `connection-indicator ${className}`;
    
    // FIX: Update connection panel status
    const panelStatusElement = document.getElementById('connection-status-text');
    if (panelStatusElement) {
        panelStatusElement.textContent = droneConnected ? 'Connected' : 'Disconnected';
        panelStatusElement.className = droneConnected ? 'status-connected' : 'status-disconnected';
    }
    
    // FIX: Update heartbeat timestamps when connected
    if (droneConnected && window.WebGCS.telemetryData && window.WebGCS.telemetryData.timestamp) {
        const lastHeartbeat = document.getElementById('last-heartbeat');
        const telemetryHeartbeat = document.getElementById('telemetry-last-heartbeat');
        const heartbeatTime = new Date(window.WebGCS.telemetryData.timestamp * 1000).toLocaleTimeString();
        
        if (lastHeartbeat) lastHeartbeat.textContent = heartbeatTime;
        if (telemetryHeartbeat) telemetryHeartbeat.textContent = heartbeatTime;
    }
}

/**
 * Global error handler
 */
window.addEventListener('error', (event) => {
    console.error('WebGCS Error:', event.error);
});

/**
 * Global utility functions
 */
window.WebGCS.utils = {
    formatNumber: (value, decimals = 1) => {
        return parseFloat(value).toFixed(decimals);
    },
    
    formatTime: (timestamp) => {
        return new Date(timestamp).toLocaleTimeString();
    },
    
    showConfirmation: (message) => {
        return confirm(message);
    }
};

/**
 * FIX: SocketIO Debug Information
 * Call window.debugSocketIO() in browser console for connection diagnostics
 */
function debugSocketIO() {
    console.log('=== SocketIO Debug Info ===');
    console.log('Socket exists:', !!window.WebGCS.socket);
    console.log('Socket connected:', window.WebGCS.socket?.connected);
    console.log('Socket ID:', window.WebGCS.socket?.id);
    console.log('WebGCS connected:', window.WebGCS.connected);
    console.log('Transport:', window.WebGCS.socket?.io?.engine?.transport?.name);
    console.log('Socket readyState:', window.WebGCS.socket?.io?.engine?.readyState);
    console.log('Socket URL:', window.WebGCS.socket?.io?.uri);
    console.log('=========================');
}

// Make debug function available globally
window.debugSocketIO = debugSocketIO;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeWebGCS);
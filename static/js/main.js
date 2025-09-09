/**
 * Main WebGCS JavaScript
 * Initialization and basic functionality
 * 
 * File size: Must stay under 100 lines per WebGCS PRD
 */

// Initialize WebGCS when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('WebGCS initializing...');
    
    // Initialize SocketIO connection
    const socket = io();
    
    // Make socket globally available
    window.socket = socket;
    
    // Connection event handlers
    socket.on('connect', function() {
        console.log('Connected to WebGCS server');
        // Don't change status - wait for actual drone connection
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebGCS server');
        updateConnectionStatus('Disconnected');
    });
    
    // Drone connection results
    socket.on('drone_connection_result', function(data) {
        console.log('Drone connection result:', data);
        if (data.success) {
            console.log('Connection successful - updating UI immediately');
            updateConnectionStatus('Connected to Drone');
            const connectBtn = document.getElementById('connect-btn');
            const disconnectBtn = document.getElementById('disconnect-btn');
            if (connectBtn) connectBtn.disabled = true;
            if (disconnectBtn) disconnectBtn.disabled = false;
            console.log('Button states updated after connection success');
        } else {
            console.log('Connection failed - updating UI with error');
            updateConnectionStatus('Disconnected - ' + data.message);
            const connectBtn = document.getElementById('connect-btn');
            const disconnectBtn = document.getElementById('disconnect-btn');
            if (connectBtn) connectBtn.disabled = false;
            if (disconnectBtn) disconnectBtn.disabled = true;
        }
    });
    
    // Drone status updates
    socket.on('drone_status', function(data) {
        console.log('Drone status:', data);
        updateDroneStatus(data);
    });
    
    // Button event listeners
    document.getElementById('connect-btn').addEventListener('click', function() {
        const host = document.getElementById('drone-host').value;
        const port = document.getElementById('drone-port').value;
        
        console.log(`Connecting to drone at ${host}:${port}`);
        socket.emit('connect_drone', { host: host, port: parseInt(port) });
    });
    
    document.getElementById('disconnect-btn').addEventListener('click', function() {
        console.log('Disconnecting from drone');
        socket.emit('disconnect_drone');
        
        // Reset button states
        document.getElementById('connect-btn').disabled = false;
        document.getElementById('disconnect-btn').disabled = true;
        updateConnectionStatus('Disconnected');
    });
    
    // Basic UI update functions - make them globally accessible
    window.updateConnectionStatus = function(status) {
        console.log('Updating connection status to:', status);
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = `Status: ${status}`;
            console.log('Connection status updated successfully');
        } else {
            console.error('Could not find connection-status element');
        }
    };
    
    window.updateDroneStatus = function(data) {
        console.log('Updating drone status with data:', data);
        
        // Update heartbeat counter
        if (data.heartbeat_count !== undefined) {
            const heartbeatElement = document.getElementById('heartbeat-counter');
            if (heartbeatElement) {
                heartbeatElement.textContent = `❤️ Heartbeat: ${data.heartbeat_count}`;
                console.log(`Heartbeat counter updated to: ${data.heartbeat_count}`);
            } else {
                console.error('Could not find heartbeat-counter element');
            }
        }
        
        // Update connection status based on connected flag
        if (data.connected !== undefined) {
            if (data.connected) {
                window.updateConnectionStatus('Connected to Drone');
                const connectBtn = document.getElementById('connect-btn');
                const disconnectBtn = document.getElementById('disconnect-btn');
                if (connectBtn) connectBtn.disabled = true;
                if (disconnectBtn) disconnectBtn.disabled = false;
                console.log('Button states updated for connected');
            } else {
                window.updateConnectionStatus('Disconnected');
                const connectBtn = document.getElementById('connect-btn');
                const disconnectBtn = document.getElementById('disconnect-btn');
                if (connectBtn) connectBtn.disabled = false;
                if (disconnectBtn) disconnectBtn.disabled = true;
                console.log('Button states updated for disconnected');
            }
        }
    };
    
    // Create shorter aliases for internal use
    const updateConnectionStatus = window.updateConnectionStatus;
    const updateDroneStatus = window.updateDroneStatus;
    
    // Initialize PFD after a short delay to ensure DOM is ready
    setTimeout(function() {
        if (typeof PrimaryFlightDisplay !== 'undefined') {
            console.log('Initializing Primary Flight Display...');
            window.pfd = new PrimaryFlightDisplay('pfd-canvas');
        }
    }, 100);
    
    console.log('WebGCS initialized');
});

// Make socket available globally for other modules
window.webgcs = window.webgcs || {};
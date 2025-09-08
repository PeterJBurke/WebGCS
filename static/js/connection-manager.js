/**
 * WebGCS Connection Manager Module
 * Handles MAVLink connection management and heartbeat monitoring
 */

window.ConnectionManager = (function() {
    'use strict';
    
    // Private variables
    let heartbeatCount = 0;
    let lastHeartbeatTime = 0;
    let heartbeatInterval = null;
    let isConnecting = false;
    let lastTelemetryHeartbeat = 0;
    
    // DOM elements
    let elements = {};
    
    /**
     * Initialize Connection Manager
     */
    function initialize() {
        console.log('Initializing Connection Manager...');
        
        // Cache DOM elements
        cacheElements();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize UI state
        updateConnectionUI(false);
        
        console.log('Connection Manager initialized successfully');
    }
    
    /**
     * Cache DOM Elements
     */
    function cacheElements() {
        console.log('Caching DOM elements...');
        elements = {
            connectionStatus: document.getElementById('connection-status'),
            backendStatus: document.getElementById('backend-status'),
            heartbeatIndicator: document.getElementById('heartbeat-indicator'),
            heartbeatCounter: document.getElementById('heartbeat-counter'),
            heartbeatSound: document.getElementById('heartbeat-sound'),
            ipAddress: document.getElementById('ip-address'),
            portNumber: document.getElementById('port-number'),
            connectBtn: document.getElementById('connect-btn'),
            disconnectBtn: document.getElementById('disconnect-btn')
        };
        
        // Check for missing elements
        Object.entries(elements).forEach(([key, element]) => {
            if (!element) {
                console.error(`Connection Manager: Element '${key}' not found`);
            } else {
                console.log(`Connection Manager: Element '${key}' found`);
            }
        });
    }
    
    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // Connect button
        if (elements.connectBtn) {
            console.log('Adding click listener to connect button');
            elements.connectBtn.addEventListener('click', handleConnect);
        } else {
            console.error('Connect button not found!');
        }
        
        // Disconnect button
        if (elements.disconnectBtn) {
            console.log('Adding click listener to disconnect button');
            elements.disconnectBtn.addEventListener('click', handleDisconnect);
        } else {
            console.error('Disconnect button not found!');
        }
        
        // Input validation
        if (elements.portNumber) {
            elements.portNumber.addEventListener('input', validatePortInput);
        }
        
        if (elements.ipAddress) {
            elements.ipAddress.addEventListener('input', validateIpInput);
        }
        
        // Heartbeat sound toggle
        if (elements.heartbeatSound) {
            elements.heartbeatSound.addEventListener('change', handleHeartbeatSoundToggle);
        }
        
        // Listen for global events
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('telemetry_updated', handleTelemetryUpdate);
            window.WebGCS.eventBus.addEventListener('websocket_connected', handleWebSocketConnect);
            window.WebGCS.eventBus.addEventListener('websocket_disconnected', handleWebSocketDisconnect);
            window.WebGCS.eventBus.addEventListener('connection_status', handleConnectionStatusUpdate);
        }
    }
    
    /**
     * Handle Connect Button Click
     */
    function handleConnect() {
        console.log('Connect button clicked!');
        if (isConnecting) {
            console.log('Already connecting, ignoring click');
            return;
        }
        
        const ip = elements.ipAddress?.value?.trim() || '192.168.193.235';
        const port = parseInt(elements.portNumber?.value) || 5678;
        
        // Validate inputs
        if (!validateIP(ip)) {
            window.WebGCS?.showMessage('Invalid IP address format', 'error');
            return;
        }
        
        if (port < 1 || port > 65535) {
            window.WebGCS?.showMessage('Port must be between 1 and 65535', 'error');
            return;
        }
        
        console.log(`Attempting to connect to ${ip}:${port}`);
        
        // Update UI to connecting state
        setConnectingState(true);
        
        // Send connection command via SocketIO
        if (window.WebGCS?.socket) {
            window.WebGCS.socket.emit('connect_drone', {
                ip: ip,
                port: port
            });
            
            console.log(`Connection request sent to ${ip}:${port}`);
            window.WebGCS?.showMessage(`Connecting to ${ip}:${port}...`, 'info');
            
            // Set timeout for connection attempt
            setTimeout(() => {
                if (isConnecting && !window.WebGCS.droneConnected) {
                    setConnectingState(false);
                    window.WebGCS.showMessage('Connection timeout', 'warning');
                }
            }, 30000); // 30 second timeout
            
        } else {
            setConnectingState(false);
            window.WebGCS?.showMessage('WebGCS not ready', 'error');
        }
    }
    
    /**
     * Handle Disconnect Button Click
     */
    function handleDisconnect() {
        console.log('Disconnect button clicked!');
        console.log('Disconnecting from drone...');
        
        // Send disconnect command via SocketIO
        if (window.WebGCS?.socket) {
            console.log('WebGCS socket found, emitting disconnect_drone event');
            console.log('Socket connected:', window.WebGCS.socket.connected);
            console.log('Socket ID:', window.WebGCS.socket.id);
            
            // First test basic SocketIO communication
            console.log('Testing SocketIO communication...');
            window.WebGCS.socket.emit('test_event');
            console.log('test_event emitted');
            
            // Then try disconnect
            window.WebGCS.socket.emit('disconnect_drone');
            console.log('disconnect_drone event emitted');
            
            window.WebGCS?.showMessage('Disconnecting...', 'info');
        } else {
            console.log('WebGCS socket NOT found');
            console.log('WebGCS state - socket:', !!window.WebGCS?.socket, 'isConnected:', window.WebGCS?.isConnected);
            window.WebGCS?.showMessage('WebGCS not ready', 'error');
        }
        
        // Reset heartbeat
        resetHeartbeat();
        
        // Update UI
        updateConnectionUI(false);
    }
    
    /**
     * Set Connecting State
     */
    function setConnectingState(connecting) {
        isConnecting = connecting;
        
        if (elements.connectBtn) {
            elements.connectBtn.disabled = connecting;
            elements.connectBtn.textContent = connecting ? 'Connecting...' : 'Connect';
        }
        
        if (elements.disconnectBtn) {
            elements.disconnectBtn.disabled = !connecting && !window.WebGCS?.droneConnected;
        }
        
        // Update status
        if (elements.connectionStatus && connecting) {
            elements.connectionStatus.className = 'status-indicator connecting';
            elements.connectionStatus.textContent = 'Connecting to drone...';
        }
    }
    
    /**
     * Update Connection UI
     */
    function updateConnectionUI(connected, systemId = 0) {
        if (elements.connectionStatus) {
            if (connected) {
                elements.connectionStatus.className = 'status-indicator connected';
                elements.connectionStatus.textContent = systemId > 0 
                    ? `Connected to drone (System ${systemId})`
                    : 'Connected to drone';
            } else {
                elements.connectionStatus.className = 'status-indicator disconnected';
                elements.connectionStatus.textContent = 'Disconnected from drone';
            }
        }
        
        if (elements.connectBtn) {
            elements.connectBtn.disabled = connected || isConnecting;
        }
        
        if (elements.disconnectBtn) {
            elements.disconnectBtn.disabled = !connected;
        }
        
        isConnecting = false;
    }
    
    /**
     * Handle Heartbeat Update
     */
    function updateHeartbeat() {
        heartbeatCount++;
        lastHeartbeatTime = Date.now();
        
        // Update counter
        if (elements.heartbeatCounter) {
            elements.heartbeatCounter.textContent = heartbeatCount;
        }
        
        // Animate heartbeat icon
        if (elements.heartbeatIndicator) {
            elements.heartbeatIndicator.classList.add('pulse');
            setTimeout(() => {
                elements.heartbeatIndicator.classList.remove('pulse');
            }, 300);
        }
        
        // Play heartbeat sound if enabled
        if (elements.heartbeatSound?.checked) {
            playHeartbeatSound();
        }
        
        // Notify audio manager for voice announcements
        if (window.WebGCS?.modules?.AudioManager?.onHeartbeat) {
            window.WebGCS.modules.AudioManager.onHeartbeat();
        }
    }
    
    /**
     * Reset Heartbeat
     */
    function resetHeartbeat() {
        heartbeatCount = 0;
        lastHeartbeatTime = 0;
        lastTelemetryHeartbeat = 0;
        
        if (elements.heartbeatCounter) {
            elements.heartbeatCounter.textContent = '0';
        }
        
        if (heartbeatInterval) {
            clearInterval(heartbeatInterval);
            heartbeatInterval = null;
        }
    }
    
    /**
     * Play Heartbeat Sound
     */
    function playHeartbeatSound() {
        try {
            // Create audio context if not exists
            if (!window.audioContext) {
                window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            // Create beep sound
            const oscillator = window.audioContext.createOscillator();
            const gainNode = window.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(window.audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, window.audioContext.currentTime);
            gainNode.gain.setValueAtTime(0, window.audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, window.audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, window.audioContext.currentTime + 0.1);
            
            oscillator.start(window.audioContext.currentTime);
            oscillator.stop(window.audioContext.currentTime + 0.1);
            
        } catch (error) {
            console.warn('Could not play heartbeat sound:', error);
        }
    }
    
    /**
     * Validate IP Address
     */
    function validateIP(ip) {
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    }
    
    /**
     * Validate Port Input
     */
    function validatePortInput(event) {
        const port = parseInt(event.target.value);
        if (isNaN(port) || port < 1 || port > 65535) {
            event.target.setCustomValidity('Port must be between 1 and 65535');
        } else {
            event.target.setCustomValidity('');
        }
    }
    
    /**
     * Validate IP Input
     */
    function validateIpInput(event) {
        const ip = event.target.value.trim();
        if (ip && !validateIP(ip)) {
            event.target.setCustomValidity('Invalid IP address format');
        } else {
            event.target.setCustomValidity('');
        }
    }
    
    /**
     * Handle Heartbeat Sound Toggle
     */
    function handleHeartbeatSoundToggle(event) {
        const enabled = event.target.checked;
        console.log('Heartbeat sound:', enabled ? 'enabled' : 'disabled');
        
        // Store preference
        localStorage.setItem('webgcs_heartbeat_sound', enabled.toString());
        
        if (enabled && window.audioContext?.state === 'suspended') {
            window.audioContext.resume();
        }
    }
    
    /**
     * Event Handlers
     */
    function handleTelemetryUpdate(event) {
        const data = event.detail || event;
        
        // Ensure data is valid
        if (!data) {
            console.warn('handleTelemetryUpdate: No data received');
            return;
        }
        
        // Check for heartbeat (limit to once per second)
        if (data.connected) {
            const now = Date.now();
            if (now - lastTelemetryHeartbeat >= 1000) { // Only heartbeat once per second
                updateHeartbeat();
                lastTelemetryHeartbeat = now;
            }
        }
        
        // Update connection status
        updateConnectionUI(data.connected, data.system_id);
    }
    
    function handleWebSocketConnect() {
        // WebSocket connected - enable connect button if not already connected
        if (elements.connectBtn && !window.WebGCS?.droneConnected) {
            elements.connectBtn.disabled = false;
        }
    }
    
    function handleWebSocketDisconnect() {
        // WebSocket disconnected - reset everything
        updateConnectionUI(false);
        resetHeartbeat();
        setConnectingState(false);
    }
    
    /**
     * Handle Connection Status Updates from Server
     */
    function handleConnectionStatusUpdate(event) {
        const status = event.detail;
        console.log('Received connection status:', status);
        
        // Update connection state based on status
        switch (status.status) {
            case 'connecting':
                setConnectingState(true);
                break;
                
            case 'connected':
                setConnectingState(false);
                updateConnectionUI(true, status.system_id || 0);
                break;
                
            case 'disconnected':
                setConnectingState(false);
                updateConnectionUI(false);
                resetHeartbeat();
                break;
                
            case 'error':
                setConnectingState(false);
                updateConnectionUI(false);
                break;
                
            default:
                console.warn('Unknown connection status:', status.status);
        }
    }
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        
        // Connection state methods
        isConnected: () => window.WebGCS?.droneConnected || false,
        isConnecting: () => isConnecting,
        getHeartbeatCount: () => heartbeatCount,
        getLastHeartbeatTime: () => lastHeartbeatTime,
        
        // Module lifecycle callbacks
        onTelemetryUpdate: (data) => {
            // Convert data to event-like object for handleTelemetryUpdate
            handleTelemetryUpdate({ detail: data });
        },
        onConnectionChange: (data) => {
            updateConnectionUI(data.connected, data.system_id);
        },
        onResize: () => {
            // Handle responsive layout changes if needed
        }
    };
})();

// Load saved preferences
document.addEventListener('DOMContentLoaded', function() {
    // Restore heartbeat sound preference
    const heartbeatSoundSaved = localStorage.getItem('webgcs_heartbeat_sound');
    if (heartbeatSoundSaved !== null) {
        const checkbox = document.getElementById('heartbeat-sound');
        if (checkbox) {
            checkbox.checked = heartbeatSoundSaved === 'true';
        }
    }
});
/**
 * WebGCS Connection Management
 * Handles SocketIO connection and real-time communication.
 */

class ConnectionManager {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.heartbeatInterval = null;
        this.eventHandlers = new Map();
    }

    /**
     * Initialize connection manager
     */
    initialize() {
        console.log('Initializing connection manager...');
        this.connect();
        this.setupEventHandlers();
    }

    /**
     * Establish SocketIO connection
     */
    connect() {
        if (this.socket && this.socket.connected) {
            console.log('Already connected');
            return;
        }

        console.log('Connecting to WebGCS server...');
        
        // FIX: Enhanced SocketIO configuration for compatibility
        this.socket = io({
            forceNew: true,
            reconnection: true,
            timeout: 10000,              // Increased timeout for better stability
            reconnectionDelay: 1000,
            reconnectionAttempts: 10,    // More reconnection attempts
            transports: ['polling', 'websocket'], // Start with polling, upgrade to websocket
            upgrade: true,               // Allow upgrades to websocket
            rememberUpgrade: true        // Remember successful upgrades
        });

        // Store socket globally immediately
        window.WebGCS.socket = this.socket;

        this.setupSocketEvents();
        
        // FIX: Add connection timeout handling
        setTimeout(() => {
            if (!this.socket.connected) {
                console.error('❌ SocketIO connection timeout after 10 seconds');
                console.error('Server may be incompatible or not running');
                console.error('Check console for SocketIO negotiation errors');
            }
        }, 10000);
    }

    /**
     * Setup SocketIO event handlers
     */
    setupSocketEvents() {
        console.log('Setting up SocketIO event handlers...');
        
        // Enhanced connection debugging
        this.socket.on('connect', () => {
            console.log('✅ Connected to WebGCS server');
            console.log('Socket ID:', this.socket.id);
            window.WebGCS.connected = true;
            this.reconnectAttempts = 0;
            this.startHeartbeat();
            this.triggerEvent('connected');
        });

        this.socket.on('connect_error', (error) => {
            console.error('❌ Connection error:', error);
            window.WebGCS.connected = false;
            this.triggerEvent('connection_error', error);
        });

        this.socket.on('disconnect', (reason) => {
            console.log('❌ Disconnected from server:', reason);
            window.WebGCS.connected = false;
            window.WebGCS.droneConnected = false;
            this.stopHeartbeat();
            this.triggerEvent('disconnected', reason);
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log('🔄 Reconnected after', attemptNumber, 'attempts');
            window.WebGCS.connected = true;
        });

        this.socket.on('reconnect_error', (error) => {
            console.error('🔄❌ Reconnection error:', error);
        });

        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Reconnection attempt ${attemptNumber}`);
            this.reconnectAttempts = attemptNumber;
        });

        this.socket.on('drone_connected', (data) => {
            console.log('Drone connected:', data);
            window.WebGCS.droneConnected = true;
            this.triggerEvent('drone_connected', data);
        });

        this.socket.on('drone_disconnected', (data) => {
            console.log('Drone disconnected:', data);
            window.WebGCS.droneConnected = false;
            this.triggerEvent('drone_disconnected', data);
        });

        this.socket.on('telemetry_update', (data) => {
            console.log('Telemetry update received:', data);
            window.WebGCS.telemetryData = { ...window.WebGCS.telemetryData, ...data };
            
            // Update heartbeat display
            if (data.timestamp || data.connection_status?.last_heartbeat) {
                const timestamp = data.timestamp || data.connection_status.last_heartbeat;
                const heartbeatTime = new Date(timestamp).toLocaleTimeString();
                const lastHeartbeat = document.getElementById('last-heartbeat');
                const telemetryHeartbeat = document.getElementById('telemetry-last-heartbeat');
                
                if (lastHeartbeat) lastHeartbeat.textContent = heartbeatTime;
                if (telemetryHeartbeat) telemetryHeartbeat.textContent = heartbeatTime;
            }
            
            // Trigger event for other components
            this.triggerEvent('telemetry_update', data);
        });

        // FIX: Handle system status updates
        this.socket.on('system_status', (data) => {
            console.log('System status update:', data);
            window.WebGCS.droneConnected = data.mavlink_connected;
            window.WebGCS.droneArmed = data.drone_armed;
            window.WebGCS.flightMode = data.flight_mode;
            
            // Update UI
            this.updateConnectionUI();
        });

        this.socket.on('command_acknowledged', (data) => {
            console.log('Command acknowledged:', data);
            this.triggerEvent('command_acknowledged', data);
        });

        this.socket.on('command_error', (data) => {
            console.error('Command error:', data);
            this.triggerEvent('command_error', data);
        });

        this.socket.on('connection_error', (data) => {
            console.error('Connection error:', data);
            this.triggerEvent('connection_error', data);
        });

        this.socket.on('error', (error) => {
            console.error('🚨 SOCKET ERROR:', error);
            this.triggerEvent('error', error);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('🚨 CONNECTION ERROR:', error.message || error);
            this.triggerEvent('connection_error', error);
        });
    }

    /**
     * Setup application event handlers
     */
    setupEventHandlers() {
        // Register for telemetry updates
        this.on('telemetry_update', (data) => {
            if (window.WebGCS.modules.telemetry) {
                window.WebGCS.modules.telemetry.updateDisplay(data);
            }
            if (window.WebGCS.modules.pfd) {
                window.WebGCS.modules.pfd.updateDisplay(data);
            }
        });

        // Register for connection status updates
        this.on('connected', () => {
            this.updateConnectionUI();
        });

        this.on('disconnected', () => {
            this.updateConnectionUI();
        });

        this.on('drone_connected', () => {
            this.updateConnectionUI();
        });

        this.on('drone_disconnected', () => {
            this.updateConnectionUI();
        });
    }

    /**
     * Update connection UI elements
     */
    updateConnectionUI() {
        // Update main connection status
        if (typeof updateConnectionStatus === 'function') {
            updateConnectionStatus();
        }

        // Update drone connection button
        const connectBtn = document.getElementById('connect-drone-btn');
        if (connectBtn) {
            const connected = window.WebGCS.droneConnected;
            connectBtn.textContent = connected ? 'Disconnect' : 'Connect';
            connectBtn.className = `btn ${connected ? 'btn-danger' : 'btn-primary'}`;
        }
    }

    /**
     * Start heartbeat mechanism
     */
    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatInterval = setInterval(() => {
            if (this.socket && this.socket.connected) {
                this.socket.emit('heartbeat');
            }
        }, 10000); // 10 second heartbeat
    }

    /**
     * Stop heartbeat mechanism
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * Disconnect from server
     */
    disconnect() {
        console.log('Disconnecting from server...');
        if (this.socket) {
            this.socket.disconnect();
        }
        this.stopHeartbeat();
    }

    /**
     * Send command to drone via SocketIO
     */
    sendCommand(command, params = {}) {
        if (!this.socket || !this.socket.connected) {
            console.error('Cannot send command: not connected to server');
            return false;
        }

        console.log('Sending command:', command, params);
        
        this.socket.emit('send_command', {
            command: command,
            parameters: params,
            timestamp: Date.now()
        });

        return true;
    }

    /**
     * Register event handler
     */
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }

    /**
     * Trigger event handlers
     */
    triggerEvent(event, data = null) {
        const handlers = this.eventHandlers.get(event);
        if (handlers) {
            handlers.forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in ${event} handler:`, error);
                }
            });
        }
    }
}

// Export for use in main.js
window.ConnectionManager = ConnectionManager;
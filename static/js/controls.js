/**
 * WebGCS Flight Controls
 * Handles flight control buttons with safety confirmations.
 */

class FlightControls {
    constructor() {
        this.commandTimeout = 5000;
        this.pendingCommands = new Map();
    }

    /**
     * Initialize flight controls
     */
    initialize() {
        console.log('Initializing flight controls...');
        this.setupEventListeners();
        this.updateButtonStates();
        this.setupSocketEventHandlers();
    }

    /**
     * Setup event listeners for flight control buttons
     */
    setupEventListeners() {
        // Connection controls
        this.bindButton('connect-drone-btn', this.handleConnectDrone.bind(this));
        
        // ARM/DISARM controls with safety confirmations
        this.bindButton('arm-btn', () => this.handleArmCommand());
        this.bindButton('disarm-btn', () => this.handleDisarmCommand());
        
        // Flight mode controls
        this.bindButton('stabilize-btn', () => this.handleFlightMode('STABILIZE'));
        this.bindButton('alt-hold-btn', () => this.handleFlightMode('ALT_HOLD'));
        this.bindButton('loiter-btn', () => this.handleFlightMode('LOITER'));
        this.bindButton('guided-btn', () => this.handleFlightMode('GUIDED'));
        this.bindButton('rtl-btn', () => this.handleFlightMode('RTL'));
        this.bindButton('auto-btn', () => this.handleFlightMode('AUTO'));
        this.bindButton('land-btn', () => this.handleFlightMode('LAND'));
        
        // Takeoff control with safety confirmation
        this.bindButton('takeoff-btn', () => this.handleTakeoffCommand());
        
        // Emergency controls
        this.bindButton('emergency-stop-btn', () => this.handleEmergencyStop());
        
        // Navigation controls
        this.bindButton('goto-btn', () => this.handleGotoWaypoint());
        this.bindButton('set-home-btn', () => this.handleSetHome());
        
        // Gimbal controls
        this.bindButton('gimbal-center-btn', () => this.handleGimbalCenter());
        this.bindButton('gimbal-down-btn', () => this.handleGimbalDown());
    }

    /**
     * Bind button click event with error handling
     */
    bindButton(buttonId, handler) {
        const button = document.getElementById(buttonId);
        if (button) {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                try {
                    handler();
                } catch (error) {
                    console.error(`Error in ${buttonId} handler:`, error);
                }
            });
        }
    }

    /**
     * Handle drone connection toggle
     */
    handleConnectDrone() {
        console.log('🔘 Connect button clicked');
        
        // FIX: More robust connection validation that handles race conditions
        if (!window.WebGCS.socket) {
            console.error('❌ No SocketIO socket available');
            alert('SocketIO not initialized. Please refresh the page.');
            return;
        }
        
        // Check both connection indicators for reliability
        const socketConnected = window.WebGCS.socket.connected;
        const webgcsConnected = window.WebGCS.connected;
        
        console.log('🔍 Connection status check:', {
            socketConnected,
            webgcsConnected,
            socketId: window.WebGCS.socket.id,
            socketDisconnected: window.WebGCS.socket.disconnected
        });
        
        // If either connection indicator is false, try to reconnect first
        if (!socketConnected || !webgcsConnected) {
            console.log('🔄 Connection issue detected, attempting reconnection...');
            
            // Give socket a moment to reconnect if it's in a transition state
            setTimeout(() => {
                const finalSocketConnected = window.WebGCS.socket.connected;
                const finalWebgcsConnected = window.WebGCS.connected;
                
                if (!finalSocketConnected || !finalWebgcsConnected) {
                    console.error('❌ Connection not available after retry');
                    console.error('Final socket state:', {
                        connected: finalSocketConnected,
                        webgcs: finalWebgcsConnected,
                        id: window.WebGCS.socket.id
                    });
                    alert('Connection to WebGCS server lost. Please refresh the page.');
                    return;
                }
                
                // Proceed with drone connection after validation
                this.proceedWithDroneConnection();
            }, 1000);
            return;
        }
        
        // Both connection indicators are good, proceed immediately
        this.proceedWithDroneConnection();
    }
    
    /**
     * Proceed with drone connection after validation
     */
    proceedWithDroneConnection() {
        
        const connected = window.WebGCS.droneConnected;
        const connectionManager = window.WebGCS.modules.connection;
        
        if (!connectionManager) {
            console.error('❌ Connection manager not available');
            alert('Connection manager not available');
            return;
        }

        if (connected) {
            if (window.WebGCS.utils.showConfirmation('Disconnect from drone?')) {
                console.log('🔌 Sending disconnect command');
                connectionManager.sendCommand('disconnect_drone');
            }
        } else {
            console.log('🔌 Sending connect command');
            connectionManager.sendCommand('connect_drone');
        }
    }

    /**
     * Handle ARM command with safety confirmation
     */
    handleArmCommand() {
        if (!this.validateConnection()) return;
        
        const message = 'ARM the drone? This will enable motor spinning.';
        if (window.WebGCS.utils.showConfirmation(message)) {
            this.sendCommand('arm', {}, 'Arming drone...');
        }
    }

    /**
     * Handle DISARM command with safety confirmation
     */
    handleDisarmCommand() {
        if (!this.validateConnection()) return;
        
        const message = 'DISARM the drone? Motors will stop immediately.';
        if (window.WebGCS.utils.showConfirmation(message)) {
            this.sendCommand('disarm', {}, 'Disarming drone...');
        }
    }

    /**
     * Handle flight mode change
     */
    handleFlightMode(mode) {
        if (!this.validateConnection()) return;
        
        this.sendCommand('set_mode', { mode: mode }, `Setting mode to ${mode}...`);
    }

    /**
     * Handle takeoff command with safety confirmation
     */
    handleTakeoffCommand() {
        if (!this.validateConnection()) return;
        
        const altitudeInput = document.getElementById('takeoff-altitude');
        const altitude = altitudeInput ? parseFloat(altitudeInput.value) : 10;
        
        if (altitude < 1 || altitude > 100) {
            alert('Takeoff altitude must be between 1 and 100 meters');
            return;
        }
        
        const message = `TAKEOFF to ${altitude}m altitude? Ensure area is clear.`;
        if (window.WebGCS.utils.showConfirmation(message)) {
            this.sendCommand('takeoff', { altitude: altitude }, `Taking off to ${altitude}m...`);
        }
    }

    /**
     * Handle emergency stop
     */
    handleEmergencyStop() {
        const message = 'EMERGENCY STOP? This will immediately disarm the drone!';
        if (window.WebGCS.utils.showConfirmation(message)) {
            this.sendCommand('emergency_stop', {}, 'Emergency stop initiated...');
        }
    }

    /**
     * Handle goto waypoint command
     */
    handleGotoWaypoint() {
        if (!this.validateConnection()) return;
        
        const latInput = document.getElementById('goto-latitude');
        const lonInput = document.getElementById('goto-longitude');
        const altInput = document.getElementById('goto-altitude');
        
        if (!latInput || !lonInput || !altInput) {
            console.error('Navigation input fields not found');
            return;
        }
        
        const latitude = parseFloat(latInput.value);
        const longitude = parseFloat(lonInput.value);
        const altitude = parseFloat(altInput.value);
        
        if (!this.validateCoordinates(latitude, longitude, altitude)) {
            return;
        }
        
        this.sendCommand('goto_waypoint', {
            latitude: latitude,
            longitude: longitude,
            altitude: altitude
        }, 'Flying to waypoint...');
    }

    /**
     * Handle set home command
     */
    handleSetHome() {
        if (!this.validateConnection()) return;
        
        if (window.WebGCS.utils.showConfirmation('Set current position as home?')) {
            this.sendCommand('set_home', {}, 'Setting home position...');
        }
    }

    /**
     * Handle gimbal center
     */
    handleGimbalCenter() {
        if (!this.validateConnection()) return;
        this.sendCommand('gimbal_control', { pitch: 0, yaw: 0 }, 'Centering gimbal...');
    }

    /**
     * Handle gimbal down
     */
    handleGimbalDown() {
        if (!this.validateConnection()) return;
        this.sendCommand('gimbal_control', { pitch: -90, yaw: 0 }, 'Pointing gimbal down...');
    }

    /**
     * Validate connection before sending commands
     */
    validateConnection() {
        if (!window.WebGCS.connected) {
            alert('Not connected to server');
            return false;
        }
        
        if (!window.WebGCS.droneConnected) {
            alert('Drone not connected');
            return false;
        }
        
        return true;
    }

    /**
     * Validate coordinates
     */
    validateCoordinates(latitude, longitude, altitude) {
        if (isNaN(latitude) || latitude < -90 || latitude > 90) {
            alert('Latitude must be between -90 and 90 degrees');
            return false;
        }
        
        if (isNaN(longitude) || longitude < -180 || longitude > 180) {
            alert('Longitude must be between -180 and 180 degrees');
            return false;
        }
        
        if (isNaN(altitude) || altitude < 0 || altitude > 1000) {
            alert('Altitude must be between 0 and 1000 meters');
            return false;
        }
        
        return true;
    }

    /**
     * Send command with tracking and feedback
     */
    sendCommand(command, params = {}, statusMessage = '') {
        const connectionManager = window.WebGCS.modules.connection;
        if (!connectionManager) {
            console.error('Connection manager not available');
            return;
        }

        const commandId = Date.now().toString();
        
        // Show status message
        if (statusMessage) {
            this.showStatus(statusMessage);
        }
        
        // Track pending command
        this.pendingCommands.set(commandId, {
            command: command,
            timestamp: Date.now(),
            timeout: setTimeout(() => {
                this.handleCommandTimeout(commandId);
            }, this.commandTimeout)
        });

        // Send command
        const success = connectionManager.sendCommand(command, {
            ...params,
            command_id: commandId
        });

        if (!success) {
            this.pendingCommands.delete(commandId);
            this.showStatus('Failed to send command', 'error');
        }
    }

    /**
     * Handle command timeout
     */
    handleCommandTimeout(commandId) {
        const command = this.pendingCommands.get(commandId);
        if (command) {
            console.warn(`Command timeout: ${command.command}`);
            this.showStatus(`Command timeout: ${command.command}`, 'error');
            this.pendingCommands.delete(commandId);
        }
    }

    /**
     * Handle command acknowledgment
     */
    handleCommandAck(data) {
        const commandId = data.command_id;
        if (commandId && this.pendingCommands.has(commandId)) {
            const command = this.pendingCommands.get(commandId);
            clearTimeout(command.timeout);
            this.pendingCommands.delete(commandId);
            
            if (data.success) {
                this.showStatus(`${command.command} successful`, 'success');
            } else {
                this.showStatus(`${command.command} failed: ${data.error || 'Unknown error'}`, 'error');
            }
        }
    }

    /**
     * Show status message
     */
    showStatus(message, type = 'info') {
        const statusElement = document.getElementById('command-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status ${type}`;
            
            // Clear after 5 seconds
            setTimeout(() => {
                statusElement.textContent = '';
                statusElement.className = 'status';
            }, 5000);
        }
        
        console.log(`Status [${type}]: ${message}`);
    }

    /**
     * Setup SocketIO event handlers
     */
    setupSocketEventHandlers() {
        const connectionManager = window.WebGCS.modules.connection;
        if (!connectionManager) {
            console.error('Connection manager not available for event setup');
            return;
        }

        // Handle command acknowledgments
        connectionManager.on('command_acknowledged', (data) => {
            this.handleCommandAck({ 
                command_id: data.command_id || data.command, 
                success: true,
                command: data.command 
            });
        });

        // Handle command errors
        connectionManager.on('command_error', (data) => {
            this.handleCommandAck({ 
                command_id: data.command_id || data.command, 
                success: false, 
                error: data.error,
                command: data.command 
            });
        });

        // Handle connection status changes
        connectionManager.on('drone_connected', () => {
            this.updateButtonStates();
        });

        connectionManager.on('drone_disconnected', () => {
            this.updateButtonStates();
        });

        connectionManager.on('connection_error', (data) => {
            this.showStatus(`Connection error: ${data.message}`, 'error');
        });
    }

    /**
     * Update button states based on drone status
     */
    updateButtonStates() {
        const connected = window.WebGCS.droneConnected;
        const telemetry = window.WebGCS.telemetryData;
        
        // Update button availability
        const controlButtons = document.querySelectorAll('.flight-control-btn');
        controlButtons.forEach(button => {
            button.disabled = !connected;
        });
        
        // Update ARM/DISARM button states
        const armBtn = document.getElementById('arm-btn');
        const disarmBtn = document.getElementById('disarm-btn');
        
        if (armBtn && disarmBtn && telemetry && telemetry.armed !== undefined) {
            if (telemetry.armed) {
                armBtn.disabled = true;
                disarmBtn.disabled = false;
            } else {
                armBtn.disabled = false;
                disarmBtn.disabled = !connected;
            }
        }
    }
}

// Export for use in main.js
window.FlightControls = FlightControls;
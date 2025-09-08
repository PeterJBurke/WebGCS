/**
 * WebGCS Flight Controls Module
 * Handles all flight control operations with safety confirmations
 */

window.FlightControls = (function() {
    'use strict';
    
    // Private variables
    let isConnected = false;
    let currentMode = 'UNKNOWN';
    let isArmed = false;
    
    // DOM elements
    let elements = {};
    
    // Safety-critical commands requiring confirmation
    const SAFETY_COMMANDS = ['arm', 'disarm', 'takeoff', 'land', 'rtl'];
    
    /**
     * Initialize Flight Controls
     */
    function initialize() {
        console.log('Initializing Flight Controls...');
        
        // Cache DOM elements
        cacheElements();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize UI state
        updateControlsState();
        
        console.log('Flight Controls initialized');
    }
    
    /**
     * Cache DOM Elements
     */
    function cacheElements() {
        elements = {
            armBtn: document.getElementById('arm-btn'),
            disarmBtn: document.getElementById('disarm-btn'),
            takeoffBtn: document.getElementById('takeoff-btn'),
            takeoffAltitude: document.getElementById('takeoff-altitude'),
            landBtn: document.getElementById('land-btn'),
            rtlBtn: document.getElementById('rtl-btn'),
            flightModeSelect: document.getElementById('flight-mode-select'),
            setModeBtn: document.getElementById('set-mode-btn')
        };
        
        // Check for missing elements
        Object.entries(elements).forEach(([key, element]) => {
            if (!element) {
                console.warn(`Flight Controls: Element '${key}' not found`);
            }
        });
    }
    
    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // ARM button
        if (elements.armBtn) {
            elements.armBtn.addEventListener('click', () => handleSafetyCommand('arm', 'ARM Vehicle', 'This will ARM the vehicle. Propellers may start spinning!'));
        }
        
        // DISARM button
        if (elements.disarmBtn) {
            elements.disarmBtn.addEventListener('click', () => handleSafetyCommand('disarm', 'DISARM Vehicle', 'This will DISARM the vehicle. Make sure it is landed safely.'));
        }
        
        // Takeoff button
        if (elements.takeoffBtn) {
            elements.takeoffBtn.addEventListener('click', handleTakeoff);
        }
        
        // Land button
        if (elements.landBtn) {
            elements.landBtn.addEventListener('click', () => handleSafetyCommand('land', 'LAND Vehicle', 'This will initiate automatic landing at current position.'));
        }
        
        // RTL button
        if (elements.rtlBtn) {
            elements.rtlBtn.addEventListener('click', () => handleSafetyCommand('rtl', 'Return to Launch', 'This will return the vehicle to launch position and land.'));
        }
        
        // Set mode button
        if (elements.setModeBtn) {
            elements.setModeBtn.addEventListener('click', handleSetMode);
        }
        
        // Takeoff altitude validation
        if (elements.takeoffAltitude) {
            elements.takeoffAltitude.addEventListener('input', validateTakeoffAltitude);
        }
        
        // Listen for global events
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('telemetry_updated', handleTelemetryUpdate);
            window.WebGCS.eventBus.addEventListener('connection_changed', handleConnectionChange);
            window.WebGCS.eventBus.addEventListener('command_result', handleCommandResult);
        }
    }
    
    /**
     * Handle Safety Command with Confirmation
     */
    function handleSafetyCommand(command, title, message) {
        if (!isConnected) {
            window.WebGCS?.showMessage('Not connected to drone', 'error');
            return;
        }
        
        // Show confirmation dialog
        if (window.WebGCS?.showConfirmation) {
            window.WebGCS.showConfirmation(title, message, (confirmed) => {
                if (confirmed) {
                    executeCommand(command);
                } else {
                    window.WebGCS.showMessage(`${command.toUpperCase()} command cancelled`, 'info');
                }
            });
        } else {
            // Fallback if confirmation dialog not available
            if (confirm(`${title}\n\n${message}`)) {
                executeCommand(command);
            }
        }
    }
    
    /**
     * Handle Takeoff Command
     */
    function handleTakeoff() {
        if (!isConnected) {
            window.WebGCS?.showMessage('Not connected to drone', 'error');
            return;
        }
        
        if (!isArmed) {
            window.WebGCS?.showMessage('Vehicle must be armed before takeoff', 'warning');
            return;
        }
        
        const altitude = parseFloat(elements.takeoffAltitude?.value) || 5;
        
        if (altitude < 1 || altitude > 1000) {
            window.WebGCS?.showMessage('Takeoff altitude must be between 1 and 1000 meters', 'error');
            return;
        }
        
        const message = `This will initiate takeoff to ${altitude} meters altitude.`;
        
        if (window.WebGCS?.showConfirmation) {
            window.WebGCS.showConfirmation('TAKEOFF Vehicle', message, (confirmed) => {
                if (confirmed) {
                    executeCommand('takeoff', { altitude: altitude });
                } else {
                    window.WebGCS.showMessage('TAKEOFF command cancelled', 'info');
                }
            });
        } else {
            if (confirm(`TAKEOFF Vehicle\n\n${message}`)) {
                executeCommand('takeoff', { altitude: altitude });
            }
        }
    }
    
    /**
     * Handle Set Mode Command
     */
    function handleSetMode() {
        if (!isConnected) {
            window.WebGCS?.showMessage('Not connected to drone', 'error');
            return;
        }
        
        const selectedMode = elements.flightModeSelect?.value;
        
        if (!selectedMode) {
            window.WebGCS?.showMessage('Please select a flight mode', 'error');
            return;
        }
        
        if (selectedMode === currentMode) {
            window.WebGCS?.showMessage(`Already in ${selectedMode} mode`, 'info');
            return;
        }
        
        console.log(`Setting flight mode to: ${selectedMode}`);
        executeCommand('set_mode', { mode: selectedMode });
    }
    
    /**
     * Execute Command
     */
    function executeCommand(command, params = {}) {
        console.log(`Executing flight command: ${command}`, params);
        
        // Disable relevant buttons during command execution
        setCommandInProgress(command, true);
        
        // Send command
        if (window.WebGCS?.sendCommand) {
            const success = window.WebGCS.sendCommand(command, params);
            if (!success) {
                setCommandInProgress(command, false);
            }
        } else {
            window.WebGCS?.showMessage('WebGCS not ready', 'error');
            setCommandInProgress(command, false);
        }
    }
    
    /**
     * Set Command In Progress State
     */
    function setCommandInProgress(command, inProgress) {
        const buttonMap = {
            'arm': elements.armBtn,
            'disarm': elements.disarmBtn,
            'takeoff': elements.takeoffBtn,
            'land': elements.landBtn,
            'rtl': elements.rtlBtn,
            'set_mode': elements.setModeBtn
        };
        
        const button = buttonMap[command];
        if (button) {
            button.disabled = inProgress || !isConnected;
            if (inProgress) {
                button.textContent = button.textContent.replace(/\.\.\.$/, '') + '...';
            } else {
                button.textContent = button.textContent.replace(/\.\.\.$/, '');
            }
        }
        
        // For commands that affect all controls
        if (['arm', 'disarm'].includes(command)) {
            setTimeout(() => updateControlsState(), 1000);
        }
    }
    
    /**
     * Update Controls State
     */
    function updateControlsState() {
        const buttonsConfig = [
            { element: elements.armBtn, enabled: isConnected && !isArmed },
            { element: elements.disarmBtn, enabled: isConnected && isArmed },
            { element: elements.takeoffBtn, enabled: isConnected && isArmed },
            { element: elements.landBtn, enabled: isConnected },
            { element: elements.rtlBtn, enabled: isConnected },
            { element: elements.setModeBtn, enabled: isConnected }
        ];
        
        buttonsConfig.forEach(({ element, enabled }) => {
            if (element) {
                element.disabled = !enabled;
            }
        });
        
        // Update flight mode selector
        if (elements.flightModeSelect) {
            elements.flightModeSelect.disabled = !isConnected;
            
            // Update current mode selection if it matches
            if (currentMode && currentMode !== 'UNKNOWN') {
                const option = elements.flightModeSelect.querySelector(`option[value="${currentMode}"]`);
                if (option) {
                    elements.flightModeSelect.value = currentMode;
                }
            }
        }
    }
    
    /**
     * Validate Takeoff Altitude Input
     */
    function validateTakeoffAltitude(event) {
        const altitude = parseFloat(event.target.value);
        
        if (isNaN(altitude) || altitude < 1 || altitude > 1000) {
            event.target.setCustomValidity('Altitude must be between 1 and 1000 meters');
        } else {
            event.target.setCustomValidity('');
        }
        
        // Update placeholder if valid
        if (!isNaN(altitude) && altitude >= 1 && altitude <= 1000) {
            event.target.setAttribute('data-valid-alt', altitude);
        }
    }
    
    /**
     * Event Handlers
     */
    function handleTelemetryUpdate(event) {
        const data = event.detail || event;
        
        if (!data) return;
        
        // Update state
        const wasArmed = isArmed;
        const oldMode = currentMode;
        
        isArmed = data.armed || false;
        currentMode = data.mode || 'UNKNOWN';
        
        // Check for state changes
        if (wasArmed !== isArmed) {
            const status = isArmed ? 'ARMED' : 'DISARMED';
            window.WebGCS?.showMessage(`Vehicle ${status}`, isArmed ? 'warning' : 'info');
            
            // Announce arm/disarm status
            if (window.WebGCS?.modules?.AudioManager?.announceArmStatus) {
                window.WebGCS.modules.AudioManager.announceArmStatus(isArmed);
            }
        }
        
        if (oldMode !== currentMode && currentMode !== 'UNKNOWN') {
            window.WebGCS?.showMessage(`Flight mode: ${currentMode}`, 'info');
            
            // Announce mode change
            if (window.WebGCS?.modules?.AudioManager?.announceModeChange) {
                window.WebGCS.modules.AudioManager.announceModeChange(currentMode);
            }
        }
        
        // Update UI
        updateControlsState();
    }
    
    function handleConnectionChange(event) {
        const data = event.detail || event;
        isConnected = data ? data.connected : false;
        updateControlsState();
        
        // Reset state on disconnect
        if (!isConnected) {
            isArmed = false;
            currentMode = 'UNKNOWN';
        }
    }
    
    function handleCommandResult(event) {
        const result = event.detail;
        const command = result.command;
        
        // Re-enable buttons
        setCommandInProgress(command, false);
        
        // Handle specific command results
        if (result.success) {
            switch (command) {
                case 'arm':
                    window.WebGCS?.showMessage('Vehicle armed successfully', 'success');
                    break;
                case 'disarm':
                    window.WebGCS?.showMessage('Vehicle disarmed successfully', 'success');
                    break;
                case 'takeoff':
                    window.WebGCS?.showMessage('Takeoff command sent successfully', 'success');
                    break;
                case 'land':
                    window.WebGCS?.showMessage('Landing command sent successfully', 'success');
                    break;
                case 'rtl':
                    window.WebGCS?.showMessage('Return to Launch initiated', 'success');
                    break;
                case 'set_mode':
                    window.WebGCS?.showMessage(`Flight mode change to ${result.params?.mode || 'requested mode'} sent`, 'success');
                    break;
            }
        } else {
            // Command failed
            const errorMsg = result.error || 'Unknown error';
            window.WebGCS?.showMessage(`${command.toUpperCase()} failed: ${errorMsg}`, 'error');
        }
    }
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        
        // State getters
        isArmed: () => isArmed,
        getCurrentMode: () => currentMode,
        isConnected: () => isConnected,
        
        // Module lifecycle callbacks
        onTelemetryUpdate: handleTelemetryUpdate,
        onConnectionChange: handleConnectionChange,
        onResize: () => {
            // Handle responsive layout changes if needed
        }
    };
})();
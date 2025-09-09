/**
 * Flight Controls JavaScript for WebGCS
 * Handles ARM, DISARM, TAKEOFF, LAND, RTL, and Set Mode button functionality
 * 
 * File size: Must stay under 200 lines per WebGCS PRD
 */

// Initialize flight controls when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Flight Controls initializing...');
    
    // Get socket connection from main.js
    const socket = io();
    
    // Flight control button event listeners
    initializeFlightControlButtons(socket);
    
    console.log('Flight Controls initialized');
});

function initializeFlightControlButtons(socket) {
    // ARM button with safety confirmation
    const armButton = document.getElementById('arm-btn');
    if (armButton) {
        armButton.addEventListener('click', function() {
            const confirmed = confirm('⚠️ ARM COMMAND SAFETY CONFIRMATION ⚠️\n\nThis will ARM the drone and enable motors.\nEnsure area is clear and safe for operation.\n\nConfirm ARM command?');
            
            if (confirmed) {
                console.log('ARM command confirmed');
                socket.emit('send_command', {
                    command: 'arm',
                    params: { confirmed: true }
                });
            } else {
                console.log('ARM command cancelled by user');
            }
        });
    }
    
    // DISARM button with safety confirmation  
    const disarmButton = document.getElementById('disarm-btn');
    if (disarmButton) {
        disarmButton.addEventListener('click', function() {
            const confirmed = confirm('⚠️ DISARM COMMAND SAFETY CONFIRMATION ⚠️\n\nThis will DISARM the drone and disable motors.\nEnsure drone is safely landed.\n\nConfirm DISARM command?');
            
            if (confirmed) {
                console.log('DISARM command confirmed');
                socket.emit('send_command', {
                    command: 'disarm',
                    params: { confirmed: true }
                });
            } else {
                console.log('DISARM command cancelled by user');
            }
        });
    }
    
    // TAKEOFF button with altitude validation and safety confirmation
    const takeoffButton = document.getElementById('takeoff-btn');
    const altitudeInput = document.getElementById('takeoff-alt');
    if (takeoffButton && altitudeInput) {
        takeoffButton.addEventListener('click', function() {
            const altitude = parseFloat(altitudeInput.value);
            
            // Validate altitude
            if (isNaN(altitude) || altitude <= 0) {
                alert('❌ INVALID ALTITUDE\n\nTakeoff altitude must be a positive number greater than 0.');
                return;
            }
            
            if (altitude > 100) {
                alert('❌ ALTITUDE TOO HIGH\n\nTakeoff altitude exceeds maximum safe limit of 100m.\nPlease enter a lower altitude.');
                return;
            }
            
            const confirmed = confirm(`⚠️ TAKEOFF COMMAND SAFETY CONFIRMATION ⚠️\n\nThis will command the drone to TAKEOFF to ${altitude}m altitude.\nEnsure area is clear and safe for takeoff.\n\nConfirm TAKEOFF to ${altitude}m?`);
            
            if (confirmed) {
                console.log(`TAKEOFF command confirmed for ${altitude}m`);
                socket.emit('send_command', {
                    command: 'takeoff',
                    params: { 
                        altitude: altitude,
                        confirmed: true 
                    }
                });
            } else {
                console.log('TAKEOFF command cancelled by user');
            }
        });
    }
    
    // LAND button  
    const landButton = document.getElementById('land-btn');
    if (landButton) {
        landButton.addEventListener('click', function() {
            console.log('LAND command sent');
            socket.emit('send_command', {
                command: 'land',
                params: {}
            });
        });
    }
    
    // RTL button (immediate emergency command)
    const rtlButton = document.getElementById('rtl-btn');
    if (rtlButton) {
        rtlButton.addEventListener('click', function() {
            console.log('RTL command sent');
            socket.emit('send_command', {
                command: 'rtl',
                params: {}
            });
        });
    }
    
    // Set Mode button with flight mode dropdown
    const setModeButton = document.getElementById('set-mode-btn');
    const flightModeSelect = document.getElementById('flight-mode');
    if (setModeButton && flightModeSelect) {
        setModeButton.addEventListener('click', function() {
            const selectedMode = flightModeSelect.value;
            
            if (!selectedMode) {
                alert('❌ NO MODE SELECTED\n\nPlease select a flight mode from the dropdown.');
                return;
            }
            
            console.log(`Set mode command sent: ${selectedMode}`);
            socket.emit('send_command', {
                command: 'set_mode',
                params: { 
                    mode: selectedMode 
                }
            });
        });
    }
    
    // Listen for command results
    socket.on('command_result', function(data) {
        console.log('Command result:', data);
        
        if (!data.success && data.message) {
            // Show error message for failed commands
            alert(`❌ COMMAND FAILED\n\nCommand: ${data.command}\nError: ${data.message}`);
        } else if (data.success) {
            console.log(`✅ Command ${data.command} successful`);
        }
    });
}

// Make flight controls available globally if needed
window.webgcs = window.webgcs || {};
window.webgcs.flightControls = {
    initialized: true
};
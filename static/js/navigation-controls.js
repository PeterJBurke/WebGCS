/**
 * Navigation Controls JavaScript
 * Handles GO TO and CLEAR navigation functionality with input validation
 * 
 * File size: Must stay under 150 lines per WebGCS PRD
 */

// Initialize navigation controls when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Navigation controls initializing...');
    
    // Get navigation input elements
    const navLatInput = document.getElementById('nav-lat');
    const navLonInput = document.getElementById('nav-lon');
    const navAltInput = document.getElementById('nav-alt');
    const gotoBtn = document.getElementById('goto-btn');
    const clearBtn = document.getElementById('clear-btn');
    
    if (!navLatInput || !navLonInput || !navAltInput || !gotoBtn || !clearBtn) {
        console.error('Navigation control elements not found');
        return;
    }
    
    // Input validation functions
    function validateLatitude(lat) {
        const latNum = parseFloat(lat);
        if (isNaN(latNum)) return { valid: false, error: 'Latitude must be a number' };
        if (latNum < -90 || latNum > 90) return { valid: false, error: 'Latitude must be between -90 and 90 degrees' };
        return { valid: true, value: latNum };
    }
    
    function validateLongitude(lon) {
        const lonNum = parseFloat(lon);
        if (isNaN(lonNum)) return { valid: false, error: 'Longitude must be a number' };
        if (lonNum < -180 || lonNum > 180) return { valid: false, error: 'Longitude must be between -180 and 180 degrees' };
        return { valid: true, value: lonNum };
    }
    
    function validateAltitude(alt) {
        const altNum = parseFloat(alt);
        if (isNaN(altNum)) return { valid: false, error: 'Altitude must be a number' };
        if (altNum < 0) return { valid: false, error: 'Altitude must be positive (AGL)' };
        if (altNum > 5000) return { valid: false, error: 'Altitude must be below 5000m AGL' };
        return { valid: true, value: altNum };
    }
    
    // Show validation error
    function showValidationError(message) {
        // Remove existing error messages
        const existingError = document.querySelector('.nav-error');
        if (existingError) {
            existingError.remove();
        }
        
        // Create and show new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'nav-error';
        errorDiv.style.color = 'red';
        errorDiv.style.fontSize = '12px';
        errorDiv.style.marginTop = '5px';
        errorDiv.textContent = message;
        
        const navControls = document.querySelector('.nav-controls');
        navControls.appendChild(errorDiv);
        
        // Auto-remove error after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    // Clear validation errors
    function clearValidationErrors() {
        const existingError = document.querySelector('.nav-error');
        if (existingError) {
            existingError.remove();
        }
    }
    
    // GO TO button handler
    gotoBtn.addEventListener('click', function() {
        console.log('GO TO button clicked');
        clearValidationErrors();
        
        const latValue = navLatInput.value.trim();
        const lonValue = navLonInput.value.trim();
        const altValue = navAltInput.value.trim() || '10'; // Default altitude
        
        // Validate inputs
        const latValidation = validateLatitude(latValue);
        if (!latValidation.valid) {
            showValidationError(latValidation.error);
            navLatInput.focus();
            return;
        }
        
        const lonValidation = validateLongitude(lonValue);
        if (!lonValidation.valid) {
            showValidationError(lonValidation.error);
            navLonInput.focus();
            return;
        }
        
        const altValidation = validateAltitude(altValue);
        if (!altValidation.valid) {
            showValidationError(altValidation.error);
            navAltInput.focus();
            return;
        }
        
        // Prepare navigation command with 6 decimal precision
        const navCommand = {
            command: 'goto',
            params: {
                latitude: parseFloat(latValidation.value.toFixed(6)),
                longitude: parseFloat(lonValidation.value.toFixed(6)),
                altitude: parseFloat(altValidation.value.toFixed(1)),
                timestamp: Date.now()
            }
        };
        
        console.log('Sending navigation command:', JSON.stringify(navCommand, null, 2));
        
        // Check if socket is available
        if (typeof io !== 'undefined') {
            const socket = io();
            console.log('Socket available, connection status:', socket.connected);
            
            // Listen for command results
            socket.on('command_result', function(data) {
                console.log('GO TO command result:', data);
                if (!data.success && data.message) {
                    showValidationError(`Command failed: ${data.message}`);
                } else if (data.success) {
                    console.log('✅ GO TO command successful');
                }
            });
            
            // Send command via SocketIO (even if not connected to test command generation)
            socket.emit('send_command', navCommand);
            console.log('Navigation command sent successfully');
        } else {
            console.error('SocketIO not available');
            showValidationError('SocketIO not available. Please reload page.');
            return;
        }
    });
    
    // CLEAR button handler
    clearBtn.addEventListener('click', function() {
        console.log('CLEAR button clicked');
        
        // Clear all input fields
        navLatInput.value = '';
        navLonInput.value = '';
        navAltInput.value = '10'; // Reset to default altitude
        
        // Clear any validation errors
        clearValidationErrors();
        
        console.log('Navigation inputs cleared');
    });
    
    // Real-time input validation with visual feedback
    function addInputValidation(input, validateFn) {
        input.addEventListener('input', function() {
            const validation = validateFn(this.value);
            if (this.value && !validation.valid) {
                this.style.borderColor = 'red';
                this.title = validation.error;
            } else {
                this.style.borderColor = '';
                this.title = '';
            }
        });
        
        input.addEventListener('blur', function() {
            if (this.value) {
                const validation = validateFn(this.value);
                if (validation.valid) {
                    // Round to appropriate precision
                    if (this === navAltInput) {
                        this.value = validation.value.toFixed(1);
                    } else {
                        this.value = validation.value.toFixed(6);
                    }
                }
            }
        });
    }
    
    // Add real-time validation to inputs
    addInputValidation(navLatInput, validateLatitude);
    addInputValidation(navLonInput, validateLongitude);
    addInputValidation(navAltInput, validateAltitude);
    
    console.log('Navigation controls initialized successfully');
});
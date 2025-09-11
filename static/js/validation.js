/**
 * WebGCS Input Validation
 * Handles input validation and safety checks for user inputs.
 */

class InputValidation {
    constructor() {
        this.validators = new Map();
        this.errorMessages = new Map();
    }

    /**
     * Initialize input validation
     */
    initialize() {
        console.log('Initializing input validation...');
        this.setupValidators();
        this.bindInputEvents();
    }

    /**
     * Setup validation rules for different input types
     */
    setupValidators() {
        // Coordinate validators
        this.validators.set('latitude', (value) => {
            const num = parseFloat(value);
            return !isNaN(num) && num >= -90 && num <= 90;
        });

        this.validators.set('longitude', (value) => {
            const num = parseFloat(value);
            return !isNaN(num) && num >= -180 && num <= 180;
        });

        this.validators.set('altitude', (value) => {
            const num = parseFloat(value);
            return !isNaN(num) && num >= 0 && num <= 1000;
        });

        this.validators.set('takeoff-altitude', (value) => {
            const num = parseFloat(value);
            return !isNaN(num) && num >= 1 && num <= 100;
        });

        // Speed validators
        this.validators.set('speed', (value) => {
            const num = parseFloat(value);
            return !isNaN(num) && num >= 0 && num <= 30;
        });

        // Angle validators
        this.validators.set('heading', (value) => {
            const num = parseFloat(value);
            return !isNaN(num) && num >= 0 && num < 360;
        });

        // Error messages
        this.errorMessages.set('latitude', 'Latitude must be between -90 and 90 degrees');
        this.errorMessages.set('longitude', 'Longitude must be between -180 and 180 degrees');
        this.errorMessages.set('altitude', 'Altitude must be between 0 and 1000 meters');
        this.errorMessages.set('takeoff-altitude', 'Takeoff altitude must be between 1 and 100 meters');
        this.errorMessages.set('speed', 'Speed must be between 0 and 30 m/s');
        this.errorMessages.set('heading', 'Heading must be between 0 and 359 degrees');
    }

    /**
     * Bind validation events to input fields
     */
    bindInputEvents() {
        // Navigation inputs
        this.bindValidation('goto-latitude', 'latitude');
        this.bindValidation('goto-longitude', 'longitude');
        this.bindValidation('goto-altitude', 'altitude');
        
        // Takeoff input
        this.bindValidation('takeoff-altitude', 'takeoff-altitude');
        
        // Speed inputs
        this.bindValidation('speed-input', 'speed');
        
        // Heading input
        this.bindValidation('heading-input', 'heading');
    }

    /**
     * Bind validation to specific input field
     */
    bindValidation(inputId, validationType) {
        const input = document.getElementById(inputId);
        if (!input) return;

        // Real-time validation on input
        input.addEventListener('input', (event) => {
            this.validateInput(event.target, validationType);
        });

        // Validation on blur
        input.addEventListener('blur', (event) => {
            this.validateInput(event.target, validationType);
        });

        // Initial validation if value exists
        if (input.value) {
            this.validateInput(input, validationType);
        }
    }

    /**
     * Validate individual input field
     */
    validateInput(input, validationType) {
        const value = input.value.trim();
        const validator = this.validators.get(validationType);
        
        if (!validator) {
            console.warn(`No validator found for type: ${validationType}`);
            return true;
        }

        const isValid = value === '' || validator(value);
        this.updateInputState(input, isValid, validationType);
        
        return isValid;
    }

    /**
     * Update input field visual state
     */
    updateInputState(input, isValid, validationType) {
        // Remove existing validation classes
        input.classList.remove('valid', 'invalid');
        
        // Add appropriate class
        if (input.value.trim() !== '') {
            input.classList.add(isValid ? 'valid' : 'invalid');
        }

        // Update error message
        const errorElement = document.getElementById(`${input.id}-error`);
        if (errorElement) {
            if (!isValid && input.value.trim() !== '') {
                errorElement.textContent = this.errorMessages.get(validationType) || 'Invalid input';
                errorElement.style.display = 'block';
            } else {
                errorElement.textContent = '';
                errorElement.style.display = 'none';
            }
        }
    }

    /**
     * Validate all inputs in a form
     */
    validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return true;

        let allValid = true;
        const inputs = form.querySelectorAll('input[type="number"], input[type="text"]');
        
        inputs.forEach(input => {
            const validationType = this.getValidationType(input);
            if (validationType) {
                const isValid = this.validateInput(input, validationType);
                if (!isValid) allValid = false;
            }
        });

        return allValid;
    }

    /**
     * Get validation type based on input attributes
     */
    getValidationType(input) {
        // Check data attribute first
        if (input.dataset.validation) {
            return input.dataset.validation;
        }

        // Infer from ID
        const id = input.id.toLowerCase();
        if (id.includes('latitude')) return 'latitude';
        if (id.includes('longitude')) return 'longitude';
        if (id.includes('altitude')) return 'altitude';
        if (id.includes('speed')) return 'speed';
        if (id.includes('heading')) return 'heading';
        
        return null;
    }

    /**
     * Validate coordinate inputs specifically
     */
    validateCoordinates(latitude, longitude, altitude) {
        const errors = [];

        if (!this.validators.get('latitude')(latitude)) {
            errors.push(this.errorMessages.get('latitude'));
        }

        if (!this.validators.get('longitude')(longitude)) {
            errors.push(this.errorMessages.get('longitude'));
        }

        if (altitude !== undefined && !this.validators.get('altitude')(altitude)) {
            errors.push(this.errorMessages.get('altitude'));
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Show validation errors to user
     */
    showValidationErrors(errors) {
        if (errors.length === 0) return;

        const message = 'Please correct the following errors:\n' + errors.join('\n');
        alert(message);
    }

    /**
     * Validate mission parameters
     */
    validateMissionParams(params) {
        const errors = [];

        // Check required fields
        if (!params.waypoints || params.waypoints.length === 0) {
            errors.push('Mission must contain at least one waypoint');
        }

        // Validate each waypoint
        if (params.waypoints) {
            params.waypoints.forEach((waypoint, index) => {
                const coordValidation = this.validateCoordinates(
                    waypoint.latitude,
                    waypoint.longitude,
                    waypoint.altitude
                );

                if (!coordValidation.valid) {
                    errors.push(`Waypoint ${index + 1}: ${coordValidation.errors.join(', ')}`);
                }
            });
        }

        // Validate speeds
        if (params.speed !== undefined && !this.validators.get('speed')(params.speed)) {
            errors.push(this.errorMessages.get('speed'));
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Safety check for flight operations
     */
    performSafetyCheck(operation, params = {}) {
        const warnings = [];
        const errors = [];

        switch (operation) {
            case 'takeoff':
                if (params.altitude > 50) {
                    warnings.push('High takeoff altitude detected');
                }
                break;

            case 'goto_waypoint':
                const distance = this.calculateDistance(params);
                if (distance > 1000) {
                    warnings.push('Long distance waypoint detected');
                }
                break;

            case 'set_speed':
                if (params.speed > 15) {
                    warnings.push('High speed setting detected');
                }
                break;

            case 'rtl':
                // No specific warnings for RTL
                break;

            default:
                break;
        }

        return {
            safe: errors.length === 0,
            warnings: warnings,
            errors: errors
        };
    }

    /**
     * Calculate distance (simplified)
     */
    calculateDistance(params) {
        // Simple distance calculation for safety checks
        const currentPos = window.WebGCS.telemetryData;
        if (!currentPos || !params.latitude || !params.longitude) {
            return 0;
        }

        const lat1 = currentPos.latitude || 0;
        const lon1 = currentPos.longitude || 0;
        const lat2 = params.latitude;
        const lon2 = params.longitude;

        // Simplified distance calculation (not accurate for real use)
        const dlat = Math.abs(lat2 - lat1);
        const dlon = Math.abs(lon2 - lon1);
        
        return Math.sqrt(dlat * dlat + dlon * dlon) * 111000; // Rough conversion to meters
    }

    /**
     * Clear all validation states
     */
    clearValidation() {
        const inputs = document.querySelectorAll('.valid, .invalid');
        inputs.forEach(input => {
            input.classList.remove('valid', 'invalid');
        });

        const errors = document.querySelectorAll('[id$="-error"]');
        errors.forEach(error => {
            error.textContent = '';
            error.style.display = 'none';
        });
    }
}

// Export for use in main.js
window.InputValidation = InputValidation;
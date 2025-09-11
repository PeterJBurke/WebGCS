/**
 * WebGCS Telemetry Display
 * Handles real-time telemetry data display and updates.
 */

class TelemetryDisplay {
    constructor() {
        this.lastUpdate = 0;
        this.updateRate = 100; // 10Hz updates
        this.elements = new Map();
    }

    /**
     * Initialize telemetry display
     */
    initialize() {
        console.log('Initializing telemetry display...');
        this.cacheElements();
        this.startUpdateLoop();
    }

    /**
     * Cache DOM elements for performance
     */
    cacheElements() {
        // Basic telemetry elements
        this.elements.set('latitude', document.getElementById('telemetry-latitude'));
        this.elements.set('longitude', document.getElementById('telemetry-longitude'));
        this.elements.set('altitude', document.getElementById('telemetry-altitude'));
        this.elements.set('relative_altitude', document.getElementById('telemetry-relative-altitude'));
        this.elements.set('groundspeed', document.getElementById('telemetry-groundspeed'));
        this.elements.set('airspeed', document.getElementById('telemetry-airspeed'));
        this.elements.set('heading', document.getElementById('telemetry-heading'));
        this.elements.set('roll', document.getElementById('telemetry-roll'));
        this.elements.set('pitch', document.getElementById('telemetry-pitch'));
        this.elements.set('yaw', document.getElementById('telemetry-yaw'));
        
        // System status elements
        this.elements.set('battery_voltage', document.getElementById('telemetry-battery-voltage'));
        this.elements.set('battery_current', document.getElementById('telemetry-battery-current'));
        this.elements.set('battery_remaining', document.getElementById('telemetry-battery-remaining'));
        this.elements.set('flight_mode', document.getElementById('telemetry-flight-mode'));
        this.elements.set('armed', document.getElementById('telemetry-armed'));
        this.elements.set('gps_fix', document.getElementById('telemetry-gps-fix'));
        this.elements.set('satellites', document.getElementById('telemetry-satellites'));
        
        // Connection status
        this.elements.set('connection_quality', document.getElementById('telemetry-connection-quality'));
        this.elements.set('last_heartbeat', document.getElementById('telemetry-last-heartbeat'));
    }

    /**
     * Start update loop for telemetry display
     */
    startUpdateLoop() {
        setInterval(() => {
            this.updateDisplay(window.WebGCS.telemetryData);
        }, this.updateRate);
    }

    /**
     * Update telemetry display with new data
     */
    updateDisplay(data) {
        if (!data || Object.keys(data).length === 0) {
            return;
        }

        const currentTime = Date.now();
        
        // FIX: Map real telemetry data structure
        const mappedData = this.mapTelemetryData(data);
        
        // Update basic telemetry
        this.updateElement('latitude', mappedData.latitude, (val) => this.formatCoordinate(val, 'lat'));
        this.updateElement('longitude', mappedData.longitude, (val) => this.formatCoordinate(val, 'lon'));
        this.updateElement('altitude', mappedData.altitude, (val) => `${this.formatNumber(val, 1)}m`);
        this.updateElement('relative_altitude', mappedData.relative_altitude, (val) => `${this.formatNumber(val, 1)}m`);
        this.updateElement('groundspeed', mappedData.groundspeed, (val) => `${this.formatNumber(val, 1)} m/s`);
        this.updateElement('airspeed', mappedData.airspeed, (val) => `${this.formatNumber(val, 1)} m/s`);
        this.updateElement('heading', mappedData.heading, (val) => `${this.formatNumber(val, 0)}°`);
        
        // Update attitude
        this.updateElement('roll', mappedData.roll, (val) => `${this.formatNumber(val, 1)}°`);
        this.updateElement('pitch', mappedData.pitch, (val) => `${this.formatNumber(val, 1)}°`);
        this.updateElement('yaw', mappedData.yaw, (val) => `${this.formatNumber(val, 1)}°`);
        
        // Update system status
        this.updateElement('battery_voltage', mappedData.battery_voltage, (val) => `${this.formatNumber(val, 2)}V`);
        this.updateElement('battery_current', mappedData.battery_current, (val) => `${this.formatNumber(val, 1)}A`);
        this.updateElement('battery_remaining', mappedData.battery_remaining, (val) => `${Math.round(val)}%`);
        this.updateElement('flight_mode', mappedData.flight_mode);
        this.updateElement('armed', mappedData.armed, (val) => val ? 'ARMED' : 'DISARMED');
        this.updateElement('gps_fix', mappedData.gps_fix_type, (val) => this.formatGPSFix(val));
        this.updateElement('satellites', mappedData.satellites_visible, (val) => `${val || 0}`);
        
        // Update connection info
        this.updateElement('connection_quality', mappedData.connection_quality, (val) => `${Math.round(val || 0)}%`);
        this.updateElement('last_heartbeat', currentTime, (val) => this.formatTimestamp(val));
        
        // Update status indicators
        this.updateStatusIndicators(mappedData);
        
        this.lastUpdate = currentTime;
    }
    
    /**
     * Map raw telemetry data to display format
     */
    mapTelemetryData(telemetryData) {
        const mapped = {};
        
        // GPS data
        if (telemetryData.gps) {
            mapped.latitude = telemetryData.gps.lat;
            mapped.longitude = telemetryData.gps.lon;
            mapped.altitude = telemetryData.gps.alt;
            mapped.relative_altitude = telemetryData.gps.relative_alt;
        }
        
        // VFR HUD data
        if (telemetryData.vfr_hud) {
            mapped.airspeed = telemetryData.vfr_hud.airspeed;
            mapped.groundspeed = telemetryData.vfr_hud.groundspeed;
            mapped.heading = telemetryData.vfr_hud.heading;
        }
        
        // Attitude data (already in degrees)
        if (telemetryData.attitude) {
            mapped.roll = telemetryData.attitude.roll;
            mapped.pitch = telemetryData.attitude.pitch;
            mapped.yaw = telemetryData.attitude.yaw;
        }
        
        // Battery/system status
        if (telemetryData.sys_status) {
            mapped.battery_voltage = telemetryData.sys_status.voltage_battery;
            mapped.battery_current = telemetryData.sys_status.current_battery;
            mapped.battery_remaining = telemetryData.sys_status.battery_remaining;
        }
        
        // Flight mode and armed status
        if (telemetryData.heartbeat) {
            mapped.flight_mode = telemetryData.heartbeat.flight_mode;
            mapped.armed = telemetryData.heartbeat.armed;
        }
        
        // Connection quality (calculated from drop rate)
        if (telemetryData.sys_status && telemetryData.sys_status.drop_rate_comm !== undefined) {
            mapped.connection_quality = 100 - (telemetryData.sys_status.drop_rate_comm * 100);
        } else {
            mapped.connection_quality = 100; // Assume good if no data
        }
        
        return mapped;
    }

    /**
     * Update individual element with formatting
     */
    updateElement(key, value, formatter = null) {
        const element = this.elements.get(key);
        if (element && value !== undefined && value !== null) {
            const displayValue = formatter ? formatter(value) : value.toString();
            if (element.textContent !== displayValue) {
                element.textContent = displayValue;
            }
        }
    }

    /**
     * Update status indicators with color coding
     */
    updateStatusIndicators(data) {
        // Armed status indicator
        const armedElement = this.elements.get('armed');
        if (armedElement) {
            armedElement.className = `status ${data.armed ? 'armed' : 'disarmed'}`;
        }
        
        // GPS fix indicator
        const gpsElement = this.elements.get('gps_fix');
        if (gpsElement && data.gps_fix_type !== undefined) {
            let gpsClass = 'no-fix';
            if (data.gps_fix_type >= 3) gpsClass = 'fix-3d';
            else if (data.gps_fix_type >= 2) gpsClass = 'fix-2d';
            gpsElement.className = `status ${gpsClass}`;
        }
        
        // Battery status indicator
        const batteryElement = this.elements.get('battery_remaining');
        if (batteryElement && data.battery_remaining !== undefined) {
            let batteryClass = 'battery-normal';
            if (data.battery_remaining < 20) batteryClass = 'battery-low';
            else if (data.battery_remaining < 30) batteryClass = 'battery-warning';
            batteryElement.className = `status ${batteryClass}`;
        }
        
        // Connection quality indicator
        const connectionElement = this.elements.get('connection_quality');
        if (connectionElement && data.connection_quality !== undefined) {
            let connectionClass = 'connection-poor';
            if (data.connection_quality > 80) connectionClass = 'connection-excellent';
            else if (data.connection_quality > 60) connectionClass = 'connection-good';
            else if (data.connection_quality > 40) connectionClass = 'connection-fair';
            connectionElement.className = `status ${connectionClass}`;
        }
    }

    /**
     * Format coordinate display
     */
    formatCoordinate(value, type) {
        if (value === undefined || value === null) return 'N/A';
        
        const degrees = Math.abs(value);
        const direction = type === 'lat' ? (value >= 0 ? 'N' : 'S') : (value >= 0 ? 'E' : 'W');
        
        return `${this.formatNumber(degrees, 6)}° ${direction}`;
    }

    /**
     * Format GPS fix type
     */
    formatGPSFix(fixType) {
        switch (fixType) {
            case 0: return 'No Fix';
            case 1: return 'Dead Reckoning';
            case 2: return '2D Fix';
            case 3: return '3D Fix';
            case 4: return 'DGPS';
            case 5: return 'RTK Float';
            case 6: return 'RTK Fixed';
            default: return `Fix ${fixType}`;
        }
    }

    /**
     * Format timestamp for display
     */
    formatTimestamp(timestamp) {
        const now = Date.now();
        const diff = now - timestamp;
        
        if (diff < 1000) return 'Just now';
        if (diff < 60000) return `${Math.round(diff / 1000)}s ago`;
        if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
        
        return new Date(timestamp).toLocaleTimeString();
    }

    /**
     * Format number with specified decimals
     */
    formatNumber(value, decimals = 1) {
        if (value === undefined || value === null || isNaN(value)) return 'N/A';
        return parseFloat(value).toFixed(decimals);
    }

    /**
     * Get telemetry age in milliseconds
     */
    getTelemetryAge() {
        return Date.now() - this.lastUpdate;
    }

    /**
     * Check if telemetry is stale
     */
    isTelemetryStale() {
        return this.getTelemetryAge() > 5000; // 5 seconds
    }
}

// Export for use in main.js
window.TelemetryDisplay = TelemetryDisplay;
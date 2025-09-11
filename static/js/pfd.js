/**
 * WebGCS Primary Flight Display (VFR HUD)
 * Implements professional glass cockpit display with 15 components.
 */

class PrimaryFlightDisplay {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.width = 800;
        this.height = 600;
        this.center = { x: 400, y: 300 };
        this.data = {};
        this.lastUpdate = 0;
    }

    /**
     * Initialize the Primary Flight Display
     */
    initialize() {
        console.log('Initializing Primary Flight Display...');
        this.setupCanvas();
        this.startRenderLoop();
    }

    /**
     * Setup canvas element
     */
    setupCanvas() {
        this.canvas = document.getElementById('pfd-canvas');
        if (!this.canvas) {
            console.error('PFD canvas not found');
            return;
        }

        this.canvas.width = this.width;
        this.canvas.height = this.height;
        this.ctx = this.canvas.getContext('2d');
        
        // Set initial styling
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
    }

    /**
     * Start render loop for 10Hz updates
     */
    startRenderLoop() {
        setInterval(() => {
            this.render();
        }, 100); // 10Hz update rate
    }

    /**
     * Update display with new telemetry data
     */
    updateDisplay(data) {
        if (!data) return;
        
        // FIX: Map telemetry data to PFD data structure
        const mappedData = this.mapTelemetryData(data);
        this.data = { ...this.data, ...mappedData };
        this.lastUpdate = Date.now();
    }
    
    /**
     * Map raw telemetry data to PFD display format
     */
    mapTelemetryData(telemetryData) {
        const mapped = {};
        
        // Attitude data
        if (telemetryData.attitude) {
            mapped.roll = telemetryData.attitude.roll * Math.PI / 180; // Convert to radians
            mapped.pitch = telemetryData.attitude.pitch * Math.PI / 180;
            mapped.yaw = telemetryData.attitude.yaw * Math.PI / 180;
            mapped.yawspeed = telemetryData.attitude.yawspeed;
        }
        
        // VFR HUD data
        if (telemetryData.vfr_hud) {
            mapped.airspeed = telemetryData.vfr_hud.airspeed;
            mapped.groundspeed = telemetryData.vfr_hud.groundspeed;
            mapped.heading = telemetryData.vfr_hud.heading * Math.PI / 180;
            mapped.climb_rate = telemetryData.vfr_hud.climb;
        }
        
        // GPS data
        if (telemetryData.gps) {
            mapped.lat = telemetryData.gps.lat;
            mapped.lon = telemetryData.gps.lon;
            mapped.relative_altitude = telemetryData.gps.relative_alt;
        }
        
        // Battery data
        if (telemetryData.sys_status) {
            mapped.battery_voltage = telemetryData.sys_status.voltage_battery;
            mapped.battery_current = telemetryData.sys_status.current_battery;
            mapped.battery_remaining = telemetryData.sys_status.battery_remaining;
        }
        
        // Armed status and flight mode
        if (telemetryData.heartbeat) {
            mapped.armed = telemetryData.heartbeat.armed;
            mapped.flight_mode = telemetryData.heartbeat.flight_mode;
        }
        
        return mapped;
    }

    /**
     * Main render function
     */
    render() {
        if (!this.ctx) return;

        // Clear canvas
        this.ctx.fillStyle = '#000033';
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Render all HUD components based on reference layout
        this.renderArtificialHorizon();    // Component 11
        this.renderAircraftAttitude();     // Component 12
        this.renderAirspeed();            // Components 1, 8
        this.renderCrosstrackError();     // Component 2
        this.renderHeadingDirection();    // Component 3
        this.renderBankAngle();           // Component 4
        this.renderTelemetryLink();       // Component 5
        this.renderGPSTime();             // Component 6
        this.renderAltitude();            // Component 7
        this.renderGroundspeed();         // Component 9
        this.renderBatteryStatus();       // Component 10
        this.renderGPSStatus();           // Component 13
        this.renderWaypointInfo();        // Component 14
        this.renderFlightMode();          // Component 15
        
        // Render armed/disarmed overlay
        this.renderArmedStatus();
    }

    /**
     * Component 11: Artificial Horizon
     */
    renderArtificialHorizon() {
        const roll = this.data.roll || 0;
        const pitch = this.data.pitch || 0;
        
        this.ctx.save();
        this.ctx.translate(this.center.x, this.center.y);
        this.ctx.rotate(roll);

        // Sky (blue)
        this.ctx.fillStyle = '#4A90E2';
        this.ctx.fillRect(-300, -300 - pitch * 100, 600, 300 + pitch * 100);

        // Ground (green/brown)
        this.ctx.fillStyle = '#8B4513';
        this.ctx.fillRect(-300, -pitch * 100, 600, 300 + pitch * 100);

        // Horizon line
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(-300, -pitch * 100);
        this.ctx.lineTo(300, -pitch * 100);
        this.ctx.stroke();

        // Pitch ladder
        this.renderPitchLadder(pitch);

        this.ctx.restore();
    }

    /**
     * Render pitch ladder lines
     */
    renderPitchLadder(pitch) {
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 1;
        this.ctx.font = '14px Arial';
        this.ctx.fillStyle = '#FFFFFF';

        for (let angle = -60; angle <= 60; angle += 10) {
            const y = -angle * 100 / 57.3 + pitch * 100; // Convert to pixels
            
            if (Math.abs(y) < 200) {
                this.ctx.beginPath();
                const lineWidth = angle % 20 === 0 ? 60 : 30;
                this.ctx.moveTo(-lineWidth, y);
                this.ctx.lineTo(lineWidth, y);
                this.ctx.stroke();
                
                if (angle !== 0 && angle % 20 === 0) {
                    this.ctx.fillText(angle.toString(), lineWidth + 15, y);
                    this.ctx.fillText(angle.toString(), -lineWidth - 15, y);
                }
            }
        }
    }

    /**
     * Component 12: Aircraft Attitude (center symbol)
     */
    renderAircraftAttitude() {
        this.ctx.strokeStyle = '#FF0000';
        this.ctx.lineWidth = 3;
        this.ctx.fillStyle = '#FF0000';

        // Center aircraft symbol
        this.ctx.beginPath();
        this.ctx.moveTo(this.center.x - 30, this.center.y);
        this.ctx.lineTo(this.center.x - 10, this.center.y);
        this.ctx.moveTo(this.center.x + 10, this.center.y);
        this.ctx.lineTo(this.center.x + 30, this.center.y);
        this.ctx.moveTo(this.center.x, this.center.y);
        this.ctx.lineTo(this.center.x, this.center.y - 10);
        this.ctx.stroke();

        // Center dot
        this.ctx.beginPath();
        this.ctx.arc(this.center.x, this.center.y, 3, 0, 2 * Math.PI);
        this.ctx.fill();
    }

    /**
     * Components 1, 8: Airspeed displays
     */
    renderAirspeed() {
        const airspeed = this.data.airspeed || 0;
        const groundspeed = this.data.groundspeed || 0;
        
        // Position 1: Top left
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 18px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`AS ${airspeed.toFixed(1)}`, 20, 50);
        
        // Position 8: Bottom left
        this.ctx.fillText(`AS ${airspeed.toFixed(1)}`, 20, this.height - 50);
    }

    /**
     * Component 2: Crosstrack error and turn rate
     */
    renderCrosstrackError() {
        const turnRate = this.data.yawspeed || 0;
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '16px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`T ${turnRate.toFixed(1)}`, 120, 50);
    }

    /**
     * Component 3: Heading direction
     */
    renderHeadingDirection() {
        const heading = this.data.heading || 0;
        const headingDeg = Math.round(heading * 180 / Math.PI);
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 18px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(`${headingDeg.toString().padStart(3, '0')}°`, this.center.x, 50);
        
        // Compass directions
        const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        const dirIndex = Math.round(headingDeg / 45) % 8;
        this.ctx.font = '14px Arial';
        this.ctx.fillText(directions[dirIndex], this.center.x + 50, 50);
    }

    /**
     * Component 4: Bank angle indicator
     */
    renderBankAngle() {
        const roll = this.data.roll || 0;
        const rollDeg = Math.round(roll * 180 / Math.PI);
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '16px Arial';
        this.ctx.textAlign = 'right';
        this.ctx.fillText(`${rollDeg}°`, this.width - 20, 70);
    }

    /**
     * Component 5: Telemetry connection link quality
     */
    renderTelemetryLink() {
        const quality = this.data.connection_quality || 0;
        
        this.ctx.fillStyle = quality > 50 ? '#00FF00' : '#FF0000';
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'right';
        this.ctx.fillText(`${Math.round(quality)}%`, this.width - 20, 50);
    }

    /**
     * Component 6: GPS time
     */
    renderGPSTime() {
        const now = new Date();
        const timeStr = now.toTimeString().split(' ')[0];
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'right';
        this.ctx.fillText(timeStr, this.width - 20, 90);
    }

    /**
     * Component 7: Altitude with rate of climb
     */
    renderAltitude() {
        const altitude = this.data.relative_altitude || 0;
        const climbRate = this.data.climb_rate || 0;
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 18px Arial';
        this.ctx.textAlign = 'right';
        this.ctx.fillText(`${altitude.toFixed(1)}m`, this.width - 20, this.center.y);
        
        // Climb rate bar (blue)
        this.ctx.fillStyle = '#4A90E2';
        this.ctx.fillRect(this.width - 15, this.center.y - 50, 10, Math.min(Math.abs(climbRate) * 10, 50));
    }

    /**
     * Component 9: Groundspeed
     */
    renderGroundspeed() {
        const groundspeed = this.data.groundspeed || 0;
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 18px Arial';
        this.ctx.textAlign = 'left';
        this.ctx.fillText(`GS ${groundspeed.toFixed(1)}`, 20, this.height - 80);
    }

    /**
     * Component 10: Battery status
     */
    renderBatteryStatus() {
        const voltage = this.data.battery_voltage || 0;
        const current = this.data.battery_current || 0;
        const remaining = this.data.battery_remaining || 0;
        
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'left';
        
        // Battery info
        this.ctx.fillStyle = remaining > 30 ? '#FFFFFF' : '#FF0000';
        this.ctx.fillText(`Bat ${voltage.toFixed(1)}v ${remaining}%`, 20, this.height - 110);
    }

    /**
     * Component 13: GPS Status
     */
    renderGPSStatus() {
        const gpsFixType = this.data.gps_fix_type || 0;
        const satellites = this.data.satellites_visible || 0;
        
        let gpsText = 'GPS: No Fix';
        let color = '#FF0000';
        
        if (gpsFixType >= 3) {
            gpsText = 'GPS: 3D Fix';
            color = '#00FF00';
        } else if (gpsFixType >= 2) {
            gpsText = 'GPS: 2D Fix';
            color = '#FFFF00';
        }
        
        this.ctx.fillStyle = color;
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'right';
        this.ctx.fillText(gpsText, this.width - 20, this.height - 50);
    }

    /**
     * Component 14: Distance to Waypoint > Current Waypoint Number
     */
    renderWaypointInfo() {
        const waypointDistance = this.data.waypoint_distance || 0;
        const currentWaypoint = this.data.current_waypoint || 0;
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '14px Arial';
        this.ctx.textAlign = 'center';
        
        if (currentWaypoint > 0) {
            this.ctx.fillText(`${waypointDistance.toFixed(0)}m > ${currentWaypoint}`, this.center.x + 150, this.height - 50);
        } else {
            this.ctx.fillText('Stabilize', this.center.x + 150, this.height - 50);
        }
    }

    /**
     * Component 15: Current Flight Mode
     */
    renderFlightMode() {
        const flightMode = this.data.flight_mode || 'UNKNOWN';
        
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = 'bold 16px Arial';
        this.ctx.textAlign = 'right';
        this.ctx.fillText(flightMode, this.width - 20, this.height - 20);
    }

    /**
     * Render ARMED/DISARMED status overlay
     */
    renderArmedStatus() {
        const armed = this.data.armed || false;
        
        this.ctx.font = 'bold 24px Arial';
        this.ctx.textAlign = 'center';
        
        if (armed) {
            this.ctx.fillStyle = '#FF0000';
            this.ctx.fillText('ARMED', this.center.x, this.center.y + 80);
        } else {
            this.ctx.fillStyle = '#FFFFFF';
            this.ctx.fillText('DISARMED', this.center.x, this.center.y + 80);
        }
    }
}

// Export for use in main.js
window.PrimaryFlightDisplay = PrimaryFlightDisplay;
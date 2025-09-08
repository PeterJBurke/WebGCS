/**
 * Clean HUD Telemetry Display Module - Based on Screenshot Layout
 * Simplified glass cockpit display matching the provided reference
 */

window.TelemetryDisplay = (function() {
    'use strict';
    
    // Private variables
    let telemetryData = {};
    let animationFrameId = null;
    let ctx = null;
    let canvas = null;
    
    // Animation and smoothing variables
    let smoothedValues = {
        airspeed: 0,
        altitude: 0,
        heading: 0,
        pitch: 0,
        roll: 0
    };
    
    // Display constants matching screenshot layout
    const DISPLAY = {
        WIDTH: 640,
        HEIGHT: 480,
        ATTITUDE_CENTER_X: 320,
        ATTITUDE_CENTER_Y: 240,
        ATTITUDE_WIDTH: 300,
        ATTITUDE_HEIGHT: 280
    };
    
    // Clean color scheme matching screenshot
    const COLORS = {
        SKY_BLUE: '#4A90E2',
        EARTH_BROWN: '#8B4513',
        HORIZON_WHITE: '#FFFFFF',
        TEXT_WHITE: '#FFFFFF',
        TEXT_GREEN: '#00FF00',
        TEXT_YELLOW: '#FFFF00',
        DISPLAY_BG: '#000000',
        TICKER_BG: 'rgba(0, 0, 0, 0.8)',
        TICKER_BORDER: '#333333'
    };
    
    /**
     * Initialize Clean HUD Display
     */
    function initialize() {
        console.log('Initializing Clean HUD Display...');
        
        canvas = document.getElementById('glass-pfd-display');
        if (!canvas) {
            console.error('HUD canvas not found');
            return;
        }
        
        ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('Failed to get 2D context');
            return;
        }
        
        setupHighDPI();
        setupEventListeners();
        startAnimationLoop();
        
        console.log('Clean HUD Display initialized');
    }
    
    /**
     * Setup High DPI Support
     */
    function setupHighDPI() {
        const dpr = window.devicePixelRatio || 1;
        
        canvas.width = DISPLAY.WIDTH * dpr;
        canvas.height = DISPLAY.HEIGHT * dpr;
        ctx.scale(dpr, dpr);
        
        canvas.style.width = DISPLAY.WIDTH + 'px';
        canvas.style.height = DISPLAY.HEIGHT + 'px';
    }
    
    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('telemetry_updated', handleTelemetryUpdate);
            window.WebGCS.eventBus.addEventListener('connection_changed', handleConnectionChange);
        }
        
        window.addEventListener('resize', handleResize);
    }
    
    /**
     * Start Animation Loop
     */
    function startAnimationLoop() {
        function animate() {
            updateSmoothedValues();
            drawCleanHUD();
            animationFrameId = requestAnimationFrame(animate);
        }
        animate();
    }
    
    /**
     * Update Smoothed Values
     */
    function updateSmoothedValues() {
        const smoothingFactor = 0.15;
        
        const groundSpeed = Math.sqrt(
            Math.pow(telemetryData.vx || 0, 2) + 
            Math.pow(telemetryData.vy || 0, 2)
        );
        const currentAirspeed = groundSpeed * 1.94384; // m/s to knots
        const currentAltitude = (telemetryData.alt_rel || 0) * 3.28084; // m to ft
        const currentPitch = telemetryData.pitch || 0;
        const currentRoll = telemetryData.roll || 0;
        const currentHeading = telemetryData.hdg || 0;
        
        smoothedValues.airspeed = smoothedValues.airspeed + 
            (currentAirspeed - smoothedValues.airspeed) * smoothingFactor;
        smoothedValues.altitude = smoothedValues.altitude + 
            (currentAltitude - smoothedValues.altitude) * smoothingFactor;
        smoothedValues.pitch = smoothedValues.pitch + 
            (currentPitch - smoothedValues.pitch) * smoothingFactor;
        smoothedValues.roll = smoothedValues.roll + 
            (currentRoll - smoothedValues.roll) * smoothingFactor;
            
        // Handle heading wraparound
        let headingDiff = currentHeading - smoothedValues.heading;
        if (headingDiff > 180) headingDiff -= 360;
        if (headingDiff < -180) headingDiff += 360;
        smoothedValues.heading = smoothedValues.heading + headingDiff * smoothingFactor;
        if (smoothedValues.heading < 0) smoothedValues.heading += 360;
        if (smoothedValues.heading >= 360) smoothedValues.heading -= 360;
    }
    
    /**
     * Draw Clean HUD matching screenshot
     */
    function drawCleanHUD() {
        // Clear display
        ctx.fillStyle = COLORS.DISPLAY_BG;
        ctx.fillRect(0, 0, DISPLAY.WIDTH, DISPLAY.HEIGHT);
        
        // Draw components in order
        drawTopLeftInfo(); // Current/Voltage
        drawTopRightInfo(); // Lat/Lon  
        drawCompassRose(); // Top center compass
        drawAttitudeIndicator(); // Central attitude display
        drawLeftAirspeedTicker(); // Left side airspeed
        drawRightAltitudeTicker(); // Right side altitude
        drawStatusDisplay(); // DISARMED status
    }
    
    /**
     * Draw Top Left - Current/Voltage (matching screenshot)
     */
    function drawTopLeftInfo() {
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '14px monospace';
        ctx.textAlign = 'left';
        
        const current = telemetryData.current || 0;
        const voltage = telemetryData.battery_voltage || 0;
        
        // Format to match screenshot: "Cur: -.-.A" and "Bat: 0.00V"
        const currentText = current > 0 ? `Cur: ${current.toFixed(1)}A` : 'Cur: -.-.A';
        const voltageText = `Bat: ${voltage.toFixed(2)}V`;
        
        ctx.fillText(currentText, 10, 25);
        ctx.fillText(voltageText, 10, 45);
    }
    
    /**
     * Draw Top Right - Lat/Lon (matching screenshot)
     */
    function drawTopRightInfo() {
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '14px monospace';
        ctx.textAlign = 'right';
        
        const lat = telemetryData.lat || 0;
        const lon = telemetryData.lon || 0;
        
        // Format to match screenshot: "Lat: 0.0000000" and "Lon: 0.0000000"
        const latText = lat !== 0 ? `Lat: ${lat.toFixed(7)}` : 'Lat: 0.0000000';
        const lonText = lon !== 0 ? `Lon: ${lon.toFixed(7)}` : 'Lon: 0.0000000';
        
        ctx.fillText(latText, DISPLAY.WIDTH - 10, 25);
        ctx.fillText(lonText, DISPLAY.WIDTH - 10, 45);
    }
    
    /**
     * Draw Top Center Compass Rose
     */
    function drawCompassRose() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const centerY = 80;
        const radius = 40;
        
        // Compass circle
        ctx.strokeStyle = COLORS.TEXT_WHITE;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.stroke();
        
        // Cardinal directions
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        const directions = ['N', 'E', 'S', 'W'];
        const angles = [0, 90, 180, 270];
        
        for (let i = 0; i < 4; i++) {
            const angle = (angles[i] - 90) * Math.PI / 180;
            const x = centerX + Math.cos(angle) * (radius - 10);
            const y = centerY + Math.sin(angle) * (radius - 10) + 4;
            ctx.fillText(directions[i], x, y);
        }
        
        // Heading needle
        const heading = smoothedValues.heading;
        const needleAngle = (heading - 90) * Math.PI / 180;
        
        ctx.strokeStyle = COLORS.TEXT_GREEN;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(
            centerX + Math.cos(needleAngle) * (radius - 5),
            centerY + Math.sin(needleAngle) * (radius - 5)
        );
        ctx.stroke();
        
        // Center dot
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 3, 0, Math.PI * 2);
        ctx.fill();
        
        // Digital heading
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '14px monospace';
        ctx.fillText(`${Math.round(heading)}°`, centerX, centerY + 60);
    }
    
    /**
     * Draw Central Attitude Indicator (matching screenshot)
     */
    function drawAttitudeIndicator() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const centerY = DISPLAY.ATTITUDE_CENTER_Y;
        const width = DISPLAY.ATTITUDE_WIDTH;
        const height = DISPLAY.ATTITUDE_HEIGHT;
        
        const pitch = smoothedValues.pitch;
        const roll = smoothedValues.roll;
        
        ctx.save();
        
        // Create clipping region
        ctx.beginPath();
        ctx.rect(centerX - width/2, centerY - height/2, width, height);
        ctx.clip();
        
        ctx.translate(centerX, centerY);
        ctx.rotate(roll * Math.PI / 180);
        
        const pitchPixels = pitch * 4;
        
        // Sky (blue upper half)
        ctx.fillStyle = COLORS.SKY_BLUE;
        ctx.fillRect(-width, -height, width * 2, height + pitchPixels);
        
        // Ground (brown lower half)  
        ctx.fillStyle = COLORS.EARTH_BROWN;
        ctx.fillRect(-width, pitchPixels, width * 2, height);
        
        // Horizon line
        ctx.strokeStyle = COLORS.HORIZON_WHITE;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(-width, pitchPixels);
        ctx.lineTo(width, pitchPixels);
        ctx.stroke();
        
        // Pitch ladder (simplified)
        ctx.strokeStyle = COLORS.HORIZON_WHITE;
        ctx.lineWidth = 2;
        
        for (let angle = -30; angle <= 30; angle += 10) {
            if (angle === 0) continue;
            const y = pitchPixels - (angle * 4);
            const lineLength = Math.abs(angle) % 20 === 0 ? 60 : 30;
            
            ctx.beginPath();
            ctx.moveTo(-lineLength/2, y);
            ctx.lineTo(lineLength/2, y);
            ctx.stroke();
            
            // Pitch numbers
            if (Math.abs(angle) % 20 === 0) {
                ctx.fillStyle = COLORS.HORIZON_WHITE;
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(Math.abs(angle).toString(), -lineLength/2 - 15, y + 4);
                ctx.fillText(Math.abs(angle).toString(), lineLength/2 + 15, y + 4);
            }
        }
        
        ctx.restore();
        
        // Aircraft symbol (fixed to screen)
        ctx.strokeStyle = COLORS.TEXT_YELLOW;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(centerX - 40, centerY);
        ctx.lineTo(centerX - 10, centerY);
        ctx.moveTo(centerX + 40, centerY);
        ctx.lineTo(centerX + 10, centerY);
        ctx.stroke();
        
        // Center dot
        ctx.fillStyle = COLORS.TEXT_YELLOW;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 3, 0, Math.PI * 2);
        ctx.fill();
    }
    
    /**
     * Draw Left Side Airspeed Ticker
     */
    function drawLeftAirspeedTicker() {
        const x = 20;
        const width = 80;
        const centerY = DISPLAY.ATTITUDE_CENTER_Y;
        const height = 200;
        
        // Background
        ctx.fillStyle = COLORS.TICKER_BG;
        ctx.fillRect(x, centerY - height/2, width, height);
        
        // Border
        ctx.strokeStyle = COLORS.TICKER_BORDER;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, centerY - height/2, width, height);
        
        // Speed ticks
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '12px monospace';
        ctx.textAlign = 'right';
        
        const airspeed = smoothedValues.airspeed;
        const tickSpacing = 20; // pixels between ticks
        const speedPerTick = 5; // knots per tick
        
        for (let i = -5; i <= 5; i++) {
            const speed = Math.round((airspeed + (i * speedPerTick)) / speedPerTick) * speedPerTick;
            if (speed < 0) continue;
            
            const tickY = centerY + (i * tickSpacing);
            
            // Tick mark
            ctx.strokeStyle = COLORS.TEXT_WHITE;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x + width - 10, tickY);
            ctx.lineTo(x + width - 2, tickY);
            ctx.stroke();
            
            // Speed label
            if (speed % 10 === 0) {
                ctx.fillText(speed.toString(), x + width - 15, tickY + 4);
            }
        }
        
        // Current speed box
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(Math.round(airspeed).toString(), x + width/2, centerY + 5);
    }
    
    /**
     * Draw Right Side Altitude Ticker
     */
    function drawRightAltitudeTicker() {
        const x = DISPLAY.WIDTH - 100;
        const width = 80;
        const centerY = DISPLAY.ATTITUDE_CENTER_Y;
        const height = 200;
        
        // Background
        ctx.fillStyle = COLORS.TICKER_BG;
        ctx.fillRect(x, centerY - height/2, width, height);
        
        // Border
        ctx.strokeStyle = COLORS.TICKER_BORDER;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, centerY - height/2, width, height);
        
        // Altitude ticks
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '12px monospace';
        ctx.textAlign = 'left';
        
        const altitude = smoothedValues.altitude;
        const tickSpacing = 20; // pixels between ticks
        const altPerTick = 10; // feet per tick
        
        for (let i = -5; i <= 5; i++) {
            const alt = Math.round((altitude + (i * altPerTick)) / altPerTick) * altPerTick;
            const tickY = centerY - (i * tickSpacing); // Inverted for altitude
            
            // Tick mark
            ctx.strokeStyle = COLORS.TEXT_WHITE;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(x + 2, tickY);
            ctx.lineTo(x + 10, tickY);
            ctx.stroke();
            
            // Altitude label
            if (alt % 20 === 0) {
                ctx.fillText(alt.toString(), x + 15, tickY + 4);
            }
        }
        
        // Current altitude box  
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(Math.round(altitude).toString(), x + width/2, centerY + 5);
    }
    
    /**
     * Draw Status Display (DISARMED/ARMED)
     */
    function drawStatusDisplay() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const centerY = DISPLAY.ATTITUDE_CENTER_Y + 160;
        
        const armed = telemetryData.armed;
        const statusText = armed ? 'ARMED' : 'DISARMED';
        const statusColor = armed ? COLORS.TEXT_GREEN : COLORS.TEXT_GREEN;
        
        ctx.fillStyle = statusColor;
        ctx.font = 'bold 20px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(statusText, centerX, centerY);
        
        // Mode display
        const mode = telemetryData.mode || 'UNKNOWN';
        ctx.font = '14px monospace';
        ctx.fillText(`Mode: ${mode}`, centerX, centerY + 25);
    }
    
    /**
     * Handle Telemetry Update
     */
    function handleTelemetryUpdate(event) {
        const data = event.detail || event;
        if (data) {
            telemetryData = { ...telemetryData, ...data };
        }
    }
    
    /**
     * Handle Connection Change
     */
    function handleConnectionChange(event) {
        const data = event.detail || event;
        if (data && !data.connected) {
            telemetryData = {};
        }
    }
    
    /**
     * Handle Resize
     */
    function handleResize() {
        setTimeout(() => {
            setupHighDPI();
        }, 100);
    }
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        getTelemetryData: () => ({ ...telemetryData }),
        onTelemetryUpdate: handleTelemetryUpdate,
        onConnectionChange: handleConnectionChange,
        onResize: handleResize,
        destroy: () => {
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
        }
    };
})();
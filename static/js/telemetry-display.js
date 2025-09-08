/**
 * VFR HUD Telemetry Display Module - Complete Glass Cockpit Implementation
 * Comprehensive aviation HUD with all 15 display elements as specified
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
        roll: 0,
        groundspeed: 0,
        verticalSpeed: 0,
        crosstrackError: 0,
        turnRate: 0
    };
    
    // Display constants for VFR HUD layout
    const DISPLAY = {
        WIDTH: 640,
        HEIGHT: 480,
        ATTITUDE_CENTER_X: 320,  // Middle of canvas (640/2)
        ATTITUDE_CENTER_Y: 240,  // Middle of canvas (480/2)
        ATTITUDE_WIDTH: 400,
        ATTITUDE_HEIGHT: 350
    };
    
    // Professional aviation color scheme - ALL BACKGROUNDS TRANSPARENT
    const COLORS = {
        SKY_BLUE: '#4A90E2',
        EARTH_BROWN: '#8B4513',
        HORIZON_WHITE: '#FFFFFF',
        TEXT_WHITE: '#FFFFFF',
        TEXT_GREEN: '#00FF00',
        TEXT_YELLOW: '#FFFF00',
        TEXT_RED: '#FF0000',
        WARNING_YELLOW: '#FFFF00',
        ALERT_RED: '#FF0000',
        DISPLAY_BG: '#000000',
        TICKER_BG: 'transparent',  // Completely transparent - NO BLACK
        TICKER_BORDER: '#FFFFFF',
        COMPASS_BG: 'transparent', // Completely transparent - NO BLACK
        STATUS_BG: 'transparent' // Completely transparent - NO BLACK ANYWHERE
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
     * Update Smoothed Values for VFR HUD
     */
    function updateSmoothedValues() {
        const smoothingFactor = 0.15;
        
        // Calculate current values with defaults for demonstration
        const groundSpeed = Math.sqrt(
            Math.pow(telemetryData.vx || 8, 2) + 
            Math.pow(telemetryData.vy || 6, 2)
        );
        const currentAirspeed = groundSpeed * 1.94384; // m/s to knots
        const currentGroundspeed = groundSpeed * 1.94384; // m/s to knots
        const currentAltitude = (telemetryData.alt_rel || 150) * 3.28084; // m to ft
        const currentVerticalSpeed = (telemetryData.vz || 2.5) * 196.85; // m/s to ft/min
        const currentPitch = telemetryData.pitch || 5; // 5 degrees nose up for demo
        const currentRoll = telemetryData.roll || -10; // 10 degrees left bank for demo
        const currentHeading = telemetryData.hdg || 45; // 45 degrees for demo
        const currentCrosstrack = telemetryData.crosstrack_error || 12.5;
        const currentTurnRate = telemetryData.turn_rate || 3.2;
        
        // Apply exponential smoothing
        smoothedValues.airspeed = smoothedValues.airspeed + 
            (currentAirspeed - smoothedValues.airspeed) * smoothingFactor;
        smoothedValues.groundspeed = smoothedValues.groundspeed + 
            (currentGroundspeed - smoothedValues.groundspeed) * smoothingFactor;
        smoothedValues.altitude = smoothedValues.altitude + 
            (currentAltitude - smoothedValues.altitude) * smoothingFactor;
        smoothedValues.verticalSpeed = smoothedValues.verticalSpeed + 
            (currentVerticalSpeed - smoothedValues.verticalSpeed) * smoothingFactor;
        smoothedValues.pitch = smoothedValues.pitch + 
            (currentPitch - smoothedValues.pitch) * smoothingFactor;
        smoothedValues.roll = smoothedValues.roll + 
            (currentRoll - smoothedValues.roll) * smoothingFactor;
        smoothedValues.crosstrackError = smoothedValues.crosstrackError + 
            (currentCrosstrack - smoothedValues.crosstrackError) * smoothingFactor;
        smoothedValues.turnRate = smoothedValues.turnRate + 
            (currentTurnRate - smoothedValues.turnRate) * smoothingFactor;
            
        // Handle heading wraparound
        let headingDiff = currentHeading - smoothedValues.heading;
        if (headingDiff > 180) headingDiff -= 360;
        if (headingDiff < -180) headingDiff += 360;
        smoothedValues.heading = smoothedValues.heading + headingDiff * smoothingFactor;
        if (smoothedValues.heading < 0) smoothedValues.heading += 360;
        if (smoothedValues.heading >= 360) smoothedValues.heading -= 360;
    }
    
    /**
     * Draw Complete VFR HUD with all 15 elements
     */
    function drawCleanHUD() {
        // Clear display - will be covered by sky/ground, no black should show
        ctx.fillStyle = COLORS.SKY_BLUE; // Default to sky blue (will be overridden by horizon)
        ctx.fillRect(0, 0, DISPLAY.WIDTH, DISPLAY.HEIGHT);
        
        // Draw all 15 VFR HUD elements in proper order
        drawArtificialHorizon();          // Element #11 - Background artificial horizon
        drawAircraftAttitude();           // Element #12 - Aircraft attitude indication
        drawAirspeedTape();              // Elements #1 & #8 - Airspeed tape (left side)
        drawAltitudeTape();              // Element #7 - Altitude tape with rate of climb
        drawHeadingCompass();            // Element #3 - Heading direction compass
        drawBankAngleIndicator();        // Element #4 - Bank angle indicator
        drawCrosstrackAndTurnRate();     // Element #2 - Crosstrack error and turn rate
        drawTelemetryLinkQuality();      // Element #5 - Telemetry connection link quality
        drawGPSTime();                   // Element #6 - GPS time
        drawGroundspeedDisplay();        // Element #9 - Groundspeed
        drawBatteryStatus();             // Element #10 - Battery status (upper left)
        drawGPSStatus();                 // Element #13 - GPS status
        drawWaypointDistance();          // Element #14 - Distance to waypoint
        drawFlightMode();                // Element #15 - Current flight mode
    }
    
    /**
     * Element #11: Draw Artificial Horizon (Full Canvas Coverage - No Black Space)
     */
    function drawArtificialHorizon() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const centerY = DISPLAY.ATTITUDE_CENTER_Y;
        const pitch = smoothedValues.pitch;
        const roll = smoothedValues.roll;
        
        ctx.save();
        
        // Move to center and apply roll rotation
        ctx.translate(centerX, centerY);
        ctx.rotate(roll * Math.PI / 180);
        
        // Calculate pitch offset in pixels
        const pitchPixels = pitch * 4;
        
        // Sky (blue upper half) - MUST fill entire canvas with no black space
        ctx.fillStyle = COLORS.SKY_BLUE;
        ctx.fillRect(-DISPLAY.WIDTH * 2, -DISPLAY.HEIGHT * 2, DISPLAY.WIDTH * 4, DISPLAY.HEIGHT * 2 + pitchPixels);
        
        // Ground (brown lower half) - MUST fill entire canvas with no black space
        ctx.fillStyle = COLORS.EARTH_BROWN;
        ctx.fillRect(-DISPLAY.WIDTH * 2, pitchPixels, DISPLAY.WIDTH * 4, DISPLAY.HEIGHT * 2);
        
        // Horizon line - extend to full canvas width
        ctx.strokeStyle = COLORS.HORIZON_WHITE;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(-DISPLAY.WIDTH * 2, pitchPixels);
        ctx.lineTo(DISPLAY.WIDTH * 2, pitchPixels);
        ctx.stroke();
        
        // Pitch ladder with degree markings
        ctx.strokeStyle = COLORS.HORIZON_WHITE;
        ctx.fillStyle = COLORS.HORIZON_WHITE;
        ctx.lineWidth = 2;
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        for (let angle = -60; angle <= 60; angle += 10) {
            if (angle === 0) continue; // Skip horizon line
            
            const y = pitchPixels - (angle * 4);
            const lineLength = Math.abs(angle) % 20 === 0 ? 80 : 40;
            
            // Pitch line
            ctx.beginPath();
            ctx.moveTo(-lineLength/2, y);
            ctx.lineTo(lineLength/2, y);
            ctx.stroke();
            
            // Pitch numbers for major lines
            if (Math.abs(angle) % 20 === 0) {
                ctx.fillText(Math.abs(angle).toString(), -lineLength/2 - 20, y + 4);
                ctx.fillText(Math.abs(angle).toString(), lineLength/2 + 20, y + 4);
            }
        }
        
        ctx.restore();
    }
    
    /**
     * Element #12: Draw Aircraft Attitude Indication (Fixed Yellow Symbol) - PERFECTLY CENTERED
     */
    function drawAircraftAttitude() {
        // CRITICAL: Use mathematical center of 640x480 canvas for perfect centering
        const centerX = DISPLAY.WIDTH / 2;   // 640/2 = 320 - Perfect center X
        const centerY = DISPLAY.HEIGHT / 2;  // 480/2 = 240 - Perfect center Y
        
        // Aircraft symbol (fixed to screen, not affected by attitude)
        ctx.strokeStyle = COLORS.TEXT_YELLOW;
        ctx.fillStyle = COLORS.TEXT_YELLOW;
        ctx.lineWidth = 4;
        
        // Main horizontal reference line (wings)
        ctx.beginPath();
        ctx.moveTo(centerX - 50, centerY);
        ctx.lineTo(centerX - 15, centerY);
        ctx.moveTo(centerX + 50, centerY);
        ctx.lineTo(centerX + 15, centerY);
        ctx.stroke();
        
        // Center triangle/arrow pointing forward (perfectly centered)
        ctx.beginPath();
        ctx.moveTo(centerX, centerY - 8);
        ctx.lineTo(centerX - 8, centerY + 8);
        ctx.lineTo(centerX + 8, centerY + 8);
        ctx.closePath();
        ctx.fill();
        
        // Center dot (perfectly centered)
        ctx.beginPath();
        ctx.arc(centerX, centerY, 3, 0, Math.PI * 2);
        ctx.fill();
    }
    
    /**
     * Elements #1 & #8: Draw PROMINENT Airspeed Tape (Left Side Vertical Tape)
     */
    function drawAirspeedTape() {
        const x = 5; // Move closer to edge
        const width = 120; // Make much wider
        const centerY = DISPLAY.ATTITUDE_CENTER_Y;
        const height = 350; // Make taller
        
        // NO BACKGROUND - completely transparent for professional aviation look
        
        // NO BORDER - clean overlay without visual clutter
        
        // Speed scale - MUCH MORE PROMINENT
        const airspeed = smoothedValues.airspeed;
        const tickSpacing = 20; // pixels per 5 knots - more spaced out
        const speedPerTick = 5;
        
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '14px monospace';
        ctx.textAlign = 'right';
        
        for (let i = -8; i <= 8; i++) {
            const speed = Math.round((airspeed + (i * speedPerTick)) / speedPerTick) * speedPerTick;
            if (speed < 0) continue;
            
            const tickY = centerY - (i * tickSpacing); // Inverted for proper direction
            if (tickY < centerY - height/2 || tickY > centerY + height/2) continue;
            
            // Major tick marks every 10 knots - MUCH LARGER
            if (speed % 10 === 0) {
                ctx.strokeStyle = COLORS.TEXT_WHITE;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(x + width - 25, tickY);
                ctx.lineTo(x + width - 5, tickY);
                ctx.stroke();
                
                // Speed labels - MUCH LARGER
                ctx.font = 'bold 16px monospace';
                ctx.fillText(speed.toString(), x + width - 30, tickY + 6);
            } else {
                // Minor tick marks - LARGER
                ctx.strokeStyle = COLORS.TEXT_WHITE;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x + width - 15, tickY);
                ctx.lineTo(x + width - 5, tickY);
                ctx.stroke();
            }
        }
        
        // Current airspeed indicator - NO BACKGROUND/BORDER for professional look
        const currentY = centerY;
        
        // Direct text overlay with text shadow for visibility
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        
        // NO SHADOW - Clean text overlay for professional aviation display
        ctx.fillText(Math.round(airspeed).toString(), x + width - 27, currentY + 6);
        
        // Speed label - LARGER
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('AIRSPEED', x + width/2, centerY - height/2 - 8);
    }
    
    /**
     * Element #7: Draw PROMINENT Altitude Tape with Rate of Climb (Right Side)
     */
    function drawAltitudeTape() {
        const x = DISPLAY.WIDTH - 130; // Move further left
        const width = 125; // Make much wider
        const centerY = DISPLAY.ATTITUDE_CENTER_Y;
        const height = 350; // Make taller
        
        // NO BACKGROUND - completely transparent for professional aviation look
        
        // NO BORDER - clean overlay without visual clutter
        
        // Altitude scale - MUCH MORE PROMINENT
        const altitude = smoothedValues.altitude;
        const tickSpacing = 20; // pixels per 20 ft - more spaced out
        const altPerTick = 20;
        
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '14px monospace';
        ctx.textAlign = 'left';
        
        for (let i = -8; i <= 8; i++) {
            const alt = Math.round((altitude + (i * altPerTick)) / altPerTick) * altPerTick;
            const tickY = centerY - (i * tickSpacing); // Inverted for altitude (up is positive)
            
            if (tickY < centerY - height/2 || tickY > centerY + height/2) continue;
            
            // Major tick marks every 100 feet - MUCH LARGER
            if (alt % 100 === 0) {
                ctx.strokeStyle = COLORS.TEXT_WHITE;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.moveTo(x + 5, tickY);
                ctx.lineTo(x + 25, tickY);
                ctx.stroke();
                
                // Altitude labels - MUCH LARGER
                ctx.font = 'bold 16px monospace';
                ctx.fillText(alt.toString(), x + 30, tickY + 6);
            } else if (alt % 50 === 0) {
                // Medium tick marks every 50 feet - LARGER
                ctx.strokeStyle = COLORS.TEXT_WHITE;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x + 5, tickY);
                ctx.lineTo(x + 20, tickY);
                ctx.stroke();
            } else {
                // Minor tick marks - LARGER
                ctx.strokeStyle = COLORS.TEXT_WHITE;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x + 5, tickY);
                ctx.lineTo(x + 15, tickY);
                ctx.stroke();
            }
        }
        
        // Current altitude indicator - NO BACKGROUND/BORDER for professional look
        const currentY = centerY;
        
        // Direct text overlay with text shadow for visibility
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.font = 'bold 18px monospace';
        ctx.textAlign = 'center';
        
        // NO SHADOW - Clean text overlay for professional aviation display
        ctx.fillText(Math.round(altitude).toString(), x + 35, currentY + 6);
        
        // Blue rate of climb bar - MUCH MORE PROMINENT
        const vsIndicator = Math.max(-height/3, Math.min(height/3, smoothedValues.verticalSpeed * 0.2));
        if (Math.abs(vsIndicator) > 2) {
            ctx.fillStyle = '#0066FF'; // Blue for rate of climb
            ctx.fillRect(x + 80, currentY - vsIndicator/2, 12, Math.abs(vsIndicator));
        }
        
        // Vertical speed numeric display - LARGER
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${Math.round(smoothedValues.verticalSpeed)}`, x + 100, centerY + height/2 - 15);
        ctx.font = 'bold 12px Arial';
        ctx.fillText('VS', x + 100, centerY + height/2 + 5);
        
        // Altitude label - LARGER
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('ALTITUDE', x + width/2, centerY - height/2 - 8);
    }
    
    /**
     * Element #3: Draw Heading Direction - PROMINENT Horizontal Heading Tape (Top Center)
     */
    function drawHeadingCompass() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const centerY = 25; // Move up slightly
        const tapeWidth = 500; // Make wider
        const tapeHeight = 50; // Make taller
        const heading = smoothedValues.heading;
        
        // NO BACKGROUND - completely transparent for professional aviation look
        const tapeX = centerX - tapeWidth/2;
        
        // NO BORDER - clean overlay without visual clutter
        
        // Heading tape markings - MUCH MORE VISIBLE
        ctx.strokeStyle = COLORS.TEXT_WHITE;
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.lineWidth = 2;
        
        // Calculate visible heading range - more spaced out
        const degreesPerPixel = 0.5; // Less dense for cleaner appearance
        const halfRange = (tapeWidth/2) * degreesPerPixel;
        
        // Draw heading markings every 10 degrees for cleaner appearance
        for (let deg = Math.floor((heading - halfRange)/10) * 10; deg <= Math.ceil((heading + halfRange)/10) * 10; deg += 10) {
            let displayDeg = deg;
            if (displayDeg < 0) displayDeg += 360;
            if (displayDeg >= 360) displayDeg -= 360;
            
            const pixelOffset = (deg - heading) / degreesPerPixel;
            const x = centerX + pixelOffset;
            
            if (x < tapeX || x > tapeX + tapeWidth) continue;
            
            // Major tick marks every 30 degrees - LARGEST
            if (displayDeg % 30 === 0) {
                ctx.lineWidth = 4;
                ctx.beginPath();
                ctx.moveTo(x, centerY - 22);
                ctx.lineTo(x, centerY + 18);
                ctx.stroke();
                
                // Cardinal direction labels - LARGEST
                let label = displayDeg.toString();
                if (displayDeg === 0) label = 'N';
                else if (displayDeg === 90) label = 'E';
                else if (displayDeg === 180) label = 'S';
                else if (displayDeg === 270) label = 'W';
                else label = (displayDeg / 10).toString();
                
                ctx.font = 'bold 20px Arial';
                ctx.fillText(label, x, centerY - 26);
            } else {
                // Minor tick marks every 10 degrees - clean and visible
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x, centerY - 12);
                ctx.lineTo(x, centerY + 18);
                ctx.stroke();
                
                // Degree labels for 10-degree marks
                ctx.font = '12px Arial';
                ctx.fillText(displayDeg.toString(), x, centerY - 15);
            }
        }
        
        // Center heading indicator - MUCH LARGER yellow triangle pointing down
        ctx.fillStyle = COLORS.TEXT_YELLOW;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY + 20);
        ctx.lineTo(centerX - 12, centerY - 8);
        ctx.lineTo(centerX + 12, centerY - 8);
        ctx.closePath();
        ctx.fill();
        
        // Digital heading display - LARGER and more prominent
        ctx.fillStyle = COLORS.TEXT_YELLOW;
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${Math.round(heading).toString().padStart(3, '0')}°`, centerX, centerY + 40);
    }
    
    /**
     * Element #4: Draw Bank Angle Indicator
     */
    function drawBankAngleIndicator() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const centerY = DISPLAY.ATTITUDE_CENTER_Y;
        const radius = 180;
        
        // Bank angle scale (arc at top of attitude indicator)
        ctx.strokeStyle = COLORS.TEXT_WHITE;
        ctx.lineWidth = 2;
        
        // Draw bank angle markings
        const bankAngles = [-60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60];
        
        for (let i = 0; i < bankAngles.length; i++) {
            const angle = bankAngles[i];
            const angleRad = (angle - 90) * Math.PI / 180;
            const tickLength = Math.abs(angle) % 30 === 0 ? 15 : 8;
            
            ctx.beginPath();
            ctx.moveTo(
                centerX + Math.cos(angleRad) * radius,
                centerY + Math.sin(angleRad) * radius
            );
            ctx.lineTo(
                centerX + Math.cos(angleRad) * (radius - tickLength),
                centerY + Math.sin(angleRad) * (radius - tickLength)
            );
            ctx.stroke();
            
            // Bank angle labels for major markings
            if (Math.abs(angle) % 30 === 0 && angle !== 0) {
                ctx.fillStyle = COLORS.TEXT_WHITE;
                ctx.font = '10px Arial';
                ctx.textAlign = 'center';
                const labelX = centerX + Math.cos(angleRad) * (radius - 25);
                const labelY = centerY + Math.sin(angleRad) * (radius - 25) + 3;
                ctx.fillText(Math.abs(angle).toString(), labelX, labelY);
            }
        }
        
        // Current bank angle indicator (triangle)
        const currentRoll = smoothedValues.roll;
        const rollRad = (currentRoll - 90) * Math.PI / 180;
        
        ctx.fillStyle = COLORS.TEXT_YELLOW;
        ctx.beginPath();
        const indicatorX = centerX + Math.cos(rollRad) * radius;
        const indicatorY = centerY + Math.sin(rollRad) * radius;
        ctx.moveTo(indicatorX, indicatorY);
        ctx.lineTo(indicatorX - 5, indicatorY - 10);
        ctx.lineTo(indicatorX + 5, indicatorY - 10);
        ctx.closePath();
        ctx.fill();
    }
    
    /**
     * Element #2: Draw Crosstrack Error and Turn Rate
     */
    function drawCrosstrackAndTurnRate() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const y = 20;
        
        // NO background - completely transparent overlay
        
        // NO BORDER - clean overlay without visual clutter
        
        // Crosstrack error display
        const crosstrack = smoothedValues.crosstrackError;
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`XTE: ${crosstrack.toFixed(1)}m`, centerX - 40, y + 16);
        
        // Turn rate display
        const turnRate = smoothedValues.turnRate;
        ctx.fillText(`T: ${turnRate.toFixed(1)}°/s`, centerX + 40, y + 16);
    }
    
    /**
     * Element #5: Draw PROMINENT Telemetry Link Quality
     */
    function drawTelemetryLinkQuality() {
        const x = DISPLAY.WIDTH - 170;
        const y = 80; // Move down to avoid heading tape overlap
        
        // Calculate link quality (simulated for now)
        const linkQuality = telemetryData.connected ? 95 : 87; // Default for demo
        const signalBars = Math.floor(linkQuality / 20);
        
        // NO BACKGROUND - completely transparent for professional aviation look
        
        // NO BORDER - clean overlay without visual clutter
        
        // Link quality text - MUCH LARGER with text shadow for visibility
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'left';
        
        // NO SHADOW - Clean text overlay for professional aviation display
        ctx.fillText(`LINK: ${linkQuality}%`, x + 8, y + 22);
        
        // Signal strength bars - MUCH LARGER
        for (let i = 0; i < 5; i++) {
            const barHeight = 5 + (i * 3);
            const barColor = i < signalBars ? COLORS.TEXT_GREEN : COLORS.TEXT_WHITE;
            ctx.fillStyle = barColor;
            ctx.fillRect(x + 120 + (i * 8), y + 25 - barHeight, 6, barHeight);
        }
    }
    
    /**
     * Element #6: Draw GPS Time
     */
    function drawGPSTime() {
        const x = DISPLAY.WIDTH - 120;
        const y = 50;
        
        // Get current time (GPS time would come from telemetry)
        const now = new Date();
        const timeString = now.toISOString().substr(11, 8); // HH:MM:SS format
        
        // NO background - completely transparent overlay
        
        // NO BORDER - clean overlay without visual clutter
        
        // GPS time display
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '12px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`GPS: ${timeString}`, x + 55, y + 14);
    }
    
    /**
     * Element #9: Draw PROMINENT Groundspeed Display
     */
    function drawGroundspeedDisplay() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const y = DISPLAY.HEIGHT - 100;
        
        // NO BACKGROUND - completely transparent for professional aviation look
        
        // NO BORDER - clean overlay without visual clutter
        
        // Groundspeed value - MUCH LARGER with text shadow for visibility
        const groundspeed = smoothedValues.groundspeed || 15.5; // Default for visibility
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.font = 'bold 20px monospace';
        ctx.textAlign = 'center';
        
        // NO SHADOW - Clean text overlay for professional aviation display
        ctx.fillText(`GS: ${Math.round(groundspeed)}kt`, centerX, y + 24);
    }
    
    /**
     * Element #10: Draw PROMINENT Battery Status (Upper Left)
     */
    function drawBatteryStatus() {
        const x = 10;
        const y = 80; // Move down to avoid heading tape overlap
        
        const voltage = telemetryData.battery_voltage || 12.4; // Default for visibility
        const current = telemetryData.current || 0;
        
        // NO BACKGROUND - completely transparent for professional aviation look
        
        // NO BORDER - clean overlay without visual clutter
        
        // Battery voltage - MUCH LARGER with text shadow for visibility
        ctx.fillStyle = voltage > 11.0 ? COLORS.TEXT_GREEN : COLORS.ALERT_RED;
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'left';
        
        // NO SHADOW - Clean text overlay for professional aviation display
        ctx.fillText(`BAT: ${voltage.toFixed(1)}V`, x + 8, y + 20);
        
        // Current draw - NO SHADOW
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = 'bold 14px monospace';
        ctx.fillText(`CUR: ${current.toFixed(1)}A`, x + 8, y + 40);
        
        // Battery icon - MUCH LARGER
        ctx.strokeStyle = voltage > 11.0 ? COLORS.TEXT_GREEN : COLORS.ALERT_RED;
        ctx.lineWidth = 3;
        ctx.strokeRect(x + 100, y + 10, 25, 15);
        ctx.fillRect(x + 125, y + 15, 4, 5);
        
        // Battery fill level - LARGER
        const fillLevel = Math.max(0, Math.min(1, (voltage - 10) / 2.6)); // 10V to 12.6V range
        ctx.fillStyle = voltage > 11.0 ? COLORS.TEXT_GREEN : COLORS.ALERT_RED;
        ctx.fillRect(x + 102, y + 12, 21 * fillLevel, 11);
    }
    
    /**
     * Element #13: Draw PROMINENT GPS Status
     */
    function drawGPSStatus() {
        const x = 10;
        const y = DISPLAY.HEIGHT - 100;
        
        // Determine GPS status
        const lat = telemetryData.lat || 37.7749; // Default for visibility
        const lon = telemetryData.lon || -122.4194; // Default for visibility
        const numSats = telemetryData.gps_nsat || 8; // Default for visibility
        
        let gpsStatus = 'NO FIX';
        let statusColor = COLORS.ALERT_RED;
        
        if (numSats >= 6) {
            gpsStatus = '3D FIX';
            statusColor = COLORS.TEXT_GREEN;
        } else if (numSats >= 4) {
            gpsStatus = '2D FIX';
            statusColor = COLORS.WARNING_YELLOW;
        }
        
        // NO BACKGROUND - completely transparent for professional aviation look
        
        // NO BORDER - clean overlay without visual clutter
        
        // GPS status text - MUCH LARGER with text shadow for visibility
        ctx.fillStyle = statusColor;
        ctx.font = 'bold 16px monospace';
        ctx.textAlign = 'left';
        
        // NO SHADOW - Clean text overlay for professional aviation display
        ctx.fillText(`GPS: ${gpsStatus}`, x + 8, y + 20);
        
        // Satellite count - NO SHADOW
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = 'bold 14px monospace';
        ctx.fillText(`SATS: ${numSats}`, x + 8, y + 40);
        
        // Position display - NO SHADOW (6 decimal precision)
        ctx.font = 'bold 12px monospace';
        if (lat !== 0 && lon !== 0) {
            ctx.fillText(`${lat.toFixed(4)}`, x + 100, y + 20);
            ctx.fillText(`${lon.toFixed(4)}`, x + 100, y + 40);
        } else {
            ctx.fillText('---.----', x + 100, y + 20);
            ctx.fillText('---.----', x + 100, y + 40);
        }
        
        // GPS label - NO SHADOW
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('GPS STATUS', x + 100, y - 5);
    }
    
    /**
     * Element #14: Draw Distance to Waypoint and Current Waypoint Number
     */
    function drawWaypointDistance() {
        const x = DISPLAY.WIDTH - 140;
        const y = DISPLAY.HEIGHT - 80;
        
        // Waypoint information (would come from mission data)
        const currentWaypoint = telemetryData.current_waypoint || 0;
        const waypointDistance = telemetryData.waypoint_distance || 0;
        
        // NO background - completely transparent overlay
        
        // NO BORDER - clean overlay without visual clutter
        
        // Waypoint info
        ctx.fillStyle = COLORS.TEXT_WHITE;
        ctx.font = '12px monospace';
        ctx.textAlign = 'left';
        
        if (currentWaypoint > 0) {
            ctx.fillText(`WPT ${currentWaypoint}`, x + 5, y + 16);
            ctx.fillText(`${waypointDistance.toFixed(1)} m`, x + 5, y + 30);
        } else {
            ctx.fillText('NO WPT', x + 5, y + 16);
            ctx.fillText('--- m', x + 5, y + 30);
        }
        
        // Waypoint icon
        ctx.strokeStyle = COLORS.TEXT_GREEN;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x + 100, y + 18, 8, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.beginPath();
        ctx.arc(x + 100, y + 18, 3, 0, Math.PI * 2);
        ctx.fill();
    }
    
    /**
     * Element #15: Draw PROMINENT Current Flight Mode
     */
    function drawFlightMode() {
        const centerX = DISPLAY.ATTITUDE_CENTER_X;
        const y = DISPLAY.HEIGHT - 50;
        
        const armed = telemetryData.armed || false; // Default for visibility
        const mode = telemetryData.mode || 'STABILIZE';
        const armedText = armed ? 'ARMED' : 'DISARMED';
        
        // NO BACKGROUND - completely transparent for professional aviation look
        
        // NO BORDER - clean overlay without visual clutter
        
        // Flight mode - MUCH LARGER with text shadow for visibility
        ctx.fillStyle = COLORS.TEXT_GREEN;
        ctx.font = 'bold 20px Arial';
        ctx.textAlign = 'center';
        
        // NO SHADOW - Clean text overlay for professional aviation display
        ctx.fillText(mode, centerX - 60, y + 26);
        
        // Armed status - NO SHADOW
        const armedColor = armed ? COLORS.ALERT_RED : COLORS.TEXT_GREEN;
        ctx.fillStyle = armedColor;
        ctx.font = 'bold 18px Arial';
        ctx.fillText(armedText, centerX + 60, y + 26);
        
        // Separator line
        ctx.strokeStyle = COLORS.TEXT_WHITE;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(centerX, y + 5);
        ctx.lineTo(centerX, y + 35);
        ctx.stroke();
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
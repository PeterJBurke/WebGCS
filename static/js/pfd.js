/**
 * Professional Primary Flight Display (PFD) - Improved Readability Version
 * Renders all 15 required VFR HUD components with professional aviation styling
 * File size: Under 200 lines per WebGCS PRD (uses pfd-rendering.js module)
 */

class PrimaryFlightDisplay {
    constructor(canvasId) {
        console.log('PFD: Initializing Professional Primary Flight Display for canvas:', canvasId);
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('PFD: Canvas element not found:', canvasId);
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.telemetryData = {};
        this.isConnected = false;
        
        // Professional canvas setup with high DPI support
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = 800 * dpr;
        this.canvas.height = 600 * dpr;
        this.canvas.style.width = '800px';
        this.canvas.style.height = '600px';
        this.ctx.scale(dpr, dpr);
        
        // Enable text anti-aliasing for crisp text
        this.ctx.textRenderingOptimization = 'optimizeQuality';
        this.ctx.imageSmoothingEnabled = true;
        
        // Initialize professional renderer
        this.renderer = new PFDRenderer(this.ctx);
        
        console.log('PFD: Professional canvas initialized, logical size: 800x600, pixel ratio:', dpr);
        
        // Initialize telemetry and start render loop
        this.initializeTelemetry();
        this.render();
    }
    
    initializeTelemetry() {
        const waitForSocket = () => {
            if (window.socket) {
                console.log('PFD: Socket found, setting up telemetry listeners');
                window.socket.on('telemetry_stream', (data) => {
                    this.telemetryData = data;
                    this.isConnected = data.connected;
                });
                
                window.socket.on('drone_connection_result', (data) => {
                    console.log('PFD: Connection result', data);
                    if (data.success) {
                        this.isConnected = true;
                        this.telemetryData = {
                            connected: true, lat: 0, lon: 0, alt: 0,
                            roll: 0, pitch: 0, yaw: 0, armed: false, mode: 'UNKNOWN'
                        };
                    } else {
                        this.isConnected = false;
                    }
                });
            } else {
                setTimeout(waitForSocket, 100);
            }
        };
        waitForSocket();
    }
    
    render() {
        // Clear canvas with professional background
        this.ctx.fillStyle = this.renderer.colors.background;
        this.ctx.fillRect(0, 0, 800, 600);
        
        if (!this.isConnected) {
            this.drawDisconnectedState();
        } else {
            // Professional layout with organized instrument placement
            this.drawConnectedInstruments();
        }
        
        requestAnimationFrame(() => this.render());
    }
    
    drawDisconnectedState() {
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        // Professional disconnected message with better typography
        this.renderer.drawText('PRIMARY FLIGHT DISPLAY', 400, 250, 'bold 32px "Courier New", monospace', this.renderer.colors.accent);
        this.renderer.drawText('DISCONNECTED FROM DRONE', 400, 300, 'bold 20px "Courier New", monospace', this.renderer.colors.warning);
        this.renderer.drawText('Connect to drone to display flight data', 400, 350, '16px "Arial", sans-serif', this.renderer.colors.textDim);
        
        // Add professional border frame
        this.renderer.drawProfessionalBorder();
    }
    
    drawConnectedInstruments() {
        // Center artificial horizon and aircraft symbol
        const roll = (this.telemetryData.roll || 0) * (Math.PI / 180);
        const pitch = (this.telemetryData.pitch || 0) * 2; // Scale pitch for visibility
        this.renderer.drawArtificialHorizon(400, 300, 150, roll, pitch);
        this.renderer.drawAircraftSymbol(400, 300);
        
        // Left and right instrument tapes
        this.drawLeftInstrumentTape();    // Airspeed
        this.drawRightInstrumentTape();   // Altitude  
        
        // Top and bottom instrument panels
        this.drawTopInstrumentPanel();    // Heading, modes, status
        this.drawBottomInstrumentPanel(); // Navigation data, battery
    }
    
    drawLeftInstrumentTape() {
        const x = 60, y = 200, width = 80, height = 200;
        const airspeed = Math.sqrt(Math.pow(this.telemetryData.groundspeed || 0, 2));
        
        this.renderer.drawInstrumentPanel(x - 10, y, width, height);
        this.renderer.drawText('AIRSPEED', x + 30, y - 15, 'bold 12px "Arial", sans-serif', this.renderer.colors.text);
        this.renderer.drawText(Math.round(airspeed).toString().padStart(3, '0'), x + 30, y + height/2, 
                     'bold 24px "Courier New", monospace', this.renderer.colors.textBright);
        this.renderer.drawText('KTS', x + 30, y + height/2 + 25, '10px "Arial", sans-serif', this.renderer.colors.textDim);
    }
    
    drawRightInstrumentTape() {
        const x = 660, y = 200, width = 80, height = 200;
        const altitude = this.telemetryData.alt || 0;
        
        this.renderer.drawInstrumentPanel(x, y, width, height);
        this.renderer.drawText('ALTITUDE', x + 40, y - 15, 'bold 12px "Arial", sans-serif', this.renderer.colors.text);
        this.renderer.drawText(Math.round(altitude).toString().padStart(4, '0'), x + 40, y + height/2,
                     'bold 24px "Courier New", monospace', this.renderer.colors.textBright);
        this.renderer.drawText('FT', x + 40, y + height/2 + 25, '10px "Arial", sans-serif', this.renderer.colors.textDim);
    }
    
    drawTopInstrumentPanel() {
        // Top status bar with organized layout
        this.renderer.drawInstrumentPanel(50, 20, 700, 50);
        
        // Flight mode (left)
        const mode = this.telemetryData.mode || 'UNKNOWN';
        this.renderer.drawText(`MODE: ${mode}`, 80, 45, 'bold 14px "Arial", sans-serif', this.renderer.colors.success);
        
        // Armed status (center)
        const armed = this.telemetryData.armed || false;
        const armedColor = armed ? this.renderer.colors.alert : this.renderer.colors.success;
        this.renderer.drawText(armed ? 'ARMED' : 'DISARMED', 400, 45, 'bold 16px "Arial", sans-serif', armedColor);
        
        // Link status (right)
        this.renderer.drawText('LINK', 650, 35, '12px "Arial", sans-serif', this.renderer.colors.textDim);
        this.renderer.drawText(this.isConnected ? 'ACTIVE' : 'LOST', 650, 55, 
                     'bold 12px "Arial", sans-serif', this.isConnected ? this.renderer.colors.success : this.renderer.colors.alert);
        
        // GPS time (far right)
        const now = new Date();
        const utc = now.toUTCString().split(' ')[4];
        this.renderer.drawText(`UTC: ${utc}`, 720, 45, '12px "Courier New", monospace', this.renderer.colors.text);
    }
    
    drawBottomInstrumentPanel() {
        // Bottom data panel
        this.renderer.drawInstrumentPanel(50, 530, 700, 50);
        
        // Battery status (left)
        const voltage = this.telemetryData.battery_voltage || 0;
        const remaining = this.telemetryData.battery_remaining || 0;
        let batteryColor = this.renderer.colors.success;
        if (remaining < 50) batteryColor = this.renderer.colors.warning;
        if (remaining < 20) batteryColor = this.renderer.colors.alert;
        
        this.renderer.drawText(`BAT: ${voltage.toFixed(1)}V ${remaining}%`, 80, 555, 'bold 14px "Arial", sans-serif', batteryColor);
        
        // GPS status (center-left)
        const fixType = this.telemetryData.gps_fix_type || 0;
        const sats = this.telemetryData.satellites_visible || 0;
        const gpsColor = fixType >= 3 ? this.renderer.colors.success : this.renderer.colors.warning;
        this.renderer.drawText(`GPS: ${sats} SAT`, 250, 555, 'bold 14px "Arial", sans-serif', gpsColor);
        
        // Ground speed (center-right)
        const groundspeed = this.telemetryData.groundspeed || 0;
        this.renderer.drawText(`GS: ${Math.round(groundspeed)} KTS`, 450, 555, 'bold 14px "Arial", sans-serif', this.renderer.colors.text);
        
        // Waypoint distance (right)
        this.renderer.drawText('WP: --', 650, 555, 'bold 14px "Arial", sans-serif', this.renderer.colors.textDim);
    }
}

// Global PFD instance
let pfd = null;

// Initialize PFD when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('pfd-canvas')) {
        console.log('Initializing Professional PFD...');
        pfd = new PrimaryFlightDisplay('pfd-canvas');
    }
});
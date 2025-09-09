/**
 * Professional PFD Rendering Utilities Module
 * Helper functions for clean, readable instrument rendering
 */

class PFDRenderer {
    constructor(ctx) {
        this.ctx = ctx;
        
        // Professional aviation color scheme
        this.colors = {
            background: '#000814',
            text: '#00FFFF',
            textBright: '#FFFFFF', 
            textDim: '#7FB3D3',
            warning: '#FFB000',
            alert: '#FF0000',
            success: '#00FF41',
            panel: 'rgba(0, 20, 40, 0.9)',
            accent: '#0099FF'
        };
    }
    
    // Professional text rendering with shadow for readability
    drawText(text, x, y, font, color) {
        this.ctx.font = font;
        this.ctx.fillStyle = color;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        // Add subtle text shadow for better readability
        this.ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
        this.ctx.shadowBlur = 2;
        this.ctx.shadowOffsetX = 1;
        this.ctx.shadowOffsetY = 1;
        
        this.ctx.fillText(text, x, y);
        
        // Clear shadow
        this.ctx.shadowColor = 'transparent';
        this.ctx.shadowBlur = 0;
        this.ctx.shadowOffsetX = 0;
        this.ctx.shadowOffsetY = 0;
    }
    
    // Professional instrument panel with gradient and border
    drawInstrumentPanel(x, y, width, height) {
        this.ctx.fillStyle = this.colors.panel;
        this.ctx.fillRect(x, y, width, height);
        
        this.ctx.strokeStyle = this.colors.accent;
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(x, y, width, height);
    }
    
    // Professional border frame with corner markers
    drawProfessionalBorder() {
        this.ctx.strokeStyle = this.colors.accent;
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(10, 10, 780, 580);
        
        // Corner markers for professional appearance
        const corners = [[10, 10], [790, 10], [10, 590], [790, 590]];
        corners.forEach(([x, y]) => {
            this.ctx.fillStyle = this.colors.accent;
            this.ctx.fillRect(x - 5, y - 5, 10, 10);
        });
    }
    
    // Professional artificial horizon with gradients
    drawArtificialHorizon(centerX, centerY, size, roll, pitch) {
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, size, 0, 2 * Math.PI);
        this.ctx.clip();
        
        this.ctx.translate(centerX, centerY);
        this.ctx.rotate(roll);
        
        // Sky with professional blue gradient
        const skyGradient = this.ctx.createLinearGradient(0, -size, 0, size);
        skyGradient.addColorStop(0, '#4A90E2');
        skyGradient.addColorStop(1, '#87CEEB');
        this.ctx.fillStyle = skyGradient;
        this.ctx.fillRect(-size, -size, size*2, size + pitch);
        
        // Ground with professional brown gradient
        const groundGradient = this.ctx.createLinearGradient(0, -size, 0, size);
        groundGradient.addColorStop(0, '#8B4513');
        groundGradient.addColorStop(1, '#A0522D');
        this.ctx.fillStyle = groundGradient;
        this.ctx.fillRect(-size, pitch, size*2, size);
        
        // Professional horizon line
        this.ctx.strokeStyle = this.colors.textBright;
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([]);
        this.ctx.beginPath();
        this.ctx.moveTo(-size, pitch);
        this.ctx.lineTo(size, pitch);
        this.ctx.stroke();
        
        this.ctx.restore();
    }
    
    // Professional aircraft symbol
    drawAircraftSymbol(centerX, centerY) {
        this.ctx.strokeStyle = this.colors.warning;
        this.ctx.lineWidth = 3;
        this.ctx.setLineDash([]);
        this.ctx.beginPath();
        
        this.ctx.moveTo(centerX - 40, centerY);
        this.ctx.lineTo(centerX - 10, centerY);
        this.ctx.moveTo(centerX + 10, centerY);
        this.ctx.lineTo(centerX + 40, centerY);
        this.ctx.moveTo(centerX, centerY - 8);
        this.ctx.lineTo(centerX, centerY + 20);
        
        // Center dot
        this.ctx.fillStyle = this.colors.warning;
        this.ctx.arc(centerX, centerY, 3, 0, 2 * Math.PI);
        this.ctx.fill();
        this.ctx.stroke();
    }
}
# VFR HUD Configuration Guide

## Overview
This document outlines the configuration and customization requirements for the WebGCS VFR (Visual Flight Rules) Head-Up Display (HUD). The HUD has been designed to match professional glass cockpit standards while providing clean, uncluttered flight information.

## Reference Design
The HUD layout is based on the screenshot reference: `Screenshot 2025-09-06 at 17.48.02.png`

## Current Implementation Requirements

### Layout Structure
The VFR HUD follows a clean, professional layout with the following components:

#### 1. Top Left Information Panel
**Location:** Upper left corner of display
**Content:**
- Current draw: `Cur: -.-.A` (displays actual current when available)
- Battery voltage: `Bat: 0.00V` (displays actual voltage)
**Format:** White monospace text, left-aligned

#### 2. Top Right Information Panel  
**Location:** Upper right corner of display
**Content:**
- Latitude: `Lat: 0.0000000` (7 decimal places)
- Longitude: `Lon: 0.0000000` (7 decimal places)
**Format:** White monospace text, right-aligned

#### 3. Top Center Compass Rose
**Location:** Top center of display
**Components:**
- Circular compass with cardinal directions (N, E, S, W)
- Green heading needle indicating current direction
- Digital heading readout below compass
- Real-time heading updates from telemetry

#### 4. Central Attitude Indicator
**Location:** Center of display
**Features:**
- Blue sky (upper half) and brown ground (lower half)
- White horizon line extending full canvas width
- Pitch ladder with degree markings
- Yellow aircraft symbol (fixed reference)
- Roll indication through horizon rotation
- Pitch indication through vertical movement
- **CRITICAL:** Sky and ground backgrounds must extend to full canvas edges (no black space)

#### 5. Left Side Airspeed Ticker
**Location:** Left side of attitude indicator
**Features:**
- Vertical scrolling airspeed tape
- Speed tick marks every 5 knots
- Major markings every 10 knots
- Current airspeed highlighted in green
- Semi-transparent background with border

#### 6. Right Side Altitude Ticker
**Location:** Right side of attitude indicator  
**Features:**
- Vertical scrolling altitude tape
- Altitude tick marks every 10 feet
- Major markings every 20 feet
- Current altitude highlighted in green
- Semi-transparent background with border

#### 7. Status Display
**Location:** Below attitude indicator
**Content:**
- Armed/Disarmed status in green text
- Current flight mode display
- Large, bold font for visibility

## Key Design Principles

### 1. Clean, Uncluttered Layout
- **REMOVED:** Black flight update box that was cluttering the display
- **FOCUS:** Essential flight information only
- **SPACING:** Proper spacing between elements for clarity
- **NO BLACK SPACE:** VFR HUD canvas must be completely filled with sky/ground colors

### 2. Professional Aviation Colors
- **Sky Blue:** `#4A90E2` for sky representation
- **Earth Brown:** `#8B4513` for ground representation  
- **White:** `#FFFFFF` for horizon line and text
- **Green:** `#00FF00` for normal status and current values
- **Yellow:** `#FFFF00` for aircraft reference symbol

### 3. Real-time Telemetry Integration
- All displays update with live MAVLink telemetry data
- Smooth animations for tape movement and compass needle
- Exponential smoothing for fluid visual transitions

## Technical Implementation

### File Locations
- **Primary Implementation:** `/static/js/telemetry-display.js`
- **Canvas Element:** `glass-pfd-display`
- **Display Size:** 640x480 pixels

### Update Frequency
- **Animation Loop:** 60 FPS using `requestAnimationFrame`
- **Telemetry Updates:** Real-time via WebSocket
- **Smoothing Factor:** 0.15 for fluid animations

## Configuration Guidelines

### For VFR Subagent Usage
When using the VFR/telemetry display subagent, reference this configuration:

1. **Layout Matching:** Ensure all elements match the positions described above
2. **Color Consistency:** Use the specified color scheme for aviation compliance
3. **Data Format:** Follow exact formatting for coordinates and measurements
4. **Animation Quality:** Maintain smooth 60 FPS animations
5. **Professional Standards:** Keep the display clean and uncluttered

### Browser Testing
- **Primary Tool:** Use Playwright MCP server for all browser testing
- **Test URL:** `http://localhost:5002` (or current server port)
- **Screenshot Verification:** Compare against reference screenshot
- **Functionality Testing:** Verify real-time updates and animations

## Current Configuration Status

### Latest Updates
- ✅ Flight data box removed from display
- ✅ Horizon line extended to full canvas width  
- ✅ Sky and ground backgrounds extend full width (no black space)
- ✅ Clean, uncluttered VFR display layout maintained

### Future Enhancements
- Consider adding wind information display
- Implement course deviation indicators
- Add terrain awareness features
- Integrate GPS status indicators
- Enhance low-light mode compatibility

## Testing Requirements

### Browser Compatibility
- Test using Playwright MCP automation
- Verify canvas rendering across browsers
- Ensure telemetry data updates correctly
- Validate smooth animations and responsiveness

### Functional Verification  
- Real-time telemetry display updates
- Smooth tape scrolling animations
- Accurate compass heading indication
- Proper attitude indicator behavior
- Clear status message display

---

*This configuration ensures the WebGCS VFR HUD maintains professional aviation standards while providing pilots with essential flight information in a clean, readable format.*
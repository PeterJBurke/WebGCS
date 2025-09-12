# WebGCS - Complete Product Requirements Document (Replit Edition)

## Executive Summary

WebGCS is a production-ready, safety-critical web-based ground control station for MAVLink-compatible drones. The system provides comprehensive drone control through a browser interface with real-time telemetry, flight controls, mission planning capabilities, and a professional Primary Flight Display (VFR HUD).

## Project Overview

### Core Purpose
- **Safety-Critical System**: Production-ready ground control station for drone operations
- **Real-Time Control**: Live telemetry, flight controls, and mission planning
- **Professional Display**: Glass cockpit-style VFR HUD with 15 specific components
- **Web-Based**: Browser interface accessible from any device
- **MAVLink Compatible**: Works with ArduPilot, PX4, and other MAVLink drones

### Key Features
- Real-time telemetry display at 10Hz
- Professional Primary Flight Display (VFR HUD) with artificial horizon
- Interactive map with click-to-fly functionality
- Flight control buttons (ARM, DISARM, TAKEOFF, LAND, RTL, mode changes)
- Safety confirmations for critical operations
- Mission and geofence management
- Offline map tile support
- **Heartbeat audio feedback**: Audio beep played on each heartbeat (1Hz rate)
- **Heartbeat visual indicator**: Animated heart icon that pulses with each heartbeat
- Voice announcements and configurable audio feedback
- Multi-device responsive design with Bootstrap 5
- **Offline functionality**: Works without internet (local Bootstrap assets, offline maps)

## Development Setup

### Environment Requirements
- Python 3.8+ with asyncio support
- Flask and Flask-SocketIO for web application
- PyMAVLink for drone communication
- Playwright for UI testing
- **Bootstrap 5** for responsive UI framework
- Standard web development tools

### Configuration Requirements
- Drone connection parameters (IP/port)
- Web server port configuration
- Logging level settings
- Audio feedback controls
- Heartbeat rate specification
- Map tiles storage location
- **Local Bootstrap assets**: Bootstrap 5 CSS/JS files stored locally in project
- **Offline capability**: All web dependencies available without internet

## Architecture Requirements

### Critical Constraints
- **File Size Limit**: NO file may exceed 200 lines (strict enforcement)
- **Modular Design**: Break large files immediately into smaller modules
- **Single Responsibility**: Each component should have one clear purpose
- **Maximum Function Length**: 50 lines per function

### Performance Requirements
- **Telemetry Update Rate**: 10Hz to web interface
- **Logging Latency**: <1ms per log entry
- **End-to-End Telemetry Latency**: <100ms
- **Command Acknowledgment Timeout**: <5 seconds
- **Connection Establishment**: <5 seconds

### Safety Requirements
- **Confirmation Dialogs**: ARM, DISARM, TAKEOFF require explicit confirmation
- **Command Tracking**: All commands tracked with acknowledgment verification
- **Timeout Handling**: Automatic timeout for unacknowledged commands
- **Connection Monitoring**: Automatic detection of connection loss
- **Fail-Safe Behaviors**: Safe defaults on communication failure

## VFR HUD Specifications (Primary Flight Display)

### Canvas Requirements
- **Size**: 800x600px canvas
- **Update Rate**: 10Hz minimum for smooth animation
- **Styling**: Professional glass cockpit appearance
- **Background**: Sky blue above horizon, grass green below

### 15 Required Components

Based on reference specifications, implement exactly these components:

1. **Airspeed Tape** (Left Side, 60px wide)
   - Vertical tape with black background, white text
   - Values: 10, 5, 0 (descending)
   - Current speed highlighted in black box with white border
   - White horizontal tick marks
   - Font: Arial Bold, 14px

2. **Crosstrack Error & Turn Rate** (Top Center Left)
   - Small green rectangular bars above heading tape
   - Turn rate indicator "T" with directional arrow
   - Green when on track, red when off

3. **Heading Tape** (Top Horizontal, Full Width)
   - Continuous horizontal tape: 215°-W-285°-304°-NW-330°-345°
   - Blue background with white text
   - Current heading in orange box with black border
   - Cardinal directions: N, NE, E, SE, S, SW, W, NW

4. **Bank Angle Arc** (Top Center Arc)
   - Semi-circular arc: 60°-45°-30°-20°-10°-0-10°-20°-30°-45°-60°
   - Orange triangle pointer showing current bank angle
   - Arc radius: ~140px from center

5. **Telemetry Link Quality** (Top Right Corner)
   - Format: "XX%" (signal strength)
   - Green background box with white text
   - Font: Arial Bold, 14px

6. **GPS Time** (Top Right, Below Link Quality)
   - Format: "HH:MM:SS" (UTC time)
   - White text on transparent background
   - Font: Arial, 12px

7. **Altitude Tape** (Right Side, 70px wide)
   - Vertical tape: 10, 5, 0, -5, -10
   - Black background with white text
   - Current altitude in black box
   - Blue vertical bar for climb/descent rate

8. **Airspeed Readout** (Bottom Left, First Line)
   - Format: "AS 0.0" (Airspeed in m/s)
   - White text on green background box
   - Font: Arial Bold, 12px

9. **Groundspeed Readout** (Bottom Left, Second Line)
   - Format: "GS 0.0" (Groundspeed in m/s)
   - White text on green background box
   - Font: Arial Bold, 12px

10. **Battery Status** (Bottom Left, Third Line)
    - Format: "Bat 10.00v 10%"
    - Color coding: Green >40%, Yellow 20-40%, Red <20%
    - Font: Arial Bold, 12px

11. **Artificial Horizon** (Center Rectangle)
    - **Full rectangular display filling center area**
    - Sky: Blue gradient (#87CEEB to #4682B4)
    - Ground: Green gradient (#8FBC8F to #556B2F)
    - Sharp horizontal horizon line (white, 2px thick)
    - Pitch ladder: White lines every 5° (-20° to +20°)
    - Horizon line tilts with roll angle

12. **Aircraft Symbol** (Fixed Center)
    - Orange/red chevron pointing upward
    - Fixed position in exact center
    - Wing-like horizontal lines extending left/right
    - Size: 30px wide, 20px tall
    - Always remains level regardless of aircraft attitude

13. **GPS Status** (Bottom Right)
    - Format: "GPS: No Fix" or "GPS: 3D Fix (12)"
    - Color coded: Red (No Fix), Yellow (2D Fix), Green (3D Fix)
    - Font: Arial Bold, 12px

14. **Distance to Waypoint** (Bottom Center)
    - Format: "0>0°" (Distance > Bearing)
    - White text on dark background
    - Font: Arial Bold, 12px

15. **Flight Mode** (Bottom Right Corner)
    - Format: "Stabilize" or current flight mode
    - Large white text on semi-transparent dark background
    - Font: Arial Bold, 16px

### Status Overlays
- **DISARMED Status**: Large red text "DISARMED" centered over horizon
- **ARMED Status**: Large green text "ARMED" centered over horizon

## User Interface Layout

### Bootstrap 5 Responsive Design
- **Framework**: Use Bootstrap 5 for responsive grid system and professional UI components
- **Grid Layout**: Bootstrap container-fluid with responsive columns for different screen sizes
- **Component Styling**: Bootstrap buttons, forms, cards, alerts, and navigation components
- **Responsive Breakpoints**: Adapt layout for desktop, tablet, and mobile devices
- **Professional Appearance**: Clean, modern interface using Bootstrap's design system
- **🚨 OFFLINE REQUIREMENT**: All Bootstrap 5 assets (CSS, JS) MUST be locally cached/bundled
- **No CDN Dependencies**: Do not use Bootstrap CDN links - download and serve locally
- **Internet Independence**: Website must work without internet access for Bootstrap assets

### Main Interface Components
- **Primary Flight Display (VFR HUD)**: Bootstrap card containing 800x600px canvas with artificial horizon, flight tapes, and all 15 required components
- **Interactive Map**: Bootstrap card with drone position, home marker, target markers, and click-to-fly functionality
- **Connection Panel**: Bootstrap form with input groups for IP/port, styled buttons for Connect/Disconnect, connection status badges, heartbeat indicator
- **Flight Controls**: Bootstrap button groups for ARM, DISARM, TAKEOFF (with input group for altitude), LAND, RTL, and styled dropdown for flight mode selection
- **Navigation Panel**: Bootstrap form with input groups for latitude, longitude, altitude and styled action buttons
- **Request Panel**: Bootstrap button toolbar for geofence and mission request buttons
- **Message Log**: Bootstrap card with scrollable body containing timestamped system messages

## MAVLink Integration

### Connection Management
- TCP connection to drone (default: 172.233.128.95:5678)
- Automatic reconnection on connection loss
- Heartbeat monitoring (expected at 1Hz - every 1 second)
- Connection status propagation to all UI components
- **Heartbeat Visual Indicator**: Animated heart icon (❤️) that beats/pulses when heartbeat received
- **Heartbeat Audio Feedback**: Audio beep sound played every time heartbeat message received
- **Heartbeat Counter**: Display incrementing counter showing total heartbeats received

### Message Handling
**Incoming Messages:**
- `HEARTBEAT` - Connection monitoring, system status (received at 1Hz rate)
- `GLOBAL_POSITION_INT` - GPS position data
- `ATTITUDE` - Roll, pitch, yaw orientation
- `VFR_HUD` - Airspeed, groundspeed, heading, throttle
- `BATTERY_STATUS` - Voltage, current, remaining capacity
- `COMMAND_ACK` - Command acknowledgments
- `GPS_RAW_INT` - GPS status and satellite count
- `SYS_STATUS` - System health and diagnostics

**Outgoing Commands:**
- `MAV_CMD_COMPONENT_ARM_DISARM` - ARM/DISARM
- `MAV_CMD_NAV_TAKEOFF` - Takeoff with altitude
- `MAV_CMD_NAV_LAND` - Immediate landing
- `MAV_CMD_NAV_RETURN_TO_LAUNCH` - Return to home
- `MAV_CMD_DO_SET_MODE` - Flight mode changes
- `MAV_CMD_DO_REPOSITION` - Go-to waypoint navigation

### Thread Safety
- All MAVLink operations must be thread-safe
- Concurrent message processing support
- Shared state protection with appropriate locking

## Flask-SocketIO Implementation

### Server Components
- Flask application factory pattern for modular design
- SocketIO event handlers for real-time communication
- Client connection/disconnection management
- Drone command processing and validation
- Telemetry streaming at 10Hz rate

### Client-Side JavaScript
- Connection management with automatic reconnection
- Real-time telemetry updates and PFD rendering
- Interactive controls and user input handling with Bootstrap validation
- Map integration with click-to-fly functionality
- Audio feedback and visual indicator management
- Bootstrap component interaction (modals, alerts, tooltips)
- Responsive behavior across different screen sizes

## Testing Requirements

### Test Philosophy
**🚨 CRITICAL: NO MOCK TESTS ALLOWED 🚨**

All tests must verify actual functionality:
- ✅ **REQUIRED**: Real MAVLink connection to virtual drone
- ✅ **REQUIRED**: Actual command sending and acknowledgment
- ✅ **REQUIRED**: Real telemetry streaming and display updates
- ✅ **REQUIRED**: Visual components render actual data
- ✅ **REQUIRED**: Tests FAIL when functionality is broken
- ❌ **PROHIBITED**: Mock tests that fake success responses
- ❌ **PROHIBITED**: Tests that only check UI elements exist
- ❌ **PROHIBITED**: Tests that only verify events are emitted

**🌐 MANDATORY: ALL TESTS MUST USE ACTUAL WEBSITE UI**
- **DEPLOY WEBSITE**: Website MUST be running and accessible in browser
- **CLICK ACTUAL BUTTONS**: Use Playwright or similar to click real UI buttons
- **VERIFY IN BROWSER**: Confirm functionality works in the actual web interface
- **NO BACKEND-ONLY TESTING**: Do not test server code in isolation
- **END-TO-END VALIDATION**: Test complete user workflows through the UI

### Test Environment Setup
**🚨 CRITICAL: WEBSITE DEPLOYMENT REQUIRED FOR ALL TESTS**
- **Website MUST be deployed and running**: Website accessible in browser
- **Browser testing required**: Open actual website in browser, not just server testing
- **UI interaction testing**: Click buttons, fill forms, observe visual changes in browser
- **Server must remain running**: Keep web application running during all testing phases
- **Real drone connection**: Connect to virtual drone (IP: 172.233.128.95, Port: 5678)
- **Default IP validation**: Website must display 172.233.128.95:5678 as default in connection form
- **End-to-end validation**: Test complete user experience through website interface

### 7 Testing Phases (50+ Tests Total)

#### Phase 1: MAVLink Foundation (Tests 001-003)
**Backend connectivity and protocol implementation**
- TEST-001: Basic connection to virtual drone
  * Establish TCP connection to 172.233.128.95:5678
  * Verify MAVLink handshake and protocol detection
  * Test connection timeout handling
- TEST-002: Heartbeat message reception
  * Receive HEARTBEAT messages at 1Hz (every 1 second)
  * Parse system ID, component ID, and vehicle type
  * Test heartbeat timeout detection
  * Verify heartbeat animation triggers on message receipt
  * Test heartbeat audio beep functionality
- TEST-003: Telemetry/message processing
  * Process ATTITUDE, GLOBAL_POSITION_INT, VFR_HUD messages
  * Validate message parsing and data extraction
  * Test message rate monitoring (10Hz target)

**Gate Criteria**: All 3 tests must pass before Phase 2

#### Phase 2: Web Interface Foundation (Tests 004-008)
**Flask-SocketIO application and real-time communication**

**🚨 CRITICAL: Deploy Website Early for UI Testing**
- **MANDATORY FIRST STEP**: Deploy website and ensure browser accessibility
- **BROWSER ACCESSIBILITY REQUIRED**: Website MUST be accessible in browser for UI testing
- **ALL SUBSEQUENT TESTS REQUIRE UI**: Every test from Phase 2 onwards must interact with actual website
- **NO SERVER-ONLY TESTING**: Tests must click buttons and interact with web interface, not just backend

- TEST-004: SocketIO version compatibility **[MANDATORY FIRST]**
  * Validate client/server version compatibility
  * Prevent "Not connected to WebGCS server" popup
  * Test real user behavior with immediate button clicks
- TEST-004a: **Default IP Address UI Validation**
  * **🌐 BROWSER TESTING**: Open deployed website in browser
  * **📋 UI INSPECTION**: Read IP address field value displayed in connection form
  * **✅ VERIFY DEFAULT**: Confirm IP field shows "172.233.128.95" as default value
  * **✅ VERIFY PORT**: Confirm port field shows "5678" as default value
  * **🚨 CRITICAL**: Must test actual UI display, NOT backend configuration or server code
- TEST-005: Flask-SocketIO server startup
  * Start Flask web application
  * Verify SocketIO integration
  * Test static file serving and template rendering
- TEST-006: SocketIO real-time connection
  * Establish SocketIO connection between client and server
  * Test event emission and reception
  * Verify real-time data flow
- TEST-007: Basic telemetry streaming
  * Stream telemetry data from drone to web interface
  * Verify 10Hz update rate
  * Test data flow: Drone → MAVLink → Backend → SocketIO → Frontend
- TEST-008: Connection form pre-population validation
  * **🌐 UI VERIFICATION**: Load website and inspect connection form fields
  * **📝 DEFAULT VALUES**: Verify IP field contains "172.233.128.95" and port field contains "5678"
  * **👁️ VISUAL CONFIRMATION**: Confirm default values are visible to user in browser interface

**Gate Criteria**: All 5 tests must pass (including default IP validation) AND website deployed before Phase 3

#### Phase 3: Performance & Safety (Tests 009-012)
**System performance optimization and safety mechanisms**
- TEST-009: Logging performance <1ms
  * Benchmark logging latency under load
  * Verify <1ms per log entry requirement
  * Test concurrent logging performance
- TEST-010: Telemetry latency <100ms
  * Measure end-to-end telemetry latency
  * Test: Drone message → Web display update
  * Verify <100ms requirement maintained
- TEST-011: Command safety mechanisms
  * Test safety confirmation dialogs
  * Verify command timeout handling
  * Test fail-safe behaviors on communication loss
- TEST-012: Integration workflow
  * End-to-end system integration test
  * Complete workflow: Connect → Arm → Command → Telemetry
  * Performance validation under operational load

**Gate Criteria**: All 4 tests must pass before Phase 4

#### Phase 4: Individual Button Testing (Tests 013-034)
**Comprehensive UI button functionality with Playwright**

**🚨 CRITICAL: WEBSITE UI TESTING MANDATORY**
- **PREREQUISITE**: Website MUST be deployed and accessible in browser
- **BROWSER INTERACTION REQUIRED**: Use Playwright to open website in browser and click actual buttons
- **VISUAL CONFIRMATION**: Observe button responses, status changes, and UI updates in browser
- **NO PROGRAMMATIC TESTING**: Do not test button handlers or backend functions directly
- **USER EXPERIENCE VALIDATION**: Test exactly what a user would see and do in the website

**Real Data Validation Requirements:**
- ✅ Real MAVLink heartbeat messages received AND displayed in UI
- ✅ Real telemetry data displayed on HUD AND visible in browser
- ✅ Real drone position shown on map AND rendered in browser
- ✅ Real command acknowledgments from drone AND reflected in UI
- ❌ Tests MUST FAIL if data is missing, fake, OR not visible in browser interface

**Connection Tests:**
- TEST-013: Real MAVLink connection validation
  * **BROWSER TESTING**: Open website in browser, click Connect button, observe UI changes
  * **VISUAL VERIFICATION**: Watch heartbeat visual indicator pulse at 1Hz in browser
  * **AUDIO TESTING**: Listen for heartbeat audio beep in browser interface
  * **UI VALIDATION**: See heartbeat counter increment in connection panel on website
- TEST-014: Telemetry data flow validation
- TEST-015: HUD data display validation
- TEST-016: Map data display validation

**Flight Control Tests:**
- TEST-017: ARM command real validation
- TEST-018: DISARM command real validation
- TEST-019: TAKEOFF command real validation
- TEST-020: LAND button emergency capability
- TEST-021: RTL (Return to Launch) button
- TEST-022: Flight mode buttons comprehensive

**Navigation Tests:**
- TEST-023: GO TO command real validation
- TEST-024: Navigation CLEAR real validation
- TEST-025: Navigation integration

**Mission/Fence Tests:**
- TEST-026: Geofence REQUEST button
- TEST-027: Mission REQUEST button

**Map Interface Tests:**
- TEST-028: Map drone position validation
- TEST-029: Fly-to real command validation
- TEST-030: Map interface interactions

**Additional Integration Tests:**
- TEST-031: Button functionality
- TEST-032: Real drone button integration
- TEST-033: Flight control buttons comprehensive
- TEST-034: Connection workflow end-to-end

**Gate Criteria**: All 22 tests must pass before Phase 5

#### Phase 5: VFR HUD/PFD Display Testing (Tests 035-040)
**Visual component validation and Primary Flight Display**

**🚨 MANDATORY: VISUAL VALIDATION IN BROWSER**
- **WEBSITE MUST BE RUNNING**: Deployed and accessible in browser for visual testing
- **BROWSER-BASED TESTING**: View actual PFD canvas rendering in web browser
- **VISUAL CONFIRMATION**: Verify all 15 VFR HUD components display correctly in UI
- **REAL-TIME OBSERVATION**: Watch telemetry updates animate in browser interface
- TEST-035: PFD canvas foundation
  * Verify 800x600 canvas rendering
  * Test coordinate system and graphics pipeline
  * Validate basic drawing operations
- TEST-036: Rectangular attitude display
  * Test artificial horizon (rectangular display)
  * Verify pitch ladder and roll indication
  * Test aircraft symbol positioning
- TEST-037: Flight data tapes
  * Verify airspeed tape (left side)
  * Test altitude tape (right side)
  * Validate current value highlighting
- TEST-038: Navigation elements
  * Test heading compass tape
  * Verify GPS status and satellite count
  * Test waypoint distance display
- TEST-039: System status displays
  * Verify battery status with color coding
  * Test armed/disarmed status overlay
  * Validate flight mode and telemetry link quality
- TEST-040: Complete VFR integration
  * All 15 HUD elements integrated
  * Real-time updates at 10Hz
  * Professional glass cockpit styling

**Gate Criteria**: All 6 tests must pass before Phase 6

#### Phase 6: UI Validation & Safety (Tests 041-045)
**Input validation, error handling, and safety confirmations**

**🚨 CRITICAL: UI INTERACTION TESTING REQUIRED**
- **BROWSER INTERFACE TESTING**: Open website and interact with actual form inputs and buttons
- **SAFETY DIALOG TESTING**: Click ARM/DISARM/TAKEOFF buttons and verify confirmation dialogs appear
- **INPUT VALIDATION**: Enter invalid data in forms and observe error messages in browser
- **USER EXPERIENCE VALIDATION**: Test exactly what users see and experience on the website
- TEST-041: UI validation comprehensive
  * Test all input field validations
  * Verify error message display
  * Test form validation before submission
- TEST-042: Validation logic
  * Test coordinate validation (-90 to 90 lat, -180 to 180 lon)
  * Verify altitude input validation
  * Test input sanitization and formatting
- TEST-043: Safety confirmations
  * Test safety dialogs for ARM/DISARM/TAKEOFF
  * Verify confirmation prevents accidental commands
  * Test emergency command overrides
- TEST-044: Critical validation
  * Test timeout handling for commands
  * Verify connection loss detection
  * Test fail-safe behaviors
- TEST-045: Final validation report
  * Comprehensive system validation
  * Generate validation report
  * Performance benchmark validation

**Gate Criteria**: All 5 tests must pass before Phase 7

#### Phase 7: Integration Testing (Tests 046-052)
**End-to-end system validation and performance testing**

**🚨 FINAL VALIDATION: COMPLETE WEBSITE FUNCTIONALITY**
- **FULL WEBSITE TESTING**: Complete end-to-end user workflows through browser interface
- **PRODUCTION SIMULATION**: Test website as if real users are operating drone controls
- **COMPREHENSIVE UI VALIDATION**: All buttons, displays, and interactions working in browser
- **PERFORMANCE VERIFICATION**: Observe real-time updates and responsiveness in web interface
- TEST-046: SocketIO connection
  * Complete SocketIO communication test
  * Test connection stability under load
  * Verify event handling reliability
- TEST-047: Minimal SocketIO
  * Minimal viable SocketIO functionality
  * Basic event emission and reception
  * Connection lifecycle management
- TEST-048: Navigation with connection
  * Navigation functionality with live connection
  * End-to-end waypoint navigation
  * Real-time position updates
- TEST-049: Performance integration
  * System performance under full load
  * All requirements validation simultaneously
  * Stress testing with multiple operations
- TEST-050: Safety integration
  * Complete safety system validation
  * Emergency scenarios and recovery
  * Multi-component safety coordination
- TEST-051: Full system validation
  * Complete end-to-end system test
  * All components working together
  * Production readiness validation
- TEST-052: **FINAL COMPLETE WEBSITE VALIDATION**
  * **🌐 LAUNCH WEBSITE**: Deploy and access website in browser
  * **🔌 CONNECT VIA UI**: Click Connect button on website, enter drone IP/port in web interface
  * **👀 OBSERVE CONNECTION IN WEBSITE**: Watch connection status change to "Connected" in UI
  * **🗺️ OBSERVE DRONE LOCATION ON MAP**: See blue drone marker appear on map in website
  * **📊 OBSERVE ALL TELEMETRY IN WEBSITE**: Watch VFR HUD display real attitude, speed, altitude, battery data
  * **🚁 CLICK ARM IN WEBSITE**: Click ARM button, confirm safety dialog, see "ARMED" status in UI
  * **🛫 CLICK TAKEOFF IN WEBSITE**: Click TAKEOFF button, set altitude, confirm in UI
  * **✈️ VERIFY TAKEOFF IN WEBSITE**: Watch altitude increase on VFR HUD and drone position change on map
  * **🚨 CRITICAL**: ALL verification must be visual in website UI - NO backend code inspection allowed
  * **🎯 SUCCESS CRITERIA**: Complete drone control workflow visible and working in browser interface

**Gate Criteria**: All 7 tests must pass for project completion

### Test Execution Strategy
**🌐 MANDATORY: WEBSITE-BASED TESTING ONLY**
- **DEPLOY WEBSITE FIRST**: Ensure website is deployed and accessible in browser
- **BROWSER INTERACTION**: Use Playwright or similar to interact with actual website UI
- **VISUAL VERIFICATION**: Observe all changes, animations, and data updates in browser
- **CLICK REAL BUTTONS**: Test actual button clicks, form submissions, and user interactions
- **END-TO-END WORKFLOWS**: Complete user journeys from connection to flight commands
- **NO BACKEND-ONLY TESTS**: Do not test server functions without UI interaction
- **PHASE PROGRESSION**: All tests in a phase must pass before advancing to next phase

## Development Guidelines

### Code Quality Standards
- **Type Hints**: Use Python type hints throughout
- **Documentation**: Docstrings for all public functions and classes
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging with appropriate levels
- **Testing**: Test-driven development approach

### Safety-Critical Development
1. **Write Test First**: Create failing test before implementation
2. **Implement Minimal Code**: Just enough to make test pass
3. **Refactor**: Improve code while maintaining green tests
4. **Never Skip Tests**: No partial implementations allowed
5. **Real Hardware Testing**: Always test with actual drone connection

### Performance Optimization
- Asynchronous operations for non-blocking UI
- Efficient canvas rendering with minimal redraws
- WebSocket connection optimization
- Memory management for long-running operations
- Caching strategies for map tiles and static data

## Deployment Requirements

### Development Environment
- Development server with debug mode enabled
- Website deployed and accessible in browser
- Auto-reload functionality for rapid development
- Virtual drone connection for testing

### Production Environment
- Production-optimized configuration
- Real drone IP and standard MAVLink port settings
- WSGI server deployment with proper worker configuration
- Enhanced error handling and logging

### System Requirements
- **Python**: 3.8+ with asyncio support
- **Memory**: 512MB minimum, 1GB recommended
- **Network**: TCP connectivity to drone
- **Browser**: Modern browser with WebSocket support

## Success Criteria

**Project completion requires ALL of:**
1. ✅ ALL 51+ tests PASS (100% pass rate required)
2. ✅ Every button functional (no mock implementations)
3. ✅ Real drone connection verified
4. ✅ Performance requirements met (<1ms log, <100ms telemetry, 10Hz updates)
5. ✅ Safety confirmations implemented and tested
6. ✅ VFR HUD displays all 15 components correctly
7. ✅ Modular architecture enforced (no file >200 lines)
8. ✅ Website fully functional and accessible in browser
9. ✅ Interactive map with click-to-fly working
10. ✅ Professional glass cockpit styling implemented
11. ✅ **Bootstrap 5 responsive design fully implemented with local assets**
12. ✅ **Complete offline functionality** (Bootstrap assets, map tiles, no CDN dependencies)
13. ✅ Offline map functionality operational

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Project structure setup
2. MAVLink connection implementation
3. Basic Flask-SocketIO application
4. Phase 1 tests (001-003)

### Phase 2: Web Interface (Week 2)
1. Download and integrate Bootstrap 5 assets locally (CSS, JS files)
2. Deploy website with local Bootstrap 5 framework
3. SocketIO real-time communication
4. Bootstrap UI components (cards, forms, buttons, alerts) using local assets
5. Responsive grid layout for different screen sizes
6. Verify offline functionality without internet access
7. Phase 2 tests (004-007)

### Phase 3: Core Functionality (Week 3)
1. Flight control implementation
2. Navigation system
3. Performance optimization
4. Phase 3-4 tests (008-033)

### Phase 4: Display & Safety (Week 4)
1. VFR HUD implementation (all 15 components)
2. Interactive map integration with Bootstrap styling
3. Bootstrap modal dialogs for safety confirmations
4. Responsive design optimization
5. Phase 5-6 tests (034-044)

### Phase 5: Integration & Polish (Week 5)
1. End-to-end integration
2. Performance tuning
3. Error handling refinement
4. Phase 7 tests (045-051)
5. Final validation and deployment preparation

---

## Quick Start Guide

1. **Setup Environment**: Install Python dependencies including Flask, Flask-SocketIO, PyMAVLink, and testing frameworks
2. **Download Bootstrap Assets**: Download Bootstrap 5 CSS and JS files, store locally in project
3. **Configuration**: Set up environment variables for drone connection, web server, and feature toggles
4. **Run Application**: Deploy the web application and ensure browser accessibility
5. **Verify Offline Mode**: Test website functionality without internet connection
6. **Connect to Drone**: Use connection panel to establish MAVLink communication
7. **Verify Functionality**: Test heartbeat reception, telemetry display, and control responsiveness
8. **Run Tests**: Execute comprehensive test suite to validate all functionality

This comprehensive PRD provides everything needed to implement the complete WebGCS system without requiring the multi-agent Claude Code setup. The system maintains all safety-critical requirements, performance specifications, and comprehensive testing while being suitable for standard development environments like Replit.
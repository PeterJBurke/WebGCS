# WebGCS Product Requirements Document (PRD)

## Executive Summary

WebGCS (Web Ground Control Station) is a safety-critical, real-time web application for controlling MAVLink-compatible drones. The system provides comprehensive ground control capabilities through a browser-based interface, supporting mission planning, real-time telemetry monitoring, and direct flight control with enterprise-grade reliability.

## Product Vision

To create the most reliable, responsive, and user-friendly web-based ground control station that enables safe drone operations in both connected and offline environments, with deployment flexibility across desktop and embedded platforms.

## Business Objectives

### Primary Objectives
- **Safety First**: Achieve zero safety incidents through robust command acknowledgment and error handling
- **Real-time Performance**: Maintain <100ms telemetry latency and <1ms logging performance
- **Platform Flexibility**: Support deployment on Ubuntu desktop and Raspberry Pi field systems
- **Offline Capability**: Ensure full operational capability without internet connectivity
- **User Experience**: Provide intuitive web interface accessible from any modern browser

### Success Metrics
- **Telemetry Update Rate**: 10Hz continuous updates to web interface
- **Command Response Time**: <5 seconds for flight command acknowledgment
- **System Uptime**: 99.9% availability in field deployments
- **Connection Reliability**: Automatic recovery from network interruptions
- **Performance**: <1ms logging latency for safety-critical operations

## Target Users

### Primary Users
- **Drone Pilots**: Professional operators requiring real-time control and monitoring
- **Mission Planners**: Users creating and executing autonomous flight missions
- **Field Technicians**: Personnel deploying systems in remote locations

### Secondary Users
- **System Administrators**: IT personnel managing deployed systems
- **Developers**: Engineers extending or customizing the platform
- **Safety Officers**: Personnel monitoring flight operations for compliance

## Product Requirements

### Functional Requirements

#### FR-1: Real-time Drone Communication
- **FR-1.1**: Establish and maintain MAVLink protocol connections via TCP/UDP/Serial
- **FR-1.2**: Process all standard MAVLink message types (HEARTBEAT, GLOBAL_POSITION_INT, etc.)
- **FR-1.3**: Handle connection failures with automatic retry and user notification
- **FR-1.4**: Support multiple concurrent drone connections
- **FR-1.5**: Validate message integrity and source system identification

#### FR-2: Flight Control Operations  
- **FR-2.1**: ARM/DISARM drone with explicit user confirmation
- **FR-2.2**: Change flight modes (STABILIZE, GUIDED, AUTO, RTL, etc.)
- **FR-2.3**: Send navigation commands (GOTO, LOITER, LAND)
- **FR-2.4**: Emergency stop functionality with immediate response
- **FR-2.5**: Command acknowledgment tracking with timeout handling

#### FR-3: Telemetry Display
- **FR-3.1**: Real-time position display on interactive map
- **FR-3.2**: Flight parameter monitoring (altitude, speed, heading, battery)
- **FR-3.3**: GPS status and satellite count display
- **FR-3.4**: System health indicators (EKF status, sensor health)
- **FR-3.5**: Historical telemetry data visualization

#### FR-4: Mission Planning
- **FR-4.1**: Create and edit waypoint missions through web interface
- **FR-4.2**: Upload/download missions to/from drone
- **FR-4.3**: Mission progress monitoring during execution
- **FR-4.4**: Mission validation and safety checks
- **FR-4.5**: Mission library management and templates

#### FR-5: Geofencing
- **FR-5.1**: Define polygon-based geofence boundaries
- **FR-5.2**: Upload geofence to drone flight controller
- **FR-5.3**: Real-time geofence violation monitoring
- **FR-5.4**: Automatic safety actions on fence breach
- **FR-5.5**: Multiple fence zone support (inclusion/exclusion)

#### FR-6: Offline Maps
- **FR-6.1**: Pre-cache map tiles for offline operation
- **FR-6.2**: Support OpenStreetMap and satellite imagery
- **FR-6.3**: Automatic tile download based on mission areas
- **FR-6.4**: Cache management with storage optimization
- **FR-6.5**: Fallback to cached tiles when network unavailable

#### FR-7: User Interface Components
- **FR-7.1**: Primary Flight Display (PFD) with real-time flight instruments
- **FR-7.2**: Interactive map interface with drone positioning and navigation
- **FR-7.3**: Connection management interface with IP/Port configuration
- **FR-7.4**: Flight control buttons and mode selection interface
- **FR-7.5**: Navigation input interface for coordinate-based flight commands
- **FR-7.6**: Offline map management panel with tile download capabilities
- **FR-7.7**: Real-time status displays and message logging interface
- **FR-7.8**: Voice announcement controls and audio feedback system

#### FR-8: System Monitoring
- **FR-8.1**: Connection status display with health indicators
- **FR-8.2**: Performance metrics monitoring (latency, message rates)
- **FR-8.3**: Error logging and diagnostic information
- **FR-8.4**: System resource utilization tracking
- **FR-8.5**: Automated health checks and alerts

### Detailed Interface Requirements

#### UI-1: Primary Flight Display (PFD) Interface
- **UI-1.1**: Attitude indicator with pitch and roll visualization (280x250px canvas)
- **UI-1.2**: Airspeed indicator tape (60x250px vertical tape display)
- **UI-1.3**: Altitude indicator tape (70x250px vertical tape display)
- **UI-1.4**: Arming status overlay displaying "ARMED" or "DISARMED"
- **UI-1.5**: Battery voltage display with real-time updates (format: "Bat: XX.X V")
- **UI-1.6**: Current flight mode display (format: "Mode: XXXX")
- **UI-1.7**: Current draw display (format: "Cur: XX.X A")
- **UI-1.8**: GPS status with fix type, satellite count, and HDOP (format: "GPS: XXX (X) HDOP:XX.X")
- **UI-1.9**: Latitude/Longitude display with 6 decimal precision

#### UI-2: Connection Management Interface
- **UI-2.1**: Connection status indicator with colored text (green=connected, red=disconnected, blue=connecting)
- **UI-2.2**: Heartbeat indicator (❤️ icon) with beat counter display
- **UI-2.3**: Heartbeat visual animation - icon pulses/scales with each received heartbeat
- **UI-2.4**: Heartbeat audio beep - audible tone generated for each received heartbeat
- **UI-2.5**: Heartbeat sound toggle with custom slider control and speaker icon to enable/disable audio
- **UI-2.6**: IP Address text input field with placeholder "192.168.193.235" (default: 192.168.193.235)
- **UI-2.7**: Port number input field with validation (1-65535, default: 5678)
- **UI-2.8**: Connect button (green styling, disabled when connected)
- **UI-2.9**: Disconnect button (red styling, disabled when disconnected)

#### UI-3: Flight Control Interface
- **UI-3.1**: Arm button for vehicle arming with confirmation dialog
- **UI-3.2**: Disarm button for vehicle disarming with confirmation dialog
- **UI-3.3**: Takeoff button with altitude input field (default: 5m, range: 1-1000m)
- **UI-3.4**: Land button for immediate landing command
- **UI-3.5**: RTL (Return to Launch) button for autonomous return
- **UI-3.6**: Flight mode dropdown selector with options:
  - STABILIZE, ALT_HOLD, POS_HOLD, LOITER, GUIDED, RTL, LAND, AUTO, BRAKE
- **UI-3.7**: Set Mode button to apply selected flight mode

#### UI-4: Navigation Control Interface
- **UI-4.1**: Latitude input field with step precision and range validation ([-90,90])
- **UI-4.2**: Longitude input field with step precision and range validation ([-180,180])
- **UI-4.3**: Altitude input field (AGL) with default 10m and range (-100 to 5000m)
- **UI-4.4**: Go To button to execute navigation command to specified coordinates
- **UI-4.5**: Clear button to reset all navigation input fields

#### UI-5: Request Control Interface
- **UI-5.1**: Request Fence button to download geofence from vehicle
- **UI-5.2**: Request Mission button to download mission waypoints from vehicle

#### UI-6: Interactive Map Interface
- **UI-6.1**: Leaflet-based interactive map with zoom controls (levels 2-22)
- **UI-6.2**: Layer control with Street/Satellite map type selection (always expanded)
- **UI-6.3**: Drone position marker with directional arrow icon (blue)
- **UI-6.4**: Home position marker with house icon (green)
- **UI-6.5**: Target marker for fly-to destinations with bullseye icon (red, pulsing animation)
- **UI-6.6**: Center Map button to center view on drone position
- **UI-6.7**: Fly To mode toggle button with ON/OFF states (green when active)
- **UI-6.8**: Click-to-fly functionality when Fly To mode is enabled
- **UI-6.9**: Map controls positioned at top-left with translucent background

#### UI-7: Voice and Audio Interface
- **UI-7.1**: Voice Announcements checkbox toggle for audio feedback
- **UI-7.2**: Heartbeat sound effects with toggle control
- **UI-7.3**: Real-time heartbeat beep generation synchronized with MAVLink heartbeat messages
- **UI-7.4**: Audio feedback for flight mode changes and system status
- **UI-7.5**: Heartbeat animation synchronization with visual icon pulsing effect

#### UI-8: Message Logging Interface
- **UI-8.1**: Real-time message log display area with timestamp
- **UI-8.2**: Scrollable message history with automatic updates
- **UI-8.3**: Color-coded message types for different system events

#### UI-9: Offline Maps Management Panel
- **UI-9.1**: Offline Maps toggle button with radar icon (📡)
- **UI-9.2**: Collapsible side panel with close button (×)
- **UI-9.3**: Internet connection status indicator with online/offline states
- **UI-9.4**: Download area coordinate inputs:
  - North Latitude (step: 0.000001)
  - South Latitude (step: 0.000001)
  - West Longitude (step: 0.000001)
  - East Longitude (step: 0.000001)
- **UI-9.5**: Use Current Map View button to auto-populate coordinates
- **UI-9.6**: Zoom level range inputs (Min: default 2, Max: default 16, range: 1-20)
- **UI-9.7**: Map type selection checkboxes:
  - Street Map (OpenStreetMap)
  - Satellite (Esri imagery)
- **UI-9.8**: Area preview with estimated tile count and storage size
- **UI-9.9**: Download tiles button with progress indication
- **UI-9.10**: Stop download button (enabled during download)
- **UI-9.11**: Progress bar with percentage and tile count status
- **UI-9.12**: Cache statistics display:
  - Street tiles count
  - Satellite tiles count
  - Total tiles count
- **UI-9.13**: Clear cache button with confirmation dialog
- **UI-9.14**: Usage tip section with download area hints

#### UI-10: Additional Interface Elements
- **UI-10.1**: Main title header "Drone Control Interface v2.0" with dark background
- **UI-10.2**: MAVLink Dump link button for debugging/diagnostic page
- **UI-10.3**: Responsive layout with left column (controls) and right column (map)
- **UI-10.4**: Button state management (enabled/disabled based on connection status)
- **UI-10.5**: Input validation with range restrictions and error handling
- **UI-10.6**: Consistent styling with hover effects and transitions
- **UI-10.7**: Accessibility features including tooltips and ARIA labels

### Code Organization Requirements

#### CO-1: File Structure and Separation of Concerns
- **CO-1.1**: HTML structure must be separated from JavaScript code (no inline JavaScript in index.html)
- **CO-1.2**: CSS styling must be separated into external stylesheet files (no inline CSS in index.html)
- **CO-1.3**: JavaScript functionality must be modularized into multiple files based on functional areas
- **CO-1.4**: Each JavaScript module should handle a specific domain (e.g., map controls, flight controls, UI updates)
- **CO-1.5**: Maintain clear separation between presentation layer (HTML/CSS) and business logic (JavaScript)

#### CO-2: JavaScript Modular Architecture
- **CO-2.1**: Map management JavaScript module for all map-related functionality
- **CO-2.2**: Flight control JavaScript module for drone command operations
- **CO-2.3**: Connection management JavaScript module for MAVLink communication handling
- **CO-2.4**: UI state management JavaScript module for interface updates and real-time data display
- **CO-2.5**: Audio/voice JavaScript module for sound effects and voice announcements
- **CO-2.6**: Offline maps JavaScript module for tile management and caching
- **CO-2.7**: Main application JavaScript module for initialization and coordination
- **CO-2.8**: Each module should have clear APIs and minimal dependencies on other modules

#### CO-3: CSS Organization Requirements
- **CO-3.1**: Main stylesheet for overall layout and component styling
- **CO-3.2**: Responsive design CSS rules for mobile and desktop compatibility
- **CO-3.3**: Animation and transition CSS for heartbeat effects and UI feedback
- **CO-3.4**: Map-specific CSS for Leaflet customizations and overlay styling
- **CO-3.5**: Offline maps panel CSS for download interface styling
- **CO-3.6**: CSS variables for consistent theming and easy maintenance

#### CO-4: Modular File Organization Standards
- **CO-4.1**: Maximum file size limit of 200 lines per file (preferably under 150 lines)
- **CO-4.2**: Single responsibility principle - each file handles one specific function or related set of functions
- **CO-4.3**: Modular Python backend structure under `/src/` directory:
  - `/src/app/` - Flask application factory and configuration (≤50 lines per file)
  - `/src/mavlink/` - MAVLink protocol handling, split by message type (≤150 lines per file)
  - `/src/socketio/` - SocketIO event handlers, split by event category (≤120 lines per file)
  - `/src/web/` - Web routes and endpoints (≤100 lines per file)
  - `/src/models/` - Data structures and state management (≤150 lines per file)
  - `/src/services/` - Business logic services (≤150 lines per file)
  - `/src/utils/` - Utility functions and constants (≤100 lines per file)
- **CO-4.4**: Modular frontend structure under `/static/`:
  - `/static/js/` - JavaScript modules by functionality (≤200 lines per file)
  - `/static/css/` - CSS files by component/section (≤200 lines per file)
  - `/static/templates/` - HTML templates, minimal and focused (≤100 lines per file)
- **CO-4.5**: Modular test structure under `/tests/`:
  - `/tests/unit/` - Unit tests per module (≤150 lines per file)
  - `/tests/integration/` - Integration tests (≤200 lines per file)
  - `/tests/performance/` - Performance benchmarks (≤100 lines per file)
- **CO-4.6**: Clear import/dependency management with minimal coupling between modules
- **CO-4.7**: Descriptive file naming that reflects exact functionality
- **CO-4.8**: Each file must be self-contained and easily understood by LLM without external context

#### CO-5: Token Usage Management Requirements
- **CO-5.1**: Implement comprehensive token tracking system for all agents (main + 6 subagents)
- **CO-5.2**: Track input tokens, output tokens, and cumulative usage per agent per session
- **CO-5.3**: Automatic warning system at 80% of Claude context limit (~160K tokens)
- **CO-5.4**: Critical alerts at 90% of context limit with restart recommendations
- **CO-5.5**: Session logging with timestamps, agent breakdown, and usage statistics
- **CO-5.6**: Periodic status reports every 10-15 subagent tasks during development
- **CO-5.7**: Token usage optimization recommendations when approaching limits
- **CO-5.8**: Session persistence and recovery procedures for context limit scenarios
- **CO-5.9**: Individual agent monitoring with high-usage alerts (>20K tokens per agent)
- **CO-5.10**: Export functionality for token usage logs and performance analysis

### Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1**: Telemetry updates at 10Hz to web interface
- **NFR-1.2**: <1ms latency for logging operations
- **NFR-1.3**: <100ms end-to-end telemetry latency
- **NFR-1.4**: Support 100+ concurrent web client connections
- **NFR-1.5**: Minimal memory footprint for embedded deployment

#### NFR-2: Reliability
- **NFR-2.1**: 99.9% system uptime in production deployment  
- **NFR-2.2**: Graceful degradation during partial system failures
- **NFR-2.3**: Automatic recovery from network disconnections
- **NFR-2.4**: Data consistency during concurrent operations
- **NFR-2.5**: No data loss during system restarts

#### NFR-3: Safety
- **NFR-3.1**: All flight commands require explicit user confirmation
- **NFR-3.2**: Command acknowledgment within 5 seconds or timeout alert
- **NFR-3.3**: Prevention of conflicting commands from multiple users
- **NFR-3.4**: Fail-safe behavior during communication loss
- **NFR-3.5**: Audit trail of all safety-critical operations

#### NFR-4: Scalability
- **NFR-4.1**: Horizontal scaling across multiple server instances
- **NFR-4.2**: Load balancing for high-availability deployments
- **NFR-4.3**: Database sharding for telemetry data storage
- **NFR-4.4**: CDN integration for global map tile distribution
- **NFR-4.5**: Microservices architecture for component independence

#### NFR-5: Security
- **NFR-5.1**: Authentication and authorization for web access
- **NFR-5.2**: Encrypted communication channels (HTTPS/WSS)
- **NFR-5.3**: Role-based access control for flight operations
- **NFR-5.4**: Security hardening for production deployments
- **NFR-5.5**: Audit logging for security events

#### NFR-6: Usability
- **NFR-6.1**: Responsive web design for mobile and desktop
- **NFR-6.2**: Intuitive interface requiring minimal training
- **NFR-6.3**: Accessibility compliance (WCAG 2.1 Level AA)
- **NFR-6.4**: Multi-language support for international deployment
- **NFR-6.5**: Keyboard shortcuts for power users

## Technical Architecture

### System Components

#### Core Application Layer
- **Flask-SocketIO Server**: Web application framework with real-time communication
- **MAVLink Connection Manager**: Protocol handling and connection lifecycle
- **Message Processing Engine**: Real-time telemetry and command processing
- **Request Handler System**: Mission and geofence request processing

#### Data Layer
- **In-Memory State Store**: Thread-safe drone state management
- **IndexedDB Cache**: Client-side offline data storage
- **File-based Configuration**: Environment and deployment settings
- **Circular Log Buffers**: High-performance logging system

#### Integration Layer
- **SocketIO Event Handlers**: Real-time web client communication
- **MAVLink Protocol Interface**: Drone communication protocol
- **Map Tile Services**: OpenStreetMap and satellite imagery
- **System Service Integration**: Platform-specific deployment

### Deployment Architecture

#### Ubuntu Desktop Deployment
- systemd service with security hardening
- TCP-based drone connections
- Full development environment support
- Network-accessible web interface

#### Raspberry Pi Field Deployment  
- UART communication with flight controller
- MAVLink router for connection multiplexing
- WiFi hotspot capability for client access
- Headless operation with minimal resources

## Testing Strategy

### Test-Driven Development Protocol

All implementation follows a strict **Test-First** approach where Claude must:
1. **Write the test first** based on the requirement
2. **Run the test and verify it fails** (Red phase)
3. **Implement minimum code to pass** (Green phase) 
4. **Refactor while keeping tests passing** (Refactor phase)
5. **Continue until test passes completely** - No partial implementations allowed

### Virtual Drone Testing Environment

**Primary Test Endpoint:**
- **Address**: `192.168.193.235:5678` (TCP)
- **Protocol**: MAVLink v2.0
- **Usage**: All MAVLink communication tests must use this endpoint
- **Availability**: 24/7 virtual drone simulator

### Test Specifications by Component

#### TS-1: MAVLink Connection Tests

**TS-1.1: Basic Connection Test**
```python
def test_mavlink_connection():
    """Test basic MAVLink connection to virtual drone"""
    # PASS CRITERIA: Connection established within 5 seconds
    # PASS CRITERIA: mavlink_connection_instance is not None  
    # PASS CRITERIA: Connection reports as active
    # FAIL CRITERIA: Any timeout or connection error
```

**TS-1.2: Heartbeat Reception Test**
```python
def test_heartbeat_reception():
    """Test receiving heartbeat messages"""
    # PASS CRITERIA: Receive heartbeat within 10 seconds
    # PASS CRITERIA: drone_state['connected'] == True
    # PASS CRITERIA: System ID and Component ID populated
    # FAIL CRITERIA: No heartbeat received in 10 seconds
```

**TS-1.3: Connection Recovery Test**
```python
def test_connection_recovery():
    """Test automatic reconnection after disconnect"""
    # PASS CRITERIA: Reconnects within 30 seconds after simulated disconnect
    # PASS CRITERIA: drone_state properly reset during disconnection
    # PASS CRITERIA: Telemetry resumes after reconnection
```

#### TS-2: Message Processing Tests

**TS-2.1: Telemetry Processing Test**
```python
def test_telemetry_processing():
    """Test processing of GLOBAL_POSITION_INT messages"""
    # PASS CRITERIA: Position data updates in drone_state within 1 second
    # PASS CRITERIA: Lat/lon values are reasonable (-90 to 90, -180 to 180)
    # PASS CRITERIA: Altitude values are populated
    # PASS CRITERIA: Thread-safe access confirmed
```

**TS-2.2: Command Acknowledgment Test**  
```python
def test_command_acknowledgment():
    """Test MAVLink command acknowledgment processing"""
    # PASS CRITERIA: ACK received within 5 seconds of command
    # PASS CRITERIA: Command result properly interpreted
    # PASS CRITERIA: pending_commands dict updated correctly
    # PASS CRITERIA: User feedback message generated
```

#### TS-3: Web Interface Tests

**TS-3.1: SocketIO Connection Test**
```python
def test_socketio_connection():
    """Test web client SocketIO connection"""
    # PASS CRITERIA: Client connects successfully
    # PASS CRITERIA: Connection event handler executes
    # PASS CRITERIA: Initial telemetry sent to client
    # PASS CRITERIA: Connection logged in webgcs_logger
```

**TS-3.2: Real-time Telemetry Test**
```python
def test_realtime_telemetry():
    """Test 10Hz telemetry updates to web clients"""
    # PASS CRITERIA: Telemetry updates received at 9-11 Hz
    # PASS CRITERIA: Data consistency between updates
    # PASS CRITERIA: No telemetry older than 200ms
    # PASS CRITERIA: All clients receive identical data
```

**TS-3.3: Flight Command Test**
```python
def test_flight_command_execution():
    """Test sending flight commands through web interface"""  
    # PASS CRITERIA: Command sent to virtual drone at 192.168.193.235:5678
    # PASS CRITERIA: ACK received within 5 seconds
    # PASS CRITERIA: Command confirmation sent to web client
    # PASS CRITERIA: Command logged with timestamp
```

#### TS-4: Performance Tests

**TS-4.1: Logging Performance Test**
```python
def test_logging_performance():
    """Test logging system meets <1ms requirement"""
    # PASS CRITERIA: 1000 log entries completed in <1000ms total
    # PASS CRITERIA: No individual log entry takes >1ms
    # PASS CRITERIA: No memory leaks in circular buffer
    # PASS CRITERIA: Thread safety confirmed under load
```

**TS-4.2: Telemetry Latency Test**
```python
def test_telemetry_latency():
    """Test end-to-end telemetry latency <100ms"""
    # PASS CRITERIA: MAVLink message to web client <100ms
    # PASS CRITERIA: Consistent latency over 60 second test
    # PASS CRITERIA: No dropped telemetry updates
    # PASS CRITERIA: Latency measured and logged
```

#### TS-5: Safety Tests

**TS-5.1: Command Confirmation Test**
```python
def test_command_confirmation():
    """Test safety-critical command confirmation"""
    # PASS CRITERIA: ARM command requires explicit confirmation
    # PASS CRITERIA: Timeout if no confirmation in 30 seconds
    # PASS CRITERIA: Command canceled if confirmation denied  
    # PASS CRITERIA: All safety commands logged to audit trail
```

**TS-5.2: Concurrent Command Test**
```python
def test_concurrent_command_prevention():
    """Test prevention of conflicting commands"""
    # PASS CRITERIA: Only one flight command active at a time
    # PASS CRITERIA: Second command queued or rejected appropriately
    # PASS CRITERIA: Clear user feedback on command conflicts
    # PASS CRITERIA: No race conditions in command processing
```

#### TS-6: Integration Tests

**TS-6.1: End-to-End Mission Test**
```python
def test_end_to_end_mission():
    """Test complete mission upload and execution"""
    # PASS CRITERIA: Mission uploaded to virtual drone successfully
    # PASS CRITERIA: Mission execution monitored in real-time
    # PASS CRITERIA: Web interface shows mission progress
    # PASS CRITERIA: Mission completion detected and reported
```

**TS-6.2: Geofence Integration Test**
```python
def test_geofence_integration():
    """Test geofence upload and monitoring"""
    # PASS CRITERIA: Geofence uploaded to virtual drone
    # PASS CRITERIA: Fence status monitored in real-time  
    # PASS CRITERIA: Fence violations detected and reported
    # PASS CRITERIA: Safety actions triggered on violations
```

### Test Execution Protocol

**Test Environment Setup:**
```bash
# Virtual drone connection test
export DRONE_TCP_ADDRESS=192.168.193.235
export DRONE_TCP_PORT=5678
export TEST_MODE=virtual_drone

# Run test suite
uv run pytest tests/ -v --tb=short
```

**Continuous Testing Requirements:**
- **All tests must pass** before any code is considered complete
- **Failed tests trigger immediate debugging** - no moving to next task
- **Performance tests run on every commit** to ensure no regression
- **Integration tests run daily** against virtual drone
- **Safety tests have zero tolerance** - any failure blocks release

**Test Coverage Requirements:**
- **Functional Coverage**: 95% of all functions tested
- **Line Coverage**: 90% of all code lines executed in tests
- **Branch Coverage**: 85% of all conditional branches tested  
- **Safety Coverage**: 100% of safety-critical paths tested

## Technical Implementation Strategy

### Subagent Architecture

The system implements a **coordinated subagent development model** where specialized agents handle different aspects of the system while communicating through a central coordination mechanism.

#### Subagent Definitions

**1. MAVLink Protocol Agent**
- **Scope**: MAVLink communication, message processing, connection management
- **Components**: `mavlink_connection_manager.py`, `mavlink_message_processor.py`, `mavlink_utils.py`
- **Responsibilities**: Protocol compliance, thread safety, real-time message handling

**2. Web Interface Agent**  
- **Scope**: Web server, real-time communication, user interface
- **Components**: `app.py`, `socketio_handlers.py`, `templates/`, `static/`
- **Responsibilities**: Web framework, SocketIO events, client-side functionality

**3. Request Handlers Agent**
- **Scope**: Mission planning, geofencing, data requests
- **Components**: `request_handlers.py`, `get_mission.py`, `get_fence.py`
- **Responsibilities**: Asynchronous request processing, data validation

**4. Infrastructure Agent**
- **Scope**: Configuration, logging, deployment, monitoring
- **Components**: `config.py`, `webgcs_logger.py`, `setup_*.sh`, deployment scripts
- **Responsibilities**: System configuration, performance monitoring, deployment automation

**5. Testing & Quality Agent**
- **Scope**: Test automation, quality assurance, performance validation
- **Components**: `test_*.py`, benchmarking tools, integration tests
- **Responsibilities**: Test coverage, performance validation, quality gates

**6. Coordinator Agent**
- **Scope**: Project coordination, architecture decisions, integration management
- **Components**: Cross-cutting concerns, subagent coordination
- **Responsibilities**: Task delegation, dependency management, progress tracking

#### Coordination Protocol

All subagents communicate through `PROJECT_COORDINATION.md` which serves as:
- **Central TODO System**: Shared task tracking and status updates
- **Inter-Agent Messaging**: Communication channel between specialized agents  
- **Dependency Management**: Cross-component dependency resolution
- **Progress Visibility**: Real-time development status for stakeholders

### Test-Driven Development Phases

#### Phase 1: Foundation (Tests 001-003) - Weeks 1-3
**Gate Criteria: All Phase 1 tests must pass before proceeding**
- **TEST-001**: Basic MAVLink connection to virtual drone (192.168.193.235:5678)
- **TEST-002**: Heartbeat message reception and processing
- **TEST-003**: GLOBAL_POSITION_INT message handling
- **Deliverables**: MAVLink protocol foundation, thread-safe state management

**Claude Implementation Protocol:**
1. Write TEST-001 first (must FAIL initially)
2. Implement minimum `mavlink_connection_manager.py` to pass test
3. Write TEST-002, implement heartbeat processing to pass
4. Write TEST-003, implement message processing to pass
5. Only proceed to Phase 2 when all tests pass consistently

#### Phase 2: Web Interface (Tests 004-006) - Weeks 4-8
**Gate Criteria: All Phase 1 + Phase 2 tests must pass**
- **TEST-004**: Flask-SocketIO server startup and basic endpoints
- **TEST-005**: SocketIO client connection and telemetry reception
- **TEST-006**: Flight command execution through web interface
- **Deliverables**: Real-time web interface, command processing

**Claude Implementation Protocol:**
1. Write TEST-004, implement Flask app to pass
2. Write TEST-005, implement SocketIO handlers to pass
3. Write TEST-006, implement command system to pass
4. Continuous testing against virtual drone endpoint
5. All Phase 1 tests must still pass (regression prevention)

#### Phase 3: Performance & Safety (Tests 007-008) - Weeks 9-12
**Gate Criteria: All previous tests + Performance tests must pass**
- **TEST-007**: Logging system performance (<1ms per entry)
- **TEST-008**: End-to-end telemetry latency (<100ms)
- **Deliverables**: High-performance logging, optimized telemetry pipeline

**Claude Implementation Protocol:**
1. Write TEST-007, optimize webgcs_logger.py to pass
2. Write TEST-008, optimize telemetry path to pass
3. Performance regression testing on every change
4. All safety-critical functions must have 100% test coverage

#### Phase 4: Integration & Safety (Tests 009-010) - Weeks 13-16
**Gate Criteria: All tests including safety tests must pass**
- **TEST-009**: Command confirmation safety mechanisms
- **TEST-010**: Complete end-to-end mission workflow
- **Deliverables**: Production-ready safety systems, full integration

**Claude Implementation Protocol:**
1. Write TEST-009, implement safety confirmation system
2. Write TEST-010, integrate all components for mission workflow
3. Comprehensive integration testing against virtual drone
4. Security hardening and deployment preparation

#### Phase 5: Production Deployment (All Tests) - Weeks 17-20
**Gate Criteria: 100% test pass rate, performance benchmarks met**
- **All 10 core tests** must pass consistently
- **Performance benchmarks** must be met under load
- **Safety tests** must have zero tolerance for failure
- **Deliverables**: Production deployment, documentation, monitoring

**Final Validation Protocol:**
```bash
# All tests must pass before production deployment
uv run pytest tests/ -v --tb=short
# Performance validation
uv run pytest tests/test_007_logging_performance.py -v
uv run pytest tests/test_008_telemetry_latency.py -v
# Safety validation  
uv run pytest tests/test_009_command_safety.py -v
# Integration validation against virtual drone
uv run pytest tests/test_010_integration.py -v --drone-endpoint=192.168.193.235:5678
```

## Risk Management

### Technical Risks
- **MAVLink Protocol Changes**: Mitigation through version compatibility testing
- **Real-time Performance**: Mitigation through performance profiling and optimization
- **Cross-platform Compatibility**: Mitigation through automated testing on target platforms
- **Network Reliability**: Mitigation through robust connection recovery mechanisms

### Safety Risks  
- **Command Acknowledgment Failures**: Mitigation through timeout handling and user alerts
- **Concurrent User Conflicts**: Mitigation through command queuing and user coordination
- **Communication Loss**: Mitigation through fail-safe behaviors and emergency procedures
- **Incorrect Navigation Commands**: Mitigation through input validation and confirmation dialogs

### Operational Risks
- **Deployment Complexity**: Mitigation through automated deployment scripts
- **User Training Requirements**: Mitigation through intuitive interface design and documentation
- **Hardware Compatibility**: Mitigation through extensive testing on target platforms
- **Maintenance Overhead**: Mitigation through centralized logging and monitoring

## Success Criteria

### Technical Success
- All functional requirements implemented and tested
- Performance benchmarks consistently met
- Zero safety-critical bugs in production
- Successful deployment on both target platforms

### Business Success  
- User satisfaction scores >4.5/5.0
- System uptime >99.9% in production
- Adoption by target user communities
- Positive feedback from safety evaluations

### Quality Gates
- 95% code coverage in automated tests
- All security requirements validated
- Performance requirements consistently met
- Cross-platform compatibility verified

## Appendices

### Appendix A: MAVLink Message Support
- Complete list of supported MAVLink message types
- Custom message extensions for specific use cases
- Protocol version compatibility matrix

### Appendix B: Deployment Specifications
- Hardware requirements for each platform
- Network configuration requirements
- Security hardening checklists
- Monitoring and alerting setup

### Appendix C: API Documentation  
- SocketIO event specifications
- REST API endpoint documentation
- Configuration parameter reference
- Integration examples

This PRD serves as the definitive specification for WebGCS development, providing clear requirements, architecture guidance, and success criteria while incorporating the coordinated subagent development model for efficient implementation.
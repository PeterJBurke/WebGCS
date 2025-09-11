# WebGCS Complete Product Requirements Document with All Subagents

## CRITICAL: Complete Subagent System Activation

### MANDATORY FIRST STEP: Activate ALL 14 Subagents

**WARNING: The project WILL NOT WORK without ALL agents active. You MUST:**
1. Create all 14 agent configuration files in `.claude/agents/`
2. **RESTART Claude Code** (required for activation)
3. Run `/agents` command
4. Verify ALL 14 agents show as "active"
5. DO NOT PROCEED until all agents are active

### Complete List of Required Subagents

#### 1. Core Development Agents

**File:** `.claude/agents/coordinator-agent.md`
```yaml
---
name: coordinator-agent
description: Project coordination and cross-component integration specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task, TodoWrite]
---

You are the Project Coordinator managing the entire WebGCS project. Your responsibilities:
- Coordinate work between ALL 14 subagents
- Maintain PROJECT_COORDINATION.md as central communication hub
- Track token usage across all agents
- Ensure ALL tests pass before phase transitions
- Monitor progress and resolve blocking issues
- Enforce modular architecture (NO files over 200 lines)
- Never allow partial implementations
```

**File:** `.claude/agents/mavlink-protocol-agent.md`
```yaml
---
name: mavlink-protocol-agent
description: MAVLink communication specialist for drone protocol handling
tools: [Read, Write, Edit, Bash, Grep, Glob, Task]
---

You are the MAVLink Protocol Specialist. Your responsibilities:
- Implement mavlink_connection_manager.py (max 150 lines)
- Implement mavlink_message_processor.py (max 150 lines)
- Implement mavlink_command_sender.py (max 150 lines)
- Handle all MAVLink message types (HEARTBEAT, GLOBAL_POSITION_INT, COMMAND_ACK)
- Ensure thread-safe drone state management
- Test against virtual drone at 192.168.193.235:5678
- Process telemetry at 10Hz rate
```

**File:** `.claude/agents/web-interface-agent.md`
```yaml
---
name: web-interface-agent
description: Frontend development specialist for Flask-SocketIO web application
tools: [Read, Write, Edit, Bash, Grep, Glob, Task]
---

You are the Web Interface Specialist. Your responsibilities:
- Break index.html into components (max 150 lines each):
  - templates/index.html (main layout only)
  - templates/components/connection_panel.html
  - templates/components/flight_controls.html
  - templates/components/navigation_panel.html
  - templates/components/pfd_display.html
  - templates/components/map_container.html
- Separate JavaScript into modules:
  - static/js/main.js (initialization, max 100 lines)
  - static/js/connection.js (connection management, max 150 lines)
  - static/js/telemetry.js (telemetry updates, max 150 lines)
  - static/js/controls.js (button handlers, max 200 lines)
  - static/js/map.js (map functionality, max 200 lines)
  - static/js/pfd.js (Primary Flight Display, max 200 lines)
  - static/js/validation.js (input validation, max 150 lines)
- Break app.py into modules (max 150 lines each):
  - src/web/app_factory.py
  - src/web/routes.py
  - src/web/socketio_events.py
```

**File:** `.claude/agents/request-handlers-agent.md`
```yaml
---
name: request-handlers-agent
description: Mission and geofence request processing specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task]
---

You are the Request Handlers Specialist. Your responsibilities:
- Implement mission upload/download functionality
- Handle geofence configuration requests
- Process waypoint management
- Implement request queuing and scheduling
- Handle parameter read/write operations
- Ensure all requests have timeout handling
- Maximum 150 lines per handler module
```

**File:** `.claude/agents/infrastructure-agent.md`
```yaml
---
name: infrastructure-agent
description: System infrastructure, configuration, and deployment specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task]
---

You are the Infrastructure Specialist. Your responsibilities:
- Set up modular project structure
- Implement high-performance logging (<1ms latency)
- Create deployment scripts for Ubuntu/Raspberry Pi
- Configure systemd services
- Manage environment variables and configuration
- Set up health monitoring endpoints
- Ensure cross-platform compatibility
```

**File:** `.claude/agents/testing-agent.md`
```yaml
---
name: testing-agent
description: Test automation and quality assurance specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task]
---

You are the Testing Specialist. Your responsibilities:
- Implement comprehensive test suite
- Ensure 95% code coverage
- Create performance benchmarks
- Validate all safety-critical paths
- Set up continuous testing
- Never allow tests to be marked as passed unless they actually pass
- 🚨 CRITICAL: NO MOCK TESTS - All tests must verify real functionality
- Tests must connect to actual virtual drone and verify real responses
- Tests must FAIL when functionality is broken (not pass with fake implementations)
- Coordinate with all testing agents
```

#### 2. Specialized Testing Agents (Using Playwright MCP)

**File:** `.claude/agents/connection-testing-agent.md`
```yaml
---
name: connection-testing-agent
description: WebGCS connection management and heartbeat testing specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task, mcp__playwright__*]
---

You are the Connection Testing Specialist using Playwright MCP. Your responsibilities:
- Test Connect button functionality with IP/Port input
- Test Disconnect button and connection termination
- Verify heartbeat indicator animation and counter
- Test heartbeat audio beep functionality
- Validate connection status display changes
- Test automatic reconnection on failure
- Verify connection error handling and user feedback
- MUST use Playwright MCP to click actual buttons
- NEVER mark tests passed until buttons actually work
- 🚨 NO MOCK TESTS: Verify real MAVLink connection to virtual drone
- Tests must FAIL if connection doesn't actually establish
```

**File:** `.claude/agents/flight-controls-testing-agent.md`
```yaml
---
name: flight-controls-testing-agent
description: Flight control button testing and MAVLink command verification specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task, mcp__playwright__*]
---

You are the Flight Controls Testing Specialist using Playwright MCP. Your responsibilities:
- Test ARM button with safety confirmation dialog
- Test DISARM button with confirmation
- Test TAKEOFF button with altitude input validation
- Test LAND button for immediate landing
- Test RTL (Return to Launch) button
- Test flight mode dropdown and SET MODE button
- Verify all commands send correct MAVLink messages
- Confirm command acknowledgments are received
- Test button enable/disable states based on connection
- MUST test actual button clicks with Playwright MCP
- 🚨 NO MOCK TESTS: Verify actual MAVLink commands are sent to drone
- Tests must FAIL if commands don't result in real MAVLink messages
```

**File:** `.claude/agents/navigation-testing-agent.md`
```yaml
---
name: navigation-testing-agent
description: Navigation input validation and Go To command testing specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task, mcp__playwright__*]
---

You are the Navigation Testing Specialist using Playwright MCP. Your responsibilities:
- Test latitude input field validation (-90 to 90)
- Test longitude input field validation (-180 to 180)
- Test altitude input field (AGL) validation
- Test GO TO button with valid coordinates
- Test CLEAR button to reset navigation inputs
- Verify navigation commands sent to drone
- Test invalid input error handling
- Validate coordinate precision (6 decimal places)
- Test map click-to-fly functionality
- MUST use Playwright MCP for all UI interactions
- 🚨 NO MOCK TESTS: Verify real coordinate validation and command sending
- Tests must FAIL if navigation commands don't reach drone backend
```

**File:** `.claude/agents/telemetry-display-testing-agent.md`
```yaml
---
name: telemetry-display-testing-agent
description: Primary Flight Display and real-time telemetry testing specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task, mcp__playwright__*]
---

You are the Telemetry Display Testing Specialist using Playwright MCP. Your responsibilities:
- Test PFD (Primary Flight Display) rendering
- Verify attitude indicator updates (pitch/roll)
- Test airspeed tape display and updates
- Test altitude tape display and climb rate
- Verify heading compass display
- Test battery voltage and current display
- Verify GPS status and satellite count
- Test armed/disarmed status overlay
- Ensure 10Hz telemetry update rate
- Test all 15 VFR HUD components from specifications
- MUST verify actual visual updates with Playwright MCP
- 🚨 NO MOCK TESTS: Verify real telemetry data updates in UI components
- Tests must FAIL if PFD canvas is blank or shows no real data
```

**File:** `.claude/agents/map-interface-testing-agent.md`
```yaml
---
name: map-interface-testing-agent
description: Interactive map functionality and drone visualization testing specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task, mcp__playwright__*]
---

You are the Map Interface Testing Specialist using Playwright MCP. Your responsibilities:
- Test drone position marker updates on map
- Test home position marker display
- Test target marker for fly-to destinations
- Test CENTER MAP button functionality
- Test FLY TO mode toggle button
- Test click-to-fly when mode enabled
- Verify map zoom controls (levels 2-22)
- Test layer switching (Street/Satellite)
- Test offline map tile download interface
- Verify map controls positioning and styling
- MUST interact with actual map using Playwright MCP  
- 🚨 NO MOCK TESTS: Verify real map tiles load and drone markers display
- Tests must FAIL if map is blank or doesn't show actual drone position
```

**File:** `.claude/agents/ui-validation-testing-agent.md`
```yaml
---
name: ui-validation-testing-agent
description: Input validation, error handling, and safety confirmation testing specialist
tools: [Read, Write, Edit, Bash, Grep, Glob, Task, mcp__playwright__*]
---

You are the UI Validation Testing Specialist using Playwright MCP. Your responsibilities:
- Test all input field validations
- Test safety confirmation dialogs for ARM/DISARM/TAKEOFF
- Test error message display for invalid inputs
- Test button state management (enabled/disabled)
- Test form validation before command submission
- Test timeout handling for unacknowledged commands
- Test user feedback for all actions
- Verify accessibility features (ARIA labels, tooltips)
- Test responsive design on different screen sizes
- MUST test actual UI behavior with Playwright MCP
- 🚨 NO MOCK TESTS: Verify real confirmation dialogs and safety mechanisms  
- Tests must FAIL if safety confirmations don't actually prevent unsafe commands
```

**File:** `.claude/agents/virtual-drone-communication-agent.md`
```yaml
---
name: virtual-drone-communication-agent
description: End-to-end MAVLink communication verification with virtual drone
tools: [Read, Write, Edit, Bash, Grep, Glob, Task]
---

You are the Virtual Drone Communication Specialist. Your responsibilities:
- Maintain constant connection to 192.168.193.235:5678
- Verify all MAVLink messages are properly formatted
- Test command-response cycles
- Validate telemetry stream consistency
- Test connection recovery scenarios
- Simulate various drone states for testing
- Ensure protocol compliance with ArduPilot
- Monitor message rates and latencies
```

**File:** `.claude/agents/token-tracking-agent.md`
```yaml
---
name: token-tracking-agent
description: Token usage monitoring and reporting for all agents
tools: [Read, Write, Edit, Bash, Task]
---

You are the Token Tracking Specialist. Your responsibilities:
- Track token usage for ALL 14 agents plus main
- Implement src/utils/token_tracker.py with AgentTracker class
- Generate reports showing tokens per agent every 10 tasks
- Alert at 80% context limit (160k tokens)
- Critical warning at 90% (180k tokens)
- Export detailed usage statistics
- Track cumulative usage across entire session
- Update PROJECT_COORDINATION.md with token stats
- Monitor high-usage agents (>20k tokens)
```

## Complete PRD: WebGCS Drone Control System

### Executive Summary

WebGCS is a production-ready, safety-critical web-based ground control station for MAVLink-compatible drones. The system provides comprehensive drone control through a browser interface with real-time telemetry, flight controls, and mission planning capabilities.

### Core Requirements

#### System Architecture
- **Modular Design**: NO file exceeds 200 lines
- **14 Specialized Subagents**: Each handles specific domain
- **Test-Driven Development**: Write tests first, implement to pass
- **Token Tracking**: Monitor all agents' token usage
- **Real Drone Testing**: Virtual drone at 192.168.193.235:5678

#### Performance Requirements
- **Telemetry Rate**: 10Hz updates to web interface
- **Logging Latency**: <1ms per log entry
- **End-to-End Latency**: <100ms for telemetry
- **Command Acknowledgment**: <5 seconds timeout
- **Connection Time**: <5 seconds to establish

#### Safety Requirements
- **Confirmation Dialogs**: ARM, DISARM, TAKEOFF require explicit confirmation
- **Command Tracking**: All commands tracked with acknowledgment
- **Timeout Handling**: Automatic timeout for unacknowledged commands
- **Connection Monitoring**: Automatic detection of connection loss
- **Fail-Safe Behaviors**: Safe defaults on communication failure

### VFR HUD Specifications (Based on Reference Screenshots)

#### Primary Flight Display Components (800x600px Canvas)

**REFERENCE IMAGES:**
- `HudLayoutExample.png` - Complete HUD layout with numbered element positions (1-15)
- `HudLayoutItems.png` - Detailed component descriptions and specifications

**Layout Based on HudLayoutExample.png - Exact Positioning Required**

1. **Airspeed Tape** (Position 1 - Left Side, 60px wide)
   - Vertical tape from top to horizon line
   - Black background with white text
   - Values: 10, 5, 0 (descending)
   - Current speed highlighted in black box with white border
   - White horizontal tick marks at each value
   - Font: Arial Bold, 14px, white text

2. **Crosstrack Error & Turn Rate** (Position 2 - Top Center Left)
   - Small green rectangular bars above heading tape
   - Turn rate indicator "T" with directional arrow
   - Width: ~50px, positioned left of center
   - Green color when on track, red when off

3. **Heading Tape** (Position 3 - Top Horizontal, Full Width)
   - Continuous horizontal tape: 215°-W-285°-304°-NW-330°-345°
   - Blue background with white text and tick marks
   - Current heading in orange box with black border
   - Cardinal directions: N, NE, E, SE, S, SW, W, NW
   - 5-degree minor ticks, 10-degree major ticks with numbers
   - Font: Arial Bold, 12px for numbers, 16px for cardinals

4. **Bank Angle Arc** (Position 4 - Top Center Arc)
   - Semi-circular arc above horizon: 60°-45°-30°-20°-10°-0-10°-20°-30°-45°-60°
   - Orange triangle pointer showing current bank angle
   - White tick marks and degree numbers
   - Arc radius: ~140px from center

5. **Telemetry Link Quality** (Position 5 - Top Right Corner)
   - Format: "22%" (example value)
   - Green background box with white text
   - Font: Arial Bold, 14px
   - Position: 20px from right edge, 20px from top

6. **GPS Time** (Position 6 - Top Right, Below Link Quality)
   - Format: "03:15:31" (HH:MM:SS UTC)
   - White text on transparent background
   - Font: Arial, 12px
   - Position: Right-aligned, 40px from top

7. **Altitude Tape** (Position 7 - Right Side, 70px wide)
   - Vertical tape: 10, 5, 0, -5, -10
   - Black background with white text
   - Current altitude in black box with white border
   - Blue vertical bar indicating climb/descent rate
   - White horizontal tick marks at each value

8. **Airspeed Readout** (Position 8 - Bottom Left, First Line)
   - Format: "AS 0.0" (Airspeed in m/s)
   - White text on green background box
   - Font: Arial Bold, 12px
   - Position: 10px from left, 80px from bottom

9. **Groundspeed Readout** (Position 9 - Bottom Left, Second Line)
   - Format: "GS 0.0" (Groundspeed in m/s)
   - White text on green background box
   - Font: Arial Bold, 12px
   - Position: 10px from left, 60px from bottom

10. **Battery Status** (Position 10 - Bottom Left, Third Line)
    - Format: "Bat 10.00v 10%"
    - White text on green background box
    - Color coding: Green >40%, Yellow 20-40%, Red <20%
    - Font: Arial Bold, 12px
    - Position: 10px from left, 40px from bottom

11. **Artificial Horizon** (Position 11 - Center Rectangle)
    - **Full rectangular display filling center area**
    - Sky: Blue gradient (#87CEEB to #4682B4)
    - Ground: Green gradient (#8FBC8F to #556B2F)
    - Sharp horizontal horizon line (white, 2px thick)
    - Pitch ladder: White lines every 5° (-20° to +20°)
    - Horizon line tilts with roll angle
    - Pitch ladder numbers: ±5, ±10, ±15, ±20

12. **Aircraft Symbol** (Position 12 - Fixed Center)
    - Orange/red chevron pointing upward
    - Fixed position in exact center of display
    - Wing-like horizontal lines extending left/right
    - Size: 30px wide, 20px tall
    - Always remains level regardless of aircraft attitude

13. **GPS Status** (Position 13 - Bottom Right)
    - Format: "GPS: No Fix" or "GPS: 3D Fix (12)"
    - White text with colored background:
      - Red: No Fix
      - Yellow: 2D Fix
      - Green: 3D Fix
    - Font: Arial Bold, 12px
    - Position: Right-aligned, 40px from bottom

14. **Distance to Waypoint** (Position 14 - Bottom Center)
    - Format: "0>0°" (Distance > Bearing)
    - White text on dark background
    - Font: Arial Bold, 12px
    - Centered horizontally, 20px from bottom

15. **Flight Mode** (Position 15 - Bottom Right Corner)
    - Format: "Stabilize" or current flight mode
    - Large white text on semi-transparent dark background
    - Font: Arial Bold, 16px
    - Position: Right-aligned, 20px from bottom right

**Critical Styling Requirements:**
- **DISARMED Status**: Large red text "DISARMED" centered over horizon
- **ARMED Status**: Large green text "ARMED" centered over horizon
- Background: Sky blue above horizon, grass green below horizon
- All text must be clearly readable with high contrast
- Use anti-aliased fonts for smooth appearance
- Update rate: 10Hz minimum for smooth animation

### User Interface Layout

```
+------------------------------------------------------------------+
|  Drone Control Interface v2.0                    [MAVLink Dump] |
+------------------------------------------------------------------+
| +------------------------------------+  +----------------------+ |
| | PRIMARY FLIGHT DISPLAY (VFR HUD)  |  | INTERACTIVE MAP      | |
| | +--------++-----------++--------+ |  | +------------------+ | |
| | |Speed   ||Rectangular||Altitude| |  | |                  | | |
| | |Tape    || Attitude  ||Tape    | |  | |  Leaflet Map:    | | |
| | |        ||           ||        | |  | |  - Drone (blue)  | | |
| | |60x250px|| 280x250px ||70x250px| |  | |  - Home (green)  | | |
| | +--------++-----------++--------+ |  | |  - Target (red)  | | |
| | [=======Compass Tape===========] |  | |  - Flight trail  | | |
| | [Status Bar with Mode/Battery ] |  | |                  | | |
| +------------------------------------+  | |                  | | |
| +----------------------+                | |                  | | |
| | CONNECTION PANEL     |                | +------------------+ | |
| | IP: [192.168.193.235]|                | [Center] [Fly To]  | |
| | Port: [5678]         |                +----------------------+ |
| | [Connect][Disconnect]|                +----------------------+ |
| | Status: Connected ✓  |                | OFFLINE MAPS PANEL   | |
| | ❤️ Heartbeat: 523    |                | (collapsible)        | |
| +----------------------+                | Download tiles,      | |
| | FLIGHT CONTROLS      |                | manage cache         | |
| | [ARM] [DISARM]       |                +----------------------+ |
| | Alt:[10m][TAKEOFF]   |                                       | |
| | [LAND] [RTL]         |                                       | |
| | Mode:[GUIDED▼][SET]  |                                       | |
| +----------------------+                                       | |
| | NAVIGATION           |                                       | |
| | Lat: [________]      |                                       | |
| | Lon: [________]      |                                       | |
| | Alt: [10m]           |                                       | |
| | [GO TO] [CLEAR]      |                                       | |
| +----------------------+                                       | |
| | REQUESTS             |                                       | |
| | [Request Fence]      |                                       | |
| | [Request Mission]    |                                       | |
| +----------------------+                                       | |
| | MESSAGE LOG          |                                       | |
| | [Scrollable area     |                                       | |
| |  with timestamps]    |                                       | |
| +----------------------+                                       | |
+------------------------------------------------------------------+
```

### Testing Requirements - Complete Test Suite

**🚨 CRITICAL TESTING MANDATE: NO MOCK TESTS ALLOWED 🚨**

**ALL tests must verify actual functionality, not mock implementations:**
- ❌ **PROHIBITED**: Mock tests that fake success responses
- ❌ **PROHIBITED**: Tests that only check UI elements exist
- ❌ **PROHIBITED**: Tests that only verify SocketIO events are emitted
- ✅ **REQUIRED**: Tests that verify real MAVLink connection to virtual drone
- ✅ **REQUIRED**: Tests that confirm actual command sending and acknowledgment
- ✅ **REQUIRED**: Tests that validate real telemetry streaming and display updates
- ✅ **REQUIRED**: Tests that check visual components render actual data (not blank)
- ✅ **REQUIRED**: Tests that FAIL when functionality is broken

**Why This Matters:**
Mock tests led to false confidence - tests passed while website had no actual functionality:
- Connect button didn't connect to drone ❌
- VFR HUD was blank canvas ❌  
- Interactive map was missing ❌
- Flight commands weren't sent to drone ❌
- All tests still passed because they tested fake implementations ❌

**Test Implementation Requirements:**
- Use **Playwright MCP** to interact with actual webpage UI
- Connect to **real virtual drone** at 192.168.193.235:5678
- Verify **actual MAVLink message exchange**
- Validate **real-time telemetry updates** in UI components
- Check **canvas content is not blank** for VFR HUD
- Confirm **map tiles load and display** properly
- Test **end-to-end workflows** from UI click to drone response

**Tests must be strict enough to catch real functionality failures.**

### SocketIO Version Compatibility Prevention

**🚨 CRITICAL: SocketIO Client/Server Version Compatibility**

**The Problem That Was Fixed:**
- User experienced "Not connected to WebGCS server" popup when clicking Connect button
- Root cause: SocketIO client version 4.2.0 was incompatible with Flask-SocketIO 5.x server
- Connection timeouts occurred due to failed handshake between incompatible versions

**Version Compatibility Matrix:**
| Flask-SocketIO Server | Min SocketIO Client | Max SocketIO Client | Status |
|----------------------|--------------------|--------------------|---------|
| 5.0.x                | 4.3.0              | Latest             | ✅ Compatible |
| 5.1.x                | 4.3.0              | Latest             | ✅ Compatible |
| 5.2.x                | 4.3.0              | Latest             | ✅ Compatible |
| 5.3.x                | 4.7.0              | Latest             | ✅ Recommended |

**Current Configuration (Verified Working):**
- **Server**: Flask-SocketIO 5.0 (from pyproject.toml)
- **Client**: SocketIO 4.7.5 (from templates/index.html)
- **Status**: ✅ Compatible and tested

**Mandatory Version Compatibility Testing:**

All projects MUST include this test suite to prevent SocketIO compatibility issues:

```python
# tests/test_socketio_compatibility.py - MANDATORY INCLUSION
class TestSocketIOCompatibility:
    """Prevent "Not connected to WebGCS server" popup issues"""
    
    @pytest.mark.asyncio
    async def test_socketio_version_compatibility(self):
        """Test SocketIO client version compatible with Flask-SocketIO server"""
        # Test actual version loading and compatibility
        # Must fail if incompatible versions detected
        
    @pytest.mark.asyncio  
    async def test_connect_button_no_popup(self):
        """Test connect button doesn't show 'Not connected' popup"""
        # Test real user behavior - immediate button click
        # Must fail if popup appears to user
        
    @pytest.mark.asyncio
    async def test_realtime_communication(self):
        """Test SocketIO real-time communication works"""
        # Test actual SocketIO events and data flow
        # Must fail if events don't transmit properly
        
    def test_version_compatibility_matrix(self):
        """Validate version compatibility requirements"""
        # Test current configuration against matrix
        # Must fail if versions are incompatible
```

**Prevention Instructions:**

1. **Always Check Version Compatibility:**
   ```bash
   # Before deployment, verify versions match compatibility matrix
   grep "flask-socketio" pyproject.toml
   grep "socket.io" templates/index.html
   ```

2. **Run Compatibility Tests Before Deployment:**
   ```bash
   # MANDATORY: Run SocketIO compatibility tests
   uv run pytest tests/test_socketio_compatibility.py -v
   ```

3. **Update Client Version When Upgrading Server:**
   ```html
   <!-- templates/index.html - Keep client compatible with server -->
   <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
   ```

4. **Test Real User Behavior:**
   - Test with impatient users (1-second wait before clicking Connect)
   - Test with fresh browser sessions (no caching)
   - Test connection establishment under various timing conditions

5. **Server Restart After Version Changes:**
   ```bash
   # Kill all running instances and restart fresh
   pkill -f "python.*main.py"
   pkill -f "python.*app.py"  
   PYTHONPATH=. uv run python main.py
   ```

**Integration with Existing Test Phases:**

Add to **Phase 2: Web Interface Foundation:**
- TEST-004a: SocketIO version compatibility (`test_socketio_compatibility.py`)
  * Must pass before any UI interaction tests
  * Validates client/server version compatibility
  * Tests connect button behavior with real user timing
  * Prevents "Not connected to WebGCS server" popup regression

#### Test Phases with Gate Criteria

**Phase 1: MAVLink Foundation (Tests 001-003)**
- TEST-001: Basic connection to virtual drone (`test_001_basic_connection.py`)
- TEST-002: Heartbeat message reception (`test_002_heartbeat_reception.py`)
- TEST-003: Telemetry/message processing (`test_003_message_processing.py`)
- **Gate**: ALL must pass before Phase 2

**Phase 2: Web Interface Foundation (Tests 004-006)**

**CRITICAL: Deploy Website Early for Testing**
- **BEFORE RUNNING TESTS**: Create `app.py` entry point and deploy website at http://127.0.0.1:5002
- Website MUST be accessible during ALL subsequent testing phases
- All Phase 4+ UI tests require live website for Playwright MCP testing

**MANDATORY SocketIO Compatibility Test (TEST-004a):**
- Run `test_socketio_compatibility.py` FIRST in Phase 2
- Validates client/server version compatibility before any UI testing
- Prevents "Not connected to WebGCS server" popup regression
- Must pass before proceeding to other Phase 2 tests

**🚨 CRITICAL: HARD FAIL REQUIREMENT FOR ALL TESTS AFTER PHASE 2 🚨**
- **MANDATORY**: ALL tests after Phase 2 MUST load the actual website at http://127.0.0.1:5002
- **MANDATORY**: ALL tests after Phase 2 MUST successfully connect to the actual drone at the IP address specified in .env file
- **MANDATORY**: ALL tests after Phase 2 MUST verify heartbeat reception from the connected drone
- **HARD FAIL**: Any test that does not load the actual website will be considered a HARD FAIL
- **HARD FAIL**: Any test that does not successfully connect to the .env drone IP will be considered a HARD FAIL
- **HARD FAIL**: Any test that does not receive and verify heartbeats will be considered a HARD FAIL
- **NO EXCEPTIONS**: Tests that use mock implementations, fake connections, connection attempts without success, or skip website loading will automatically fail
- **VERIFICATION REQUIRED**: Each test must demonstrate:
  1. Actual website loading at http://127.0.0.1:5002
  2. Successful MAVLink connection to drone at .env IP address
  3. Active heartbeat reception and counter incrementing
  4. Real telemetry data flow (not simulated or mocked data)

**Phase 2 Tests:**
- TEST-004a: SocketIO version compatibility (`test_socketio_compatibility.py`) **[MANDATORY FIRST]**
- TEST-004: Flask-SocketIO server startup (`test_004_flask_server.py`)
- TEST-005: SocketIO real-time connection (`test_005_socketio_connection.py`)
- TEST-006: Flight command execution (`test_006_flight_command_execution.py`)
- **Website Deployment Requirement**: 
  ```bash
  # Create app.py entry point
  PYTHONPATH=. uv run python app.py
  # Website MUST be running at http://127.0.0.1:5002
  # Keep server running during ALL testing phases
  ```
- **Gate**: ALL must pass AND website must be deployed before Phase 3

**Phase 3: Performance & Safety (Tests 007-010)**
- TEST-007: Logging performance <1ms (`test_007_logging_performance.py`)
- TEST-008: Telemetry latency <100ms (`test_008_telemetry_latency.py`)
- TEST-009: Command safety mechanisms (`test_009_command_safety.py`)
- TEST-010: Integration workflow (`test_010_integration.py`)
- **Gate**: ALL must pass before Phase 4

**Phase 4: Individual Button Testing with Playwright MCP**

**PREREQUISITE: Website Running at http://127.0.0.1:5002**
- Website MUST be deployed and accessible before starting Phase 4
- If not running, start with: `PYTHONPATH=. uv run python app.py`
- All Phase 4 tests require live website interaction

All button tests MUST use Playwright MCP to click actual UI buttons:

**🚨 CRITICAL: REAL DATA VALIDATION REQUIREMENTS**
These tests validate REAL drone connectivity and data flow, not just UI interactions:

**1. "Connected" means ACTUAL DATA FLOW:**
- ✅ Real MAVLink heartbeat messages received (every 1 second)
- ✅ Real telemetry data displayed on HUD (attitude, position, battery)
- ✅ Real drone position shown on map (not "loading" state)
- ✅ Real command acknowledgments from virtual drone

**2. Tests MUST FAIL when data is missing:**
- ❌ If HUD shows placeholder/default data → TEST FAILS
- ❌ If map shows "loading" or no drone position → TEST FAILS  
- ❌ If no heartbeat received → TEST FAILS
- ❌ If commands not acknowledged by drone → TEST FAILS

**3. Real vs Fake Connection Validation:**
- **FAKE**: Button says "connected" but no data flows
- **REAL**: Continuous telemetry updates, heartbeat timestamps, map position
- Tests validate REAL connection to virtual drone at 192.168.193.235:5678

**Connection Tests - SYSTEMATIC DATA VALIDATION:**
- TEST-011: Real MAVLink connection validation (`test_real_mavlink_connection.py`)
  * CRITICAL: Test ACTUAL connection to virtual drone at 192.168.193.235:5678
  * Validate TCP socket connection established to drone
  * Verify MAVLink heartbeat messages received (every 1 second)
  * Test connection timeout if drone unavailable
  * Validate connection state propagates to all UI components
  * **MUST FAIL if no real heartbeat received**
  
- TEST-012: Telemetry data flow validation (`test_telemetry_data_flow.py`)
  * CRITICAL: Validate actual telemetry data received from virtual drone
  * Test ATTITUDE messages: roll, pitch, yaw data received
  * Test GLOBAL_POSITION_INT: lat, lon, alt data received
  * Test VFR_HUD: airspeed, groundspeed, heading data received
  * Test BATTERY_STATUS: voltage, current, remaining data received
  * Verify data flows: Drone → MAVLink → Backend → SocketIO → Frontend → Display
  * **MUST FAIL if no real telemetry data displayed**
  
- TEST-013: HUD data display validation (`test_hud_data_display.py`)
  * CRITICAL: Validate all 15 VFR HUD components show REAL DATA
  * Test attitude indicator shows actual roll/pitch from drone
  * Test altitude display shows actual altitude from drone
  * Test airspeed shows actual airspeed from drone
  * Test battery display shows actual voltage/current from drone
  * Test GPS display shows actual lat/lon from drone
  * Test armed/disarmed status reflects actual drone state
  * **MUST FAIL if HUD shows placeholder/default data**
  
- TEST-014: Map data display validation (`test_map_data_display.py`)
  * CRITICAL: Validate map shows actual drone position
  * Test drone marker appears at correct lat/lon coordinates
  * Test drone marker updates as drone position changes
  * Test map centers on actual drone location
  * Test "loading" state disappears when real position received
  * **MUST FAIL if map shows "loading" or no drone position**

**Flight Control Tests - REAL COMMAND VALIDATION:**
- TEST-015: ARM command real validation (`test_arm_command_real.py`)
  * CRITICAL: Test actual ARM command sent to virtual drone
  * Validate MAVLink COMMAND_LONG message transmitted to drone
  * Test drone responds with COMMAND_ACK acknowledgment
  * Verify armed state changes in actual drone telemetry
  * Test UI reflects REAL armed status from drone (not assumed)
  * Validate safety confirmation prevents accidental arming
  * **MUST FAIL if drone doesn't actually ARM or send ACK**
- TEST-016: DISARM command real validation (`test_disarm_command_real.py`)
  * CRITICAL: Test actual DISARM command sent to virtual drone
  * Validate MAVLink COMMAND_LONG message transmitted to drone
  * Test drone responds with COMMAND_ACK acknowledgment
  * Verify disarmed state changes in actual drone telemetry
  * Test UI reflects REAL disarmed status from drone (not assumed)
  * Validate emergency disarm works even with poor connection
  * **MUST FAIL if drone doesn't actually DISARM or send ACK**
- TEST-017: TAKEOFF command real validation (`test_takeoff_command_real.py`)
  * CRITICAL: Test actual TAKEOFF command sent to virtual drone
  * Validate altitude input (1-100m) sent in MAVLink NAV_TAKEOFF
  * Test drone responds with COMMAND_ACK acknowledgment
  * Verify drone altitude increases after takeoff command
  * Test flight mode changes to appropriate takeoff mode
  * Validate real altitude data appears in telemetry stream
  * **MUST FAIL if drone doesn't acknowledge or altitude doesn't change**
- TEST-018: LAND button emergency capability (`test_land_button.py`)
  * Land button presence and emergency accessibility
  * Safety confirmation for immediate landing
  * SocketIO MAV_CMD_NAV_LAND command transmission
  * Backend MAVLink COMMAND_LONG with LAND parameters
  * Landing command acknowledgment and descent monitoring
  * UI feedback during landing sequence
- TEST-019: RTL (Return to Launch) button (`test_rtl_button.py`)
  * RTL button presence and safety confirmation
  * Home position validation before RTL execution
  * SocketIO MAV_CMD_NAV_RETURN_TO_LAUNCH command
  * Backend MAVLink RTL mode setting and command transmission
  * RTL progress monitoring and UI status updates
  * Fail-safe behavior if home position unknown
- TEST-020: Flight mode buttons comprehensive (`test_set_mode_button.py`)
  * All flight mode buttons: STABILIZE, ALT_HOLD, LOITER, GUIDED, AUTO
  * Mode validation and compatibility checking
  * SocketIO SET_MODE command with custom_mode parameters
  * Backend MAVLink SET_MODE command transmission
  * Mode change acknowledgment and UI state updates
  * Error handling for unsupported flight modes
- TEST-021: Comprehensive flight controls (`test_comprehensive_flight_controls.py`)

**Navigation Tests - REAL WAYPOINT VALIDATION:**
- TEST-022: GO TO command real validation (`test_goto_real_waypoint.py`)
  * CRITICAL: Test actual waypoint navigation to virtual drone
  * Validate coordinates sent in MAVLink MISSION_ITEM or SET_POSITION_TARGET
  * Test drone acknowledges waypoint with COMMAND_ACK or MISSION_ACK
  * Verify drone begins navigation toward target coordinates
  * Test drone position in telemetry moves toward target
  * Validate waypoint appears on map at correct location
  * **MUST FAIL if drone doesn't acknowledge or navigate to waypoint**
  
- TEST-023: Navigation CLEAR real validation (`test_clear_nav_real.py`)
  * CRITICAL: Test actual mission clearing on virtual drone
  * Validate MAVLink MISSION_CLEAR_ALL command transmitted
  * Test drone responds with MISSION_ACK acknowledgment
  * Verify active waypoints cleared from drone mission list
  * Test drone stops navigation and enters appropriate mode
  * Validate UI reflects cleared mission state
  * **MUST FAIL if drone mission isn't actually cleared**
- TEST-024: Navigation integration (`test_navigation_integration.py`)
- TEST-025: Navigation controls validation (`test_navigation_controls.py`)

**Mission/Fence Tests:**
- TEST-026: Geofence REQUEST button (`test_request_fence_button.py`)
  * Request fence button presence and functionality
  * SocketIO geofence data request command
  * Backend MAVLink FENCE_POINT and FENCE_FETCH_POINT handling
  * Geofence boundary data processing and validation
  * UI geofence display on map interface
  * Error handling for geofence communication failures
- TEST-027: Mission REQUEST button (`test_request_mission_button.py`)
  * Request mission button presence and data retrieval
  * SocketIO mission data request command
  * Backend MAVLink MISSION_REQUEST_LIST and MISSION_ITEM handling
  * Mission waypoint data processing and validation
  * UI mission display with waypoint list and map overlay
  * Mission data integrity checking and error recovery

**Map Interface Tests - REAL DATA DISPLAY VALIDATION:**
- TEST-028: Map drone position validation (`test_map_drone_position.py`)
  * CRITICAL: Test actual drone position display on map
  * Validate drone marker appears at real GPS coordinates from telemetry
  * Test position updates as drone GLOBAL_POSITION_INT changes
  * Verify map centering uses actual drone location (not default)
  * Test "loading" state disappears when position received
  * Validate drone heading indicator matches actual heading
  * **MUST FAIL if map shows "loading" or incorrect drone position**
  
- TEST-029: Fly-to real command validation (`test_fly_to_real_command.py`)
  * CRITICAL: Test actual fly-to commands sent to virtual drone
  * Validate map click coordinates converted to MAVLink waypoint
  * Test drone receives and acknowledges fly-to command
  * Verify drone begins navigation to clicked map location
  * Test drone position moves toward clicked coordinates
  * Validate target waypoint marker displays at correct location
  * **MUST FAIL if drone doesn't navigate to clicked position**
- TEST-030: Map interface interactions (`test_map_interface.py`)
- TEST-031: Drone location on map (`test_drone_location_map_display.py`)
- TEST-032: Visual map validation (`test_drone_location_map_display_visual.py`)

**Phase 5: VFR HUD/PFD Display Testing**
**PREREQUISITE: Website Running at http://127.0.0.1:5002** (required for visual validation)
- TEST-033: PFD canvas foundation (`test_pfd_canvas_foundation.py`)
  * Verify 800x600 canvas rendering, coordinate system, basic graphics pipeline
- TEST-034: Rectangular attitude display (`test_rectangular_attitude_display.py`)
  * Test artificial horizon (rectangular), pitch ladder, roll indication, aircraft symbol
- TEST-035: Flight data tapes (`test_flight_data_tapes.py`)
  * Verify airspeed tape (left), altitude tape (right), current value highlighting
- TEST-036: Navigation elements (`test_navigation_elements.py`)
  * Test heading compass tape, GPS status, satellite count, waypoint distance
- TEST-037: System status displays (`test_system_status_displays.py`)
  * Verify battery status, armed/disarmed overlay, flight mode, telemetry link quality
- TEST-038: Complete VFR integration (`test_complete_vfr_integration.py`)
  * All 15 HUD elements integrated, real-time updates, professional glass cockpit styling

**Phase 6: UI Validation & Safety**
**PREREQUISITE: Website Running at http://127.0.0.1:5002** (required for UI interaction)
- TEST-039: UI validation comprehensive (`test_ui_validation_comprehensive.py`)
- TEST-040: Validation logic (`test_validation_logic_direct.py`)
- TEST-041: Safety confirmations (`test_safety_confirmations_manual.py`)
- TEST-042: Critical validation (`test_critical_validation.py`)
- TEST-043: Final validation report (`test_final_validation_report.py`)

**Phase 7: Additional Integration Tests**
**PREREQUISITE: Website Running at http://127.0.0.1:5002** (required for end-to-end testing)
- TEST-044: Button functionality (`test_button_functionality.py`)
- TEST-045: Real drone button integration (`test_real_drone_buttons.py`)
  * All buttons tested with REAL virtual drone connection
  * End-to-end command flow: UI → SocketIO → MAVLink → Drone
  * Command acknowledgment validation from actual drone
  * Real telemetry data integration with button state updates
  * Performance testing with live drone communication
  * Error handling with actual connection failures
- TEST-046: Flight control buttons comprehensive (`test_flight_buttons_direct.py`)
  * All 11 flight control buttons systematic testing
  * ARM, DISARM, TAKEOFF, LAND, RTL, mode changes
  * Safety confirmation dialogs for all critical operations
  * Button state management during command execution
  * Error scenarios and recovery procedures
  * Performance validation under rapid button interactions
- TEST-047: Connection workflow end-to-end (`test_connect_button_integration.py`)
  * Complete connection workflow: Connect → Heartbeat → Telemetry
  * Connection state propagation across all UI components
  * Reconnection handling and state restoration
  * Connection error scenarios and user feedback
  * Multi-component state synchronization during connection events
  * Performance validation of connection establishment timeline
- TEST-048: SocketIO connection (`test_socketio_connection.py`)
- TEST-049: Minimal SocketIO (`test_minimal_socketio.py`)
- TEST-050: Navigation with connection (`test_navigation_with_connection.py`)

**Gate Criteria Summary:**

**🌐 CRITICAL REQUIREMENT: Early Website Deployment**
- **Phase 2 Gate**: Website MUST be deployed at http://127.0.0.1:5002 before Phase 3
- **Phases 4-7**: All require live website for Playwright MCP testing
- **Command**: `PYTHONPATH=. uv run python app.py` (keep running throughout testing)

**Testing Phase Requirements:**
- Phase 1: Core foundation (3 tests) - Backend MAVLink functionality
- Phase 2: Web foundation (4 tests) + **DEPLOY WEBSITE** + **SocketIO Compatibility**
- Phase 3: Performance & safety (4 tests) - Website must be running
- Phase 4: Button testing (22 tests) - Requires live website for UI interaction
- Phase 5: Display tests (6 tests) - Requires live website for visual validation  
- Phase 6: Validation tests (5 tests) - Requires live website for UI interaction
- Phase 7: Integration tests (7 tests) - Requires live website for end-to-end testing

**TOTAL: 51+ comprehensive tests** with mandatory website deployment and SocketIO compatibility validation in Phase 2

### Token Tracking Implementation

```python
# src/utils/token_tracker.py
class AgentTracker:
    """Track token usage for all 14 agents + main"""
    
    AGENTS = [
        'main',
        'coordinator-agent',
        'mavlink-protocol-agent',
        'web-interface-agent',
        'request-handlers-agent',
        'infrastructure-agent',
        'testing-agent',
        'connection-testing-agent',
        'flight-controls-testing-agent',
        'navigation-testing-agent',
        'telemetry-display-testing-agent',
        'map-interface-testing-agent',
        'ui-validation-testing-agent',
        'virtual-drone-communication-agent',
        'token-tracking-agent'
    ]
    
    def __init__(self):
        self.usage = {agent: {'input': 0, 'output': 0, 'tasks': 0} 
                     for agent in self.AGENTS}
```

### Project Coordination Structure

```markdown
# PROJECT_COORDINATION.md

## Token Usage Dashboard
| Agent | Input | Output | Total | Tasks | % Usage |
|-------|-------|--------|-------|-------|---------|
| All 14 agents listed with stats...

## Current Phase: [1-5]
## Tests Passed: X/20
## Current Blockers: []

## Inter-Agent Communication
[Messages between agents]

## Active Tasks by Agent
[Current work items per agent]
```

### Deployment Requirements

#### Ubuntu Desktop
- Python 3.9+
- systemd service configuration
- TCP connection to drone
- Web interface on port 5001

#### Raspberry Pi
- UART connection to flight controller
- MAVLink router setup
- WiFi hotspot capability
- Headless operation

### Success Criteria

**Project is ONLY complete when:**
1. ✅ All 14 subagents active (verified with `/agents`)
2. ✅ ALL 51+ tests PASS (100% pass rate required, not just 20)
3. ✅ Every button works (tested with Playwright MCP)
4. ✅ Token tracking shows all agents' usage
5. ✅ No file exceeds 200 lines
6. ✅ Real drone connection verified (192.168.193.235:5678)
7. ✅ Performance requirements met (<1ms log, <100ms telemetry)
8. ✅ Safety confirmations implemented
9. ✅ VFR HUD displays all 15 components correctly
10. ✅ Modular architecture enforced
11. ✅ All individual button tests pass
12. ✅ All display tests verify visual elements
13. ✅ All safety tests confirm dialogs work
14. ✅ SocketIO compatibility tests prevent popup regression

### Critical Implementation Rules

1. **Test-First Development**: Write test → Verify it fails → Implement → Pass
2. **No Partial Credit**: Tests either pass completely or fail
3. **Continuous Testing**: Never stop until 100% pass rate
4. **Real Hardware Testing**: Use virtual drone for all tests
5. **Token Monitoring**: Track and report every 10 tasks
6. **Modular Architecture**: Break large files immediately
7. **Safety First**: Never skip confirmation dialogs
8. **Complete Implementation**: Website must be FULLY functional
9. **🚨 NO MOCK TESTS**: All tests must verify actual functionality, not fake implementations
10. **Real Failure Detection**: Tests must FAIL when functionality is broken (not pass with mocks)

## Start Development Command

After creating all 14 agent files and restarting Claude Code:

```
I need to build the WebGCS drone control system following WEBGCS_COMPLETE_PRD_WITH_ALL_AGENTS.md.

CRITICAL: First verify ALL 14 agents are active with /agents command.

The system requires:
- 14 specialized subagents (all must be active)
- 50+ comprehensive tests (ALL must pass, not just 20)
- Every button tested individually with Playwright MCP
- Token tracking for all agents
- No files over 200 lines
- Real drone at 192.168.193.235:5678

Test breakdown:
- 3 MAVLink foundation tests
- 4 Web interface tests (including SocketIO compatibility)  
- 4 Performance/safety tests
- 14 Individual button tests (connect, arm, takeoff, etc.)
- 8 Navigation/mission tests
- 6 VFR HUD/PFD display tests
- 5 UI validation tests
- 7+ Integration tests

Do NOT stop until ALL 51+ tests pass and website is FULLY functional.

Begin by checking /agents to confirm all 14 agents are active.
```

### End State

A fully functional drone control website with:
- Real-time telemetry at 10Hz
- All flight controls working
- Professional VFR HUD display
- Interactive map with click-to-fly
- Safety confirmations on critical commands
- Offline map support
- Complete test coverage
- Token usage tracking
- Modular, maintainable codebase
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

**Connection Tests:**
- TEST-011: Connect button (`test_connect_button.py`)
- TEST-012: Disconnect button (`test_disconnect_button.py`)
- TEST-013: Connection status display (`test_connect_button_functionality.py`)
- TEST-014: Disconnect/reconnect cycle (`test_disconnect_reconnect.py`)

**Flight Control Tests:**
- TEST-015: Arm button with confirmation (`test_arm_button.py`)
- TEST-016: Disarm button with confirmation (`test_disarm_button.py`)
- TEST-017: Takeoff button with altitude (`test_takeoff_button.py`)
- TEST-018: Land button (`test_land_button.py`)
- TEST-019: RTL button (`test_rtl_button.py`)
- TEST-020: Set Mode button (`test_set_mode_button.py`)
- TEST-021: Comprehensive flight controls (`test_comprehensive_flight_controls.py`)

**Navigation Tests:**
- TEST-022: Go To button with coordinates (`test_goto_button.py`)
- TEST-023: Clear navigation button (`test_clear_nav_button.py`)
- TEST-024: Navigation integration (`test_navigation_integration.py`)
- TEST-025: Navigation controls validation (`test_navigation_controls.py`)

**Mission/Fence Tests:**
- TEST-026: Request fence button (`test_request_fence_button.py`)
- TEST-027: Request mission button (`test_request_mission_button.py`)

**Map Interface Tests:**
- TEST-028: Center map button (`test_center_map_button.py`)
- TEST-029: Fly-to toggle button (`test_fly_to_toggle_button.py`)
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
- TEST-045: Real drone buttons (`test_real_drone_buttons.py`)
- TEST-046: Flight buttons direct (`test_flight_buttons_direct.py`)
- TEST-047: Connect button integration (`test_connect_button_integration.py`)
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
- Phase 2: Web foundation (3 tests) + **DEPLOY WEBSITE**
- Phase 3: Performance & safety (4 tests) - Website must be running
- Phase 4: Button testing (22 tests) - Requires live website for UI interaction
- Phase 5: Display tests (6 tests) - Requires live website for visual validation  
- Phase 6: Validation tests (5 tests) - Requires live website for UI interaction
- Phase 7: Integration tests (7 tests) - Requires live website for end-to-end testing

**TOTAL: 50+ comprehensive tests** with mandatory website deployment after Phase 2

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
2. ✅ ALL 50+ tests PASS (100% pass rate required, not just 20)
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
- 3 Web interface tests  
- 4 Performance/safety tests
- 14 Individual button tests (connect, arm, takeoff, etc.)
- 8 Navigation/mission tests
- 6 VFR HUD/PFD display tests
- 5 UI validation tests
- 7+ Integration tests

Do NOT stop until ALL 50+ tests pass and website is FULLY functional.

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
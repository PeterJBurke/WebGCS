# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WebGCS is a production-ready, safety-critical web-based ground control station for MAVLink-compatible drones. The system provides comprehensive drone control through a browser interface with real-time telemetry, flight controls, mission planning, and professional VFR HUD display.

## Development Environment

**Python Operations:**
- Use `uv` instead of `python` for all Python operations  
- Run Python scripts: `uv run python script.py`
- Install packages: `uv add package_name`
- Run tests: `uv run pytest`

**Testing:**
- Use Playwright MCP for all UI testing
- Test against virtual drone at 192.168.193.235:5678
- ALL tests must pass before phase transitions
- 50+ comprehensive tests across 7 phases

## Architecture Requirements

**Modular Design Principles:**
- NO file exceeds 200 lines maximum
- Break large files into focused modules immediately
- Each component handles single responsibility

**Specialized Agents:**
System uses 14 specialized subagents (verify with `/agents` command):
- coordinator-agent: Project coordination and integration
- mavlink-protocol-agent: MAVLink communication handling
- web-interface-agent: Frontend development (must break into modules)
- request-handlers-agent: Mission/geofence processing
- infrastructure-agent: System configuration and deployment
- testing-agent: Test coordination
- connection-testing-agent: Connect/disconnect button testing
- flight-controls-testing-agent: ARM/DISARM/TAKEOFF button testing
- navigation-testing-agent: Navigation input and Go To testing
- telemetry-display-testing-agent: PFD and telemetry display testing
- map-interface-testing-agent: Interactive map functionality testing
- ui-validation-testing-agent: Input validation and safety confirmation testing
- virtual-drone-communication-agent: Drone communication verification
- token-tracking-agent: Usage monitoring for all agents

## Key System Components

**MAVLink Communication:**
- Connection to drone at 192.168.193.235:5678
- Heartbeat monitoring with visual indicator
- Command acknowledgment tracking (<5s timeout)
- Telemetry processing at 10Hz rate

**Web Interface Structure:**
```
templates/
├── index.html (main layout only, <150 lines)
└── components/
    ├── connection_panel.html
    ├── flight_controls.html
    ├── navigation_panel.html
    ├── pfd_display.html
    └── map_container.html

static/js/
├── main.js (initialization, <100 lines)
├── connection.js (connection management, <150 lines)
├── telemetry.js (telemetry updates, <150 lines)
├── controls.js (button handlers, <200 lines)
├── map.js (map functionality, <200 lines)
├── pfd.js (Primary Flight Display, <200 lines)
└── validation.js (input validation, <150 lines)

src/web/
├── app_factory.py (<150 lines)
├── routes.py (<150 lines)
└── socketio_events.py (<150 lines)
```

**VFR HUD Components (15 required elements):**
- Airspeed indicator (vertical tape, left)
- Crosstrack error & turn rate (top center)
- Heading compass (360-degree tape)
- Bank angle indicator (arc, ±60°)
- Telemetry link quality (top right)
- GPS time display (UTC)
- Altitude tape (vertical, right)
- Artificial horizon (center)
- Aircraft reference symbol
- Armed/disarmed status overlay
- Battery status with color coding
- GPS fix status and satellite count
- Distance to waypoint
- Flight mode display
- Airspeed/groundspeed readouts

## Performance Requirements

**Critical Metrics:**
- Telemetry updates: 10Hz to web interface
- Logging latency: <1ms per entry
- End-to-end latency: <100ms for telemetry
- Command acknowledgment: <5s timeout
- Connection establishment: <5s

## Safety Requirements

**Mandatory Confirmations:**
- ARM command requires explicit confirmation dialog
- DISARM command requires confirmation
- TAKEOFF command requires altitude validation and confirmation
- All safety-critical commands must show confirmation dialogs

**Input Validation:**
- Latitude: -90 to 90 degrees
- Longitude: -180 to 180 degrees  
- Altitude: positive values only (AGL)
- Coordinate precision: 6 decimal places

## Testing Strategy

**Test Phases (50+ tests total):**
1. MAVLink Foundation (3 tests): Connection, heartbeat, message processing
2. Web Interface Foundation (3 tests): Flask server, SocketIO, flight commands
3. Performance & Safety (4 tests): Logging, latency, safety, integration
4. Individual Button Testing (22 tests): Every button tested with Playwright MCP
5. VFR HUD/PFD Display (6 tests): All visual components validated
6. UI Validation & Safety (5 tests): Confirmations and input validation
7. Integration Tests (7+ tests): End-to-end workflows

**Testing Tools:**
- Playwright MCP for all UI interactions (clicking actual buttons)
- Virtual drone connection for MAVLink testing
- Performance benchmarking for latency requirements

## Token Management

**Usage Tracking:**
- Monitor all 14 agents' token consumption
- Generate reports every 10 tasks
- Alert at 80% context limit (160k tokens)
- Critical warning at 90% (180k tokens)
- Track cumulative session usage

## Common Development Commands

**Environment Setup:**
```bash
# Install dependencies
uv add flask flask-socketio pymavlink

# Run development server
uv run python src/web/app.py

# Run test suite
uv run pytest tests/ -v

# Run specific test phase
uv run pytest tests/phase1/ -v
```

**Testing Commands:**
```bash
# Run Playwright MCP tests
uv run pytest tests/ui/ --browser=chromium

# Performance testing
uv run pytest tests/performance/ -v

# Integration testing with virtual drone
uv run pytest tests/integration/ -v
```

## Deployment Targets

**Ubuntu Desktop:**
- Python 3.9+
- systemd service configuration
- TCP connection to drone
- Web interface on port 5001

**Raspberry Pi:**
- UART connection to flight controller
- MAVLink router setup
- WiFi hotspot capability
- Headless operation

## Critical Implementation Rules

1. **Test-First Development**: Write failing test → Implement → Pass test
2. **No Partial Credit**: Tests either pass completely or fail
3. **Continuous Testing**: Never stop until 100% pass rate achieved
4. **Modular Architecture**: Break files immediately when approaching 200 lines
5. **Safety First**: Never skip confirmation dialogs for critical commands
6. **Real Hardware Testing**: Use virtual drone for all integration testing
7. **Token Monitoring**: Track and report usage across all agents
8. **Complete Implementation**: System must be fully functional, not mockup

## Project Coordination

**Central Communication:**
- Maintain PROJECT_COORDINATION.md as communication hub between agents
- Track progress, blockers, and inter-agent dependencies
- Monitor test status and phase transitions
- Coordinate token usage across all agents

## Success Criteria

Project completion requires:
- All 14 subagents active and functional
- 100% test pass rate (50+ tests)
- Every button working with actual drone commands
- Professional VFR HUD with all 15 components
- Performance requirements met
- Safety confirmations implemented
- Modular architecture enforced (<200 lines per file)
- Token usage tracked and reported
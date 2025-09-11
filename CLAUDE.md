# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WebGCS is a production-ready, safety-critical web-based ground control station for MAVLink-compatible drones. The system provides comprehensive drone control through a browser interface with real-time telemetry, flight controls, and mission planning capabilities.

## Development Setup

**Python Environment:**
- Always use `uv` instead of `python` for all Python operations
- Run Python scripts with: `uv run python script.py`
- Install packages with: `uv add package_name`
- Run tests with: `uv run pytest`

**Virtual Drone Connection:**
- Virtual drone endpoint: `192.168.193.235:5678`
- All testing must connect to this real virtual drone
- No mock testing allowed - all tests must verify actual functionality

## Common Commands

**Development:**
```bash
# Start the web application
PYTHONPATH=. uv run python app.py

# Run specific test
uv run pytest tests/test_specific.py -v

# Run all tests (50+ comprehensive tests required)
uv run pytest tests/ -v

# Install new dependencies
uv add package_name

# Check Python syntax/imports
uv run python -m py_compile filename.py
```

**Testing Requirements:**
- Deploy website at `http://127.0.0.1:5002` before Phase 4+ testing
- All UI tests require live website for Playwright MCP interaction
- Tests must achieve 100% pass rate (not partial)
- No mock tests - verify real drone connectivity and functionality

## Architecture Overview

### Multi-Agent System (14 Specialized Agents)

This project uses 14 specialized Claude Code agents located in `agents/` directory:

**Core Development Agents:**
1. `coordinator-agent` - Project coordination and integration
2. `mavlink-protocol-agent` - MAVLink communication specialist  
3. `web-interface-agent` - Frontend Flask-SocketIO development
4. `request-handlers-agent` - Mission and geofence processing
5. `infrastructure-agent` - System setup and deployment
6. `testing-agent` - Test automation and QA

**Specialized Testing Agents (using Playwright MCP):**
7. `connection-testing-agent` - Connection UI testing
8. `flight-controls-testing-agent` - Flight button testing
9. `navigation-testing-agent` - Navigation input validation
10. `telemetry-display-testing-agent` - PFD/VFR HUD testing
11. `map-interface-testing-agent` - Interactive map testing
12. `ui-validation-testing-agent` - Safety confirmation testing
13. `virtual-drone-communication-agent` - End-to-end MAVLink verification
14. `token-tracking-agent` - Usage monitoring across all agents

### Modular Architecture Rules

**Critical Constraints:**
- NO file may exceed 200 lines (strict enforcement)
- Break large files immediately into smaller modules
- Each component should have single responsibility
- Maximum function length: 50 lines

**Directory Structure:**
```
src/
  web/
    app_factory.py      (max 150 lines)
    routes.py           (max 150 lines) 
    socketio_events.py  (max 150 lines)
  mavlink/
    connection_manager.py    (max 150 lines)
    message_processor.py     (max 150 lines)
    command_sender.py        (max 150 lines)
  utils/
    token_tracker.py         (max 150 lines)
    logger.py               (max 150 lines)
templates/
  index.html              (main layout only)
  components/
    connection_panel.html
    flight_controls.html
    navigation_panel.html
    pfd_display.html
    map_container.html
static/
  js/
    main.js             (max 100 lines)
    connection.js       (max 150 lines)
    telemetry.js        (max 150 lines)
    controls.js         (max 200 lines)
    map.js              (max 200 lines)
    pfd.js              (max 200 lines)
    validation.js       (max 150 lines)
  css/
    styles.css
tests/
  test_001_basic_connection.py
  ... (50+ comprehensive tests)
```

### Performance Requirements

**Critical Performance Targets:**
- Telemetry update rate: 10Hz to web interface
- Logging latency: <1ms per log entry
- End-to-end telemetry latency: <100ms
- Command acknowledgment timeout: <5 seconds
- Connection establishment: <5 seconds

### VFR HUD/Primary Flight Display

**Reference Images:**
- `HudLayoutExample.png` - Complete HUD layout (15 numbered elements)
- `HudLayoutItems.png` - Component specifications

**Display Requirements:**
- 800x600px canvas with rectangular artificial horizon
- 15 specific components positioned per reference images
- Professional glass cockpit styling
- Real-time updates at 10Hz minimum
- Armed/Disarmed status overlay
- All flight data tapes and navigation elements

### Safety Requirements

**Mandatory Safety Features:**
- Confirmation dialogs for ARM, DISARM, TAKEOFF operations
- Command tracking with acknowledgment verification
- Timeout handling for unacknowledged commands
- Connection monitoring with automatic failure detection
- Fail-safe behaviors on communication loss

### Testing Strategy

**7 Testing Phases (50+ total tests):**

1. **Phase 1: MAVLink Foundation (3 tests)** - Backend connectivity
2. **Phase 2: Web Interface Foundation (3 tests)** - Flask-SocketIO + **Deploy Website**
3. **Phase 3: Performance & Safety (4 tests)** - Benchmarks and safety mechanisms  
4. **Phase 4: Individual Button Testing (22+ tests)** - Every UI button with Playwright MCP
5. **Phase 5: VFR HUD/PFD Display (6 tests)** - Visual component validation
6. **Phase 6: UI Validation & Safety (5 tests)** - Input validation and confirmations
7. **Phase 7: Integration Testing (7+ tests)** - End-to-end workflows

**Critical Testing Requirements:**
- Website must be deployed at `http://127.0.0.1:5002` before Phase 4
- All tests must connect to real virtual drone at IP in .env
- Use Playwright MCP for all UI interaction testing
- Tests must FAIL when functionality is broken (no false positives)
- 100% pass rate required before project completion

### Token Usage Monitoring

**Implementation Required:**
```python
# src/utils/token_tracker.py
class AgentTracker:
    AGENTS = ['main', 'coordinator-agent', 'mavlink-protocol-agent', 
              'web-interface-agent', ...] # All 14 agents
    
    def track_usage(self, agent, input_tokens, output_tokens):
        # Track per agent with alerts at 80% (160k) and 90% (180k) limits
```

**Reporting:**
- Generate usage reports every 10 tasks
- Update PROJECT_COORDINATION.md with statistics
- Monitor high-usage agents (>20k tokens)
- Alert at context limit thresholds

### Deployment Targets

**Ubuntu Desktop:**
- systemd service configuration
- TCP connection to drone
- Web interface on port 5001

**Raspberry Pi:**
- UART connection to flight controller
- MAVLink router setup
- WiFi hotspot capability
- Headless operation

## Project Success Criteria

**Project completion requires ALL of:**
1. ✅ All 14 subagents active (verify with `/agents`)
2. ✅ ALL 50+ tests PASS (100% pass rate, not partial)
3. ✅ Every button functional (tested with Playwright MCP)
4. ✅ Token tracking implemented across all agents
5. ✅ No file exceeds 200 lines (modular architecture)
6. ✅ Real drone connection verified (192.168.193.235:5678)
7. ✅ Performance requirements met (<1ms log, <100ms telemetry)
8. ✅ Safety confirmations implemented and tested
9. ✅ VFR HUD displays all 15 components correctly
10. ✅ Modular architecture enforced throughout
11. ✅ Website fully functional at http://127.0.0.1:5002

## Development Guidelines

**Test-Driven Development:**
1. Write failing test first
2. Implement minimal code to pass
3. Refactor while maintaining green tests
4. Never skip tests or accept partial implementations

**Agent Coordination:**
- Use PROJECT_COORDINATION.md for inter-agent communication
- Each agent handles specific domain expertise
- Coordinator agent manages cross-component integration
- Token tracking agent monitors resource usage

**Code Quality:**
- Follow existing code patterns and conventions
- Maintain high performance for safety-critical operations  
- Implement proper error handling and logging
- Use type hints and documentation

**Critical Notes:**
- NO mock testing allowed - all tests must verify real functionality
- Tests must FAIL when features are broken (strict validation)
- Deploy website early (Phase 2) for subsequent UI testing phases
- Monitor token usage across all 14 agents continuously
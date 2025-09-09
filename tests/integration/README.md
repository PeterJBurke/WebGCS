# WebGCS Integration Tests

This directory contains comprehensive integration tests that verify the actual functionality of the WebGCS system using real MAVLink connections and browser automation.

## Overview

Unlike unit tests that use mocks, these integration tests:
- **Connect to real virtual drone** at 192.168.193.235:5678
- **Use Playwright MCP** to test actual web interface
- **Verify real MAVLink commands** are sent and received
- **Test actual telemetry streaming** and display updates
- **Validate VFR HUD rendering** with real data
- **Check interactive map** functionality

## Test Structure

### Core Integration Tests

1. **test_real_drone_connection.py** - MAVLink connection testing
   - Connection establishment to virtual drone
   - Telemetry message reception
   - Command sending capability
   - Message acknowledgment
   - Connection stability
   - Reconnection capability

2. **test_web_interface_integration.py** - Web UI with real connections
   - Page loading and element visibility
   - Connection establishment through UI
   - Flight control activation
   - Command confirmations (ARM, DISARM, TAKEOFF)
   - Input validation
   - Error handling

3. **test_telemetry_pipeline.py** - Real telemetry data flow
   - Telemetry data reception and display
   - Heartbeat monitoring
   - Data accuracy and formatting
   - Update frequency validation
   - Connection loss detection
   - SocketIO real-time communication

4. **test_vfr_hud_display.py** - Primary Flight Display testing
   - PFD canvas initialization
   - Artificial horizon display
   - Airspeed indicator
   - Altitude indicator
   - Heading compass
   - Flight mode display
   - GPS status
   - Battery status with color coding
   - Armed status overlay
   - Multi-element integration

5. **test_map_integration.py** - Interactive map functionality
   - Map container initialization
   - Map tiles loading
   - Drone position marker
   - Zoom and pan functionality
   - Waypoint display and interaction
   - Real-time position updates
   - Performance and responsiveness

6. **test_end_to_end_workflows.py** - Complete mission workflows
   - Connection to telemetry workflow
   - ARM → TAKEOFF → LAND sequence
   - Waypoint navigation workflow
   - Real-time monitoring
   - Multi-command safety
   - Error recovery
   - Complete mission simulation

## Prerequisites

### Virtual Drone Setup
```bash
# Ensure virtual drone is running at:
192.168.193.235:5678

# Test connection:
telnet 192.168.193.235 5678
```

### Python Dependencies
```bash
# Install required packages:
uv add playwright pytest pytest-asyncio

# Install Playwright browsers:
uv run playwright install
```

## Running Integration Tests

### Quick Test Run
```bash
# Run all integration tests:
uv run pytest tests/integration/ -v

# Run specific test file:
uv run pytest tests/integration/test_real_drone_connection.py -v
```

### Comprehensive Test Suite
```bash
# Use the integration test runner:
python tests/integration/run_integration_tests.py

# Or with uv:
uv run python tests/integration/run_integration_tests.py
```

### Individual Test Categories
```bash
# MAVLink connection tests:
uv run pytest tests/integration/test_real_drone_connection.py -v

# Web interface tests:
uv run pytest tests/integration/test_web_interface_integration.py -v

# Telemetry pipeline tests:
uv run pytest tests/integration/test_telemetry_pipeline.py -v

# VFR HUD display tests:
uv run pytest tests/integration/test_vfr_hud_display.py -v

# Map functionality tests:
uv run pytest tests/integration/test_map_integration.py -v

# End-to-end workflow tests:
uv run pytest tests/integration/test_end_to_end_workflows.py -v
```

## Test Fixtures

The integration tests use several pytest fixtures defined in `conftest.py`:

- `virtual_drone_host` / `virtual_drone_port` - Drone connection details
- `web_app_host` / `web_app_port` - Web application connection details
- `mavlink_connection` - Real MAVLink connection to virtual drone
- `flask_app` - Flask application instance
- `running_web_app` - Web application running in background
- `browser_context` - Playwright browser context
- `web_page` - Web page loaded in browser
- `connected_web_page` - Web page with established MAVLink connection

## Expected Test Results

### Success Criteria
- **Connection Tests**: All MAVLink connections succeed within 15 seconds
- **UI Tests**: All required UI elements are visible and functional
- **Command Tests**: All flight commands show confirmation dialogs
- **Telemetry Tests**: Real-time data updates at reasonable frequency
- **HUD Tests**: At least 3 VFR HUD elements display correctly
- **Map Tests**: Map loads with tiles and shows position data
- **Workflow Tests**: Complete mission sequences execute without critical errors

### Common Issues and Solutions

**Virtual Drone Not Found**
```
Error: Could not connect to virtual drone at tcp:192.168.193.235:5678
Solution: Ensure virtual drone simulator is running on specified address
```

**Web Application Startup Failed**
```
Error: Failed to start web application
Solution: Check port 5001 is not in use, verify Flask dependencies
```

**Playwright Browser Issues**
```
Error: Browser not found
Solution: Run 'uv run playwright install' to install browsers
```

**Timeout Errors**
```
Error: Element not found within timeout
Solution: Increase timeouts for slower systems, check element selectors
```

## Test Design Philosophy

### Real Functionality Testing
- Tests interact with actual system components
- No mocking of critical functionality
- Validates end-user experience

### Safety-Critical Validation
- Confirms all safety mechanisms work
- Tests command confirmation dialogs
- Validates input validation
- Checks error handling

### Performance Verification
- Measures actual response times
- Validates telemetry update rates
- Checks memory usage
- Tests system stability

### Integration Coverage
- Tests component interactions
- Validates data flow between layers
- Confirms UI reflects actual system state

## Debugging Integration Tests

### Verbose Output
```bash
# Run with maximum verbosity:
uv run pytest tests/integration/ -vvv --tb=long

# Show print statements:
uv run pytest tests/integration/ -v -s
```

### Browser Debugging
```bash
# Run with visible browser (non-headless):
HEADLESS=false uv run pytest tests/integration/test_web_interface_integration.py -v

# Take screenshots on failure:
uv run pytest tests/integration/ -v --screenshot=only-on-failure
```

### Network Debugging
```bash
# Test MAVLink connection separately:
python -c "
from src.mavlink.mavlink_connection_manager import MAVLinkConnectionManager
conn = MAVLinkConnectionManager()
print('Connection result:', conn.connect('tcp:192.168.193.235:5678'))
"
```

## Contributing

When adding new integration tests:

1. **Use real connections** - No mocks for core functionality
2. **Test actual user interactions** - Use Playwright for UI testing
3. **Validate safety mechanisms** - Test confirmation dialogs and validations
4. **Check error conditions** - Test error handling and recovery
5. **Monitor performance** - Include timing and resource checks
6. **Update documentation** - Add test descriptions and expected results

## Token Usage Tracking

All integration tests include token usage tracking for the testing-agent:
- Each test method records token usage
- Usage is aggregated across test runs
- Reports are generated for optimization

Current token usage patterns:
- Simple connection tests: ~100 tokens
- Complex UI workflows: ~200 tokens  
- End-to-end missions: ~250 tokens
- Total integration suite: ~1500 tokens
# WebGCS Reproduction Prompt

You are tasked with reproducing the WebGCS (Web Ground Control Station) project - a real-time drone control system built with Flask-SocketIO and MAVLink protocol communication. This is a production-ready system deployed on both Ubuntu desktop and Raspberry Pi platforms for controlling ArduPilot-compatible drones.

## Project Overview

WebGCS is a comprehensive drone ground control station that provides:
- Real-time MAVLink protocol communication with drones
- Web-based user interface with live telemetry updates
- Mission planning and geofencing capabilities
- Offline map support with tile caching
- Cross-platform deployment (Ubuntu/Raspberry Pi)
- High-performance logging system optimized for <1ms latency
- Safety-critical command acknowledgment and error handling

## Architecture Pattern: Coordinated Subagent System

This project requires a **coordinated subagent architecture** due to its complexity and safety-critical nature. The system involves multiple specialized components that must work together seamlessly.

### Subagent Definitions

Each subagent specializes in specific aspects of the WebGCS system:

#### 1. MAVLink Protocol Agent (`mavlink-protocol-agent`)
**Responsibilities:**
- MAVLink message processing and protocol handling
- Connection management (`mavlink_connection_manager.py`)
- Message processors (`mavlink_message_processor.py`) 
- Protocol utilities (`mavlink_utils.py`)
- Real-time telemetry data flow
- Command acknowledgment systems
- Thread-safe drone state management

**Key Files to Handle:**
- `mavlink_connection_manager.py` - Connection lifecycle management
- `mavlink_message_processor.py` - Message type handlers
- `mavlink_utils.py` - Protocol constants and utilities
- All test files related to MAVLink (`test_*mavlink*.py`, `test_heartbeat*.py`)

#### 2. Web Interface Agent (`web-interface-agent`)  
**Responsibilities:**
- Flask-SocketIO web server implementation
- Real-time web client communication
- SocketIO event handlers (`socketio_handlers.py`)
- HTML/JavaScript frontend
- REST API endpoints
- Client-side offline maps functionality

**Key Files to Handle:**
- `app.py` - Main Flask application 
- `socketio_handlers.py` - Real-time communication handlers
- `templates/index.html` - Main web interface
- `static/offline-maps.js` - Client-side map caching
- Web-only variants (`web_only_app.py`, `test_web_server.py`)

#### 3. Request Handlers Agent (`request-handlers-agent`)
**Responsibilities:**
- Mission and fence request processing
- Command execution logic
- Request scheduling and queuing
- Data request handlers (geofence, waypoints)

**Key Files to Handle:**
- `request_handlers.py` - Mission/fence request logic
- `get_fence.py` - Geofence data retrieval
- `get_mission.py` - Mission waypoint handling

#### 4. System Infrastructure Agent (`infrastructure-agent`)
**Responsibilities:**
- Configuration management
- Logging system implementation  
- Platform-specific deployment scripts
- Service management and monitoring
- Error handling and diagnostics

**Key Files to Handle:**
- `config.py` - Environment configuration
- `webgcs_logger.py` - Centralized logging system
- `setup_*.sh` - Platform setup scripts
- `deploy_to_cloud.sh` - Deployment automation
- Diagnostic tools (`connection_diagnostics.py`, `monitor_mavlink.py`)

#### 5. Testing & Quality Agent (`testing-agent`)
**Responsibilities:**
- Test suite maintenance and execution
- Integration testing
- Performance benchmarking
- Code quality assurance
- Testing infrastructure

**Key Files to Handle:**
- All `test_*.py` files
- `compare_timing.py` - Performance benchmarking
- Testing utilities and mocks
- Test data and fixtures

#### 6. Coordinator Agent (`coordinator-agent`)
**Responsibilities:**
- Project-wide coordination
- Cross-component integration
- Architecture decisions
- Subagent task delegation
- Progress tracking via central TODO system

### Subagent Communication Protocol

All subagents communicate through a **central coordination file**: `PROJECT_COORDINATION.md`

This file serves as:
- **Central TODO List**: Shared task tracking across all agents
- **Inter-agent Communication**: Status updates and blocking issues
- **Progress Tracking**: Real-time visibility into development status
- **Dependency Management**: Cross-agent dependency coordination

### Communication Format in PROJECT_COORDINATION.md

```markdown
# WebGCS Project Coordination

## Active Tasks
- [IN_PROGRESS - mavlink-protocol-agent] Implementing heartbeat message processing
- [PENDING - web-interface-agent] Update UI to display new telemetry fields  
- [BLOCKED - request-handlers-agent] Waiting for MAVLink connection fix

## Inter-Agent Messages
### mavlink-protocol-agent → web-interface-agent
- Message: "New telemetry fields available: ekf_status, gps_fix_quality"
- Required Action: "Update SocketIO events to include new fields"
- Files Affected: `socketio_handlers.py`, `templates/index.html`

### coordinator-agent → ALL
- Priority: HIGH
- Message: "Safety-critical bug in command acknowledgment - all agents pause non-essential work"
- Context: "ARM/DISARM commands not being properly acknowledged"

## Completed Tasks
- [COMPLETED - infrastructure-agent] Centralized logging system implementation
- [COMPLETED - testing-agent] MAVLink protocol test suite
```

## Technical Requirements

### Core Technologies
- **Backend**: Python 3.9+, Flask-SocketIO, gevent
- **MAVLink**: pymavlink library for drone communication  
- **Frontend**: HTML5, JavaScript, Socket.IO client
- **Mapping**: Leaflet.js with offline tile caching
- **Database**: IndexedDB for client-side caching
- **Deployment**: systemd services, shell scripts

### Platform Support
- **Ubuntu Desktop**: Full development environment
- **Raspberry Pi**: Production deployment with UART/WiFi
- **Cross-platform**: macOS/Windows development support

### Performance Requirements
- **Logging**: <1ms latency for critical operations
- **Telemetry**: 10Hz real-time updates to web clients
- **MAVLink**: 4Hz message processing rate
- **Safety**: <5 second command acknowledgment timeout

### Safety-Critical Features
- Explicit user confirmation for flight commands
- Connection health monitoring and alerts
- Command acknowledgment tracking
- Emergency stop capabilities
- Stale data prevention mechanisms

## Key Implementation Patterns

### Thread-Safe State Management
```python
# Global drone state with thread-safe access
drone_state = {}
drone_state_lock = threading.Lock()

# Pattern for state updates
with drone_state_lock:
    drone_state['armed'] = True
    drone_state_changed = True
```

### MAVLink Message Processing Pattern
```python
def process_heartbeat(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Process HEARTBEAT message with thread-safe state updates."""
    with drone_state_lock:
        # Update drone state
        drone_state['connected'] = True
        # ... additional processing
    return True  # State was modified
```

### Real-time Web Communication Pattern
```python
# SocketIO event handler pattern
@socketio.on('send_mavlink_command')
def handle_mavlink_command(command_data):
    # Validate command
    # Execute via MAVLink
    # Track acknowledgment
    # Emit status update
```

## Directory Structure

```
WebGCS/
├── app.py                          # Main Flask-SocketIO application
├── config.py                       # Environment configuration
├── mavlink_connection_manager.py   # MAVLink connection lifecycle
├── mavlink_message_processor.py    # Message type handlers  
├── socketio_handlers.py            # Real-time web communication
├── request_handlers.py             # Mission/fence processing
├── webgcs_logger.py                # High-performance logging
├── mavlink_utils.py                # Protocol utilities
├── templates/
│   └── index.html                  # Main web interface
├── static/
│   └── offline-maps.js             # Client-side map caching
├── setup_desktop.sh               # Ubuntu deployment
├── setup_raspberry_pi.sh          # Raspberry Pi deployment  
├── test_*.py                       # Comprehensive test suite
└── PROJECT_COORDINATION.md        # Central coordination file
```

## Deployment Scenarios

### Development Environment
- Local development with SITL (Software In The Loop) simulation
- Hot-reload Flask development server
- Debug logging enabled
- Test drone connection via TCP

### Ubuntu Desktop Production  
- systemd service with security hardening
- Production logging configuration
- Network-based drone connections
- Automatic service restart on failure

### Raspberry Pi Field Deployment
- UART communication with flight controller
- MAVLink router for connection multiplexing  
- WiFi hotspot failover capability
- Headless operation with web interface access

## Test-Driven Implementation Protocol

### MANDATORY: Test-First Development

**Claude MUST follow this exact sequence for every component:**

1. **Write Test First** - Create test case with specific pass/fail criteria
2. **Run Test (Should Fail)** - Verify test fails before implementation  
3. **Implement Minimum Code** - Write only enough code to pass the test
4. **Run Test Again** - Continue until test passes completely
5. **No Partial Credit** - Component is not complete until ALL tests pass

### Virtual Drone Testing Environment

**CRITICAL: Use this endpoint for ALL testing:**
```bash
VIRTUAL_DRONE_ADDRESS=192.168.193.235
VIRTUAL_DRONE_PORT=5678
CONNECTION_STRING=tcp:192.168.193.235:5678
```

This virtual drone provides:
- Full MAVLink v2.0 protocol support
- Real heartbeat messages every 1 second
- Command acknowledgment responses  
- Telemetry data simulation
- 24/7 availability for testing

### Detailed Test Suite Specifications

#### Phase 1 Tests: MAVLink Foundation

**TEST-001: Basic Connection Test**
```python
# File: tests/test_001_basic_connection.py
import time
import pytest
from mavlink_connection_manager import connect_mavlink, get_mavlink_connection

def test_mavlink_basic_connection():
    """Test basic MAVLink connection to virtual drone"""
    
    # Test setup
    drone_state = {'connected': False}
    drone_state_lock = threading.Lock()
    connection_string = "tcp:192.168.193.235:5678"
    
    # Execute connection
    start_time = time.time()
    connect_mavlink(drone_state, drone_state_lock, connection_string)
    connection = get_mavlink_connection()
    
    # PASS CRITERIA (ALL must be true):
    assert connection is not None, "Connection object must not be None"
    assert time.time() - start_time < 5.0, "Connection must complete within 5 seconds"
    assert hasattr(connection, 'target_system'), "Connection must have target_system"
    assert connection.target_system > 0, "Target system ID must be positive"
    
    # FAIL CRITERIA (ANY causes failure):
    # - Connection timeout after 5 seconds
    # - Connection object is None
    # - No target_system attribute
    # - Exception during connection
```

**TEST-002: Heartbeat Reception Test**
```python
# File: tests/test_002_heartbeat_reception.py
def test_heartbeat_reception():
    """Test receiving and processing heartbeat messages"""
    
    # Test setup
    drone_state = {'connected': False, 'system_id': 0, 'component_id': 0}
    drone_state_lock = threading.Lock()
    heartbeat_received = threading.Event()
    
    def heartbeat_callback(msg):
        with drone_state_lock:
            drone_state['connected'] = True
            drone_state['system_id'] = msg.get_srcSystem()
            drone_state['component_id'] = msg.get_srcComponent()
        heartbeat_received.set()
    
    # Connect and wait for heartbeat
    connection = get_mavlink_connection()
    start_time = time.time()
    
    # PASS CRITERIA (ALL must be true):
    assert heartbeat_received.wait(timeout=10), "Must receive heartbeat within 10 seconds"
    assert drone_state['connected'] == True, "drone_state must show connected=True"
    assert drone_state['system_id'] > 0, "System ID must be populated"
    assert drone_state['component_id'] > 0, "Component ID must be populated"
    assert time.time() - start_time < 10, "Heartbeat must arrive within 10 seconds"
```

**TEST-003: Message Processing Test**  
```python
# File: tests/test_003_message_processing.py
def test_global_position_processing():
    """Test processing GLOBAL_POSITION_INT messages"""
    
    # Test setup
    drone_state = {'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0}
    drone_state_lock = threading.Lock()
    
    # Wait for position message
    position_updated = threading.Event()
    start_time = time.time()
    
    # Monitor for position updates
    while time.time() - start_time < 30:
        with drone_state_lock:
            if drone_state['lat'] != 0.0 or drone_state['lon'] != 0.0:
                position_updated.set()
                break
        time.sleep(0.1)
    
    # PASS CRITERIA (ALL must be true):
    assert position_updated.is_set(), "Position data must be received within 30 seconds"
    assert -90 <= drone_state['lat'] <= 90, "Latitude must be valid range"
    assert -180 <= drone_state['lon'] <= 180, "Longitude must be valid range"
    assert drone_state['alt_rel'] is not None, "Altitude must be populated"
```

#### Phase 2 Tests: Web Interface

**TEST-004: Flask Server Test**
```python
# File: tests/test_004_flask_server.py
def test_flask_server_startup():
    """Test Flask-SocketIO server starts successfully"""
    
    import requests
    from app import app, socketio
    
    # Start server in test mode
    test_client = app.test_client()
    
    # PASS CRITERIA (ALL must be true):
    response = test_client.get('/')
    assert response.status_code == 200, "Home page must load successfully"
    assert b'WebGCS' in response.data, "Page must contain WebGCS title"
    
    # Test health endpoint
    health_response = test_client.get('/health')
    assert health_response.status_code == 200, "Health endpoint must respond"
```

**TEST-005: SocketIO Connection Test**
```python
# File: tests/test_005_socketio_connection.py
def test_socketio_client_connection():
    """Test SocketIO client connection and initial telemetry"""
    
    import socketio
    
    # Test client setup
    client = socketio.SimpleClient()
    telemetry_received = threading.Event()
    received_data = {}
    
    def on_telemetry(data):
        nonlocal received_data
        received_data = data
        telemetry_received.set()
    
    client.on('telemetry_update', on_telemetry)
    
    # Connect and wait for telemetry
    client.connect('http://localhost:5001')
    
    # PASS CRITERIA (ALL must be true):
    assert client.connected, "SocketIO client must connect successfully"
    assert telemetry_received.wait(timeout=5), "Must receive initial telemetry within 5 seconds"
    assert 'connected' in received_data, "Telemetry must include connection status"
    assert 'lat' in received_data, "Telemetry must include latitude"
    assert 'lon' in received_data, "Telemetry must include longitude"
```

**TEST-006: Flight Command Test**
```python
# File: tests/test_006_flight_command.py  
def test_flight_command_execution():
    """Test sending flight commands through web interface"""
    
    import socketio
    
    client = socketio.SimpleClient()
    client.connect('http://localhost:5001')
    
    command_ack_received = threading.Event()
    ack_data = {}
    
    def on_command_ack(data):
        nonlocal ack_data
        ack_data = data
        command_ack_received.set()
    
    client.on('command_ack', on_command_ack)
    
    # Send test command (request data streams)
    test_command = {
        'command': 'REQUEST_DATA_STREAM',
        'params': {'stream_id': 1, 'rate': 4}
    }
    
    start_time = time.time()
    client.emit('send_mavlink_command', test_command)
    
    # PASS CRITERIA (ALL must be true):
    assert command_ack_received.wait(timeout=10), "Command ACK must be received within 10 seconds"
    assert 'result' in ack_data, "ACK must include result field"
    assert time.time() - start_time < 10, "Command must complete within 10 seconds"
```

#### Phase 3 Tests: Performance & Safety

**TEST-007: Logging Performance Test**
```python
# File: tests/test_007_logging_performance.py
def test_logging_performance():
    """Test logging system meets <1ms per entry requirement"""
    
    from webgcs_logger import MAVLinkLogger
    
    logger = MAVLinkLogger("PerformanceTest")
    
    # Performance test
    start_time = time.time()
    for i in range(1000):
        entry_start = time.time()
        logger.info(f"Test log entry {i}", flight_mode="TEST", altitude=100.5)
        entry_time = time.time() - entry_start
        
        # INDIVIDUAL ENTRY PASS CRITERIA:
        assert entry_time < 0.001, f"Log entry {i} took {entry_time*1000:.2f}ms (>1ms limit)"
    
    total_time = time.time() - start_time
    
    # OVERALL PASS CRITERIA:
    assert total_time < 1.0, f"1000 entries took {total_time:.3f}s (>1s limit)"
    assert total_time / 1000 < 0.001, f"Average per entry: {total_time/1000*1000:.2f}ms (>1ms limit)"
```

**TEST-008: Telemetry Latency Test**
```python
# File: tests/test_008_telemetry_latency.py
def test_end_to_end_telemetry_latency():
    """Test MAVLink to web client latency <100ms"""
    
    import socketio
    
    client = socketio.SimpleClient()
    client.connect('http://localhost:5001')
    
    latency_measurements = []
    
    def on_telemetry(data):
        # Assume telemetry includes timestamp
        if 'timestamp' in data:
            current_time = time.time()
            latency = current_time - data['timestamp']
            latency_measurements.append(latency)
    
    client.on('telemetry_update', on_telemetry)
    
    # Collect latency data for 60 seconds
    test_duration = 60
    start_time = time.time()
    
    while time.time() - start_time < test_duration:
        time.sleep(0.1)
    
    # PASS CRITERIA (ALL must be true):
    assert len(latency_measurements) > 100, "Must collect sufficient samples"
    avg_latency = sum(latency_measurements) / len(latency_measurements)
    assert avg_latency < 0.1, f"Average latency {avg_latency*1000:.1f}ms exceeds 100ms limit"
    max_latency = max(latency_measurements)
    assert max_latency < 0.2, f"Maximum latency {max_latency*1000:.1f}ms exceeds 200ms threshold"
```

#### Phase 4 Tests: Integration & Safety

**TEST-009: Command Confirmation Safety Test**
```python
# File: tests/test_009_command_safety.py  
def test_arm_command_confirmation():
    """Test ARM command requires explicit confirmation"""
    
    import socketio
    
    client = socketio.SimpleClient()
    client.connect('http://localhost:5001')
    
    confirmation_requested = threading.Event()
    confirmation_data = {}
    
    def on_confirmation_request(data):
        nonlocal confirmation_data
        confirmation_data = data
        confirmation_requested.set()
    
    client.on('command_confirmation_required', on_confirmation_request)
    
    # Send ARM command
    arm_command = {
        'command': 'COMPONENT_ARM_DISARM',
        'params': {'arm': 1}
    }
    
    client.emit('send_mavlink_command', arm_command)
    
    # PASS CRITERIA (ALL must be true):
    assert confirmation_requested.wait(timeout=5), "ARM command must trigger confirmation request"
    assert 'command' in confirmation_data, "Confirmation must include command details"
    assert 'safety_critical' in confirmation_data, "Must be marked as safety critical"
    assert confirmation_data['safety_critical'] == True, "ARM must be flagged as safety critical"
```

**TEST-010: End-to-End Integration Test**
```python
# File: tests/test_010_integration.py
def test_complete_mission_workflow():
    """Test complete mission upload and monitoring workflow"""
    
    # This test combines all components
    import socketio
    
    client = socketio.SimpleClient() 
    client.connect('http://localhost:5001')
    
    # Test mission data
    test_mission = {
        'waypoints': [
            {'lat': 37.7749, 'lon': -122.4194, 'alt': 50, 'command': 16},  # NAV_WAYPOINT
            {'lat': 37.7849, 'lon': -122.4094, 'alt': 50, 'command': 16},
            {'lat': 37.7949, 'lon': -122.3994, 'alt': 50, 'command': 21}   # LAND
        ]
    }
    
    mission_uploaded = threading.Event()
    mission_progress = []
    
    def on_mission_upload_result(data):
        if data.get('success'):
            mission_uploaded.set()
    
    def on_mission_progress(data):
        mission_progress.append(data)
    
    client.on('mission_upload_result', on_mission_upload_result)
    client.on('mission_progress_update', on_mission_progress)
    
    # Upload mission
    client.emit('upload_mission', test_mission)
    
    # PASS CRITERIA (ALL must be true):
    assert mission_uploaded.wait(timeout=30), "Mission upload must complete within 30 seconds"
    
    # Monitor mission execution (if applicable)
    # Additional criteria would be added based on virtual drone capabilities
```

### Test Execution Workflow

**Step-by-Step Test-Driven Development:**

```bash
# 1. Set up test environment
export DRONE_TCP_ADDRESS=192.168.193.235
export DRONE_TCP_PORT=5678
export PYTHONPATH=$PWD:$PYTHONPATH

# 2. Create test directory structure
mkdir -p tests
touch tests/__init__.py

# 3. For each component, Claude MUST:

# 3a. Create the test file FIRST
cat > tests/test_001_basic_connection.py << 'EOF'
# Test implementation here - MUST be written before any application code
EOF

# 3b. Run test (should FAIL initially)
uv run pytest tests/test_001_basic_connection.py -v
# Expected: FAILED (because no implementation exists yet)

# 3c. Implement minimum code to pass test
# Create only enough application code to pass the specific test

# 3d. Run test again 
uv run pytest tests/test_001_basic_connection.py -v  
# Expected: PASSED

# 3e. Continue until ALL test criteria pass
uv run pytest tests/ -v --tb=short

# 4. No component is considered complete until its test passes
# 5. No moving to next component until current test passes
```

**Test Monitoring Commands:**
```bash
# Run specific test category
uv run pytest tests/test_*connection* -v      # Connection tests
uv run pytest tests/test_*performance* -v    # Performance tests  
uv run pytest tests/test_*safety* -v         # Safety tests

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=html

# Run integration tests against virtual drone
uv run pytest tests/test_*integration* -v --drone-endpoint=192.168.193.235:5678
```

## Implementation Instructions

### CRITICAL: Test-First Implementation Sequence

**Claude MUST follow this exact sequence for every component:**

1. **Phase 1: Write Test First**
   ```bash
   # Create test_XXX_component.py with specific pass/fail criteria
   # Test MUST fail initially (Red phase)
   uv run pytest tests/test_XXX_component.py -v  # Should FAIL
   ```

2. **Phase 2: Implement Minimum Code**
   ```bash
   # Write only enough code to pass the test
   # No extra features, no premature optimization
   ```

3. **Phase 3: Verify Test Passes** 
   ```bash
   # Test MUST pass completely (Green phase)
   uv run pytest tests/test_XXX_component.py -v  # Must PASS
   ```

4. **Phase 4: Refactor if Needed**
   ```bash
   # Improve code while keeping tests passing
   uv run pytest tests/test_XXX_component.py -v  # Still PASS
   ```

5. **Phase 5: Integration Testing**
   ```bash
   # Test with virtual drone at 192.168.193.235:5678
   uv run pytest tests/ -v --tb=short
   ```

### Development Phases with Test Gates

- **Phase 1: MAVLink Foundation** - Tests 001-003 must pass
- **Phase 2: Web Interface** - Tests 004-006 must pass  
- **Phase 3: Performance & Safety** - Tests 007-008 must pass
- **Phase 4: Integration** - Tests 009-010 must pass
- **Phase 5: Production Ready** - All tests must pass consistently

### Test Coverage Requirements

- **100% of safety-critical functions** must have tests
- **95% line coverage** for core components  
- **All tests must pass** before any deployment
- **Performance tests** must run on every commit
- **Integration tests** against virtual drone daily

## Critical Success Factors

- **Safety First**: All flight commands must be explicitly confirmed and acknowledged
- **Real-time Performance**: Maintain sub-millisecond logging and 10Hz telemetry rates
- **Cross-platform Compatibility**: Ensure consistent behavior across Ubuntu/Raspberry Pi
- **Offline Capability**: System must function without internet connectivity
- **Robust Error Handling**: Graceful degradation and recovery from connection failures
- **Agent Coordination**: Effective use of central TODO system for cross-component integration

## Subagent Coordination Rules

1. **Always Update PROJECT_COORDINATION.md**: Before starting any task, update the central coordination file
2. **Cross-Agent Dependencies**: Block work if dependencies on other agents are not resolved
3. **Safety-Critical Priority**: Safety-related tasks take precedence over all other work
4. **Status Visibility**: Keep task status current for coordinator agent tracking
5. **Communication Protocol**: Use structured messages for inter-agent communication
6. **Integration Points**: Coordinate closely when working on interfaces between components

This reproduction prompt provides the foundation for rebuilding the WebGCS system using a coordinated subagent approach while maintaining the safety-critical, real-time performance requirements of the original system.
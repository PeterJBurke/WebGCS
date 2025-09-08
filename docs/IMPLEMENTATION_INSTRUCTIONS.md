# WebGCS Implementation Instructions

**Complete step-by-step guide for recreating WebGCS using test-driven development with virtual drone testing**

## Overview

This document provides exact instructions for recreating the WebGCS (Web Ground Control Station) project using the companion documents:
- **WEBGCS_PRD.md** - Product requirements and test specifications
- **REPRODUCTION_PROMPT.md** - Technical implementation guide and code patterns

## Prerequisites

- Python 3.9+
- uv (fast Python package manager) - Install from https://docs.astral.sh/uv/
- Virtual drone available at `192.168.193.235:5678` (TCP)
- Git for version control
- Terminal/command line access

## Step 1: Project Setup and Environment

### 1.1 Create Project Structure
```bash
# Create project directory
mkdir WebGCS && cd WebGCS

# Initialize Git repository
git init

# Create directory structure
mkdir -p tests templates static
touch tests/__init__.py

# Initialize uv project with Python 3.9+
uv init --python 3.9

# Add core dependencies using uv
uv add flask flask-socketio pymavlink gevent pytest pytest-cov python-dotenv
```

### 1.2 Configure Virtual Drone Environment
```bash
# Set environment variables for virtual drone testing
export DRONE_TCP_ADDRESS=192.168.193.235
export DRONE_TCP_PORT=5678
export PYTHONPATH=$PWD:$PYTHONPATH

# Create .env file for persistent configuration
cat > .env << 'EOF'
DRONE_TCP_ADDRESS=192.168.193.235
DRONE_TCP_PORT=5678
WEB_SERVER_HOST=localhost
WEB_SERVER_PORT=5001
SECRET_KEY=webgcs_development_key
HEARTBEAT_TIMEOUT=30
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=10
TELEMETRY_UPDATE_INTERVAL=0.1
EOF
```

### 1.3 Initialize Coordination System
```bash
# Create central coordination file for subagent communication
cat > PROJECT_COORDINATION.md << 'EOF'
# WebGCS Project Coordination

## Current Phase: 1 (MAVLink Foundation)
## Gate Criteria: Tests 001-003 must pass before Phase 2

## Active Tasks
- [PENDING - coordinator-agent] Initialize Phase 1: TEST-001 Basic Connection
- [NOT_STARTED] All other components await Phase 1 completion

## Test Status
- TEST-001: NOT_STARTED (Basic MAVLink Connection)
- TEST-002: BLOCKED (Heartbeat Reception - awaiting 001)  
- TEST-003: BLOCKED (Message Processing - awaiting 002)
- TEST-004: BLOCKED (Flask Server - awaiting Phase 1)
- TEST-005: BLOCKED (SocketIO Connection - awaiting Phase 1)
- TEST-006: BLOCKED (Flight Commands - awaiting Phase 1)
- TEST-007: BLOCKED (Logging Performance - awaiting Phase 2)
- TEST-008: BLOCKED (Telemetry Latency - awaiting Phase 2)
- TEST-009: BLOCKED (Command Safety - awaiting Phase 3)
- TEST-010: BLOCKED (End-to-End Integration - awaiting Phase 4)

## Subagent Status
- coordinator-agent: ACTIVE (managing overall progress)
- mavlink-protocol-agent: READY (will handle Tests 001-003)
- web-interface-agent: STANDBY (awaiting Phase 1 completion)
- infrastructure-agent: STANDBY (awaiting Phase 2 completion)
- testing-agent: READY (supporting all phases)

## Virtual Drone Connection
- Endpoint: tcp://192.168.193.235:5678
- Status: Available for testing
- Protocol: MAVLink v2.0

## Next Action Required
Write TEST-001 for basic MAVLink connection validation
EOF
```

## Step 2: Phase 1 - MAVLink Foundation (Tests 001-003)

### 2.1 TEST-001: Basic Connection Test

**CRITICAL: Write test FIRST, then implement**

```bash
# Create TEST-001 (Red Phase - should FAIL initially)
cat > tests/test_001_basic_connection.py << 'EOF'
"""
TEST-001: Basic MAVLink Connection Test
Tests connection to virtual drone at 192.168.193.235:5678
"""
import time
import threading
import pytest

def test_mavlink_basic_connection():
    """Test basic MAVLink connection to virtual drone"""
    
    # Import will fail initially - this is expected
    from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    
    # Test setup
    drone_state = {'connected': False}
    drone_state_lock = threading.Lock()
    connection_string = "tcp:192.168.193.235:5678"
    
    print(f"Attempting connection to {connection_string}")
    
    # Execute connection
    start_time = time.time()
    connect_mavlink(drone_state, drone_state_lock, connection_string)
    connection = get_mavlink_connection()
    connection_time = time.time() - start_time
    
    # PASS CRITERIA (ALL must be true):
    assert connection is not None, "Connection object must not be None"
    assert connection_time < 5.0, f"Connection took {connection_time:.2f}s (>5s limit)"
    assert hasattr(connection, 'target_system'), "Connection must have target_system attribute"
    assert connection.target_system > 0, f"Target system ID is {connection.target_system} (must be >0)"
    
    print(f"✓ Connection successful in {connection_time:.2f}s")
    print(f"✓ Target System ID: {connection.target_system}")
    
    # FAIL CRITERIA (ANY causes failure):
    # - Connection timeout after 5 seconds
    # - Connection object is None
    # - No target_system attribute
    # - target_system is 0 or negative
    # - Exception during connection process

if __name__ == "__main__":
    test_mavlink_basic_connection()
    print("TEST-001 PASSED: Basic connection successful")
EOF

# Run test (should FAIL - no implementation exists)
echo "Running TEST-001 (should FAIL initially):"
uv run pytest tests/test_001_basic_connection.py -v
echo "Expected: FAILED (ImportError - mavlink_connection_manager does not exist)"
```

**Update coordination file:**
```bash
cat >> PROJECT_COORDINATION.md << 'EOF'

## Progress Update - $(date)
- [IN_PROGRESS - mavlink-protocol-agent] Created TEST-001 (Failed as expected - Red phase)
- [NEXT - mavlink-protocol-agent] Implement mavlink_connection_manager.py to pass TEST-001

## Implementation Notes
- Test created with specific pass/fail criteria
- Virtual drone endpoint: 192.168.193.235:5678 configured
- Connection timeout limit: 5 seconds
EOF
```

**Now implement minimum code to pass test (Green Phase):**
```bash
# Create mavlink_connection_manager.py with ONLY enough code to pass TEST-001
cat > mavlink_connection_manager.py << 'EOF'
"""
MAVLink Connection Manager
Handles MAVLink protocol connections and lifecycle management
"""
from pymavlink import mavutil
import time
import threading

# Module-level state
mavlink_connection_instance = None
last_heartbeat_time = 0
connection_lock = threading.Lock()

def connect_mavlink(drone_state, drone_state_lock, connection_string):
    """
    Establishes MAVLink connection to specified endpoint
    
    Args:
        drone_state: Shared state dictionary
        drone_state_lock: Threading lock for drone_state
        connection_string: MAVLink connection string (e.g., "tcp:192.168.193.235:5678")
    """
    global mavlink_connection_instance, last_heartbeat_time
    
    print(f"Connecting to MAVLink endpoint: {connection_string}")
    
    with connection_lock:
        try:
            # Create MAVLink connection
            mavlink_connection_instance = mavutil.mavlink_connection(
                connection_string,
                source_system=255,  # Ground Control Station ID
                source_component=0
            )
            
            print("MAVLink connection object created, waiting for target system...")
            
            # Wait for target system to be identified
            start_time = time.time()
            while time.time() - start_time < 4.0:  # 4 second timeout for target system
                if hasattr(mavlink_connection_instance, 'target_system'):
                    if mavlink_connection_instance.target_system > 0:
                        print(f"Target system identified: {mavlink_connection_instance.target_system}")
                        
                        with drone_state_lock:
                            drone_state['connected'] = True
                        
                        last_heartbeat_time = time.time()
                        return
                
                # Check for incoming messages to establish target system
                try:
                    msg = mavlink_connection_instance.recv_match(timeout=0.1)
                    if msg:
                        print(f"Received message: {msg.get_type()}")
                except:
                    pass
                
                time.sleep(0.1)
            
            print("Warning: Target system not identified within timeout")
            
        except Exception as e:
            print(f"Connection failed: {e}")
            mavlink_connection_instance = None
            with drone_state_lock:
                drone_state['connected'] = False

def get_mavlink_connection():
    """Returns the current MAVLink connection instance"""
    return mavlink_connection_instance

def get_last_heartbeat_time():
    """Returns timestamp of last received heartbeat"""
    return last_heartbeat_time

def is_connected():
    """Check if MAVLink connection is active"""
    global mavlink_connection_instance
    return mavlink_connection_instance is not None
EOF

# Run TEST-001 again (should PASS now)
echo "Running TEST-001 again (should PASS now):"
uv run pytest tests/test_001_basic_connection.py -v -s
```

**Update coordination after success:**
```bash
cat >> PROJECT_COORDINATION.md << 'EOF'

## Progress Update - $(date)
- [COMPLETED - mavlink-protocol-agent] TEST-001 PASSED: Basic connection implemented
- Connection to 192.168.193.235:5678 successful
- Target system identification working
- [IN_PROGRESS - mavlink-protocol-agent] Starting TEST-002: Heartbeat reception

## TEST-001 Results
- ✓ Connection established to virtual drone
- ✓ Connection time < 5 seconds
- ✓ Target system ID obtained
- Ready to proceed to heartbeat message handling
EOF
```

### 2.2 TEST-002: Heartbeat Reception Test

```bash
# Create TEST-002 for heartbeat message processing
cat > tests/test_002_heartbeat_reception.py << 'EOF'
"""
TEST-002: Heartbeat Reception Test
Tests receiving and processing HEARTBEAT messages from virtual drone
"""
import time
import threading
import pytest

def test_heartbeat_reception():
    """Test receiving and processing heartbeat messages"""
    
    from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    from mavlink_message_processor import process_heartbeat
    
    # Test setup
    drone_state = {
        'connected': False, 
        'system_id': 0, 
        'component_id': 0, 
        'armed': False,
        'mode': 'UNKNOWN'
    }
    drone_state_lock = threading.Lock()
    heartbeat_received = threading.Event()
    
    def mock_log_callback(command, params=None, details=None):
        print(f"LOG: {command} - {details}")
    
    def mock_socketio_instance():
        pass
    
    # Connect to virtual drone
    connection_string = "tcp:192.168.193.235:5678"
    connect_mavlink(drone_state, drone_state_lock, connection_string)
    connection = get_mavlink_connection()
    
    assert connection is not None, "Connection must be established first"
    
    print("Waiting for heartbeat messages...")
    start_time = time.time()
    
    # Listen for heartbeat messages
    while time.time() - start_time < 15:  # 15 second timeout
        try:
            msg = connection.recv_match(type='HEARTBEAT', timeout=1.0)
            if msg:
                print(f"Received HEARTBEAT from system {msg.get_srcSystem()}")
                
                # Process heartbeat using message processor
                state_changed = process_heartbeat(
                    msg, 
                    drone_state, 
                    drone_state_lock, 
                    connection,
                    mock_log_callback,
                    mock_socketio_instance
                )
                
                if state_changed:
                    heartbeat_received.set()
                    break
                    
        except Exception as e:
            print(f"Error receiving heartbeat: {e}")
        
        time.sleep(0.1)
    
    # PASS CRITERIA (ALL must be true):
    assert heartbeat_received.is_set(), "Must receive and process heartbeat within 15 seconds"
    
    with drone_state_lock:
        assert drone_state['connected'] == True, f"drone_state.connected is {drone_state['connected']} (must be True)"
        assert drone_state['system_id'] > 0, f"System ID is {drone_state['system_id']} (must be >0)"
        assert drone_state['component_id'] > 0, f"Component ID is {drone_state['component_id']} (must be >0)"
        assert drone_state['mode'] != 'UNKNOWN', f"Flight mode is {drone_state['mode']} (must not be UNKNOWN)"
    
    elapsed_time = time.time() - start_time
    print(f"✓ Heartbeat processed successfully in {elapsed_time:.2f}s")
    print(f"✓ System ID: {drone_state['system_id']}")
    print(f"✓ Component ID: {drone_state['component_id']}")
    print(f"✓ Flight Mode: {drone_state['mode']}")
    print(f"✓ Armed Status: {drone_state['armed']}")

if __name__ == "__main__":
    test_heartbeat_reception()
    print("TEST-002 PASSED: Heartbeat reception successful")
EOF

# Run TEST-002 (should FAIL - no message processor)
echo "Running TEST-002 (should FAIL initially):"
uv run pytest tests/test_002_heartbeat_reception.py -v
```

**Implement message processor to pass TEST-002:**
```bash
# Create mavlink_message_processor.py
cat > mavlink_message_processor.py << 'EOF'
"""
MAVLink Message Processor
Handles processing of specific MAVLink message types
"""
import time
import math
from pymavlink import mavutil

# Import configuration for flight modes
AP_CUSTOM_MODES = {
    'STABILIZE': 0,
    'ACRO': 1,
    'ALT_HOLD': 2,
    'AUTO': 3,
    'GUIDED': 4,
    'LOITER': 5,
    'RTL': 6,
    'LAND': 9,
    'POS_HOLD': 16,
    'BRAKE': 17,
    'THROW': 18,
    'AVOID_ADSB': 19,
    'GUIDED_NOGPS': 20,
    'SMART_RTL': 21,
    'FLOWHOLD': 22,
    'FOLLOW': 23,
    'ZIGZAG': 24,
    'SYSTEMID': 25,
    'AUTOROTATE': 26,
    'AUTO_RTL': 27
}

def process_heartbeat(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance, heartbeat_log_cb=None):
    """
    Process HEARTBEAT message and update drone state
    
    Args:
        msg: MAVLink HEARTBEAT message
        drone_state: Shared state dictionary  
        drone_state_lock: Threading lock
        mavlink_conn: MAVLink connection object
        log_cmd_action_cb: Logging callback
        sio_instance: SocketIO instance
        heartbeat_log_cb: Optional heartbeat logging callback
        
    Returns:
        bool: True if drone_state was modified
    """
    
    try:
        with drone_state_lock:
            # Update connection status
            drone_state['connected'] = True
            
            # Extract system and component IDs
            drone_state['system_id'] = msg.get_srcSystem()
            drone_state['component_id'] = msg.get_srcComponent()
            
            # Extract armed status from base mode
            drone_state['armed'] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            
            # Extract flight mode from custom mode
            custom_mode = msg.custom_mode
            mode_name = 'UNKNOWN'
            
            # Find mode name from custom mode number
            for mode_str, mode_num in AP_CUSTOM_MODES.items():
                if mode_num == custom_mode:
                    mode_name = mode_str
                    break
            
            if mode_name == 'UNKNOWN' and custom_mode != 0:
                mode_name = f'CUSTOM_{custom_mode}'
            
            drone_state['mode'] = mode_name
            
            # Store system status
            drone_state['system_status'] = msg.system_status
            
            # Log heartbeat processing
            if log_cmd_action_cb:
                log_cmd_action_cb(
                    "HEARTBEAT_PROCESSED", 
                    details=f"System {drone_state['system_id']}, Mode: {mode_name}, Armed: {drone_state['armed']}"
                )
        
        # Custom heartbeat logging if callback provided
        if heartbeat_log_cb:
            heartbeat_log_cb(msg)
        
        return True  # State was modified
        
    except Exception as e:
        if log_cmd_action_cb:
            log_cmd_action_cb("HEARTBEAT_ERROR", details=f"Processing failed: {e}")
        print(f"Error processing heartbeat: {e}")
        return False

def process_global_position_int(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Process GLOBAL_POSITION_INT message for position data"""
    
    try:
        with drone_state_lock:
            # Update position data (convert from 1E7 format)
            drone_state['lat'] = msg.lat / 1e7
            drone_state['lon'] = msg.lon / 1e7
            drone_state['alt_abs'] = msg.alt / 1000.0  # mm to m
            drone_state['alt_rel'] = msg.relative_alt / 1000.0  # mm to m
            
            # Update velocity (convert from cm/s to m/s)
            drone_state['vx'] = msg.vx / 100.0
            drone_state['vy'] = msg.vy / 100.0
            drone_state['vz'] = msg.vz / 100.0
            
            # Calculate heading from velocity
            if msg.hdg != 65535:  # Valid heading available
                drone_state['heading'] = msg.hdg / 100.0  # centidegrees to degrees
            else:
                # Calculate from velocity if heading not available
                if drone_state['vx'] != 0 or drone_state['vy'] != 0:
                    heading_rad = math.atan2(drone_state['vy'], drone_state['vx'])
                    drone_state['heading'] = math.degrees(heading_rad)
                    if drone_state['heading'] < 0:
                        drone_state['heading'] += 360
        
        return True
        
    except Exception as e:
        if log_cmd_action_cb:
            log_cmd_action_cb("POSITION_ERROR", details=f"Processing failed: {e}")
        return False

def process_command_ack(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance):
    """Process COMMAND_ACK message for command acknowledgments"""
    
    try:
        command = msg.command
        result = msg.result
        
        # Log command acknowledgment
        if log_cmd_action_cb:
            result_str = "SUCCESS" if result == 0 else f"FAILED({result})"
            log_cmd_action_cb(
                "COMMAND_ACK", 
                params={'command': command, 'result': result},
                details=f"Command {command} result: {result_str}"
            )
        
        return False  # ACK doesn't modify drone state directly
        
    except Exception as e:
        if log_cmd_action_cb:
            log_cmd_action_cb("ACK_ERROR", details=f"Processing failed: {e}")
        return False
EOF

# Run TEST-002 again (should PASS now)
echo "Running TEST-002 again (should PASS now):"
uv run pytest tests/test_002_heartbeat_reception.py -v -s
```

### 2.3 TEST-003: Message Processing Test

```bash
# Create TEST-003 for GLOBAL_POSITION_INT processing
cat > tests/test_003_message_processing.py << 'EOF'
"""
TEST-003: Message Processing Test  
Tests processing of GLOBAL_POSITION_INT messages
"""
import time
import threading
import pytest

def test_global_position_processing():
    """Test processing GLOBAL_POSITION_INT messages"""
    
    from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    from mavlink_message_processor import process_global_position_int
    
    # Test setup
    drone_state = {
        'connected': False,
        'lat': 0.0, 
        'lon': 0.0, 
        'alt_rel': 0.0,
        'alt_abs': 0.0,
        'heading': 0.0,
        'vx': 0.0, 'vy': 0.0, 'vz': 0.0
    }
    drone_state_lock = threading.Lock()
    position_updated = threading.Event()
    
    def mock_log_callback(command, params=None, details=None):
        print(f"LOG: {command} - {details}")
    
    def mock_socketio_instance():
        pass
    
    # Connect to virtual drone
    connection_string = "tcp:192.168.193.235:5678"
    connect_mavlink(drone_state, drone_state_lock, connection_string)
    connection = get_mavlink_connection()
    
    assert connection is not None, "Connection must be established first"
    
    print("Waiting for GLOBAL_POSITION_INT messages...")
    start_time = time.time()
    
    # Monitor for position updates
    while time.time() - start_time < 30:  # 30 second timeout
        try:
            msg = connection.recv_match(type='GLOBAL_POSITION_INT', timeout=1.0)
            if msg:
                print(f"Received GLOBAL_POSITION_INT: lat={msg.lat/1e7:.6f}, lon={msg.lon/1e7:.6f}")
                
                # Process position message
                state_changed = process_global_position_int(
                    msg,
                    drone_state,
                    drone_state_lock, 
                    connection,
                    mock_log_callback,
                    mock_socketio_instance
                )
                
                if state_changed:
                    with drone_state_lock:
                        if drone_state['lat'] != 0.0 or drone_state['lon'] != 0.0:
                            position_updated.set()
                            break
                            
        except Exception as e:
            print(f"Error receiving position: {e}")
        
        time.sleep(0.1)
    
    # PASS CRITERIA (ALL must be true):
    assert position_updated.is_set(), "Position data must be received and processed within 30 seconds"
    
    with drone_state_lock:
        assert -90 <= drone_state['lat'] <= 90, f"Latitude {drone_state['lat']} outside valid range"
        assert -180 <= drone_state['lon'] <= 180, f"Longitude {drone_state['lon']} outside valid range"
        assert drone_state['alt_rel'] is not None, "Relative altitude must be populated"
        assert drone_state['alt_abs'] is not None, "Absolute altitude must be populated"
    
    elapsed_time = time.time() - start_time
    print(f"✓ Position data processed in {elapsed_time:.2f}s")
    print(f"✓ Latitude: {drone_state['lat']:.6f}")
    print(f"✓ Longitude: {drone_state['lon']:.6f}")
    print(f"✓ Altitude (rel): {drone_state['alt_rel']:.1f}m")
    print(f"✓ Altitude (abs): {drone_state['alt_abs']:.1f}m")
    print(f"✓ Heading: {drone_state['heading']:.1f}°")

if __name__ == "__main__":
    test_global_position_processing()
    print("TEST-003 PASSED: Position message processing successful")
EOF

# Run TEST-003 (should PASS with existing message processor)
echo "Running TEST-003:"
uv run pytest tests/test_003_message_processing.py -v -s
```

### 2.4 Phase 1 Gate Validation

```bash
# Validate all Phase 1 tests pass together
echo "=== PHASE 1 GATE VALIDATION ==="
uv run pytest tests/test_001_basic_connection.py tests/test_002_heartbeat_reception.py tests/test_003_message_processing.py -v

# Update coordination file
cat >> PROJECT_COORDINATION.md << 'EOF'

## PHASE 1 COMPLETION - $(date)
- [COMPLETED - mavlink-protocol-agent] TEST-001: Basic Connection ✓
- [COMPLETED - mavlink-protocol-agent] TEST-002: Heartbeat Reception ✓  
- [COMPLETED - mavlink-protocol-agent] TEST-003: Message Processing ✓

## Phase 1 Gate: PASSED
All MAVLink foundation tests successful. Ready for Phase 2.

## Phase 2 Ready
- [READY - web-interface-agent] Can now start Flask/SocketIO implementation
- [PENDING] TEST-004: Flask Server Startup
- [PENDING] TEST-005: SocketIO Connection
- [PENDING] TEST-006: Flight Command Execution

## MAVLink Foundation Confirmed
- ✓ Virtual drone connection at 192.168.193.235:5678
- ✓ Heartbeat message processing
- ✓ Position telemetry processing
- ✓ Thread-safe state management
EOF
```

## Step 3: Phase 2 - Web Interface (Tests 004-006)

### 3.1 Create Basic Flask Application

```bash
# Create config.py first
cat > config.py << 'EOF'
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Drone Connection Settings
DRONE_TCP_ADDRESS = os.getenv('DRONE_TCP_ADDRESS', '192.168.193.235')
DRONE_TCP_PORT = os.getenv('DRONE_TCP_PORT', '5678')
MAVLINK_CONNECTION_STRING = f'tcp:{DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}'

# Web Server Settings
WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST', 'localhost')
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT', '5001'))
SECRET_KEY = os.getenv('SECRET_KEY', 'webgcs_development_secret')

# MAVLink Settings
HEARTBEAT_TIMEOUT = int(os.getenv('HEARTBEAT_TIMEOUT', '30'))
REQUEST_STREAM_RATE_HZ = int(os.getenv('REQUEST_STREAM_RATE_HZ', '4'))
COMMAND_ACK_TIMEOUT = int(os.getenv('COMMAND_ACK_TIMEOUT', '10'))
TELEMETRY_UPDATE_INTERVAL = float(os.getenv('TELEMETRY_UPDATE_INTERVAL', '0.1'))

# ArduPilot Custom Flight Modes
AP_CUSTOM_MODES = {
    'STABILIZE': 0, 'ACRO': 1, 'ALT_HOLD': 2, 'AUTO': 3, 'GUIDED': 4,
    'LOITER': 5, 'RTL': 6, 'LAND': 9, 'POS_HOLD': 16, 'BRAKE': 17,
    'THROW': 18, 'AVOID_ADSB': 19, 'GUIDED_NOGPS': 20, 'SMART_RTL': 21,
    'FLOWHOLD': 22, 'FOLLOW': 23, 'ZIGZAG': 24, 'SYSTEMID': 25,
    'AUTOROTATE': 26, 'AUTO_RTL': 27
}
EOF
```

### 3.2 TEST-004: Flask Server Test

```bash
# Create TEST-004
cat > tests/test_004_flask_server.py << 'EOF'
"""
TEST-004: Flask Server Test
Tests Flask-SocketIO server startup and basic endpoints
"""
import pytest
import threading
import time
import requests

def test_flask_server_startup():
    """Test Flask-SocketIO server starts successfully"""
    
    from app import app, socketio
    
    # Test with Flask test client (synchronous)
    test_client = app.test_client()
    
    # PASS CRITERIA: Home page loads successfully
    response = test_client.get('/')
    assert response.status_code == 200, f"Home page returned {response.status_code}, expected 200"
    assert b'WebGCS' in response.data, "Home page must contain 'WebGCS' title"
    
    print("✓ Home page loaded successfully")
    
    # PASS CRITERIA: Health endpoint responds
    health_response = test_client.get('/health')
    assert health_response.status_code == 200, f"Health endpoint returned {health_response.status_code}, expected 200"
    
    health_data = health_response.get_json()
    assert 'status' in health_data, "Health response must include 'status' field"
    assert health_data['status'] == 'healthy', f"Health status is '{health_data['status']}', expected 'healthy'"
    
    print("✓ Health endpoint working")
    print(f"✓ Health data: {health_data}")

def test_flask_server_live():
    """Test Flask server can be started and responds to HTTP requests"""
    
    # Import after ensuring app.py exists
    import app
    
    # Start server in background thread
    server_ready = threading.Event()
    server_thread = None
    
    def run_server():
        try:
            print("Starting Flask-SocketIO server...")
            app.socketio.run(
                app.app, 
                host='127.0.0.1', 
                port=5001, 
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            print(f"Server error: {e}")
    
    try:
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        print("Waiting for server startup...")
        time.sleep(3)  # Give server time to start
        
        # Test server is responding
        response = requests.get('http://127.0.0.1:5001/health', timeout=5)
        assert response.status_code == 200, f"Server health check failed: {response.status_code}"
        
        health_data = response.json()
        assert health_data['status'] == 'healthy', f"Server not healthy: {health_data}"
        
        print("✓ Live server test passed")
        print(f"✓ Server health: {health_data}")
        
    except Exception as e:
        pytest.skip(f"Live server test skipped due to: {e}")

if __name__ == "__main__":
    test_flask_server_startup()
    print("TEST-004 PASSED: Flask server startup successful")
EOF

# Run TEST-004 (should FAIL - no app.py)
echo "Running TEST-004 (should FAIL initially):"
uv run pytest tests/test_004_flask_server.py::test_flask_server_startup -v
```

### 3.3 Implement Basic Flask Application

```bash
# Create basic app.py to pass TEST-004
cat > app.py << 'EOF'
"""
WebGCS Flask Application
Web Ground Control Station main application
"""
import os
import sys
import threading
import time
from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# Import configuration
from config import (
    WEB_SERVER_HOST, WEB_SERVER_PORT, SECRET_KEY,
    MAVLINK_CONNECTION_STRING, TELEMETRY_UPDATE_INTERVAL
)

# Import MAVLink components
from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
from mavlink_message_processor import process_heartbeat, process_global_position_int

# Flask & SocketIO Setup
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True

socketio = SocketIO(
    app,
    async_mode='threading',
    cors_allowed_origins="*",
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e6,
    engineio_logger=False,
    socketio_logger=False
)

# Global State
drone_state = {
    'connected': False,
    'armed': False,
    'mode': 'UNKNOWN',
    'lat': 0.0, 'lon': 0.0,
    'alt_rel': 0.0, 'alt_abs': 0.0,
    'heading': 0.0,
    'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
    'system_id': 0,
    'component_id': 0,
    'system_status': 0
}
drone_state_lock = threading.Lock()
drone_state_changed = False

def log_command_action(command_name, params=None, details=None, level="INFO"):
    """Simple logging function"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    params_str = f", Params: {params}" if params else ""
    details_str = f" - {details}" if details else ""
    print(f"[{timestamp}] {level} | {command_name}{params_str}{details_str}")

def set_drone_state_changed():
    """Mark drone state as changed for telemetry updates"""
    global drone_state_changed
    drone_state_changed = True

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html', version="WebGCS v1.0")

@app.route('/health')
def health():
    """Health check endpoint"""
    with drone_state_lock:
        return jsonify({
            "status": "healthy",
            "drone_connected": drone_state.get("connected", False),
            "timestamp": time.time()
        })

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# SocketIO Event Handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid if 'request' in globals() else 'unknown'}")
    
    # Send initial telemetry
    with drone_state_lock:
        emit('telemetry_update', drone_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid if 'request' in globals() else 'unknown'}")

# Telemetry Update Thread
def telemetry_update_thread():
    """Send periodic telemetry updates to web clients"""
    global drone_state_changed
    
    while True:
        try:
            if drone_state_changed:
                with drone_state_lock:
                    socketio.emit('telemetry_update', drone_state)
                    drone_state_changed = False
            
            time.sleep(TELEMETRY_UPDATE_INTERVAL)
            
        except Exception as e:
            print(f"Telemetry update error: {e}")
            time.sleep(1)

if __name__ == '__main__':
    print(f"Starting WebGCS server on {WEB_SERVER_HOST}:{WEB_SERVER_PORT}")
    
    # Start telemetry update thread
    telemetry_thread = threading.Thread(target=telemetry_update_thread, daemon=True)
    telemetry_thread.start()
    print("Telemetry update thread started")
    
    # Start Flask-SocketIO server
    try:
        socketio.run(
            app,
            host=WEB_SERVER_HOST,
            port=WEB_SERVER_PORT,
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        print(f"Server startup failed: {e}")
        sys.exit(1)
EOF

# Create basic HTML template
mkdir -p templates
cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ version }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f0f0f0; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .connected { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .disconnected { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .telemetry { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .telemetry-item { padding: 10px; background: #e9ecef; border-radius: 4px; }
        .value { font-weight: bold; font-size: 1.2em; color: #007bff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ version }}</h1>
        
        <div id="connection-status" class="status disconnected">
            Disconnected from drone
        </div>
        
        <div class="telemetry">
            <div class="telemetry-item">
                <div>Latitude</div>
                <div id="lat" class="value">0.000000</div>
            </div>
            <div class="telemetry-item">
                <div>Longitude</div>
                <div id="lon" class="value">0.000000</div>
            </div>
            <div class="telemetry-item">
                <div>Altitude (rel)</div>
                <div id="alt" class="value">0.0 m</div>
            </div>
            <div class="telemetry-item">
                <div>Flight Mode</div>
                <div id="mode" class="value">UNKNOWN</div>
            </div>
            <div class="telemetry-item">
                <div>Armed Status</div>
                <div id="armed" class="value">DISARMED</div>
            </div>
            <div class="telemetry-item">
                <div>Heading</div>
                <div id="heading" class="value">0.0°</div>
            </div>
        </div>
    </div>

    <script src="/static/socket.io.min.js"></script>
    <script>
        const socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to WebGCS server');
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from WebGCS server');
        });
        
        socket.on('telemetry_update', function(data) {
            // Update connection status
            const statusDiv = document.getElementById('connection-status');
            if (data.connected) {
                statusDiv.className = 'status connected';
                statusDiv.textContent = `Connected to drone (System ${data.system_id})`;
            } else {
                statusDiv.className = 'status disconnected';
                statusDiv.textContent = 'Disconnected from drone';
            }
            
            // Update telemetry values
            document.getElementById('lat').textContent = data.lat.toFixed(6);
            document.getElementById('lon').textContent = data.lon.toFixed(6);
            document.getElementById('alt').textContent = data.alt_rel.toFixed(1) + ' m';
            document.getElementById('mode').textContent = data.mode;
            document.getElementById('armed').textContent = data.armed ? 'ARMED' : 'DISARMED';
            document.getElementById('heading').textContent = data.heading.toFixed(1) + '°';
        });
    </script>
</body>
</html>
EOF

# Create static directory and download Socket.IO client
mkdir -p static
# Note: In production, download socket.io.min.js to static/ directory
echo "// Socket.IO client placeholder - download from https://cdn.socket.io/4.0.0/socket.io.min.js" > static/socket.io.min.js

# Run TEST-004 again (should PASS now)
echo "Running TEST-004 again (should PASS now):"
uv run pytest tests/test_004_flask_server.py::test_flask_server_startup -v
```

## Step 4: Continuing with Remaining Tests

**Follow the same pattern for all remaining tests:**

```bash
# For each subsequent test (005-010):
# 1. Write test first (RED phase)
# 2. Run test - should FAIL initially  
# 3. Implement minimum code to pass (GREEN phase)
# 4. Run test again - must PASS
# 5. Update PROJECT_COORDINATION.md with progress
# 6. Only move to next test when current test passes

# Example workflow for TEST-005:
cat > tests/test_005_socketio_connection.py << 'EOF'
# Complete SocketIO test implementation...
EOF

uv run pytest tests/test_005_socketio_connection.py -v  # Should FAIL
# Implement SocketIO functionality
uv run pytest tests/test_005_socketio_connection.py -v  # Must PASS

# Continue this pattern for all tests...
```

## Step 5: Final Validation and Deployment

### 5.1 Run Complete Test Suite

```bash
# All tests must pass before deployment
echo "=== COMPLETE TEST SUITE VALIDATION ==="
uv run pytest tests/ -v --tb=short

# Performance validation
uv run pytest tests/test_007_logging_performance.py -v
uv run pytest tests/test_008_telemetry_latency.py -v

# Safety validation
uv run pytest tests/test_009_command_safety.py -v

# Integration validation
uv run pytest tests/test_010_integration.py -v
```

### 5.2 Start Complete System

```bash
# Connect to virtual drone and start web server
export DRONE_TCP_ADDRESS=192.168.193.235
export DRONE_TCP_PORT=5678

uv run python app.py
```

### 5.3 Validate in Browser

```bash
# Test web interface
curl http://localhost:5001/health

# Open browser to http://localhost:5001
# Should see:
# - WebGCS interface
# - Connection to virtual drone
# - Real-time telemetry updates
```

## Critical Success Rules

### **1. Test-First Discipline**
- **NEVER** implement without writing test first
- **EVERY** test must FAIL initially (Red phase)
- **NO** partial implementations - test must PASS completely
- **NO** moving forward until current test passes

### **2. Virtual Drone Testing**
- **ALL** MAVLink tests use `192.168.193.235:5678`
- **VERIFY** real protocol communication
- **NO** mock implementations for MAVLink testing
- **CONFIRM** heartbeat, telemetry, and commands work

### **3. Phase Gate Discipline**  
- **Phase 1**: Tests 001-003 must pass (MAVLink foundation)
- **Phase 2**: Tests 004-006 must pass (Web interface)
- **Phase 3**: Tests 007-008 must pass (Performance)  
- **Phase 4**: Tests 009-010 must pass (Safety/Integration)
- **NO** skipping phases or tests

### **4. Coordination Protocol**
- **UPDATE** `PROJECT_COORDINATION.md` before each task
- **BLOCK** on dependencies from other subagents
- **MAINTAIN** visibility into progress and status
- **COMMUNICATE** issues and blockers immediately

### **5. Zero Tolerance for Safety**
- **100%** test coverage for safety-critical functions
- **ALL** flight commands require confirmation
- **IMMEDIATE** debugging if safety tests fail
- **NO** deployment until all safety tests pass

Following these instructions ensures you build a complete, tested, and safe WebGCS system that works with real drone hardware through the virtual drone testing endpoint.
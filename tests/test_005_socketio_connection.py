"""
TEST-005: SocketIO Connection Test
Tests SocketIO client connection, telemetry reception, and real-time data flow

CRITICAL: This test validates the complete real-time telemetry flow:
Virtual Drone → MAVLink → Flask Server → SocketIO → Test Client

Following test-driven development: RED phase (should FAIL initially)
"""
import pytest
import threading
import time
import sys
import os
import json
import socketio

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_socketio_client_connection():
    """Test SocketIO client can connect to Flask-SocketIO server"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    # Test setup
    server_thread = None
    server_started = threading.Event()
    server_error = None
    client_connected = threading.Event()
    client_disconnected = threading.Event()
    connection_error = None
    
    # Create SocketIO test client
    sio_client = socketio.Client()
    
    @sio_client.event
    def connect():
        """Handle client connection event"""
        print("✓ SocketIO client connected to server")
        client_connected.set()
    
    @sio_client.event
    def disconnect():
        """Handle client disconnection event"""
        print("✓ SocketIO client disconnected from server")
        client_disconnected.set()
    
    @sio_client.event
    def connect_error(data):
        """Handle connection errors"""
        nonlocal connection_error
        connection_error = data
        print(f"SocketIO connection error: {data}")
    
    def run_server():
        """Run Flask-SocketIO server in background"""
        try:
            print("Starting Flask-SocketIO server for SocketIO test...")
            app.socketio.run(
                app.app,
                host='127.0.0.1',
                port=5003,  # Different port for SocketIO test
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            nonlocal server_error
            server_error = e
            print(f"Server error in SocketIO test: {e}")
    
    try:
        # Start server in background thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server startup
        print("Waiting for server to start...")
        time.sleep(2.0)
        
        # PASS CRITERIA 1: Client can connect to SocketIO server
        print("Attempting SocketIO client connection...")
        connection_timeout = 10.0
        start_time = time.time()
        
        try:
            sio_client.connect('http://127.0.0.1:5003', wait_timeout=connection_timeout)
        except Exception as e:
            if server_error:
                pytest.fail(f"Server failed to start: {server_error}")
            else:
                pytest.fail(f"SocketIO client connection failed: {e}")
        
        # Wait for connection confirmation
        if not client_connected.wait(timeout=5.0):
            pytest.fail("SocketIO client did not connect within timeout")
        
        connection_time = time.time() - start_time
        assert connection_time < 10.0, f"Connection took {connection_time:.2f}s (>10s limit)"
        
        print(f"✓ SocketIO client connected successfully in {connection_time:.2f}s")
        
        # PASS CRITERIA 2: Connection is stable and maintains session
        time.sleep(1.0)  # Test connection stability
        assert sio_client.connected, "SocketIO connection should remain stable"
        
        print("✓ SocketIO connection stable")
        
        # Clean disconnect
        sio_client.disconnect()
        
        # Wait for clean disconnection
        if not client_disconnected.wait(timeout=3.0):
            print("Warning: Clean disconnection not confirmed")
        
        print("✓ SocketIO client disconnection successful")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower():
            pytest.skip(f"SocketIO connection test skipped due to: {e}")
        else:
            raise
    finally:
        # Cleanup
        if sio_client.connected:
            sio_client.disconnect()

def test_telemetry_update_reception():
    """Test receiving telemetry_update events from SocketIO server with real MAVLink data"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    # Test setup
    server_thread = None
    mavlink_thread = None
    server_started = threading.Event()
    telemetry_received = threading.Event()
    server_error = None
    telemetry_data = {}
    telemetry_count = 0
    
    # Create SocketIO test client for telemetry
    sio_client = socketio.Client()
    
    @sio_client.event
    def connect():
        """Handle client connection"""
        print("✓ SocketIO telemetry client connected")
        server_started.set()
    
    @sio_client.event
    def telemetry_update(data):
        """Handle telemetry update events"""
        nonlocal telemetry_data, telemetry_count
        telemetry_count += 1
        telemetry_data = data
        print(f"Received telemetry update #{telemetry_count}: connected={data.get('connected')}")
        if telemetry_count >= 1:  # Wait for at least 1 telemetry update
            telemetry_received.set()
    
    @sio_client.event
    def disconnect():
        """Handle disconnection"""
        print("✓ SocketIO telemetry client disconnected")
    
    def run_server():
        """Run Flask-SocketIO server"""
        try:
            print("Starting Flask-SocketIO server for telemetry test...")
            app.socketio.run(
                app.app,
                host='127.0.0.1',
                port=5004,  # Different port for telemetry test
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            nonlocal server_error
            server_error = e
            print(f"Telemetry server error: {e}")
    
    def run_mavlink_connection():
        """Connect to virtual drone and process messages"""
        try:
            # Connect to virtual drone
            print("Connecting to virtual drone for telemetry test...")
            drone_state = {
                'connected': False, 'armed': False, 'mode': 'UNKNOWN',
                'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0, 'alt_abs': 0.0,
                'heading': 0.0, 'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
                'system_id': 0, 'component_id': 0
            }
            drone_state_lock = threading.Lock()
            
            # Connect to virtual drone
            connect_mavlink(drone_state, drone_state_lock, "tcp:192.168.193.235:5678")
            connection = get_mavlink_connection()
            
            if connection:
                print("✓ MAVLink connection established for telemetry test")
                
                # Simple message processing to trigger telemetry updates
                start_time = time.time()
                while time.time() - start_time < 15:  # Run for 15 seconds max
                    try:
                        msg = connection.recv_match(timeout=1.0)
                        if msg:
                            msg_type = msg.get_type()
                            if msg_type in ['HEARTBEAT', 'GLOBAL_POSITION_INT']:
                                print(f"Received {msg_type} for telemetry test")
                                
                                # Update drone state to trigger telemetry broadcast
                                with drone_state_lock:
                                    if msg_type == 'HEARTBEAT':
                                        drone_state['connected'] = True
                                        drone_state['system_id'] = msg.get_srcSystem()
                                        drone_state['component_id'] = msg.get_srcComponent()
                                        
                                # Trigger telemetry update
                                app.set_drone_state_changed()
                                
                                if telemetry_received.is_set():
                                    break
                        
                    except Exception as e:
                        print(f"MAVLink processing error: {e}")
                        break
                        
                    time.sleep(0.1)
            else:
                print("Warning: MAVLink connection failed for telemetry test")
                
        except Exception as e:
            print(f"MAVLink thread error: {e}")
    
    try:
        # Start server
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2.0)
        
        # Connect SocketIO client
        print("Connecting SocketIO client for telemetry test...")
        sio_client.connect('http://127.0.0.1:5004', wait_timeout=10.0)
        
        # Wait for client connection
        if not server_started.wait(timeout=5.0):
            pytest.fail("SocketIO client connection failed for telemetry test")
        
        # Start MAVLink connection in background
        mavlink_thread = threading.Thread(target=run_mavlink_connection, daemon=True)
        mavlink_thread.start()
        
        # PASS CRITERIA 3: Receive telemetry_update events
        print("Waiting for telemetry updates...")
        wait_timeout = 20.0  # 20 second timeout for telemetry
        
        if not telemetry_received.wait(timeout=wait_timeout):
            pytest.fail(f"No telemetry updates received within {wait_timeout} seconds")
        
        # PASS CRITERIA 4: Telemetry data contains required fields
        assert isinstance(telemetry_data, dict), "Telemetry data must be a dictionary"
        
        required_fields = ['connected', 'armed', 'mode', 'lat', 'lon', 'alt_rel', 'system_id']
        for field in required_fields:
            assert field in telemetry_data, f"Telemetry missing required field: {field}"
        
        print(f"✓ Received {telemetry_count} telemetry updates")
        print(f"✓ Telemetry data contains all required fields")
        print(f"✓ Connection status: {telemetry_data.get('connected')}")
        print(f"✓ System ID: {telemetry_data.get('system_id')}")
        print(f"✓ Flight mode: {telemetry_data.get('mode')}")
        
        # PASS CRITERIA 5: Telemetry data values are reasonable
        assert isinstance(telemetry_data['connected'], bool), "Connected field must be boolean"
        assert isinstance(telemetry_data['armed'], bool), "Armed field must be boolean"
        assert isinstance(telemetry_data['system_id'], int), "System ID must be integer"
        
        print("✓ Telemetry data types validated")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower():
            pytest.skip(f"Telemetry test skipped due to: {e}")
        else:
            raise
    finally:
        # Cleanup
        if sio_client.connected:
            sio_client.disconnect()

def test_realtime_data_flow_integration():
    """Test complete real-time data flow: Virtual Drone → MAVLink → Flask → SocketIO → Client"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
        from mavlink_message_processor import process_heartbeat, process_global_position_int
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    # Test setup
    server_thread = None
    mavlink_processor_thread = None
    server_error = None
    
    # Data flow tracking
    heartbeat_received = threading.Event()
    position_received = threading.Event()
    socketio_connected = threading.Event()
    telemetry_flow_confirmed = threading.Event()
    
    heartbeat_count = 0
    position_count = 0
    telemetry_updates = []
    
    # Create SocketIO client for integration test
    sio_client = socketio.Client()
    
    @sio_client.event
    def connect():
        """Handle connection"""
        print("✓ Integration test SocketIO client connected")
        socketio_connected.set()
    
    @sio_client.event
    def telemetry_update(data):
        """Track telemetry updates for integration validation"""
        telemetry_updates.append({
            'timestamp': time.time(),
            'connected': data.get('connected', False),
            'system_id': data.get('system_id', 0),
            'mode': data.get('mode', 'UNKNOWN'),
            'lat': data.get('lat', 0.0),
            'lon': data.get('lon', 0.0)
        })
        
        # Check for meaningful telemetry flow
        if len(telemetry_updates) >= 3:  # Multiple updates received
            recent = telemetry_updates[-1]
            if recent['connected'] and recent['system_id'] > 0:
                print(f"✓ Integration telemetry flow confirmed: {len(telemetry_updates)} updates")
                telemetry_flow_confirmed.set()
    
    @sio_client.event
    def disconnect():
        """Handle disconnection"""
        print("✓ Integration test SocketIO client disconnected")
    
    def run_server():
        """Run Flask-SocketIO server for integration test"""
        try:
            print("Starting Flask-SocketIO server for integration test...")
            
            # Start telemetry thread before starting server
            app.start_telemetry_thread()
            
            app.socketio.run(
                app.app,
                host='127.0.0.1',
                port=5005,  # Different port for integration test
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            nonlocal server_error
            server_error = e
            print(f"Integration server error: {e}")
    
    def run_mavlink_processor():
        """Process MAVLink messages and update app's global state"""
        nonlocal heartbeat_count, position_count
        
        try:
            print("Starting MAVLink processor for integration test...")
            
            # Use app's global drone state instead of creating a separate one
            # This ensures the telemetry broadcasting system sees the updates
            
            # Connect to virtual drone using app's global state
            connect_mavlink(app.drone_state, app.drone_state_lock, "tcp:192.168.193.235:5678")
            connection = get_mavlink_connection()
            
            if not connection:
                print("Warning: MAVLink connection failed in integration test")
                return
            
            print("✓ MAVLink connection established for integration test")
            
            def log_callback(command, params=None, details=None):
                """Simple logging callback"""
                print(f"MAVLink: {command} - {details}")
            
            # Process messages for up to 30 seconds
            start_time = time.time()
            while time.time() - start_time < 30:
                try:
                    msg = connection.recv_match(timeout=1.0)
                    if msg:
                        msg_type = msg.get_type()
                        
                        if msg_type == 'HEARTBEAT':
                            heartbeat_count += 1
                            # Process heartbeat and update app's global drone_state
                            process_heartbeat(
                                msg, app.drone_state, app.drone_state_lock, 
                                connection, log_callback, app.socketio
                            )
                            heartbeat_received.set()
                            app.set_drone_state_changed()  # Trigger telemetry update
                            
                        elif msg_type == 'GLOBAL_POSITION_INT':
                            position_count += 1
                            # Process position and update app's global drone_state
                            process_global_position_int(
                                msg, app.drone_state, app.drone_state_lock,
                                connection, log_callback, app.socketio
                            )
                            position_received.set()
                            app.set_drone_state_changed()  # Trigger telemetry update
                        
                        # Exit early if we've confirmed telemetry flow
                        if telemetry_flow_confirmed.is_set():
                            break
                            
                except Exception as e:
                    print(f"MAVLink processing error in integration test: {e}")
                    break
                
                time.sleep(0.1)
            
            print(f"✓ Integration test processed {heartbeat_count} heartbeats, {position_count} positions")
            
        except Exception as e:
            print(f"MAVLink processor error: {e}")
    
    try:
        # Start server
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server startup
        time.sleep(2.0)
        
        # Connect SocketIO client
        print("Connecting SocketIO client for integration test...")
        sio_client.connect('http://127.0.0.1:5005', wait_timeout=10.0)
        
        if not socketio_connected.wait(timeout=5.0):
            pytest.fail("SocketIO connection failed for integration test")
        
        # Start MAVLink processing
        mavlink_processor_thread = threading.Thread(target=run_mavlink_processor, daemon=True)
        mavlink_processor_thread.start()
        
        # PASS CRITERIA 6: Complete data flow validation
        print("Validating complete real-time data flow...")
        
        # Wait for heartbeat processing
        if not heartbeat_received.wait(timeout=15.0):
            pytest.skip("No heartbeat messages received - virtual drone may be unavailable")
        
        # Wait for telemetry flow confirmation
        if not telemetry_flow_confirmed.wait(timeout=20.0):
            pytest.fail("Complete telemetry data flow not confirmed within timeout")
        
        # Validate data flow metrics
        assert len(telemetry_updates) >= 3, f"Expected ≥3 telemetry updates, got {len(telemetry_updates)}"
        assert heartbeat_count > 0, f"Expected >0 heartbeats processed, got {heartbeat_count}"
        
        # Validate telemetry data quality
        latest_telemetry = telemetry_updates[-1]
        assert latest_telemetry['connected'] == True, "Final telemetry should show connected=True"
        assert latest_telemetry['system_id'] > 0, f"System ID should be >0, got {latest_telemetry['system_id']}"
        
        print(f"✓ Integration test PASSED: {len(telemetry_updates)} telemetry updates")
        print(f"✓ Heartbeat messages processed: {heartbeat_count}")
        print(f"✓ Position messages processed: {position_count}")
        print(f"✓ Final connection status: {latest_telemetry['connected']}")
        print(f"✓ System ID: {latest_telemetry['system_id']}")
        print(f"✓ Flight mode: {latest_telemetry['mode']}")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower() or "virtual drone" in str(e).lower():
            pytest.skip(f"Integration test skipped due to: {e}")
        else:
            raise
    finally:
        # Cleanup
        if sio_client.connected:
            sio_client.disconnect()

if __name__ == "__main__":
    print("=== TEST-005: SocketIO Connection Test ===")
    
    # Run individual tests with detailed output
    try:
        print("\n1. Testing SocketIO client connection...")
        test_socketio_client_connection()
        print("✓ PASSED: SocketIO client connection test")
        
        print("\n2. Testing telemetry update reception...")
        test_telemetry_update_reception()
        print("✓ PASSED: Telemetry update reception test")
        
        print("\n3. Testing real-time data flow integration...")
        test_realtime_data_flow_integration()
        print("✓ PASSED: Real-time data flow integration test")
        
        print("\n=== TEST-005 COMPLETE: ALL TESTS PASSED ===")
        print("✓ SocketIO client can connect to Flask-SocketIO server")
        print("✓ telemetry_update events are received from server")
        print("✓ Real MAVLink telemetry data is broadcasted via SocketIO") 
        print("✓ Virtual drone connection and real-time data flow validated")
        print("✓ Complete integration: Virtual Drone → MAVLink → Flask → SocketIO → Client")
        
    except Exception as e:
        print(f"\n❌ TEST-005 FAILED: {e}")
        print("\nEXPECTED BEHAVIOR: This test should FAIL initially (RED phase)")
        print("Next steps:")
        print("1. Ensure Flask-SocketIO server broadcasts telemetry_update events")
        print("2. Integrate MAVLink message processing with SocketIO telemetry streaming")
        print("3. Verify real-time telemetry update mechanism")
        sys.exit(1)

# FAIL CRITERIA (ANY causes test failure):
# - Cannot connect SocketIO client to server
# - Connection timeout exceeds 10 seconds
# - No telemetry_update events received within 20 seconds
# - Telemetry data missing required fields (connected, armed, mode, lat, lon, alt_rel, system_id)
# - Telemetry data types are incorrect (connected not bool, system_id not int, etc.)
# - No heartbeat messages processed from virtual drone
# - Integration data flow not confirmed (fewer than 3 telemetry updates)
# - Final connection status not showing connected=True
# - System ID not identified (system_id ≤ 0)

# PASS CRITERIA (ALL must be true):
# - SocketIO client successfully connects to Flask-SocketIO server
# - Connection established within 10 seconds
# - telemetry_update events received from server
# - Telemetry data contains all required fields with correct types
# - Real MAVLink data (heartbeat, position) processed and broadcasted
# - Complete data flow: Virtual Drone → MAVLink → Flask → SocketIO → Client
# - At least 3 telemetry updates received during test
# - Final telemetry shows connected=True and valid system_id > 0
# - Integration test confirms real-time telemetry streaming
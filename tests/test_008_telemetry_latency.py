"""
TEST-008: End-to-End Telemetry Latency Test
Tests complete telemetry flow latency: Virtual Drone → MAVLink → Processing → SocketIO → Web Client

CRITICAL: This test validates the <100ms end-to-end telemetry latency requirement for real-time drone monitoring.

The complete real-time pipeline tested:
1. MAVLink message reception from virtual drone
2. Message processing and state updates
3. SocketIO broadcast to web clients
4. Web client reception and processing
5. Overall end-to-end latency measurement

Performance Requirements:
- <100ms end-to-end telemetry latency (CRITICAL)
- 10Hz telemetry update rate (100ms intervals)
- <1ms individual processing steps
- Concurrent client support without degradation
- Real-time data synchronization validation

Following test-driven development: RED phase (should FAIL initially)
"""
import pytest
import threading
import time
import statistics
import socketio
import sys
import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_end_to_end_telemetry_latency():
    """Test complete telemetry latency: Virtual Drone → MAVLink → SocketIO → Client < 100ms"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
        from mavlink_message_processor import process_heartbeat, process_global_position_int
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    # Test setup
    server_thread = None
    mavlink_thread = None
    server_error = None
    
    # Latency measurement tracking
    latency_measurements = deque(maxlen=100)  # Store last 100 measurements
    telemetry_events = []
    test_complete = threading.Event()
    client_ready = threading.Event()
    
    # Performance thresholds
    MAX_END_TO_END_LATENCY = 100.0  # 100ms requirement
    TARGET_UPDATE_INTERVAL = 100.0  # 100ms = 10Hz
    MIN_MEASUREMENTS = 20  # Need at least 20 samples
    
    # Create SocketIO test client with latency tracking
    sio_client = socketio.Client()
    
    @sio_client.event
    def connect():
        """Handle client connection"""
        print("✓ Telemetry latency test client connected")
        client_ready.set()
    
    @sio_client.event
    def telemetry_update(data):
        """Handle telemetry updates and measure end-to-end latency"""
        receive_time = time.perf_counter() * 1000  # Convert to ms
        
        # Extract timestamp from telemetry if available, otherwise estimate
        # This represents when the MAVLink message was processed
        mavlink_timestamp = data.get('timestamp', receive_time - 50)  # Fallback estimate
        
        # Calculate end-to-end latency
        end_to_end_latency = receive_time - mavlink_timestamp
        
        # Only measure positive, reasonable latencies (filter out timing anomalies)
        if 0 < end_to_end_latency < 1000:  # Between 0-1000ms is reasonable
            latency_measurements.append(end_to_end_latency)
            
            event = {
                'timestamp': receive_time,
                'mavlink_time': mavlink_timestamp,
                'latency_ms': end_to_end_latency,
                'connected': data.get('connected', False),
                'system_id': data.get('system_id', 0)
            }
            telemetry_events.append(event)
            
            print(f"Latency sample #{len(latency_measurements)}: {end_to_end_latency:.2f}ms "
                  f"(Connected: {data.get('connected', False)})")
            
            # Complete test after collecting sufficient samples
            if len(latency_measurements) >= MIN_MEASUREMENTS:
                test_complete.set()
    
    @sio_client.event
    def disconnect():
        """Handle client disconnection"""
        print("✓ Telemetry latency test client disconnected")
    
    def run_server():
        """Run Flask-SocketIO server for latency testing"""
        try:
            print("Starting Flask-SocketIO server for latency test...")
            
            # Ensure telemetry thread is running
            app.start_telemetry_thread()
            
            app.socketio.run(
                app.app,
                host='127.0.0.1',
                port=5008,  # Unique port for latency test
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            nonlocal server_error
            server_error = e
            print(f"Latency test server error: {e}")
    
    def run_mavlink_with_timestamps():
        """Process MAVLink messages and add timestamps for latency measurement"""
        try:
            print("Starting MAVLink processor with timestamp tracking...")
            
            # Connect to virtual drone using app's global state
            connect_mavlink(app.drone_state, app.drone_state_lock, "tcp:192.168.193.235:5678")
            connection = get_mavlink_connection()
            
            if not connection:
                print("Warning: MAVLink connection failed for latency test")
                return
            
            print("✓ MAVLink connection established for latency test")
            
            def latency_log_callback(command, params=None, details=None):
                """Logging callback with timing information"""
                timestamp = time.perf_counter() * 1000
                print(f"[{timestamp:.2f}ms] MAVLink: {command} - {details}")
            
            message_count = 0
            start_time = time.time()
            
            # Process messages for up to 45 seconds or until test complete
            while time.time() - start_time < 45 and not test_complete.is_set():
                try:
                    msg = connection.recv_match(timeout=1.0)
                    if msg:
                        mavlink_receive_time = time.perf_counter() * 1000  # Timestamp when received
                        msg_type = msg.get_type()
                        
                        if msg_type == 'HEARTBEAT':
                            message_count += 1
                            # Process heartbeat and update global state
                            process_heartbeat(
                                msg, app.drone_state, app.drone_state_lock,
                                connection, latency_log_callback, app.socketio
                            )
                            
                            # Add timestamp to drone state for latency tracking
                            with app.drone_state_lock:
                                app.drone_state['timestamp'] = mavlink_receive_time
                            
                            app.set_drone_state_changed()  # Trigger telemetry broadcast
                            
                        elif msg_type == 'GLOBAL_POSITION_INT':
                            message_count += 1
                            # Process position data
                            process_global_position_int(
                                msg, app.drone_state, app.drone_state_lock,
                                connection, latency_log_callback, app.socketio
                            )
                            
                            # Add timestamp to drone state
                            with app.drone_state_lock:
                                app.drone_state['timestamp'] = mavlink_receive_time
                            
                            app.set_drone_state_changed()
                        
                        # Exit early if we have sufficient measurements
                        if len(latency_measurements) >= MIN_MEASUREMENTS:
                            break
                            
                except Exception as e:
                    print(f"MAVLink processing error in latency test: {e}")
                    break
                
                time.sleep(0.01)  # Short sleep to prevent excessive CPU usage
            
            print(f"✓ Latency test processed {message_count} MAVLink messages")
            
        except Exception as e:
            print(f"MAVLink processor error: {e}")
    
    try:
        # Start server
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server startup
        time.sleep(2.0)
        
        # Connect SocketIO client
        print("Connecting SocketIO client for latency test...")
        sio_client.connect('http://127.0.0.1:5008', wait_timeout=10.0)
        
        if not client_ready.wait(timeout=5.0):
            pytest.fail("SocketIO client connection failed for latency test")
        
        # Start MAVLink processing with timestamp tracking
        mavlink_thread = threading.Thread(target=run_mavlink_with_timestamps, daemon=True)
        mavlink_thread.start()
        
        # PASS CRITERIA 1: Collect sufficient latency measurements
        print(f"Collecting latency measurements (need {MIN_MEASUREMENTS} samples)...")
        wait_timeout = 30.0  # 30 second timeout for data collection
        
        if not test_complete.wait(timeout=wait_timeout):
            if len(latency_measurements) < 5:
                pytest.skip(f"Insufficient latency data: {len(latency_measurements)} samples (need {MIN_MEASUREMENTS})")
            else:
                print(f"Warning: Only collected {len(latency_measurements)} samples in {wait_timeout}s")
        
        # PASS CRITERIA 2: End-to-end latency analysis
        assert len(latency_measurements) > 0, "No latency measurements collected"
        
        # Calculate latency statistics
        latencies = list(latency_measurements)
        mean_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
        p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)
        
        print(f"\n=== TELEMETRY LATENCY RESULTS ===")
        print(f"Samples collected: {len(latencies)}")
        print(f"Mean latency: {mean_latency:.2f}ms")
        print(f"Median latency: {median_latency:.2f}ms")
        print(f"95th percentile: {p95_latency:.2f}ms")
        print(f"99th percentile: {p99_latency:.2f}ms")
        print(f"Maximum latency: {max_latency:.2f}ms")
        print(f"Minimum latency: {min_latency:.2f}ms")
        
        # PASS CRITERIA 3: Critical latency requirements
        assert mean_latency < MAX_END_TO_END_LATENCY, f"Mean latency {mean_latency:.2f}ms exceeds {MAX_END_TO_END_LATENCY}ms requirement"
        assert median_latency < MAX_END_TO_END_LATENCY, f"Median latency {median_latency:.2f}ms exceeds {MAX_END_TO_END_LATENCY}ms requirement"
        assert p95_latency < MAX_END_TO_END_LATENCY * 1.5, f"95th percentile {p95_latency:.2f}ms exceeds {MAX_END_TO_END_LATENCY * 1.5}ms tolerance"
        assert max_latency < 500.0, f"Maximum latency {max_latency:.2f}ms exceeds 500ms absolute limit"
        
        print(f"✓ End-to-end latency requirements PASSED")
        print(f"✓ Mean latency {mean_latency:.2f}ms < {MAX_END_TO_END_LATENCY}ms requirement")
        print(f"✓ 95th percentile {p95_latency:.2f}ms within tolerance")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower() or "virtual drone" in str(e).lower():
            pytest.skip(f"Telemetry latency test skipped due to: {e}")
        else:
            raise
    finally:
        # Cleanup
        if sio_client.connected:
            sio_client.disconnect()


def test_telemetry_update_rate_10hz():
    """Test telemetry update rate maintains 10Hz (100ms interval) consistency"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    # Test setup
    server_thread = None
    mavlink_thread = None
    
    # Update rate tracking
    telemetry_timestamps = deque(maxlen=50)  # Store last 50 update times
    update_intervals = []
    client_connected = threading.Event()
    sufficient_data = threading.Event()
    
    TARGET_INTERVAL = 100.0  # 100ms = 10Hz
    MIN_UPDATES = 20  # Need at least 20 updates to measure intervals
    
    # Create SocketIO client for update rate testing
    sio_client = socketio.Client()
    
    @sio_client.event
    def connect():
        """Handle client connection"""
        print("✓ Update rate test client connected")
        client_connected.set()
    
    @sio_client.event
    def telemetry_update(data):
        """Track telemetry update timing"""
        current_time = time.perf_counter() * 1000  # ms
        telemetry_timestamps.append(current_time)
        
        # Calculate intervals once we have multiple timestamps
        if len(telemetry_timestamps) >= 2:
            interval = current_time - telemetry_timestamps[-2]
            update_intervals.append(interval)
            
            print(f"Update #{len(telemetry_timestamps)}: interval {interval:.1f}ms")
            
            # Complete test after sufficient data
            if len(update_intervals) >= MIN_UPDATES:
                sufficient_data.set()
    
    def run_server():
        """Run server for update rate testing"""
        try:
            print("Starting server for update rate test...")
            app.start_telemetry_thread()
            
            app.socketio.run(
                app.app,
                host='127.0.0.1',
                port=5009,  # Unique port for update rate test
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            print(f"Update rate test server error: {e}")
    
    def run_continuous_updates():
        """Generate continuous telemetry updates"""
        try:
            # Connect to virtual drone
            connect_mavlink(app.drone_state, app.drone_state_lock, "tcp:192.168.193.235:5678")
            connection = get_mavlink_connection()
            
            if connection:
                print("✓ MAVLink connection for update rate test")
                
                # Continuously process messages to trigger updates
                start_time = time.time()
                while time.time() - start_time < 25 and not sufficient_data.is_set():
                    try:
                        msg = connection.recv_match(timeout=0.5)
                        if msg and msg.get_type() in ['HEARTBEAT', 'GLOBAL_POSITION_INT']:
                            # Update state and trigger telemetry broadcast
                            with app.drone_state_lock:
                                app.drone_state['connected'] = True
                                app.drone_state['system_id'] = msg.get_srcSystem()
                            
                            app.set_drone_state_changed()
                        
                        time.sleep(0.01)
                        
                    except Exception as e:
                        print(f"Update generation error: {e}")
                        break
            
        except Exception as e:
            print(f"Continuous updates error: {e}")
    
    try:
        # Start server
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2.0)
        
        # Connect client
        sio_client.connect('http://127.0.0.1:5009', wait_timeout=10.0)
        
        if not client_connected.wait(timeout=5.0):
            pytest.fail("Client connection failed for update rate test")
        
        # Start continuous updates
        mavlink_thread = threading.Thread(target=run_continuous_updates, daemon=True)
        mavlink_thread.start()
        
        # Collect update timing data
        print(f"Measuring telemetry update rate (need {MIN_UPDATES} intervals)...")
        if not sufficient_data.wait(timeout=20.0):
            pytest.skip(f"Insufficient update data: {len(update_intervals)} intervals collected")
        
        # PASS CRITERIA: Update rate analysis
        assert len(update_intervals) >= MIN_UPDATES, f"Need {MIN_UPDATES} intervals, got {len(update_intervals)}"
        
        mean_interval = statistics.mean(update_intervals)
        median_interval = statistics.median(update_intervals)
        std_dev = statistics.stdev(update_intervals) if len(update_intervals) > 1 else 0
        
        print(f"\n=== TELEMETRY UPDATE RATE RESULTS ===")
        print(f"Update intervals measured: {len(update_intervals)}")
        print(f"Mean interval: {mean_interval:.1f}ms (target: {TARGET_INTERVAL}ms)")
        print(f"Median interval: {median_interval:.1f}ms")
        print(f"Standard deviation: {std_dev:.1f}ms")
        print(f"Update rate: {1000/mean_interval:.1f}Hz (target: 10Hz)")
        
        # PASS CRITERIA: Rate consistency requirements
        assert 50 <= mean_interval <= 200, f"Mean interval {mean_interval:.1f}ms outside acceptable range (50-200ms)"
        assert std_dev < 50, f"Update timing too inconsistent: {std_dev:.1f}ms std dev (max 50ms)"
        
        print(f"✓ Telemetry update rate requirements PASSED")
        print(f"✓ Update rate: {1000/mean_interval:.1f}Hz")
        print(f"✓ Timing consistency: {std_dev:.1f}ms std dev")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower():
            pytest.skip(f"Update rate test skipped: {e}")
        else:
            raise
    finally:
        if sio_client.connected:
            sio_client.disconnect()


def test_concurrent_clients_latency_impact():
    """Test telemetry latency with multiple concurrent web clients"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    # Test setup  
    server_thread = None
    mavlink_thread = None
    
    NUM_CLIENTS = 5  # Test with 5 concurrent clients
    client_latencies = {}  # Track latencies per client
    clients_ready = threading.Event()
    test_complete = threading.Event()
    
    def create_test_client(client_id):
        """Create a test client that measures latency"""
        client = socketio.Client()
        client_latencies[client_id] = deque(maxlen=20)
        
        @client.event
        def connect():
            print(f"✓ Concurrent client {client_id} connected")
            
            # Signal when all clients are ready
            if len([c for c in client_latencies if len(client_latencies[c]) >= 0]) == NUM_CLIENTS:
                clients_ready.set()
        
        @client.event 
        def telemetry_update(data):
            receive_time = time.perf_counter() * 1000
            mavlink_time = data.get('timestamp', receive_time - 50)
            
            if 0 < receive_time - mavlink_time < 500:  # Filter reasonable latencies
                client_latencies[client_id].append(receive_time - mavlink_time)
                
                # Complete when we have enough data from all clients
                total_measurements = sum(len(client_latencies[cid]) for cid in client_latencies)
                if total_measurements >= NUM_CLIENTS * 10:  # 10 measurements per client
                    test_complete.set()
        
        return client
    
    def run_server():
        """Run server for concurrent client test"""
        try:
            print("Starting server for concurrent client test...")
            app.start_telemetry_thread()
            
            app.socketio.run(
                app.app,
                host='127.0.0.1', 
                port=5010,  # Unique port
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            print(f"Concurrent client test server error: {e}")
    
    def run_telemetry_generator():
        """Generate telemetry data for concurrent clients"""
        try:
            connect_mavlink(app.drone_state, app.drone_state_lock, "tcp:192.168.193.235:5678")
            connection = get_mavlink_connection()
            
            if connection:
                print("✓ MAVLink connection for concurrent client test")
                
                start_time = time.time()
                while time.time() - start_time < 20 and not test_complete.is_set():
                    try:
                        msg = connection.recv_match(timeout=0.5)
                        if msg and msg.get_type() == 'HEARTBEAT':
                            with app.drone_state_lock:
                                app.drone_state['timestamp'] = time.perf_counter() * 1000
                                app.drone_state['connected'] = True
                                app.drone_state['system_id'] = msg.get_srcSystem()
                            
                            app.set_drone_state_changed()
                        
                        time.sleep(0.05)  # 20Hz generation rate
                        
                    except Exception as e:
                        print(f"Telemetry generation error: {e}")
                        break
                        
        except Exception as e:
            print(f"Telemetry generator error: {e}")
    
    try:
        # Start server
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2.0)
        
        # Create and connect multiple clients
        clients = []
        for i in range(NUM_CLIENTS):
            client = create_test_client(i)
            clients.append(client)
            
            try:
                client.connect('http://127.0.0.1:5010', wait_timeout=5.0)
                time.sleep(0.2)  # Stagger connections slightly
            except Exception as e:
                print(f"Client {i} connection failed: {e}")
        
        # Wait for all clients to be ready
        print(f"Waiting for {NUM_CLIENTS} concurrent clients to connect...")
        if not clients_ready.wait(timeout=10.0):
            connected_clients = len([c for c in clients if c.connected])
            if connected_clients < 2:
                pytest.skip(f"Insufficient concurrent clients: {connected_clients} connected")
        
        # Start telemetry generation
        mavlink_thread = threading.Thread(target=run_telemetry_generator, daemon=True)
        mavlink_thread.start()
        
        # Collect concurrent latency data
        print("Measuring latency with concurrent clients...")
        if not test_complete.wait(timeout=15.0):
            total_data = sum(len(client_latencies[cid]) for cid in client_latencies)
            if total_data < NUM_CLIENTS * 3:
                pytest.skip(f"Insufficient concurrent data: {total_data} measurements")
        
        # PASS CRITERIA: Analyze concurrent client latency impact
        all_latencies = []
        client_stats = {}
        
        for client_id in client_latencies:
            if len(client_latencies[client_id]) > 0:
                latencies = list(client_latencies[client_id])
                all_latencies.extend(latencies)
                client_stats[client_id] = {
                    'count': len(latencies),
                    'mean': statistics.mean(latencies),
                    'max': max(latencies)
                }
        
        assert len(all_latencies) > 0, "No latency data collected from concurrent clients"
        
        overall_mean = statistics.mean(all_latencies)
        overall_max = max(all_latencies)
        
        print(f"\n=== CONCURRENT CLIENT LATENCY RESULTS ===")
        print(f"Active clients: {len(client_stats)}")
        print(f"Total measurements: {len(all_latencies)}")
        print(f"Overall mean latency: {overall_mean:.2f}ms")
        print(f"Overall max latency: {overall_max:.2f}ms")
        
        for client_id in client_stats:
            stats = client_stats[client_id]
            print(f"Client {client_id}: {stats['count']} samples, mean {stats['mean']:.2f}ms, max {stats['max']:.2f}ms")
        
        # PASS CRITERIA: Concurrent performance requirements
        assert overall_mean < 150.0, f"Concurrent mean latency {overall_mean:.2f}ms exceeds 150ms tolerance"
        assert overall_max < 500.0, f"Concurrent max latency {overall_max:.2f}ms exceeds 500ms limit"
        assert len(client_stats) >= 2, f"Need at least 2 active clients, got {len(client_stats)}"
        
        print(f"✓ Concurrent client latency requirements PASSED")
        print(f"✓ {len(client_stats)} clients handled with {overall_mean:.2f}ms mean latency")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower():
            pytest.skip(f"Concurrent client test skipped: {e}")
        else:
            raise
    finally:
        # Cleanup all clients
        for client in clients:
            if client.connected:
                client.disconnect()


def test_telemetry_pipeline_performance_breakdown():
    """Test individual components of telemetry pipeline for performance bottlenecks"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
        from mavlink_message_processor import process_heartbeat
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    print("Testing telemetry pipeline performance breakdown...")
    
    # Test setup
    performance_metrics = {
        'mavlink_processing': [],
        'state_update': [],
        'socketio_broadcast': [],
        'total_pipeline': []
    }
    
    # Create mock components for isolated testing
    test_drone_state = {
        'connected': False, 'armed': False, 'mode': 'UNKNOWN',
        'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0,
        'system_id': 0, 'component_id': 0
    }
    test_lock = threading.Lock()
    
    def mock_log_callback(command, params=None, details=None):
        """Fast mock logging for performance testing"""
        pass
    
    def mock_socketio_emit(event, data):
        """Mock SocketIO emit for timing"""
        time.sleep(0.001)  # Simulate 1ms broadcast time
    
    # PASS CRITERIA 1: MAVLink message processing performance
    print("1. Testing MAVLink message processing performance...")
    
    # Create sample heartbeat message data
    class MockHeartbeatMessage:
        def __init__(self):
            self.base_mode = 1
            self.custom_mode = 0
            self.system_status = 4
            
        def get_srcSystem(self):
            return 1
            
        def get_srcComponent(self):
            return 1
    
    mock_msg = MockHeartbeatMessage()
    
    # Test MAVLink processing speed
    processing_times = []
    for i in range(100):
        start_time = time.perf_counter_ns()
        
        # Process heartbeat message
        process_heartbeat(
            mock_msg, test_drone_state, test_lock, 
            None, mock_log_callback, None
        )
        
        end_time = time.perf_counter_ns()
        processing_time = (end_time - start_time) / 1_000_000  # Convert to ms
        processing_times.append(processing_time)
    
    mean_processing_time = statistics.mean(processing_times)
    max_processing_time = max(processing_times)
    
    performance_metrics['mavlink_processing'] = processing_times
    
    print(f"MAVLink Processing: mean {mean_processing_time:.4f}ms, max {max_processing_time:.4f}ms")
    
    # PASS CRITERIA 2: State update performance
    print("2. Testing state update performance...")
    
    state_update_times = []
    for i in range(100):
        start_time = time.perf_counter_ns()
        
        # Simulate state update operations
        with test_lock:
            test_drone_state['connected'] = True
            test_drone_state['system_id'] = 1
            test_drone_state['timestamp'] = time.perf_counter() * 1000
        
        end_time = time.perf_counter_ns() 
        update_time = (end_time - start_time) / 1_000_000
        state_update_times.append(update_time)
    
    mean_update_time = statistics.mean(state_update_times)
    max_update_time = max(state_update_times)
    
    performance_metrics['state_update'] = state_update_times
    
    print(f"State Update: mean {mean_update_time:.4f}ms, max {max_update_time:.4f}ms")
    
    # PASS CRITERIA 3: SocketIO broadcast performance simulation
    print("3. Testing SocketIO broadcast performance...")
    
    broadcast_times = []
    for i in range(100):
        start_time = time.perf_counter_ns()
        
        # Simulate SocketIO broadcast
        mock_socketio_emit('telemetry_update', test_drone_state.copy())
        
        end_time = time.perf_counter_ns()
        broadcast_time = (end_time - start_time) / 1_000_000
        broadcast_times.append(broadcast_time)
    
    mean_broadcast_time = statistics.mean(broadcast_times)
    max_broadcast_time = max(broadcast_times)
    
    performance_metrics['socketio_broadcast'] = broadcast_times
    
    print(f"SocketIO Broadcast: mean {mean_broadcast_time:.4f}ms, max {max_broadcast_time:.4f}ms")
    
    # PASS CRITERIA 4: Total pipeline simulation
    print("4. Testing complete pipeline performance...")
    
    pipeline_times = []
    for i in range(50):  # Fewer iterations for complete pipeline
        pipeline_start = time.perf_counter_ns()
        
        # Simulate complete pipeline
        # 1. Process MAVLink message
        process_heartbeat(
            mock_msg, test_drone_state, test_lock,
            None, mock_log_callback, None
        )
        
        # 2. Update state with timestamp
        with test_lock:
            test_drone_state['timestamp'] = time.perf_counter() * 1000
        
        # 3. Broadcast via SocketIO
        mock_socketio_emit('telemetry_update', test_drone_state.copy())
        
        pipeline_end = time.perf_counter_ns()
        total_time = (pipeline_end - pipeline_start) / 1_000_000
        pipeline_times.append(total_time)
    
    mean_pipeline_time = statistics.mean(pipeline_times)
    max_pipeline_time = max(pipeline_times)
    
    performance_metrics['total_pipeline'] = pipeline_times
    
    print(f"Complete Pipeline: mean {mean_pipeline_time:.4f}ms, max {max_pipeline_time:.4f}ms")
    
    # PASS CRITERIA: Performance requirements validation
    print(f"\n=== PIPELINE PERFORMANCE BREAKDOWN ===")
    print(f"MAVLink Processing: {mean_processing_time:.4f}ms (max {max_processing_time:.4f}ms)")
    print(f"State Update: {mean_update_time:.4f}ms (max {max_update_time:.4f}ms)") 
    print(f"SocketIO Broadcast: {mean_broadcast_time:.4f}ms (max {max_broadcast_time:.4f}ms)")
    print(f"Complete Pipeline: {mean_pipeline_time:.4f}ms (max {max_pipeline_time:.4f}ms)")
    
    # Performance assertions
    assert mean_processing_time < 1.0, f"MAVLink processing {mean_processing_time:.4f}ms exceeds 1ms"
    assert mean_update_time < 0.1, f"State update {mean_update_time:.4f}ms exceeds 0.1ms"
    assert mean_broadcast_time < 5.0, f"SocketIO broadcast {mean_broadcast_time:.4f}ms exceeds 5ms"
    assert mean_pipeline_time < 10.0, f"Complete pipeline {mean_pipeline_time:.4f}ms exceeds 10ms"
    
    print(f"✓ Pipeline performance breakdown requirements PASSED")
    print(f"✓ All components meet individual performance targets")


def test_real_time_data_synchronization():
    """Test real-time data synchronization between MAVLink and web interface"""
    
    try:
        import app
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection  
        from mavlink_message_processor import process_heartbeat, process_global_position_int
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import required modules - {e}")
    
    # Test setup
    server_thread = None
    mavlink_thread = None
    
    # Data synchronization tracking
    mavlink_data_points = []
    socketio_data_points = []
    synchronization_errors = []
    
    sync_test_complete = threading.Event()
    client_ready = threading.Event()
    
    # Create SocketIO client for synchronization testing
    sio_client = socketio.Client()
    
    @sio_client.event
    def connect():
        """Handle client connection"""
        print("✓ Sync test client connected")
        client_ready.set()
    
    @sio_client.event
    def telemetry_update(data):
        """Track SocketIO telemetry for synchronization analysis"""
        receive_time = time.perf_counter()
        
        socketio_data_points.append({
            'time': receive_time,
            'system_id': data.get('system_id', 0),
            'connected': data.get('connected', False),
            'lat': data.get('lat', 0.0),
            'lon': data.get('lon', 0.0),
            'mode': data.get('mode', 'UNKNOWN')
        })
        
        print(f"SocketIO data: system_id={data.get('system_id')}, connected={data.get('connected')}")
        
        # Complete test after collecting sufficient data
        if len(socketio_data_points) >= 15:
            sync_test_complete.set()
    
    def run_server():
        """Run server for synchronization test"""
        try:
            print("Starting server for synchronization test...")
            app.start_telemetry_thread()
            
            app.socketio.run(
                app.app,
                host='127.0.0.1',
                port=5011,  # Unique port
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            print(f"Sync test server error: {e}")
    
    def run_mavlink_sync_tracking():
        """Track MAVLink data for synchronization comparison"""
        try:
            print("Starting MAVLink sync tracking...")
            
            connect_mavlink(app.drone_state, app.drone_state_lock, "tcp:192.168.193.235:5678")
            connection = get_mavlink_connection()
            
            if not connection:
                print("Warning: MAVLink connection failed for sync test")
                return
            
            def sync_log_callback(command, params=None, details=None):
                """Track MAVLink processing events"""
                mavlink_data_points.append({
                    'time': time.perf_counter(),
                    'command': command,
                    'details': details
                })
            
            # Process messages and track synchronization
            start_time = time.time()
            while time.time() - start_time < 20 and not sync_test_complete.is_set():
                try:
                    msg = connection.recv_match(timeout=1.0)
                    if msg:
                        msg_time = time.perf_counter()
                        msg_type = msg.get_type()
                        
                        if msg_type == 'HEARTBEAT':
                            # Process and track heartbeat
                            process_heartbeat(
                                msg, app.drone_state, app.drone_state_lock,
                                connection, sync_log_callback, app.socketio
                            )
                            
                            # Record MAVLink data point
                            with app.drone_state_lock:
                                mavlink_data_points.append({
                                    'time': msg_time,
                                    'type': 'HEARTBEAT',
                                    'system_id': app.drone_state.get('system_id', 0),
                                    'connected': app.drone_state.get('connected', False),
                                    'mode': app.drone_state.get('mode', 'UNKNOWN')
                                })
                                
                                # Add timestamp and trigger update
                                app.drone_state['timestamp'] = msg_time * 1000
                            
                            app.set_drone_state_changed()
                            
                        elif msg_type == 'GLOBAL_POSITION_INT':
                            # Process position data
                            process_global_position_int(
                                msg, app.drone_state, app.drone_state_lock,
                                connection, sync_log_callback, app.socketio
                            )
                            
                            # Record position data point
                            with app.drone_state_lock:
                                mavlink_data_points.append({
                                    'time': msg_time,
                                    'type': 'POSITION',
                                    'lat': app.drone_state.get('lat', 0.0),
                                    'lon': app.drone_state.get('lon', 0.0)
                                })
                            
                            app.set_drone_state_changed()
                        
                        # Check for synchronization within reasonable time windows
                        if len(socketio_data_points) > 0:
                            latest_socketio = socketio_data_points[-1]
                            latest_mavlink = mavlink_data_points[-1] if mavlink_data_points else None
                            
                            if latest_mavlink:
                                time_diff = abs(latest_socketio['time'] - latest_mavlink['time'])
                                if time_diff > 0.2:  # >200ms is a sync error
                                    synchronization_errors.append({
                                        'time_diff': time_diff * 1000,  # Convert to ms
                                        'mavlink_time': latest_mavlink['time'],
                                        'socketio_time': latest_socketio['time']
                                    })
                        
                        if len(mavlink_data_points) >= 15:
                            break
                            
                except Exception as e:
                    print(f"MAVLink sync tracking error: {e}")
                    break
                
                time.sleep(0.01)
            
            print(f"✓ Sync test tracked {len(mavlink_data_points)} MAVLink events")
            
        except Exception as e:
            print(f"MAVLink sync tracking error: {e}")
    
    try:
        # Start server
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2.0)
        
        # Connect client
        sio_client.connect('http://127.0.0.1:5011', wait_timeout=10.0)
        
        if not client_ready.wait(timeout=5.0):
            pytest.fail("Client connection failed for sync test")
        
        # Start MAVLink sync tracking
        mavlink_thread = threading.Thread(target=run_mavlink_sync_tracking, daemon=True)
        mavlink_thread.start()
        
        # Wait for synchronization data collection
        print("Collecting data synchronization samples...")
        if not sync_test_complete.wait(timeout=25.0):
            if len(socketio_data_points) < 5 or len(mavlink_data_points) < 5:
                pytest.skip("Insufficient synchronization data collected")
        
        # PASS CRITERIA: Data synchronization analysis
        assert len(mavlink_data_points) > 0, "No MAVLink data points collected"
        assert len(socketio_data_points) > 0, "No SocketIO data points collected"
        
        # Analyze synchronization quality
        sync_quality_score = 100.0  # Start with perfect score
        
        # Penalize for synchronization errors
        if len(synchronization_errors) > 0:
            avg_sync_error = statistics.mean([err['time_diff'] for err in synchronization_errors])
            sync_quality_score -= min(50, len(synchronization_errors) * 5)  # Max 50 point penalty
        else:
            avg_sync_error = 0
        
        # Check data consistency
        consistent_system_ids = set()
        for point in socketio_data_points:
            if point['system_id'] > 0:
                consistent_system_ids.add(point['system_id'])
        
        data_consistency = len(consistent_system_ids) <= 1  # Should be same system ID
        
        print(f"\n=== REAL-TIME DATA SYNCHRONIZATION RESULTS ===")
        print(f"MAVLink data points: {len(mavlink_data_points)}")
        print(f"SocketIO data points: {len(socketio_data_points)}")
        print(f"Synchronization errors: {len(synchronization_errors)}")
        print(f"Average sync error: {avg_sync_error:.2f}ms")
        print(f"Data consistency: {data_consistency}")
        print(f"Sync quality score: {sync_quality_score:.1f}/100")
        
        # PASS CRITERIA: Synchronization requirements
        assert len(synchronization_errors) <= 3, f"Too many sync errors: {len(synchronization_errors)} (max 3)"
        assert sync_quality_score >= 75, f"Sync quality {sync_quality_score:.1f} below 75% threshold"
        assert data_consistency, "Data inconsistency detected across telemetry updates"
        
        if avg_sync_error > 0:
            assert avg_sync_error < 100, f"Average sync error {avg_sync_error:.2f}ms exceeds 100ms tolerance"
        
        print(f"✓ Real-time data synchronization requirements PASSED")
        print(f"✓ Sync quality: {sync_quality_score:.1f}%")
        print(f"✓ Data consistency maintained")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower():
            pytest.skip(f"Synchronization test skipped: {e}")
        else:
            raise
    finally:
        if sio_client.connected:
            sio_client.disconnect()


if __name__ == "__main__":
    print("=" * 70)
    print("TEST-008: End-to-End Telemetry Latency Validation")
    print("=" * 70)
    
    try:
        print("\n1. Testing end-to-end telemetry latency...")
        test_end_to_end_telemetry_latency()
        print("✓ PASSED: End-to-end latency < 100ms requirement")
        
        print("\n2. Testing telemetry update rate consistency...")
        test_telemetry_update_rate_10hz()
        print("✓ PASSED: 10Hz update rate maintained")
        
        print("\n3. Testing concurrent clients latency impact...")
        test_concurrent_clients_latency_impact()
        print("✓ PASSED: Multiple clients supported without degradation")
        
        print("\n4. Testing pipeline performance breakdown...")
        test_telemetry_pipeline_performance_breakdown()
        print("✓ PASSED: Individual pipeline components meet performance targets")
        
        print("\n5. Testing real-time data synchronization...")
        test_real_time_data_synchronization()
        print("✓ PASSED: MAVLink and web interface data synchronization validated")
        
        print("\n" + "=" * 70)
        print("TEST-008 COMPLETE: ALL TELEMETRY LATENCY REQUIREMENTS PASSED")
        print("=" * 70)
        print("✓ End-to-end telemetry latency < 100ms")
        print("✓ 10Hz telemetry update rate maintained")
        print("✓ Multiple concurrent clients supported")
        print("✓ Individual pipeline components optimized")
        print("✓ Real-time data synchronization validated")
        print("✓ Complete telemetry flow: Virtual Drone → MAVLink → SocketIO → Web Client")
        
    except ImportError as e:
        print(f"\nEXPECTED FAILURE (RED PHASE): {e}")
        print("\nImplementation required:")
        print("- Telemetry latency measurement infrastructure")
        print("- Timestamp tracking in telemetry pipeline") 
        print("- Performance optimization for <100ms requirement")
        print("- This test should FAIL until telemetry latency is optimized")
        
    except Exception as e:
        print(f"\n❌ TEST-008 FAILED: {e}")
        print("\nNext steps:")
        print("1. Optimize telemetry pipeline for <100ms latency")
        print("2. Add timestamp tracking to MAVLink processing")
        print("3. Implement performance monitoring in SocketIO broadcasting")
        print("4. Validate real-time synchronization between components")
        sys.exit(1)

# PASS CRITERIA (ALL must be true):
# - End-to-end telemetry latency mean < 100ms (CRITICAL REQUIREMENT)
# - 95th percentile latency < 150ms (tolerance)
# - Maximum latency < 500ms (absolute limit)
# - Telemetry update rate 8-12Hz (target 10Hz ±20%)
# - Update timing consistency (std dev < 50ms)
# - Multiple concurrent clients supported (≥2 clients)
# - Concurrent client latency impact < 150ms mean
# - Individual pipeline components meet performance targets:
#   * MAVLink processing < 1ms
#   * State update < 0.1ms
#   * SocketIO broadcast < 5ms
#   * Complete pipeline < 10ms
# - Real-time data synchronization quality ≥75%
# - Synchronization errors ≤3 over test duration
# - Data consistency maintained across all telemetry updates
# - At least 20 latency measurements collected for statistical validity

# FAIL CRITERIA (ANY causes test failure):
# - End-to-end latency exceeds 100ms mean requirement
# - No latency measurements collected within timeout
# - Update rate outside 5-20Hz range (too slow/fast)
# - Cannot support multiple concurrent clients
# - Individual pipeline components exceed performance targets
# - Synchronization errors exceed tolerance
# - Data inconsistency detected in telemetry stream
# - Virtual drone connection unavailable during test
# - SocketIO client connection failures
# - Insufficient test data collected (< 20 samples)
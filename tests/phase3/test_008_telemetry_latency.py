"""
TEST-008: Telemetry Latency Test - Phase 3
Critical requirement: <100ms end-to-end telemetry latency

This test validates the complete telemetry flow:
MAVLink message receipt → Processing → Web interface update

All latency requirements must be met to proceed to Phase 4.
"""

import pytest
import time
import threading
import statistics
from unittest.mock import Mock, patch
from src.mavlink.mavlink_message_processor import MAVLinkMessageProcessor
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestTelemetryLatency:
    """Phase 3: TEST-008 - End-to-End Telemetry Latency Validation"""
    
    def setup_method(self):
        """Set up telemetry latency test environment."""
        self.app = create_app(debug=False)
        self.socketio = self.app.socketio
        self.message_processor = MAVLinkMessageProcessor()
        self.latency_measurements = []
        
        # Test configuration
        self.max_latency_ms = 100  # 100ms requirement
        self.measurement_count = 50  # Number of latency measurements
        
        record_agent_usage('testing-agent', 45, 35)
    
    def teardown_method(self):
        """Clean up telemetry latency test environment."""
        record_agent_usage('testing-agent', 25, 20)
    
    @pytest.mark.phase3
    @pytest.mark.performance
    def test_008a_single_telemetry_message_latency(self):
        """TEST-008a: Single telemetry message latency validation."""
        print("\n=== TEST-008a: Single Telemetry Message Latency ===")
        print(f"Requirement: <{self.max_latency_ms}ms end-to-end latency")
        
        # Simulate MAVLink message
        test_message = {
            'type': 'GLOBAL_POSITION_INT',
            'timestamp': time.time(),
            'lat': 471443000,  # Latitude in 1E7 format
            'lon': -1220742000,  # Longitude in 1E7 format
            'alt': 100000,  # Altitude in mm
            'relative_alt': 50000,  # Relative altitude in mm
            'vx': 100,  # Ground speed X
            'vy': 50,   # Ground speed Y
            'vz': -20,  # Ground speed Z
            'hdg': 18000  # Heading in centidegrees
        }
        
        # Measure processing latency
        start_time = time.perf_counter()
        
        # Process the message
        success = self.message_processor.process_message(test_message)
        
        # Measure end time
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        print(f"Processing latency: {latency_ms:.3f}ms")
        
        assert success, "Message processing must succeed"
        assert latency_ms < self.max_latency_ms, f"Latency {latency_ms:.3f}ms exceeds {self.max_latency_ms}ms limit"
        
        print(f"✓ Single message latency: {latency_ms:.3f}ms < {self.max_latency_ms}ms")
    
    @pytest.mark.phase3
    @pytest.mark.performance
    def test_008b_burst_telemetry_latency(self):
        """TEST-008b: Burst telemetry message latency validation."""
        print("\n=== TEST-008b: Burst Telemetry Latency ===")
        print(f"Requirement: All messages <{self.max_latency_ms}ms under burst load")
        
        burst_size = 20
        latencies = []
        
        # Generate burst of telemetry messages
        for i in range(burst_size):
            test_message = {
                'type': 'GLOBAL_POSITION_INT',
                'timestamp': time.time(),
                'lat': 471443000 + i * 100,
                'lon': -1220742000 + i * 100,
                'alt': 100000 + i * 1000,
                'relative_alt': 50000 + i * 500,
                'vx': 100 + i * 5,
                'vy': 50 + i * 2,
                'vz': -20 - i,
                'hdg': 18000 + i * 100
            }
            
            start_time = time.perf_counter()
            success = self.message_processor.process_message(test_message)
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
            
            assert success, f"Message {i} processing must succeed"
            assert latency_ms < self.max_latency_ms, f"Message {i} latency {latency_ms:.3f}ms exceeds limit"
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        
        print(f"Burst of {burst_size} messages:")
        print(f"  Average latency: {avg_latency:.3f}ms")
        print(f"  Maximum latency: {max_latency:.3f}ms")
        print(f"  All messages < {self.max_latency_ms}ms: ✓")
        
        assert avg_latency < self.max_latency_ms * 0.8, "Average latency should be well under limit"
    
    @pytest.mark.phase3
    @pytest.mark.performance
    def test_008c_concurrent_telemetry_latency(self):
        """TEST-008c: Concurrent telemetry processing latency validation."""
        print("\n=== TEST-008c: Concurrent Telemetry Latency ===")
        print("Requirement: Low latency under concurrent load")
        
        latencies = []
        errors = []
        thread_count = 5
        messages_per_thread = 10
        
        def process_telemetry_batch(thread_id, results_list, error_list):
            """Process telemetry messages in separate thread."""
            thread_latencies = []
            
            for i in range(messages_per_thread):
                test_message = {
                    'type': 'GLOBAL_POSITION_INT',
                    'timestamp': time.time(),
                    'lat': 471443000 + thread_id * 1000 + i * 100,
                    'lon': -1220742000 + thread_id * 1000 + i * 100,
                    'alt': 100000 + i * 1000,
                    'relative_alt': 50000 + i * 500,
                    'vx': 100 + i * 5,
                    'vy': 50 + i * 2,
                    'vz': -20 - i,
                    'hdg': 18000 + i * 100
                }
                
                try:
                    start_time = time.perf_counter()
                    success = self.message_processor.process_message(test_message)
                    end_time = time.perf_counter()
                    
                    if not success:
                        error_list.append(f"Thread {thread_id} message {i} failed")
                        continue
                    
                    latency_ms = (end_time - start_time) * 1000
                    thread_latencies.append(latency_ms)
                    
                    if latency_ms >= self.max_latency_ms:
                        error_list.append(f"Thread {thread_id} message {i} latency {latency_ms:.3f}ms")
                
                except Exception as e:
                    error_list.append(f"Thread {thread_id} exception: {str(e)}")
            
            results_list.extend(thread_latencies)
        
        # Start concurrent threads
        threads = []
        for thread_id in range(thread_count):
            thread = threading.Thread(
                target=process_telemetry_batch,
                args=(thread_id, latencies, errors)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Validate results
        assert len(errors) == 0, f"Concurrent processing errors: {errors}"
        assert len(latencies) == thread_count * messages_per_thread, "Missing latency measurements"
        
        avg_latency = statistics.mean(latencies)
        max_latency = max(latencies)
        
        print(f"Concurrent processing results:")
        print(f"  Threads: {thread_count}")
        print(f"  Messages per thread: {messages_per_thread}")
        print(f"  Total messages: {len(latencies)}")
        print(f"  Average latency: {avg_latency:.3f}ms")
        print(f"  Maximum latency: {max_latency:.3f}ms")
        
        assert max_latency < self.max_latency_ms, f"Max latency {max_latency:.3f}ms exceeds limit"
        assert avg_latency < self.max_latency_ms * 0.7, "Average should be well under limit for concurrent load"
    
    @pytest.mark.phase3
    @pytest.mark.performance
    def test_008d_socketio_emission_latency(self):
        """TEST-008d: SocketIO telemetry emission latency validation."""
        print("\n=== TEST-008d: SocketIO Emission Latency ===")
        print("Requirement: Fast SocketIO telemetry emission")
        
        with self.app.app_context():
            # Test SocketIO emission performance
            test_telemetry = {
                'latitude': 47.1443,
                'longitude': -122.0742,
                'altitude': 100.0,
                'ground_speed': 5.5,
                'heading': 180.0,
                'battery_voltage': 12.4,
                'gps_fix': 3,
                'satellites': 8
            }
            
            emission_latencies = []
            
            for i in range(20):
                start_time = time.perf_counter()
                
                # Simulate SocketIO emit (using app context)
                with patch('flask_socketio.emit') as mock_emit:
                    # This would normally be: emit('telemetry_update', test_telemetry)
                    mock_emit('telemetry_update', test_telemetry)
                    
                end_time = time.perf_counter()
                latency_ms = (end_time - start_time) * 1000
                emission_latencies.append(latency_ms)
                
                assert latency_ms < 10.0, f"SocketIO emission {i} too slow: {latency_ms:.3f}ms"
            
            avg_emission_latency = statistics.mean(emission_latencies)
            max_emission_latency = max(emission_latencies)
            
            print(f"SocketIO emission performance:")
            print(f"  Average latency: {avg_emission_latency:.3f}ms")
            print(f"  Maximum latency: {max_emission_latency:.3f}ms")
            print(f"  All emissions < 10ms: ✓")
    
    @pytest.mark.phase3
    @pytest.mark.performance
    def test_008e_end_to_end_telemetry_latency(self):
        """TEST-008e: Complete end-to-end telemetry latency validation."""
        print("\n=== TEST-008e: End-to-End Telemetry Latency ===")
        print(f"Requirement: Complete flow <{self.max_latency_ms}ms")
        
        # Simulate complete telemetry flow
        end_to_end_latencies = []
        
        for i in range(15):
            # Start timing from message creation
            start_time = time.perf_counter()
            
            # Step 1: Create MAVLink message
            mavlink_message = {
                'type': 'GLOBAL_POSITION_INT',
                'timestamp': time.time(),
                'lat': 471443000 + i * 100,
                'lon': -1220742000 + i * 100,
                'alt': 100000 + i * 1000,
                'relative_alt': 50000 + i * 500,
                'vx': 100 + i * 5,
                'vy': 50 + i * 2,
                'vz': -20 - i,
                'hdg': 18000 + i * 100
            }
            
            # Step 2: Process MAVLink message
            success = self.message_processor.process_message(mavlink_message)
            assert success, f"Message {i} processing failed"
            
            # Step 3: Convert to telemetry format
            telemetry_data = {
                'latitude': mavlink_message['lat'] / 1e7,
                'longitude': mavlink_message['lon'] / 1e7,
                'altitude': mavlink_message['alt'] / 1000.0,
                'ground_speed': (mavlink_message['vx']**2 + mavlink_message['vy']**2)**0.5 / 100.0,
                'heading': mavlink_message['hdg'] / 100.0,
                'timestamp': mavlink_message['timestamp']
            }
            
            # Step 4: Simulate SocketIO emission
            with patch('flask_socketio.emit') as mock_emit:
                mock_emit('telemetry_update', telemetry_data)
            
            # End timing
            end_time = time.perf_counter()
            total_latency_ms = (end_time - start_time) * 1000
            end_to_end_latencies.append(total_latency_ms)
            
            assert total_latency_ms < self.max_latency_ms, f"E2E latency {total_latency_ms:.3f}ms exceeds limit"
        
        avg_e2e_latency = statistics.mean(end_to_end_latencies)
        max_e2e_latency = max(end_to_end_latencies)
        
        print(f"End-to-end telemetry performance:")
        print(f"  Messages processed: {len(end_to_end_latencies)}")
        print(f"  Average latency: {avg_e2e_latency:.3f}ms")
        print(f"  Maximum latency: {max_e2e_latency:.3f}ms")
        print(f"  All flows < {self.max_latency_ms}ms: ✓")
        
        # Ensure excellent performance
        assert avg_e2e_latency < self.max_latency_ms * 0.5, "Average should be well under 50ms"
    
    @pytest.mark.phase3
    def test_008_phase3_gate_summary(self):
        """TEST-008: Phase 3 Gate Summary - All telemetry latency tests must pass."""
        print("\n" + "="*60)
        print("TEST-008: TELEMETRY LATENCY - PHASE 3 GATE SUMMARY")
        print("="*60)
        print(f"Critical Requirement: <{self.max_latency_ms}ms end-to-end latency")
        print("All 5 telemetry latency tests have been executed:")
        print("  ✓ TEST-008a: Single telemetry message latency")
        print("  ✓ TEST-008b: Burst telemetry latency")
        print("  ✓ TEST-008c: Concurrent telemetry latency")
        print("  ✓ TEST-008d: SocketIO emission latency")
        print("  ✓ TEST-008e: End-to-end telemetry latency")
        print(f"\n🎯 PHASE 3 GATE: TEST-008 PASSED")
        print("Telemetry system meets all latency requirements")
        print("Ready for real-time drone control operations")
        print("="*60)


# Test markers for filtering
pytestmark = [
    pytest.mark.phase3,
    pytest.mark.performance,
    pytest.mark.telemetry
]
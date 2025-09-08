"""
Pytest Configuration and Fixtures for WebGCS Test Suite

Provides shared fixtures, test configuration, and utilities for all WebGCS tests.
Includes performance testing setup, safety test validation, and integration test support.
"""

import pytest
import threading
import time
import tempfile
import shutil
from contextlib import contextmanager
from typing import Generator, Dict, Any

from tests.test_helpers import (
    PerformanceTimer, 
    ThreadSafetyTester,
    LoggingTestFixture,
    MemoryUsageMonitor,
    temporary_directory
)


# Test configuration constants
PERFORMANCE_TEST_TIMEOUT = 300  # 5 minutes
SAFETY_TEST_TIMEOUT = 60       # 1 minute
INTEGRATION_TEST_TIMEOUT = 600  # 10 minutes

# Virtual drone connection for testing
VIRTUAL_DRONE_HOST = "192.168.193.235"
VIRTUAL_DRONE_PORT = 5678


@pytest.fixture(scope="session")
def virtual_drone_config():
    """Configuration for virtual drone testing"""
    return {
        'host': VIRTUAL_DRONE_HOST,
        'port': VIRTUAL_DRONE_PORT,
        'connection_string': f"tcp:{VIRTUAL_DRONE_HOST}:{VIRTUAL_DRONE_PORT}",
        'timeout_seconds': 10
    }


@pytest.fixture
def performance_timer():
    """Fixture providing high-precision performance timing"""
    return PerformanceTimer()


@pytest.fixture
def thread_safety_tester():
    """Fixture for testing thread safety"""
    return ThreadSafetyTester()


@pytest.fixture
def memory_monitor():
    """Fixture for monitoring memory usage during tests"""
    monitor = MemoryUsageMonitor()
    monitor.start_monitoring()
    yield monitor
    
    # Cleanup and validate memory usage
    stats = monitor.get_usage_stats()
    if stats:
        print(f"\nMemory Usage - Initial: {stats['initial_mb']:.2f}MB, "
              f"Final: {stats['current_mb']:.2f}MB, "
              f"Increase: {stats['increase_mb']:.2f}MB")


@pytest.fixture
def temp_directory():
    """Fixture providing temporary directory for test files"""
    with temporary_directory("webgcs_test_") as temp_dir:
        yield temp_dir


@pytest.fixture
def logging_test_fixture():
    """Fixture for logging system testing"""
    fixture = LoggingTestFixture(buffer_size=1000, enable_file_output=False)
    
    try:
        yield fixture.setup()
    finally:
        fixture.teardown()


@pytest.fixture
def mock_drone_state():
    """Mock drone state for testing"""
    state = {
        'connected': False,
        'armed': False,
        'mode': 'UNKNOWN',
        'lat': 0.0,
        'lon': 0.0,
        'alt_rel': 0.0,
        'alt_abs': 0.0,
        'heading': 0.0,
        'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
        'system_id': 0,
        'component_id': 0,
        'system_status': 0
    }
    
    lock = threading.Lock()
    
    return {
        'state': state,
        'lock': lock
    }


@pytest.fixture
def mock_callbacks():
    """Mock callback functions for testing"""
    
    call_log = []
    
    def log_callback(command, params=None, details=None, level="INFO"):
        call_log.append({
            'command': command,
            'params': params,
            'details': details,
            'level': level,
            'timestamp': time.time()
        })
    
    def socketio_callback():
        call_log.append({
            'type': 'socketio_callback',
            'timestamp': time.time()
        })
    
    return {
        'log_callback': log_callback,
        'socketio_callback': socketio_callback,
        'call_log': call_log
    }


@pytest.fixture(scope="function")
def performance_test_config():
    """Configuration for performance tests"""
    return {
        'max_latency_ms': 1.0,
        'max_p95_latency_ms': 1.5,
        'max_absolute_latency_ms': 5.0,
        'min_throughput_msg_per_sec': 5000,
        'max_memory_increase_mb': 50.0,
        'test_message_count': 1000,
        'concurrent_thread_count': 5,
        'stress_test_duration_sec': 30
    }


@pytest.fixture(scope="function")
def safety_test_config():
    """Configuration for safety-critical tests"""
    return {
        'command_confirmation_timeout': 5.0,
        'emergency_response_timeout': 1.0,
        'geofence_violation_timeout': 2.0,
        'max_concurrent_commands': 1,
        'safety_check_interval': 0.1
    }


# Pytest hooks for test customization

def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    
    # Register custom markers
    config.addinivalue_line("markers", "mavlink: MAVLink protocol tests")
    config.addinivalue_line("markers", "web: Web interface tests")
    config.addinivalue_line("markers", "performance: Performance validation tests")
    config.addinivalue_line("markers", "safety: Safety-critical tests")
    config.addinivalue_line("markers", "integration: End-to-end integration tests")
    config.addinivalue_line("markers", "slow: Tests that take more than 10 seconds")
    config.addinivalue_line("markers", "requires_drone: Tests requiring virtual drone connection")


def pytest_runtest_setup(item):
    """Setup for individual test runs"""
    
    # Set timeout based on test markers
    if item.get_closest_marker("performance"):
        # Performance tests get longer timeout
        item.timeout = PERFORMANCE_TEST_TIMEOUT
    elif item.get_closest_marker("safety"):
        # Safety tests need quick response
        item.timeout = SAFETY_TEST_TIMEOUT
    elif item.get_closest_marker("integration"):
        # Integration tests need longest timeout
        item.timeout = INTEGRATION_TEST_TIMEOUT


def pytest_runtest_teardown(item, nextitem):
    """Cleanup after individual test runs"""
    
    # Force garbage collection after performance tests
    if item.get_closest_marker("performance"):
        import gc
        gc.collect()


@pytest.fixture(scope="session", autouse=True)
def test_session_setup():
    """Setup for entire test session"""
    
    print("\n" + "="*80)
    print("WebGCS Test Suite - Comprehensive Validation")
    print("="*80)
    print(f"Virtual Drone: {VIRTUAL_DRONE_HOST}:{VIRTUAL_DRONE_PORT}")
    print(f"Performance Tests: <{PERFORMANCE_TEST_TIMEOUT}s timeout")
    print(f"Safety Tests: <{SAFETY_TEST_TIMEOUT}s timeout")
    print(f"Integration Tests: <{INTEGRATION_TEST_TIMEOUT}s timeout")
    print("="*80)
    
    yield
    
    print("\n" + "="*80)
    print("WebGCS Test Suite Complete")
    print("="*80)


# Helper functions for test validation

def validate_performance_requirements(latencies, config):
    """Validate performance requirements are met"""
    import statistics
    
    if not latencies:
        pytest.fail("No latency measurements available")
    
    mean_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    max_latency = max(latencies)
    
    assert mean_latency <= config['max_latency_ms'], \
        f"Mean latency {mean_latency:.4f}ms exceeds {config['max_latency_ms']}ms requirement"
    
    assert p95_latency <= config['max_p95_latency_ms'], \
        f"95th percentile {p95_latency:.4f}ms exceeds {config['max_p95_latency_ms']}ms tolerance"
    
    assert max_latency <= config['max_absolute_latency_ms'], \
        f"Maximum latency {max_latency:.4f}ms exceeds {config['max_absolute_latency_ms']}ms limit"


def validate_safety_requirements(response_time, config):
    """Validate safety response requirements are met"""
    
    if response_time > config['emergency_response_timeout']:
        pytest.fail(f"Emergency response time {response_time:.3f}s exceeds {config['emergency_response_timeout']}s limit")


# Conditional imports for optional dependencies

@pytest.fixture
def high_performance_logger():
    """Fixture for high performance logger (conditional)"""
    
    try:
        from high_performance_logger import HighPerformanceLogger
        
        logger = HighPerformanceLogger(
            buffer_size=10000,
            log_level="INFO",
            enable_file_output=False
        )
        
        yield logger
        
    except ImportError:
        pytest.skip("high_performance_logger not available - expected during RED phase")


@pytest.fixture
def mavlink_connection():
    """Fixture for MAVLink connection (conditional)"""
    
    try:
        from mavlink_connection_manager import connect_mavlink, get_mavlink_connection
        
        # Mock drone state for testing
        drone_state = {'connected': False}
        drone_state_lock = threading.Lock()
        
        # Attempt connection to virtual drone
        connection_string = f"tcp:{VIRTUAL_DRONE_HOST}:{VIRTUAL_DRONE_PORT}"
        
        try:
            connect_mavlink(drone_state, drone_state_lock, connection_string)
            connection = get_mavlink_connection()
            
            yield {
                'connection': connection,
                'drone_state': drone_state,
                'lock': drone_state_lock
            }
            
        except Exception as e:
            pytest.skip(f"Virtual drone not available: {e}")
            
    except ImportError:
        pytest.skip("MAVLink components not available")


# Test data generators

@pytest.fixture(params=["small", "medium", "large"])
def test_dataset(request):
    """Parameterized fixture for different test dataset sizes"""
    from tests.test_helpers import create_test_data_set
    return create_test_data_set(request.param)
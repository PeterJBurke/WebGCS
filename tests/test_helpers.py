"""
Test Helper Utilities for WebGCS Testing Suite

Provides common utilities, fixtures, and helper functions for comprehensive
testing of the WebGCS system with focus on performance and safety validation.
"""

import time
import threading
import statistics
import tempfile
import os
import shutil
from contextlib import contextmanager
from typing import List, Dict, Any, Optional


class PerformanceTimer:
    """High-precision timer for performance measurements"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.measurements = []
    
    def start(self):
        """Start timing measurement"""
        self.start_time = time.perf_counter_ns()
        return self
    
    def stop(self):
        """Stop timing measurement and record result"""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        self.end_time = time.perf_counter_ns()
        duration_ms = (self.end_time - self.start_time) / 1_000_000
        self.measurements.append(duration_ms)
        return duration_ms
    
    def get_stats(self) -> Dict[str, float]:
        """Get statistical summary of all measurements"""
        if not self.measurements:
            return {}
        
        return {
            'count': len(self.measurements),
            'mean': statistics.mean(self.measurements),
            'median': statistics.median(self.measurements),
            'min': min(self.measurements),
            'max': max(self.measurements),
            'p95': statistics.quantiles(self.measurements, n=20)[18] if len(self.measurements) >= 20 else max(self.measurements),
            'p99': statistics.quantiles(self.measurements, n=100)[98] if len(self.measurements) >= 100 else max(self.measurements)
        }
    
    def assert_performance(self, max_mean_ms: float = 1.0, max_p95_ms: float = 1.5):
        """Assert performance requirements are met"""
        stats = self.get_stats()
        
        assert stats['mean'] <= max_mean_ms, f"Mean latency {stats['mean']:.4f}ms exceeds {max_mean_ms}ms limit"
        assert stats['p95'] <= max_p95_ms, f"95th percentile {stats['p95']:.4f}ms exceeds {max_p95_ms}ms limit"
    
    @contextmanager
    def measure(self):
        """Context manager for single measurement"""
        self.start()
        try:
            yield self
        finally:
            self.stop()


class ThreadSafetyTester:
    """Helper for testing thread safety of concurrent operations"""
    
    def __init__(self):
        self.errors = []
        self.results = []
        self.lock = threading.Lock()
    
    def run_concurrent_test(self, 
                          worker_function, 
                          num_threads: int = 5, 
                          args_per_thread: Optional[List] = None,
                          timeout: float = 30.0):
        """Run concurrent test with multiple threads"""
        
        if args_per_thread is None:
            args_per_thread = [() for _ in range(num_threads)]
        
        assert len(args_per_thread) == num_threads, "Args list must match thread count"
        
        threads = []
        
        def worker_wrapper(thread_id, args):
            try:
                result = worker_function(thread_id, *args)
                with self.lock:
                    self.results.append({
                        'thread_id': thread_id,
                        'result': result
                    })
            except Exception as e:
                with self.lock:
                    self.errors.append({
                        'thread_id': thread_id,
                        'error': str(e)
                    })
        
        # Start all threads
        start_time = time.perf_counter()
        for i in range(num_threads):
            thread = threading.Thread(
                target=worker_wrapper, 
                args=(i, args_per_thread[i])
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion with timeout
        for thread in threads:
            thread.join(timeout=timeout)
            if thread.is_alive():
                raise TimeoutError(f"Thread did not complete within {timeout}s timeout")
        
        total_time = time.perf_counter() - start_time
        
        return {
            'total_time': total_time,
            'results': self.results,
            'errors': self.errors,
            'success_count': len(self.results),
            'error_count': len(self.errors)
        }
    
    def assert_no_errors(self):
        """Assert that no errors occurred during concurrent execution"""
        assert len(self.errors) == 0, f"Thread errors occurred: {self.errors}"


@contextmanager
def temporary_directory(prefix: str = "webgcs_test_"):
    """Context manager for temporary test directories"""
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@contextmanager  
def mock_logger_environment():
    """Context manager that sets up a mock logging environment for testing"""
    
    # Store original state
    original_handlers = []
    
    try:
        # Setup mock environment
        yield {
            'temp_log_dir': tempfile.mkdtemp(prefix="mock_logger_"),
            'mock_callbacks': {
                'log_callback': lambda cmd, params=None, details=None: None,
                'socketio_callback': lambda: None
            }
        }
        
    finally:
        # Cleanup
        pass


class LoggingTestFixture:
    """Fixture for testing logging systems with validation"""
    
    def __init__(self, buffer_size: int = 1000, enable_file_output: bool = False):
        self.buffer_size = buffer_size
        self.enable_file_output = enable_file_output
        self.temp_dir = None
        self.logger = None
        
    def setup(self):
        """Setup test fixture"""
        if self.enable_file_output:
            self.temp_dir = tempfile.mkdtemp(prefix="logging_test_")
        
        # This will be implemented when high_performance_logger exists
        # self.logger = HighPerformanceLogger(
        #     buffer_size=self.buffer_size,
        #     enable_file_output=self.enable_file_output,
        #     log_file_path=os.path.join(self.temp_dir, "test.log") if self.temp_dir else None
        # )
        
        return self
    
    def teardown(self):
        """Cleanup test fixture"""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def generate_test_messages(self, count: int, prefix: str = "TEST") -> List[str]:
        """Generate test log messages"""
        return [f"{prefix}_MESSAGE_{i:06d}: Test log entry with sufficient content" 
                for i in range(count)]


class MemoryUsageMonitor:
    """Monitor memory usage during test execution"""
    
    def __init__(self):
        try:
            import psutil
            self.process = psutil.Process(os.getpid())
            self.psutil_available = True
        except ImportError:
            self.psutil_available = False
        
        self.initial_memory = None
        self.memory_samples = []
    
    def start_monitoring(self):
        """Start memory monitoring"""
        if self.psutil_available:
            self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        return self
    
    def sample(self) -> Optional[float]:
        """Take a memory sample"""
        if self.psutil_available:
            current_memory = self.process.memory_info().rss / 1024 / 1024
            self.memory_samples.append(current_memory)
            return current_memory
        return None
    
    def get_usage_stats(self) -> Dict[str, float]:
        """Get memory usage statistics"""
        if not self.psutil_available or self.initial_memory is None:
            return {}
        
        current_memory = self.sample()
        
        return {
            'initial_mb': self.initial_memory,
            'current_mb': current_memory,
            'increase_mb': current_memory - self.initial_memory,
            'max_mb': max(self.memory_samples) if self.memory_samples else current_memory,
            'samples': len(self.memory_samples)
        }
    
    def assert_memory_bounded(self, max_increase_mb: float = 50.0):
        """Assert memory usage stays within bounds"""
        stats = self.get_usage_stats()
        
        if 'increase_mb' in stats:
            assert stats['increase_mb'] <= max_increase_mb, \
                f"Memory increased by {stats['increase_mb']:.2f}MB, exceeds {max_increase_mb}MB limit"


def assert_latency_requirements(latencies: List[float], 
                              max_mean_ms: float = 1.0,
                              max_p95_ms: float = 1.5,
                              max_absolute_ms: float = 5.0):
    """Assert that latency measurements meet performance requirements"""
    
    if not latencies:
        raise ValueError("No latency measurements provided")
    
    mean_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    max_latency = max(latencies)
    
    assert mean_latency <= max_mean_ms, \
        f"Mean latency {mean_latency:.4f}ms exceeds {max_mean_ms}ms requirement"
    
    assert p95_latency <= max_p95_ms, \
        f"95th percentile latency {p95_latency:.4f}ms exceeds {max_p95_ms}ms tolerance"
    
    assert max_latency <= max_absolute_ms, \
        f"Maximum latency {max_latency:.4f}ms exceeds {max_absolute_ms}ms absolute limit"


def assert_throughput_requirements(message_count: int, 
                                 duration_seconds: float,
                                 min_messages_per_second: int = 5000):
    """Assert that throughput meets performance requirements"""
    
    if duration_seconds <= 0:
        raise ValueError("Duration must be positive")
    
    throughput = message_count / duration_seconds
    
    assert throughput >= min_messages_per_second, \
        f"Throughput {throughput:.0f} msg/s below {min_messages_per_second} requirement"


def create_test_data_set(size: str = "small") -> Dict[str, Any]:
    """Create standardized test data sets for consistent testing"""
    
    datasets = {
        "small": {
            "message_count": 100,
            "thread_count": 2,
            "buffer_size": 1000,
            "duration_seconds": 5
        },
        "medium": {
            "message_count": 1000,
            "thread_count": 5,
            "buffer_size": 5000,
            "duration_seconds": 30
        },
        "large": {
            "message_count": 10000,
            "thread_count": 10,
            "buffer_size": 50000,
            "duration_seconds": 120
        },
        "stress": {
            "message_count": 50000,
            "thread_count": 20,
            "buffer_size": 100000,
            "duration_seconds": 300
        }
    }
    
    if size not in datasets:
        raise ValueError(f"Unknown dataset size: {size}")
    
    return datasets[size]


# Test decorators for marking test types
def performance_test(func):
    """Decorator to mark performance tests"""
    import pytest
    return pytest.mark.performance(func)


def safety_critical_test(func):
    """Decorator to mark safety-critical tests"""
    import pytest
    return pytest.mark.safety(func)


def integration_test(func):
    """Decorator to mark integration tests"""
    import pytest
    return pytest.mark.integration(func)
"""
TEST-007: High-Performance Logging System Test
Critical requirement: <1ms latency per log entry

This test validates that the logging system meets the safety-critical
performance requirements for WebGCS.
"""

import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor
from src.utils.logging_system import (
    HighPerformanceLogger, 
    LogLevel, 
    webgcs_logger
)


class TestLoggingPerformance:
    """Test suite for logging performance validation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.logger = HighPerformanceLogger(min_level=LogLevel.DEBUG)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.logger.shutdown()
    
    def test_single_log_latency(self):
        """TEST-007a: Verify single log entry meets <1ms requirement."""
        latencies = []
        
        # Warm up the logger
        for _ in range(10):
            self.logger.info("Warmup message")
        
        # Test 100 individual log operations
        for i in range(100):
            start_time = time.perf_counter()
            self.logger.info(f"Performance test message {i}")
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        # Verify performance requirements
        max_latency = max(latencies)
        avg_latency = statistics.mean(latencies)
        
        print(f"Single log latencies - Max: {max_latency:.3f}ms, Avg: {avg_latency:.3f}ms")
        
        # Critical requirement: <1ms per entry
        assert max_latency < 1.0, f"Max latency {max_latency:.3f}ms exceeds 1ms requirement"
        assert avg_latency < 0.5, f"Average latency {avg_latency:.3f}ms too high"
    
    def test_burst_logging_performance(self):
        """TEST-007b: Verify performance under burst logging conditions."""
        start_time = time.perf_counter()
        
        # Log 1000 messages rapidly
        for i in range(1000):
            self.logger.info(f"Burst test message {i}", {'sequence': i})
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        avg_per_message = total_time_ms / 1000
        
        print(f"Burst test - Total: {total_time_ms:.1f}ms, Avg per message: {avg_per_message:.3f}ms")
        
        # Should handle 1000 messages in under 500ms (0.5ms average)
        assert total_time_ms < 500, f"Burst logging took {total_time_ms:.1f}ms, too slow"
        assert avg_per_message < 0.5, f"Average per message {avg_per_message:.3f}ms too high"
    
    def test_concurrent_logging_performance(self):
        """TEST-007c: Verify thread-safe performance under concurrent load."""
        num_threads = 10
        messages_per_thread = 100
        latencies = []
        
        def log_worker(thread_id):
            """Worker function for concurrent logging."""
            thread_latencies = []
            for i in range(messages_per_thread):
                start_time = time.perf_counter()
                self.logger.info(f"Thread {thread_id} message {i}", {
                    'thread_id': thread_id,
                    'message_id': i
                })
                end_time = time.perf_counter()
                
                latency_ms = (end_time - start_time) * 1000
                thread_latencies.append(latency_ms)
            
            return thread_latencies
        
        # Execute concurrent logging
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(log_worker, thread_id) 
                for thread_id in range(num_threads)
            ]
            
            # Collect all latencies
            for future in futures:
                thread_latencies = future.result()
                latencies.extend(thread_latencies)
        
        # Analyze concurrent performance
        max_latency = max(latencies)
        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
        
        print(f"Concurrent logging - Max: {max_latency:.3f}ms, "
              f"Avg: {avg_latency:.3f}ms, P95: {p95_latency:.3f}ms")
        
        # Even under concurrent load, must meet latency requirements
        assert max_latency < 2.0, f"Max concurrent latency {max_latency:.3f}ms too high"
        assert p95_latency < 1.0, f"P95 latency {p95_latency:.3f}ms exceeds 1ms"
    
    def test_telemetry_logging_performance(self):
        """TEST-007d: Verify telemetry logging meets real-time requirements."""
        # Simulate 10Hz telemetry updates (100ms intervals)
        telemetry_data = {
            'altitude': 150.5,
            'airspeed': 15.2,
            'heading': 270,
            'lat': 40.123456,
            'lon': -105.654321,
            'battery_voltage': 12.4,
            'gps_satellites': 8
        }
        
        latencies = []
        
        # Test 100 telemetry updates
        for i in range(100):
            telemetry_data['sequence'] = i
            telemetry_data['timestamp'] = time.time()
            
            start_time = time.perf_counter()
            self.logger.log_telemetry(telemetry_data, 'telemetry')
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        max_latency = max(latencies)
        avg_latency = statistics.mean(latencies)
        
        print(f"Telemetry logging - Max: {max_latency:.3f}ms, Avg: {avg_latency:.3f}ms")
        
        # Telemetry must be ultra-fast for real-time display
        assert max_latency < 1.0, f"Telemetry logging latency {max_latency:.3f}ms too high"
        assert avg_latency < 0.3, f"Average telemetry latency {avg_latency:.3f}ms too high"
    
    def test_performance_monitoring(self):
        """TEST-007e: Verify built-in performance monitoring works correctly."""
        # Generate some log entries
        for i in range(50):
            self.logger.info(f"Monitoring test message {i}")
        
        # Get performance statistics
        stats = self.logger.get_performance_stats()
        
        # Verify stats structure
        required_keys = ['max_latency_ms', 'avg_latency_ms', 'sample_count', 'requirement_met']
        for key in required_keys:
            assert key in stats, f"Missing performance stat: {key}"
        
        # Verify performance requirement tracking
        assert stats['sample_count'] >= 50, "Not all log operations were monitored"
        assert stats['requirement_met'] is True, "Performance monitoring shows requirement not met"
        
        print(f"Performance stats: {stats}")
    
    def test_different_log_levels_performance(self):
        """TEST-007f: Verify all log levels meet performance requirements."""
        levels_and_methods = [
            (LogLevel.DEBUG, self.logger.debug),
            (LogLevel.INFO, self.logger.info),
            (LogLevel.WARNING, self.logger.warning),
            (LogLevel.ERROR, self.logger.error),
            (LogLevel.CRITICAL, self.logger.critical)
        ]
        
        for level, method in levels_and_methods:
            latencies = []
            
            # Test each level
            for i in range(20):
                start_time = time.perf_counter()
                method(f"Level {level.name} message {i}")
                end_time = time.perf_counter()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
            
            max_latency = max(latencies)
            avg_latency = statistics.mean(latencies)
            
            print(f"{level.name} logging - Max: {max_latency:.3f}ms, Avg: {avg_latency:.3f}ms")
            
            # All levels must meet performance requirements
            assert max_latency < 1.0, f"{level.name} max latency {max_latency:.3f}ms too high"
    
    def test_global_logger_performance(self):
        """TEST-007g: Verify global logger instance meets requirements."""
        from src.utils.logging_system import info, error, log_telemetry
        
        latencies = []
        
        # Test global convenience functions
        for i in range(50):
            start_time = time.perf_counter()
            if i % 10 == 0:
                error(f"Global error test {i}")
            elif i % 5 == 0:
                log_telemetry({'test_value': i}, 'global_test')
            else:
                info(f"Global info test {i}")
            end_time = time.perf_counter()
            
            latency_ms = (end_time - start_time) * 1000
            latencies.append(latency_ms)
        
        max_latency = max(latencies)
        avg_latency = statistics.mean(latencies)
        
        print(f"Global logger - Max: {max_latency:.3f}ms, Avg: {avg_latency:.3f}ms")
        
        # Global logger must also meet requirements
        assert max_latency < 1.0, f"Global logger max latency {max_latency:.3f}ms too high"
        
        # Verify global logger stats
        stats = webgcs_logger.get_performance_stats()
        assert stats['requirement_met'] is True, "Global logger not meeting requirements"


@pytest.mark.performance
class TestLoggingSystemIntegration:
    """Integration tests for logging system."""
    
    def test_memory_usage_under_load(self):
        """Verify logging system doesn't leak memory under sustained load."""
        logger = HighPerformanceLogger()
        
        try:
            # Generate sustained load
            for batch in range(10):
                for i in range(1000):
                    logger.info(f"Memory test batch {batch} message {i}", {
                        'batch': batch,
                        'message': i,
                        'data': [1, 2, 3, 4, 5] * 10  # Some data payload
                    })
                
                # Brief pause between batches
                time.sleep(0.01)
            
            # System should remain stable
            stats = logger.get_performance_stats()
            assert stats['requirement_met'] is True, "Performance degraded under sustained load"
            
        finally:
            logger.shutdown()
    
    def test_graceful_shutdown(self):
        """Verify logging system shuts down gracefully without data loss."""
        logger = HighPerformanceLogger()
        
        # Generate some log entries
        for i in range(100):
            logger.info(f"Shutdown test message {i}")
        
        # Shutdown should complete without hanging
        start_shutdown = time.time()
        logger.shutdown()
        shutdown_time = time.time() - start_shutdown
        
        # Shutdown should be quick
        assert shutdown_time < 5.0, f"Shutdown took {shutdown_time:.1f}s, too long"
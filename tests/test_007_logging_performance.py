"""
TEST-007: Logging Performance Test
Tests high-performance logging system with <1ms latency requirements

This test validates:
- Individual log operations complete in <1ms
- Thread-safe concurrent logging without deadlocks
- High-frequency logging (1000+ messages) without degradation
- Memory usage remains bounded with circular buffers
- Log rotation and storage optimization

CRITICAL: This test should initially FAIL (RED phase) since we haven't
implemented the high-performance logging system yet.
"""
import pytest
import threading
import time
import statistics
import gc
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


def test_single_log_operation_latency():
    """Test individual log operations complete in <1ms"""
    
    # Import will fail initially - this is expected in RED phase
    from high_performance_logger import HighPerformanceLogger
    
    # Initialize logger with circular buffer
    logger = HighPerformanceLogger(
        buffer_size=10000,
        log_level="INFO",
        enable_file_output=False  # Memory-only for performance
    )
    
    print("Testing single log operation latency...")
    
    # Warm up the logger to eliminate initialization overhead
    for i in range(100):
        logger.log("INFO", "WARMUP", f"warmup message {i}")
    
    # Performance measurement
    latencies = []
    test_message = "Performance test message with some detail"
    
    # Test 1000 individual log operations
    for i in range(1000):
        start_time = time.perf_counter_ns()
        logger.log("INFO", "PERF_TEST", f"{test_message} #{i}")
        end_time = time.perf_counter_ns()
        
        latency_ns = end_time - start_time
        latency_ms = latency_ns / 1_000_000
        latencies.append(latency_ms)
    
    # Calculate statistics
    mean_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
    max_latency = max(latencies)
    
    print(f"Logging Performance Results:")
    print(f"  Mean latency: {mean_latency:.4f}ms")
    print(f"  Median latency: {median_latency:.4f}ms")
    print(f"  95th percentile: {p95_latency:.4f}ms")
    print(f"  Maximum latency: {max_latency:.4f}ms")
    
    # PASS CRITERIA - ALL must be true:
    assert mean_latency < 1.0, f"Mean latency {mean_latency:.4f}ms exceeds 1ms requirement"
    assert median_latency < 1.0, f"Median latency {median_latency:.4f}ms exceeds 1ms requirement"
    assert p95_latency < 1.5, f"95th percentile {p95_latency:.4f}ms exceeds 1.5ms tolerance"
    assert max_latency < 5.0, f"Maximum latency {max_latency:.4f}ms exceeds 5ms absolute limit"
    
    print("✓ Single operation latency test PASSED")


def test_concurrent_logging_thread_safety():
    """Test thread-safe concurrent logging without deadlocks"""
    
    from high_performance_logger import HighPerformanceLogger
    
    # Initialize logger
    logger = HighPerformanceLogger(
        buffer_size=50000,
        log_level="INFO",
        enable_file_output=False
    )
    
    print("Testing concurrent logging thread safety...")
    
    # Test configuration
    num_threads = 10
    messages_per_thread = 500
    total_expected_messages = num_threads * messages_per_thread
    
    # Shared state for monitoring
    completion_times = []
    thread_errors = []
    thread_lock = threading.Lock()
    
    def worker_thread(thread_id):
        """Worker thread that logs messages concurrently"""
        try:
            thread_start = time.perf_counter()
            
            for i in range(messages_per_thread):
                message = f"Thread-{thread_id:02d} message {i:03d}"
                logger.log("INFO", f"THREAD_{thread_id}", message)
                
                # Simulate variable workload
                if i % 100 == 0:
                    time.sleep(0.001)  # 1ms pause every 100 messages
            
            thread_end = time.perf_counter()
            
            with thread_lock:
                completion_times.append(thread_end - thread_start)
                
        except Exception as e:
            with thread_lock:
                thread_errors.append(f"Thread {thread_id}: {e}")
    
    # Start concurrent threads
    start_time = time.perf_counter()
    threads = []
    
    for thread_id in range(num_threads):
        thread = threading.Thread(target=worker_thread, args=(thread_id,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete with timeout
    for thread in threads:
        thread.join(timeout=30.0)  # 30 second timeout
        if thread.is_alive():
            pytest.fail("Thread failed to complete within timeout - possible deadlock")
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    # Get final log count
    log_count = logger.get_log_count()
    
    print(f"Concurrent Logging Results:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Expected messages: {total_expected_messages}")
    print(f"  Actual messages logged: {log_count}")
    print(f"  Average thread completion: {statistics.mean(completion_times):.3f}s")
    print(f"  Thread errors: {len(thread_errors)}")
    
    # PASS CRITERIA - ALL must be true:
    assert len(thread_errors) == 0, f"Thread errors occurred: {thread_errors}"
    assert log_count >= total_expected_messages * 0.95, f"Lost messages: expected ~{total_expected_messages}, got {log_count}"
    assert total_time < 15.0, f"Concurrent logging took {total_time:.3f}s (>15s timeout)"
    
    print("✓ Concurrent logging thread safety test PASSED")


def test_high_frequency_logging_no_degradation():
    """Test sustained high-frequency logging without performance degradation"""
    
    from high_performance_logger import HighPerformanceLogger
    
    # Initialize logger with larger buffer for sustained load
    logger = HighPerformanceLogger(
        buffer_size=100000,
        log_level="INFO", 
        enable_file_output=False
    )
    
    print("Testing high-frequency logging without degradation...")
    
    # Test parameters
    batch_size = 1000
    num_batches = 10
    total_messages = batch_size * num_batches
    
    batch_times = []
    
    # Run batches of high-frequency logging
    for batch_num in range(num_batches):
        batch_start = time.perf_counter()
        
        # Log batch_size messages as fast as possible
        for i in range(batch_size):
            message = f"High-freq batch {batch_num:02d} message {i:04d}"
            logger.log("INFO", "HIGH_FREQ", message)
        
        batch_end = time.perf_counter()
        batch_time = batch_end - batch_start
        batch_times.append(batch_time)
        
        # Calculate messages per second for this batch
        msgs_per_sec = batch_size / batch_time
        print(f"  Batch {batch_num + 1:2d}: {batch_time:.4f}s ({msgs_per_sec:.0f} msg/s)")
        
        # Short pause between batches
        time.sleep(0.1)
    
    # Performance analysis
    first_batch_time = batch_times[0]
    last_batch_time = batch_times[-1]
    mean_batch_time = statistics.mean(batch_times)
    degradation_pct = ((last_batch_time - first_batch_time) / first_batch_time) * 100
    
    total_time = sum(batch_times)
    overall_msgs_per_sec = total_messages / total_time
    
    print(f"High-Frequency Logging Results:")
    print(f"  Total messages: {total_messages}")
    print(f"  Total logging time: {total_time:.3f}s")
    print(f"  Overall rate: {overall_msgs_per_sec:.0f} messages/sec")
    print(f"  First batch time: {first_batch_time:.4f}s")
    print(f"  Last batch time: {last_batch_time:.4f}s")
    print(f"  Performance degradation: {degradation_pct:.2f}%")
    
    # PASS CRITERIA - ALL must be true:
    assert overall_msgs_per_sec > 5000, f"Logging rate {overall_msgs_per_sec:.0f} msg/s below 5000 requirement"
    assert degradation_pct < 20, f"Performance degradation {degradation_pct:.2f}% exceeds 20% limit"
    assert mean_batch_time < 0.5, f"Mean batch time {mean_batch_time:.4f}s exceeds 0.5s limit"
    
    print("✓ High-frequency logging degradation test PASSED")


def test_memory_usage_circular_buffer():
    """Test memory usage remains bounded with circular buffers"""
    
    from high_performance_logger import HighPerformanceLogger
    
    print("Testing circular buffer memory efficiency...")
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Initialize logger with small circular buffer
    buffer_size = 5000
    logger = HighPerformanceLogger(
        buffer_size=buffer_size,
        log_level="INFO",
        enable_file_output=False
    )
    
    # Fill buffer beyond capacity multiple times
    messages_to_log = buffer_size * 5  # 5x buffer capacity
    
    print(f"Logging {messages_to_log} messages to {buffer_size}-entry circular buffer...")
    
    # Log many messages to exceed buffer capacity
    for i in range(messages_to_log):
        long_message = f"Memory test message {i:06d} with extra content to increase memory pressure " * 5
        logger.log("INFO", "MEMORY_TEST", long_message)
        
        # Check memory periodically
        if i % 1000 == 0:
            current_memory = process.memory_info().rss / 1024 / 1024
            print(f"  After {i:5d} messages: {current_memory:.2f} MB")
    
    # Final memory measurement
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    
    # Force garbage collection
    gc.collect()
    gc_memory = process.memory_info().rss / 1024 / 1024
    gc_improvement = final_memory - gc_memory
    
    # Buffer should contain only latest entries
    buffer_contents = logger.get_recent_logs(count=buffer_size + 100)
    actual_buffer_size = len(buffer_contents)
    
    print(f"Memory Usage Results:")
    print(f"  Initial memory: {initial_memory:.2f} MB")
    print(f"  Final memory: {final_memory:.2f} MB")
    print(f"  After GC: {gc_memory:.2f} MB")
    print(f"  Memory increase: {memory_increase:.2f} MB")
    print(f"  GC improvement: {gc_improvement:.2f} MB")
    print(f"  Buffer capacity: {buffer_size}")
    print(f"  Actual buffer size: {actual_buffer_size}")
    print(f"  Messages logged: {messages_to_log}")
    
    # PASS CRITERIA - ALL must be true:
    assert memory_increase < 50, f"Memory increase {memory_increase:.2f}MB exceeds 50MB limit"
    assert actual_buffer_size <= buffer_size, f"Buffer size {actual_buffer_size} exceeds capacity {buffer_size}"
    assert gc_improvement > 0 or memory_increase < 10, "Memory not properly released after GC"
    
    print("✓ Circular buffer memory efficiency test PASSED")


def test_log_rotation_and_storage_optimization():
    """Test log rotation and storage optimization"""
    
    from high_performance_logger import HighPerformanceLogger
    import tempfile
    import shutil
    
    print("Testing log rotation and storage optimization...")
    
    # Create temporary directory for log files
    temp_dir = tempfile.mkdtemp(prefix="webgcs_log_test_")
    
    try:
        # Initialize logger with file output and rotation
        logger = HighPerformanceLogger(
            buffer_size=1000,
            log_level="INFO",
            enable_file_output=True,
            log_file_path=os.path.join(temp_dir, "test.log"),
            max_file_size_mb=1,  # Small file for testing
            max_log_files=3
        )
        
        # Generate enough logs to trigger rotation
        large_message = "X" * 1000  # 1KB message
        rotation_triggered = False
        
        for i in range(2000):  # 2MB of data
            logger.log("INFO", "ROTATION_TEST", f"Message {i:04d}: {large_message}")
            
            # Check if rotation occurred
            if i % 200 == 0:
                log_files = [f for f in os.listdir(temp_dir) if f.endswith('.log')]
                if len(log_files) > 1:
                    rotation_triggered = True
                    print(f"  Log rotation triggered after {i} messages")
        
        # Final file system check
        log_files = [f for f in os.listdir(temp_dir) if f.endswith('.log')]
        log_files.sort()
        
        total_log_size = 0
        for log_file in log_files:
            file_path = os.path.join(temp_dir, log_file)
            file_size = os.path.getsize(file_path)
            total_log_size += file_size
            print(f"  Log file: {log_file} ({file_size / 1024:.1f} KB)")
        
        # Test log retrieval across rotated files
        recent_logs = logger.get_recent_logs(count=100)
        
        print(f"Log Rotation Results:")
        print(f"  Total log files: {len(log_files)}")
        print(f"  Total log size: {total_log_size / 1024:.1f} KB")
        print(f"  Rotation triggered: {rotation_triggered}")
        print(f"  Recent logs retrievable: {len(recent_logs)}")
        
        # PASS CRITERIA - ALL must be true:
        assert rotation_triggered, "Log rotation was not triggered"
        assert len(log_files) <= 4, f"Too many log files: {len(log_files)} (expected ≤4)"
        assert len(recent_logs) > 0, "No recent logs retrievable"
        assert total_log_size < 5 * 1024 * 1024, f"Total log size {total_log_size / 1024 / 1024:.2f}MB too large"
        
        print("✓ Log rotation and storage optimization test PASSED")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_concurrent_read_write_operations():
    """Test concurrent read and write operations without conflicts"""
    
    from high_performance_logger import HighPerformanceLogger
    
    print("Testing concurrent read/write operations...")
    
    logger = HighPerformanceLogger(
        buffer_size=10000,
        log_level="INFO",
        enable_file_output=False
    )
    
    # Shared state
    read_operations = []
    write_operations = []
    errors = []
    operation_lock = threading.Lock()
    
    def writer_thread(thread_id, num_messages):
        """Thread that continuously writes log messages"""
        try:
            start_time = time.perf_counter()
            
            for i in range(num_messages):
                message = f"Writer-{thread_id} message {i:04d}"
                logger.log("INFO", f"WRITER_{thread_id}", message)
                
                if i % 100 == 0:
                    time.sleep(0.001)  # Brief pause
            
            end_time = time.perf_counter()
            
            with operation_lock:
                write_operations.append({
                    'thread_id': thread_id,
                    'messages': num_messages,
                    'time': end_time - start_time
                })
                
        except Exception as e:
            with operation_lock:
                errors.append(f"Writer-{thread_id}: {e}")
    
    def reader_thread(thread_id, num_reads):
        """Thread that continuously reads log messages"""
        try:
            start_time = time.perf_counter()
            read_count = 0
            
            for i in range(num_reads):
                logs = logger.get_recent_logs(count=100)
                read_count += len(logs)
                
                if i % 10 == 0:
                    time.sleep(0.002)  # Brief pause
            
            end_time = time.perf_counter()
            
            with operation_lock:
                read_operations.append({
                    'thread_id': thread_id,
                    'reads': num_reads,
                    'logs_read': read_count,
                    'time': end_time - start_time
                })
                
        except Exception as e:
            with operation_lock:
                errors.append(f"Reader-{thread_id}: {e}")
    
    # Start concurrent read/write operations
    threads = []
    
    # Start 3 writer threads
    for i in range(3):
        thread = threading.Thread(target=writer_thread, args=(i, 1000))
        threads.append(thread)
        thread.start()
    
    # Start 2 reader threads
    for i in range(2):
        thread = threading.Thread(target=reader_thread, args=(i, 100))
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    start_time = time.perf_counter()
    for thread in threads:
        thread.join(timeout=20.0)
        if thread.is_alive():
            pytest.fail("Thread did not complete within timeout")
    
    total_time = time.perf_counter() - start_time
    
    # Results analysis
    total_writes = sum(op['messages'] for op in write_operations)
    total_reads = sum(op['reads'] for op in read_operations)
    total_logs_read = sum(op['logs_read'] for op in read_operations)
    
    print(f"Concurrent Read/Write Results:")
    print(f"  Total time: {total_time:.3f}s")
    print(f"  Write operations: {len(write_operations)}")
    print(f"  Read operations: {len(read_operations)}")
    print(f"  Messages written: {total_writes}")
    print(f"  Read requests: {total_reads}")
    print(f"  Total logs read: {total_logs_read}")
    print(f"  Errors: {len(errors)}")
    
    # PASS CRITERIA - ALL must be true:
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(write_operations) == 3, f"Expected 3 write operations, got {len(write_operations)}"
    assert len(read_operations) == 2, f"Expected 2 read operations, got {len(read_operations)}"
    assert total_writes > 0, "No messages were written"
    assert total_logs_read > 0, "No logs were read"
    
    print("✓ Concurrent read/write operations test PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST-007: Logging Performance Validation")
    print("=" * 60)
    
    try:
        test_single_log_operation_latency()
        test_concurrent_logging_thread_safety()
        test_high_frequency_logging_no_degradation()
        test_memory_usage_circular_buffer()
        test_log_rotation_and_storage_optimization()
        test_concurrent_read_write_operations()
        
        print("=" * 60)
        print("TEST-007 PASSED: All logging performance requirements validated")
        print("=" * 60)
        
    except ImportError as e:
        print(f"EXPECTED FAILURE (RED PHASE): {e}")
        print("Implementation required: high_performance_logger.py")
        print("This test should FAIL until the logging system is implemented.")
        
    except Exception as e:
        print(f"TEST-007 FAILED: {e}")
        raise
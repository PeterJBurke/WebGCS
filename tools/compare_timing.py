#!/usr/bin/env python3
"""
Performance Benchmarking Tool for WebGCS Logging System

This tool provides detailed performance analysis and comparison
between different logging implementations to validate the <1ms
latency requirement for TEST-007.

Usage:
    python compare_timing.py                    # Benchmark current implementation
    python compare_timing.py --baseline-only    # Test baseline Python logging
    python compare_timing.py --compare          # Compare multiple implementations
    python compare_timing.py --full-analysis    # Complete performance analysis
"""

import argparse
import time
import statistics
import threading
import logging
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import psutil


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for logging systems"""
    
    def __init__(self):
        self.results = {}
        
    def benchmark_baseline_logging(self, num_messages=1000):
        """Benchmark baseline Python logging performance"""
        print("Benchmarking baseline Python logging...")
        
        # Setup baseline logger
        logger = logging.getLogger('baseline_test')
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add memory handler (no file I/O)
        handler = logging.StreamHandler(open(os.devnull, 'w'))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Warm up
        for i in range(100):
            logger.info(f"Warmup message {i}")
        
        # Benchmark
        latencies = []
        message = "Baseline performance test message with details"
        
        for i in range(num_messages):
            start_time = time.perf_counter_ns()
            logger.info(f"{message} #{i}")
            end_time = time.perf_counter_ns()
            
            latency_ms = (end_time - start_time) / 1_000_000
            latencies.append(latency_ms)
        
        # Cleanup
        handler.close()
        logger.removeHandler(handler)
        
        return {
            'implementation': 'Baseline Python Logging',
            'latencies': latencies,
            'mean': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'p95': statistics.quantiles(latencies, n=20)[18],
            'max': max(latencies),
            'min': min(latencies),
            'count': len(latencies)
        }
    
    def benchmark_high_performance_logger(self, num_messages=1000):
        """Benchmark high performance logger implementation"""
        print("Benchmarking high performance logger...")
        
        try:
            from high_performance_logger import HighPerformanceLogger
            
            # Setup high performance logger
            logger = HighPerformanceLogger(
                buffer_size=10000,
                log_level="INFO",
                enable_file_output=False
            )
            
            # Warm up
            for i in range(100):
                logger.log("INFO", "WARMUP", f"warmup message {i}")
            
            # Benchmark
            latencies = []
            message = "High performance test message with details"
            
            for i in range(num_messages):
                start_time = time.perf_counter_ns()
                logger.log("INFO", "PERF_TEST", f"{message} #{i}")
                end_time = time.perf_counter_ns()
                
                latency_ms = (end_time - start_time) / 1_000_000
                latencies.append(latency_ms)
            
            return {
                'implementation': 'High Performance Logger',
                'latencies': latencies,
                'mean': statistics.mean(latencies),
                'median': statistics.median(latencies),
                'p95': statistics.quantiles(latencies, n=20)[18],
                'max': max(latencies),
                'min': min(latencies),
                'count': len(latencies)
            }
            
        except ImportError:
            return {
                'implementation': 'High Performance Logger',
                'error': 'Not implemented - high_performance_logger module not found'
            }
    
    def benchmark_concurrent_performance(self, num_threads=5, messages_per_thread=200):
        """Benchmark concurrent logging performance"""
        print(f"Benchmarking concurrent performance ({num_threads} threads)...")
        
        try:
            from high_performance_logger import HighPerformanceLogger
            
            logger = HighPerformanceLogger(
                buffer_size=50000,
                log_level="INFO",
                enable_file_output=False
            )
            
            completion_times = []
            errors = []
            lock = threading.Lock()
            
            def worker_thread(thread_id):
                try:
                    start_time = time.perf_counter()
                    
                    for i in range(messages_per_thread):
                        message = f"Thread-{thread_id} concurrent message {i}"
                        logger.log("INFO", f"THREAD_{thread_id}", message)
                    
                    end_time = time.perf_counter()
                    
                    with lock:
                        completion_times.append(end_time - start_time)
                        
                except Exception as e:
                    with lock:
                        errors.append(f"Thread {thread_id}: {e}")
            
            # Run concurrent benchmark
            overall_start = time.perf_counter()
            threads = []
            
            for i in range(num_threads):
                thread = threading.Thread(target=worker_thread, args=(i,))
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join(timeout=10.0)
            
            overall_end = time.perf_counter()
            
            total_messages = num_threads * messages_per_thread
            overall_time = overall_end - overall_start
            msgs_per_sec = total_messages / overall_time if overall_time > 0 else 0
            
            return {
                'implementation': 'High Performance Logger (Concurrent)',
                'total_messages': total_messages,
                'total_time': overall_time,
                'messages_per_second': msgs_per_sec,
                'thread_completion_times': completion_times,
                'errors': errors,
                'threads': num_threads
            }
            
        except ImportError:
            return {
                'implementation': 'High Performance Logger (Concurrent)',
                'error': 'Not implemented - high_performance_logger module not found'
            }
    
    def benchmark_memory_usage(self, num_messages=10000):
        """Benchmark memory usage during logging"""
        print("Benchmarking memory usage...")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            from high_performance_logger import HighPerformanceLogger
            
            logger = HighPerformanceLogger(
                buffer_size=5000,  # Smaller than message count to test circular behavior
                log_level="INFO",
                enable_file_output=False
            )
            
            memory_samples = []
            
            for i in range(num_messages):
                message = f"Memory test message {i} with extra content " * 3
                logger.log("INFO", "MEMORY_TEST", message)
                
                if i % 1000 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory - initial_memory)
            
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            return {
                'implementation': 'High Performance Logger (Memory)',
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_increase_mb': memory_increase,
                'memory_samples': memory_samples,
                'messages_logged': num_messages
            }
            
        except ImportError:
            return {
                'implementation': 'High Performance Logger (Memory)',
                'error': 'Not implemented - high_performance_logger module not found'
            }
    
    def print_results(self, results):
        """Print formatted benchmark results"""
        print("=" * 80)
        print(f"BENCHMARK RESULTS: {results['implementation']}")
        print("=" * 80)
        
        if 'error' in results:
            print(f"❌ ERROR: {results['error']}")
            return
        
        if 'latencies' in results:
            # Single-threaded latency results
            print(f"Messages tested: {results['count']}")
            print(f"Mean latency: {results['mean']:.4f}ms")
            print(f"Median latency: {results['median']:.4f}ms")
            print(f"95th percentile: {results['p95']:.4f}ms")
            print(f"Maximum latency: {results['max']:.4f}ms")
            print(f"Minimum latency: {results['min']:.4f}ms")
            
            # Performance assessment
            if results['mean'] < 1.0:
                print("✅ PASS: Mean latency meets <1ms requirement")
            else:
                print("❌ FAIL: Mean latency exceeds 1ms requirement")
            
            if results['p95'] < 1.5:
                print("✅ PASS: 95th percentile meets <1.5ms tolerance")
            else:
                print("❌ FAIL: 95th percentile exceeds 1.5ms tolerance")
        
        elif 'messages_per_second' in results:
            # Concurrent performance results
            print(f"Total messages: {results['total_messages']}")
            print(f"Total time: {results['total_time']:.3f}s")
            print(f"Messages per second: {results['messages_per_second']:.0f}")
            print(f"Threads: {results['threads']}")
            print(f"Errors: {len(results['errors'])}")
            
            if results['messages_per_second'] > 5000:
                print("✅ PASS: Throughput meets >5000 msg/s requirement")
            else:
                print("❌ FAIL: Throughput below 5000 msg/s requirement")
        
        elif 'memory_increase_mb' in results:
            # Memory usage results
            print(f"Messages logged: {results['messages_logged']}")
            print(f"Initial memory: {results['initial_memory_mb']:.2f} MB")
            print(f"Final memory: {results['final_memory_mb']:.2f} MB")
            print(f"Memory increase: {results['memory_increase_mb']:.2f} MB")
            
            if results['memory_increase_mb'] < 50:
                print("✅ PASS: Memory usage meets <50MB increase limit")
            else:
                print("❌ FAIL: Memory usage exceeds 50MB increase limit")
        
        print()
    
    def run_full_analysis(self):
        """Run complete performance analysis"""
        print("Starting comprehensive logging performance analysis...")
        print(f"Platform: {sys.platform}")
        print(f"Python: {sys.version}")
        print(f"Process ID: {os.getpid()}")
        print()
        
        # Baseline benchmark
        baseline_results = self.benchmark_baseline_logging(1000)
        self.results['baseline'] = baseline_results
        self.print_results(baseline_results)
        
        # High performance logger benchmark
        hp_results = self.benchmark_high_performance_logger(1000)
        self.results['high_performance'] = hp_results
        self.print_results(hp_results)
        
        # Concurrent performance benchmark
        concurrent_results = self.benchmark_concurrent_performance(5, 200)
        self.results['concurrent'] = concurrent_results
        self.print_results(concurrent_results)
        
        # Memory usage benchmark
        memory_results = self.benchmark_memory_usage(10000)
        self.results['memory'] = memory_results
        self.print_results(memory_results)
        
        # Comparison summary
        self.print_comparison_summary()
    
    def print_comparison_summary(self):
        """Print comparison summary between implementations"""
        print("=" * 80)
        print("PERFORMANCE COMPARISON SUMMARY")
        print("=" * 80)
        
        baseline = self.results.get('baseline', {})
        hp_logger = self.results.get('high_performance', {})
        
        if 'error' not in baseline and 'error' not in hp_logger:
            if 'mean' in baseline and 'mean' in hp_logger:
                improvement_factor = baseline['mean'] / hp_logger['mean']
                print(f"Latency improvement: {improvement_factor:.2f}x faster")
                print(f"Baseline mean: {baseline['mean']:.4f}ms")
                print(f"High-perf mean: {hp_logger['mean']:.4f}ms")
        
        # Requirements compliance summary
        print("\n📋 REQUIREMENTS COMPLIANCE:")
        
        if 'high_performance' in self.results and 'error' not in self.results['high_performance']:
            hp = self.results['high_performance']
            if 'mean' in hp:
                req_1ms = "✅ PASS" if hp['mean'] < 1.0 else "❌ FAIL"
                print(f"  <1ms latency requirement: {req_1ms} ({hp['mean']:.4f}ms)")
        
        if 'concurrent' in self.results and 'error' not in self.results['concurrent']:
            conc = self.results['concurrent']
            if 'messages_per_second' in conc:
                req_throughput = "✅ PASS" if conc['messages_per_second'] > 5000 else "❌ FAIL"
                print(f"  >5000 msg/s throughput: {req_throughput} ({conc['messages_per_second']:.0f} msg/s)")
        
        if 'memory' in self.results and 'error' not in self.results['memory']:
            mem = self.results['memory']
            if 'memory_increase_mb' in mem:
                req_memory = "✅ PASS" if mem['memory_increase_mb'] < 50 else "❌ FAIL"
                print(f"  <50MB memory increase: {req_memory} ({mem['memory_increase_mb']:.2f}MB)")


def main():
    """Main entry point for performance benchmarking"""
    parser = argparse.ArgumentParser(description='WebGCS Logging Performance Benchmarking')
    parser.add_argument('--baseline-only', action='store_true', 
                       help='Only benchmark baseline Python logging')
    parser.add_argument('--compare', action='store_true',
                       help='Compare baseline vs high-performance implementations')
    parser.add_argument('--full-analysis', action='store_true',
                       help='Run complete performance analysis (default)')
    parser.add_argument('--messages', type=int, default=1000,
                       help='Number of messages for latency testing (default: 1000)')
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark()
    
    if args.baseline_only:
        print("Running baseline-only benchmark...")
        results = benchmark.benchmark_baseline_logging(args.messages)
        benchmark.print_results(results)
        
    elif args.compare:
        print("Running comparison benchmark...")
        baseline = benchmark.benchmark_baseline_logging(args.messages)
        benchmark.results['baseline'] = baseline
        benchmark.print_results(baseline)
        
        hp_logger = benchmark.benchmark_high_performance_logger(args.messages)
        benchmark.results['high_performance'] = hp_logger
        benchmark.print_results(hp_logger)
        
        benchmark.print_comparison_summary()
        
    else:
        # Default: full analysis
        benchmark.run_full_analysis()
    
    print("Benchmarking complete!")


if __name__ == "__main__":
    main()
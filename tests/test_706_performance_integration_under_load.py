"""
TEST-706: Performance Integration Under Load

Tests system performance with rapid user interactions and stress conditions.

Validates:
- System performance with rapid user interactions
- Telemetry processing under high update rates
- Concurrent user actions and command queuing
- System stability during stress conditions
"""

import pytest
import time
import asyncio
import threading
import statistics
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
import concurrent.futures
import psutil
import os

from src.web.app_factory import initialize_app


class TestPerformanceIntegrationUnderLoad:
    """Performance integration under load tests."""

    @pytest.fixture(scope="class")
    def performance_app(self):
        """Create application optimized for performance testing."""
        app, socketio = initialize_app()
        
        app.config.update({
            'TESTING': True,
            'WEB_SERVER_PORT': 5002,
            'TELEMETRY_UPDATE_INTERVAL': 0.1,  # 10Hz
            'COMMAND_ACK_TIMEOUT': 2.0,  # Faster for load testing
            'HEARTBEAT_TIMEOUT': 15
        })
        
        def run_server():
            socketio.run(app, host='localhost', port=5002, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        yield app, socketio
        
        if hasattr(app, 'mavlink_service'):
            app.mavlink_service.stop()

    def test_telemetry_processing_under_load(self, performance_app):
        """Test telemetry processing performance under high load."""
        app, socketio = performance_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone for load testing")
        
        time.sleep(2)
        
        # Performance metrics collection
        telemetry_times = []
        cpu_usage_samples = []
        memory_usage_samples = []
        
        # Get current process for monitoring
        process = psutil.Process(os.getpid())
        
        # High-frequency telemetry requests (simulating heavy load)
        start_time = time.time()
        test_duration = 10.0  # 10 seconds of load testing
        request_count = 0
        
        while time.time() - start_time < test_duration:
            # Measure telemetry request performance
            telemetry_start = time.time()
            telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            telemetry_duration = time.time() - telemetry_start
            
            telemetry_times.append(telemetry_duration)
            
            # Sample system resources periodically
            if request_count % 50 == 0:  # Sample every 50 requests
                try:
                    cpu_percent = process.cpu_percent()
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    
                    cpu_usage_samples.append(cpu_percent)
                    memory_usage_samples.append(memory_mb)
                except:
                    pass  # Skip if monitoring fails
            
            request_count += 1
            
            # Brief sleep to prevent overwhelming the system
            time.sleep(0.001)  # 1ms between requests
        
        total_time = time.time() - start_time
        
        # Performance analysis
        avg_telemetry_time = statistics.mean(telemetry_times)
        max_telemetry_time = max(telemetry_times)
        min_telemetry_time = min(telemetry_times)
        p95_telemetry_time = statistics.quantiles(telemetry_times, n=20)[18]  # 95th percentile
        
        # Performance requirements validation
        assert avg_telemetry_time < 0.001, f"Average telemetry time too slow: {avg_telemetry_time:.4f}s"
        assert max_telemetry_time < 0.01, f"Max telemetry time too slow: {max_telemetry_time:.4f}s"
        assert p95_telemetry_time < 0.002, f"95th percentile too slow: {p95_telemetry_time:.4f}s"
        
        # Request rate validation
        requests_per_second = request_count / total_time
        assert requests_per_second >= 500, f"Request rate too low: {requests_per_second:.1f} req/s"
        
        # Resource usage validation
        if cpu_usage_samples:
            avg_cpu = statistics.mean(cpu_usage_samples)
            max_cpu = max(cpu_usage_samples)
            print(f"CPU usage: avg={avg_cpu:.1f}%, max={max_cpu:.1f}%")
            
            # CPU usage should be reasonable under load
            assert avg_cpu < 80.0, f"Average CPU usage too high: {avg_cpu:.1f}%"
        
        if memory_usage_samples:
            memory_growth = max(memory_usage_samples) - min(memory_usage_samples)
            print(f"Memory usage: {min(memory_usage_samples):.1f}MB - {max(memory_usage_samples):.1f}MB")
            
            # Memory should not grow excessively
            assert memory_growth < 100, f"Memory growth too high: {memory_growth:.1f}MB"

    def test_concurrent_command_processing(self, performance_app):
        """Test concurrent command processing performance."""
        app, socketio = performance_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone for concurrent testing")
        
        time.sleep(2)
        
        # Test concurrent command workers
        def command_worker(worker_id, num_commands, results_dict):
            worker_results = {
                'commands': [],
                'total_time': 0,
                'success_count': 0,
                'error_count': 0
            }
            
            start_time = time.time()
            
            for i in range(num_commands):
                cmd_start = time.time()
                
                try:
                    # Alternate between ARM and DISARM commands
                    if i % 2 == 0:
                        result = mavlink_service.command_sender.arm_vehicle()
                    else:
                        result = mavlink_service.command_sender.disarm_vehicle()
                    
                    cmd_duration = time.time() - cmd_start
                    
                    worker_results['commands'].append({
                        'command_id': i,
                        'duration': cmd_duration,
                        'success': result
                    })
                    
                    if result:
                        worker_results['success_count'] += 1
                    else:
                        worker_results['error_count'] += 1
                
                except Exception as e:
                    worker_results['error_count'] += 1
                    worker_results['commands'].append({
                        'command_id': i,
                        'duration': time.time() - cmd_start,
                        'success': False,
                        'error': str(e)
                    })
                
                # Brief delay between commands
                time.sleep(0.1)
            
            worker_results['total_time'] = time.time() - start_time
            results_dict[worker_id] = worker_results
        
        # Run multiple concurrent command workers
        num_workers = 5
        commands_per_worker = 10
        worker_results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for worker_id in range(num_workers):
                future = executor.submit(
                    command_worker, 
                    worker_id, 
                    commands_per_worker, 
                    worker_results
                )
                futures.append(future)
            
            # Wait for all workers to complete
            concurrent.futures.wait(futures, timeout=60)
        
        # Performance analysis
        total_commands = num_workers * commands_per_worker
        all_command_times = []
        total_successes = 0
        total_errors = 0
        
        for worker_id, results in worker_results.items():
            total_successes += results['success_count']
            total_errors += results['error_count']
            
            for cmd in results['commands']:
                all_command_times.append(cmd['duration'])
        
        # Concurrent performance validation
        if all_command_times:
            avg_command_time = statistics.mean(all_command_times)
            max_command_time = max(all_command_times)
            
            # Commands should complete within reasonable time even under load
            assert avg_command_time < 3.0, f"Average command time too slow: {avg_command_time:.2f}s"
            assert max_command_time < 10.0, f"Max command time too slow: {max_command_time:.2f}s"
        
        # Success rate should be reasonable (some failures expected under load)
        success_rate = total_successes / (total_successes + total_errors) if (total_successes + total_errors) > 0 else 0
        print(f"Concurrent command success rate: {success_rate:.2f} ({total_successes}/{total_successes + total_errors})")
        
        # At least some commands should succeed
        assert success_rate >= 0.1, f"Success rate too low: {success_rate:.2f}"

    @pytest.mark.asyncio
    async def test_web_interface_under_rapid_interactions(self, performance_app):
        """Test web interface performance under rapid user interactions."""
        app, socketio = performance_app
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_selector('#connection-panel')
                
                # Connect first
                await page.click('#connect-btn')
                await page.wait_for_function(
                    "document.querySelector('#connection-status').textContent.includes('Connected')",
                    timeout=15000
                )
                
                # Test rapid button interactions
                interaction_times = []
                buttons_to_test = ['#arm-btn', '#disarm-btn', '#takeoff-btn', '#land-btn', '#rtl-btn']
                
                for round_num in range(3):  # 3 rounds of rapid interactions
                    round_start = time.time()
                    
                    for button_selector in buttons_to_test:
                        try:
                            button = page.locator(button_selector)
                            
                            if await button.is_visible():
                                interaction_start = time.time()
                                await button.click()
                                
                                # Handle any confirmation dialogs quickly
                                try:
                                    confirmation_modal = page.locator('#safety-confirmation-modal')
                                    await confirmation_modal.wait_for(state='visible', timeout=1000)
                                    
                                    # Randomly confirm or cancel to test both paths
                                    if round_num % 2 == 0:
                                        await page.click('#confirm-action-btn')
                                    else:
                                        await page.click('#cancel-action-btn')
                                        
                                except:
                                    pass  # No confirmation dialog
                                
                                interaction_duration = time.time() - interaction_start
                                interaction_times.append(interaction_duration)
                                
                                # Brief pause between interactions
                                await asyncio.sleep(0.1)
                        
                        except Exception as e:
                            print(f"Interaction error for {button_selector}: {e}")
                    
                    round_duration = time.time() - round_start
                    print(f"Round {round_num + 1} duration: {round_duration:.2f}s")
                    
                    # Pause between rounds
                    await asyncio.sleep(0.5)
                
                # Analyze interaction performance
                if interaction_times:
                    avg_interaction_time = statistics.mean(interaction_times)
                    max_interaction_time = max(interaction_times)
                    
                    # UI interactions should be responsive
                    assert avg_interaction_time < 2.0, f"Average interaction too slow: {avg_interaction_time:.2f}s"
                    assert max_interaction_time < 5.0, f"Max interaction too slow: {max_interaction_time:.2f}s"
                
                # Test rapid navigation input changes
                navigation_times = []
                nav_inputs = ['#nav-latitude', '#nav-longitude', '#nav-altitude']
                
                for i in range(10):  # 10 rapid navigation updates
                    nav_start = time.time()
                    
                    try:
                        await page.fill('#nav-latitude', f'37.77{i:02d}')
                        await page.fill('#nav-longitude', f'-122.4{i:02d}')
                        await page.fill('#nav-altitude', f'{50 + i}')
                        
                        nav_duration = time.time() - nav_start
                        navigation_times.append(nav_duration)
                        
                    except Exception as e:
                        print(f"Navigation input error: {e}")
                    
                    await asyncio.sleep(0.05)  # Very rapid updates
                
                # Navigation input should be responsive
                if navigation_times:
                    avg_nav_time = statistics.mean(navigation_times)
                    assert avg_nav_time < 0.5, f"Navigation input too slow: {avg_nav_time:.3f}s"
                
                # Test system stability after rapid interactions
                final_status = await page.locator('#connection-status').text_content()
                assert 'Connected' in final_status or 'Disconnected' in final_status, \
                    "System should maintain valid state after rapid interactions"
                
            finally:
                await browser.close()

    def test_socketio_performance_under_load(self, performance_app):
        """Test SocketIO performance under high client load."""
        app, socketio = performance_app
        
        import socketio as sio_client
        
        # Start MAVLink service to generate telemetry
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone for SocketIO load testing")
        
        time.sleep(1)
        
        # Create multiple SocketIO clients to simulate load
        clients = []
        client_data = {}
        connection_times = []
        
        num_clients = 10  # Test with 10 concurrent clients
        
        try:
            # Connect all clients and measure connection time
            for client_id in range(num_clients):
                connect_start = time.time()
                
                try:
                    client = sio_client.SimpleClient()
                    client.connect('http://localhost:5002')
                    
                    connect_duration = time.time() - connect_start
                    connection_times.append(connect_duration)
                    
                    clients.append(client)
                    client_data[client_id] = {
                        'telemetry_count': 0,
                        'connection_events': 0,
                        'errors': 0
                    }
                    
                    # Set up event handlers for each client
                    def make_telemetry_handler(cid):
                        def handler(data):
                            client_data[cid]['telemetry_count'] += 1
                        return handler
                    
                    def make_connection_handler(cid):
                        def handler(data):
                            client_data[cid]['connection_events'] += 1
                        return handler
                    
                    client.on('telemetry_update', make_telemetry_handler(client_id))
                    client.on('connection_status_update', make_connection_handler(client_id))
                    
                except Exception as e:
                    client_data[client_id] = {'errors': 1, 'error_msg': str(e)}
            
            print(f"Connected {len(clients)} out of {num_clients} clients")
            
            # Connection performance analysis
            if connection_times:
                avg_connect_time = statistics.mean(connection_times)
                max_connect_time = max(connection_times)
                
                assert avg_connect_time < 2.0, f"Average connection time too slow: {avg_connect_time:.2f}s"
                assert max_connect_time < 5.0, f"Max connection time too slow: {max_connect_time:.2f}s"
            
            # Let clients receive telemetry for a period
            if clients:
                test_duration = 5.0  # 5 seconds of telemetry collection
                time.sleep(test_duration)
                
                # Analyze telemetry distribution
                telemetry_counts = [data.get('telemetry_count', 0) for data in client_data.values()]
                
                if telemetry_counts:
                    min_telemetry = min(telemetry_counts)
                    max_telemetry = max(telemetry_counts)
                    avg_telemetry = statistics.mean(telemetry_counts)
                    
                    print(f"Telemetry distribution: min={min_telemetry}, avg={avg_telemetry:.1f}, max={max_telemetry}")
                    
                    # All clients should receive reasonable amount of telemetry
                    assert avg_telemetry >= 20, f"Average telemetry count too low: {avg_telemetry:.1f}"
                    
                    # Distribution should not be too uneven
                    if max_telemetry > 0:
                        distribution_ratio = min_telemetry / max_telemetry
                        assert distribution_ratio >= 0.5, f"Telemetry distribution too uneven: {distribution_ratio:.2f}"
                
                # Test concurrent client interactions
                def client_interaction_worker(client, client_id, results_dict):
                    interaction_results = []
                    
                    for i in range(5):
                        try:
                            # Simple client interaction - just maintain connection
                            client.sleep(0.1)
                            interaction_results.append({'success': True})
                        except Exception as e:
                            interaction_results.append({'success': False, 'error': str(e)})
                    
                    results_dict[client_id] = interaction_results
                
                # Run concurrent interactions
                interaction_results = {}
                interaction_threads = []
                
                for i, client in enumerate(clients[:5]):  # Use first 5 clients for interaction test
                    thread = threading.Thread(
                        target=client_interaction_worker,
                        args=(client, i, interaction_results)
                    )
                    interaction_threads.append(thread)
                    thread.start()
                
                for thread in interaction_threads:
                    thread.join()
                
                # Analyze interaction performance
                total_interactions = sum(len(results) for results in interaction_results.values())
                successful_interactions = sum(
                    sum(1 for result in results if result['success']) 
                    for results in interaction_results.values()
                )
                
                if total_interactions > 0:
                    interaction_success_rate = successful_interactions / total_interactions
                    assert interaction_success_rate >= 0.8, \
                        f"Interaction success rate too low: {interaction_success_rate:.2f}"
        
        finally:
            # Cleanup all clients
            for client in clients:
                try:
                    client.disconnect()
                except:
                    pass

    def test_memory_performance_under_load(self, performance_app):
        """Test memory usage and performance under sustained load."""
        app, socketio = performance_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone for memory testing")
        
        time.sleep(1)
        
        # Get baseline memory usage
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run sustained load for memory leak detection
        load_duration = 15.0  # 15 seconds of sustained load
        memory_samples = []
        operation_count = 0
        
        start_time = time.time()
        
        while time.time() - start_time < load_duration:
            # Perform various operations
            
            # 1. Telemetry requests
            telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
            
            # 2. Status requests
            status = mavlink_service.get_status()
            
            # 3. Command operations (lightweight)
            pending_commands = mavlink_service.command_sender.get_pending_commands()
            
            operation_count += 3
            
            # Sample memory usage periodically
            if operation_count % 100 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append({
                    'timestamp': time.time() - start_time,
                    'memory_mb': current_memory,
                    'operations': operation_count
                })
            
            # Brief sleep to prevent overwhelming
            time.sleep(0.01)  # 10ms between operations
        
        # Memory performance analysis
        if memory_samples:
            initial_memory = memory_samples[0]['memory_mb']
            final_memory = memory_samples[-1]['memory_mb']
            max_memory = max(sample['memory_mb'] for sample in memory_samples)
            
            memory_growth = final_memory - initial_memory
            peak_memory_increase = max_memory - initial_memory
            
            print(f"Memory usage: baseline={baseline_memory:.1f}MB, "
                  f"initial={initial_memory:.1f}MB, final={final_memory:.1f}MB, "
                  f"growth={memory_growth:.1f}MB, peak_increase={peak_memory_increase:.1f}MB")
            
            # Memory should not grow significantly during sustained load
            assert memory_growth < 50, f"Memory growth too high: {memory_growth:.1f}MB"
            assert peak_memory_increase < 100, f"Peak memory increase too high: {peak_memory_increase:.1f}MB"
            
            # Operations per second
            ops_per_second = operation_count / load_duration
            print(f"Operations per second: {ops_per_second:.1f}")
            
            assert ops_per_second >= 200, f"Operation rate too low: {ops_per_second:.1f} ops/s"

    def test_system_stability_under_stress(self, performance_app):
        """Test overall system stability under stress conditions."""
        app, socketio = performance_app
        
        mavlink_service = app.mavlink_service
        if not mavlink_service.start():
            pytest.skip("Could not connect to drone for stress testing")
        
        time.sleep(2)
        
        # Multi-threaded stress test
        stress_results = {
            'telemetry_worker': {},
            'command_worker': {},
            'status_worker': {}
        }
        
        def telemetry_stress_worker(results_dict):
            worker_stats = {'requests': 0, 'errors': 0, 'avg_time': 0}
            times = []
            
            for i in range(100):
                try:
                    start = time.time()
                    telemetry = mavlink_service.message_processor.get_telemetry_snapshot()
                    duration = time.time() - start
                    
                    times.append(duration)
                    worker_stats['requests'] += 1
                    
                    if telemetry is None:
                        worker_stats['errors'] += 1
                        
                except Exception as e:
                    worker_stats['errors'] += 1
                
                time.sleep(0.01)  # 10ms between requests
            
            worker_stats['avg_time'] = statistics.mean(times) if times else 0
            results_dict['telemetry_worker'] = worker_stats
        
        def command_stress_worker(results_dict):
            worker_stats = {'commands': 0, 'successes': 0, 'errors': 0}
            
            for i in range(20):  # Fewer commands to avoid overwhelming drone
                try:
                    if i % 4 == 0:
                        result = mavlink_service.command_sender.arm_vehicle()
                    elif i % 4 == 1:
                        result = mavlink_service.command_sender.disarm_vehicle()
                    else:
                        # Just check status instead of sending more commands
                        result = mavlink_service.get_status() is not None
                    
                    worker_stats['commands'] += 1
                    
                    if result:
                        worker_stats['successes'] += 1
                    else:
                        worker_stats['errors'] += 1
                        
                except Exception as e:
                    worker_stats['errors'] += 1
                
                time.sleep(0.25)  # 250ms between commands
            
            results_dict['command_worker'] = worker_stats
        
        def status_stress_worker(results_dict):
            worker_stats = {'requests': 0, 'errors': 0, 'avg_time': 0}
            times = []
            
            for i in range(50):
                try:
                    start = time.time()
                    status = mavlink_service.get_status()
                    duration = time.time() - start
                    
                    times.append(duration)
                    worker_stats['requests'] += 1
                    
                    if status is None or not isinstance(status, dict):
                        worker_stats['errors'] += 1
                        
                except Exception as e:
                    worker_stats['errors'] += 1
                
                time.sleep(0.02)  # 20ms between requests
            
            worker_stats['avg_time'] = statistics.mean(times) if times else 0
            results_dict['status_worker'] = worker_stats
        
        # Run stress test workers concurrently
        stress_threads = [
            threading.Thread(target=telemetry_stress_worker, args=(stress_results,)),
            threading.Thread(target=command_stress_worker, args=(stress_results,)),
            threading.Thread(target=status_stress_worker, args=(stress_results,))
        ]
        
        stress_start_time = time.time()
        
        for thread in stress_threads:
            thread.start()
        
        for thread in stress_threads:
            thread.join()
        
        stress_duration = time.time() - stress_start_time
        
        print(f"Stress test completed in {stress_duration:.2f}s")
        
        # Analyze stress test results
        for worker_name, stats in stress_results.items():
            print(f"{worker_name}: {stats}")
            
            if 'requests' in stats:
                assert stats['requests'] > 0, f"{worker_name} made no requests"
                error_rate = stats['errors'] / stats['requests'] if stats['requests'] > 0 else 1
                assert error_rate < 0.2, f"{worker_name} error rate too high: {error_rate:.2f}"
                
                if 'avg_time' in stats and stats['avg_time'] > 0:
                    assert stats['avg_time'] < 0.01, f"{worker_name} avg response time too slow: {stats['avg_time']:.4f}s"
            
            if 'commands' in stats:
                assert stats['commands'] > 0, f"{worker_name} made no commands"
                # Command success rate can be lower due to drone state constraints
                success_rate = stats['successes'] / stats['commands'] if stats['commands'] > 0 else 0
                print(f"{worker_name} success rate: {success_rate:.2f}")
        
        # Verify system is still functional after stress test
        post_stress_status = mavlink_service.get_status()
        assert post_stress_status is not None, "System should remain functional after stress test"
        assert post_stress_status['mavlink_connected'], "Should maintain connection after stress test"
        
        # Verify threads are still running
        assert post_stress_status['service_threads']['message_processor'], \
            "Message processor should continue after stress"
        assert post_stress_status['service_threads']['telemetry_streamer'], \
            "Telemetry streamer should continue after stress"

    def teardown_method(self, method):
        """Cleanup after each test method."""
        time.sleep(0.5)
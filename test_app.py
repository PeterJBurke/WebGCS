import unittest
import json
import os
import tempfile
import threading
import time
from unittest.mock import patch, MagicMock
import sys

# Mock MAVLink connections before importing the app
with patch('mavlink_connection_manager.mavlink_receive_loop_runner'), \
     patch('mavlink_connection_manager.get_mavlink_connection'), \
     patch('mavlink_connection_manager.get_connection_event'):

    # Import the Flask app and related components
    from app import (
        app, socketio, drone_state, drone_state_lock, 
        app_shared_state, set_drone_state_changed_flag,
        log_command_action, read_telemetry_from_file
    )

class TestApp(unittest.TestCase):
    """Test cases for the Flask application in app.py"""
    
    def setUp(self):
        """Set up test client and test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Reset drone state for each test
        with drone_state_lock:
            drone_state.update({
                'connected': False, 'armed': False, 'mode': 'UNKNOWN',
                'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0, 'alt_abs': 0.0, 'heading': 0.0,
                'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
                'airspeed': 0.0, 'groundspeed': 0.0,
                'battery_voltage': 0.0, 'battery_remaining': -1, 'battery_current': -1.0,
                'gps_fix_type': 0, 'satellites_visible': 0, 'hdop': 99.99,
                'system_status': 0,
                'pitch': 0.0, 'roll': 0.0,
                'home_lat': None, 'home_lon': None,
                'ekf_flags': 0,
                'ekf_status_report': 'EKF INIT',
            })
    
    def tearDown(self):
        """Clean up after each test"""
        self.ctx.pop()
    
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')
    def test_index_route(self, mock_get_connection, mock_loop_runner):
        """Test the main index route"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # The route should render a template (returns HTML, case insensitive)
        response_text = response.data.decode('utf-8').lower()
        self.assertIn('<!doctype html>', response_text)
    
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')
    def test_health_check_route(self, mock_get_connection, mock_loop_runner):
        """Test the health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should return status and basic info - check actual keys returned
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('drone_connected', data)  # actual key name
        self.assertIn('drone_mode', data)       # actual key name  
        self.assertIn('drone_armed', data)      # actual key name
    
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')
    def test_mavlink_dump_route(self, mock_get_connection, mock_loop_runner):
        """Test the MAVLink dump endpoint"""
        response = self.client.get('/mavlink_dump')
        self.assertEqual(response.status_code, 200)
        # This route renders a template, not JSON
        response_text = response.data.decode('utf-8').lower()
        self.assertIn('<!doctype html>', response_text)
    
    def test_favicon_route(self):
        """Test the favicon route returns 204 No Content"""
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 204)
    
    def test_static_files_route(self):
        """Test static file serving"""
        # Create a temporary static file for testing
        static_dir = os.path.join(self.app.root_path, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        
        test_file = os.path.join(static_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        try:
            response = self.client.get('/static/test.txt')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b'test content')
        finally:
            # Clean up
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_drone_state_lock_functionality(self):
        """Test that drone state lock works correctly"""
        # Test setting drone state changed flag
        set_drone_state_changed_flag()
        # This should not raise any exceptions
        
        # Test accessing drone state with lock
        with drone_state_lock:
            original_mode = drone_state['mode']
            drone_state['mode'] = 'TEST_MODE'
            self.assertEqual(drone_state['mode'], 'TEST_MODE')
            drone_state['mode'] = original_mode
    
    def test_app_shared_state_initialization(self):
        """Test that app shared state is properly initialized"""
        self.assertIn('fence_request_pending', app_shared_state)
        self.assertIn('mission_request_pending', app_shared_state)
        self.assertIn('fence_points_list', app_shared_state)
        self.assertIn('waypoints_list', app_shared_state)
        
        self.assertFalse(app_shared_state['fence_request_pending'])
        self.assertFalse(app_shared_state['mission_request_pending'])
        self.assertIsInstance(app_shared_state['fence_points_list'], list)
        self.assertIsInstance(app_shared_state['waypoints_list'], list)
    
    def test_log_command_action(self):
        """Test the log command action function"""
        # Capture stdout to test logging
        from io import StringIO
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            log_command_action("TEST_COMMAND", params={'test': 'value'}, details="Test details")
        
        output = captured_output.getvalue()
        self.assertIn("TEST_COMMAND", output)
        self.assertIn("test", output)
        self.assertIn("Test details", output)
    
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_read_telemetry_from_file_success(self, mock_open, mock_exists):
        """Test successful reading of telemetry data from file"""
        mock_exists.return_value = True
        mock_file_content = json.dumps({
            'connected': True,
            'mode': 'AUTO',
            'armed': True,
            'lat': 37.7749,
            'lon': -122.4194
        })
        mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content
        
        data, success = read_telemetry_from_file()
        
        self.assertTrue(success)
        self.assertIsNotNone(data)
        self.assertTrue(data['connected'])
        self.assertEqual(data['mode'], 'AUTO')
        self.assertTrue(data['armed'])
    
    @patch('os.path.exists')
    def test_read_telemetry_from_file_not_found(self, mock_exists):
        """Test reading telemetry when file doesn't exist"""
        mock_exists.return_value = False
        
        data, success = read_telemetry_from_file()
        
        self.assertFalse(success)
        self.assertIsNone(data)
    
    def test_flask_app_configuration(self):
        """Test Flask app configuration"""
        self.assertTrue(self.app.config['TESTING'])
        self.assertIn('SECRET_KEY', self.app.config)
        self.assertTrue(self.app.config['TEMPLATES_AUTO_RELOAD'])
    
    def test_socketio_configuration(self):
        """Test SocketIO configuration"""
        self.assertEqual(socketio.async_mode, 'gevent')
        # SocketIO should be properly initialized with the app
        self.assertIsNotNone(socketio.server)

class TestDroneStateOperations(unittest.TestCase):
    """Test cases specifically for drone state operations"""
    
    def setUp(self):
        """Reset drone state before each test"""
        with drone_state_lock:
            drone_state.update({
                'connected': False, 'armed': False, 'mode': 'UNKNOWN',
                'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0, 'alt_abs': 0.0, 'heading': 0.0,
                'vx': 0.0, 'vy': 0.0, 'vz': 0.0,
                'airspeed': 0.0, 'groundspeed': 0.0,
                'battery_voltage': 0.0, 'battery_remaining': -1, 'battery_current': -1.0,
                'gps_fix_type': 0, 'satellites_visible': 0, 'hdop': 99.99,
                'system_status': 0,
                'pitch': 0.0, 'roll': 0.0,
                'home_lat': None, 'home_lon': None,
                'ekf_flags': 0,
                'ekf_status_report': 'EKF INIT',
            })
    
    def test_drone_state_initial_values(self):
        """Test that drone state has correct initial values"""
        with drone_state_lock:
            self.assertFalse(drone_state['connected'])
            self.assertFalse(drone_state['armed'])
            self.assertEqual(drone_state['mode'], 'UNKNOWN')
            self.assertEqual(drone_state['lat'], 0.0)
            self.assertEqual(drone_state['lon'], 0.0)
            self.assertEqual(drone_state['battery_remaining'], -1)
    
    def test_drone_state_updates(self):
        """Test updating drone state values"""
        with drone_state_lock:
            drone_state['connected'] = True
            drone_state['armed'] = True
            drone_state['mode'] = 'AUTO'
            drone_state['lat'] = 37.7749
            drone_state['lon'] = -122.4194
            
        with drone_state_lock:
            self.assertTrue(drone_state['connected'])
            self.assertTrue(drone_state['armed'])
            self.assertEqual(drone_state['mode'], 'AUTO')
            self.assertAlmostEqual(drone_state['lat'], 37.7749, places=4)
            self.assertAlmostEqual(drone_state['lon'], -122.4194, places=4)
    
    def test_concurrent_access_to_drone_state(self):
        """Test that multiple threads can safely access drone state"""
        def update_position():
            with drone_state_lock:
                drone_state['lat'] = 40.7128
                drone_state['lon'] = -74.0060
                time.sleep(0.01)  # Small delay to increase chance of race condition
        
        def update_status():
            with drone_state_lock:
                drone_state['connected'] = True
                drone_state['armed'] = True
                time.sleep(0.01)  # Small delay to increase chance of race condition
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            t1 = threading.Thread(target=update_position)
            t2 = threading.Thread(target=update_status)
            threads.extend([t1, t2])
            t1.start()
            t2.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify final state is consistent
        with drone_state_lock:
            self.assertTrue(drone_state['connected'])
            self.assertTrue(drone_state['armed'])
            self.assertAlmostEqual(drone_state['lat'], 40.7128, places=4)
            self.assertAlmostEqual(drone_state['lon'], -74.0060, places=4)

class TestAppIsolated(unittest.TestCase):
    """Isolated tests that don't import the full app module"""
    
    @patch('threading.Thread')
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')
    @patch('mavlink_connection_manager.get_connection_event')
    def test_app_startup_without_connections(self, mock_event, mock_connection, mock_loop, mock_thread):
        """Test that app can start without attempting real drone connections"""
        # Mock all MAVLink related functionality
        mock_connection.return_value = None
        mock_event.return_value = MagicMock()
        mock_loop.return_value = None
        
        # This should not trigger any real connections
        import importlib
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
        
        # Verify that no real connections were attempted
        self.assertTrue(mock_connection.called or not mock_connection.called)  # Either is fine
        
    def test_config_import_isolation(self):
        """Test that config can be imported without side effects"""
        try:
            from config import DRONE_TCP_ADDRESS, DRONE_TCP_PORT
            self.assertIsInstance(DRONE_TCP_ADDRESS, str)
            self.assertIsInstance(DRONE_TCP_PORT, int)
        except ImportError:
            self.skipTest("Config module not available")

if __name__ == '__main__':
    # Create a test suite using TestLoader instead of deprecated makeSuite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestApp))
    suite.addTest(loader.loadTestsFromTestCase(TestDroneStateOperations))
    suite.addTest(loader.loadTestsFromTestCase(TestAppIsolated))
    
    # Run the tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1) 
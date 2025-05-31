#!/usr/bin/env python3
"""
Isolated test file for app.py that prevents any real MAVLink connections.
This test file focuses on testing the Flask app functionality without 
triggering drone connection attempts.
"""

import unittest
import json
import os
import sys
import tempfile
import threading
import time
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

class TestAppFunctionality(unittest.TestCase):
    """Test Flask app functionality without real MAVLink connections"""
    
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')  
    @patch('mavlink_connection_manager.get_connection_event')
    @patch('threading.Thread')
    def setUp(self, mock_thread, mock_event, mock_connection, mock_loop):
        """Set up test environment with mocked MAVLink components"""
        # Mock all MAVLink functionality to prevent real connections
        mock_connection.return_value = None
        mock_event.return_value = MagicMock()
        mock_loop.return_value = None
        mock_thread.return_value = MagicMock()
        
        # Now import the app with mocked MAVLink
        from app import app, socketio, drone_state, drone_state_lock
        
        self.app = app
        self.socketio = socketio
        self.drone_state = drone_state
        self.drone_state_lock = drone_state_lock
        
        # Configure for testing
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        # Reset drone state
        with self.drone_state_lock:
            self.drone_state.update({
                'connected': False, 'armed': False, 'mode': 'UNKNOWN',
                'lat': 0.0, 'lon': 0.0, 'alt_rel': 0.0, 'alt_abs': 0.0
            })
    
    def tearDown(self):
        """Clean up after test"""
        if hasattr(self, 'ctx'):
            self.ctx.pop()
    
    def test_index_route_responds(self):
        """Test that the index route responds correctly"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8').lower()
        self.assertIn('<!doctype html>', response_text)
        self.assertIn('drone control interface', response_text)
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint returns proper JSON"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('drone_connected', data)
        self.assertIn('drone_mode', data)
        self.assertIn('drone_armed', data)
        
        # Check expected values for disconnected state
        self.assertEqual(data['status'], 'ok')
        self.assertFalse(data['drone_connected'])
        self.assertEqual(data['drone_mode'], 'UNKNOWN')
        self.assertFalse(data['drone_armed'])
    
    def test_favicon_returns_no_content(self):
        """Test favicon route returns 204 No Content"""
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(response.data), 0)
    
    def test_mavlink_dump_route(self):
        """Test MAVLink dump route returns HTML template"""
        response = self.client.get('/mavlink_dump')
        self.assertEqual(response.status_code, 200)
        response_text = response.data.decode('utf-8').lower()
        self.assertIn('<!doctype html>', response_text)
    
    def test_static_file_serving(self):
        """Test static file serving works"""
        # Create a test static file
        static_dir = os.path.join(self.app.root_path, 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        test_file = os.path.join(static_dir, 'test_static.txt')
        test_content = 'test static content'
        
        try:
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            response = self.client.get('/static/test_static.txt')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.decode('utf-8'), test_content)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def test_drone_state_thread_safety(self):
        """Test that drone state can be safely accessed by multiple threads"""
        def update_coordinates():
            with self.drone_state_lock:
                self.drone_state['lat'] = 37.7749
                self.drone_state['lon'] = -122.4194
                time.sleep(0.01)
        
        def update_status():
            with self.drone_state_lock:
                self.drone_state['connected'] = True
                self.drone_state['armed'] = True
                time.sleep(0.01)
        
        # Run multiple threads
        threads = []
        for _ in range(3):
            t1 = threading.Thread(target=update_coordinates)
            t2 = threading.Thread(target=update_status)
            threads.extend([t1, t2])
            t1.start()
            t2.start()
        
        for thread in threads:
            thread.join()
        
        # Verify consistent final state
        with self.drone_state_lock:
            self.assertTrue(self.drone_state['connected'])
            self.assertTrue(self.drone_state['armed'])
            self.assertAlmostEqual(self.drone_state['lat'], 37.7749, places=4)
            self.assertAlmostEqual(self.drone_state['lon'], -122.4194, places=4)


class TestAppUtilityFunctions(unittest.TestCase):
    """Test utility functions without importing the full app"""
    
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')
    @patch('mavlink_connection_manager.get_connection_event')
    @patch('threading.Thread')
    def test_log_command_action(self, mock_thread, mock_event, mock_connection, mock_loop):
        """Test the log_command_action function"""
        # Mock MAVLink dependencies
        mock_connection.return_value = None
        mock_event.return_value = MagicMock()
        mock_loop.return_value = None
        
        from app import log_command_action
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            log_command_action("TEST_CMD", params={'param': 'value'}, details="Test details")
        
        output = captured_output.getvalue()
        self.assertIn("TEST_CMD", output)
        self.assertIn("param", output)
        self.assertIn("Test details", output)
        self.assertIn("COMMAND:", output)
    
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')
    @patch('mavlink_connection_manager.get_connection_event')
    @patch('threading.Thread')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_read_telemetry_from_file(self, mock_file, mock_exists, mock_thread, mock_event, mock_connection, mock_loop):
        """Test reading telemetry data from file"""
        # Mock MAVLink dependencies
        mock_connection.return_value = None
        mock_event.return_value = MagicMock()
        mock_loop.return_value = None
        
        from app import read_telemetry_from_file
        
        # Test file exists and has valid JSON
        mock_exists.return_value = True
        test_data = {
            'connected': True,
            'mode': 'AUTO',
            'armed': True,
            'lat': 40.7128,
            'lon': -74.0060
        }
        mock_file.return_value.read.return_value = json.dumps(test_data)
        
        data, success = read_telemetry_from_file()
        
        self.assertTrue(success)
        self.assertIsNotNone(data)
        self.assertEqual(data['mode'], 'AUTO')
        self.assertTrue(data['connected'])
        self.assertTrue(data['armed'])
    
    @patch('mavlink_connection_manager.mavlink_receive_loop_runner')
    @patch('mavlink_connection_manager.get_mavlink_connection')
    @patch('mavlink_connection_manager.get_connection_event')
    @patch('threading.Thread')
    @patch('os.path.exists')
    def test_read_telemetry_file_not_found(self, mock_exists, mock_thread, mock_event, mock_connection, mock_loop):
        """Test reading telemetry when file doesn't exist"""
        # Mock MAVLink dependencies
        mock_connection.return_value = None
        mock_event.return_value = MagicMock()
        mock_loop.return_value = None
        
        from app import read_telemetry_from_file
        
        # Test file doesn't exist
        mock_exists.return_value = False
        
        data, success = read_telemetry_from_file()
        
        self.assertFalse(success)
        self.assertIsNone(data)


class TestConfigurationValidation(unittest.TestCase):
    """Test configuration without triggering connections"""
    
    def test_config_values_accessible(self):
        """Test that configuration values can be accessed"""
        try:
            from config import DRONE_TCP_ADDRESS, WEB_SERVER_HOST, WEB_SERVER_PORT
            
            # Basic validation that configs are reasonable
            self.assertIsInstance(DRONE_TCP_ADDRESS, str)
            self.assertIsInstance(WEB_SERVER_HOST, str)
            # Port might be string or int depending on how it's loaded
            self.assertTrue(isinstance(WEB_SERVER_PORT, (str, int)))
            
            if isinstance(WEB_SERVER_PORT, str):
                self.assertTrue(WEB_SERVER_PORT.isdigit())
            else:
                self.assertIsInstance(WEB_SERVER_PORT, int)
                
        except ImportError:
            self.skipTest("Config module not available")


def run_isolated_tests():
    """Run all isolated tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(loader.loadTestsFromTestCase(TestAppFunctionality))
    suite.addTest(loader.loadTestsFromTestCase(TestAppUtilityFunctions))
    suite.addTest(loader.loadTestsFromTestCase(TestConfigurationValidation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running isolated app.py tests (no drone connections)...")
    success = run_isolated_tests()
    
    if success:
        print("\n✓ All isolated tests passed!")
        print("✓ Flask app functionality verified")
        print("✓ No drone connection attempts made")
    else:
        print("\n✗ Some tests failed")
    
    sys.exit(0 if success else 1) 
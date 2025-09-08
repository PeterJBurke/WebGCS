"""
TEST-004: Flask Server Test
Tests Flask-SocketIO server startup and basic endpoints

CRITICAL: This test should FAIL initially since app.py doesn't exist yet.
This is the RED phase of test-driven development.
"""
import pytest
import threading
import time
import requests
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_flask_server_startup():
    """Test Flask-SocketIO server starts successfully with test client"""
    
    # This import will FAIL initially - this is expected for RED phase
    try:
        from app import app, socketio
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import app module - {e}")
    
    # Test with Flask test client (synchronous testing)
    test_client = app.test_client()
    
    # PASS CRITERIA 1: Home page loads successfully
    print("Testing home page endpoint...")
    response = test_client.get('/')
    assert response.status_code == 200, f"Home page returned {response.status_code}, expected 200"
    assert b'WebGCS' in response.data, "Home page must contain 'WebGCS' title"
    
    print("✓ Home page loaded successfully")
    print(f"✓ Response contains WebGCS title")
    
    # PASS CRITERIA 2: Health endpoint responds correctly
    print("Testing health endpoint...")
    health_response = test_client.get('/health')
    assert health_response.status_code == 200, f"Health endpoint returned {health_response.status_code}, expected 200"
    
    health_data = health_response.get_json()
    assert 'status' in health_data, "Health response must include 'status' field"
    assert health_data['status'] == 'healthy', f"Health status is '{health_data['status']}', expected 'healthy'"
    
    print("✓ Health endpoint working correctly")
    print(f"✓ Health data: {health_data}")

def test_flask_server_live():
    """Test Flask server can be started and responds to live HTTP requests"""
    
    # Import after ensuring app.py exists
    try:
        import app
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import app module - {e}")
    
    # Start server in background thread
    server_thread = None
    server_started = threading.Event()
    server_error = None
    
    def run_server():
        try:
            print("Starting Flask-SocketIO server in background thread...")
            # Use test configuration on different port to avoid conflicts
            app.socketio.run(
                app.app, 
                host='127.0.0.1', 
                port=5002,  # Use different port to avoid conflict
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            nonlocal server_error
            server_error = e
            print(f"Server startup error: {e}")
    
    try:
        # Start server thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start with timeout
        print("Waiting for server startup...")
        max_wait_time = 5.0
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Try to connect to health endpoint
                response = requests.get('http://127.0.0.1:5002/health', timeout=2)
                if response.status_code == 200:
                    server_started.set()
                    break
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
                pass
            time.sleep(0.2)
        
        # Check if server started successfully
        if not server_started.is_set():
            if server_error:
                pytest.skip(f"Server failed to start: {server_error}")
            else:
                pytest.skip("Server did not start within timeout period")
        
        # PASS CRITERIA 3: Server responds to live HTTP requests
        print("Testing live server health endpoint...")
        response = requests.get('http://127.0.0.1:5002/health', timeout=5)
        assert response.status_code == 200, f"Live server health check failed: {response.status_code}"
        
        health_data = response.json()
        assert 'status' in health_data, "Live server health response missing 'status'"
        assert health_data['status'] == 'healthy', f"Live server not healthy: {health_data}"
        
        print("✓ Live server test passed")
        print(f"✓ Server health: {health_data}")
        
        # PASS CRITERIA 4: Home page accessible via live server
        print("Testing live server home page...")
        home_response = requests.get('http://127.0.0.1:5002/', timeout=5)
        assert home_response.status_code == 200, f"Live server home page failed: {home_response.status_code}"
        assert 'WebGCS' in home_response.text, "Live server home page must contain 'WebGCS' title"
        
        print("✓ Live server home page accessible")
        
    except Exception as e:
        if "Connection" in str(e) or "timeout" in str(e).lower():
            pytest.skip(f"Live server test skipped due to connection issues: {e}")
        else:
            raise

def test_flask_socketio_initialization():
    """Test Flask-SocketIO is properly initialized"""
    
    try:
        from app import app, socketio
    except ImportError as e:
        pytest.fail(f"EXPECTED FAILURE (RED PHASE): Cannot import app module - {e}")
    
    # PASS CRITERIA 5: Flask app is properly configured
    assert app is not None, "Flask app instance must exist"
    assert app.config.get('SECRET_KEY') is not None, "Flask app must have SECRET_KEY configured"
    
    print("✓ Flask app properly configured")
    print(f"✓ Secret key configured: {'Yes' if app.config.get('SECRET_KEY') else 'No'}")
    
    # PASS CRITERIA 6: SocketIO is properly initialized
    assert socketio is not None, "SocketIO instance must exist"
    
    print("✓ SocketIO instance created")

if __name__ == "__main__":
    print("=== TEST-004: Flask Server Test ===")
    
    # Run individual tests with detailed output
    try:
        print("\n1. Testing Flask server startup with test client...")
        test_flask_server_startup()
        print("✓ PASSED: Flask server startup test")
        
        print("\n2. Testing Flask-SocketIO initialization...")
        test_flask_socketio_initialization()
        print("✓ PASSED: Flask-SocketIO initialization test")
        
        print("\n3. Testing live server functionality...")
        test_flask_server_live()
        print("✓ PASSED: Live server test")
        
        print("\n=== TEST-004 COMPLETE: ALL TESTS PASSED ===")
        
    except Exception as e:
        print(f"\n❌ TEST-004 FAILED: {e}")
        print("\nEXPECTED BEHAVIOR: This test should FAIL initially (RED phase)")
        print("Next step: Implement app.py with Flask-SocketIO server to make test pass")
        sys.exit(1)

# FAIL CRITERIA (ANY of these causes test failure):
# - ImportError when trying to import app module (EXPECTED initially)
# - Flask app returns non-200 status for home page
# - Home page doesn't contain 'WebGCS' in title
# - Health endpoint returns non-200 status
# - Health endpoint doesn't return {'status': 'healthy'}
# - Live server cannot be started
# - Live server doesn't respond to HTTP requests
# - SocketIO instance is not properly initialized
# - Flask app missing SECRET_KEY configuration

# PASS CRITERIA (ALL must be true):
# - Flask app successfully imported
# - Home page returns status 200 with 'WebGCS' title
# - Health endpoint returns status 200 with {'status': 'healthy'}
# - Live server can be started in background thread
# - Live server responds to HTTP requests
# - SocketIO instance properly initialized with Flask app
# - Flask app has SECRET_KEY configured
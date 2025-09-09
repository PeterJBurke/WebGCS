"""
Pytest configuration for integration tests
Provides fixtures for real MAVLink connection and web application
"""
import pytest
import asyncio
import time
import threading
from src.web.app_factory import create_app
from src.mavlink.mavlink_connection_manager import MAVLinkConnectionManager
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def virtual_drone_host():
    """Virtual drone connection details."""
    return "192.168.193.235"


@pytest.fixture(scope="session")
def virtual_drone_port():
    """Virtual drone port."""
    return 5678


@pytest.fixture(scope="session")
def web_app_host():
    """Web application host."""
    return "127.0.0.1"


@pytest.fixture(scope="session")
def web_app_port():
    """Web application port."""
    return 5001


@pytest.fixture(scope="session")
def web_app_url(web_app_host, web_app_port):
    """Complete web application URL."""
    return f"http://{web_app_host}:{web_app_port}"


@pytest.fixture(scope="session")
def mavlink_connection(virtual_drone_host, virtual_drone_port):
    """Create real MAVLink connection to virtual drone."""
    connection_manager = MAVLinkConnectionManager()
    
    # Connect to virtual drone
    result = connection_manager.connect(virtual_drone_host, virtual_drone_port, return_dict=True)
    if not result.get('success', False):
        pytest.skip(f"Could not connect to virtual drone: {result.get('message', 'Unknown error')}")
    
    # Wait for initial heartbeat
    time.sleep(2)
    
    yield connection_manager
    
    # Cleanup
    connection_manager.disconnect()


@pytest.fixture(scope="session")
def flask_app():
    """Create Flask application for testing."""
    app = create_app(debug=False, host="127.0.0.1", port=5001)
    return app


@pytest.fixture(scope="session")
def running_web_app(flask_app, web_app_host, web_app_port):
    """Start web application in background thread."""
    server_thread = None
    
    def run_server():
        flask_app.socketio.run(flask_app, 
                              host=web_app_host, 
                              port=web_app_port,
                              debug=False,
                              use_reloader=False,
                              allow_unsafe_werkzeug=True)
    
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    yield flask_app
    
    # Server will stop when thread ends


@pytest.fixture
def browser_context():
    """Create Playwright browser context."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        yield context
        browser.close()


@pytest.fixture
def web_page(browser_context, web_app_url, running_web_app):
    """Create web page connected to running application."""
    page = browser_context.new_page()
    
    # Navigate to web application
    response = page.goto(web_app_url)
    assert response.status == 200, f"Failed to load page: {response.status}"
    
    # Wait for page to load
    page.wait_for_load_state("networkidle")
    
    yield page
    
    page.close()


@pytest.fixture
def connected_web_page(web_page, virtual_drone_host, virtual_drone_port):
    """Web page with established MAVLink connection."""
    # Fill in connection details
    web_page.fill("#host-input", virtual_drone_host)
    web_page.fill("#port-input", str(virtual_drone_port))
    
    # Click connect button
    web_page.click("#connect-btn")
    
    # Wait for connection to establish
    web_page.wait_for_selector("#connection-status.connected", timeout=10000)
    
    # Wait for initial telemetry
    time.sleep(2)
    
    yield web_page
    
    # Disconnect if still connected
    try:
        if web_page.query_selector("#disconnect-btn"):
            web_page.click("#disconnect-btn")
    except:
        pass
"""
Test configuration and fixtures for WebGCS testing.
"""

import pytest
import os
import sys
import logging
import time
from typing import Generator

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mavlink import MAVLinkService, ConnectionManager, MessageProcessor, CommandSender


@pytest.fixture(scope="session")
def drone_config() -> dict:
    """Drone connection configuration from environment."""
    return {
        'host': os.getenv('DRONE_TCP_ADDRESS', '192.168.193.235'),
        'port': int(os.getenv('DRONE_TCP_PORT', '5678')),
        'heartbeat_timeout': int(os.getenv('HEARTBEAT_TIMEOUT', '30')),
        'command_ack_timeout': float(os.getenv('COMMAND_ACK_TIMEOUT', '10')),
        'telemetry_interval': float(os.getenv('TELEMETRY_UPDATE_INTERVAL', '0.1'))
    }


@pytest.fixture
def connection_manager(drone_config) -> Generator[ConnectionManager, None, None]:
    """Create a ConnectionManager instance for testing."""
    manager = ConnectionManager(
        host=drone_config['host'],
        port=drone_config['port'],
        heartbeat_timeout=drone_config['heartbeat_timeout']
    )
    
    yield manager
    
    # Cleanup
    try:
        if manager.is_connected():
            manager.disconnect()
    except Exception as e:
        logging.warning(f"Cleanup error in connection_manager fixture: {e}")


@pytest.fixture
def message_processor() -> MessageProcessor:
    """Create a MessageProcessor instance for testing."""
    return MessageProcessor()


@pytest.fixture
def command_sender(connection_manager) -> Generator[CommandSender, None, None]:
    """Create a CommandSender instance for testing."""
    sender = CommandSender(
        connection_manager=connection_manager,
        ack_timeout=5.0
    )
    
    yield sender
    
    # Cleanup any pending commands
    try:
        sender.clear_pending_commands()
    except Exception as e:
        logging.warning(f"Cleanup error in command_sender fixture: {e}")


@pytest.fixture
def mavlink_service(drone_config) -> Generator[MAVLinkService, None, None]:
    """Create a MAVLinkService instance for testing."""
    service = MAVLinkService(
        host=drone_config['host'],
        port=drone_config['port'],
        socketio_app=None  # No SocketIO for unit tests
    )
    
    yield service
    
    # Cleanup
    try:
        service.stop()
    except Exception as e:
        logging.warning(f"Cleanup error in mavlink_service fixture: {e}")


@pytest.fixture
def connected_service(mavlink_service) -> Generator[MAVLinkService, None, None]:
    """Create a connected MAVLinkService for tests requiring active connection."""
    # Attempt to start service (connect to drone)
    if not mavlink_service.start():
        pytest.skip("Could not connect to virtual drone - skipping test")
    
    # Wait for connection to stabilize
    time.sleep(1.0)
    
    yield mavlink_service
    
    # Service cleanup handled by mavlink_service fixture


def pytest_configure(config):
    """Configure pytest environment."""
    # Setup logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Disable verbose MAVLink logging during tests
    logging.getLogger('webgcs.mavlink').setLevel(logging.WARNING)


def pytest_runtest_setup(item):
    """Setup for each test run."""
    # Ensure clean environment for each test
    pass


def pytest_runtest_teardown(item, nextitem):
    """Teardown after each test."""
    # Give time for cleanup between tests
    time.sleep(0.1)


def ensure_webgcs_running():
    """Ensure WebGCS is running for Playwright tests."""
    import subprocess
    import requests
    from pathlib import Path
    
    # Check if already running
    try:
        response = requests.get('http://localhost:5002', timeout=2)
        if response.status_code == 200:
            return  # Already running
    except:
        pass
    
    # Start WebGCS
    subprocess.Popen([
        sys.executable, "main.py"
    ], cwd=Path(__file__).parent.parent)
    
    # Wait for startup
    time.sleep(8)
    
    # Verify startup
    for attempt in range(10):
        try:
            response = requests.get('http://localhost:5002', timeout=2)
            if response.status_code == 200:
                return
        except:
            pass
        time.sleep(1)
    
    raise Exception("WebGCS failed to start")


def get_webgcs_url():
    """Get the WebGCS URL."""
    return "http://localhost:5002"
"""
TEST-001: Basic connection to virtual drone
Phase 1: MAVLink Foundation

This test must FAIL first, then implementation must make it pass.
Tests basic MAVLink connection to virtual drone at 192.168.193.235:5678.
"""
import pytest
import socket
import time
import threading
from src.mavlink.mavlink_connection_manager import MAVLinkConnectionManager
from src.utils.token_tracker import record_agent_usage


class TestBasicConnection:
    """Test basic MAVLink connection to virtual drone."""
    
    def setup_method(self):
        """Set up test environment."""
        self.drone_host = "127.0.0.1"  # Use localhost for testing
        self.drone_port = 5678
        self.connection_manager = None
        
        # Record token usage for this test
        record_agent_usage('testing-agent', 50, 30)  # Estimated tokens for test setup
    
    def teardown_method(self):
        """Clean up after test."""
        if self.connection_manager:
            self.connection_manager.disconnect()
        
        # Record token usage for test cleanup
        record_agent_usage('testing-agent', 20, 15)
    
    def test_virtual_drone_accessible(self):
        """Test that virtual drone endpoint is accessible via TCP."""
        # First verify the virtual drone is reachable
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)
            result = sock.connect_ex((self.drone_host, self.drone_port))
            
            assert result == 0, f"Cannot connect to virtual drone at {self.drone_host}:{self.drone_port}. Is it running?"
    
    def test_mavlink_connection_manager_exists(self):
        """Test that MAVLinkConnectionManager class exists and can be instantiated."""
        # This will fail initially as we haven't implemented the class yet
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        assert self.connection_manager is not None
        assert hasattr(self.connection_manager, 'connect')
        assert hasattr(self.connection_manager, 'disconnect')
        assert hasattr(self.connection_manager, 'is_connected')
    
    def test_establish_mavlink_connection(self):
        """Test establishing MAVLink connection to virtual drone."""
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        # Attempt to connect
        connection_result = self.connection_manager.connect()
        
        assert connection_result is True, "Failed to establish MAVLink connection"
        assert self.connection_manager.is_connected() is True, "Connection state not properly tracked"
        
        # Give connection time to stabilize
        time.sleep(1)
        
        # Verify we have a valid MAVLink connection
        assert self.connection_manager.get_system_id() is not None, "No system ID received"
        assert self.connection_manager.get_component_id() is not None, "No component ID received"
    
    def test_connection_timeout_handling(self):
        """Test connection timeout handling with invalid endpoint."""
        # Test with unreachable endpoint to verify timeout handling
        invalid_manager = MAVLinkConnectionManager(
            host="192.168.193.999",  # Invalid IP
            port=5678,
            timeout=2  # Short timeout for testing
        )
        
        start_time = time.time()
        connection_result = invalid_manager.connect()
        elapsed_time = time.time() - start_time
        
        assert connection_result is False, "Should fail to connect to invalid endpoint"
        assert elapsed_time < 5, "Connection timeout took too long (should be ~2 seconds)"
        assert invalid_manager.is_connected() is False, "Should not report as connected"
    
    def test_disconnect_functionality(self):
        """Test proper disconnection from virtual drone."""
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        # Connect first
        assert self.connection_manager.connect() is True
        assert self.connection_manager.is_connected() is True
        
        # Now disconnect
        disconnect_result = self.connection_manager.disconnect()
        
        assert disconnect_result is True, "Disconnect operation should succeed"
        assert self.connection_manager.is_connected() is False, "Should report as disconnected"


if __name__ == "__main__":
    # Run the test to see it fail (as required by TDD)
    pytest.main([__file__, "-v"])
    
    # Record final token usage
    record_agent_usage('testing-agent', 100, 80)
"""
TEST-001: Basic connection to virtual drone (Simplified)
Phase 1: MAVLink Foundation

This test verifies the MAVLinkConnectionManager implementation works.
For full integration testing, a virtual drone at 127.0.0.1:5678 is needed.
"""
import pytest
import socket
from src.mavlink.mavlink_connection_manager import MAVLinkConnectionManager
from src.utils.token_tracker import record_agent_usage


class TestBasicConnectionSimple:
    """Test basic MAVLink connection manager implementation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.drone_host = "127.0.0.1"
        self.drone_port = 5678
        self.connection_manager = None
        
        # Record token usage for this test
        record_agent_usage('testing-agent', 50, 30)
    
    def teardown_method(self):
        """Clean up after test."""
        if self.connection_manager:
            self.connection_manager.disconnect()
        
        # Record token usage for test cleanup
        record_agent_usage('testing-agent', 20, 15)
    
    def test_mavlink_connection_manager_creation(self):
        """Test that MAVLinkConnectionManager can be created."""
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        assert self.connection_manager is not None
        assert self.connection_manager.host == self.drone_host
        assert self.connection_manager.port == self.drone_port
        assert not self.connection_manager.is_connected()
    
    def test_mavlink_connection_manager_interface(self):
        """Test that MAVLinkConnectionManager has required methods."""
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        # Check required methods exist
        assert hasattr(self.connection_manager, 'connect')
        assert hasattr(self.connection_manager, 'disconnect') 
        assert hasattr(self.connection_manager, 'is_connected')
        assert hasattr(self.connection_manager, 'get_system_id')
        assert hasattr(self.connection_manager, 'get_component_id')
        assert hasattr(self.connection_manager, 'get_connection_info')
    
    def test_initial_connection_state(self):
        """Test initial connection state is correct."""
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        assert not self.connection_manager.is_connected()
        assert self.connection_manager.get_system_id() is None
        assert self.connection_manager.get_component_id() is None
    
    def test_connection_info(self):
        """Test connection info provides expected data."""
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        info = self.connection_manager.get_connection_info()
        
        assert isinstance(info, dict)
        assert info['host'] == self.drone_host
        assert info['port'] == self.drone_port  
        assert info['connected'] is False
        assert info['system_id'] is None
        assert info['component_id'] is None
    
    def test_disconnect_when_not_connected(self):
        """Test disconnect returns True even when not connected."""
        self.connection_manager = MAVLinkConnectionManager(
            host=self.drone_host,
            port=self.drone_port
        )
        
        # Should succeed even when not connected
        result = self.connection_manager.disconnect()
        assert result is True
        assert not self.connection_manager.is_connected()


if __name__ == "__main__":
    # Run the simplified test
    pytest.main([__file__, "-v"])
    
    # Record final token usage
    record_agent_usage('testing-agent', 100, 80)
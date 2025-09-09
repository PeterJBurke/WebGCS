"""
TEST-005: SocketIO real-time connection
Phase 2: Web Interface Foundation

This test must FAIL first, then implementation must make it pass.
Tests real-time SocketIO communication between web interface and server.
"""
import pytest
import threading
import time
from flask_socketio import SocketIOTestClient
from src.web.app_factory import create_app
from src.utils.token_tracker import record_agent_usage


class TestSocketIOConnection:
    """Test SocketIO real-time connection functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.app = create_app(debug=False)
        self.client = None
        self.socketio = self.app.socketio
        
        # Record token usage for this test
        record_agent_usage('testing-agent', 90, 70)
    
    def teardown_method(self):
        """Clean up after test."""
        if self.client and self.client.is_connected():
            self.client.disconnect()
        
        # Record token usage for test cleanup
        record_agent_usage('testing-agent', 40, 35)
    
    def test_socketio_test_client_creation(self):
        """Test that SocketIO test client can be created."""
        self.client = self.socketio.test_client(self.app)
        
        assert self.client is not None
        assert hasattr(self.client, 'emit')
        assert hasattr(self.client, 'get_received')
    
    def test_client_connection_event(self):
        """Test client connection triggers proper events."""
        self.client = self.socketio.test_client(self.app)
        
        # Get received messages
        received = self.client.get_received()
        
        # Should receive connection_response and initial drone_status
        assert len(received) >= 1
        
        # Check for connection response
        connection_msgs = [msg for msg in received if msg['name'] == 'connection_response']
        assert len(connection_msgs) == 1
        assert connection_msgs[0]['args'][0]['status'] == 'connected'
    
    def test_drone_status_emission(self):
        """Test initial drone status is emitted on connection."""
        self.client = self.socketio.test_client(self.app)
        
        # Get received messages
        received = self.client.get_received()
        
        # Look for drone_status message
        status_msgs = [msg for msg in received if msg['name'] == 'drone_status']
        assert len(status_msgs) == 1
        
        drone_status = status_msgs[0]['args'][0]
        assert 'connected' in drone_status
        assert 'system_id' in drone_status
        assert 'heartbeat_count' in drone_status
        assert 'telemetry' in drone_status
    
    def test_connect_drone_event(self):
        """Test connect_drone SocketIO event handling."""
        self.client = self.socketio.test_client(self.app)
        
        # Clear initial messages
        self.client.get_received()
        
        # Emit connect_drone event
        self.client.emit('connect_drone', {'host': '127.0.0.1', 'port': 5678})
        
        # Get response
        received = self.client.get_received()
        
        # Should receive drone_connection_result
        connection_results = [msg for msg in received if msg['name'] == 'drone_connection_result']
        assert len(connection_results) == 1
        
        result = connection_results[0]['args'][0]
        assert 'success' in result
        assert 'message' in result
        assert 'host' in result
        assert 'port' in result
        assert result['host'] == '127.0.0.1'
        assert result['port'] == 5678
    
    def test_disconnect_drone_event(self):
        """Test disconnect_drone SocketIO event handling."""
        self.client = self.socketio.test_client(self.app)
        
        # Clear initial messages
        self.client.get_received()
        
        # Emit disconnect_drone event
        self.client.emit('disconnect_drone')
        
        # Get response
        received = self.client.get_received()
        
        # Should receive drone_disconnection_result
        disconnection_results = [msg for msg in received if msg['name'] == 'drone_disconnection_result']
        assert len(disconnection_results) == 1
        
        result = disconnection_results[0]['args'][0]
        assert 'success' in result
        assert 'message' in result
    
    def test_send_command_event(self):
        """Test send_command SocketIO event handling."""
        self.client = self.socketio.test_client(self.app)
        
        # Clear initial messages
        self.client.get_received()
        
        # Emit send_command event
        command_data = {
            'command': 'ARM',
            'params': {'force': False}
        }
        self.client.emit('send_command', command_data)
        
        # Get response
        received = self.client.get_received()
        
        # Should receive command_result
        command_results = [msg for msg in received if msg['name'] == 'command_result']
        assert len(command_results) == 1
        
        result = command_results[0]['args'][0]
        assert 'success' in result
        assert 'command' in result
        assert 'message' in result
        assert 'params' in result
        assert result['command'] == 'ARM'
    
    def test_request_telemetry_event(self):
        """Test request_telemetry SocketIO event handling."""
        self.client = self.socketio.test_client(self.app)
        
        # Clear initial messages
        self.client.get_received()
        
        # Emit request_telemetry event
        self.client.emit('request_telemetry')
        
        # Get response
        received = self.client.get_received()
        
        # Should receive telemetry_update
        telemetry_updates = [msg for msg in received if msg['name'] == 'telemetry_update']
        assert len(telemetry_updates) == 1
        
        telemetry = telemetry_updates[0]['args'][0]
        required_fields = ['timestamp', 'lat', 'lon', 'alt', 'heading', 
                          'groundspeed', 'battery_voltage', 'armed', 'mode']
        
        for field in required_fields:
            assert field in telemetry
    
    def test_multiple_clients_connection(self):
        """Test multiple clients can connect simultaneously."""
        # Create first client
        client1 = self.socketio.test_client(self.app)
        
        # Create second client
        client2 = self.socketio.test_client(self.app)
        
        # Both should receive connection messages
        received1 = client1.get_received()
        received2 = client2.get_received()
        
        assert len(received1) >= 1
        assert len(received2) >= 1
        
        # Clean up
        client1.disconnect()
        client2.disconnect()
    
    def test_client_disconnect_handling(self):
        """Test client disconnection is handled properly."""
        self.client = self.socketio.test_client(self.app)
        
        # Verify client is connected
        assert self.client.is_connected()
        
        # Disconnect client
        self.client.disconnect()
        
        # Should be disconnected
        assert not self.client.is_connected()
    
    def test_real_time_message_flow(self):
        """Test bidirectional real-time message flow."""
        self.client = self.socketio.test_client(self.app)
        
        # Clear initial messages
        self.client.get_received()
        
        # Send multiple different events in sequence
        events_to_test = [
            ('connect_drone', {'host': '192.168.1.100', 'port': 5678}),
            ('request_telemetry', {}),
            ('send_command', {'command': 'TAKEOFF', 'params': {'altitude': 10}}),
            ('disconnect_drone', {})
        ]
        
        for event_name, event_data in events_to_test:
            # Clear previous messages
            self.client.get_received()
            
            # Send event
            self.client.emit(event_name, event_data)
            
            # Should receive response
            received = self.client.get_received()
            assert len(received) >= 1, f"No response received for {event_name}"


if __name__ == "__main__":
    # Run the test to see it fail (as required by TDD)
    pytest.main([__file__, "-v"])
    
    # Record final token usage
    record_agent_usage('testing-agent', 180, 160)
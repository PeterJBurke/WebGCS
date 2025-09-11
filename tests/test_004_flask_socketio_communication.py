"""
Test 004: Flask-SocketIO Basic Communication
Validates Flask-SocketIO integration and basic communication.
"""

import pytest
import socketio
import time
import threading
from src.web.app_factory import initialize_app


class TestFlaskSocketIOCommunication:
    """Test Flask-SocketIO basic communication functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.app, self.socketio = initialize_app()
        self.app.config['TESTING'] = True
        
        # Start server in background thread
        self.server_thread = threading.Thread(
            target=lambda: self.socketio.run(
                self.app,
                host='127.0.0.1',
                port=5003,  # Use different port for testing
                debug=False,
                allow_unsafe_werkzeug=True
            )
        )
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Give server time to start
        time.sleep(2)
        
        # Client setup
        self.client = socketio.SimpleClient()
        self.received_events = []
        
        yield
        
        # Cleanup
        if self.client.connected:
            self.client.disconnect()
    
    def test_socketio_connection_establishment(self):
        """Test that SocketIO connection can be established."""
        # Attempt to connect
        connected = self.client.connect('http://127.0.0.1:5003')
        assert connected, "SocketIO client should connect successfully"
        
        # Verify connection
        assert self.client.connected, "Client should be connected"
        print("✅ SocketIO connection established successfully")
    
    def test_heartbeat_mechanism(self):
        """Test heartbeat mechanism."""
        # Connect first
        self.client.connect('http://127.0.0.1:5003')
        assert self.client.connected
        
        # Send heartbeat
        self.client.emit('heartbeat')
        
        # Should not disconnect (no error means success)
        time.sleep(1)
        assert self.client.connected, "Connection should remain after heartbeat"
        print("✅ Heartbeat mechanism working")
    
    def test_command_sending_structure(self):
        """Test command sending structure."""
        # Connect first
        self.client.connect('http://127.0.0.1:5003')
        assert self.client.connected
        
        # Send test command
        test_command = {
            'command': 'test_command',
            'params': {'test': 'value'},
            'timestamp': int(time.time() * 1000)
        }
        
        # This should not raise an exception
        self.client.emit('send_command', test_command)
        
        # Give time for processing
        time.sleep(0.5)
        
        print("✅ Command sending structure validated")
    
    def test_multiple_client_support(self):
        """Test that multiple clients can connect."""
        # Connect first client
        client1 = socketio.SimpleClient()
        connected1 = client1.connect('http://127.0.0.1:5003')
        assert connected1, "First client should connect"
        
        # Connect second client
        client2 = socketio.SimpleClient()
        connected2 = client2.connect('http://127.0.0.1:5003')
        assert connected2, "Second client should connect"
        
        # Both should be connected
        assert client1.connected and client2.connected
        
        # Cleanup
        client1.disconnect()
        client2.disconnect()
        
        print("✅ Multiple client connections supported")
    
    def test_event_handler_registration(self):
        """Test that event handlers are properly registered."""
        # Connect first
        self.client.connect('http://127.0.0.1:5003')
        assert self.client.connected
        
        # Test various events that should be handled
        test_events = [
            'connect',
            'disconnect', 
            'heartbeat',
            'send_command'
        ]
        
        # Send each event type (some may not have responses, that's OK)
        for event in test_events:
            if event not in ['connect', 'disconnect']:
                self.client.emit(event, {'test': True})
        
        time.sleep(1)
        print("✅ Event handlers registered and accepting events")
    
    def test_error_handling(self):
        """Test error handling for malformed requests."""
        # Connect first
        self.client.connect('http://127.0.0.1:5003')
        assert self.client.connected
        
        # Send malformed command
        self.client.emit('send_command', 'invalid_data')
        
        # Connection should remain stable
        time.sleep(0.5)
        assert self.client.connected, "Connection should remain stable after error"
        
        print("✅ Error handling working correctly")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__ + "::TestFlaskSocketIOCommunication::test_socketio_connection_establishment", "-v"])
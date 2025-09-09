"""
TEST-002: Heartbeat message reception
Phase 1: MAVLink Foundation

This test must FAIL first, then implementation must make it pass.
Tests MAVLink heartbeat message reception from virtual drone.
"""
import pytest
import time
from src.mavlink.mavlink_connection_manager import MAVLinkConnectionManager
from src.mavlink.mavlink_message_processor import MAVLinkMessageProcessor
from src.utils.token_tracker import record_agent_usage


class TestHeartbeatReception:
    """Test MAVLink heartbeat message reception."""
    
    def setup_method(self):
        """Set up test environment."""
        self.drone_host = "127.0.0.1"
        self.drone_port = 5678
        self.connection_manager = None
        self.message_processor = None
        
        # Record token usage for this test
        record_agent_usage('testing-agent', 60, 40)
    
    def teardown_method(self):
        """Clean up after test."""
        if self.connection_manager:
            self.connection_manager.disconnect()
        
        # Record token usage for test cleanup
        record_agent_usage('testing-agent', 25, 20)
    
    def test_message_processor_exists(self):
        """Test that MAVLinkMessageProcessor class exists."""
        # This will fail initially as we haven't implemented it yet
        self.message_processor = MAVLinkMessageProcessor()
        
        assert self.message_processor is not None
        assert hasattr(self.message_processor, 'process_message')
        assert hasattr(self.message_processor, 'get_last_heartbeat')
        assert hasattr(self.message_processor, 'get_heartbeat_count')
        assert hasattr(self.message_processor, 'is_heartbeat_active')
    
    def test_heartbeat_tracking_initialization(self):
        """Test heartbeat tracking is properly initialized."""
        self.message_processor = MAVLinkMessageProcessor()
        
        # Initial state should show no heartbeats
        assert self.message_processor.get_heartbeat_count() == 0
        assert self.message_processor.get_last_heartbeat() is None
        assert not self.message_processor.is_heartbeat_active()
    
    def test_heartbeat_message_processing(self):
        """Test processing of heartbeat messages."""
        self.message_processor = MAVLinkMessageProcessor()
        
        # Create mock heartbeat message data
        mock_heartbeat_data = {
            'type': 'HEARTBEAT',
            'system_id': 1,
            'component_id': 1,
            'mavtype': 2,  # MAV_TYPE_QUADROTOR
            'autopilot': 3,  # MAV_AUTOPILOT_ARDUPILOTMEGA
            'base_mode': 1,
            'custom_mode': 0,
            'system_status': 4,  # MAV_STATE_STANDBY
            'timestamp': time.time()
        }
        
        # Process the heartbeat message
        result = self.message_processor.process_message(mock_heartbeat_data)
        
        assert result is True, "Heartbeat message processing should succeed"
        assert self.message_processor.get_heartbeat_count() == 1
        assert self.message_processor.get_last_heartbeat() is not None
        assert self.message_processor.is_heartbeat_active()
    
    def test_multiple_heartbeat_processing(self):
        """Test processing multiple heartbeat messages."""
        self.message_processor = MAVLinkMessageProcessor()
        
        # Process multiple heartbeats
        for i in range(5):
            mock_heartbeat = {
                'type': 'HEARTBEAT',
                'system_id': 1,
                'component_id': 1,
                'timestamp': time.time() + (i * 0.1)
            }
            
            self.message_processor.process_message(mock_heartbeat)
            time.sleep(0.1)  # Small delay between heartbeats
        
        assert self.message_processor.get_heartbeat_count() == 5
        assert self.message_processor.is_heartbeat_active()
    
    def test_heartbeat_timeout_detection(self):
        """Test detection of heartbeat timeout (no recent heartbeats)."""
        self.message_processor = MAVLinkMessageProcessor(heartbeat_timeout=1.0)
        
        # Process one heartbeat
        old_heartbeat = {
            'type': 'HEARTBEAT',
            'system_id': 1,
            'component_id': 1,
            'timestamp': time.time() - 2.0  # 2 seconds ago
        }
        
        self.message_processor.process_message(old_heartbeat)
        
        # Should detect timeout after configured period
        assert not self.message_processor.is_heartbeat_active()
        assert self.message_processor.get_heartbeat_count() == 1  # Still counted
    
    def test_heartbeat_frequency_tracking(self):
        """Test tracking of heartbeat frequency."""
        self.message_processor = MAVLinkMessageProcessor()
        
        # Simulate heartbeats at ~1Hz (every 1 second)
        start_time = time.time()
        for i in range(3):
            heartbeat = {
                'type': 'HEARTBEAT',
                'system_id': 1,
                'component_id': 1,
                'timestamp': start_time + i
            }
            self.message_processor.process_message(heartbeat)
        
        # Should be able to calculate frequency
        frequency = self.message_processor.get_heartbeat_frequency()
        
        assert frequency is not None
        assert 0.8 <= frequency <= 1.2, f"Frequency {frequency} should be ~1Hz"
    
    def test_non_heartbeat_message_handling(self):
        """Test that non-heartbeat messages are handled appropriately."""
        self.message_processor = MAVLinkMessageProcessor()
        
        # Process a non-heartbeat message
        non_heartbeat = {
            'type': 'GLOBAL_POSITION_INT',
            'system_id': 1,
            'component_id': 1,
            'timestamp': time.time()
        }
        
        result = self.message_processor.process_message(non_heartbeat)
        
        # Should process successfully but not affect heartbeat count
        assert result is True
        assert self.message_processor.get_heartbeat_count() == 0
        assert not self.message_processor.is_heartbeat_active()


if __name__ == "__main__":
    # Run the test to see it fail (as required by TDD)
    pytest.main([__file__, "-v"])
    
    # Record final token usage
    record_agent_usage('testing-agent', 120, 100)
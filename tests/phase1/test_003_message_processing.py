"""
TEST-003: Telemetry/message processing
Phase 1: MAVLink Foundation

This test must FAIL first, then implementation must make it pass.
Tests comprehensive MAVLink message processing capabilities.
"""
import pytest
import time
from src.mavlink.mavlink_message_processor import MAVLinkMessageProcessor
from src.mavlink.mavlink_command_sender import MAVLinkCommandSender
from src.utils.token_tracker import record_agent_usage


class TestMessageProcessing:
    """Test comprehensive MAVLink message processing."""
    
    def setup_method(self):
        """Set up test environment."""
        self.message_processor = None
        self.command_sender = None
        
        # Record token usage for this test
        record_agent_usage('testing-agent', 70, 50)
    
    def teardown_method(self):
        """Clean up after test."""
        # Record token usage for test cleanup
        record_agent_usage('testing-agent', 30, 25)
    
    def test_command_sender_exists(self):
        """Test that MAVLinkCommandSender class exists."""
        # This will fail initially as we haven't implemented it yet
        self.command_sender = MAVLinkCommandSender()
        
        assert self.command_sender is not None
        assert hasattr(self.command_sender, 'send_command')
        assert hasattr(self.command_sender, 'send_arm_command')
        assert hasattr(self.command_sender, 'send_disarm_command')
        assert hasattr(self.command_sender, 'send_takeoff_command')
        assert hasattr(self.command_sender, 'send_set_mode_command')
    
    def test_global_position_message_processing(self):
        """Test processing GLOBAL_POSITION_INT messages."""
        self.message_processor = MAVLinkMessageProcessor()
        
        global_position_msg = {
            'type': 'GLOBAL_POSITION_INT',
            'system_id': 1,
            'component_id': 1,
            'lat': -353632607,  # Latitude * 1e7
            'lon': 1491652374,  # Longitude * 1e7
            'alt': 584000,      # Altitude in mm
            'relative_alt': 100000,  # Relative altitude in mm
            'vx': 50,           # Velocity X
            'vy': -25,          # Velocity Y
            'vz': 0,            # Velocity Z
            'hdg': 18000,       # Heading in centidegrees
            'timestamp': time.time()
        }
        
        result = self.message_processor.process_message(global_position_msg)
        assert result is True
        
        # Check message statistics
        stats = self.message_processor.get_message_statistics()
        assert stats.get('GLOBAL_POSITION_INT', 0) == 1
    
    def test_attitude_message_processing(self):
        """Test processing ATTITUDE messages."""
        self.message_processor = MAVLinkMessageProcessor()
        
        attitude_msg = {
            'type': 'ATTITUDE',
            'system_id': 1,
            'component_id': 1,
            'roll': 0.1,     # Roll angle in radians
            'pitch': -0.05,  # Pitch angle in radians
            'yaw': 1.57,     # Yaw angle in radians
            'rollspeed': 0.01,   # Roll angular speed
            'pitchspeed': 0.02,  # Pitch angular speed
            'yawspeed': 0.0,     # Yaw angular speed
            'timestamp': time.time()
        }
        
        result = self.message_processor.process_message(attitude_msg)
        assert result is True
        
        stats = self.message_processor.get_message_statistics()
        assert stats.get('ATTITUDE', 0) == 1
    
    def test_command_acknowledgment_processing(self):
        """Test processing COMMAND_ACK messages."""
        self.message_processor = MAVLinkMessageProcessor()
        
        command_ack_msg = {
            'type': 'COMMAND_ACK',
            'system_id': 1,
            'component_id': 1,
            'command': 400,  # MAV_CMD_COMPONENT_ARM_DISARM
            'result': 0,     # MAV_RESULT_ACCEPTED
            'progress': 255, # No progress info
            'result_param2': 0,
            'target_system': 255,
            'target_component': 0,
            'timestamp': time.time()
        }
        
        result = self.message_processor.process_message(command_ack_msg)
        assert result is True
        
        stats = self.message_processor.get_message_statistics()
        assert stats.get('COMMAND_ACK', 0) == 1
    
    def test_command_sender_arm_command(self):
        """Test sending ARM command."""
        self.command_sender = MAVLinkCommandSender()
        
        # Test ARM command creation
        arm_command = self.command_sender.send_arm_command()
        
        assert arm_command is not None
        assert isinstance(arm_command, dict)
        assert arm_command.get('command') == 400  # MAV_CMD_COMPONENT_ARM_DISARM
        assert arm_command.get('param1') == 1     # ARM
    
    def test_command_sender_disarm_command(self):
        """Test sending DISARM command."""
        self.command_sender = MAVLinkCommandSender()
        
        # Test DISARM command creation
        disarm_command = self.command_sender.send_disarm_command()
        
        assert disarm_command is not None
        assert isinstance(disarm_command, dict)
        assert disarm_command.get('command') == 400  # MAV_CMD_COMPONENT_ARM_DISARM
        assert disarm_command.get('param1') == 0     # DISARM
    
    def test_command_sender_takeoff_command(self):
        """Test sending TAKEOFF command."""
        self.command_sender = MAVLinkCommandSender()
        
        takeoff_altitude = 10.0  # 10 meters
        takeoff_command = self.command_sender.send_takeoff_command(takeoff_altitude)
        
        assert takeoff_command is not None
        assert isinstance(takeoff_command, dict)
        assert takeoff_command.get('command') == 22  # MAV_CMD_NAV_TAKEOFF
        assert takeoff_command.get('param7') == takeoff_altitude
    
    def test_command_sender_set_mode_command(self):
        """Test sending SET_MODE command."""
        self.command_sender = MAVLinkCommandSender()
        
        # Test GUIDED mode
        mode_command = self.command_sender.send_set_mode_command("GUIDED")
        
        assert mode_command is not None
        assert isinstance(mode_command, dict)
        assert mode_command.get('command') == 176  # MAV_CMD_DO_SET_MODE
    
    def test_multiple_message_types_processing(self):
        """Test processing multiple different message types."""
        self.message_processor = MAVLinkMessageProcessor()
        
        messages = [
            {'type': 'HEARTBEAT', 'system_id': 1, 'timestamp': time.time()},
            {'type': 'GLOBAL_POSITION_INT', 'system_id': 1, 'timestamp': time.time()},
            {'type': 'ATTITUDE', 'system_id': 1, 'timestamp': time.time()},
            {'type': 'COMMAND_ACK', 'system_id': 1, 'timestamp': time.time()},
            {'type': 'BATTERY_STATUS', 'system_id': 1, 'timestamp': time.time()}
        ]
        
        # Process all messages
        for msg in messages:
            result = self.message_processor.process_message(msg)
            assert result is True
        
        # Verify statistics
        stats = self.message_processor.get_message_statistics()
        assert len(stats) == 5  # 5 different message types
        assert stats.get('HEARTBEAT', 0) == 1
        assert stats.get('GLOBAL_POSITION_INT', 0) == 1
        assert stats.get('ATTITUDE', 0) == 1
        assert stats.get('COMMAND_ACK', 0) == 1
        assert stats.get('BATTERY_STATUS', 0) == 1
    
    def test_message_processing_rate(self):
        """Test message processing performance."""
        self.message_processor = MAVLinkMessageProcessor()
        
        # Process many messages to test performance
        start_time = time.time()
        message_count = 100
        
        for i in range(message_count):
            test_msg = {
                'type': 'GLOBAL_POSITION_INT',
                'system_id': 1,
                'timestamp': time.time()
            }
            self.message_processor.process_message(test_msg)
        
        elapsed_time = time.time() - start_time
        
        # Should process messages quickly (requirement: handle 10Hz telemetry)
        messages_per_second = message_count / elapsed_time
        assert messages_per_second > 50, f"Processing rate {messages_per_second:.1f} msgs/sec too slow"


if __name__ == "__main__":
    # Run the test to see it fail (as required by TDD)
    pytest.main([__file__, "-v"])
    
    # Record final token usage
    record_agent_usage('testing-agent', 150, 120)
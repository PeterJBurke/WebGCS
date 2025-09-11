"""
TEST-003: Command Sending Testing
Tests MAVLink command construction, sending, acknowledgment tracking, and safety.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from src.mavlink.command_sender import CommandSender


class TestCommandSending:
    """Test MAVLink command sending and acknowledgment functionality."""
    
    def test_command_sender_initialization(self, connection_manager):
        """Test CommandSender initializes correctly."""
        sender = CommandSender(connection_manager, ack_timeout=5.0)
        
        assert sender.connection_manager == connection_manager
        assert sender.ack_timeout == 5.0
        assert hasattr(sender, '_pending_commands')
        assert hasattr(sender, '_command_sequence')
        assert hasattr(sender, '_flight_modes')
        
        # Verify flight mode mappings
        assert 'GUIDED' in sender._flight_modes
        assert 'AUTO' in sender._flight_modes
        assert 'RTL' in sender._flight_modes
        assert sender._flight_modes['GUIDED'] == 4
        
        # Verify initial state
        pending = sender.get_pending_commands()
        assert isinstance(pending, dict)
        assert len(pending) == 0
    
    def test_command_id_sequence_generation(self, command_sender):
        """Test command ID sequence generation is unique and incrementing."""
        # Access private method for testing
        id1 = command_sender._get_next_command_id()
        id2 = command_sender._get_next_command_id()
        id3 = command_sender._get_next_command_id()
        
        # IDs should be unique and incrementing
        assert id1 != id2 != id3
        assert id2 == id1 + 1
        assert id3 == id2 + 1
        assert all(isinstance(cmd_id, int) for cmd_id in [id1, id2, id3])
    
    @patch('pymavlink.mavutil.mavlink_connection')
    def test_command_long_construction_and_sending(self, mock_connection_class, command_sender):
        """Test COMMAND_LONG message construction and sending."""
        # Mock the connection
        mock_connection = Mock()
        mock_mav = Mock()
        mock_connection.mav = mock_mav
        mock_connection.target_system = 1
        mock_connection.target_component = 1
        
        command_sender.connection_manager.get_connection = Mock(return_value=mock_connection)
        
        # Test command construction
        from pymavlink import mavutil
        command_id = command_sender._send_command_long(
            command=mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            param1=1,  # ARM
            param2=0,
            param3=10.5,  # Test float parameter
            param4=-5.2,  # Test negative parameter
            param5=0, param6=0, param7=0
        )
        
        # Verify command was sent
        assert command_id is not None
        assert isinstance(command_id, int)
        
        # Verify MAVLink command_long_send was called
        mock_mav.command_long_send.assert_called_once()
        call_args = mock_mav.command_long_send.call_args[0]
        
        assert call_args[0] == 1  # target_system
        assert call_args[1] == 1  # target_component
        assert call_args[2] == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM
        assert call_args[3] == command_id  # confirmation/sequence
        assert call_args[4] == 1  # param1
        assert call_args[5] == 0  # param2
        assert call_args[6] == 10.5  # param3
        assert call_args[7] == -5.2  # param4
        
        # Verify command is tracked as pending
        pending = command_sender.get_pending_commands()
        assert command_id in pending
        assert pending[command_id]['command'] == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM
        assert pending[command_id]['params'][0] == 1
        assert pending[command_id]['params'][2] == 10.5
    
    def test_command_sending_without_connection(self, command_sender):
        """Test command sending fails gracefully without connection."""
        # Ensure no connection
        command_sender.connection_manager.get_connection = Mock(return_value=None)
        
        # Attempt to send command
        from pymavlink import mavutil
        result = command_sender._send_command_long(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, param1=1)
        
        assert result is None
        
        # Verify no pending commands
        pending = command_sender.get_pending_commands()
        assert len(pending) == 0
    
    def test_arm_disarm_command_validation(self, command_sender):
        """Test ARM/DISARM command validation and safety checks."""
        # Mock connection manager
        command_sender.connection_manager.is_connected = Mock(return_value=True)
        command_sender._send_command_long = Mock(return_value=123)
        command_sender._wait_for_ack = Mock(return_value=True)
        
        # Test ARM command
        result = command_sender.arm_vehicle()
        assert result is True
        
        # Verify correct command was sent
        command_sender._send_command_long.assert_called_with(
            400,  # MAV_CMD_COMPONENT_ARM_DISARM
            param1=1,  # ARM
            param2=0   # no force
        )
        
        # Reset mocks
        command_sender._send_command_long.reset_mock()
        
        # Test DISARM command
        result = command_sender.disarm_vehicle()
        assert result is True
        
        command_sender._send_command_long.assert_called_with(
            400,  # MAV_CMD_COMPONENT_ARM_DISARM
            param1=0,  # DISARM
            param2=0   # no force
        )
        
        # Test force DISARM
        result = command_sender.disarm_vehicle(force=True)
        assert result is True
        
        command_sender._send_command_long.assert_called_with(
            400,
            param1=0,
            param2=21196  # force disarm magic number
        )
    
    def test_takeoff_command_validation(self, command_sender):
        """Test TAKEOFF command validation and safety limits."""
        command_sender.connection_manager.is_connected = Mock(return_value=True)
        command_sender._send_command_long = Mock(return_value=123)
        command_sender._wait_for_ack = Mock(return_value=True)
        
        # Test valid takeoff altitude
        result = command_sender.takeoff(10.0)
        assert result is True
        
        # Verify correct command was sent
        from pymavlink import mavutil
        command_sender._send_command_long.assert_called_with(
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            param1=0, param2=0, param3=0, param4=0, param5=0, param6=0,
            param7=10.0  # altitude
        )
        
        # Test invalid altitudes (safety checks)
        command_sender._send_command_long.reset_mock()
        
        # Zero altitude
        result = command_sender.takeoff(0.0)
        assert result is False
        command_sender._send_command_long.assert_not_called()
        
        # Negative altitude
        result = command_sender.takeoff(-5.0)
        assert result is False
        command_sender._send_command_long.assert_not_called()
        
        # Too high altitude (safety limit)
        result = command_sender.takeoff(150.0)
        assert result is False
        command_sender._send_command_long.assert_not_called()
        
        # Maximum valid altitude
        result = command_sender.takeoff(120.0)
        assert result is True
        command_sender._send_command_long.assert_called_once()
    
    def test_flight_mode_setting(self, command_sender):
        """Test flight mode setting with validation."""
        # Mock connection
        mock_connection = Mock()
        mock_mav = Mock()
        mock_connection.mav = mock_mav
        mock_connection.target_system = 1
        
        command_sender.connection_manager.is_connected = Mock(return_value=True)
        command_sender.connection_manager.get_connection = Mock(return_value=mock_connection)
        
        # Test valid flight modes
        valid_modes = ['GUIDED', 'AUTO', 'RTL', 'LOITER', 'STABILIZE']
        
        for mode in valid_modes:
            result = command_sender.set_mode(mode)
            assert result is True
            
            # Verify set_mode_send was called with correct parameters
            expected_mode_id = command_sender._flight_modes[mode]
            mock_mav.set_mode_send.assert_called_with(
                1,  # target_system
                1,  # MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
                expected_mode_id
            )
            
            mock_mav.reset_mock()
        
        # Test case insensitive mode names
        mock_mav.reset_mock()
        result = command_sender.set_mode('guided')
        assert result is True
        
        result = command_sender.set_mode('GUIDED')
        assert result is True
        
        # Test invalid flight mode
        mock_mav.reset_mock()
        result = command_sender.set_mode('INVALID_MODE')
        assert result is False
        mock_mav.set_mode_send.assert_not_called()
    
    def test_command_acknowledgment_tracking(self, command_sender):
        """Test command acknowledgment waiting and timeout handling."""
        # Mock connection for ACK reception
        mock_connection = Mock()
        command_sender.connection_manager.get_connection = Mock(return_value=mock_connection)
        
        # Test successful ACK
        from pymavlink import mavutil
        mock_ack_msg = Mock()
        mock_ack_msg.command = 123
        mock_ack_msg.result = mavutil.mavlink.MAV_RESULT_ACCEPTED
        
        mock_connection.recv_match.side_effect = [None, None, mock_ack_msg]  # ACK on 3rd call
        
        # Add command to pending list
        command_sender._pending_commands[123] = {
            'command': 400,
            'timestamp': datetime.now(),
            'params': [1, 0, 0, 0, 0, 0, 0]
        }
        
        result = command_sender._wait_for_ack(123)
        assert result is True
        
        # Verify command removed from pending
        pending = command_sender.get_pending_commands()
        assert 123 not in pending
        
        # Test command rejection
        mock_ack_msg.result = mavutil.mavlink.MAV_RESULT_DENIED
        mock_connection.recv_match.side_effect = [mock_ack_msg]
        
        command_sender._pending_commands[124] = {
            'command': 400,
            'timestamp': datetime.now(),
            'params': [1, 0, 0, 0, 0, 0, 0]
        }
        
        result = command_sender._wait_for_ack(124)
        assert result is False
        
        # Test timeout scenario
        mock_connection.recv_match.side_effect = [None] * 100  # No ACK received
        command_sender.ack_timeout = 0.5  # Short timeout for testing
        
        command_sender._pending_commands[125] = {
            'command': 400,
            'timestamp': datetime.now(),
            'params': [1, 0, 0, 0, 0, 0, 0]
        }
        
        start_time = time.time()
        result = command_sender._wait_for_ack(125)
        elapsed = time.time() - start_time
        
        assert result is False
        assert elapsed >= 0.5  # Should wait for timeout
        assert elapsed < 1.0   # But not much longer
        
        # Verify command removed from pending after timeout
        pending = command_sender.get_pending_commands()
        assert 125 not in pending
    
    def test_concurrent_command_handling(self, command_sender):
        """Test thread safety of concurrent command operations."""
        results = []
        errors = []
        
        # Mock connection manager
        command_sender.connection_manager.is_connected = Mock(return_value=True)
        command_sender._send_command_long = Mock(side_effect=lambda *args, **kwargs: len(results) + 1)
        command_sender._wait_for_ack = Mock(return_value=True)
        
        def send_command_worker(worker_id):
            try:
                for i in range(5):
                    result = command_sender.arm_vehicle()
                    results.append((worker_id, i, result))
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple worker threads
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=send_command_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Concurrent command errors: {errors}"
        
        # Verify all commands succeeded
        assert len(results) == 15  # 3 workers * 5 commands each
        assert all(result[2] is True for result in results)
    
    def test_pending_command_management(self, command_sender):
        """Test pending command tracking and cleanup."""
        # Add some pending commands manually
        now = datetime.now()
        command_sender._pending_commands[100] = {
            'command': 400,
            'timestamp': now,
            'params': [1, 0, 0, 0, 0, 0, 0]
        }
        command_sender._pending_commands[101] = {
            'command': 22,
            'timestamp': now - timedelta(seconds=30),
            'params': [10, 0, 0, 0, 0, 0, 0]
        }
        
        # Verify pending commands
        pending = command_sender.get_pending_commands()
        assert len(pending) == 2
        assert 100 in pending
        assert 101 in pending
        
        # Test clear all pending
        command_sender.clear_pending_commands()
        pending = command_sender.get_pending_commands()
        assert len(pending) == 0
    
    def test_real_drone_command_execution(self, connected_service):
        """Test actual command sending to virtual drone."""
        if not connected_service.connection_manager.is_connected():
            pytest.skip("Virtual drone not connected")
        
        command_sender = connected_service.command_sender
        
        # Test basic command without actual execution (safety)
        # We'll test command construction and sending but not full execution
        
        # Mock the actual command sending to avoid affecting drone state
        original_send = command_sender._send_command_long
        sent_commands = []
        
        def mock_send_command(command, **params):
            sent_commands.append((command, params))
            return len(sent_commands)  # Return fake command ID
        
        command_sender._send_command_long = mock_send_command
        command_sender._wait_for_ack = Mock(return_value=True)
        
        try:
            # Test ARM command construction
            result = command_sender.arm_vehicle()
            assert result is True
            assert len(sent_commands) == 1
            
            from pymavlink import mavutil
            assert sent_commands[0][0] == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM
            assert sent_commands[0][1]['param1'] == 1  # ARM
            
            # Test TAKEOFF command construction
            result = command_sender.takeoff(5.0)
            assert result is True
            assert len(sent_commands) == 2
            
            assert sent_commands[1][0] == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF
            assert sent_commands[1][1]['param7'] == 5.0  # altitude
            
            # Test mode change
            result = command_sender.set_mode('GUIDED')
            assert result is True
            
        finally:
            # Restore original method
            command_sender._send_command_long = original_send
    
    def test_command_timeout_performance(self, command_sender):
        """Test command acknowledgment timeout meets performance requirements."""
        # Mock connection with no ACK response
        mock_connection = Mock()
        mock_connection.recv_match.return_value = None
        command_sender.connection_manager.get_connection = Mock(return_value=mock_connection)
        
        # Set short timeout for testing
        original_timeout = command_sender.ack_timeout
        command_sender.ack_timeout = 1.0
        
        try:
            # Add pending command
            command_sender._pending_commands[999] = {
                'command': 400,
                'timestamp': datetime.now(),
                'params': [1, 0, 0, 0, 0, 0, 0]
            }
            
            # Test timeout performance
            start_time = time.time()
            result = command_sender._wait_for_ack(999)
            elapsed = time.time() - start_time
            
            # Verify timeout behavior
            assert result is False
            assert 1.0 <= elapsed <= 1.2  # Should timeout close to 1 second
            
            # Verify command removed from pending
            pending = command_sender.get_pending_commands()
            assert 999 not in pending
            
        finally:
            command_sender.ack_timeout = original_timeout
    
    def test_emergency_command_scenarios(self, command_sender):
        """Test emergency command handling and error scenarios."""
        command_sender.connection_manager.is_connected = Mock(return_value=True)
        command_sender._send_command_long = Mock(return_value=None)  # Simulate send failure
        
        # Test command sending failure
        result = command_sender.arm_vehicle()
        assert result is False
        
        result = command_sender.disarm_vehicle()
        assert result is False
        
        result = command_sender.takeoff(10.0)
        assert result is False
        
        # Test disconnect during command
        command_sender.connection_manager.is_connected = Mock(return_value=False)
        
        result = command_sender.arm_vehicle()
        assert result is False
        
        result = command_sender.land()
        assert result is False
        
        result = command_sender.return_to_launch()
        assert result is False
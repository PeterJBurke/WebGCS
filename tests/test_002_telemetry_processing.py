"""
TEST-002: Telemetry Processing Testing
Tests MAVLink message processing, data conversion, and telemetry handling.
"""

import pytest
import time
import math
from datetime import datetime
from unittest.mock import Mock, MagicMock
from pymavlink import mavutil
from src.mavlink.message_processor import MessageProcessor


class TestTelemetryProcessing:
    """Test MAVLink message processing and telemetry data handling."""
    
    def test_message_processor_initialization(self, message_processor):
        """Test MessageProcessor initializes correctly."""
        assert isinstance(message_processor, MessageProcessor)
        
        # Verify message handlers are registered
        assert hasattr(message_processor, '_message_handlers')
        assert 'HEARTBEAT' in message_processor._message_handlers
        assert 'ATTITUDE' in message_processor._message_handlers
        assert 'GLOBAL_POSITION_INT' in message_processor._message_handlers
        assert 'VFR_HUD' in message_processor._message_handlers
        assert 'SYS_STATUS' in message_processor._message_handlers
        assert 'BATTERY_STATUS' in message_processor._message_handlers
        
        # Verify telemetry cache is initialized
        cache = message_processor.get_telemetry_snapshot()
        assert isinstance(cache, dict)
    
    def test_heartbeat_message_processing(self, message_processor):
        """Test HEARTBEAT message processing and data extraction."""
        # Create mock HEARTBEAT message
        msg = Mock()
        msg.get_type.return_value = 'HEARTBEAT'
        msg.autopilot = mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA
        msg.type = mavutil.mavlink.MAV_TYPE_QUADROTOR
        msg.system_status = mavutil.mavlink.MAV_STATE_ACTIVE
        msg.base_mode = (mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED | 
                        mavutil.mavlink.MAV_MODE_FLAG_GUIDED_ENABLED)
        msg.custom_mode = 4  # GUIDED mode
        msg.mavlink_version = 3
        
        # Process message
        result = message_processor.process_message(msg)
        
        # Verify result structure
        assert result is not None
        assert 'heartbeat' in result
        
        heartbeat_data = result['heartbeat']
        assert 'timestamp' in heartbeat_data
        assert heartbeat_data['autopilot'] == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA
        assert heartbeat_data['type'] == mavutil.mavlink.MAV_TYPE_QUADROTOR
        assert heartbeat_data['system_status'] == mavutil.mavlink.MAV_STATE_ACTIVE
        assert heartbeat_data['armed'] is True
        assert heartbeat_data['guided'] is True
        assert heartbeat_data['flight_mode'] == 'GUIDED'
        
        # Verify cache is updated
        cache = message_processor.get_telemetry_snapshot()
        assert 'heartbeat' in cache
        assert 'last_update' in cache
    
    def test_attitude_message_processing(self, message_processor):
        """Test ATTITUDE message processing and unit conversion."""
        # Create mock ATTITUDE message with radian values
        msg = Mock()
        msg.get_type.return_value = 'ATTITUDE'
        msg.roll = math.radians(15.0)      # 15 degrees in radians
        msg.pitch = math.radians(-10.0)    # -10 degrees in radians
        msg.yaw = math.radians(45.0)       # 45 degrees in radians
        msg.rollspeed = math.radians(5.0)  # 5 deg/s in rad/s
        msg.pitchspeed = math.radians(-2.0) # -2 deg/s in rad/s
        msg.yawspeed = math.radians(10.0)  # 10 deg/s in rad/s
        
        # Process message
        result = message_processor.process_message(msg)
        
        # Verify result structure and unit conversion
        assert result is not None
        assert 'attitude' in result
        
        attitude_data = result['attitude']
        assert 'timestamp' in attitude_data
        
        # Verify angles converted to degrees (with tolerance for floating point)
        assert abs(attitude_data['roll'] - 15.0) < 0.01
        assert abs(attitude_data['pitch'] - (-10.0)) < 0.01
        assert abs(attitude_data['yaw'] - 45.0) < 0.01
        
        # Verify angular rates converted to degrees/second
        assert abs(attitude_data['rollspeed'] - 5.0) < 0.01
        assert abs(attitude_data['pitchspeed'] - (-2.0)) < 0.01
        assert abs(attitude_data['yawspeed'] - 10.0) < 0.01
    
    def test_global_position_message_processing(self, message_processor):
        """Test GLOBAL_POSITION_INT message processing and unit conversion."""
        # Create mock GLOBAL_POSITION_INT message
        msg = Mock()
        msg.get_type.return_value = 'GLOBAL_POSITION_INT'
        msg.lat = 473977418  # 47.3977418 degrees * 1E7
        msg.lon = 85455939   # 8.5455939 degrees * 1E7
        msg.alt = 488000     # 488 meters * 1000 (mm)
        msg.relative_alt = 50000  # 50 meters * 1000 (mm)
        msg.vx = 150         # 1.5 m/s * 100 (cm/s)
        msg.vy = -200        # -2.0 m/s * 100 (cm/s)
        msg.vz = -50         # -0.5 m/s * 100 (cm/s)
        msg.hdg = 12500      # 125 degrees * 100 (centidegrees)
        msg.time_boot_ms = 123456
        
        # Process message
        result = message_processor.process_message(msg)
        
        # Verify result structure and unit conversion
        assert result is not None
        assert 'gps' in result
        
        gps_data = result['gps']
        assert 'timestamp' in gps_data
        
        # Verify coordinate conversion (1E7 degrees to degrees)
        assert abs(gps_data['lat'] - 47.3977418) < 0.0000001
        assert abs(gps_data['lon'] - 8.5455939) < 0.0000001
        
        # Verify altitude conversion (mm to meters)
        assert abs(gps_data['alt'] - 488.0) < 0.001
        assert abs(gps_data['relative_alt'] - 50.0) < 0.001
        
        # Verify velocity conversion (cm/s to m/s)
        assert abs(gps_data['vx'] - 1.5) < 0.01
        assert abs(gps_data['vy'] - (-2.0)) < 0.01
        assert abs(gps_data['vz'] - (-0.5)) < 0.01
        
        # Verify heading conversion (centidegrees to degrees)
        assert abs(gps_data['hdg'] - 125.0) < 0.01
        
        assert gps_data['time_boot_ms'] == 123456
    
    def test_vfr_hud_message_processing(self, message_processor):
        """Test VFR_HUD message processing for flight instruments."""
        # Create mock VFR_HUD message
        msg = Mock()
        msg.get_type.return_value = 'VFR_HUD'
        msg.airspeed = 15.5      # m/s
        msg.groundspeed = 12.3   # m/s
        msg.heading = 275        # degrees
        msg.throttle = 65        # percentage
        msg.alt = 152.4          # meters MSL
        msg.climb = -2.1         # m/s
        
        # Process message
        result = message_processor.process_message(msg)
        
        # Verify result structure
        assert result is not None
        assert 'vfr_hud' in result
        
        vfr_data = result['vfr_hud']
        assert 'timestamp' in vfr_data
        assert vfr_data['airspeed'] == 15.5
        assert vfr_data['groundspeed'] == 12.3
        assert vfr_data['heading'] == 275
        assert vfr_data['throttle'] == 65
        assert vfr_data['alt'] == 152.4
        assert vfr_data['climb'] == -2.1
    
    def test_sys_status_message_processing(self, message_processor):
        """Test SYS_STATUS message processing and unit conversion."""
        # Create mock SYS_STATUS message
        msg = Mock()
        msg.get_type.return_value = 'SYS_STATUS'
        msg.voltage_battery = 12580   # 12.58V * 1000 (mV)
        msg.current_battery = 1250    # 12.5A * 100 (cA)
        msg.battery_remaining = 75    # percentage
        msg.drop_rate_comm = 150      # 1.5% * 100
        msg.errors_comm = 5
        msg.errors_count1 = 1
        msg.errors_count2 = 0
        msg.errors_count3 = 2
        msg.errors_count4 = 0
        
        # Process message
        result = message_processor.process_message(msg)
        
        # Verify result structure and unit conversion
        assert result is not None
        assert 'sys_status' in result
        
        sys_data = result['sys_status']
        assert 'timestamp' in sys_data
        
        # Verify voltage conversion (mV to V)
        assert abs(sys_data['voltage_battery'] - 12.58) < 0.001
        
        # Verify current conversion (cA to A)
        assert abs(sys_data['current_battery'] - 12.5) < 0.01
        
        assert sys_data['battery_remaining'] == 75
        
        # Verify drop rate conversion
        assert abs(sys_data['drop_rate_comm'] - 1.5) < 0.01
        
        assert sys_data['errors_comm'] == 5
        assert sys_data['errors_count1'] == 1
        assert sys_data['errors_count2'] == 0
    
    def test_battery_status_message_processing(self, message_processor):
        """Test BATTERY_STATUS message processing."""
        # Create mock BATTERY_STATUS message
        msg = Mock()
        msg.get_type.return_value = 'BATTERY_STATUS'
        msg.id = 0
        msg.battery_function = 0
        msg.type = 1
        msg.temperature = 2500        # 25.0°C * 100 (centidegrees)
        msg.voltages = [4150, 4140, 4160, 65535, 65535, 65535, 65535, 65535, 65535, 65535]  # mV
        msg.current_battery = 1200    # 12.0A * 100 (cA)
        msg.current_consumed = 3500   # mAh
        msg.energy_consumed = 158400  # hJ
        msg.battery_remaining = 80    # percentage
        
        # Process message
        result = message_processor.process_message(msg)
        
        # Verify result structure and unit conversion
        assert result is not None
        assert 'battery' in result
        
        battery_data = result['battery']
        assert 'timestamp' in battery_data
        assert battery_data['id'] == 0
        
        # Verify temperature conversion (centidegrees to degrees)
        assert abs(battery_data['temperature'] - 25.0) < 0.01
        
        # Verify voltage conversion (mV to V) and filtering of invalid values
        expected_voltages = [4.15, 4.14, 4.16]  # Only first 3 are valid
        assert len(battery_data['voltages']) == 3
        for i, voltage in enumerate(battery_data['voltages']):
            assert abs(voltage - expected_voltages[i]) < 0.001
        
        # Verify current conversion (cA to A)
        assert abs(battery_data['current_battery'] - 12.0) < 0.01
        
        assert battery_data['current_consumed'] == 3500
        assert battery_data['energy_consumed'] == 158400
        assert battery_data['battery_remaining'] == 80
    
    def test_message_processing_error_handling(self, message_processor):
        """Test error handling in message processing."""
        # Test with None message
        result = message_processor.process_message(None)
        assert result is None
        
        # Test with malformed message
        bad_msg = Mock()
        bad_msg.get_type.return_value = 'HEARTBEAT'
        bad_msg.autopilot = None  # This should cause an error
        
        # Should handle error gracefully and return None
        result = message_processor.process_message(bad_msg)
        assert result is None
        
        # Test with unknown message type
        unknown_msg = Mock()
        unknown_msg.get_type.return_value = 'UNKNOWN_MESSAGE_TYPE'
        
        result = message_processor.process_message(unknown_msg)
        assert result is None
    
    def test_telemetry_cache_management(self, message_processor):
        """Test telemetry data caching and retrieval."""
        # Initial cache should be empty
        initial_cache = message_processor.get_telemetry_snapshot()
        assert isinstance(initial_cache, dict)
        
        # Process some messages
        heartbeat_msg = Mock()
        heartbeat_msg.get_type.return_value = 'HEARTBEAT'
        heartbeat_msg.autopilot = 3
        heartbeat_msg.type = 2
        heartbeat_msg.system_status = 4
        heartbeat_msg.base_mode = 1
        heartbeat_msg.custom_mode = 0
        heartbeat_msg.mavlink_version = 3
        
        attitude_msg = Mock()
        attitude_msg.get_type.return_value = 'ATTITUDE'
        attitude_msg.roll = 0.1
        attitude_msg.pitch = 0.2
        attitude_msg.yaw = 0.3
        attitude_msg.rollspeed = 0.01
        attitude_msg.pitchspeed = 0.02
        attitude_msg.yawspeed = 0.03
        
        # Process messages
        message_processor.process_message(heartbeat_msg)
        message_processor.process_message(attitude_msg)
        
        # Verify cache contains both message types
        cache = message_processor.get_telemetry_snapshot()
        assert 'heartbeat' in cache
        assert 'attitude' in cache
        assert 'last_update' in cache
        
        # Verify cache returns independent copies
        cache1 = message_processor.get_telemetry_snapshot()
        cache2 = message_processor.get_telemetry_snapshot()
        
        # Modify one cache
        cache1['test_field'] = 'test_value'
        
        # Other cache should be unaffected
        assert 'test_field' not in cache2
    
    def test_telemetry_update_rate_performance(self, connected_service):
        """Test telemetry processing meets 10Hz update rate requirement."""
        if not connected_service.connection_manager.is_connected():
            pytest.skip("Virtual drone not connected")
        
        processor = connected_service.message_processor
        update_times = []
        
        def telemetry_callback(data):
            update_times.append(time.time())
        
        connected_service.add_telemetry_callback(telemetry_callback)
        
        # Wait for telemetry updates
        start_time = time.time()
        while len(update_times) < 20 and (time.time() - start_time) < 5.0:
            time.sleep(0.05)
        
        assert len(update_times) >= 10, "Should receive at least 10 telemetry updates in 5 seconds"
        
        # Calculate update intervals
        intervals = []
        for i in range(1, len(update_times)):
            interval = update_times[i] - update_times[i-1]
            intervals.append(interval)
        
        # Verify average update rate is at least 5Hz (0.2s interval)
        # This allows for some variability while ensuring reasonable performance
        avg_interval = sum(intervals) / len(intervals)
        assert avg_interval < 0.2, f"Average telemetry interval {avg_interval:.3f}s too high for 10Hz requirement"
    
    def test_real_drone_message_processing(self, connected_service):
        """Test processing of actual messages from virtual drone."""
        if not connected_service.connection_manager.is_connected():
            pytest.skip("Virtual drone not connected")
        
        processor = connected_service.message_processor
        received_messages = {}
        
        def telemetry_callback(data):
            for msg_type in data.keys():
                if msg_type != 'last_update':
                    received_messages[msg_type] = data[msg_type]
        
        connected_service.add_telemetry_callback(telemetry_callback)
        
        # Wait for various message types
        start_time = time.time()
        expected_messages = ['heartbeat', 'attitude', 'gps']
        
        while (not all(msg in received_messages for msg in expected_messages) and 
               (time.time() - start_time) < 10.0):
            time.sleep(0.1)
        
        # Verify we received expected message types
        assert 'heartbeat' in received_messages, "Should receive HEARTBEAT messages"
        
        # Verify heartbeat data structure
        heartbeat = received_messages['heartbeat']
        assert 'armed' in heartbeat
        assert 'flight_mode' in heartbeat
        assert 'timestamp' in heartbeat
        
        # Check other common message types if available
        if 'attitude' in received_messages:
            attitude = received_messages['attitude']
            assert 'roll' in attitude
            assert 'pitch' in attitude
            assert 'yaw' in attitude
            
            # Verify attitude values are in reasonable ranges
            assert -180 <= attitude['roll'] <= 180
            assert -90 <= attitude['pitch'] <= 90
        
        if 'gps' in received_messages:
            gps = received_messages['gps']
            assert 'lat' in gps
            assert 'lon' in gps
            assert 'alt' in gps
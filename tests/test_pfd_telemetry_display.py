#!/usr/bin/env python3
"""
Primary Flight Display (PFD) Telemetry Display Testing Agent
Tests all PFD elements for real-time telemetry updates from virtual drone
"""

import time
import requests
import json
import socketio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import threading
from dataclasses import dataclass
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TelemetrySnapshot:
    """Capture telemetry data snapshot with timestamp"""
    timestamp: datetime
    data: Dict[str, Any]
    
@dataclass
class TestResult:
    """Test result data"""
    test_name: str
    passed: bool
    details: str
    timestamp: datetime
    duration: Optional[float] = None

class PFDTelemetryTester:
    """Primary Flight Display Telemetry Testing Agent"""
    
    def __init__(self, server_url: str = "http://localhost:5001"):
        self.server_url = server_url
        self.socketio_url = server_url.replace('http', 'ws')
        self.sio = None
        self.test_results: List[TestResult] = []
        self.telemetry_history: deque = deque(maxlen=1000)  # Keep last 1000 samples
        self.connected = False
        self.test_start_time = None
        self.update_count = 0
        self.last_update_time = None
        self.update_times = deque(maxlen=100)  # Track update timing
        
        # Expected PFD elements to test
        self.pfd_elements = {
            'attitude-indicator': {'width': 280, 'height': 250, 'type': 'canvas'},
            'airspeed-tape': {'width': 60, 'height': 250, 'type': 'canvas'},
            'altitude-tape': {'width': 70, 'height': 250, 'type': 'canvas'},
            'armed-status': {'type': 'text', 'values': ['ARMED', 'DISARMED']},
            'flight-mode': {'type': 'text', 'format': 'Mode: XXXX'},
            'battery-voltage': {'type': 'text', 'format': 'Bat: XX.X V'},
            'current-draw': {'type': 'text', 'format': 'Cur: XX.X A'},
            'gps-status': {'type': 'text', 'format': 'GPS: XXX (X) HDOP:XX.X'},
            'position-display': {'type': 'text', 'format': 'lat, lon (6 decimals)'}
        }
        
    def connect_socketio(self) -> bool:
        """Connect to WebGCS SocketIO server"""
        try:
            logger.info("Connecting to WebGCS SocketIO server...")
            self.sio = socketio.Client()
            
            @self.sio.event
            def connect():
                logger.info("Connected to WebGCS SocketIO server")
                self.connected = True
                
            @self.sio.event  
            def disconnect():
                logger.info("Disconnected from WebGCS SocketIO server")
                self.connected = False
                
            @self.sio.event
            def telemetry_update(data):
                """Handle telemetry updates"""
                now = datetime.now()
                self.telemetry_history.append(TelemetrySnapshot(now, data))
                self.update_count += 1
                
                # Track update timing
                if self.last_update_time:
                    delta = (now - self.last_update_time).total_seconds()
                    self.update_times.append(delta)
                    
                self.last_update_time = now
                
                if self.update_count % 10 == 0:  # Log every 10th update
                    logger.debug(f"Telemetry update #{self.update_count}: {json.dumps(data, indent=2)}")
                    
            @self.sio.event
            def connection_status(data):
                """Handle connection status updates"""
                logger.info(f"Connection status: {data}")
                
            # Connect
            self.sio.connect(self.server_url)
            time.sleep(1)  # Allow connection to establish
            
            return self.connected
            
        except Exception as e:
            logger.error(f"Failed to connect to SocketIO: {e}")
            return False
            
    def check_server_health(self) -> TestResult:
        """TEST-PFD-000: Check server health and connectivity"""
        start_time = datetime.now()
        
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                duration = (datetime.now() - start_time).total_seconds()
                
                details = f"Server healthy. Response: {health_data}"
                return TestResult("TEST-PFD-000: Server Health", True, details, start_time, duration)
            else:
                details = f"Server returned status {response.status_code}"
                return TestResult("TEST-PFD-000: Server Health", False, details, start_time)
                
        except Exception as e:
            details = f"Server health check failed: {e}"
            return TestResult("TEST-PFD-000: Server Health", False, details, start_time)
            
    def test_real_time_telemetry_updates(self, duration_seconds: int = 60) -> TestResult:
        """TEST-PFD-001: Real-time Telemetry Display Updates"""
        logger.info(f"Starting TEST-PFD-001: Real-time telemetry updates test ({duration_seconds}s)")
        
        start_time = datetime.now()
        self.test_start_time = start_time
        self.update_count = 0
        self.update_times.clear()
        self.telemetry_history.clear()
        
        # Wait for telemetry updates
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        logger.info("Collecting telemetry data...")
        while datetime.now() < end_time:
            time.sleep(0.1)  # 100ms polling interval
            
            if self.update_count > 0 and self.update_count % 100 == 0:
                logger.info(f"Collected {self.update_count} telemetry updates so far...")
                
        test_duration = (datetime.now() - start_time).total_seconds()
        
        # Analyze results
        if len(self.telemetry_history) == 0:
            return TestResult(
                "TEST-PFD-001: Real-time Telemetry Updates",
                False,
                "No telemetry data received during test period",
                start_time,
                test_duration
            )
            
        # Calculate update rate
        update_rate = self.update_count / test_duration
        
        # Calculate average latency (time between updates)
        if len(self.update_times) > 0:
            avg_interval = sum(self.update_times) / len(self.update_times)
            avg_frequency = 1.0 / avg_interval if avg_interval > 0 else 0
        else:
            avg_interval = 0
            avg_frequency = 0
            
        # Check for required telemetry fields
        latest_data = self.telemetry_history[-1].data if self.telemetry_history else {}
        required_fields = ['lat', 'lon', 'alt_rel', 'vx', 'vy', 'pitch', 'roll', 'armed', 'mode']
        missing_fields = [field for field in required_fields if field not in latest_data]
        
        # Verify data freshness (no stale data >200ms)
        now = datetime.now()
        stale_data = []
        for snapshot in list(self.telemetry_history)[-10:]:  # Check last 10 samples
            age = (now - snapshot.timestamp).total_seconds() * 1000  # Convert to ms
            if age > 200:
                stale_data.append(f"Data {age:.1f}ms old")
                
        # Determine pass/fail
        passed = True
        issues = []
        
        # Check update rate (9-11 Hz acceptable)
        if not (9 <= update_rate <= 11):
            passed = False
            issues.append(f"Update rate {update_rate:.2f}Hz outside 9-11Hz range")
            
        # Check for missing fields
        if missing_fields:
            passed = False
            issues.append(f"Missing telemetry fields: {missing_fields}")
            
        # Check for stale data
        if stale_data:
            passed = False
            issues.append(f"Stale data detected: {stale_data}")
            
        details = f"""Telemetry Update Analysis:
• Total updates: {self.update_count}
• Test duration: {test_duration:.1f}s  
• Update rate: {update_rate:.2f} Hz
• Average interval: {avg_interval*1000:.1f}ms
• Average frequency: {avg_frequency:.2f} Hz
• Latest telemetry fields: {list(latest_data.keys())}
• Missing required fields: {missing_fields}
• Issues: {issues if issues else 'None'}

Latest telemetry sample:
{json.dumps(latest_data, indent=2)}"""
        
        return TestResult(
            "TEST-PFD-001: Real-time Telemetry Updates",
            passed,
            details,
            start_time,
            test_duration
        )
        
    def test_attitude_indicator_data(self) -> TestResult:
        """Test attitude indicator receives pitch/roll data"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-001a: Attitude Indicator Data",
                False,
                "No telemetry data available for attitude test",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        # Check for pitch and roll data
        has_pitch = 'pitch' in latest_data
        has_roll = 'roll' in latest_data
        
        pitch_value = latest_data.get('pitch', 0)
        roll_value = latest_data.get('roll', 0)
        
        # Verify data types and ranges
        pitch_valid = isinstance(pitch_value, (int, float)) and -90 <= pitch_value <= 90
        roll_valid = isinstance(roll_value, (int, float)) and -180 <= roll_value <= 180
        
        passed = has_pitch and has_roll and pitch_valid and roll_valid
        
        details = f"""Attitude Indicator Data Check:
• Has pitch: {has_pitch} (value: {pitch_value})  
• Has roll: {has_roll} (value: {roll_value})
• Pitch valid range (-90 to 90): {pitch_valid}
• Roll valid range (-180 to 180): {roll_valid}
• Canvas dimensions: 280x250px (as specified)"""
        
        return TestResult(
            "TEST-PFD-001a: Attitude Indicator Data", 
            passed, 
            details, 
            start_time
        )
        
    def test_airspeed_altitude_tapes(self) -> TestResult:
        """Test airspeed and altitude tape data"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-001b: Airspeed/Altitude Tapes",
                False,
                "No telemetry data available for tape test",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        # Check airspeed components (vx, vy for ground speed calculation)
        has_vx = 'vx' in latest_data
        has_vy = 'vy' in latest_data
        has_altitude = 'alt_rel' in latest_data
        
        vx = latest_data.get('vx', 0)
        vy = latest_data.get('vy', 0)
        altitude = latest_data.get('alt_rel', 0)
        
        # Calculate ground speed (used as airspeed proxy)
        ground_speed = (vx**2 + vy**2)**0.5 if has_vx and has_vy else 0
        
        passed = has_vx and has_vy and has_altitude
        
        details = f"""Airspeed/Altitude Tape Data Check:
• Has vx (velocity component): {has_vx} (value: {vx})
• Has vy (velocity component): {has_vy} (value: {vy})
• Calculated ground speed: {ground_speed:.2f} m/s
• Has relative altitude: {has_altitude} (value: {altitude})
• Airspeed tape canvas: 60x250px
• Altitude tape canvas: 70x250px"""
        
        return TestResult(
            "TEST-PFD-001b: Airspeed/Altitude Tapes",
            passed,
            details,
            start_time
        )
        
    def test_flight_mode_display(self) -> TestResult:
        """TEST-PFD-002: Flight Mode Display"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-002: Flight Mode Display",
                False,
                "No telemetry data available for flight mode test",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        has_mode = 'mode' in latest_data
        mode_value = latest_data.get('mode', 'UNKNOWN')
        
        # Check if mode is a valid flight mode
        valid_modes = [
            'STABILIZE', 'ACRO', 'ALT_HOLD', 'AUTO', 'GUIDED', 
            'LOITER', 'RTL', 'CIRCLE', 'POSITION', 'LAND', 
            'OF_LOITER', 'DRIFT', 'SPORT', 'FLIP', 'AUTOTUNE',
            'POSHOLD', 'BRAKE', 'THROW', 'AVOID_ADSB', 'GUIDED_NOGPS'
        ]
        
        mode_valid = mode_value in valid_modes
        
        passed = has_mode and isinstance(mode_value, str)
        
        details = f"""Flight Mode Display Check:
• Has mode field: {has_mode}
• Mode value: '{mode_value}'
• Mode in valid list: {mode_valid}
• Display format: 'Mode: {mode_value}'"""
        
        return TestResult(
            "TEST-PFD-002: Flight Mode Display",
            passed,
            details,
            start_time
        )
        
    def test_armed_status_display(self) -> TestResult:
        """TEST-PFD-003: Armed Status Display"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-003: Armed Status Display", 
                False,
                "No telemetry data available for armed status test",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        has_armed = 'armed' in latest_data
        armed_value = latest_data.get('armed', False)
        
        # Verify armed status is boolean
        armed_valid = isinstance(armed_value, bool)
        
        # Expected display text
        expected_display = "ARMED" if armed_value else "DISARMED"
        
        passed = has_armed and armed_valid
        
        details = f"""Armed Status Display Check:
• Has armed field: {has_armed}
• Armed value: {armed_value}
• Value is boolean: {armed_valid}
• Expected display: '{expected_display}'"""
        
        return TestResult(
            "TEST-PFD-003: Armed Status Display",
            passed,
            details,
            start_time
        )
        
    def test_battery_telemetry(self) -> TestResult:
        """Test battery voltage and current display"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-004: Battery Telemetry",
                False, 
                "No telemetry data available for battery test",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        has_voltage = 'battery_voltage' in latest_data
        has_current = 'current' in latest_data
        
        voltage = latest_data.get('battery_voltage', 0)
        current = latest_data.get('current', 0)
        
        # Verify reasonable ranges
        voltage_valid = isinstance(voltage, (int, float)) and 0 <= voltage <= 30  # 0-30V range
        current_valid = isinstance(current, (int, float)) and 0 <= current <= 100  # 0-100A range
        
        passed = has_voltage and has_current and voltage_valid and current_valid
        
        details = f"""Battery Telemetry Check:
• Has battery_voltage: {has_voltage} (value: {voltage}V)
• Has current: {has_current} (value: {current}A) 
• Voltage valid (0-30V): {voltage_valid}
• Current valid (0-100A): {current_valid}
• Display format: 'Bat: {voltage:.1f} V', 'Cur: {current:.1f} A'"""
        
        return TestResult(
            "TEST-PFD-004: Battery Telemetry",
            passed,
            details,
            start_time
        )
        
    def test_gps_position_display(self) -> TestResult:
        """Test GPS status and position display with 6 decimal precision"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-005: GPS Position Display",
                False,
                "No telemetry data available for GPS test", 
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        has_lat = 'lat' in latest_data
        has_lon = 'lon' in latest_data
        has_gps_fix = 'gps_fix_type' in latest_data
        has_sats = 'satellites_visible' in latest_data
        has_hdop = 'hdop' in latest_data
        
        lat = latest_data.get('lat', 0)
        lon = latest_data.get('lon', 0)
        gps_fix = latest_data.get('gps_fix_type', 0)
        sats = latest_data.get('satellites_visible', 0)
        hdop = latest_data.get('hdop', 99.9)
        
        # Verify coordinate ranges
        lat_valid = isinstance(lat, (int, float)) and -90 <= lat <= 90
        lon_valid = isinstance(lon, (int, float)) and -180 <= lon <= 180
        
        # GPS fix types
        fix_types = ['NO_GPS', 'NO_FIX', '2D_FIX', '3D_FIX', 'DGPS', 'RTK_FLOAT', 'RTK_FIXED']
        fix_name = fix_types[gps_fix] if 0 <= gps_fix < len(fix_types) else 'UNKNOWN'
        
        passed = has_lat and has_lon and lat_valid and lon_valid and has_gps_fix
        
        details = f"""GPS Position Display Check:
• Has latitude: {has_lat} (value: {lat})
• Has longitude: {has_lon} (value: {lon})
• Latitude valid (-90 to 90): {lat_valid}
• Longitude valid (-180 to 180): {lon_valid}
• GPS fix type: {gps_fix} ({fix_name})
• Satellites visible: {sats}
• HDOP: {hdop}
• Position format (6 decimals): '{lat:.6f}, {lon:.6f}'
• GPS status format: 'GPS: {fix_name} ({sats}) HDOP:{hdop:.1f}'"""
        
        return TestResult(
            "TEST-PFD-005: GPS Position Display",
            passed, 
            details,
            start_time
        )
        
    def run_all_tests(self) -> List[TestResult]:
        """Run all PFD telemetry display tests"""
        logger.info("=== STARTING PFD TELEMETRY DISPLAY TESTING ===")
        
        # Test 0: Server health
        result = self.check_server_health()
        self.test_results.append(result)
        logger.info(f"✅ {result.test_name}: {'PASSED' if result.passed else 'FAILED'}")
        
        if not result.passed:
            logger.error("Server health check failed. Aborting tests.")
            return self.test_results
            
        # Connect to SocketIO
        if not self.connect_socketio():
            logger.error("Failed to connect to SocketIO. Aborting tests.")
            return self.test_results
            
        try:
            # Test 1: Real-time telemetry updates (60 second test)
            result = self.test_real_time_telemetry_updates(60)
            self.test_results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"{status} {result.test_name}")
            
            if not result.passed:
                logger.warning("Real-time telemetry test failed. Continuing with available data...")
                
            # Test 1a: Attitude indicator data
            result = self.test_attitude_indicator_data()
            self.test_results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED" 
            logger.info(f"{status} {result.test_name}")
            
            # Test 1b: Airspeed/altitude tapes
            result = self.test_airspeed_altitude_tapes()
            self.test_results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"{status} {result.test_name}")
            
            # Test 2: Flight mode display
            result = self.test_flight_mode_display()
            self.test_results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"{status} {result.test_name}")
            
            # Test 3: Armed status display
            result = self.test_armed_status_display()
            self.test_results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"{status} {result.test_name}")
            
            # Test 4: Battery telemetry
            result = self.test_battery_telemetry()
            self.test_results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            logger.info(f"{status} {result.test_name}")
            
            # Test 5: GPS position display
            result = self.test_gps_position_display()
            self.test_results.append(result)
            status = "✅ PASSED" if result.passed else "❌ FAILED" 
            logger.info(f"{status} {result.test_name}")
            
        finally:
            # Disconnect
            if self.sio and self.connected:
                self.sio.disconnect()
                
        return self.test_results
        
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        passed_tests = [r for r in self.test_results if r.passed]
        failed_tests = [r for r in self.test_results if not r.passed]
        
        report = f"""
=== PRIMARY FLIGHT DISPLAY (PFD) TELEMETRY TESTING REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
• Total Tests: {len(self.test_results)}
• Passed: {len(passed_tests)}
• Failed: {len(failed_tests)}
• Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%

TELEMETRY STATISTICS:
• Total Updates Collected: {self.update_count}
• Data Samples in History: {len(self.telemetry_history)}

TEST RESULTS:
"""
        
        for result in self.test_results:
            status_icon = "✅" if result.passed else "❌"
            duration_str = f" ({result.duration:.2f}s)" if result.duration else ""
            report += f"\n{status_icon} {result.test_name}{duration_str}\n"
            report += f"   {result.details}\n"
            
        if failed_tests:
            report += f"\nFAILED TESTS SUMMARY:\n"
            for result in failed_tests:
                report += f"❌ {result.test_name}: {result.details.split('.')[0]}\n"
                
        report += f"\n=== END REPORT ===\n"
        return report

def main():
    """Main test execution"""
    print("Primary Flight Display (PFD) Telemetry Display Testing Agent")
    print("============================================================")
    print("Testing virtual drone at 192.168.193.235:5678")
    print("WebGCS server at localhost:5001")
    print()
    
    tester = PFDTelemetryTester()
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        # Generate and display report
        report = tester.generate_report()
        print(report)
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"/Users/peterburke/Documents/Code/WebGCS5/PFD_TELEMETRY_TEST_REPORT_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(f"Report saved to: {report_file}")
        
        # Exit with appropriate code
        failed_count = len([r for r in results if not r.passed])
        return 0 if failed_count == 0 else 1
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
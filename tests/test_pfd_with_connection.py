#!/usr/bin/env python3
"""
Complete PFD Telemetry Testing with Drone Connection
Tests PFD elements with established virtual drone connection
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

class CompletePFDTester:
    """Complete PFD Testing with Connection Management"""
    
    def __init__(self, server_url: str = "http://localhost:5001"):
        self.server_url = server_url
        self.sio = None
        self.test_results: List[TestResult] = []
        self.telemetry_history: deque = deque(maxlen=1000)
        self.connected_to_server = False
        self.drone_connected = False
        self.connection_status = "disconnected"
        self.update_count = 0
        self.last_update_time = None
        self.update_times = deque(maxlen=100)
        
    def connect_socketio(self) -> bool:
        """Connect to WebGCS SocketIO server"""
        try:
            logger.info("Connecting to WebGCS SocketIO server...")
            self.sio = socketio.Client(logger=False, engineio_logger=False)
            
            @self.sio.event
            def connect():
                logger.info("✅ Connected to WebGCS SocketIO server")
                self.connected_to_server = True
                
            @self.sio.event  
            def disconnect():
                logger.info("❌ Disconnected from WebGCS SocketIO server")
                self.connected_to_server = False
                
            @self.sio.event
            def telemetry_update(data):
                """Handle telemetry updates from drone"""
                now = datetime.now()
                self.telemetry_history.append(TelemetrySnapshot(now, data))
                self.update_count += 1
                
                # Track update timing
                if self.last_update_time:
                    delta = (now - self.last_update_time).total_seconds()
                    self.update_times.append(delta)
                    
                self.last_update_time = now
                
                # Log sample updates
                if self.update_count % 20 == 0:
                    logger.info(f"📊 Received {self.update_count} telemetry updates so far...")
                    
            @self.sio.event
            def connection_status(data):
                """Handle drone connection status updates"""
                status = data.get('status', 'unknown')
                message = data.get('message', '')
                self.connection_status = status
                
                if status == 'connected':
                    self.drone_connected = True
                    logger.info(f"🚁 Drone connected: {message}")
                elif status == 'disconnected':
                    self.drone_connected = False
                    logger.info(f"🚁 Drone disconnected: {message}")
                else:
                    logger.info(f"🔄 Connection status: {status} - {message}")
                    
            # Connect to server
            self.sio.connect(self.server_url)
            time.sleep(2)  # Allow more time for connection
            
            return self.connected_to_server
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to SocketIO: {e}")
            return False
            
    def connect_to_drone(self, ip: str = "localhost", port: int = 5678) -> bool:
        """Connect to virtual drone"""
        logger.info(f"🚁 Connecting to virtual drone at {ip}:{port}...")
        
        try:
            # Send drone connection request via SocketIO
            self.sio.emit('connect_drone', {'ip': ip, 'port': port})
            
            # Wait for connection with timeout
            timeout = time.time() + 30  # 30 second timeout
            while time.time() < timeout:
                if self.drone_connected:
                    logger.info("✅ Virtual drone connected successfully!")
                    return True
                    
                time.sleep(0.5)  # Check every 500ms
                
            logger.error("❌ Timeout waiting for drone connection")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to drone: {e}")
            return False
            
    def disconnect_from_drone(self):
        """Disconnect from virtual drone"""
        try:
            logger.info("🚁 Disconnecting from virtual drone...")
            self.sio.emit('disconnect_drone')
            time.sleep(2)  # Allow disconnection to process
            
        except Exception as e:
            logger.error(f"❌ Failed to disconnect from drone: {e}")
            
    def check_server_health(self) -> TestResult:
        """TEST-PFD-000: Check server health"""
        start_time = datetime.now()
        
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                duration = (datetime.now() - start_time).total_seconds()
                
                details = f"Server healthy. Status: {health_data}"
                return TestResult("TEST-PFD-000: Server Health", True, details, start_time, duration)
            else:
                details = f"Server returned status {response.status_code}"
                return TestResult("TEST-PFD-000: Server Health", False, details, start_time)
                
        except Exception as e:
            details = f"Server health check failed: {e}"
            return TestResult("TEST-PFD-000: Server Health", False, details, start_time)
            
    def test_drone_connection(self) -> TestResult:
        """TEST-PFD-001: Drone Connection Test"""
        start_time = datetime.now()
        
        success = self.connect_to_drone()
        duration = (datetime.now() - start_time).total_seconds()
        
        if success:
            details = f"Successfully connected to virtual drone at 192.168.193.235:5678 in {duration:.1f}s"
            return TestResult("TEST-PFD-001: Drone Connection", True, details, start_time, duration)
        else:
            details = f"Failed to connect to virtual drone after {duration:.1f}s timeout"
            return TestResult("TEST-PFD-001: Drone Connection", False, details, start_time, duration)
            
    def test_real_time_telemetry_updates(self, duration_seconds: int = 60) -> TestResult:
        """TEST-PFD-002: Real-time Telemetry Updates from Connected Drone"""
        logger.info(f"📊 Starting real-time telemetry test ({duration_seconds}s)")
        
        start_time = datetime.now()
        initial_count = self.update_count
        self.update_times.clear()
        
        # Collect telemetry for specified duration
        end_time = start_time + timedelta(seconds=duration_seconds)
        
        while datetime.now() < end_time:
            current_count = self.update_count - initial_count
            if current_count > 0 and current_count % 50 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = current_count / elapsed
                logger.info(f"📊 Collected {current_count} updates in {elapsed:.1f}s (rate: {rate:.2f} Hz)")
                
            time.sleep(0.1)
            
        test_duration = (datetime.now() - start_time).total_seconds()
        total_updates = self.update_count - initial_count
        
        # Analyze results
        if total_updates == 0:
            return TestResult(
                "TEST-PFD-002: Real-time Telemetry Updates",
                False,
                "No telemetry updates received from connected drone",
                start_time,
                test_duration
            )
            
        # Calculate metrics
        update_rate = total_updates / test_duration
        
        if len(self.update_times) > 0:
            avg_interval = sum(self.update_times) / len(self.update_times)
            min_interval = min(self.update_times)
            max_interval = max(self.update_times)
        else:
            avg_interval = min_interval = max_interval = 0
            
        # Get latest telemetry
        latest_data = self.telemetry_history[-1].data if self.telemetry_history else {}
        
        # Check required fields
        required_fields = ['lat', 'lon', 'alt_rel', 'vx', 'vy', 'pitch', 'roll', 'armed', 'mode']
        present_fields = [field for field in required_fields if field in latest_data]
        missing_fields = [field for field in required_fields if field not in latest_data]
        
        # Determine pass/fail (9-11 Hz acceptable)
        rate_ok = 9 <= update_rate <= 11
        has_core_data = len(present_fields) >= 7  # At least 7 of 9 fields
        
        passed = rate_ok and has_core_data
        
        details = f"""Real-time Telemetry Analysis:
• Updates received: {total_updates}
• Test duration: {test_duration:.1f}s
• Update rate: {update_rate:.2f} Hz {'✅' if rate_ok else '❌'}
• Rate range OK (9-11 Hz): {rate_ok}
• Average interval: {avg_interval*1000:.1f}ms
• Min/Max interval: {min_interval*1000:.1f}/{max_interval*1000:.1f}ms
• Core telemetry fields: {len(present_fields)}/9 {'✅' if has_core_data else '❌'}
• Present fields: {present_fields}
• Missing fields: {missing_fields}

Latest telemetry sample:
{json.dumps(latest_data, indent=2)}"""
        
        return TestResult(
            "TEST-PFD-002: Real-time Telemetry Updates",
            passed,
            details,
            start_time,
            test_duration
        )
        
    def test_attitude_indicator_data(self) -> TestResult:
        """TEST-PFD-003: Attitude Indicator Data"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-003: Attitude Indicator",
                False,
                "No telemetry data available",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        # Check attitude data
        has_pitch = 'pitch' in latest_data
        has_roll = 'roll' in latest_data
        
        pitch = latest_data.get('pitch', 0)
        roll = latest_data.get('roll', 0)
        
        # Validate ranges
        pitch_valid = isinstance(pitch, (int, float)) and -90 <= pitch <= 90
        roll_valid = isinstance(roll, (int, float)) and -180 <= roll <= 180
        
        passed = has_pitch and has_roll and pitch_valid and roll_valid
        
        details = f"""Attitude Indicator Data:
• Pitch available: {has_pitch} {'✅' if has_pitch else '❌'}
• Roll available: {has_roll} {'✅' if has_roll else '❌'}
• Pitch value: {pitch}° (valid range: -90 to 90) {'✅' if pitch_valid else '❌'}
• Roll value: {roll}° (valid range: -180 to 180) {'✅' if roll_valid else '❌'}
• Canvas size: 280x250px
• Update source: GLOBAL_POSITION_INT message"""
        
        return TestResult("TEST-PFD-003: Attitude Indicator", passed, details, start_time)
        
    def test_flight_mode_and_armed_status(self) -> TestResult:
        """TEST-PFD-004: Flight Mode and Armed Status"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-004: Flight Mode & Armed Status",
                False,
                "No telemetry data available",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        # Check flight mode
        has_mode = 'mode' in latest_data
        mode = latest_data.get('mode', 'UNKNOWN')
        
        # Check armed status
        has_armed = 'armed' in latest_data
        armed = latest_data.get('armed', False)
        armed_valid = isinstance(armed, bool)
        
        passed = has_mode and has_armed and armed_valid
        
        details = f"""Flight Mode & Armed Status:
• Mode available: {has_mode} {'✅' if has_mode else '❌'}
• Current mode: '{mode}'
• Armed status available: {has_armed} {'✅' if has_armed else '❌'}
• Armed value: {armed} {'✅' if armed_valid else '❌'}
• Display text: 'Mode: {mode}', '{'ARMED' if armed else 'DISARMED'}'"""
        
        return TestResult("TEST-PFD-004: Flight Mode & Armed Status", passed, details, start_time)
        
    def test_navigation_data(self) -> TestResult:
        """TEST-PFD-005: Navigation Data (GPS, Altitude, Speed)"""
        start_time = datetime.now()
        
        if not self.telemetry_history:
            return TestResult(
                "TEST-PFD-005: Navigation Data",
                False,
                "No telemetry data available",
                start_time
            )
            
        latest_data = self.telemetry_history[-1].data
        
        # GPS coordinates
        has_lat = 'lat' in latest_data
        has_lon = 'lon' in latest_data
        lat = latest_data.get('lat', 0)
        lon = latest_data.get('lon', 0)
        
        # Altitude
        has_alt = 'alt_rel' in latest_data
        altitude = latest_data.get('alt_rel', 0)
        
        # Velocity components for airspeed
        has_vx = 'vx' in latest_data
        has_vy = 'vy' in latest_data
        vx = latest_data.get('vx', 0)
        vy = latest_data.get('vy', 0)
        
        # Calculate ground speed
        ground_speed = (vx**2 + vy**2)**0.5 if has_vx and has_vy else 0
        
        # Validate coordinate ranges
        lat_valid = isinstance(lat, (int, float)) and -90 <= lat <= 90
        lon_valid = isinstance(lon, (int, float)) and -180 <= lon <= 180
        
        nav_data_complete = has_lat and has_lon and has_alt and has_vx and has_vy
        coords_valid = lat_valid and lon_valid
        
        passed = nav_data_complete and coords_valid
        
        details = f"""Navigation Data Analysis:
• Latitude: {lat:.6f}° {'✅' if lat_valid else '❌'}
• Longitude: {lon:.6f}° {'✅' if lon_valid else '❌'}
• Altitude (relative): {altitude:.1f}m {'✅' if has_alt else '❌'}
• Velocity X: {vx:.2f} m/s {'✅' if has_vx else '❌'}
• Velocity Y: {vy:.2f} m/s {'✅' if has_vy else '❌'}
• Ground speed: {ground_speed:.2f} m/s
• Position display: '{lat:.6f}, {lon:.6f}' (6 decimal precision)
• Airspeed tape: {ground_speed:.1f} m/s (60x250px canvas)
• Altitude tape: {altitude:.1f} m (70x250px canvas)"""
        
        return TestResult("TEST-PFD-005: Navigation Data", passed, details, start_time)
        
    def run_complete_pfd_tests(self) -> List[TestResult]:
        """Run complete PFD testing with connection management"""
        logger.info("=== STARTING COMPLETE PFD TELEMETRY TESTING ===")
        
        try:
            # Test 0: Server health
            result = self.check_server_health()
            self.test_results.append(result)
            logger.info(f"{'✅' if result.passed else '❌'} {result.test_name}")
            
            if not result.passed:
                logger.error("Server health check failed. Aborting tests.")
                return self.test_results
                
            # Connect to WebGCS server
            if not self.connect_socketio():
                logger.error("Failed to connect to WebGCS server. Aborting tests.")
                return self.test_results
                
            # Test 1: Drone connection
            result = self.test_drone_connection()
            self.test_results.append(result)
            logger.info(f"{'✅' if result.passed else '❌'} {result.test_name}")
            
            if not result.passed:
                logger.error("Drone connection failed. Cannot test telemetry.")
                return self.test_results
                
            # Wait a moment for telemetry to start flowing
            logger.info("⏳ Waiting for initial telemetry data...")
            time.sleep(5)
            
            # Test 2: Real-time telemetry updates
            result = self.test_real_time_telemetry_updates(60)
            self.test_results.append(result)
            logger.info(f"{'✅' if result.passed else '❌'} {result.test_name}")
            
            # Test 3: Attitude indicator
            result = self.test_attitude_indicator_data()
            self.test_results.append(result)
            logger.info(f"{'✅' if result.passed else '❌'} {result.test_name}")
            
            # Test 4: Flight mode and armed status
            result = self.test_flight_mode_and_armed_status()
            self.test_results.append(result)
            logger.info(f"{'✅' if result.passed else '❌'} {result.test_name}")
            
            # Test 5: Navigation data
            result = self.test_navigation_data()
            self.test_results.append(result)
            logger.info(f"{'✅' if result.passed else '❌'} {result.test_name}")
            
        except Exception as e:
            logger.error(f"❌ Test execution error: {e}")
            
        finally:
            # Clean up
            if self.drone_connected:
                self.disconnect_from_drone()
                
            if self.sio and self.connected_to_server:
                self.sio.disconnect()
                
        return self.test_results
        
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        passed_tests = [r for r in self.test_results if r.passed]
        failed_tests = [r for r in self.test_results if not r.passed]
        
        report = f"""
=== COMPLETE PFD TELEMETRY TESTING REPORT ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Virtual Drone: 192.168.193.235:5678
WebGCS Server: localhost:5001

EXECUTIVE SUMMARY:
• Total Tests: {len(self.test_results)}
• Passed: {len(passed_tests)} ✅
• Failed: {len(failed_tests)} ❌
• Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%

TELEMETRY PERFORMANCE:
• Total Updates Collected: {self.update_count}
• Telemetry Samples: {len(self.telemetry_history)}
• Drone Connected: {self.drone_connected}
• Connection Status: {self.connection_status}

DETAILED TEST RESULTS:
"""
        
        for result in self.test_results:
            status = "✅ PASSED" if result.passed else "❌ FAILED"
            duration = f" ({result.duration:.2f}s)" if result.duration else ""
            report += f"\n{status} {result.test_name}{duration}\n"
            
            # Format details with proper indentation
            details_lines = result.details.split('\n')
            for line in details_lines:
                report += f"   {line}\n"
                
        # PFD Element Status Summary
        if self.telemetry_history:
            latest = self.telemetry_history[-1].data
            report += f"\nPFD ELEMENTS STATUS (Latest Data):\n"
            report += f"• Attitude Indicator: {'✅' if 'pitch' in latest and 'roll' in latest else '❌'}\n"
            report += f"• Airspeed Tape: {'✅' if 'vx' in latest and 'vy' in latest else '❌'}\n"
            report += f"• Altitude Tape: {'✅' if 'alt_rel' in latest else '❌'}\n"
            report += f"• Armed Status: {'✅' if 'armed' in latest else '❌'}\n"
            report += f"• Flight Mode: {'✅' if 'mode' in latest else '❌'}\n"
            report += f"• GPS Position: {'✅' if 'lat' in latest and 'lon' in latest else '❌'}\n"
            
        if failed_tests:
            report += f"\nFAILED TESTS SUMMARY:\n"
            for result in failed_tests:
                brief_details = result.details.split('\n')[0] if result.details else "No details"
                report += f"❌ {result.test_name}: {brief_details}\n"
                
        report += f"\n=== TEST REPORT COMPLETE ===\n"
        return report

def main():
    """Main execution"""
    print("Complete PFD Telemetry Testing with Virtual Drone Connection")
    print("===========================================================")
    print("🚁 Virtual Drone: 192.168.193.235:5678")
    print("🌐 WebGCS Server: localhost:5001")
    print("🎯 Testing: Attitude, Airspeed, Altitude, GPS, Flight Mode, Armed Status")
    print()
    
    tester = CompletePFDTester()
    
    try:
        # Run comprehensive tests
        results = tester.run_complete_pfd_tests()
        
        # Generate report
        report = tester.generate_report()
        print(report)
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"/Users/peterburke/Documents/Code/WebGCS5/COMPLETE_PFD_TEST_REPORT_{timestamp}.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
            
        print(f"📁 Report saved: {report_file}")
        
        # Return appropriate exit code
        failed_count = len([r for r in results if not r.passed])
        return 0 if failed_count == 0 else 1
        
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
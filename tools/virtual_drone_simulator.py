#!/usr/bin/env python3
"""
Virtual Drone MAVLink Simulator for PFD Testing
Provides realistic telemetry data to test Primary Flight Display components
"""

import socket
import struct
import time
import threading
import math
from pymavlink import mavutil
from pymavlink.dialects.v20 import ardupilotmega as mavlink
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VirtualDroneSimulator:
    """Virtual drone providing MAVLink telemetry for PFD testing"""
    
    def __init__(self, host='0.0.0.0', port=5678):
        self.host = host
        self.port = port
        self.socket = None
        self.client_connections = []
        self.running = False
        
        # Drone state for simulation
        self.system_id = 1
        self.component_id = 1
        self.armed = False
        self.mode = mavlink.MAV_MODE_GUIDED_ARMED if self.armed else mavlink.MAV_MODE_GUIDED_DISARMED
        self.custom_mode = 4  # GUIDED mode
        
        # Position simulation (starts at some coordinates)
        self.lat = 37.7749  # San Francisco latitude
        self.lon = -122.4194  # San Francisco longitude
        self.alt_amsl = 100000  # 100 meters in millimeters
        self.alt_rel = 50000   # 50 meters relative altitude in millimeters
        
        # Motion simulation
        self.heading = 0.0  # Yaw in degrees
        self.pitch = 0.0    # Pitch in degrees
        self.roll = 0.0     # Roll in degrees
        self.vx = 0.0       # Velocity X (m/s)
        self.vy = 0.0       # Velocity Y (m/s)
        self.vz = 0.0       # Velocity Z (m/s)
        
        # Battery simulation
        self.battery_voltage = 12.6  # Volts
        self.current = 5.2          # Amps
        
        # GPS simulation
        self.gps_fix = 3  # 3D fix
        self.satellites_visible = 12
        self.hdop = 1.2
        
        # Animation parameters
        self.start_time = time.time()
        
    def create_mavlink_message(self, msg):
        """Convert pymavlink message to bytes"""
        try:
            # Create MAVLink instance
            mav = mavlink.MAVLink(None, srcSystem=self.system_id, srcComponent=self.component_id)
            
            # Pack message
            packed = msg.pack(mav)
            return packed
        except Exception as e:
            logger.error(f"Failed to pack MAVLink message: {e}")
            return None
            
    def create_heartbeat_message(self):
        """Create HEARTBEAT message"""
        msg = mavlink.MAVLink_heartbeat_message(
            type=mavlink.MAV_TYPE_QUADROTOR,
            autopilot=mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
            base_mode=self.mode,
            custom_mode=self.custom_mode,
            system_status=mavlink.MAV_STATE_ACTIVE,
            mavlink_version=3
        )
        return self.create_mavlink_message(msg)
        
    def create_global_position_int_message(self):
        """Create GLOBAL_POSITION_INT message with animated position"""
        # Animate position and attitude for realistic testing
        elapsed = time.time() - self.start_time
        
        # Gentle circular motion
        radius = 0.0001  # Small radius in degrees
        self.lat = 37.7749 + radius * math.sin(elapsed * 0.1)
        self.lon = -122.4194 + radius * math.cos(elapsed * 0.1)
        
        # Gentle altitude changes
        self.alt_rel = int(50000 + 10000 * math.sin(elapsed * 0.05))  # 40-60m altitude
        self.alt_amsl = self.alt_rel + 100000  # Add 100m ground level
        
        # Gentle attitude changes for attitude indicator testing
        self.pitch = 5.0 * math.sin(elapsed * 0.2)  # ±5 degrees pitch
        self.roll = 3.0 * math.cos(elapsed * 0.15)  # ±3 degrees roll
        self.heading = (elapsed * 10) % 360  # Slow rotation
        
        # Velocity simulation
        self.vx = 2.0 * math.cos(elapsed * 0.1)  # 0-2 m/s forward/back
        self.vy = 1.5 * math.sin(elapsed * 0.1)  # 0-1.5 m/s left/right
        self.vz = 0.5 * math.sin(elapsed * 0.05)  # Gentle climb/descent
        
        msg = mavlink.MAVLink_global_position_int_message(
            time_boot_ms=int(elapsed * 1000),
            lat=int(self.lat * 1e7),  # Convert to 1E7 format
            lon=int(self.lon * 1e7),  # Convert to 1E7 format
            alt=self.alt_amsl,        # Altitude AMSL in mm
            relative_alt=self.alt_rel, # Relative altitude in mm
            vx=int(self.vx * 100),    # Convert to cm/s
            vy=int(self.vy * 100),    # Convert to cm/s
            vz=int(self.vz * 100),    # Convert to cm/s
            hdg=int(self.heading * 100)  # Convert to centidegrees
        )
        return self.create_mavlink_message(msg)
        
    def create_attitude_message(self):
        """Create ATTITUDE message"""
        elapsed = time.time() - self.start_time
        
        msg = mavlink.MAVLink_attitude_message(
            time_boot_ms=int(elapsed * 1000),
            roll=math.radians(self.roll),
            pitch=math.radians(self.pitch), 
            yaw=math.radians(self.heading),
            rollspeed=0.1,
            pitchspeed=0.1,
            yawspeed=0.1
        )
        return self.create_mavlink_message(msg)
        
    def create_sys_status_message(self):
        """Create SYS_STATUS message for battery info"""
        msg = mavlink.MAVLink_sys_status_message(
            onboard_control_sensors_present=0,
            onboard_control_sensors_enabled=0,
            onboard_control_sensors_health=0,
            load=500,  # 50% load
            voltage_battery=int(self.battery_voltage * 1000),  # mV
            current_battery=int(self.current * 100),  # cA (centi-amperes)
            battery_remaining=85,  # 85% remaining
            drop_rate_comm=0,
            errors_comm=0,
            errors_count1=0,
            errors_count2=0,
            errors_count3=0,
            errors_count4=0
        )
        return self.create_mavlink_message(msg)
        
    def create_gps_raw_int_message(self):
        """Create GPS_RAW_INT message"""
        elapsed = time.time() - self.start_time
        
        msg = mavlink.MAVLink_gps_raw_int_message(
            time_usec=int(elapsed * 1e6),
            fix_type=self.gps_fix,
            lat=int(self.lat * 1e7),
            lon=int(self.lon * 1e7),
            alt=self.alt_amsl,
            eph=int(self.hdop * 100),  # HDOP in cm
            epv=int(self.hdop * 100),  # VDOP in cm
            vel=int(math.sqrt(self.vx**2 + self.vy**2) * 100),  # Ground speed in cm/s
            cog=int(self.heading * 100),  # Course over ground in centidegrees
            satellites_visible=self.satellites_visible
        )
        return self.create_mavlink_message(msg)
        
    def start_server(self):
        """Start the virtual drone server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            logger.info(f"🚁 Virtual drone simulator started on {self.host}:{self.port}")
            logger.info("Providing telemetry: HEARTBEAT, GLOBAL_POSITION_INT, ATTITUDE, SYS_STATUS, GPS_RAW_INT")
            
            while self.running:
                try:
                    client_socket, addr = self.socket.accept()
                    logger.info(f"✅ Client connected from {addr}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, addr),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
        finally:
            self.cleanup()
            
    def handle_client(self, client_socket, addr):
        """Handle individual client connections"""
        try:
            self.client_connections.append(client_socket)
            
            # Send messages at ~10Hz for realistic telemetry rate
            message_interval = 0.1  # 100ms = 10Hz
            last_message_time = 0
            
            while self.running:
                current_time = time.time()
                
                if current_time - last_message_time >= message_interval:
                    try:
                        # Send heartbeat every message
                        heartbeat = self.create_heartbeat_message()
                        if heartbeat:
                            client_socket.send(heartbeat)
                            
                        # Send position data
                        position = self.create_global_position_int_message()
                        if position:
                            client_socket.send(position)
                            
                        # Send attitude data
                        attitude = self.create_attitude_message() 
                        if attitude:
                            client_socket.send(attitude)
                            
                        # Send battery status (less frequently)
                        if int(current_time * 10) % 10 == 0:  # Every second
                            sys_status = self.create_sys_status_message()
                            if sys_status:
                                client_socket.send(sys_status)
                                
                        # Send GPS data (less frequently)
                        if int(current_time * 10) % 20 == 0:  # Every 2 seconds
                            gps_raw = self.create_gps_raw_int_message()
                            if gps_raw:
                                client_socket.send(gps_raw)
                        
                        last_message_time = current_time
                        
                    except socket.error:
                        logger.info(f"Client {addr} disconnected")
                        break
                        
                time.sleep(0.01)  # Small sleep to prevent busy waiting
                
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
        finally:
            if client_socket in self.client_connections:
                self.client_connections.remove(client_socket)
            try:
                client_socket.close()
            except:
                pass
                
    def stop_server(self):
        """Stop the virtual drone server"""
        logger.info("🛑 Stopping virtual drone simulator...")
        self.running = False
        
        # Close client connections
        for client in self.client_connections[:]:
            try:
                client.close()
            except:
                pass
                
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
                
    def cleanup(self):
        """Clean up resources"""
        self.stop_server()
        
    def arm_drone(self):
        """Simulate arming the drone"""
        self.armed = True
        self.mode = mavlink.MAV_MODE_GUIDED_ARMED
        logger.info("🔓 Virtual drone ARMED")
        
    def disarm_drone(self):
        """Simulate disarming the drone"""
        self.armed = False
        self.mode = mavlink.MAV_MODE_GUIDED_DISARMED
        logger.info("🔒 Virtual drone DISARMED")

def main():
    """Main function to run virtual drone simulator"""
    print("🚁 Virtual Drone MAVLink Simulator for PFD Testing")
    print("==================================================")
    print("Provides realistic telemetry data for:")
    print("• Attitude Indicator (pitch/roll)")
    print("• Airspeed Tape (velocity)")
    print("• Altitude Tape (relative altitude)")
    print("• GPS Position (lat/lon with 6 decimals)")
    print("• Flight Mode & Armed Status")
    print("• Battery Voltage & Current")
    print()
    
    simulator = VirtualDroneSimulator()
    
    try:
        simulator.start_server()
    except KeyboardInterrupt:
        print("\n⛔ Shutting down virtual drone simulator...")
        simulator.stop_server()
    except Exception as e:
        print(f"❌ Simulator error: {e}")
    
    print("✅ Virtual drone simulator stopped")

if __name__ == "__main__":
    main()
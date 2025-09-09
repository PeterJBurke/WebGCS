"""
Virtual Drone Simulator for WebGCS Testing
Creates a MAVLink endpoint at 192.168.193.235:5678 for testing

File size: Must stay under 200 lines per WebGCS PRD
"""
import socket
import time
import threading
import struct
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink_common
from src.utils.token_tracker import record_agent_usage


class VirtualDrone:
    """Simple virtual drone that responds to MAVLink messages."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5678):
        """Initialize virtual drone."""
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.clients = []
        self.thread = None
        
        # Drone state
        self.system_id = 1
        self.component_id = 1
        self.armed = False
        self.lat = -35.3632607  # Canberra coordinates
        self.lon = 149.1652374
        self.alt = 584.0
        self.heading = 0
        self.groundspeed = 0
        
        record_agent_usage('virtual-drone-communication-agent', 40, 25)
    
    def start(self):
        """Start virtual drone server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            
            self.running = True
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()
            
            print(f"Virtual drone started on {self.host}:{self.port}")
            record_agent_usage('virtual-drone-communication-agent', 30, 20)
            return True
            
        except Exception as e:
            print(f"Failed to start virtual drone: {e}")
            return False
    
    def stop(self):
        """Stop virtual drone server."""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join(timeout=2)
        
        record_agent_usage('virtual-drone-communication-agent', 20, 15)
        print("Virtual drone stopped")
    
    def _server_loop(self):
        """Main server loop to handle client connections."""
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                print(f"Client connected from {address}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"Server loop error: {e}")
    
    def _handle_client(self, client_socket, address):
        """Handle individual client connection."""
        try:
            # Send initial heartbeat
            heartbeat_thread = threading.Thread(
                target=self._send_heartbeats,
                args=(client_socket,),
                daemon=True
            )
            heartbeat_thread.start()
            
            # Listen for incoming messages
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Process incoming MAVLink messages
                    self._process_mavlink_data(data, client_socket)
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Client handling error: {e}")
                    break
                    
        except Exception as e:
            print(f"Client connection error: {e}")
        finally:
            client_socket.close()
            print(f"Client {address} disconnected")
    
    def _send_heartbeats(self, client_socket):
        """Send periodic heartbeat messages."""
        while self.running:
            try:
                # Create heartbeat message
                heartbeat = mavlink_common.MAVLink_heartbeat_message(
                    type=mavlink_common.MAV_TYPE_QUADROTOR,
                    autopilot=mavlink_common.MAV_AUTOPILOT_ARDUPILOTMEGA,
                    base_mode=mavlink_common.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                    custom_mode=0,
                    system_status=mavlink_common.MAV_STATE_STANDBY,
                    mavlink_version=3
                )
                
                # Create MAVLink instance for packing
                mav = mavlink_common.MAVLink(None, self.system_id, self.component_id)
                
                # Pack message with proper headers
                msg_buf = heartbeat.pack(mav)
                
                # Send the raw bytes
                client_socket.send(msg_buf)
                print(f"Heartbeat sent: {len(msg_buf)} bytes")
                
                time.sleep(1)  # Send heartbeat every 1 second
                
            except Exception as e:
                print(f"Heartbeat error: {e}")
                break
    
    def _process_mavlink_data(self, data, client_socket):
        """Process incoming MAVLink data from client."""
        try:
            # Simple message processing - just acknowledge
            # In a full implementation, this would parse and respond to commands
            record_agent_usage('virtual-drone-communication-agent', 25, 15)
            
        except Exception as e:
            print(f"Message processing error: {e}")


# Global virtual drone instance
_virtual_drone = None


def start_virtual_drone(host: str = "127.0.0.1", port: int = 5678) -> bool:
    """Start the virtual drone simulator."""
    global _virtual_drone
    
    if _virtual_drone is None:
        _virtual_drone = VirtualDrone(host, port)
    
    return _virtual_drone.start()


def stop_virtual_drone():
    """Stop the virtual drone simulator."""
    global _virtual_drone
    
    if _virtual_drone:
        _virtual_drone.stop()


if __name__ == "__main__":
    # Run virtual drone directly
    drone = VirtualDrone()
    try:
        if drone.start():
            print("Virtual drone running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping virtual drone...")
        drone.stop()
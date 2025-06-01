# WebGCS - Web-Based Ground Control Station

A modern web-based ground control interface for MAVLink-compatible drones and vehicles. Features real-time telemetry, map visualization, and comprehensive flight control capabilities.

[![Version](https://img.shields.io/badge/version-1.4-blue.svg)](https://github.com/PeterJBurke/WebGCS/releases/tag/v1.4)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

- **Real-time Flight Control**: Arm/disarm, takeoff, landing, and mode changes
- **Interactive Map Navigation**: Point-and-click "Go To" functionality with visual markers
- **Live Telemetry Display**: Attitude indicator, GPS position, and flight status
- **Mission Planning**: Visualize and manage waypoints and geofences
- **Command Feedback**: Detailed acknowledgment and error reporting
- **Responsive Design**: Works on desktop and mobile devices
- **MAVLink Integration**: Direct TCP connection to autopilot systems

## 🚀 Quick Start

### Prerequisites

- Python 3.7+ 
- Git (for cloning)
- Network access to your drone/autopilot

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PeterJBurke/WebGCS.git
   cd WebGCS
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure connection** (optional)
   
   Create a `.env` file to customize settings:
   ```bash
   DRONE_TCP_ADDRESS=192.168.1.247
   DRONE_TCP_PORT=5678
   WEB_SERVER_PORT=5000
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the interface**
   
   Open your browser to: `http://localhost:5000`

## 🎮 Using the Interface

### Flight Controls
- **ARM/DISARM**: Safely enable/disable motors
- **TAKEOFF**: Automated takeoff to specified altitude  
- **LAND/RTL**: Landing or return-to-launch commands
- **MODE CHANGES**: Switch between flight modes (Guided, Loiter, etc.)

### Navigation
- **Go To**: Click on map or enter coordinates to command navigation
- **Real-time Tracking**: Live position updates with flight path history
- **Waypoint Visualization**: View mission plans and geofences

### Status Monitoring  
- **Connection Status**: Real-time link quality and heartbeat monitoring
- **Flight Status**: Armed state, GPS fix, EKF health
- **Command Feedback**: Detailed success/error messages for all operations

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DRONE_TCP_ADDRESS` | `192.168.1.247` | IP address of the drone |
| `DRONE_TCP_PORT` | `5678` | MAVLink TCP port |
| `WEB_SERVER_HOST` | `0.0.0.0` | Web server bind address |
| `WEB_SERVER_PORT` | `5000` | Web server port |
| `HEARTBEAT_TIMEOUT` | `15` | Heartbeat timeout (seconds) |

### Drone Setup Requirements

Your autopilot must be configured as a **MAVLink TCP Server**:
- Listen on port `5678` (or your configured port)
- Accept incoming TCP connections
- Be accessible on the network from your computer

## 🔧 Troubleshooting

### Connection Issues
- **No Heartbeat**: Verify drone IP address and MAVLink TCP server is running
- **Connection Refused**: Check network connectivity with `ping <drone_ip>`
- **Port Issues**: Ensure port `5678` is open and not blocked by firewalls

### Web Interface Issues  
- **Page Won't Load**: Verify `python app.py` is running without errors
- **Port Conflicts**: Change `WEB_SERVER_PORT` if port `5000` is in use

### Commands Not Working
- **Mode Restrictions**: Some commands require specific flight modes (e.g., GUIDED for navigation)
- **Safety Checks**: Ensure GPS lock and proper calibration before flight operations

## 🛠️ Development

### Project Structure
```
WebGCS/
├── app.py                          # Main Flask application
├── socketio_handlers.py            # WebSocket event handlers  
├── mavlink_connection_manager.py   # MAVLink communication
├── templates/                      # HTML templates
├── static/                         # CSS, JS, and assets
└── requirements.txt               # Python dependencies
```

### Key Components
- **Flask + SocketIO**: Real-time web communication
- **PyMAVLink**: MAVLink protocol implementation
- **Leaflet.js**: Interactive mapping
- **Bootstrap**: Responsive UI framework

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/PeterJBurke/WebGCS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/PeterJBurke/WebGCS/discussions)

---

**⚠️ Safety Notice**: This software is for educational and experimental use. Always follow local regulations and safety guidelines when operating drones or unmanned vehicles.

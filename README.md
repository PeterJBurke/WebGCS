# WebGCS - Web-Based Ground Control Station

A modern web-based ground control interface for MAVLink-compatible drones and vehicles. Features real-time telemetry, map visualization, offline mapping capabilities, and comprehensive flight control capabilities.

[![Version](https://img.shields.io/badge/version-1.8-blue.svg)](https://github.com/PeterJBurke/WebGCS/releases/tag/v1.8)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

- **Real-time Flight Control**: Arm/disarm, takeoff, landing, and mode changes
- **Interactive Map Navigation**: Point-and-click "Go To" functionality with visual markers
- **🗺️ Offline Maps**: Download and cache map tiles for use without internet connectivity
- **Live Telemetry Display**: Attitude indicator, GPS position, and flight status
- **Mission Planning**: Visualize and manage waypoints and geofences
- **Command Feedback**: Detailed acknowledgment and error reporting
- **Responsive Design**: Works on desktop and mobile devices
- **MAVLink Integration**: Direct TCP connection to autopilot systems

## 🚀 Quick Start

Choose your platform for optimized installation:

### 🖥️ Ubuntu 24.04 LTS Desktop

**Fastest installation for Ubuntu desktop systems:**

```bash
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS
chmod +x setup_desktop.sh
./setup_desktop.sh --service  # Installs as system service
```

- ✅ **Optimized for Ubuntu 24.04 LTS** with Python 3.10+ 
- ✅ **Automatic dependency management** (build tools, libraries)
- ✅ **Systemd service with security hardening**
- ✅ **Frontend library downloads** (Bootstrap, Leaflet, Socket.IO)

📖 **[Complete Ubuntu Setup Guide →](UBUNTU_24_04_SETUP.md)**

### 🥧 Raspberry Pi OS (Bookworm)

**Complete ground station setup for Raspberry Pi:**

```bash
sudo apt-get install -y git
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS
chmod +x setup_raspberry_pi.sh
sudo ./setup_raspberry_pi.sh
sudo reboot  # Required for UART configuration
```

- ✅ **MAVLink Router integration** (UART ↔ TCP routing)
- ✅ **UART configuration** for flight controller connection
- ✅ **WiFi hotspot failover** (automatic backup hotspot)
- ✅ **Service dependency management** with automatic startup
- ✅ **Hardware connection setup** (GPIO UART pins)

📖 **[Complete Raspberry Pi Setup Guide →](RASPBERRY_PI_SETUP.md)**

### 💻 Manual Installation (Any Platform)

**For development or custom deployments:**

```bash
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py  # Access at http://localhost:5000
```

---

## 🏗️ Platform-Specific Features

### Ubuntu Desktop Features
- **System service integration** with systemd
- **Security hardening** with restricted permissions  
- **Automatic startup** on boot
- **Centralized logging** via journalctl
- **Package manager integration** for dependencies

### Raspberry Pi Features
- **MAVLink Router** for serial communication with flight controllers
- **UART configuration** (GPIO pins 8/10) with Bluetooth disabled
- **WiFi hotspot failover** - creates "RaspberryPiHotspot" if internet fails
- **Hardware integration** - optimized for Pi 3B+, 4B, and 5
- **Headless operation** - perfect for field deployments

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DRONE_TCP_ADDRESS` | `127.0.0.1` | IP address of MAVLink TCP server |
| `DRONE_TCP_PORT` | `5678` | MAVLink TCP port |
| `WEB_SERVER_HOST` | `0.0.0.0` | Web server bind address |
| `WEB_SERVER_PORT` | `5000` | Web server port |
| `HEARTBEAT_TIMEOUT` | `15` | Heartbeat timeout (seconds) |
| `REQUEST_STREAM_RATE_HZ` | `4` | MAVLink data stream rate |

### MAVLink Connection Setup

**For ArduPilot SITL:**
```bash
sim_vehicle.py --aircraft test --console --map --out tcpin:0.0.0.0:5678
```

**For Hardware Flight Controllers:**
- **Raspberry Pi**: Connected via UART (automatic with Pi setup)
- **Desktop**: Configure autopilot as TCP server on port 5678

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
- **🗺️ Offline Maps**: Pre-download map tiles for offline operation

### Status Monitoring  
- **Connection Status**: Real-time link quality and heartbeat monitoring
- **Flight Status**: Armed state, GPS fix, EKF health
- **Command Feedback**: Detailed success/error messages for all operations

## 🗺️ Offline Maps

WebGCS includes powerful offline mapping capabilities that allow you to download and cache map tiles for use in areas without internet connectivity. This is essential for field operations, remote locations, or when network reliability is a concern.

### 🌟 Key Features

- **🏠 Local Storage**: Map tiles stored in browser's IndexedDB for fast access
- **🌍 Dual Map Types**: Download both street maps (OpenStreetMap) and satellite imagery (Esri)
- **📡 Smart Fallback**: Automatically switches between cached and online tiles
- **📊 Progress Monitoring**: Real-time download progress with detailed statistics
- **💾 Storage Management**: View cache statistics and clear cached data when needed
- **🎯 Area Selection**: Define download areas by map view or manual coordinates

### 🚀 Quick Start Guide

#### 1. Access Offline Maps Panel
Click the **"📡 Offline Maps"** button in the top-right corner of the map interface.

#### 2. Define Download Area
**Option A - Current Map View:**
1. Navigate to your area of interest on the map
2. Click **"Use Current Map View"** to automatically set coordinates

**Option B - Manual Coordinates:**
1. Enter coordinates manually:
   - **North Lat**: Northern boundary latitude
   - **South Lat**: Southern boundary latitude  
   - **West Lng**: Western boundary longitude
   - **East Lng**: Eastern boundary longitude

#### 3. Configure Download Settings
- **Zoom Levels**: Select minimum and maximum zoom levels (2-20)
  - Lower zoom = wider area, less detail
  - Higher zoom = more detail, larger file size
- **Map Types**: Choose which maps to download:
  - ✅ **Street Map**: OpenStreetMap road and terrain data
  - ✅ **Satellite**: High-resolution aerial imagery

#### 4. Review and Download
1. **Estimate Preview**: Review estimated tile count and download size
2. **Start Download**: Click **"Download"** to begin caching tiles
3. **Monitor Progress**: Watch real-time progress with success/failure counts
4. **Stop if Needed**: Use **"Stop"** button to halt download at any time

### 📏 Planning Your Downloads

#### Zoom Level Guidelines

| Zoom Level | Use Case | Detail Level | Tiles per km² |
|------------|----------|--------------|---------------|
| 2-6 | Continental view | Country/state level | 1-64 |
| 7-10 | Regional planning | City/county level | 128-1K |
| 11-14 | Local operations | Neighborhood level | 2K-16K |
| 15-18 | Detailed navigation | Street/building level | 32K-262K |
| 19-20 | Precision work | Sub-meter detail | 524K+ |

#### Storage Estimates

- **Average tile size**: ~25KB (varies by content)
- **Small area (1km²)** at zoom 10-16: ~50-200MB
- **Medium area (25km²)** at zoom 8-14: ~100-500MB  
- **Large area (100km²)** at zoom 6-12: ~200MB-1GB

💡 **Tip**: Start with lower zoom levels (8-14) for larger areas, then download higher detail for specific zones.

### 🔧 Advanced Usage

#### Connection Status Indicator
The panel shows your current connection status:
- 🟢 **Online**: Can download new tiles
- 🔴 **Offline**: Using cached tiles only

#### Cache Management
- **View Statistics**: See how many tiles are cached for each map type
- **Clear Cache**: Remove all cached tiles to free up storage
- **Automatic Cleanup**: Browser manages storage automatically

#### Best Practices

1. **Pre-flight Planning**: Download maps while connected to WiFi
2. **Layered Approach**: Download large areas at low zoom, then specific zones at high zoom
3. **Regular Updates**: Periodically refresh cached tiles for updated imagery
4. **Storage Monitoring**: Check available browser storage before large downloads

### ⚠️ Important Considerations

#### Data Usage
- Downloads use your internet connection and may count against data limits
- Large areas with high zoom levels can result in significant data usage
- Plan downloads when connected to WiFi or unlimited connections

#### Storage Limits
- Browser storage typically limited to several GB per domain
- Large downloads may prompt browser storage permission requests
- Clear cache periodically to maintain performance

#### Tile Services
- **OpenStreetMap**: Free, community-driven maps with good coverage
- **Esri Satellite**: High-quality satellite imagery with global coverage
- Respect tile service usage policies and avoid excessive downloads

### 🐛 Troubleshooting

#### Download Issues
- **Slow Downloads**: Reduce concurrent downloads or check internet speed
- **Failed Tiles**: Some tiles may fail - download will continue with remaining tiles
- **Storage Full**: Clear cache or increase browser storage allocation

#### Offline Operation
- **Missing Tiles**: Download didn't complete or area not covered
- **Low Detail**: Increase maximum zoom level for more detailed tiles
- **Mixed Quality**: Normal - different zoom levels provide different detail

#### Browser Compatibility
- **IndexedDB Required**: Modern browsers (Chrome 24+, Firefox 29+, Safari 10+)
- **Storage Quota**: Varies by browser and system settings
- **Private Mode**: May have reduced storage capacity

### 📱 Mobile Considerations

When using WebGCS on mobile devices:
- **Smaller Downloads**: Mobile browsers have stricter storage limits
- **WiFi Recommended**: Avoid large downloads over cellular data
- **Battery Impact**: Large downloads may drain battery faster
- **Touch Interface**: Use pinch-to-zoom for area selection

---

## 🛠️ Service Management

### Ubuntu Desktop
```bash
# Service control
sudo systemctl status webgcs
sudo systemctl restart webgcs
sudo journalctl -u webgcs -f

# Configuration
nano .env
sudo systemctl restart webgcs
```

### Raspberry Pi
```bash
# Check all services
sudo systemctl status mavlink-router webgcs check_wifi

# View logs
sudo journalctl -u webgcs -f
sudo journalctl -u mavlink-router -f

# Hardware connection
ls -l /dev/serial0  # Should exist after reboot
```

## 🔧 Troubleshooting

### Connection Issues
- **No Heartbeat**: Verify MAVLink TCP server is running on correct IP/port
- **Connection Refused**: Check network connectivity and firewall settings
- **Raspberry Pi UART**: Ensure reboot after installation for UART activation

### Web Interface Issues  
- **Page Won't Load**: Check if service is running: `sudo systemctl status webgcs`
- **Port Conflicts**: Change `WEB_SERVER_PORT` in `.env` file
- **Permission Errors**: Verify user permissions and service configuration

### Offline Maps Issues
- **Maps Not Loading**: Check browser console for IndexedDB errors
- **Download Failures**: Verify internet connection and tile service availability
- **Storage Warnings**: Clear cache or use smaller download areas
- **Performance Issues**: Reduce concurrent downloads or clear browser cache
- **Missing Offline Panel**: Ensure JavaScript is enabled and `offline-maps.js` is loaded

### Platform-Specific Issues
- **Ubuntu**: Check Python 3.10+ requirement and system dependencies
- **Raspberry Pi**: Verify UART devices (`/dev/serial0`) and MAVLink Router status

📖 **Detailed troubleshooting guides available in platform-specific documentation**

## 🛠️ Development

### Project Structure
```
WebGCS/
├── app.py                          # Main Flask application
├── socketio_handlers.py            # WebSocket event handlers  
├── mavlink_connection_manager.py   # MAVLink communication
├── setup_desktop.sh               # Ubuntu/Linux setup script
├── setup_raspberry_pi.sh          # Raspberry Pi setup script
├── UBUNTU_24_04_SETUP.md          # Detailed Ubuntu guide
├── RASPBERRY_PI_SETUP.md          # Detailed Pi guide
├── templates/
│   └── index.html                  # Main web interface
├── static/
│   ├── lib/                        # External libraries (Leaflet, etc.)
│   ├── css/
│   │   ├── style.css              # Main application styles
│   │   └── offline-maps.css       # Offline maps UI styles
│   ├── offline-maps.js            # Offline maps functionality
│   └── ...                        # Other static assets
└── requirements.txt               # Python dependencies
```

### Key Components
- **Flask + SocketIO**: Real-time web communication
- **PyMAVLink**: MAVLink protocol implementation
- **Leaflet.js**: Interactive mapping with offline tile support
- **IndexedDB**: Client-side tile storage for offline maps
- **Bootstrap**: Responsive UI framework

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.10+ (Ubuntu), 3.11+ (Raspberry Pi OS Bookworm)
- **Memory**: 1GB RAM (2GB+ recommended)
- **Storage**: 2GB free space
- **Network**: WiFi or Ethernet connectivity

### Recommended Hardware
- **Ubuntu Desktop**: Any x64 machine with 4GB+ RAM
- **Raspberry Pi**: Pi 4B with 4GB+ RAM for best performance
- **Flight Controller**: ArduPilot/PX4 with MAVLink support

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
- **Ubuntu Setup**: [Ubuntu 24.04 Setup Guide](UBUNTU_24_04_SETUP.md)
- **Raspberry Pi Setup**: [Raspberry Pi Setup Guide](RASPBERRY_PI_SETUP.md)

---

**⚠️ Safety Notice**: This software is for educational and experimental use. Always follow local regulations and safety guidelines when operating drones or unmanned vehicles.

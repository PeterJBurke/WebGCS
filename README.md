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

## 🚀 Installation Options

WebGCS offers two installation methods to suit different use cases:

1. **[Manual Installation](#-manual-installation)** - Run the application manually when needed
2. **[Automated Service Installation (Linux Only)](#-automated-service-installation-linux-only)** - Install as a system service that runs automatically

---

## 📋 Manual Installation

Perfect for development, testing, or when you want full control over when the application runs.

### Prerequisites

- Python 3.7+ 
- Git (for cloning)
- Network access to your drone/autopilot

### Installation Steps

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
   cp .env.example .env
   nano .env  # Edit with your drone's IP and settings
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the interface**
   
   Open your browser to: `http://localhost:5000`

### Manual Operation

- **Start**: `source venv/bin/activate && python app.py`
- **Stop**: Press `Ctrl+C` in the terminal
- **Logs**: Displayed in the terminal where you ran the application

---

## 🐧 Automated Service Installation (Linux Only)

Ideal for production deployments, headless servers, or when you want WebGCS to start automatically on boot.

### Prerequisites

- Linux operating system (Ubuntu, Debian, CentOS, RHEL, Arch, etc.)
- Internet connection for downloading dependencies
- `sudo` access for installing the system service

### Installation Methods

#### Option A: Interactive Setup
```bash
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS
chmod +x setup_desktop.sh
./setup_desktop.sh
# Choose "y" when prompted to install as a service
```

#### Option B: Direct Service Installation
```bash
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS
chmod +x setup_desktop.sh
./setup_desktop.sh --service
```

### What the Service Installation Does

The automated setup script will:
- ✅ Check for Linux OS and Python 3.7+ compatibility
- ✅ Verify system dependencies (curl, git, python3-venv)
- ✅ Create a Python virtual environment
- ✅ Install all Python dependencies from requirements.txt
- ✅ Download required frontend libraries (Leaflet, Socket.IO, Bootstrap)
- ✅ Create a `.env.example` configuration template
- ✅ **Install WebGCS as a systemd service**
- ✅ **Enable auto-start on boot**
- ✅ **Start the service immediately**
- ✅ Verify the installation and service status

### Service Management

Once installed as a service, WebGCS runs automatically and can be managed with standard systemd commands:

#### Check Service Status
```bash
sudo systemctl status webgcs
```

#### View Live Logs
```bash
sudo journalctl -u webgcs -f
```

#### Restart the Service
```bash
sudo systemctl restart webgcs
```

#### Stop the Service
```bash
sudo systemctl stop webgcs
```

#### Start the Service
```bash
sudo systemctl start webgcs
```

#### Disable Auto-start on Boot
```bash
sudo systemctl disable webgcs
```

#### Enable Auto-start on Boot
```bash
sudo systemctl enable webgcs
```

### Service Configuration

#### Updating Configuration
1. Edit the configuration file:
   ```bash
   nano /path/to/WebGCS/.env
   ```

2. Restart the service to apply changes:
   ```bash
   sudo systemctl restart webgcs
   ```

#### Service Details
- **Service Name**: `webgcs`
- **Service File**: `/etc/systemd/system/webgcs.service`
- **User**: Runs under the user who installed it
- **Auto-restart**: Automatically restarts if the application crashes
- **Logs**: Available via `journalctl`

### Supported Linux Distributions

The setup script provides package installation commands for:
- **Ubuntu/Debian**: `apt install`
- **CentOS/RHEL**: `yum install`
- **Arch Linux**: `pacman -S`

### Service Benefits

- 🚀 **Automatic startup** on system boot
- 🔄 **Auto-restart** if the application crashes
- 📋 **Centralized logging** via systemd journal
- 🔒 **Security hardening** with systemd security features
- 🎛️ **Easy management** with standard systemd commands
- 🌐 **Always available** - no need to manually start

---

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

## 🐧 Linux Quick Setup (Automated)

For Linux users, we provide an automated setup script that handles all dependencies and configuration:

### Prerequisites for Linux Setup

- Linux operating system (Ubuntu, Debian, CentOS, RHEL, Arch, etc.)
- Internet connection for downloading dependencies
- `sudo` access for installing system packages (if needed)

### Using the Setup Script

1. **Clone the repository**
   ```bash
   git clone https://github.com/PeterJBurke/WebGCS.git
   cd WebGCS
   ```

2. **Run the automated setup script**
   ```bash
   chmod +x setup_desktop.sh
   ./setup_desktop.sh
   ```

The setup script will automatically:
- ✅ Check for Linux OS and Python 3.7+ compatibility
- ✅ Verify system dependencies (curl, git, python3-venv)
- ✅ Create a Python virtual environment
- ✅ Install all Python dependencies from requirements.txt
- ✅ Download required frontend libraries (Leaflet, Socket.IO, Bootstrap)
- ✅ Set proper file permissions
- ✅ Create a `.env.example` configuration template
- ✅ Verify the installation

3. **Follow the post-setup instructions**
   
   After the script completes, follow the displayed instructions:
   ```bash
   # Activate the virtual environment
   source venv/bin/activate
   
   # (Optional) Configure your settings
   cp .env.example .env
   nano .env  # Edit with your drone's IP and settings
   
   # Run the application
   python app.py
   ```

4. **Access the interface**
   
   Open your browser to: `http://localhost:5000`

### Linux Setup Script Features

- **OS Detection**: Only runs on Linux systems, provides manual instructions for other OS
- **Dependency Checking**: Automatically detects missing system packages and provides installation commands
- **Python Version Validation**: Ensures Python 3.7+ is available
- **Smart Environment Handling**: Prompts before overwriting existing virtual environments
- **Colorized Output**: Clear, colored progress indicators and error messages
- **Error Handling**: Robust error detection with helpful troubleshooting information
- **Verification**: Tests the installation before completion

### Supported Linux Distributions

The setup script provides package installation commands for:
- **Ubuntu/Debian**: `apt install`
- **CentOS/RHEL**: `yum install`
- **Arch Linux**: `pacman -S`

> **Note**: The automated setup script is specifically designed for Linux systems. For macOS or Windows, please use the manual installation method above.

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

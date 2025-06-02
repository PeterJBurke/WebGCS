# Ubuntu 24.04 LTS Setup Guide for WebGCS

This guide provides detailed instructions for setting up WebGCS on Ubuntu 24.04 LTS. The setup script has been optimized specifically for Ubuntu 24.04 and includes all necessary dependencies and configurations.

## System Requirements

- **Operating System**: Ubuntu 24.04 LTS (recommended), Ubuntu 22.04, or Ubuntu 20.04
- **Python**: 3.10+ (Ubuntu 24.04 includes Python 3.12 by default)
- **Memory**: Minimum 1GB RAM (2GB+ recommended)
- **Storage**: Minimum 2GB free space
- **Network**: Internet connection for initial setup
- **Privileges**: sudo access for system service installation

## Quick Start

### Automated Installation

The fastest way to get WebGCS running on Ubuntu 24.04:

```bash
# Clone the repository
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS

# Run the setup script
chmod +x setup_desktop.sh
./setup_desktop.sh

# For automatic service installation (runs WebGCS as a system service)
./setup_desktop.sh --service
```

### What the Script Does

The `setup_desktop.sh` script automatically:

1. **System Verification**
   - Checks Ubuntu version compatibility
   - Verifies Python 3.10+ availability
   - Updates package lists

2. **Dependency Installation**
   - Installs required system packages:
     - `python3`, `python3-venv`, `python3-pip`, `python3-dev`
     - `build-essential`, `pkg-config`, `libevent-dev`
     - `git`, `curl`
   - Downloads and installs Python packages via pip

3. **Environment Setup**
   - Creates Python virtual environment
   - Downloads frontend libraries (Bootstrap, Leaflet, Socket.IO)
   - Sets proper file permissions

4. **Configuration**
   - Creates `.env.example` template
   - Generates default `.env` configuration file
   - Configures for localhost TCP connection (127.0.0.1:5678)

5. **Service Installation** (optional)
   - Creates systemd service file with security settings
   - Enables and starts the WebGCS service
   - Configures automatic startup on boot

## Manual Installation

If you prefer to install manually or need to customize the process:

### 1. Install System Dependencies

```bash
# Update package lists
sudo apt update

# Install required packages
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    pkg-config \
    libevent-dev \
    git \
    curl
```

### 2. Clone and Setup WebGCS

```bash
# Clone the repository
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### 3. Download Frontend Libraries

```bash
# Create directories
mkdir -p static/lib

# Download required JavaScript libraries
curl -fsSL https://unpkg.com/leaflet@1.9.4/dist/leaflet.css -o static/lib/leaflet.css
curl -fsSL https://unpkg.com/leaflet@1.9.4/dist/leaflet.js -o static/lib/leaflet.js
curl -fsSL https://cdn.socket.io/4.7.4/socket.io.min.js -o static/lib/socket.io.min.js
curl -fsSL https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css -o static/lib/bootstrap.min.css
curl -fsSL https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js -o static/lib/bootstrap.bundle.min.js
```

### 4. Configuration

Create a `.env` file:

```bash
cat > .env << EOF
# WebGCS Configuration
DRONE_TCP_ADDRESS=127.0.0.1
DRONE_TCP_PORT=5678
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=5000
SECRET_KEY=your_secure_secret_key_here
HEARTBEAT_TIMEOUT=15
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=5
TELEMETRY_UPDATE_INTERVAL=0.1
EOF
```

## Running WebGCS

### Manual Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python app.py
```

Access WebGCS at: http://localhost:5000

### As a System Service

If you installed with the `--service` option:

```bash
# Check service status
sudo systemctl status webgcs

# View logs
sudo journalctl -u webgcs -f

# Restart service
sudo systemctl restart webgcs

# Stop service
sudo systemctl stop webgcs

# Start service
sudo systemctl start webgcs
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DRONE_TCP_ADDRESS` | `127.0.0.1` | IP address of MAVLink TCP server |
| `DRONE_TCP_PORT` | `5678` | TCP port for MAVLink connection |
| `WEB_SERVER_HOST` | `0.0.0.0` | Web server bind address |
| `WEB_SERVER_PORT` | `5000` | Web server port |
| `SECRET_KEY` | Generated | Flask session secret key |
| `HEARTBEAT_TIMEOUT` | `15` | Heartbeat timeout (seconds) |
| `REQUEST_STREAM_RATE_HZ` | `4` | MAVLink data stream rate |
| `COMMAND_ACK_TIMEOUT` | `5` | Command acknowledgment timeout |
| `TELEMETRY_UPDATE_INTERVAL` | `0.1` | UI update interval (seconds) |

### MAVLink Connection Setup

WebGCS connects to autopilots via TCP. Your flight controller or simulator must be configured as a MAVLink TCP server:

#### ArduPilot SITL (Software-in-the-Loop)
```bash
# Start ArduPilot SITL with TCP output
sim_vehicle.py --aircraft test --console --map --out tcpin:0.0.0.0:5678
```

#### Mission Planner TCP Server
1. Open Mission Planner
2. Go to `CONFIG/TUNING` → `Full Parameter List`
3. Set `SERIAL2_PROTOCOL` to `2` (MAVLink2)
4. Set `SERIAL2_BAUD` to `57600`
5. Connect via UDP/TCP → TCP → Listen on port 5678

#### QGroundControl
1. Go to Application Settings → Comm Links
2. Add new link: TCP
3. Host Address: 0.0.0.0, Port: 5678
4. Enable "Automatically Connect on Start"

## Troubleshooting

### Common Issues

#### Python Version Issues
Ubuntu 20.04 ships with Python 3.8. For WebGCS, you need Python 3.10+:
```bash
# Install Python 3.10 on Ubuntu 20.04
sudo apt install python3.10 python3.10-venv python3.10-dev
# Use python3.10 instead of python3 in commands
```

#### Permission Errors
```bash
# Fix permissions for the project directory
sudo chown -R $USER:$USER /path/to/WebGCS
chmod -R u+rwX /path/to/WebGCS
```

#### Port Already in Use
```bash
# Check what's using port 5000
sudo netstat -tulnp | grep :5000

# Change the port in .env file
echo "WEB_SERVER_PORT=5001" >> .env
```

#### GeEvent Compilation Issues
```bash
# Install additional development headers
sudo apt install libevent-dev python3-dev build-essential
```

### Connection Issues

#### No Heartbeat from Drone
1. Verify MAVLink TCP server is running on correct IP/port
2. Check firewall settings:
   ```bash
   # Allow incoming connections on port 5678
   sudo ufw allow 5678/tcp
   ```
3. Test connection with telnet:
   ```bash
   telnet 127.0.0.1 5678
   ```

#### Web Interface Not Loading
1. Check if WebGCS is running:
   ```bash
   ps aux | grep python | grep app.py
   ```
2. Check logs for errors:
   ```bash
   # For service installation
   sudo journalctl -u webgcs -f
   
   # For manual execution
   tail -f logs/app.log
   ```

### Verification Commands

Run these commands to verify your installation:

```bash
# Check Python version
python3 --version

# Test virtual environment
source venv/bin/activate
python -c "import flask, flask_socketio, pymavlink, gevent; print('All packages imported successfully')"
deactivate

# Check service status (if installed as service)
sudo systemctl status webgcs

# Test web server accessibility
curl -I http://localhost:5000
```

## Security Considerations

### Firewall Configuration

```bash
# Allow WebGCS web interface
sudo ufw allow 5000/tcp

# Allow MAVLink connections (if accepting external connections)
sudo ufw allow 5678/tcp

# Enable firewall
sudo ufw enable
```

### Service Security

The systemd service includes security hardening:
- `NoNewPrivileges=yes` - Prevents privilege escalation
- `PrivateTmp=yes` - Isolated temporary directory
- `ProtectSystem=strict` - Read-only system directories
- `ProtectHome=yes` - Restricted home directory access

## Performance Optimization

### For Low-End Systems
Adjust these settings in `.env`:
```bash
REQUEST_STREAM_RATE_HZ=2        # Reduce telemetry rate
TELEMETRY_UPDATE_INTERVAL=0.2   # Slower UI updates
```

### For High-Performance Systems
```bash
REQUEST_STREAM_RATE_HZ=10       # Higher telemetry rate
TELEMETRY_UPDATE_INTERVAL=0.05  # Faster UI updates
```

## Ubuntu Version Specific Notes

### Ubuntu 24.04 LTS (Recommended)
- Python 3.12 available by default
- All dependencies available in repositories
- Best performance and compatibility

### Ubuntu 22.04 LTS
- Python 3.10 available by default
- Full compatibility with WebGCS
- Stable long-term support

### Ubuntu 20.04 LTS
- Requires Python 3.10 installation
- Some packages may need manual compilation
- Consider upgrading to newer Ubuntu version

## Getting Help

If you encounter issues:

1. Check the logs:
   ```bash
   # Service logs
   sudo journalctl -u webgcs -f
   
   # Application logs
   tail -f logs/app.log
   ```

2. Run the verification script:
   ```bash
   python verify_setup.py
   ```

3. Check GitHub issues: https://github.com/PeterJBurke/WebGCS/issues

4. Verify your MAVLink connection:
   ```bash
   python test_mavlink_connection.py
   ```

## Next Steps

After successful installation:

1. **Configure your autopilot** to output MAVLink on TCP port 5678
2. **Access the web interface** at http://localhost:5000
3. **Test the connection** using the built-in diagnostics
4. **Customize settings** in the `.env` file as needed

The setup is now complete and WebGCS should be ready for use! 
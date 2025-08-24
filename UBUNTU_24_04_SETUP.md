# WebGCS Ubuntu 24.04 LTS Setup Guide

This guide provides step-by-step instructions for setting up WebGCS on Ubuntu 24.04 LTS.

## Quick Start (Recommended)

For a fresh Ubuntu 24.04 instance, the setup script will automatically install all required dependencies:

```bash
# Clone the repository
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS

# Make the setup script executable
chmod +x setup_desktop.sh

# Run the setup script (it will install dependencies automatically)
./setup_desktop.sh
```

The script will:
1. Update package lists
2. Install all required system dependencies automatically
3. Create a Python virtual environment
4. Install Python packages
5. Download frontend libraries
6. Configure the application

## Pre-Installation (For Manual Setup)

If you prefer to install dependencies manually before running the setup script:

### 1. Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Required System Dependencies

```bash
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    pkg-config \
    libevent-dev \
    curl \
    git
```

### 3. Verify Python Version

WebGCS requires Python 3.10 or higher:

```bash
python3 --version
```

Ubuntu 24.04 comes with Python 3.12 by default, which is perfect.

## Installation Options

### Option 1: Manual Mode (Default)

Run the setup script without arguments for manual mode:

```bash
./setup_desktop.sh
```

This creates the environment and dependencies but doesn't install a system service.

### Option 2: System Service Mode

To install WebGCS as a systemd service that starts automatically:

```bash
./setup_desktop.sh --service
```

Or run the script and choose "Yes" when prompted about service installation.

## After Installation

### Manual Mode Usage

If you chose manual mode:

```bash
# Activate the virtual environment
source venv/bin/activate

# Run the application
python app.py

# Access the web interface
# Open http://localhost:5000 in your browser
```

### Service Mode Usage

If you installed as a service:

```bash
# Check service status
sudo systemctl status webgcs

# View logs
sudo journalctl -u webgcs -f

# Restart service
sudo systemctl restart webgcs

# Access the web interface
# Open http://localhost:5000 in your browser
```

## Configuration

Edit the `.env` file to configure your drone connection:

```bash
nano .env
```

Key settings:
- `DRONE_TCP_ADDRESS`: IP address of your drone/autopilot
- `DRONE_TCP_PORT`: Port for MAVLink TCP connection (default: 5678)
- `WEB_SERVER_PORT`: Port for the web interface (default: 5000)

## Troubleshooting

### Common Issues on Fresh Ubuntu 24.04

#### 1. Missing Dependencies Error

**Error:**
```
[ERROR] Missing required dependencies: build-essential pkg-config libevent-dev
```

**Solution:**
The updated setup script (v2.1) automatically installs missing dependencies. If you encounter this error with an older script, manually install:

```bash
sudo apt update
sudo apt install -y build-essential pkg-config libevent-dev python3-dev
```

#### 2. gevent-websocket Installation Failed

**Error:**
```
❌ VERIFICATION FAILED
Errors that must be fixed:
  • Missing Python package: gevent-websocket
```

**Solution:**
The updated setup script handles this automatically. For manual fix:

```bash
source venv/bin/activate
pip install --upgrade pip
pip install gevent==23.9.1
pip install gevent-websocket==0.10.1
```

#### 3. Service Installation Failed

**Error:**
```
[ERROR] Cannot write to /etc/systemd/system without sudo privileges
[ERROR] Service installation failed. Falling back to manual mode.
```

**Solution:**
This is expected behavior when the script cannot create system services. The installation continues in manual mode. To use service mode, ensure you have sudo privileges and run:

```bash
./setup_desktop.sh --service
```

#### 4. Service Not Found

**Error:**
```
Unit webgcs.service could not be found.
```

**Solution:**
This occurs when the service wasn't created successfully. Try:

1. Re-run the setup script with service mode:
   ```bash
   ./setup_desktop.sh --service
   ```

2. Or manually create the service after successful setup:
   ```bash
   sudo systemctl enable /path/to/WebGCS/webgcs.service
   sudo systemctl start webgcs
   ```

#### 5. Color Formatting Issues in Terminal

If you see escape sequences like `\033[0;32m` instead of colors, your terminal doesn't support ANSI colors or the output was redirected. This doesn't affect functionality.

### Verification Steps

Run the verification script to check your installation:

```bash
source venv/bin/activate
python verify_setup.py
```

This will check all dependencies and report any missing components.

### Manual Installation (Alternative)

If the automated setup fails, you can install manually:

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip wheel setuptools
   pip install -r requirements.txt
   ```

3. **Download frontend libraries:**
   ```bash
   mkdir -p static/lib
   cd static/lib
   
   # Download required libraries
   curl -o leaflet.css https://unpkg.com/leaflet@1.9.4/dist/leaflet.css
   curl -o leaflet.js https://unpkg.com/leaflet@1.9.4/dist/leaflet.js
   curl -o socket.io.min.js https://cdn.socket.io/4.7.4/socket.io.min.js
   curl -o bootstrap.min.css https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
   curl -o bootstrap.bundle.min.js https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js
   
   cd ../..
   ```

4. **Create configuration:**
   ```bash
   cp .env.example .env
   nano .env  # Edit as needed
   ```

## Security Considerations

### Firewall Configuration

If you're running on a server accessible from the internet, configure your firewall:

```bash
# Allow only local access (recommended for testing)
sudo ufw deny 5000

# Or allow specific IP ranges
sudo ufw allow from 192.168.1.0/24 to any port 5000

# For public access (use with caution)
sudo ufw allow 5000
```

### Service Security

The systemd service includes security hardening features:
- Runs as a non-privileged user
- Restricted file system access
- Network isolation where possible

## Performance Optimization

### For High-Frequency Telemetry

Edit `.env` to optimize for your use case:

```bash
# For high-frequency updates (faster, more CPU usage)
TELEMETRY_UPDATE_INTERVAL=0.05
REQUEST_STREAM_RATE_HZ=10

# For lower frequency (slower, less CPU usage)
TELEMETRY_UPDATE_INTERVAL=0.2
REQUEST_STREAM_RATE_HZ=2
```

### System Resources

WebGCS is lightweight, but for optimal performance:
- Minimum: 1 GB RAM, 1 CPU core
- Recommended: 2 GB RAM, 2 CPU cores
- Storage: ~100 MB for application + logs

## Updating WebGCS

To update to a newer version:

```bash
# Stop the service if running
sudo systemctl stop webgcs

# Pull updates
git pull origin main

# Re-run setup to update dependencies
./setup_desktop.sh

# Restart service if using service mode
sudo systemctl start webgcs
```

## Support

For issues specific to Ubuntu 24.04:
1. Check this troubleshooting guide first
2. Run the verification script: `python verify_setup.py`
3. Check the logs: `tail -f logs/app.log` or `sudo journalctl -u webgcs -f`
4. Create an issue on GitHub with:
   - Ubuntu version: `lsb_release -a`
   - Python version: `python3 --version`
   - Error messages and logs

## Additional Resources

- [Main README](README.md) - General installation and usage
- [Raspberry Pi Setup](RASPBERRY_PI_SETUP.md) - For Raspberry Pi installations
- [GitHub Issues](https://github.com/PeterJBurke/WebGCS/issues) - Report bugs and get help 
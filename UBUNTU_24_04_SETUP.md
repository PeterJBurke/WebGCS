# WebGCS Ubuntu 24.04 Setup Guide

This document provides specific guidance for setting up WebGCS on Ubuntu 24.04 LTS.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 24.04 LTS (fresh installation supported)
- **Python**: 3.8+ (Ubuntu 24.04 comes with Python 3.12 by default)
- **Memory**: Minimum 1GB RAM (2GB+ recommended)
- **Storage**: 500MB free space for dependencies
- **Network**: Internet connection for downloading dependencies

### Required System Packages
The setup script will automatically check and prompt for installation of:

```bash
# Core dependencies
sudo apt install python3 python3-venv python3-pip python3-dev build-essential curl git -y
```

## 🚀 Quick Setup

### Option 1: Automated Service Installation (Recommended)
```bash
cd WebGCS
chmod +x setup_desktop.sh
./setup_desktop.sh --service
```

### Option 2: Manual Setup
```bash
cd WebGCS
chmod +x setup_desktop.sh
./setup_desktop.sh
```

## 🔧 Manual Installation Steps

If you prefer to install manually or encounter issues:

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Dependencies
```bash
sudo apt install python3 python3-venv python3-pip python3-dev build-essential curl git -y
```

### 3. Create Virtual Environment
```bash
cd WebGCS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Packages
```bash
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

### 5. Download Frontend Libraries
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

### 6. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your drone's IP and settings
```

### 7. Test Installation
```bash
python3 verify_setup.py  # Run verification script
python3 app.py          # Test manual start
```

## 🐧 Systemd Service Setup

### Create Service File
```bash
sudo nano /etc/systemd/system/webgcs.service
```

Add the following content (replace `/path/to/WebGCS` and `username`):

```ini
[Unit]
Description=WebGCS - Web-Based Ground Control Station
After=network.target
Wants=network.target

[Service]
Type=simple
User=username
Group=username
WorkingDirectory=/path/to/WebGCS
Environment=PATH=/path/to/WebGCS/venv/bin
ExecStart=/path/to/WebGCS/venv/bin/python /path/to/WebGCS/app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=webgcs

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/path/to/WebGCS
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable webgcs
sudo systemctl start webgcs
sudo systemctl status webgcs
```

## 🔧 Configuration

### Environment Variables (.env file)
```bash
# Drone Connection Settings
DRONE_TCP_ADDRESS=192.168.1.247
DRONE_TCP_PORT=5678

# Web Server Settings
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=5000
SECRET_KEY=your_secure_secret_key_here

# MAVLink Settings
HEARTBEAT_TIMEOUT=15
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=5
TELEMETRY_UPDATE_INTERVAL=0.1
```

### Firewall Configuration
```bash
# Allow WebGCS port
sudo ufw allow 5000/tcp

# Enable firewall if not already enabled
sudo ufw enable
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Python Version Issues
```bash
# Check Python version
python3 --version

# If version is less than 3.8, install newer Python
sudo apt install python3.11 python3.11-venv python3.11-dev
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

#### 2. Permission Errors
```bash
# Fix ownership of WebGCS directory
sudo chown -R $USER:$USER /path/to/WebGCS

# Make scripts executable
chmod +x setup_desktop.sh
chmod +x verify_setup.py
```

#### 3. Virtual Environment Issues
```bash
# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

#### 4. Service Not Starting
```bash
# Check service status
sudo systemctl status webgcs

# View service logs
sudo journalctl -u webgcs -f

# Check file permissions
ls -la /path/to/WebGCS/app.py

# Restart service
sudo systemctl restart webgcs
```

#### 5. Network Connection Issues
```bash
# Test network connectivity
ping google.com

# Check if port is open
sudo netstat -tulpn | grep :5000

# Test application directly
cd /path/to/WebGCS
source venv/bin/activate
python3 app.py
```

### Log Files
- Application logs: `./logs/` directory
- Service logs: `sudo journalctl -u webgcs`
- System logs: `/var/log/syslog`

## 📊 Service Management

### Service Commands
```bash
# Check status
sudo systemctl status webgcs

# Start service
sudo systemctl start webgcs

# Stop service
sudo systemctl stop webgcs

# Restart service
sudo systemctl restart webgcs

# Enable auto-start on boot
sudo systemctl enable webgcs

# Disable auto-start on boot
sudo systemctl disable webgcs

# View real-time logs
sudo journalctl -u webgcs -f
```

### Web Interface Access
- Local: http://localhost:5000
- Network: http://YOUR_SERVER_IP:5000

## 🔒 Security Considerations

### Network Security
- Change default SECRET_KEY in .env file
- Configure firewall to restrict access
- Use HTTPS in production (consider reverse proxy)

### File Permissions
```bash
# Secure the configuration file
chmod 600 .env

# Ensure proper ownership
sudo chown -R $USER:$USER /path/to/WebGCS
```

## 📋 Verification Checklist

Run the verification script to ensure everything is properly installed:

```bash
python3 verify_setup.py
```

The script checks:
- ✅ Python version compatibility
- ✅ Required Python packages
- ✅ Project files
- ✅ Template files
- ✅ Static library files
- ✅ Configuration files

## 🆘 Getting Help

If you encounter issues:

1. **Run the verification script**: `python3 verify_setup.py`
2. **Check service logs**: `sudo journalctl -u webgcs -f`
3. **Verify dependencies**: Re-run `./setup_desktop.sh`
4. **Check network connectivity**: Ensure drone is accessible
5. **Review configuration**: Verify .env file settings

## 📝 Notes for Ubuntu 24.04

### Key Improvements in Setup Script v1.5:
- ✅ **Updated Python requirement**: Now requires Python 3.8+ (was 3.7+)
- ✅ **Package list update**: Automatically runs `apt update` before dependency checks
- ✅ **Enhanced dependency checking**: Includes python3-dev and build-essential
- ✅ **Better error messages**: Distribution-specific installation commands
- ✅ **Improved pip installation**: Upgrades wheel and setuptools along with pip
- ✅ **Comprehensive verification**: Integrated verification script
- ✅ **Security hardening**: Enhanced systemd service security settings

### Ubuntu 24.04 Specific Features:
- Native support for Python 3.12
- Improved systemd service management
- Enhanced security policies
- Better package dependency resolution

This setup has been tested on fresh Ubuntu 24.04 LTS installations and should work reliably for WebGCS deployment. 
# Raspberry Pi OS Setup Guide for WebGCS

This guide provides detailed instructions for setting up WebGCS on Raspberry Pi OS (Bookworm). The setup includes MAVLink Router for serial communication, WiFi hotspot failover, and comprehensive service management.

## System Requirements

- **Hardware**: Raspberry Pi 3B+, 4B, or 5 (recommended: Pi 4B with 4GB+ RAM)
- **Operating System**: Raspberry Pi OS (Bookworm) - 64-bit recommended
- **Python**: 3.11+ (included with Raspberry Pi OS Bookworm)
- **Storage**: Minimum 8GB microSD card (16GB+ recommended)
- **Network**: WiFi capability for initial setup
- **Peripherals**: UART pins for flight controller connection

## Quick Start

### Automated Installation

The fastest way to get WebGCS running on Raspberry Pi:

```bash
# Clone the repository
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS

# Run the setup script (requires sudo)
chmod +x setup_raspberry_pi.sh
sudo ./setup_raspberry_pi.sh

# Reboot to activate UART configuration
sudo reboot
```

## What Gets Installed

The `setup_raspberry_pi.sh` script installs and configures:

### 1. **MAVLink Router**
- Routes MAVLink messages between flight controller (UART) and WebGCS (TCP)
- Handles serial communication at 57,600 baud
- Provides TCP server on localhost:5678
- Auto-starts as systemd service

### 2. **WebGCS Application**
- Web-based ground control station
- Connects to MAVLink Router via TCP
- Serves web interface on port 5000
- Auto-starts as systemd service

### 3. **WiFi Hotspot Failover**
- Automatically creates WiFi hotspot if internet connection fails
- Hotspot name: "RaspberryPiHotspot"
- Allows continued access to WebGCS without internet
- Monitors and restores WiFi connectivity

### 4. **UART Configuration**
- Configures GPIO UART pins for flight controller
- Disables Bluetooth to free up UART
- Sets up /dev/serial0 device
- Requires reboot to take effect

### 5. **System Services**
- `mavlink-router.service` - MAVLink message routing
- `webgcs.service` - WebGCS web application
- `check_wifi.service` - WiFi monitoring and hotspot failover

## Hardware Connections

### Flight Controller to Raspberry Pi

Connect your flight controller to the Raspberry Pi UART pins:

```
Flight Controller    Raspberry Pi GPIO
─────────────────    ─────────────────
TX (Telemetry Out)  → Pin 10 (GPIO 15, RX)
RX (Telemetry In)   ← Pin 8  (GPIO 14, TX)
GND                 → Pin 6  (Ground)
5V or 3.3V         → Pin 2  (5V) or Pin 1 (3.3V)
```

**Important**: 
- Ensure voltage compatibility between your flight controller and Pi
- Most modern flight controllers use 3.3V logic levels
- Pixhawk/ArduPilot boards typically use 3.3V on telemetry ports

### UART Configuration Details

The setup script configures:
- **UART0** enabled on GPIO 14/15
- **Bluetooth** disabled to free UART
- **Serial console** disabled on UART
- **Baud rate** set to 57,600 (configurable in MAVLink Router)

## Installation Process Details

### 1. Pre-Installation Cleanup
- Stops any existing services
- Removes old installations
- Cleans up previous configurations

### 2. System Updates
- Updates package lists
- Upgrades existing packages
- Installs build dependencies

### 3. UART Configuration
- Modifies `/boot/firmware/config.txt` (or `/boot/config.txt`)
- Updates `/boot/firmware/cmdline.txt` 
- Adds pi user to dialout group

### 4. MAVLink Router Installation
- Downloads from https://github.com/PeterJBurke/installmavlinkrouter2024
- Attempts to use pre-compiled binary for ARM64
- Falls back to source compilation if needed
- Configures service with proven settings

### 5. WebGCS Installation
- Downloads from https://github.com/PeterJBurke/WebGCS
- Creates Python virtual environment
- Installs all Python dependencies
- Configures for local MAVLink Router connection

### 6. Service Configuration
- Creates systemd service files
- Sets up dependencies between services
- Configures automatic startup after reboot

## Configuration Files

### MAVLink Router Configuration
Location: `/etc/mavlink-router/main.conf`

```ini
[General]
TcpServerPort=5678
ReportStats=false
MavlinkDialect=ardupilotmega

[UartEndpoint serial]
Device=/dev/serial0
Baud=57600

[TcpEndpoint tcp_server]
Mode=server
Address=0.0.0.0
Port=5678
```

### WebGCS Configuration
Location: `/home/pi/WebGCS/.env`

```bash
# Drone Connection Settings (via MAVLink Router)
DRONE_TCP_ADDRESS=127.0.0.1
DRONE_TCP_PORT=5678

# Web Server Settings
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=5000
SECRET_KEY=raspberry_pi_webgcs_secret_[timestamp]

# MAVLink Settings
HEARTBEAT_TIMEOUT=15
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=5
TELEMETRY_UPDATE_INTERVAL=0.1
```

## Service Management

### Service Status Commands

```bash
# Check all WebGCS-related services
sudo systemctl status mavlink-router webgcs check_wifi

# Individual service status
sudo systemctl status mavlink-router
sudo systemctl status webgcs
sudo systemctl status check_wifi

# View real-time logs
sudo journalctl -u webgcs -f
sudo journalctl -u mavlink-router -f
```

### Service Control Commands

```bash
# Restart services
sudo systemctl restart mavlink-router
sudo systemctl restart webgcs

# Stop services
sudo systemctl stop mavlink-router webgcs

# Start services
sudo systemctl start mavlink-router webgcs

# Enable/disable auto-start
sudo systemctl enable webgcs
sudo systemctl disable webgcs
```

## Network Access

After installation and reboot:

### Normal Operation (WiFi Connected)
- Access WebGCS: `http://[pi-ip-address]:5000`
- SSH access: `ssh pi@[pi-ip-address]`
- Find Pi IP: `hostname -I`

### Hotspot Failover Mode
- Hotspot name: "RaspberryPiHotspot"
- Default password: (configured during hotspot setup)
- WebGCS access: `http://10.0.0.5:5000`
- SSH access: `ssh pi@10.0.0.5`

## Troubleshooting

### Common Issues

#### Services Not Starting After Reboot
```bash
# Check if UART devices exist
ls -l /dev/serial0 /dev/ttyAMA0

# If devices don't exist, check UART configuration
cat /boot/firmware/config.txt | grep uart
cat /boot/firmware/cmdline.txt | grep console

# Manually enable services if needed
sudo systemctl enable mavlink-router webgcs
sudo systemctl start mavlink-router webgcs
```

#### No MAVLink Connection
```bash
# Check MAVLink Router status and logs
sudo systemctl status mavlink-router
sudo journalctl -u mavlink-router -n 20

# Test serial port directly
sudo stty -F /dev/serial0 57600
sudo cat /dev/serial0

# Check for MAVLink traffic
sudo tcpdump -i lo port 5678
```

#### WebGCS Not Accessible
```bash
# Check WebGCS service
sudo systemctl status webgcs
sudo journalctl -u webgcs -n 20

# Check if port is listening
sudo netstat -tulnp | grep :5000

# Test local connection
curl -I http://localhost:5000
```

#### WiFi Issues
```bash
# Check WiFi status
sudo systemctl status check_wifi
iwconfig

# Manually restart WiFi monitoring
sudo systemctl restart check_wifi

# Check available networks
sudo iwlist scan | grep ESSID
```

### Hardware Troubleshooting

#### UART Connection Issues
1. **Verify wiring**: Double-check TX/RX connections
2. **Check voltage levels**: Ensure 3.3V compatibility
3. **Test with loopback**: Connect TX to RX on Pi and test
4. **Check ground connection**: Ensure common ground

#### Power Issues
- Use quality power supply (5V, 3A+ for Pi 4)
- Check for undervoltage warnings: `dmesg | grep voltage`
- Consider powered USB hub for additional devices

### Diagnostic Commands

```bash
# System information
cat /proc/device-tree/model
uname -a
cat /etc/os-release

# UART status
cat /proc/device-tree/aliases/serial*
sudo dmesg | grep tty

# Service dependencies
systemctl list-dependencies webgcs
systemctl list-dependencies mavlink-router

# Network configuration
ip addr show
ip route show
```

## Advanced Configuration

### Custom MAVLink Router Settings

Edit `/etc/mavlink-router/main.conf`:

```bash
sudo nano /etc/mavlink-router/main.conf
sudo systemctl restart mavlink-router
```

### Custom WebGCS Settings

Edit `/home/pi/WebGCS/.env`:

```bash
nano /home/pi/WebGCS/.env
sudo systemctl restart webgcs
```

### Performance Optimization

For better performance on older Pi models:

```bash
# Reduce telemetry rate in .env file
REQUEST_STREAM_RATE_HZ=2
TELEMETRY_UPDATE_INTERVAL=0.2

# Increase GPU memory split
echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt
```

## Security Considerations

### Network Security
```bash
# Configure firewall (optional)
sudo ufw allow 5000/tcp  # WebGCS web interface
sudo ufw allow 22/tcp    # SSH access
sudo ufw enable

# Change default passwords
sudo passwd pi          # Change pi user password
```

### Service Security
- Services run with minimal privileges
- No root access required for normal operation
- Isolated temporary directories
- Read-only system directories where possible

## Backup and Recovery

### Backup Configuration
```bash
# Backup configuration files
sudo tar -czf webgcs-config-backup.tar.gz \
    /etc/mavlink-router/ \
    /home/pi/WebGCS/.env \
    /etc/systemd/system/webgcs.service \
    /etc/systemd/system/mavlink-router.service

# Backup entire WebGCS installation
sudo tar -czf webgcs-full-backup.tar.gz /home/pi/WebGCS/
```

### Recovery Process
1. Flash fresh Raspberry Pi OS
2. Restore configuration files
3. Run setup script
4. Restore custom configurations

## Manual Installation

If you need to install components manually:

### MAVLink Router Only
```bash
cd /home/pi
git clone https://github.com/PeterJBurke/installmavlinkrouter2024.git
cd installmavlinkrouter2024
chmod +x install.sh
sudo ./install.sh
```

### WebGCS Only
```bash
cd /home/pi
git clone https://github.com/PeterJBurke/WebGCS.git
cd WebGCS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Performance Monitoring

### System Resources
```bash
# CPU usage
htop

# Memory usage
free -h

# Disk usage
df -h

# Temperature
vcgencmd measure_temp
```

### Service Performance
```bash
# Service resource usage
systemctl status webgcs mavlink-router --no-pager -l

# Log analysis
sudo journalctl -u webgcs --since "1 hour ago"
```

## Getting Help

If you encounter issues:

1. **Check service logs**:
   ```bash
   sudo journalctl -u webgcs -u mavlink-router -f
   ```

2. **Verify hardware connections**: Double-check UART wiring

3. **Test components individually**:
   ```bash
   # Test MAVLink Router
   sudo systemctl stop webgcs
   sudo journalctl -u mavlink-router -f
   
   # Test WebGCS
   cd /home/pi/WebGCS
   source venv/bin/activate
   python app.py
   ```

4. **Check GitHub issues**: 
   - WebGCS: https://github.com/PeterJBurke/WebGCS/issues
   - MAVLink Router: https://github.com/PeterJBurke/installmavlinkrouter2024/issues

5. **Re-run setup**: The setup script is idempotent and can be run multiple times

## Next Steps

After successful installation:

1. **Connect your flight controller** to the UART pins
2. **Power on both Pi and flight controller**
3. **Access WebGCS** at `http://[pi-ip]:5000`
4. **Verify MAVLink connection** in the WebGCS interface
5. **Test flight operations** in a safe environment

The Raspberry Pi is now configured as a complete ground control station with automatic failover capabilities! 
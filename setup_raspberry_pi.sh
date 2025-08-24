#!/bin/bash

# Record start time
START_TIME=$(date +%s)
START_TIME_HUMAN=$(date)
echo "Installation started at: $START_TIME_HUMAN"

# ==============================================================================
# WebGCS Raspberry Pi Setup Script for Raspberry Pi OS (Bookworm)
# ==============================================================================
#
# Automated setup script for WebGCS on Raspberry Pi OS (Bookworm).
# Installs MAVLink Router, WebGCS, Python environment, and configures
# systemd services with WiFi hotspot failover capability.
#
# Components:
# - MAVLink Router
# - WebGCS
# - Python Environment Setup
# - Systemd Service Configuration
# - WiFi Hotspot Failover
# - UART Configuration for Flight Controller
#
# Requirements: Raspberry Pi OS (Bookworm), Python 3.11+
#
# Usage:
#   chmod +x setup_raspberry_pi.sh
#   sudo ./setup_raspberry_pi.sh
#
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status

# --- Configuration ---
PYTHON_VERSION="python3"
PIP_VERSION="pip3"
WEBGCS_DIR="/home/pi/WebGCS"
MAVLINK_ROUTER_DIR="/home/pi/installmavlinkrouter2024"
HOTSPOT_DIR="/home/pi/RaspberryPiHotspotIfNoWifi"
SERIAL_PORT="/dev/serial0"
FC_BAUD_RATE="57600"
MAVLINK_ROUTER_UDP_PORT="14550"
WEBGCS_TCP_PORT="5678"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# --- Helper Functions ---
print_info() { 
    echo -e "${BLUE}[INFO]${NC} $1" 
}

print_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $1" 
}

print_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $1" 
}

print_error() { 
    echo -e "${RED}[ERROR]${NC} $1" >&2 
}

# Function to check internet connectivity
check_internet() {
    print_info "Checking internet connectivity..."
    for i in {1..30}; do
        if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
            print_success "Internet connection established"
            return 0
        fi
        print_info "Waiting for internet connection... (attempt $i/30)"
        sleep 2
    done
    print_error "No internet connection after 30 attempts"
    return 1
}

# Function to safely clone a git repository with retries
safe_git_clone() {
    local repo_url="$1"
    local target_dir="$2"
    local max_attempts=3
    
    for attempt in $(seq 1 $max_attempts); do
        print_info "Cloning $repo_url (attempt $attempt/$max_attempts)"
        if git clone "$repo_url" "$target_dir"; then
            return 0
        fi
        print_error "Git clone failed, checking internet connection..."
        check_internet || return 1
        sleep 5
    done
    print_error "Failed to clone repository after $max_attempts attempts"
    return 1
}

# --- Cleanup Function ---
cleanup_old_installation() {
    print_info "Cleaning up old installation..."
    
    # Stop services if they exist
    systemctl stop mavlink-router webgcs create_ap check_wifi 2>/dev/null || true
    systemctl disable mavlink-router webgcs create_ap check_wifi 2>/dev/null || true
    
    # Remove old service files
    rm -f /etc/systemd/system/mavlink-router.service
    rm -f /etc/systemd/system/webgcs.service
    rm -f /etc/systemd/system/create_ap.service
    rm -f /etc/systemd/system/check_wifi.service
    
    # Remove old config files
    rm -f /etc/mavlink-router/main.conf
    
    # Remove old installations
    rm -rf "$WEBGCS_DIR"
    rm -rf "$HOTSPOT_DIR"
    
    # Reload systemd to recognize removed services
    systemctl daemon-reload
    
    print_success "Cleanup completed"
}

# --- Check for sudo ---
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# --- Check Raspberry Pi OS Version ---
check_pi_os_version() {
    print_info "Checking Raspberry Pi OS version..."
    
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        print_info "Detected OS: $NAME $VERSION_ID"
        
        # Check if it's Raspberry Pi OS
        if [[ "$ID" == "raspbian" ]] || [[ "$NAME" == *"Raspberry Pi"* ]]; then
            case "$VERSION_CODENAME" in
                "bookworm")
                    print_success "Raspberry Pi OS Bookworm is supported"
                    ;;
                "bullseye")
                    print_warning "Raspberry Pi OS Bullseye may work but Bookworm is recommended"
                    ;;
                *)
                    print_warning "OS version $VERSION_CODENAME may work but Bookworm is recommended"
                    ;;
            esac
        else
            print_warning "$NAME may work but Raspberry Pi OS is recommended"
        fi
    fi
}

# --- 1. Clean Up Old Installation ---
cleanup_old_installation

# --- 2. Check OS Version ---
check_pi_os_version

# --- 3. Check Internet Connection ---
check_internet

# --- 4. System Updates and Dependencies ---
print_info "Updating system packages..."
apt-get update
apt-get upgrade -y
apt-get install -y git python3 python3-pip python3-venv build-essential curl pkg-config libevent-dev

# Enable immediate history writing
echo "export PROMPT_COMMAND='history -a'" | tee -a /etc/bash.bashrc

# --- 5. Configure UART for Flight Controller ---
print_info "Configuring serial port for flight controller communication..."

# Set configuration paths for Raspberry Pi OS Bookworm
if [[ -f "/boot/firmware/config.txt" ]]; then
    CONFIG_FILE="/boot/firmware/config.txt"
    CMDLINE_FILE="/boot/firmware/cmdline.txt"
else
    CONFIG_FILE="/boot/config.txt"
    CMDLINE_FILE="/boot/cmdline.txt"
fi

print_info "Using config file: $CONFIG_FILE"

# Configure UART in config.txt
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    
    # Remove existing uart settings
    sed -i '/^enable_uart=/d' "$CONFIG_FILE"
    sed -i '/^dtoverlay=uart/d' "$CONFIG_FILE"
    sed -i '/^dtoverlay=pi3-disable-bt/d' "$CONFIG_FILE"
    sed -i '/^dtoverlay=disable-bt/d' "$CONFIG_FILE"
    sed -i '/^dtparam=uart0=/d' "$CONFIG_FILE"
    sed -i '/^dtparam=uart1=/d' "$CONFIG_FILE"
    
    # Add UART configuration
    echo "" >> "$CONFIG_FILE"
    echo "# UART Configuration for MAVLink" >> "$CONFIG_FILE"
    echo "enable_uart=1" >> "$CONFIG_FILE"
    echo "dtparam=uart0=on" >> "$CONFIG_FILE"
    echo "dtparam=uart1=off" >> "$CONFIG_FILE"
    echo "dtoverlay=disable-bt" >> "$CONFIG_FILE"
    print_success "Updated config.txt with UART settings (backup saved)"
fi

# Remove serial console from cmdline.txt
if [ -f "$CMDLINE_FILE" ]; then
    cp "$CMDLINE_FILE" "${CMDLINE_FILE}.bak"
    sed -i 's/console=ttyAMA0,[0-9]\+ //g' "$CMDLINE_FILE"
    sed -i 's/console=serial0,[0-9]\+ //g' "$CMDLINE_FILE"
    print_success "Updated cmdline.txt (backup saved)"
fi

# Add user to dialout group
if ! groups pi | grep -q dialout; then
    usermod -a -G dialout pi
    print_success "Added pi user to dialout group (will take effect after next login)"
fi

print_success "Serial port configuration complete. Reboot required for changes to take effect."

# --- 6. Install Raspberry Pi Hotspot Failover ---
print_info "Installing Raspberry Pi Hotspot Failover..."

# Clone repository
cd /home/pi
if [ -d "RaspberryPiHotspotIfNoWifi" ]; then
    rm -rf "RaspberryPiHotspotIfNoWifi"
fi
if ! safe_git_clone "https://github.com/PeterJBurke/RaspberryPiHotspotIfNoWifi.git" "RaspberryPiHotspotIfNoWifi"; then
    print_error "Failed to install WiFi Hotspot Failover. Please check your internet connection and try again."
    exit 1
fi
cd RaspberryPiHotspotIfNoWifi

# Install the check_wifi service and script
print_info "Installing WiFi check service..."
cp check_wifi.service /etc/systemd/system/
cp check_wifi.sh /usr/local/bin/
chmod +x /usr/local/bin/check_wifi.sh

print_success "WiFi Hotspot Failover installation completed"

# --- 7. Install MAVLink Router ---
print_info "Installing MAVLink Router..."

# Check if MAVLink Router is already installed
if command -v mavlink-routerd &> /dev/null && systemctl is-enabled mavlink-router &> /dev/null; then
    print_success "MAVLink Router is already installed and service is configured."
    print_info "Skipping download and build to save time."
    print_info "If you want to force a reinstall, please remove mavlink-routerd and disable the service first."
else
    cd /home/pi
    if [ -d "$MAVLINK_ROUTER_DIR" ]; then
        rm -rf "$MAVLINK_ROUTER_DIR"
    fi
    if ! safe_git_clone "https://github.com/PeterJBurke/installmavlinkrouter2024.git" "installmavlinkrouter2024"; then
        print_error "Failed to install MAVLink Router. Please check your internet connection and try again."
        exit 1
    fi
    cd installmavlinkrouter2024
    chmod +x install.sh
    ./install.sh
fi

# --- 8. Install WebGCS ---
print_info "Installing WebGCS..."
cd /home/pi
if [ -d "$WEBGCS_DIR" ]; then
    rm -rf "$WEBGCS_DIR"
fi
if ! safe_git_clone "https://github.com/PeterJBurke/WebGCS.git" "WebGCS"; then
    print_error "Failed to install WebGCS. Please check your internet connection and try again."
    exit 1
fi
cd WebGCS

# --- 9. Update WebGCS Configuration for Raspberry Pi ---
print_info "Updating WebGCS configuration for Raspberry Pi..."

# Set web server to listen on all interfaces
sed -i "s/WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST', '[^']*')/WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST', '0.0.0.0')  # Listen on all interfaces/" "${WEBGCS_DIR}/config.py"

# Set drone TCP address to localhost (MAVLink router will forward)
sed -i "s/DRONE_TCP_ADDRESS = os.getenv('DRONE_TCP_ADDRESS', '[^']*')/DRONE_TCP_ADDRESS = os.getenv('DRONE_TCP_ADDRESS', '127.0.0.1')/" "${WEBGCS_DIR}/config.py"

# Set TCP port to match MAVLink router output
sed -i "s/DRONE_TCP_PORT = os.getenv('DRONE_TCP_PORT', '[^']*')/DRONE_TCP_PORT = os.getenv('DRONE_TCP_PORT', '${WEBGCS_TCP_PORT}')/" "${WEBGCS_DIR}/config.py"

# --- 10. Create Python Virtual Environment ---
print_info "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
deactivate

# --- 11. Create .env Configuration File ---
print_info "Creating .env configuration file..."
cat > "${WEBGCS_DIR}/.env" << EOF
# WebGCS Configuration for Raspberry Pi
# Drone Connection Settings (via MAVLink Router)
DRONE_TCP_ADDRESS=127.0.0.1
DRONE_TCP_PORT=${WEBGCS_TCP_PORT}

# Web Server Settings
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=5000
SECRET_KEY=raspberry_pi_webgcs_secret_$(date +%s)

# MAVLink Settings
HEARTBEAT_TIMEOUT=15
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=5
TELEMETRY_UPDATE_INTERVAL=0.1
EOF

# --- 12. Configure MAVLink Router Service ---
print_info "Configuring MAVLink Router service..."

# Ensure config directory exists
mkdir -p /etc/mavlink-router

# Create common serial device dependency file for WebGCS
print_info "Creating common serial device dependency configuration..."
cat > /etc/systemd/system/serial-device.conf << EOF
[Unit]
ConditionPathExists=${SERIAL_PORT}
After=dev-serial0.device sys-devices-platform-serial0-tty-ttyAMA0.device
Requires=dev-serial0.device sys-devices-platform-serial0-tty-ttyAMA0.device
EOF

# Download the proven working configuration from installmavlinkrouter2024
print_info "Downloading MAVLink Router configuration..."
curl -fsSL https://raw.githubusercontent.com/PeterJBurke/installmavlinkrouter2024/main/main.conf -o /etc/mavlink-router/main.conf
chmod 644 /etc/mavlink-router/main.conf

# --- 13. Create WebGCS Service ---
print_info "Creating WebGCS service..."

# Create WebGCS service
cat > /lib/systemd/system/webgcs.service << EOF
[Unit]
Description=WebGCS - Web-Based Ground Control Station for Raspberry Pi
Documentation=https://github.com/PeterJBurke/WebGCS
# Include common serial device dependencies
.include /etc/systemd/system/serial-device.conf
After=network-online.target mavlink-router.service
Wants=network-online.target
Requires=mavlink-router.service
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=${WEBGCS_DIR}
Environment=PATH=${WEBGCS_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=${WEBGCS_DIR}
ExecStart=${WEBGCS_DIR}/venv/bin/python3 app.py
Restart=on-failure
RestartSec=10
TimeoutStartSec=30
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=webgcs

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
EOF

# --- 14. Set Permissions ---
print_info "Setting permissions..."
chown -R pi:pi "$WEBGCS_DIR"
usermod -a -G dialout pi

# --- 15. Create Service Enablement Script for After Reboot ---
print_info "Creating post-reboot service enablement..."

# Initialize UART configuration flag
UART_CONFIGURED=1  # Always configured in this script

# Disable services until after reboot (since UART config requires reboot)
systemctl disable mavlink-router webgcs 2>/dev/null || true

# Create systemd oneshot service to enable services after reboot
cat > /etc/systemd/system/enable-webgcs-services.service << EOF
[Unit]
Description=Enable WebGCS Services After Reboot
# Include common serial device dependencies
.include /etc/systemd/system/serial-device.conf

[Service]
Type=oneshot
ExecStart=/bin/systemctl enable mavlink-router
ExecStart=/bin/systemctl start mavlink-router
ExecStart=/bin/systemctl enable webgcs
ExecStart=/bin/systemctl start webgcs
ExecStart=/bin/systemctl disable enable-webgcs-services
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable the oneshot service
systemctl enable enable-webgcs-services

# --- 16. Enable and Start the WiFi Failover Service ---
print_info "Enabling WiFi failover service..."
systemctl daemon-reload
systemctl enable check_wifi.service
#systemctl start check_wifi.service # it should start at reboot or you get disconnected

# Calculate and display duration
END_TIME=$(date +%s)
END_TIME_HUMAN=$(date)
DURATION=$((END_TIME - START_TIME))
HOURS=$((DURATION / 3600))
MINUTES=$(( (DURATION % 3600) / 60 ))
SECONDS=$((DURATION % 60))

echo -e "\nInstallation timing summary:"
echo "Started : $START_TIME_HUMAN"
echo "Finished: $END_TIME_HUMAN"
echo "Duration: ${HOURS}h ${MINUTES}m ${SECONDS}s"

print_success "Installation completed successfully!"

echo
echo "======================================================================"
print_success "WebGCS Raspberry Pi Installation Complete!"
echo "======================================================================"
echo
print_warning "IMPORTANT: You MUST reboot for the UART configuration changes to take effect."
print_info "After reboot, the serial devices (/dev/serial0 and /dev/ttyAMA0) will be available."
print_info "The MAVLink Router and WebGCS services will start automatically after reboot."

echo
print_info "What was installed:"
print_info "1. MAVLink Router - Routes messages from flight controller to TCP port $WEBGCS_TCP_PORT"
print_info "2. WebGCS - Web-based ground control station"
print_info "3. WiFi Hotspot Failover - Creates hotspot if WiFi connection fails"
print_info "4. UART Configuration - Serial communication with flight controller"

echo
print_info "After reboot:"
print_info "1. Connect flight controller to GPIO pins (UART: /dev/serial0 at $FC_BAUD_RATE baud)"
print_info "2. MAVLink Router will run automatically"
print_info "3. WebGCS will be available at http://[raspberry-pi-ip]:5000"
print_info "4. If WiFi fails, Pi will create hotspot 'RaspberryPiHotspot'"

echo
print_info "Service management commands:"
print_info "  Check MAVLink Router: sudo systemctl status mavlink-router"
print_info "  Check WebGCS: sudo systemctl status webgcs"
print_info "  Check WiFi service: sudo systemctl status check_wifi"
print_info "  View logs: sudo journalctl -u webgcs -f"

echo
print_info "Configuration files:"
print_info "  WebGCS config: ${WEBGCS_DIR}/.env"
print_info "  MAVLink Router config: /etc/mavlink-router/main.conf"

echo
print_success "To reboot now, type: sudo reboot"
echo "======================================================================"

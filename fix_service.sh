#!/bin/bash

# Quick fix script for WebGCS systemd service path issues

echo "=== WebGCS Service Diagnostic and Fix ==="
echo

# Check current service file
echo "1. Current service file content:"
if [[ -f "/etc/systemd/system/webgcs.service" ]]; then
    echo "Service file exists at /etc/systemd/system/webgcs.service"
    echo "ExecStart line:"
    grep "ExecStart=" /etc/systemd/system/webgcs.service
    echo
else
    echo "Service file not found!"
    exit 1
fi

# Detect correct paths
echo "2. Detecting correct paths..."
if [[ -f "./app.py" ]]; then
    CORRECT_SCRIPT_DIR="$(pwd)"
    CORRECT_VENV_PATH="${CORRECT_SCRIPT_DIR}/venv"
    CORRECT_APP_PATH="${CORRECT_SCRIPT_DIR}/app.py"
    
    echo "Found WebGCS files in current directory:"
    echo "  Script dir: $CORRECT_SCRIPT_DIR"
    echo "  Venv path: $CORRECT_VENV_PATH" 
    echo "  App path: $CORRECT_APP_PATH"
    echo
    
    # Verify paths exist
    if [[ -f "$CORRECT_VENV_PATH/bin/python" ]] && [[ -f "$CORRECT_APP_PATH" ]]; then
        echo "✓ All required files found"
    else
        echo "✗ Missing required files:"
        [[ ! -f "$CORRECT_VENV_PATH/bin/python" ]] && echo "  - Python virtual environment"
        [[ ! -f "$CORRECT_APP_PATH" ]] && echo "  - app.py file"
        exit 1
    fi
else
    echo "✗ app.py not found in current directory"
    echo "Please run this script from the WebGCS directory"
    exit 1
fi

# Create corrected service file
echo "3. Creating corrected service file..."

CURRENT_USER="$(whoami)"

SERVICE_CONTENT="[Unit]
Description=WebGCS - Web-Based Ground Control Station
Documentation=https://github.com/PeterJBurke/WebGCS
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_USER}
WorkingDirectory=${CORRECT_SCRIPT_DIR}
Environment=PATH=${CORRECT_VENV_PATH}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
Environment=PYTHONPATH=${CORRECT_SCRIPT_DIR}
ExecStart=${CORRECT_VENV_PATH}/bin/python ${CORRECT_APP_PATH}
Restart=on-failure
RestartSec=10
TimeoutStartSec=30
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal
SyslogIdentifier=webgcs

# Security settings for Ubuntu 24.04
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=${CORRECT_SCRIPT_DIR}
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
RemoveIPC=yes
PrivateDevices=yes

[Install]
WantedBy=multi-user.target"

# Stop the service if running
echo "4. Stopping webgcs service..."
systemctl stop webgcs 2>/dev/null || true

# Write corrected service file
echo "5. Installing corrected service file..."
echo "$SERVICE_CONTENT" > /etc/systemd/system/webgcs.service
chmod 644 /etc/systemd/system/webgcs.service

# Reload and restart
echo "6. Reloading systemd and starting service..."
systemctl daemon-reload
systemctl enable webgcs
systemctl start webgcs

# Check status
echo "7. Checking service status..."
sleep 2
if systemctl is-active --quiet webgcs; then
    echo "✓ WebGCS service is now running successfully!"
    echo
    echo "Service status:"
    systemctl status webgcs --no-pager
else
    echo "✗ Service still has issues. Status:"
    systemctl status webgcs --no-pager
    echo
    echo "Check logs with: journalctl -u webgcs -f"
fi

echo
echo "=== Fix Complete ===" 
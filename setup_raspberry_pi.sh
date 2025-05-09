#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

PROJECT_DIR="/home/pi/WebGCS"
REPO_URL="https://github.com/PeterJBurke/WebGCS.git"
SERVICE_NAME="webgcs"
PYTHON_ALIAS="python3"

# --- Helper Functions ---
echo_green() {
    echo -e "\033[0;32m$1\033[0m"
}

echo_yellow() {
    echo -e "\033[1;33m$1\033[0m"
}

echo_red() {
    echo -e "\033[0;31m$1\033[0m"
}

# --- Script Start ---
echo_green "Starting WebGCS setup script for Raspberry Pi..."

# 1. Update and upgrade system packages
echo_yellow "\nUpdating package lists and upgrading existing packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install necessary packages
echo_yellow "\nInstalling git, python3, python3-pip, and python3-venv..."
sudo apt-get install -y git python3 python3-pip python3-venv

# 3. Create project directory if it doesn't exist
if [ ! -d "$PROJECT_DIR" ]; then
    echo_yellow "\nCreating project directory: $PROJECT_DIR"
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown pi:pi "$PROJECT_DIR"
else
    echo_green "\nProject directory $PROJECT_DIR already exists."
fi

# 4. Clone the repository
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo_yellow "\nCloning WebGCS repository into $PROJECT_DIR..."
    sudo -u pi git clone "$REPO_URL" "$PROJECT_DIR"
else
    echo_green "\nWebGCS repository already cloned in $PROJECT_DIR."
    echo_yellow "Pulling latest changes..."
    cd "$PROJECT_DIR"
    sudo -u pi git pull
    cd -
fi

# 5. Create and activate Python virtual environment
cd "$PROJECT_DIR"
echo_yellow "\nSetting up Python virtual environment in $PROJECT_DIR/venv..."
if [ ! -d "venv" ]; then
    sudo -u pi $PYTHON_ALIAS -m venv venv
    echo_green "Virtual environment created."
else
    echo_green "Virtual environment already exists."
fi

# 6. Install Python dependencies
echo_yellow "\nInstalling Python dependencies from requirements.txt..."
sudo -u pi bash -c "source $PROJECT_DIR/venv/bin/activate && pip install -r $PROJECT_DIR/requirements.txt"
echo_green "Python dependencies installed."

# 7. Create systemd service file
SERVICE_FILE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
echo_yellow "\nCreating systemd service file at $SERVICE_FILE_PATH..."

# Ensure the script path in ExecStart is correct
APP_PATH="$PROJECT_DIR/app.py"
PYTHON_EXEC_PATH="$PROJECT_DIR/venv/bin/python"

# Check if python executable exists
if [ ! -f "$PYTHON_EXEC_PATH" ]; then
    echo_red "Error: Python executable not found at $PYTHON_EXEC_PATH. Please check venv setup."
    exit 1
fi

# Check if app.py exists
if [ ! -f "$APP_PATH" ]; then
    echo_red "Error: app.py not found at $APP_PATH. Please check repository structure."
    exit 1
fi

cat << EOF | sudo tee "$SERVICE_FILE_PATH" > /dev/null
[Unit]
Description=WebGCS Application
After=network.target

[Service]
User=pi
Group=pi
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_EXEC_PATH $APP_PATH
Restart=always
RestartSec=5
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

echo_green "Systemd service file created."

# 8. Enable and start the service
echo_yellow "\nReloading systemd daemon, enabling and starting $SERVICE_NAME service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}.service
sudo systemctl start ${SERVICE_NAME}.service

echo_green "\nChecking status of $SERVICE_NAME service:"
sudo systemctl status ${SERVICE_NAME}.service --no-pager || true # Don't exit if status fails for some reason

echo_green "\nWebGCS setup script completed!"
echo_yellow "You might need to reboot for all changes to take full effect, or if the service fails to start initially."
echo_yellow "To check logs: sudo journalctl -u $SERVICE_NAME -f"

cd - > /dev/null # Go back to original directory quietly

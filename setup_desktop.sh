#!/bin/bash

# ==============================================================================
# Drone Control Desktop Setup Script (Based on v2.63 dependencies)
# ==============================================================================
#
# Creates a Python virtual environment, installs required packages,
# and downloads necessary JavaScript libraries for the desktop GCS.
#
# Usage:
#   1. Place this script in the project root directory (e.g., ~/drone_control_desktop).
#   2. Make it executable: chmod +x setup_desktop.sh
#   3. Run it: ./setup_desktop.sh
#   4. Follow the instructions to activate the environment and run the app.
#
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status.

APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )" # Get script's directory
VENV_PATH="${APP_DIR}/venv"

echo "[INFO] Setting up Drone Control Desktop in: ${APP_DIR}"
echo "[INFO] Using Python 3: $(python3 --version)"

# --- 1. Create Directory Structure ---
echo "[INFO] Creating directories..."
mkdir -p "${APP_DIR}/templates"
mkdir -p "${APP_DIR}/static/css"
mkdir -p "${APP_DIR}/static/lib"

# --- 2. Create Python Virtual Environment ---
if [ -d "${VENV_PATH}" ]; then
    echo "[INFO] Virtual environment already exists at ${VENV_PATH}. Skipping creation."
else
    echo "[INFO] Creating Python virtual environment at ${VENV_PATH}..."
    python3 -m venv "${VENV_PATH}"
fi

# --- 3. Install Python Dependencies ---
echo "[INFO] Installing Python dependencies into virtual environment..."
# Activate step is for the user, but we call pip directly
"${VENV_PATH}/bin/pip" install --upgrade pip
"${VENV_PATH}/bin/pip" install Flask pymavlink Flask-SocketIO gevent gevent-websocket requests

# --- 4. Download Frontend Libraries ---
echo "[INFO] Downloading Frontend JavaScript libraries..."
curl -sL https://unpkg.com/leaflet@1.9.4/dist/leaflet.css -o "${APP_DIR}/static/lib/leaflet.css"
curl -sL https://unpkg.com/leaflet@1.9.4/dist/leaflet.js -o "${APP_DIR}/static/lib/leaflet.js"
curl -sL https://cdn.socket.io/4.7.4/socket.io.min.js -o "${APP_DIR}/static/lib/socket.io.min.js"
echo "[INFO] Frontend libraries downloaded to static/lib/"

# --- 5. Set Permissions (Optional but good practice) ---
echo "[INFO] Setting basic script permissions..."
chmod +x "${APP_DIR}/app.py" # Allow direct execution if needed later
chmod +x "${APP_DIR}/test_mavlink_connection.py"
chmod +x "${APP_DIR}/test_web_server.py"

# --- Final Instructions ---
echo ""
echo "[INFO] Setup Complete!"
echo "--------------------------------------------------"
echo "NEXT STEPS:"
echo "1. Activate the virtual environment:"
echo "   - On Linux/macOS: source ${VENV_PATH}/bin/activate"
echo "   - On Windows (Git Bash/WSL): source ${VENV_PATH}/bin/activate"
echo "   - On Windows (CMD): .\\venv\\Scripts\\activate.bat"
echo "   - On Windows (PowerShell): .\\venv\\Scripts\\Activate.ps1"
echo "   (You should see '(venv)' at the beginning of your command prompt)"
echo ""
echo "2. Ensure your drone is powered on and connected to the network at 192.168.1.247:14550."
echo "   (MAVLink should be running on the drone)."
echo ""
echo "3. Run the web application:"
echo "   python app.py"
echo ""
echo "4. Open your web browser and go to:"
echo "   http://127.0.0.1:5000  OR  http://<your_desktop_ip>:5000"
echo ""
echo "5. To stop the application, press CTRL+C in the terminal where it's running."
echo "6. To run again later, just reactivate the environment (step 1) and run 'python app.py' (step 3)."
echo "--------------------------------------------------"

exit 0

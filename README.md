# Drone Control Desktop Interface (v2.63-Desktop-TCP-AckEkf)

This project provides a web-based ground control interface, adapted from the Raspberry Pi version, to run on a desktop computer. It connects directly to a drone running MAVLink, expecting the drone to act as a TCP server.

## Features

* Direct TCP connection to drone running MAVLink
* Attitude/heading reference display
* Real-time map tracking
* Command interface (arm/disarm, takeoff/landing, mode changes)
* "Fly To" target location functionality with map marker
* Geofence and mission visualization
* Detailed command acknowledgment feedback
* Enhanced status monitoring (connection, EKF status, messages)
* Detailed MAVLink heartbeat logging for debugging
* Responsive UI layout for desktop and mobile use

## Prerequisites

*   A desktop computer (Linux, macOS, Windows with WSL)
*   Python 3 (check with `python3 --version`)
*   `pip` (Python package installer)
*   `git` (Optional, for cloning if obtained from a repository)
*   `curl` (For downloading libraries during setup)
*   Network connectivity between your desktop and the drone.
*   The drone must be configured to act as a **MAVLink TCP Server**, listening for incoming connections on port `5678`, and be accessible at IP `192.168.1.247`.

## Setup Instructions

1.  **Obtain Files:**
    *   Download or clone all project files (`app.py`, `setup_desktop.sh`, `templates/`, `static/`, etc.) into a single directory (e.g., `~/drone_control_desktop`).

2.  **Run Setup Script:**
    *   Open a terminal or command prompt.
    *   Navigate to the project directory: `cd ~/drone_control_desktop`
    *   Make the setup script executable: `chmod +x setup_desktop.sh`
    *   Run the script: `./setup_desktop.sh`
    *   This will create a `venv` directory, install Python packages, and download JS libraries.

3.  **Activate Virtual Environment:**
    *   You need to activate the environment *each time* you want to run the application in a new terminal session.
    *   **On Linux/macOS/Git Bash/WSL:** `source venv/bin/activate`
    *   **On Windows CMD:** `.\venv\Scripts\activate.bat`
    *   **On Windows PowerShell:** `.\venv\Scripts\Activate.ps1` (You might need to adjust execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)
    *   Your terminal prompt should now start with `(venv)`.

## Running the Application

1.  **Ensure Drone is Ready:** Power on your drone and confirm it's connected to the network (`192.168.1.247`) and the MAVLink **TCP Server** (port `5678`) is active and listening for connections.

2.  **Activate Environment:** If not already active, activate the virtual environment (see step 3 above).

3.  **Run Backend:** In the terminal (with the venv activated), run:
    ```bash
    python app.py
    ```
    *   You should see log messages indicating the server has started and is attempting a **TCP connection** to the drone.

4.  **Access Web UI:**
    *   Open a web browser on your desktop (or another device on the same network).
    *   Go to: `http://127.0.0.1:5000`
    *   Alternatively, find your desktop's IP address (e.g., using `ip addr` on Linux or `ipconfig` on Windows) and access it via `http://<your_desktop_ip>:5000`.

5.  **Use Interface:** The web interface should load. Check the connection status and wait for telemetry data to appear.

## Using the Interface

1. **Status & Indicators**:
   * Top section shows attitude and heading indicator
   * Connection status and EKF status indicators in Status box
   * Messages box displays system messages and command acknowledgments

2. **Flight Controls**:
   * Arm/Disarm: Safely arm or disarm the drone
   * Takeoff: Initiate an automatic takeoff to specified altitude
   * Land/RTL: Command landing or Return-to-Launch

3. **Mode Selection**:
   * Set flight modes via dropdown (Guided, Loiter, etc.)

4. **Go To Navigation**:
   * Enter coordinates manually or click on map
   * Enable "Fly To" button for point-and-click navigation
   * Red target marker shows navigation target

5. **Map Features**:
   * Request and visualize geofence data
   * Request and visualize mission waypoints
   * Center map on drone position

## Stopping the Application

*   Go to the terminal where `python app.py` is running.
*   Press `CTRL+C`. The server should shut down gracefully.

## Troubleshooting

*   **No Connection / No Heartbeat / Connection Refused:**
    *   Verify the drone's IP address is exactly `192.168.1.247`.
    *   Verify the drone is configured as a MAVLink **TCP Server** listening on port `5678`.
    *   Check network connectivity (can you `ping 192.168.1.247` from your desktop?).
    *   Check if the port is open and listening on the drone side. You can try tools from your desktop like:
        *   `telnet 192.168.1.247 5678` (Should connect without error if open)
        *   `nc -vz 192.168.1.247 5678` (Netcat check - might need installing)
    *   Check your **desktop's** firewall. Ensure it allows **outgoing** TCP connections to `192.168.1.247:5678`.
    *   Check the **drone's** firewall or configuration to ensure it allows **incoming** TCP connections on port `5678` (possibly limiting it to your desktop's IP if configured for security).
    *   Run the `test_mavlink_connection.py` script (after activating venv: `python test_mavlink_connection.py`) for specific TCP connection testing.
*   **Web UI Not Loading:**
    *   Ensure the `python app.py` script is running without errors in the terminal.
    *   Verify you are using the correct URL (`http://127.0.0.1:5000` or `http://<your_desktop_ip>:5000`).
    *   Check your desktop firewall allows incoming TCP connections on port `5000`.
    *   Run the `test_web_server.py` script (after activating venv: `python test_web_server.py`).
*   **"Address already in use" Error:** Another application might be using port `5000`. Stop the other application or change `WEB_SERVER_PORT` in `app.py`.
*   **Dependency Errors:** Ensure you ran `setup_desktop.sh` successfully and activated the `venv` before running `python app.py`.

# WebGCS Configuration Guide

This document describes how to configure the WebGCS application using environment variables.

## Configuration Options

### Drone Connection Settings
- `DRONE_TCP_ADDRESS`: IP address of the drone (default: 192.168.1.247)
- `DRONE_TCP_PORT`: Port number for MAVLink connection (default: 5678)

### Web Server Settings
- `WEB_SERVER_HOST`: Host address to bind the web server (default: 0.0.0.0)
- `WEB_SERVER_PORT`: Port number for the web server (default: 5000)
- `SECRET_KEY`: Secret key for Flask sessions (default: desktop_drone_secret!)

### MAVLink Settings
- `HEARTBEAT_TIMEOUT`: Timeout in seconds for MAVLink heartbeat (default: 15)
- `REQUEST_STREAM_RATE_HZ`: Rate in Hz for requesting MAVLink data streams (default: 4)
- `COMMAND_ACK_TIMEOUT`: Timeout in seconds for command acknowledgments (default: 5)
- `TELEMETRY_UPDATE_INTERVAL`: Interval in seconds for telemetry updates (default: 0.1)

## Example Configuration

Create a `.env` file in the root directory with the following content:

```bash
# Drone Connection Settings
DRONE_TCP_ADDRESS=192.168.1.247
DRONE_TCP_PORT=5678

# Web Server Settings
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=5000
SECRET_KEY=change_this_to_a_secure_secret_key

# MAVLink Settings
HEARTBEAT_TIMEOUT=15
REQUEST_STREAM_RATE_HZ=4
COMMAND_ACK_TIMEOUT=5
TELEMETRY_UPDATE_INTERVAL=0.1
```

## Usage

1. Copy the example configuration above to a new file named `.env`
2. Modify the values according to your setup
3. The application will automatically load these environment variables

## Security Notes

1. Always change the `SECRET_KEY` to a secure value in production
2. Keep your `.env` file secure and never commit it to version control
3. Use different configurations for development and production environments

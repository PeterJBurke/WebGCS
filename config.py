import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Drone Connection Settings
# At home 192.168.1.247
DRONE_TCP_ADDRESS = os.getenv('DRONE_TCP_ADDRESS', '192.168.193.63')  # Drone IP address
DRONE_TCP_PORT = os.getenv('DRONE_TCP_PORT', '5678')  # Drone port
MAVLINK_CONNECTION_STRING = f'tcp:{DRONE_TCP_ADDRESS}:{DRONE_TCP_PORT}'

# Web Server Settings
WEB_SERVER_HOST = os.getenv('WEB_SERVER_HOST', 'localhost')
WEB_SERVER_PORT = int(os.getenv('WEB_SERVER_PORT', '5000'))
SECRET_KEY = os.getenv('SECRET_KEY', 'desktop_drone_secret!')

# MAVLink Settings
HEARTBEAT_TIMEOUT = int(os.getenv('HEARTBEAT_TIMEOUT', '30'))
REQUEST_STREAM_RATE_HZ = int(os.getenv('REQUEST_STREAM_RATE_HZ', '4'))  # Restored to 4 Hz for normal operation
COMMAND_ACK_TIMEOUT = int(os.getenv('COMMAND_ACK_TIMEOUT', '10'))
TELEMETRY_UPDATE_INTERVAL = float(os.getenv('TELEMETRY_UPDATE_INTERVAL', '0.1'))  # Seconds (10 Hz for faster UI updates)

# ArduPilot Custom Flight Modes
AP_CUSTOM_MODES = {
    'STABILIZE': 0,
    'ACRO': 1,
    'ALT_HOLD': 2,
    'AUTO': 3,
    'GUIDED': 4,
    'LOITER': 5,
    'RTL': 6,
    'LAND': 9,
    'POS_HOLD': 16,
    'BRAKE': 17,
    'THROW': 18,
    'AVOID_ADSB': 19,
    'GUIDED_NOGPS': 20,
    'SMART_RTL': 21,
    'FLOWHOLD': 22,
    'FOLLOW': 23,
    'ZIGZAG': 24,
    'SYSTEMID': 25,
    'AUTOROTATE': 26,
    'AUTO_RTL': 27
}

# Create reverse mapping for mode names to IDs
AP_MODE_NAME_TO_ID = {k: v for k, v in AP_CUSTOM_MODES.items()} 
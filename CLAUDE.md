# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development
```bash
# Run the application locally
python app.py

# Run with environment variables from .env
python -m dotenv run python app.py

# Test MAVLink connection with SITL
sim_vehicle.py --aircraft test --console --map --out tcpin:0.0.0.0:5678
```

### Service Management (Ubuntu)
```bash
# Check service status
sudo systemctl status webgcs

# Restart service
sudo systemctl restart webgcs

# View logs
sudo journalctl -u webgcs -f
```

### Service Management (Raspberry Pi)
```bash
# Check all related services
sudo systemctl status mavlink-router webgcs check_wifi

# View MAVLink router logs
sudo journalctl -u mavlink-router -f
```

### TTS Notifications
```bash
# Test TTS manually
uv run tts/elevenlabs_tts.py "Test message"

# Quick completion notification
python tts/tts_notify.py "Task complete"
```

## Architecture Overview

### Core Application Structure
WebGCS is a Flask-SocketIO web application that provides real-time ground control for MAVLink-compatible drones. The architecture is built around three main components:

1. **MAVLink Connection Manager** (`mavlink_connection_manager.py`) - Handles all MAVLink protocol communication
2. **Message Processors** (`mavlink_message_processor.py`) - Processes specific MAVLink message types
3. **SocketIO Handlers** (`socketio_handlers.py`) - Manages real-time web communication

### Key Components

**Real-time Data Flow:**
- MAVLink messages flow through `mavlink_receive_loop_runner()` 
- Messages are processed by type-specific handlers in `mavlink_message_processor.py`
- Processed data updates shared `drone_state` dictionary with thread-safe locks
- Changes are emitted to web clients via SocketIO events

**Centralized Logging System:**
- `webgcs_logger.py` provides high-performance logging optimized for <1ms latency
- Uses circular buffers and structured logging for real-time operations
- All major components use `MAVLinkLogger` for consistent logging

**Web Interface:**
- Single-page application in `templates/index.html`
- Real-time updates via Socket.IO
- Offline map support with IndexedDB caching (`static/offline-maps.js`)

### Threading and Concurrency
- Uses gevent for asynchronous operations
- MAVLink connection runs in dedicated thread
- Thread-safe access to `drone_state` via locks
- SocketIO handles concurrent web client connections

### Configuration System
- Environment variables loaded from `.env` file
- MAVLink connection parameters configurable via environment
- Default values in `config.py` for ArduPilot custom modes

### Platform-Specific Features
- **Ubuntu Desktop**: Systemd service with security hardening
- **Raspberry Pi**: UART integration via MAVLink router, WiFi hotspot failover
- Automated setup scripts for both platforms

### Offline Maps Architecture
- Client-side tile caching using IndexedDB
- Support for OpenStreetMap and Esri satellite imagery  
- Progressive download with fallback to online tiles
- Cache management and storage optimization

## Important Implementation Notes

### MAVLink Message Processing
- All message processors follow the pattern: `process_<message_type>(msg, drone_state, drone_state_lock, mavlink_conn, log_cmd_action_cb, sio_instance)`
- Processors return `True` if drone_state was modified, `False` otherwise
- System ID filtering ensures messages are from the correct vehicle

### Command Acknowledgment System
- Commands are tracked in `pending_commands` dictionary
- `process_command_ack()` provides detailed feedback for ARM/DISARM, mode changes, etc.
- UI receives both technical MAVLink responses and user-friendly messages

### Voice Notifications (TTS)
- Hooks system in `.claude/hooks/` provides TTS notifications
- `stop.py` hook triggers when Claude responses complete
- ElevenLabs TTS integration with fallback to other providers

### Error Handling Patterns
- Silent failure for non-critical operations (TTS, logging)
- Structured error reporting for MAVLink operations
- Connection recovery mechanisms for network interruptions

### Development vs Production
- Debug statements minimized in favor of structured logging
- Service configurations include security hardening
- Offline capability essential for field operations

## Critical Safety Considerations

This is drone control software - safety is paramount:
- All flight commands require explicit user confirmation
- Connection status clearly displayed to user
- Command acknowledgment feedback prevents silent failures
- Heartbeat monitoring ensures connection health
- Emergency stop capabilities maintained at all times
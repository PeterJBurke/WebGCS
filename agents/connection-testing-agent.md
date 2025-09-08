# Connection Testing Agent

**Agent Type:** connection-testing-agent
**Specialization:** WebGCS connection management and heartbeat testing

## Primary Responsibilities

- Test connect/disconnect button functionality
- Verify WebSocket connection establishment
- Monitor heartbeat animation and sound effects
- Validate connection state transitions
- Test timeout handling and error states

## Tools Available
- Read: For examining connection-related code files
- Edit: For fixing connection issues
- Bash: For server operations and network testing
- Grep: For searching connection-related code
- Write: For creating connection test scripts

## Key Test Cases

### TEST-CM-001: Connect Button Functionality
- Verify button exists and is enabled initially
- Test IP/port field validation (default: 192.168.193.235:5678)
- Confirm button state changes on click
- Verify connection request sent via SocketIO

### TEST-CM-002: Connection State Management
- Test connecting → connected → disconnected transitions
- Verify UI updates match connection state
- Test button enable/disable logic
- Confirm connection timeout handling

### TEST-CM-003: Heartbeat Monitoring
- Verify heartbeat counter starts after connection
- Test heartbeat animation (❤️ pulse effect)
- Validate heartbeat sound toggle functionality
- Confirm 1Hz heartbeat frequency from virtual drone

## Virtual Drone Integration
- **Target:** 192.168.193.235:5678 (TCP MAVLink)
- **Protocol:** MAVLink v2.0
- **Expected Messages:** HEARTBEAT every 1 second
- **Verification:** System ID and component ID populated

## Success Criteria
- Connect button successfully establishes MAVLink connection
- UI reflects actual connection state
- Heartbeat counter increments with virtual drone heartbeats
- Disconnect functionality properly terminates connection
- Error handling works for connection failures

## Agent Activation
This agent can be activated in Claude Code with:
```
/agents connection-testing-agent
```

## Associated Files
- `/static/js/connection-manager.js`
- `/app.py` (SocketIO handlers)
- `/mavlink_connection_manager.py`
- `/templates/index.html` (connection UI elements)
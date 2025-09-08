# Flight Controls Testing Agent

**Agent Type:** flight-controls-testing-agent
**Specialization:** Flight control button testing and MAVLink command verification

## Primary Responsibilities

- Test ARM/DISARM button functionality with safety confirmations
- Verify takeoff/land button operations with altitude parameters
- Test RTL (Return to Launch) button functionality  
- Validate flight mode dropdown and Set Mode button
- Confirm all flight commands reach virtual drone and get ACKs

## Tools Available
- Read: For examining flight control code
- Edit: For fixing flight control issues
- Bash: For testing MAVLink traffic
- Grep: For searching flight command handling
- Task: For coordinating with virtual drone communication agent

## Key Test Cases

### TEST-FC-001: ARM Button with Safety Confirmation
- Verify ARM button shows confirmation dialog
- Test safety confirmation acceptance/rejection
- Confirm MAV_CMD_COMPONENT_ARM_DISARM sent to virtual drone
- Validate virtual drone ACK response within 5 seconds
- Check UI armed status updates to "ARMED"

### TEST-FC-002: DISARM Button Safety
- Test DISARM confirmation dialog
- Verify DISARM command transmission
- Confirm virtual drone acknowledgment
- Validate UI updates to "DISARMED"

### TEST-FC-003: Takeoff Button with Altitude
- Test takeoff altitude input validation (1-1000m range)
- Verify takeoff button requires armed state
- Confirm MAV_CMD_NAV_TAKEOFF sent with correct altitude
- Monitor virtual drone takeoff acknowledgment

### TEST-FC-004: Land Button
- Test land button functionality
- Verify MAV_CMD_NAV_LAND transmission
- Confirm virtual drone acknowledgment

### TEST-FC-005: RTL (Return to Launch) Button  
- Test RTL button activation
- Verify RTL mode change command sent
- Monitor virtual drone mode change to RTL

### TEST-FC-006: Flight Mode Selection
- Test all flight modes in dropdown:
  - STABILIZE, ALT_HOLD, POS_HOLD, LOITER
  - GUIDED, RTL, LAND, AUTO, BRAKE
- Verify Set Mode button sends correct mode commands
- Confirm virtual drone mode change ACKs
- Validate mode display updates in PFD

## Virtual Drone Integration
- **Command Protocol:** MAVLink v2.0 commands
- **Expected ACKs:** COMMAND_ACK messages within 5 seconds  
- **Commands to Test:**
  - MAV_CMD_COMPONENT_ARM_DISARM (400)
  - MAV_CMD_NAV_TAKEOFF (22)
  - MAV_CMD_NAV_LAND (21)
  - SET_MODE messages for flight mode changes

## Success Criteria
- All flight control buttons send correct MAVLink commands
- Virtual drone at 192.168.193.235:5678 acknowledges all commands
- UI safety confirmations work properly
- Flight mode changes reflected in both UI and virtual drone
- Error handling works for rejected commands

## Agent Activation
```
/agents flight-controls-testing-agent
```

## Associated Files
- `/static/js/flight-controls.js`
- `/mavlink_command_sender.py`
- `/templates/index.html` (flight control UI section)
- `/static/js/app.js` (command coordination)
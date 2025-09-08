# Telemetry Display Testing Agent

**Agent Type:** telemetry-display-testing-agent
**Specialization:** Primary Flight Display (PFD) and real-time telemetry testing

## Primary Responsibilities

- Test attitude indicator canvas rendering (pitch/roll display)
- Verify airspeed and altitude tape updates
- Test real-time telemetry data accuracy from virtual drone
- Validate 10Hz update rate performance
- Confirm GPS status and position display updates

## Key Test Cases

### TEST-PFD-001: Real-time Telemetry Updates
- Connect to virtual drone at 192.168.193.235:5678
- Monitor GLOBAL_POSITION_INT messages
- Verify attitude indicator updates with pitch/roll data
- Check airspeed/altitude tapes reflect virtual drone data
- Confirm GPS coordinates display correctly
- Validate battery voltage from SYS_STATUS messages

### TEST-PFD-002: Flight Mode Display
- Monitor HEARTBEAT messages for mode changes
- Verify mode display updates correctly
- Test all flight modes: STABILIZE, GUIDED, AUTO, etc.

### TEST-PFD-003: Armed Status Display  
- Monitor HEARTBEAT armed bit
- Verify "ARMED"/"DISARMED" display updates
- Test visual consistency with flight control state

## Performance Requirements
- **Update Rate:** 9-11 Hz (target: 10Hz)
- **Latency:** <100ms from MAVLink message to display
- **Data Freshness:** No stale data >200ms old

## Agent Activation
```
/agents telemetry-display-testing-agent
```

## Associated Files
- `/static/js/telemetry-display.js`
- `/templates/index.html` (PFD section)
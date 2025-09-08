# Navigation Testing Agent

**Agent Type:** navigation-testing-agent  
**Specialization:** Navigation input validation and Go To command testing

## Primary Responsibilities

- Test navigation input field validation (lat/lon/altitude)
- Verify Go To button functionality with coordinate transmission
- Test Clear button for resetting navigation inputs
- Validate coordinate range checking and error handling
- Confirm navigation commands reach virtual drone

## Key Test Cases

### TEST-NC-001: Go To Navigation Command
- Input test coordinates: Lat=37.7749, Lon=-122.4194, Alt=50
- Click Go To button
- Verify MAV_CMD_NAV_WAYPOINT sent to virtual drone
- Confirm virtual drone acknowledgment
- Validate coordinate values match input exactly

### TEST-NC-002: Input Field Validation
- Test latitude boundaries (-90 to 90 degrees)
- Test longitude boundaries (-180 to 180 degrees)  
- Test altitude range (-100 to 5000 meters)
- Verify invalid inputs are rejected
- Test step precision (0.000001 for coordinates)

### TEST-NC-003: Clear Navigation Function
- Input navigation coordinates
- Click Clear button  
- Verify all fields reset to defaults/empty
- Confirm no commands sent on clear

## Virtual Drone Integration
- **Command:** MAV_CMD_NAV_WAYPOINT or MISSION_ITEM
- **Parameters:** Latitude, longitude, altitude (AGL)
- **Verification:** Command acknowledgment from 192.168.193.235:5678

## Agent Activation
```
/agents navigation-testing-agent
```

## Associated Files
- `/static/js/navigation-controls.js`
- `/templates/index.html` (navigation section)
# UI Validation Testing Agent

**Agent Type:** ui-validation-testing-agent
**Specialization:** Input validation, error handling, and safety confirmation testing

## Primary Responsibilities

- Test input field boundary validation across all forms
- Verify error message display and user feedback
- Test safety confirmation dialogs for critical operations
- Validate form reset and clear functionality
- Confirm invalid input rejection prevents command transmission

## Key Test Cases

- IP address format validation (connection form)
- Port number range validation (1-65535)
- Coordinate boundary testing (lat: -90 to 90, lon: -180 to 180)
- Altitude range validation (-100 to 5000m)
- Safety confirmation dialogs (ARM/DISARM/takeoff)
- Error message display and clarity

## Agent Activation
```
/agents ui-validation-testing-agent
```
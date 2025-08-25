# WebGCS Manual Testing Guide

## Overview
This guide separates responsibilities between the testing agent and the user for WebGCS validation. The agent handles application startup and provides technical guidance, while the user performs all browser-based manual testing activities.

## Role Responsibilities

### Agent Responsibilities
- Start the WebGCS application (`python app.py`)
- Verify application is running and accessible
- Check environment configuration (.env file)
- Provide the application URL to the user
- Monitor application logs and report any startup issues
- Offer troubleshooting guidance when needed

### User Responsibilities
- Open web browser and navigate to provided URL
- Manually interact with all web interface elements
- Fill forms, click buttons, and test UI functionality
- Observe and validate telemetry data displays
- Test connection establishment and management
- Report issues and validate expected behaviors
- Perform all testing scenarios described in this guide

## Prerequisites
- WebGCS application installed and configured
- Python environment set up with required dependencies
- `.env` file configured with proper MAVLINK_HOST setting
- Web browser (Chrome, Firefox, or Edge recommended)
- Optional: SITL simulator or physical drone for full testing

## Testing Objectives
1. Agent starts WebGCS application successfully
2. User accesses web interface via browser
3. User configures drone connection using provided settings
4. User establishes connection with drone/simulator
5. User verifies telemetry data reception and display
6. User tests UI functionality and responsiveness

---

## Agent Phase: Application Startup

The agent will:
1. Read and verify the `.env` configuration file
2. Check port availability (5001)
3. Start the WebGCS application using `python app.py`
4. Verify successful startup and provide application URL
5. Monitor for any startup errors or issues

**Agent Expected Output:**
- Application running on http://127.0.0.1:5001
- No startup errors in terminal output
- MAVLINK_HOST configuration confirmed from .env file
- Clear indication that application is ready for user testing

---

## User Phase: Manual Testing Instructions

**IMPORTANT: All steps below must be performed manually by the USER. The agent does not perform any browser automation or web interface interactions.**

### Step 1: Access WebGCS Web Interface

#### 1.1 Open Browser and Navigate
1. Open your preferred web browser (Chrome, Firefox, or Edge recommended)
2. Navigate to the URL provided by the agent: `http://127.0.0.1:5001`
3. Allow 3-5 seconds for the page to fully load
4. **Expected Result**: WebGCS interface loads showing the main dashboard

#### 1.2 Verify Initial Interface State  
1. Check that the page title shows "WebGCS"
2. Verify the connection status shows "Disconnected" (red indicator)
3. Confirm the connection form is visible with IP and Port input fields
4. Look for the Connect button (should be enabled)
5. Verify the Disconnect button is disabled/grayed out
6. **Expected Result**: Clean interface load with all elements visible

**Screenshot Checkpoint**: Take a screenshot of the initial interface state for documentation

### Step 2: Configure Drone Connection

#### 2.1 Enter Connection Parameters
1. Locate the drone IP input field (should have placeholder "192.168.1.100")
2. Clear any existing value in the IP field
3. Enter the MAVLINK_HOST value provided by the agent (from .env file)
4. Verify the Port field shows `5678` (default MAVLink port)
5. **Expected Result**: IP field contains the correct IP address, Port field contains `5678`

#### 2.2 Verify Input Validation
1. Confirm the IP address format is accepted (no validation errors)
2. Check that the port number is within valid range (1-65535)
3. **Expected Result**: No validation errors, inputs accepted

**Note**: The agent will provide the correct MAVLINK_HOST IP address from the .env configuration

### Step 3: Establish Connection

#### 3.1 Initiate Connection
1. Click the "Connect" button
2. Observe the connection status indicator
3. Wait 5-10 seconds for connection establishment
4. **Expected Result**: Status changes from "Disconnected" to "Connecting" then "Connected"

#### 3.2 Monitor Connection Process
1. Check the browser interface for connection status updates
2. Look for any error messages displayed in the web interface
3. Open browser developer tools (F12) and check console for errors
4. **Expected Result**: Clean connection process with no errors

#### 3.3 Verify Connected State
1. Check connection status shows "Connected" (green indicator)
2. Verify Connect button becomes disabled
3. Confirm Disconnect button becomes enabled
4. **Expected Result**: UI reflects connected state correctly

**User Troubleshooting Steps:**
- Connection timeout: Report to agent, may indicate drone/SITL connectivity issues
- Network errors: Check that you can access other websites normally
- Browser console errors: Note any JavaScript errors and report to agent

### Step 4: Verify Telemetry Data Flow

#### 4.1 Check Real-time Data Updates
1. Look for telemetry data panels updating in real-time
2. Monitor GPS coordinates (if GPS available)
3. Check battery voltage and current readings
4. Observe attitude indicators (pitch, roll, yaw)
5. Verify altitude and ground speed displays
6. **Expected Result**: Data updates continuously every 1-2 seconds

#### 4.2 Validate Data Accuracy
1. Compare displayed values with expected ranges:
   - GPS coordinates should match approximate location
   - Battery voltage should be reasonable (10-15V for typical setups)
   - Attitude values should reflect current orientation
2. **Expected Result**: All telemetry values appear realistic and updating

#### 4.3 Test Map Functionality
1. Locate the map display panel
2. Verify map tiles load correctly
3. Check if drone position marker appears (if GPS available)
4. Test map zoom and pan functionality using mouse wheel and click-drag
5. **Expected Result**: Interactive map displays with proper tile loading

**Screenshot Checkpoint**: Take screenshots of:
- Connected status display
- Telemetry data panels with live values
- Map view with drone position (if available)

### Step 5: Test Interface Responsiveness

#### 5.1 UI Interaction Testing
1. Test various buttons and controls for responsiveness
2. Verify real-time updates don't interfere with user interactions
3. Check browser console for JavaScript errors (F12 → Console tab)
4. **Expected Result**: Smooth, responsive interface with no console errors

#### 5.2 Data Persistence Testing
1. Refresh the browser page while connected (F5 or Ctrl+R)
2. Verify connection persists through page reload
3. Check that telemetry data resumes immediately
4. **Expected Result**: Connection maintained, data flow continues

### Step 6: Connection Management Testing

#### 6.1 Test Disconnect Functionality
1. Click the "Disconnect" button
2. Observe status change to "Disconnected"
3. Verify telemetry data stops updating
4. Check Connect button becomes enabled again
5. **Expected Result**: Clean disconnection with UI state reset

#### 6.2 Test Reconnection
1. Click "Connect" button again
2. Verify quick reconnection (should be faster than initial connection)
3. Confirm telemetry data resumes
4. **Expected Result**: Successful reconnection with data flow restored

### Step 7: Error Handling and Edge Cases

#### 7.1 Test Invalid Connection Parameters
1. Disconnect if currently connected
2. Enter an invalid IP address (e.g., `192.168.999.999`)
3. Attempt to connect
4. **Expected Result**: Clear error message displayed in interface, no system crash

#### 7.2 Test Network Connectivity
1. While connected, temporarily disable your network connection (WiFi off)
2. Observe connection status changes in the interface
3. Re-enable network connection
4. **Expected Result**: Interface shows connection loss and attempts to reconnect

### Step 8: Final Documentation and Cleanup

#### 8.1 Final Documentation
1. Take final screenshots showing:
   - Successful connection state
   - Active telemetry data
   - Any error states encountered
2. Note any issues or unexpected behaviors in your browser
3. Document test completion time and overall results

#### 8.2 User Cleanup
1. Click "Disconnect" to properly close MAVLink connection
2. Close the browser tab/window
3. **Expected Result**: Clean browser session closure

**Note**: The agent will handle stopping the application (`app.py`) - users do not need to interact with the terminal

---

## Expected Test Results Summary

### Agent Success Criteria
- ✅ Application starts on port 5001 without errors
- ✅ .env configuration read and MAVLINK_HOST provided to user
- ✅ Application accessible at http://127.0.0.1:5001
- ✅ Terminal shows no startup errors or issues
- ✅ Application remains stable during user testing

### User Success Criteria
- ✅ Web interface loads completely and correctly in browser
- ✅ Connection established with drone/SITL using provided IP
- ✅ Real-time telemetry data displayed and updating
- ✅ All UI elements functional and responsive to clicks
- ✅ Clean connect/disconnect cycle functionality
- ✅ Graceful error handling for edge cases
- ✅ Browser console shows no critical JavaScript errors

### Performance Benchmarks (User Observable)
- Initial connection: Should establish within 10 seconds
- Telemetry update rate: 1-2 seconds per update cycle
- UI responsiveness: Button clicks respond within 200ms
- Page load time: Complete interface load within 5 seconds

---

## Common Issues and Troubleshooting

### Agent Issues (Application Startup)

#### Application Won't Start
**Symptoms**: Python errors, import failures, port conflicts in terminal
**Agent Solutions**: 
- Check Python dependencies: `pip install -r requirements.txt`
- Verify port 5001 availability: `netstat -ln | grep :5001`
- Check .env file configuration
- Ensure proper Python environment activation
- Kill conflicting processes using port 5001

#### Configuration Problems
**Symptoms**: Missing or incorrect .env file, MAVLINK_HOST not found
**Agent Solutions**:
- Verify .env file exists in project root
- Check MAVLINK_HOST setting is properly configured
- Validate IP address format in .env file

### User Issues (Browser Interface)

#### Web Interface Won't Load
**Symptoms**: Browser shows "can't connect" or "site not reachable"
**User Solutions**:
- Verify you're using the exact URL provided by agent
- Try refreshing the browser page (F5)
- Check if other websites work (test internet connection)
- Try a different browser (Chrome, Firefox, Edge)
- Clear browser cache and cookies

#### Connection Fails in Browser
**Symptoms**: "Connection timeout" or "Connection failed" messages in interface
**User Actions**:
- Report the exact error message to the agent
- Check browser console (F12) for additional errors
- Try connecting again after waiting 30 seconds
- Verify the IP address you entered matches what agent provided

#### No Telemetry Data Display
**Symptoms**: Connected status shows but no data updates in interface
**User Actions**:
- Wait 30 seconds for initial data sync
- Check browser console (F12) for WebSocket errors
- Try refreshing the page while staying connected
- Report console errors to agent for analysis

#### UI Performance Issues
**Symptoms**: Slow updates, unresponsive buttons, lag
**User Solutions**:
- Check browser console (F12) for JavaScript errors
- Close other browser tabs to free memory
- Try using a different browser
- Check if your computer is low on memory/CPU
- Report persistent issues to agent

#### Map Not Loading
**Symptoms**: Blank map area, missing tiles
**User Solutions**:
- Verify your internet connection works for other sites
- Check browser console (F12) for network errors
- Clear browser cache and cookies
- Try zooming in/out to trigger tile refresh
- Try refreshing the entire page (F5)

---

## Advanced Testing Scenarios (User-Performed)

### Multi-Browser Testing
1. Open the WebGCS URL in multiple browser tabs simultaneously
2. Test connecting in one tab while another is already connected
3. Verify data displays consistently across different tabs
4. Check if disconnecting in one tab affects others

### Mobile Device Testing
1. Access the WebGCS URL on your mobile device browser
2. Test touch interactions with buttons and form fields
3. Verify interface adapts to smaller screen sizes
4. Check if all functionality works on mobile browsers

### Extended Duration Testing
1. Keep the connection active for 30+ minutes
2. Monitor if performance degrades over time
3. Watch for any memory issues in browser (check Task Manager)
4. Test if connection remains stable during extended use

### Network Condition Testing
1. Test connecting while on slower WiFi networks
2. Temporarily turn WiFi on/off to test reconnection
3. Observe how interface handles intermittent connectivity
4. Check if automatic reconnection works properly

**Note**: For all advanced scenarios, report any issues or unusual behavior to the agent for investigation.

---

## Test Documentation Template

### Test Session Information
- **Date**: ________________
- **User/Tester**: _______________  
- **Agent Used**: _______________
- **Browser**: ______________
- **Operating System**: _____
- **Drone/SITL Type**: ______

### Agent Success Checklist
- [ ] Application startup successful (no terminal errors)
- [ ] .env configuration read successfully
- [ ] MAVLINK_HOST IP provided to user
- [ ] Application accessible at http://127.0.0.1:5001
- [ ] Agent provided proper troubleshooting guidance

### User Testing Checklist
- [ ] Web interface loaded successfully in browser
- [ ] Connection configuration completed using agent-provided IP
- [ ] MAVLink connection established through web interface
- [ ] Telemetry data visible and updating in browser
- [ ] All UI elements functional and responsive
- [ ] Error handling appropriate for user actions
- [ ] Clean disconnect completed in browser

### Issues Found
| Issue | Responsibility | Severity | Steps to Reproduce | Expected vs Actual |
|-------|---------------|----------|-------------------|-------------------|
|       | Agent/User    |          |                   |                   |

### Communication Notes
_Record of agent guidance provided and user feedback_

### Additional Notes
_Space for additional observations, performance notes, or suggestions_

---

## Validation Checklist for Release Testing

### Agent Validation
- [ ] Application starts consistently without errors
- [ ] Configuration reading works reliably
- [ ] Agent provides clear, helpful guidance
- [ ] Troubleshooting assistance is effective

### User Experience Validation  
- [ ] All user manual test steps pass without critical issues
- [ ] Performance meets established benchmarks from user perspective
- [ ] Error handling provides clear feedback to users
- [ ] User interface is intuitive and responsive
- [ ] Cross-browser compatibility verified by users
- [ ] Network resilience tested from user perspective

### Overall System Validation
- [ ] Agent-user collaboration works effectively
- [ ] Role separation is clear and functional
- [ ] Documentation accurate and complete
- [ ] Security considerations addressed

This manual testing guide ensures thorough validation of WebGCS functionality through a collaborative approach where agents handle application management and users perform comprehensive browser-based testing, providing systematic coverage while maintaining clear role separation.
# WebGCS Test Automation Prompt

## Objective
Launch the WebGCS application, open a browser, configure the drone connection from .env settings, and click the connect button to establish a connection using MCP browser tools.

## Step-by-Step Tasks

### 1. Environment Setup
- Read the `.env` file to get the MAVLINK_HOST configuration using the Read tool
- Store the MAVLINK_HOST value for later use

### 2. Launch WebGCS Application
- Start `app.py` in the background using Bash tool with `run_in_background: true`
- Monitor output with BashOutput to confirm "Running on http://127.0.0.1:5000"
- Keep track of the bash_id for cleanup later

### 3. Navigate to WebGCS Interface
- Use `mcp__browser-mcp__navigate` to open http://127.0.0.1:5000
- Allow 2-3 seconds for page to fully load
- Use `mcp__browser-mcp__screenshot` to capture initial state

### 4. Configure Drone Connection
- Use `mcp__browser-mcp__wait` to ensure the IP input field is present
- Use `mcp__browser-mcp__fill` to enter the MAVLINK_HOST value into the drone IP field
  - Target selector: `#drone-ip` or similar input field
- Verify the value was entered correctly

### 5. Click Connect Button
- Use `mcp__browser-mcp__wait` to ensure connect button is ready
- Use `mcp__browser-mcp__click` to click the Connect button
  - Target selector: `#connect-btn` or button with "Connect" text
- Wait 2-3 seconds for connection to establish

### 6. Verify Connection
- Use `mcp__browser-mcp__evaluate` to check connection status element text
- Look for "Connected" status or similar confirmation
- Check for telemetry data presence (GPS, battery, attitude indicators)
- Use `mcp__browser-mcp__screenshot` to capture connected state

### 7. Cleanup
- Use `mcp__browser-mcp__screenshot` for final documentation
- Use `mcp__browser-mcp__close` to close the browser
- Use KillBash with the saved bash_id to terminate app.py
- Report test results with connection status

## MCP Browser Tools Available

### Tool List
- `mcp__browser-mcp__navigate` - Navigate to URLs
- `mcp__browser-mcp__click` - Click on page elements
- `mcp__browser-mcp__fill` - Fill input fields with text
- `mcp__browser-mcp__evaluate` - Execute JavaScript in browser context
- `mcp__browser-mcp__screenshot` - Capture screenshots
- `mcp__browser-mcp__wait` - Wait for elements to appear
- `mcp__browser-mcp__close` - Close browser window

## Example MCP Tool Usage Flow

### 1. Reading Configuration
```
Use Read tool:
- file_path: ".env"
- Extract MAVLINK_HOST value (e.g., "127.0.0.1" or "192.168.1.100")
```

### 2. Starting Application
```
Use Bash tool:
- command: "python app.py"
- run_in_background: true
- Store returned bash_id for later cleanup
```

### 3. Browser Navigation
```
Use mcp__browser-mcp__navigate:
- url: "http://127.0.0.1:5000"
```

### 4. Filling Input Field
```
Use mcp__browser-mcp__fill:
- selector: "#drone-ip" (or appropriate selector from index.html)
- value: <MAVLINK_HOST from .env>
```

### 5. Clicking Connect
```
Use mcp__browser-mcp__click:
- selector: "#connect-btn" (or button containing "Connect")
```

### 6. Verifying Connection
```
Use mcp__browser-mcp__evaluate:
- script: "document.querySelector('#connection-status').textContent"
- Check if result contains "Connected"
```

### 7. Capturing Result
```
Use mcp__browser-mcp__screenshot:
- filename: "connection-test-result.png"
```

## Expected Results
- WebGCS application starts successfully
- Browser opens and loads the interface
- Drone IP is configured from .env
- Connect button is clicked
- Connection established with drone/SITL
- Telemetry data begins flowing

## Error Handling
- Check if port 5000 is already in use before starting app.py
- Use BashOutput to monitor app.py startup errors
- Capture screenshots at each step for debugging failures
- Use try/catch patterns around MCP tool calls
- Log all errors with clear descriptions
- Implement timeout logic for connection attempts

## Implementation Notes
- Element selectors should be verified from index.html first
- Use mcp__browser-mcp__wait before interacting with elements
- Allow time for WebSocket connection to establish after clicking connect
- MCP browser tools handle browser lifecycle automatically
- Screenshots are saved to project directory by default
- Consider testing with both local (127.0.0.1) and remote drone IPs

## Advantages of MCP Browser Tools
- No external dependencies (Selenium, ChromeDriver, etc.)
- Built-in browser management and lifecycle
- Direct integration with Claude Code
- Simplified error handling
- Consistent API across different browsers
- Automatic cleanup on completion
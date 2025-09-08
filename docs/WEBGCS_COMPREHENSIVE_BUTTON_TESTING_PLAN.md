# WebGCS Comprehensive Button Testing Plan

## Overview
This document outlines comprehensive automated testing for all buttons in the WebGCS web interface. Each button has its own dedicated test file that verifies functionality, UI updates, and server responses.

## Identified Buttons

### Main Interface (index.html)
| Category | Button ID | Button Text | Test File | Description |
|----------|-----------|-------------|-----------|-------------|
| **Connection** | `connect-btn` | Connect | `test_connect_button.py` | Connect to drone |
| **Connection** | `disconnect-btn` | Disconnect | `test_disconnect_functionality.py` | ✅ ALREADY EXISTS |
| **Flight Controls** | `arm-btn` | ARM | `test_arm_button.py` | Arm the drone |
| **Flight Controls** | `disarm-btn` | DISARM | `test_disarm_button.py` | Disarm the drone |
| **Flight Controls** | `takeoff-btn` | Takeoff | `test_takeoff_button.py` | Initiate takeoff |
| **Flight Controls** | `land-btn` | Land | `test_land_button.py` | Initiate landing |
| **Flight Controls** | `rtl-btn` | RTL | `test_rtl_button.py` | Return to launch |
| **Mode Control** | `set-mode-btn` | Set Mode | `test_set_mode_button.py` | Change flight mode |
| **Navigation** | `goto-btn` | Go To | `test_goto_button.py` | Navigate to coordinates |
| **Navigation** | `clear-nav-btn` | Clear | `test_clear_nav_button.py` | Clear navigation |
| **Mission/Fence** | `request-fence-btn` | Request Fence | `test_request_fence_button.py` | Request geofence |
| **Mission/Fence** | `request-mission-btn` | Request Mission | `test_request_mission_button.py` | Request mission |
| **Map Controls** | `center-map-btn` | Center Map | `test_center_map_button.py` | Center map on drone |
| **Map Controls** | `fly-to-toggle` | Fly To: OFF/ON | `test_fly_to_toggle_button.py` | Toggle fly-to mode |
| **Offline Maps** | `offline-maps-toggle` | 📡 Offline Maps | `test_offline_maps_toggle_button.py` | Open offline maps panel |
| **Offline Maps** | `close-offline-panel` | × | `test_close_offline_panel_button.py` | Close offline maps panel |
| **Offline Maps** | `use-current-view` | Use Current Map View | `test_use_current_view_button.py` | Set map view for download |
| **Offline Maps** | `download-tiles-btn` | Download Tiles | `test_download_tiles_button.py` | Start tile download |
| **Offline Maps** | `stop-download-btn` | Stop Download | `test_stop_download_button.py` | Stop tile download |
| **Offline Maps** | `clear-cache-btn` | Clear Cache | `test_clear_cache_button.py` | Clear offline cache |
| **Confirmation** | `confirm-yes` | Yes | `test_confirm_yes_button.py` | Confirm dialog yes |
| **Confirmation** | `confirm-no` | No | `test_confirm_no_button.py` | Confirm dialog no |

### MAVLink Dump Page (mavlink_dump.html)  
| Category | Button ID | Button Text | Test File | Description |
|----------|-----------|-------------|-----------|-------------|
| **Debug Tools** | `pauseBtn` | Pause/Resume | `test_mavlink_pause_button.py` | Pause/resume MAVLink stream |
| **Debug Tools** | N/A | Clear | `test_mavlink_clear_button.py` | Clear MAVLink messages |
| **Debug Tools** | N/A | Export | `test_mavlink_export_button.py` | Export MAVLink messages |

## Test Execution Plan

### Phase 1: Critical Flight Safety Buttons (Priority 1)
```bash
# Connection buttons
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_connect_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_disconnect_functionality.py

# Critical flight controls
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_arm_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_disarm_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_takeoff_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_land_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_rtl_button.py
```

### Phase 2: Navigation and Mission Control (Priority 2)
```bash
# Navigation controls
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_goto_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_clear_nav_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_set_mode_button.py

# Mission and fence
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_request_fence_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_request_mission_button.py
```

### Phase 3: Map Controls (Priority 3)
```bash
# Map functionality
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_center_map_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_fly_to_toggle_button.py
```

### Phase 4: Offline Maps (Priority 4)
```bash
# Offline maps panel
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_offline_maps_toggle_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_close_offline_panel_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_use_current_view_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_download_tiles_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_stop_download_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_clear_cache_button.py
```

### Phase 5: UI Components (Priority 5)
```bash
# Confirmation dialogs
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_confirm_yes_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_confirm_no_button.py
```

### Phase 6: Debug Tools (Priority 6)
```bash
# MAVLink debug page
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_mavlink_pause_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_mavlink_clear_button.py
PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5 uv run python test_mavlink_export_button.py
```

## Run All Tests Script
```bash
#!/bin/bash
# Run all WebGCS button tests

echo "🧪 WebGCS Comprehensive Button Testing"
echo "======================================"

export PYTHONPATH=/Users/peterburke/Documents/Code/WebGCS5

# Phase 1: Critical Safety
echo "Phase 1: Critical Flight Safety Buttons"
uv run python test_connect_button.py
uv run python test_disconnect_functionality.py
uv run python test_arm_button.py
uv run python test_disarm_button.py
uv run python test_takeoff_button.py
uv run python test_land_button.py
uv run python test_rtl_button.py

# Phase 2: Navigation
echo "Phase 2: Navigation and Mission Control"
uv run python test_goto_button.py
uv run python test_clear_nav_button.py
uv run python test_set_mode_button.py
uv run python test_request_fence_button.py
uv run python test_request_mission_button.py

# Phase 3: Map Controls  
echo "Phase 3: Map Controls"
uv run python test_center_map_button.py
uv run python test_fly_to_toggle_button.py

# Phase 4: Offline Maps
echo "Phase 4: Offline Maps"
uv run python test_offline_maps_toggle_button.py
uv run python test_close_offline_panel_button.py
uv run python test_use_current_view_button.py
uv run python test_download_tiles_button.py
uv run python test_stop_download_button.py
uv run python test_clear_cache_button.py

# Phase 5: UI Components
echo "Phase 5: UI Components"
uv run python test_confirm_yes_button.py
uv run python test_confirm_no_button.py

# Phase 6: Debug Tools
echo "Phase 6: Debug Tools"
uv run python test_mavlink_pause_button.py
uv run python test_mavlink_clear_button.py
uv run python test_mavlink_export_button.py

echo "🎉 All tests completed!"
```

## Test Results Tracking
Each test will generate a JSON report file with the pattern: `{button_name}_test_results.json`

## Success Criteria
For each button test to pass, it must verify:
1. ✅ Button is clickable
2. ✅ Expected UI changes occur  
3. ✅ Appropriate SocketIO events are sent (if applicable)
4. ✅ Server responds correctly (if applicable)
5. ✅ Console shows expected messages
6. ✅ No JavaScript errors occur

## Prerequisites
- WebGCS server running on localhost:5001
- Chrome browser available
- Virtual drone simulator available (for flight control tests)
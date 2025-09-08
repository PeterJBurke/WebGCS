#!/bin/bash
# WebGCS Comprehensive Button Testing Suite
# Run all automated tests for WebGCS buttons

set -e  # Exit on any error

echo "🧪 WebGCS Comprehensive Button Testing Suite"
echo "============================================"
echo "Testing all buttons in the WebGCS interface"
echo ""

# Set environment
export PYTHONPATH="/Users/peterburke/Documents/Code/WebGCS5"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Function to run a test
run_test() {
    local test_file="$1"
    local test_name="$2"
    
    echo -e "${BLUE}Running: $test_name${NC}"
    echo "----------------------------------------"
    
    if [ ! -f "$test_file" ]; then
        echo -e "${YELLOW}⚠️  SKIPPED: $test_file not found${NC}"
        SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        echo ""
        return
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if uv run python "$test_file"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

echo "🔗 Phase 1: Critical Flight Safety Buttons"
echo "==========================================="
run_test "test_connect_button.py" "Connect Button Test"
run_test "test_disconnect_functionality.py" "Disconnect Button Test"
run_test "test_arm_button.py" "ARM Button Test"
run_test "test_disarm_button.py" "DISARM Button Test"
run_test "test_takeoff_button.py" "Takeoff Button Test"
run_test "test_land_button.py" "Land Button Test"
run_test "test_rtl_button.py" "RTL Button Test"

echo "🧭 Phase 2: Navigation and Mission Control"
echo "=========================================="
run_test "test_goto_button.py" "Go To Button Test"
run_test "test_clear_nav_button.py" "Clear Navigation Button Test"
run_test "test_set_mode_button.py" "Set Mode Button Test"
run_test "test_request_fence_button.py" "Request Fence Button Test"
run_test "test_request_mission_button.py" "Request Mission Button Test"

echo "🗺️  Phase 3: Map Controls"
echo "========================"
run_test "test_center_map_button.py" "Center Map Button Test"
run_test "test_fly_to_toggle_button.py" "Fly To Toggle Button Test"

echo "📡 Phase 4: Offline Maps"
echo "======================="
run_test "test_offline_maps_toggle_button.py" "Offline Maps Toggle Test"
run_test "test_close_offline_panel_button.py" "Close Offline Panel Test"
run_test "test_use_current_view_button.py" "Use Current View Test"
run_test "test_download_tiles_button.py" "Download Tiles Test"
run_test "test_stop_download_button.py" "Stop Download Test"
run_test "test_clear_cache_button.py" "Clear Cache Test"

echo "💬 Phase 5: UI Components"
echo "========================"
run_test "test_confirm_yes_button.py" "Confirm Yes Button Test"
run_test "test_confirm_no_button.py" "Confirm No Button Test"

echo "🐛 Phase 6: Debug Tools"
echo "======================"
run_test "test_mavlink_pause_button.py" "MAVLink Pause Button Test"
run_test "test_mavlink_clear_button.py" "MAVLink Clear Button Test"
run_test "test_mavlink_export_button.py" "MAVLink Export Button Test"

# Print summary
echo "================================================"
echo "🎉 TESTING COMPLETE - SUMMARY REPORT"
echo "================================================"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
fi

echo ""
echo "📊 Test Results:"
echo "  Total Tests:   $TOTAL_TESTS"
echo -e "  ${GREEN}Passed:        $PASSED_TESTS${NC}"
echo -e "  ${RED}Failed:        $FAILED_TESTS${NC}"
echo -e "  ${YELLOW}Skipped:       $SKIPPED_TESTS${NC}"

if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    echo "  Pass Rate:     $PASS_RATE%"
fi

echo ""
echo "📁 Test result files generated:"
echo "  - *_test_results.json (individual test results)"
echo "  - comprehensive_disconnect_test.json (disconnect test)"

# Generate summary report
echo "{" > test_summary_report.json
echo "  \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"," >> test_summary_report.json
echo "  \"total_tests\": $TOTAL_TESTS," >> test_summary_report.json
echo "  \"passed_tests\": $PASSED_TESTS," >> test_summary_report.json
echo "  \"failed_tests\": $FAILED_TESTS," >> test_summary_report.json
echo "  \"skipped_tests\": $SKIPPED_TESTS," >> test_summary_report.json
if [ $TOTAL_TESTS -gt 0 ]; then
    echo "  \"pass_rate\": $PASS_RATE," >> test_summary_report.json
else
    echo "  \"pass_rate\": 0," >> test_summary_report.json
fi
echo "  \"all_tests_passed\": $([ $FAILED_TESTS -eq 0 ] && echo true || echo false)" >> test_summary_report.json
echo "}" >> test_summary_report.json

echo "📋 Summary report saved to: test_summary_report.json"

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi
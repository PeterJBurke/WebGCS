#!/bin/bash
# WebGCS Test Runner Script
# Executes comprehensive test suite with proper error handling and reporting

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_TIMEOUT=300  # 5 minutes max per test
PERFORMANCE_MESSAGES=1000

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}WebGCS Test Suite - Comprehensive Validation${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""

# Function to run a single test with proper error handling
run_test() {
    local test_file="$1"
    local test_name="$2"
    
    echo -e "${YELLOW}Running $test_name...${NC}"
    
    if timeout $TEST_TIMEOUT uv run pytest "$test_file" -v -s; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        return 1
    fi
}

# Function to run performance benchmark
run_benchmark() {
    local benchmark_type="$1"
    
    echo -e "${YELLOW}Running Performance Benchmark ($benchmark_type)...${NC}"
    
    if uv run python compare_timing.py --$benchmark_type --messages $PERFORMANCE_MESSAGES; then
        echo -e "${GREEN}✅ Benchmark ($benchmark_type) completed${NC}"
        return 0
    else
        echo -e "${RED}❌ Benchmark ($benchmark_type) failed${NC}"
        return 1
    fi
}

# Test execution counters
passed_tests=0
failed_tests=0
skipped_tests=0

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" && ! -f ".venv/pyvenv.cfg" ]]; then
    echo -e "${RED}Warning: Virtual environment not detected. Tests may fail.${NC}"
    echo "Run 'uv sync' to set up the environment."
    echo ""
fi

echo -e "${BLUE}PHASE 1: MAVLink Foundation Tests${NC}"
echo "================================================="

# TEST-001: Basic MAVLink Connection
if [[ -f "tests/test_001_basic_connection.py" ]]; then
    if run_test "tests/test_001_basic_connection.py" "TEST-001: Basic MAVLink Connection"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-001 not found - skipping${NC}"
    ((skipped_tests++))
fi

# TEST-002: Heartbeat Reception
if [[ -f "tests/test_002_heartbeat_reception.py" ]]; then
    if run_test "tests/test_002_heartbeat_reception.py" "TEST-002: Heartbeat Reception"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-002 not found - skipping${NC}"
    ((skipped_tests++))
fi

# TEST-003: Message Processing
if [[ -f "tests/test_003_message_processing.py" ]]; then
    if run_test "tests/test_003_message_processing.py" "TEST-003: Message Processing"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-003 not found - skipping${NC}"
    ((skipped_tests++))
fi

echo ""
echo -e "${BLUE}PHASE 2: Web Interface Tests${NC}"
echo "================================================="

# TEST-004: Flask Server
if [[ -f "tests/test_004_flask_server.py" ]]; then
    if run_test "tests/test_004_flask_server.py" "TEST-004: Flask Server Startup"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-004 not found - skipping${NC}"
    ((skipped_tests++))
fi

# TEST-005: SocketIO Connection
if [[ -f "tests/test_005_socketio_connection.py" ]]; then
    if run_test "tests/test_005_socketio_connection.py" "TEST-005: SocketIO Connection"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-005 not found - skipping${NC}"
    ((skipped_tests++))
fi

# TEST-006: Flight Command Execution
if [[ -f "tests/test_006_flight_command_execution.py" ]]; then
    if run_test "tests/test_006_flight_command_execution.py" "TEST-006: Flight Command Execution"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-006 not found - skipping${NC}"
    ((skipped_tests++))
fi

echo ""
echo -e "${BLUE}PHASE 3: Performance Tests${NC}"
echo "================================================="

# TEST-007: Logging Performance
if [[ -f "tests/test_007_logging_performance.py" ]]; then
    echo -e "${YELLOW}Running TEST-007: Logging Performance...${NC}"
    
    if timeout $TEST_TIMEOUT uv run pytest "tests/test_007_logging_performance.py" -v -s; then
        echo -e "${GREEN}✅ TEST-007: Logging Performance PASSED${NC}"
        ((passed_tests++))
        
        # Run performance benchmarks if test passes
        echo ""
        echo -e "${BLUE}Running Performance Benchmarks...${NC}"
        run_benchmark "compare"
        
    else
        echo -e "${RED}❌ TEST-007: Logging Performance FAILED (Expected in RED phase)${NC}"
        echo "This failure is expected until high_performance_logger.py is implemented."
        ((failed_tests++))
        
        # Still run baseline benchmark to show current performance
        echo ""
        echo -e "${BLUE}Running Baseline Performance Benchmark...${NC}"
        run_benchmark "baseline-only"
    fi
else
    echo -e "${YELLOW}⚠️  TEST-007 not found - skipping${NC}"
    ((skipped_tests++))
fi

# TEST-008: Telemetry Latency
if [[ -f "tests/test_008_telemetry_latency.py" ]]; then
    if run_test "tests/test_008_telemetry_latency.py" "TEST-008: Telemetry Latency"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-008 not found - skipping${NC}"
    ((skipped_tests++))
fi

echo ""
echo -e "${BLUE}PHASE 4: Safety & Integration Tests${NC}"
echo "================================================="

# TEST-009: Command Safety
if [[ -f "tests/test_009_command_safety.py" ]]; then
    if run_test "tests/test_009_command_safety.py" "TEST-009: Command Safety"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-009 not found - skipping${NC}"
    ((skipped_tests++))
fi

# TEST-010: End-to-End Integration
if [[ -f "tests/test_010_integration.py" ]]; then
    if run_test "tests/test_010_integration.py" "TEST-010: End-to-End Integration"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  TEST-010 not found - skipping${NC}"
    ((skipped_tests++))
fi

echo ""
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}TEST SUITE SUMMARY${NC}"
echo -e "${BLUE}=================================================${NC}"

total_tests=$((passed_tests + failed_tests + skipped_tests))
echo "Total tests: $total_tests"
echo -e "${GREEN}Passed: $passed_tests${NC}"
echo -e "${RED}Failed: $failed_tests${NC}"
echo -e "${YELLOW}Skipped: $skipped_tests${NC}"

# Calculate pass rate
if [[ $total_tests -gt 0 ]]; then
    pass_rate=$(( (passed_tests * 100) / total_tests ))
    echo "Pass rate: $pass_rate%"
fi

echo ""

# Determine exit status and provide guidance
if [[ $failed_tests -eq 0 ]]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! System ready for deployment.${NC}"
    exit 0
elif [[ $passed_tests -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Some tests failed. Review failures and implement missing components.${NC}"
    
    # Provide specific guidance based on common failures
    if [[ -f "tests/test_007_logging_performance.py" ]]; then
        if ! uv run python -c "from high_performance_logger import HighPerformanceLogger" &>/dev/null; then
            echo ""
            echo -e "${YELLOW}Next Steps:${NC}"
            echo "1. Implement high_performance_logger.py to pass TEST-007"
            echo "2. Ensure <1ms latency requirement is met"
            echo "3. Implement thread-safe circular buffer logging"
            echo "4. Add memory optimization and log rotation"
        fi
    fi
    
    exit 1
else
    echo -e "${RED}❌ NO TESTS PASSED. Check test environment and dependencies.${NC}"
    exit 2
fi
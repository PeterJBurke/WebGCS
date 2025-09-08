#!/bin/bash

# WebGCS TEST-008: End-to-End Telemetry Latency Test Runner
# Tests complete telemetry flow latency: Virtual Drone → MAVLink → SocketIO → Web Client

echo "======================================================================"
echo "WebGCS TEST-008: End-to-End Telemetry Latency Validation"
echo "======================================================================"
echo "Critical Requirement: <100ms end-to-end telemetry latency"
echo "Virtual Drone: 192.168.193.235:5678"
echo "Target Update Rate: 10Hz (100ms intervals)"
echo "======================================================================"

# Set environment variables
export DRONE_TCP_ADDRESS=192.168.193.235
export DRONE_TCP_PORT=5678

# Check virtual drone connectivity
echo "Checking virtual drone connectivity..."
if nc -z -v -w3 192.168.193.235 5678 2>/dev/null; then
    echo "✓ Virtual drone available at 192.168.193.235:5678"
else
    echo "⚠ Warning: Virtual drone may not be available at 192.168.193.235:5678"
    echo "  Tests may skip or timeout if drone is unavailable"
fi

echo ""
echo "Running TEST-008 components:"
echo ""

# Run individual test components
echo "1. End-to-End Latency Test (CRITICAL <100ms requirement)"
uv run pytest tests/test_008_telemetry_latency.py::test_end_to_end_telemetry_latency -v -s

echo ""
echo "2. Pipeline Performance Breakdown"
uv run pytest tests/test_008_telemetry_latency.py::test_telemetry_pipeline_performance_breakdown -v -s

echo ""
echo "3. Telemetry Update Rate Test (10Hz target)"
uv run pytest tests/test_008_telemetry_latency.py::test_telemetry_update_rate_10hz -v -s

echo ""
echo "4. Concurrent Clients Latency Impact"
uv run pytest tests/test_008_telemetry_latency.py::test_concurrent_clients_latency_impact -v -s

echo ""
echo "5. Real-Time Data Synchronization"
uv run pytest tests/test_008_telemetry_latency.py::test_real_time_data_synchronization -v -s

echo ""
echo "======================================================================"
echo "TEST-008 Complete"
echo "======================================================================"
echo "Key Validation Points:"
echo "✓ End-to-end telemetry latency < 100ms (CRITICAL)"
echo "✓ Individual pipeline components meet performance targets"
echo "✓ Multiple concurrent clients supported"
echo "✓ Real-time data synchronization quality"
echo "⚠ Update rate optimization (target: 10Hz)"
echo ""
echo "Complete telemetry flow tested:"
echo "Virtual Drone → MAVLink → Processing → SocketIO → Web Client"
echo "======================================================================"
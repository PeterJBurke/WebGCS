#!/bin/bash

# WebGCS Cloud Server Deployment Script
# This script pulls the latest code from GitHub and restarts the WebGCS service

echo "=== WebGCS Cloud Deployment Script ==="
echo "Timestamp: $(date)"
echo

# Navigate to WebGCS directory (adjust path as needed for your cloud server)
cd /path/to/WebGCS || { echo "Error: WebGCS directory not found. Please update the path in this script."; exit 1; }

echo "Current directory: $(pwd)"
echo

# Stop the current WebGCS service if running
echo "Stopping WebGCS service..."
pkill -f "python.*app.py" || echo "No WebGCS process found running"
sleep 2

# Pull latest changes from GitHub
echo "Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main
echo "Code updated to latest version"
echo

# Show the latest commit info
echo "Latest commit:"
git log -1 --oneline
echo

# Install/update dependencies if requirements.txt changed
if git diff HEAD~1 HEAD --name-only | grep -q requirements.txt; then
    echo "Requirements.txt changed, updating dependencies..."
    pip install -r requirements.txt
else
    echo "No dependency changes detected"
fi
echo

# Start WebGCS service in background
echo "Starting WebGCS service..."
nohup python app.py > webgcs.log 2>&1 &
sleep 3

# Check if service started successfully
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ WebGCS service started successfully"
    echo "Process ID: $(pgrep -f 'python.*app.py')"
    echo "Log file: webgcs.log"
    echo "Service should be available at: http://localhost:5001"
else
    echo "❌ Failed to start WebGCS service"
    echo "Check webgcs.log for errors:"
    tail -20 webgcs.log
    exit 1
fi

echo
echo "=== Deployment Complete ==="
echo "To monitor logs: tail -f webgcs.log"
echo "To stop service: pkill -f 'python.*app.py'"

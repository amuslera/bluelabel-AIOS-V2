#!/bin/bash

# Start API server in background
echo "Starting Bluelabel AIOS API in background..."

# Make sure we're in the right directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Kill any existing API server on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Start the minimal API in background
nohup python3 apps/api/main_minimal.py > api.log 2>&1 &

# Store the PID
echo $! > api.pid

# Wait a moment for server to start
sleep 3

# Check if it's running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "API server started successfully!"
    echo "PID: $(cat api.pid)"
    echo "Logs: tail -f api.log"
    echo "Stop: kill $(cat api.pid)"
else
    echo "Failed to start API server. Check api.log for errors."
fi
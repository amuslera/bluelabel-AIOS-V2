#!/bin/bash

echo "Starting Bluelabel AIOS V2..."

# Start the API server
echo "Starting API server..."
cd /Users/arielmuslera/Development/Projects/bluelabel-AIOS-V2
source .venv/bin/activate
PYTHONPATH=/Users/arielmuslera/Development/Projects/bluelabel-AIOS-V2 python -m uvicorn apps.api.main:app --reload --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API server..."
sleep 3

# Start the UI
echo "Starting UI..."
cd apps/ui
./start.sh

# Keep the script running
echo ""
echo "============================================"
echo "Bluelabel AIOS V2 is running!"
echo "API: http://localhost:8000"
echo "UI:  http://localhost:3000"
echo "Press Ctrl+C to stop all services"
echo "============================================"

# Wait for Ctrl+C
trap "kill $API_PID; exit" INT
wait
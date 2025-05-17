#!/bin/bash

# Start API server with enhanced logging
echo "Starting Bluelabel AIOS API with logging..."

# Make sure we're in the right directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Set environment variables
export LOG_LEVEL="INFO"
export DEBUG="true"
export ENVIRONMENT="development"

# Kill any existing API server on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Create logs directory
mkdir -p logs

# Start the API with logging
echo "Starting API server with enhanced logging..."
nohup python3 apps/api/main_with_logging.py > logs/startup.log 2>&1 &

# Store the PID
echo $! > api.pid

# Wait for server to start
sleep 3

# Check if it's running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "API server started successfully!"
    echo "PID: $(cat api.pid)"
    echo ""
    echo "📋 Log files:"
    echo "  - API logs: tail -f logs/api.log"
    echo "  - Startup logs: tail -f logs/startup.log"
    echo ""
    echo "🔍 View logs in JSON format:"
    echo "  cat logs/api.log | jq '.'"
    echo ""
    echo "🛑 Stop server:"
    echo "  kill $(cat api.pid)"
else
    echo "Failed to start API server. Check logs/startup.log for errors."
    cat logs/startup.log
fi
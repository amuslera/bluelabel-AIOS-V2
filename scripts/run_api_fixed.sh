#!/bin/bash

# Start the API server with fixed imports
echo "Starting Bluelabel AIOS v2 API (Fixed)..."

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Export environment variables
export API_DEBUG=true
export LOG_LEVEL=INFO
export REDIS_SIMULATION_MODE=true
export LLM_ENABLED=false
export JWT_SECRET_KEY=development-secret-key-change-in-production

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the server
echo "Running fixed API..."
python -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
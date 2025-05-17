#!/bin/bash

# Start the minimal API server
echo "Starting Bluelabel AIOS v2 Minimal API..."

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Export environment variables
export API_DEBUG=true
export LOG_LEVEL=INFO
export REDIS_SIMULATION_MODE=true
export LLM_ENABLED=false

# Start the minimal server
echo "Running minimal API..."
python -m uvicorn apps.api.main_minimal:app --reload --host 0.0.0.0 --port 8000
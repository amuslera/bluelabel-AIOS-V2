#!/bin/bash

# Start minimal API server
echo "Starting Bluelabel AIOS Minimal API..."

# Make sure we're in the right directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the minimal API
python apps/api/main_minimal.py

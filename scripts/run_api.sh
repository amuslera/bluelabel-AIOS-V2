#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Run the API server
echo "Starting Bluelabel AIOS v2 API server..."
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

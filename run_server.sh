#!/bin/bash
# Simple script to run the development server with proper environment

# Navigate to project directory
cd "$(dirname "$0")"

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Set environment variables
export REDIS_SIMULATION_MODE=true
export LOG_LEVEL=INFO
export API_DEBUG=true

# Run the server
echo "Starting Bluelabel AIOS v2 Development Server"
echo "============================================="
echo "API Documentation: http://localhost:8000/docs"
echo "Alternative Docs: http://localhost:8000/redoc"
echo "Health Check: http://localhost:8000/health"
echo "Agent API: http://localhost:8000/api/v1/agents/"
echo ""
echo "Press CTRL+C to stop the server"
echo "============================================="

# Use the virtual environment's Python
exec python3 scripts/run_development.py
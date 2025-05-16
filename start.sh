#!/bin/bash
# Comprehensive startup script for Bluelabel AIOS v2

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Navigate to project directory
cd "$(dirname "$0")"

echo -e "${GREEN}Starting Bluelabel AIOS v2${NC}"
echo "================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating it...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Dependencies not installed. Installing...${NC}"
    pip install -r requirements.txt
fi

# Set environment variables
export REDIS_SIMULATION_MODE=true
export LOG_LEVEL=INFO
export API_DEBUG=true

# Clear any existing processes on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}Port 8000 is in use. Killing existing process...${NC}"
    kill -9 $(lsof -ti:8000)
    sleep 1
fi

# Run the server
echo ""
echo -e "${GREEN}Starting Development Server${NC}"
echo "================================"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 Alternative Docs: http://localhost:8000/redoc"
echo "🏥 Health Check:     http://localhost:8000/health"
echo "🤖 Agent API:        http://localhost:8000/api/v1/agents/"
echo ""
echo "Press CTRL+C to stop the server"
echo "================================"
echo ""

# Run with the virtual environment's Python
exec python3 -m uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000
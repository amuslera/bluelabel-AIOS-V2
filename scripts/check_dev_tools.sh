#!/bin/bash
# Quick development environment setup check

echo "=== Development Environment Check ==="
echo

# Check Python
echo "Python version:"
python3 --version
echo

# Check if in virtual environment
echo "Virtual environment:"
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Active: $VIRTUAL_ENV"
else
    echo "✗ Not active. Run: source .venv/bin/activate"
fi
echo

# Check .env file
echo "Environment file:"
if [ -f .env ]; then
    echo "✓ .env file exists"
    echo "  REDIS_SIMULATION_MODE=$(grep REDIS_SIMULATION_MODE .env | cut -d= -f2)"
    echo "  LOG_LEVEL=$(grep LOG_LEVEL .env | cut -d= -f2)"
    echo "  API_DEBUG=$(grep API_DEBUG .env | cut -d= -f2)"
else
    echo "✗ .env file missing"
fi
echo

# Check key directories
echo "Project directories:"
for dir in apps agents services core shared tests scripts logs data; do
    if [ -d "$dir" ]; then
        echo "✓ $dir/"
    else
        echo "✗ $dir/ missing"
    fi
done
echo

# Check if Redis is needed
echo "Redis simulation mode:"
if [ "$REDIS_SIMULATION_MODE" = "true" ]; then
    echo "✓ Enabled (Redis not required)"
else
    echo "  Not set (Redis required unless you export REDIS_SIMULATION_MODE=true)"
fi
echo

# Optional tools
echo "Optional tools:"
which docker > /dev/null 2>&1 && echo "✓ Docker installed" || echo "- Docker not installed (optional)"
which redis-cli > /dev/null 2>&1 && echo "✓ Redis CLI installed" || echo "- Redis CLI not installed (optional)"
which psql > /dev/null 2>&1 && echo "✓ PostgreSQL installed" || echo "- PostgreSQL not installed (optional)"
echo

echo "=== Quick Setup Commands ==="
echo "1. Activate virtual environment:"
echo "   source .venv/bin/activate"
echo
echo "2. Install dependencies:"
echo "   pip install -r requirements.txt"
echo
echo "3. Run API server:"
echo "   python scripts/run_with_logging.py"
echo
echo "4. Or run directly:"
echo "   uvicorn apps.api.main:app --reload"
#!/bin/bash
# Complete development environment setup for Bluelabel AIOS v2

set -e  # Exit on error

echo "Bluelabel AIOS v2 - Development Environment Setup"
echo "================================================"
echo

# Check Python version
echo "1. Checking Python version..."
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$python_version >= 3.9" | bc -l) -eq 1 ]]; then
    echo "✓ Python $python_version"
else
    echo "✗ Python $python_version (requires 3.9+)"
    exit 1
fi
echo

# Create virtual environment
echo "2. Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo

# Upgrade pip
echo "3. Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo

# Install dependencies
echo "4. Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo

# Create necessary directories
echo "5. Creating project directories..."
mkdir -p data/knowledge data/mcp/components data/mcp/templates logs
echo "✓ Directories created"
echo

# Create .env file
echo "6. Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo "  Please update .env with your configuration"
else
    echo "✓ .env file exists"
fi
echo

# Set development defaults in .env
echo "7. Configuring development settings..."
# Enable Redis simulation mode
if ! grep -q "REDIS_SIMULATION_MODE=true" .env; then
    if grep -q "REDIS_SIMULATION_MODE=" .env; then
        sed -i.bak 's/REDIS_SIMULATION_MODE=.*/REDIS_SIMULATION_MODE=true/' .env
    else
        echo "REDIS_SIMULATION_MODE=true" >> .env
    fi
    echo "✓ Enabled Redis simulation mode"
fi

# Set debug mode
if ! grep -q "API_DEBUG=true" .env; then
    if grep -q "API_DEBUG=" .env; then
        sed -i.bak 's/API_DEBUG=.*/API_DEBUG=true/' .env
    else
        echo "API_DEBUG=true" >> .env
    fi
    echo "✓ Enabled API debug mode"
fi

# Set log level
if ! grep -q "LOG_LEVEL=INFO" .env; then
    if grep -q "LOG_LEVEL=" .env; then
        sed -i.bak 's/LOG_LEVEL=.*/LOG_LEVEL=INFO/' .env
    else
        echo "LOG_LEVEL=INFO" >> .env
    fi
    echo "✓ Set log level to INFO"
fi
echo

# Verify setup
echo "8. Verifying setup..."
python3 scripts/verify_setup.py
echo

# Instructions
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo
echo "To start developing:"
echo
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo
echo "2. Start the API server with logging:"
echo "   python3 scripts/run_with_logging.py"
echo
echo "3. Or use uvicorn directly:"
echo "   uvicorn apps.api.main:app --reload"
echo
echo "4. Access the API documentation:"
echo "   http://localhost:8000/docs"
echo
echo "5. Check logs in:"
echo "   logs/bluelabel_aios.log"
echo
echo "Optional: Configure API keys in .env for LLM access"
echo

# Offer to start the server
read -p "Would you like to start the API server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting API server..."
    python3 scripts/run_with_logging.py
fi
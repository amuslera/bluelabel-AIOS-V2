#!/bin/bash

# Simplified setup script for Bluelabel AIOS v2

set -e  # Exit on error

echo "Setting up basic environment for Bluelabel AIOS v2..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/knowledge data/mcp/components data/mcp/templates logs

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ".env file created. Please update it with your configuration."
fi

echo "Basic setup completed successfully!"
echo "To start the API server, run: uvicorn apps.api.main:app --reload"

#!/bin/bash

# Bluelabel AIOS v2 Setup Script
# This script sets up the development environment for the project

set -e  # Exit on error

echo "Setting up Bluelabel AIOS v2 development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    echo "Virtual environment created."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

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

# Create initial MCP components and templates
echo "Creating initial MCP components and templates..."
python -c "
# Create initial MCP components and templates
from services.mcp.prompt_manager import MCPManager

# Initialize MCP manager
mcp = MCPManager()

# Create basic summary component
mcp.create_component(
    name='basic_summary',
    description='Basic content summary component',
    template='Summarize the following content in a concise way:\n\n{{content}}\n\nSummary:',
    version='1.0.0',
    tags=['summary', 'basic']
)

# Create detailed summary component
mcp.create_component(
    name='detailed_summary',
    description='Detailed content summary with key points',
    template='Provide a detailed summary of the following content. Include key points, main arguments, and important details:\n\n{{content}}\n\nDetailed Summary:',
    version='1.0.0',
    tags=['summary', 'detailed']
)

# Create executive summary template
mcp.create_template(
    name='executive_summary',
    description='Executive summary template for content digestion',
    components=[component.id for component in mcp.list_components(tags=['summary'])],
    version='1.0.0',
    tags=['summary', 'executive']
)

print('Initial MCP components and templates created successfully.')
"

echo "Setup completed successfully!"
echo "To start the API server, run: uvicorn apps.api.main:app --reload"
echo "To start Docker services, run: docker-compose up -d"

#!/bin/bash

# Script to run the integrated API that matches frontend expectations

echo "🚀 Starting Bluelabel AIOS Integrated API..."

# Change to project root
cd "$(dirname "$0")/.."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run the integrated API
echo "✅ Starting integrated API server..."
python -m uvicorn apps.api.main_integrated:app --reload --host 0.0.0.0 --port 8000
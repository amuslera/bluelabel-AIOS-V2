#!/bin/bash

# Start the React development server
echo "Starting Bluelabel AIOS UI..."

# Kill any existing processes on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Navigate to the UI directory
cd /Users/arielmuslera/Development/Projects/bluelabel-AIOS-V2/apps/ui

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the development server
echo "Starting development server on http://localhost:3000"
npm start &

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 5

# Check if server is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✓ Server is running!"
    echo "Opening browser..."
    open http://localhost:3000
else
    echo "✗ Server failed to start. Check the logs."
    exit 1
fi

echo "Bluelabel AIOS UI is now running at http://localhost:3000"
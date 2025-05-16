#!/usr/bin/env python3
"""
Run the development server with proper configuration
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up environment variables
os.environ["REDIS_SIMULATION_MODE"] = "true"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["API_DEBUG"] = "true"

# Import after setting env vars
import uvicorn

if __name__ == "__main__":
    print("Starting Bluelabel AIOS v2 Development Server")
    print("=" * 45)
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"Alternative Docs: http://localhost:8000/redoc")
    print(f"Health Check: http://localhost:8000/health")
    print(f"Agent API: http://localhost:8000/api/v1/agents/")
    print("\nPress CTRL+C to stop the server")
    print("=" * 45)
    
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
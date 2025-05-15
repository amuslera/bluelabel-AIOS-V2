#!/usr/bin/env python3
"""Run the API server with logging enabled"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uvicorn
from apps.api.main import app

if __name__ == "__main__":
    # Configure environment
    os.environ["REDIS_SIMULATION_MODE"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["API_DEBUG"] = "true"
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )
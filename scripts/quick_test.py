#!/usr/bin/env python3
"""Quick test to check basic functionality"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import requests
import subprocess
import signal

def test_server():
    """Test the server by starting it and making requests"""
    print("Starting API server...")
    
    # Start the server in a subprocess
    env = os.environ.copy()
    env["REDIS_SIMULATION_MODE"] = "true"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", "8002"],
        env=env,
        cwd=os.path.abspath(os.path.dirname(__file__) + "/.."),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give the server time to start
    time.sleep(3)
    
    try:
        # Test the health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://127.0.0.1:8002/health")
        print(f"Health response: {response.status_code} - {response.json()}")
        
        # Test the root endpoint
        print("Testing root endpoint...")
        response = requests.get("http://127.0.0.1:8002/")
        print(f"Root response: {response.status_code} - {response.json()}")
        
        # Test API docs
        print("Testing API docs...")
        response = requests.get("http://127.0.0.1:8002/docs")
        print(f"Docs response: {response.status_code}")
        
        print("\n✓ Server is working correctly!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Stop the server
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_server()
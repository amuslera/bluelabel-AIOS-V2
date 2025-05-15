#!/usr/bin/env python3
"""Test script to verify logging functionality"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import requests
import time
from core.logging import setup_logging, LogContext, logger

def test_basic_logging():
    """Test basic logging functionality"""
    print("Testing basic logging...")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✓ Basic logging test complete")

def test_context_logging():
    """Test context-aware logging"""
    print("\nTesting context logging...")
    
    # Test with context
    with LogContext(logger, tenant_id="test-tenant", request_id="123"):
        logger.info("This log should have tenant and request context")
    
    print("✓ Context logging test complete")

def test_api_logging():
    """Test API request logging"""
    print("\nTesting API logging...")
    
    # Start the API server
    import subprocess
    env = os.environ.copy()
    env["REDIS_SIMULATION_MODE"] = "true"
    env["LOG_LEVEL"] = "INFO"
    
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "apps.api.main:app", "--host", "127.0.0.1", "--port", "8003"],
        env=env,
        cwd=os.path.abspath(os.path.dirname(__file__) + "/.."),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Give server time to start
    time.sleep(3)
    
    try:
        # Make some requests
        requests.get("http://127.0.0.1:8003/")
        requests.get("http://127.0.0.1:8003/health")
        requests.get("http://127.0.0.1:8003/api/v1/agents")
        
        # Give time for logs to be written
        time.sleep(1)
        
        # Read logs from process output
        output = []
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            output.append(line.strip())
            print(f"Log: {line.strip()}")
            if len(output) > 20:  # Limit output
                break
        
        print("✓ API logging test complete")
        
    finally:
        proc.terminate()
        proc.wait()

def main():
    """Run all logging tests"""
    print("Testing Logging Implementation")
    print("=" * 40)
    
    # Run tests
    test_basic_logging()
    test_context_logging()
    test_api_logging()
    
    print("\n" + "=" * 40)
    print("All logging tests complete!")

if __name__ == "__main__":
    main()
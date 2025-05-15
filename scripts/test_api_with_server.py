#!/usr/bin/env python3
"""
Start API server and run agent tests
"""
import os
import sys
import subprocess
import time
import signal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def start_api_server():
    """Start the API server in a subprocess"""
    env = os.environ.copy()
    env["REDIS_SIMULATION_MODE"] = "true"
    env["LOG_LEVEL"] = "INFO"
    env["API_DEBUG"] = "true"
    
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "apps.api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    
    print("Starting API server...")
    proc = subprocess.Popen(
        cmd,
        env=env,
        cwd=str(project_root)
    )
    
    # Give the server time to start
    time.sleep(3)
    
    return proc


def run_tests():
    """Run the API tests"""
    print("\nRunning API tests...")
    
    result = subprocess.run(
        [sys.executable, "scripts/test_api_agents.py"],
        cwd=str(project_root)
    )
    
    return result.returncode == 0


def main():
    """Main test runner"""
    server_proc = None
    
    try:
        # Start the server
        server_proc = start_api_server()
        
        # Run tests
        success = run_tests()
        
        if success:
            print("\nAll tests passed!")
        else:
            print("\nSome tests failed!")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    finally:
        # Clean up
        if server_proc:
            print("\nShutting down API server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()
            print("Server shut down")


if __name__ == "__main__":
    sys.exit(main())
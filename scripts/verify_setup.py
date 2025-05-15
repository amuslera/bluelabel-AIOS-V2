#!/usr/bin/env python3
"""
Verify the development environment is properly configured
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def status_msg(msg, status):
    """Print colored status message"""
    colors = {"ok": GREEN, "error": RED, "warning": YELLOW}
    symbol = {"ok": "✓", "error": "✗", "warning": "⚠"}
    color = colors.get(status, "")
    return f"{color}{symbol[status]}{RESET} {msg}"

def check_basics():
    """Check basic requirements"""
    print("=== Basic Requirements ===")
    
    # Python version
    python_ok = sys.version_info >= (3, 9)
    print(status_msg(f"Python {sys.version.split()[0]}", "ok" if python_ok else "error"))
    
    # Virtual environment
    venv_ok = sys.prefix != sys.base_prefix
    print(status_msg("Virtual environment", "ok" if venv_ok else "error"))
    if not venv_ok:
        print("  Run: source .venv/bin/activate")
    
    # .env file
    env_exists = Path(".env").exists()
    print(status_msg(".env file", "ok" if env_exists else "error"))
    
    return python_ok and venv_ok and env_exists

def check_environment_config():
    """Check environment configuration"""
    print("\n=== Environment Configuration ===")
    
    # Critical settings
    critical = {
        "REDIS_SIMULATION_MODE": os.getenv("REDIS_SIMULATION_MODE", "false"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "API_DEBUG": os.getenv("API_DEBUG", "false"),
    }
    
    all_ok = True
    for key, value in critical.items():
        ok = value not in ["", None]
        print(status_msg(f"{key}={value}", "ok" if ok else "warning"))
        all_ok = all_ok and ok
    
    # Optional API keys
    optional = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    }
    
    for key, value in optional.items():
        if value and value != "your_openai_key_here" and value != "your_anthropic_key_here":
            print(status_msg(f"{key}=***{value[-4:]}", "ok"))
        else:
            print(status_msg(f"{key} not configured", "warning"))
    
    return all_ok

def check_dependencies():
    """Check Python dependencies"""
    print("\n=== Python Dependencies ===")
    
    try:
        import fastapi
        import uvicorn
        import redis
        import pydantic
        print(status_msg("Core dependencies installed", "ok"))
        return True
    except ImportError as e:
        print(status_msg(f"Missing dependency: {e}", "error"))
        print("  Run: pip install -r requirements.txt")
        return False

def check_services():
    """Check external services"""
    print("\n=== External Services ===")
    
    # Redis check (with simulation mode awareness)
    redis_sim = os.getenv("REDIS_SIMULATION_MODE", "false").lower() == "true"
    if redis_sim:
        print(status_msg("Redis: Simulation mode enabled", "ok"))
    else:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 6379))
            sock.close()
            
            if result == 0:
                print(status_msg("Redis: Available", "ok"))
            else:
                print(status_msg("Redis: Not running", "warning"))
                print("  Enable simulation: export REDIS_SIMULATION_MODE=true")
        except:
            print(status_msg("Redis: Check failed", "error"))
    
    return True

def test_api():
    """Test API startup"""
    print("\n=== API Test ===")
    
    try:
        # Add project root to Python path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from apps.api.main import app
        print(status_msg("API imports successfully", "ok"))
        
        # Quick health check
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            print(status_msg("Health endpoint works", "ok"))
            return True
        else:
            print(status_msg(f"Health endpoint failed: {response.status_code}", "error"))
            return False
            
    except Exception as e:
        print(status_msg(f"API test failed: {e}", "error"))
        return False

def main():
    """Run all checks"""
    print("Bluelabel AIOS v2 - Setup Verification")
    print("=" * 40)
    
    checks = {
        "Basic Requirements": check_basics(),
        "Environment Config": check_environment_config(),
        "Dependencies": check_dependencies(),
        "Services": check_services(),
        "API Test": test_api(),
    }
    
    # Summary
    print("\n" + "=" * 40)
    print("Summary")
    print("=" * 40)
    
    passed = sum(checks.values())
    total = len(checks)
    
    for name, result in checks.items():
        print(status_msg(name, "ok" if result else "error"))
    
    print(f"\nChecks passed: {passed}/{total}")
    
    if passed == total:
        print(status_msg("\n✅ Environment ready for development!", "ok"))
        print("\nTo start the API server:")
        print("  python scripts/run_with_logging.py")
        print("\nOr:")
        print("  uvicorn apps.api.main:app --reload")
    else:
        print(status_msg("\n❌ Some checks failed. Fix issues above.", "error"))
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
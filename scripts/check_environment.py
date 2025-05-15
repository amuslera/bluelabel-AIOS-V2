#!/usr/bin/env python3
"""
Comprehensive environment check for Bluelabel AIOS v2
Verifies all required tools, dependencies, and services are available
"""
import os
import sys
import subprocess
import pkg_resources
import importlib
import socket
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_status(message, status):
    """Print colored status message"""
    if status == "ok":
        print(f"{GREEN}✓{RESET} {message}")
    elif status == "error":
        print(f"{RED}✗{RESET} {message}")
    elif status == "warning":
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"  {message}")

def check_python_version():
    """Check if Python version meets requirements"""
    print("\n=== Python Version ===")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "ok")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)", "error")
        return False

def check_virtual_env():
    """Check if running in virtual environment"""
    print("\n=== Virtual Environment ===")
    if sys.prefix != sys.base_prefix:
        print_status(f"Virtual environment active: {sys.prefix}", "ok")
        return True
    else:
        print_status("Not running in virtual environment", "warning")
        print("  Run: source .venv/bin/activate")
        return False

def check_required_packages():
    """Check if all required Python packages are installed"""
    print("\n=== Python Packages ===")
    
    # Read requirements.txt
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_file.exists():
        print_status("requirements.txt not found", "error")
        return False
    
    with open(requirements_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    missing = []
    installed = []
    
    for req in requirements:
        # Parse package name from requirement string
        package_name = req.split('>=')[0].split('==')[0].strip()
        
        try:
            pkg_resources.get_distribution(package_name)
            installed.append(package_name)
        except pkg_resources.DistributionNotFound:
            missing.append(package_name)
    
    # Show summary
    print_status(f"Installed packages: {len(installed)}", "ok")
    
    if missing:
        print_status(f"Missing packages: {len(missing)}", "error")
        for pkg in missing:
            print(f"    - {pkg}")
        print("\n  To install missing packages:")
        print("  pip install -r requirements.txt")
        return False
    
    return True

def check_system_tools():
    """Check for system-level tools"""
    print("\n=== System Tools ===")
    
    tools = {
        'git': 'Version control',
        'docker': 'Container runtime (optional)',
        'redis-cli': 'Redis client (optional)',
        'psql': 'PostgreSQL client (optional)',
        'curl': 'HTTP client',
    }
    
    for tool, description in tools.items():
        try:
            result = subprocess.run(['which', tool], capture_output=True, text=True)
            if result.returncode == 0:
                print_status(f"{tool}: {description}", "ok")
            else:
                if tool in ['docker', 'redis-cli', 'psql']:
                    print_status(f"{tool}: {description} - not found", "warning")
                else:
                    print_status(f"{tool}: {description} - not found", "error")
        except Exception:
            print_status(f"{tool}: {description} - check failed", "error")

def check_services():
    """Check if required services are accessible"""
    print("\n=== Services ===")
    
    services = {
        'Redis': ('localhost', 6379),
        'PostgreSQL': ('localhost', 5432),
        'ChromaDB': ('localhost', 8000),
    }
    
    for service, (host, port) in services.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print_status(f"{service} ({host}:{port})", "ok")
            else:
                print_status(f"{service} ({host}:{port}) - not accessible", "warning")
                if service == 'Redis':
                    print("  Note: API can run in simulation mode without Redis")
        except Exception as e:
            print_status(f"{service} ({host}:{port}) - check failed: {e}", "error")

def check_environment_variables():
    """Check important environment variables"""
    print("\n=== Environment Variables ===")
    
    env_vars = {
        'REDIS_SIMULATION_MODE': 'Enables Redis simulation mode',
        'LOG_LEVEL': 'Logging verbosity',
        'API_DEBUG': 'API debug mode',
        'DATABASE_URL': 'PostgreSQL connection string',
        'OPENAI_API_KEY': 'OpenAI API key (optional)',
        'ANTHROPIC_API_KEY': 'Anthropic API key (optional)',
    }
    
    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if 'KEY' in var or 'PASSWORD' in var:
                display_value = value[:4] + '***'
            else:
                display_value = value
            print_status(f"{var}: {display_value} ({description})", "ok")
        else:
            if var in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
                print_status(f"{var}: Not set ({description})", "warning")
            else:
                print_status(f"{var}: Not set ({description})", "info")

def check_project_structure():
    """Check if project structure is intact"""
    print("\n=== Project Structure ===")
    
    required_dirs = [
        'apps/api',
        'agents',
        'services',
        'core',
        'shared',
        'tests',
        'scripts',
        'logs',
        'data/knowledge',
        'data/mcp',
    ]
    
    base_path = Path(__file__).parent.parent
    missing_dirs = []
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print_status(f"{dir_path}/", "ok")
        else:
            print_status(f"{dir_path}/ - missing", "error")
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print("\n  To create missing directories:")
        print(f"  mkdir -p {' '.join(missing_dirs)}")
        return False
    
    return True

def check_api_functionality():
    """Quick test of API functionality"""
    print("\n=== API Functionality ===")
    
    try:
        # Test if we can import the FastAPI app
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from apps.api.main import app
        print_status("FastAPI app imports successfully", "ok")
        
        # Test if we can create test client
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            print_status("Health endpoint responds correctly", "ok")
        else:
            print_status(f"Health endpoint returned {response.status_code}", "error")
            
    except Exception as e:
        print_status(f"API test failed: {str(e)}", "error")
        return False
    
    return True

def main():
    """Run all environment checks"""
    print("Bluelabel AIOS v2 - Environment Check")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Required Packages", check_required_packages),
        ("System Tools", check_system_tools),
        ("Services", check_services),
        ("Environment Variables", check_environment_variables),
        ("Project Structure", check_project_structure),
        ("API Functionality", check_api_functionality),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_status(f"{name} check failed: {str(e)}", "error")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("Summary")
    print("=" * 40)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nChecks passed: {passed}/{total}")
    
    if passed == total:
        print_status("\nAll checks passed! Environment is ready.", "ok")
        return 0
    else:
        print_status("\nSome checks failed. Please fix the issues above.", "error")
        
        # Provide quick fixes
        print("\n=== Quick Fixes ===")
        print("1. Activate virtual environment: source .venv/bin/activate")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Create missing directories: mkdir -p logs data/knowledge data/mcp")
        print("4. Enable simulation mode: export REDIS_SIMULATION_MODE=true")
        print("5. Set log level: export LOG_LEVEL=INFO")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
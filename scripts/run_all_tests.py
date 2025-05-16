#!/usr/bin/env python3
"""
Run all tests for the Bluelabel AIOS v2 system
"""
import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_test(name: str, command: list, description: str):
    """Run a single test"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"Description: {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, cwd=str(project_root))
    
    if result.returncode == 0:
        print(f"✓ {name} PASSED")
    else:
        print(f"✗ {name} FAILED")
    
    return result.returncode == 0


def main():
    """Run all tests"""
    print("Running All Tests for Bluelabel AIOS v2")
    print("="*60)
    
    tests = [
        ("Environment Check", 
         ["python", "scripts/verify_setup.py"],
         "Verify development environment is properly configured"),
        
        ("Logging Test",
         ["python", "scripts/test_logging_quick.py"],
         "Test logging functionality"),
        
        ("Event Bus Test",
         ["python", "scripts/test_event_bus.py"],
         "Test event bus basic functionality"),
        
        ("Event Patterns Test",
         ["python", "scripts/test_event_patterns.py"],
         "Test event bus message patterns"),
        
        ("Runtime Manager Test",
         ["python", "scripts/test_runtime_manager.py"],
         "Test agent runtime manager"),
        
        ("API Test with Server",
         ["python", "scripts/test_api_with_server.py"],
         "Test API endpoints with live server"),
        
        ("Unit Tests",
         ["python", "-m", "pytest", "tests/unit/", "-v"],
         "Run unit test suite"),
    ]
    
    results = []
    
    # Activate virtual environment
    env = os.environ.copy()
    venv_activate = project_root / ".venv/bin/activate"
    
    for test_name, test_cmd, test_desc in tests:
        try:
            result = run_test(test_name, test_cmd, test_desc)
            results.append((test_name, result))
        except Exception as e:
            print(f"Error running {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
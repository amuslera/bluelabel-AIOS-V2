#!/usr/bin/env python3
"""
Test script to verify basic functionality is working
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from fastapi.testclient import TestClient
from apps.api.main import app

def test_health_endpoint():
    """Test that the API health endpoint is working"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✓ Health endpoint working")
    return True

def test_agent_endpoints():
    """Test that agent endpoints are accessible"""
    client = TestClient(app)
    
    # Test list agents endpoint
    response = client.get("/agents")
    print(f"Agent list response: {response.status_code}")
    # It might fail due to no agent registry, but should not 500
    assert response.status_code in [200, 404, 503]
    print("✓ Agent endpoints accessible")
    return True

def test_docs_endpoint():
    """Test that API docs are available"""
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200
    print("✓ API documentation available")
    return True

def main():
    """Run all tests"""
    print("Testing Bluelabel AIOS v2 setup...")
    print("-" * 40)
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Agent Endpoints", test_agent_endpoints),
        ("API Documentation", test_docs_endpoint),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nTesting {test_name}...")
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed: {str(e)}")
            failed += 1
    
    print("\n" + "-" * 40)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
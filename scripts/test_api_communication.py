#!/usr/bin/env python3
"""Test the Communication API endpoints"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def test_communication_endpoints():
    print("Communication API Test")
    print("======================")
    
    # Test get capabilities
    print("\n1. Testing GET /communication/communication/capabilities")
    response = requests.get(f"{API_BASE}/communication/communication/capabilities")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        capabilities = response.json()
        print(f"Capabilities: {json.dumps(capabilities, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # Test status check
    print("\n2. Testing GET /communication/communication/status/email")
    response = requests.get(f"{API_BASE}/communication/communication/status/email")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        status = response.json()
        print(f"Email status: {json.dumps(status, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # Test metrics
    print("\n3. Testing GET /communication/communication/metrics")
    response = requests.get(f"{API_BASE}/communication/communication/metrics")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        metrics = response.json()
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
    else:
        print(f"Error: {response.text}")
    
    # Test send message (will likely fail without full initialization)
    print("\n4. Testing POST /communication/communication/send")
    send_data = {
        "channel": "email",
        "to": "test@example.com",
        "subject": "Test from API",
        "body": "This is a test message"
    }
    response = requests.post(f"{API_BASE}/communication/communication/send", json=send_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Send result: {json.dumps(result, indent=2)}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_communication_endpoints()
#!/usr/bin/env python3
"""Simple test for Communication API"""
import requests

base_url = "http://localhost:8000/api/v1"

try:
    # Test capabilities endpoint
    response = requests.get(f"{base_url}/communication/communication/capabilities", timeout=5)
    print(f"Capabilities: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.text)
        
    # Test status endpoint  
    response = requests.get(f"{base_url}/communication/communication/status/email", timeout=5)
    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")
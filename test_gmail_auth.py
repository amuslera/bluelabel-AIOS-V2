#!/usr/bin/env python3
"""Test Gmail authentication"""
import requests
import json

# Test authentication endpoint
url = "http://localhost:8000/api/v1/gmail-complete/auth"
headers = {"Content-Type": "application/json"}
data = {}  # Empty data since we already have token

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
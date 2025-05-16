#!/usr/bin/env python3
"""Test sending email via Gmail API"""
import requests
import json

# Test send endpoint
url = "http://localhost:8000/api/v1/gmail-complete/send"
headers = {"Content-Type": "application/json"}
data = {
    "to": ["a@bluelabel.ventures"],
    "subject": "Test from AIOS v2",
    "body": "This is a test email sent from the Bluelabel AIOS v2 system!"
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
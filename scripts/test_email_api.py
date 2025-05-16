#!/usr/bin/env python3
"""Test Email API after OAuth is configured"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def test_email_api():
    print("Email API Test")
    print("==============")
    
    # Check current status
    print("\n1. Checking email status...")
    response = requests.get(f"{API_BASE}/communication/communication/status/email")
    if response.status_code == 200:
        status = response.json()
        print(f"✓ Email status: {json.dumps(status, indent=2)}")
    else:
        print(f"✗ Error: {response.text}")
        return
    
    # Fetch recent messages
    print("\n2. Fetching recent messages...")
    response = requests.get(f"{API_BASE}/communication/communication/fetch?channel=email&limit=3")
    if response.status_code == 200:
        data = response.json()
        messages = data.get('messages', [])
        print(f"✓ Found {len(messages)} messages:")
        for msg in messages:
            print(f"   - {msg['subject'][:50]}... (from: {msg['from']})")
    else:
        print(f"✗ Error: {response.text}")
    
    # Send test email
    print("\n3. Sending test email...")
    test_email = input("Enter email address to send test to (or press Enter to skip): ")
    
    if test_email:
        send_data = {
            "channel": "email",
            "to": test_email,
            "subject": f"API Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "body": "This is a test email sent via the Bluelabel AIOS API.\n\nThe Gateway Agent is working correctly!"
        }
        
        response = requests.post(f"{API_BASE}/communication/communication/send", json=send_data)
        if response.status_code == 200:
            result = response.json()
            if 'error' in result:
                print(f"✗ Error: {result['error']}")
            else:
                print(f"✓ Email sent successfully: {json.dumps(result, indent=2)}")
        else:
            print(f"✗ Error: {response.text}")
    
    # Check metrics
    print("\n4. Checking metrics...")
    response = requests.get(f"{API_BASE}/communication/communication/metrics")
    if response.status_code == 200:
        metrics = response.json()
        print(f"✓ Metrics: {json.dumps(metrics, indent=2)}")
    else:
        print(f"✗ Error: {response.text}")

if __name__ == "__main__":
    test_email_api()
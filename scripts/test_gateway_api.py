#!/usr/bin/env python3
"""Test gateway API endpoints"""
import asyncio
import aiohttp
import json
import sys
import os


async def test_gateway_api():
    """Test gateway API endpoints"""
    base_url = "http://localhost:8000/api/v1/gateway"
    
    print("Testing Gateway API Endpoints...")
    
    async with aiohttp.ClientSession() as session:
        # Test gateway status
        print("\n1. Testing gateway status...")
        try:
            async with session.get(f"{base_url}/status") as response:
                data = await response.json()
                print(f"Gateway status: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test email endpoint
        print("\n2. Testing email endpoint...")
        email_data = {
            "from_email": "test@example.com",
            "to_email": "aios@example.com",
            "subject": "Test Email",
            "body": "This is a test email body"
        }
        
        try:
            async with session.post(f"{base_url}/email", json=email_data) as response:
                data = await response.json()
                print(f"Email response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test WhatsApp endpoint
        print("\n3. Testing WhatsApp endpoint...")
        whatsapp_data = {
            "from_number": "+1234567890",
            "to_number": "+0987654321",
            "message": "This is a test WhatsApp message"
        }
        
        try:
            async with session.post(f"{base_url}/whatsapp", json=whatsapp_data) as response:
                data = await response.json()
                print(f"WhatsApp response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test WhatsApp send endpoint (will fail without credentials)
        print("\n4. Testing WhatsApp send endpoint...")
        send_data = {
            "to": "+1234567890",
            "text": "Hello from Bluelabel AIOS!"
        }
        
        try:
            async with session.post(f"{base_url}/whatsapp/send", json=send_data) as response:
                if response.status == 503:
                    print("WhatsApp not configured (expected)")
                else:
                    data = await response.json()
                    print(f"Send response: {json.dumps(data, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Test gateway API endpoints")
        print("\nMake sure the API server is running first:")
        print("  ./run.sh")
        sys.exit(0)
    
    asyncio.run(test_gateway_api())
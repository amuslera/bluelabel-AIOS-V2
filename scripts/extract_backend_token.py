#!/usr/bin/env python3
"""Extract Gmail token from backend API"""
import asyncio
import aiohttp
import json
import os
import time
from pathlib import Path


async def monitor_backend_auth():
    """Monitor backend authentication and extract token when ready"""
    print("Gmail Token Extraction")
    print("====================\n")
    
    # Check if backend is authenticated
    async with aiohttp.ClientSession() as session:
        # 1. Check current status
        print("1. Checking backend authentication...")
        async with session.get("http://localhost:8081/gateway/google/status") as response:
            status = await response.json()
            print(f"Status: {status}")
        
        if status.get("status") != "authenticated":
            # Start authentication
            print("\n2. Starting authentication flow...")
            async with session.get("http://localhost:8081/gateway/google/auth") as response:
                auth_data = await response.json()
                auth_url = auth_data.get("auth_url")
                
                print(f"\nPlease visit this URL in your browser:")
                print(auth_url)
                print("\nAfter you see the success page, press Enter here...")
                input()
        
        # 3. Try to extract token information
        print("\n3. Checking for token in backend...")
        
        # Check various endpoints that might expose token info
        token_endpoints = [
            "/gateway/google/token",
            "/gateway/google/credentials",
            "/auth/token",
            "/config",
            "/api/config",
            "/debug/token",
        ]
        
        for endpoint in token_endpoints:
            try:
                async with session.get(f"http://localhost:8081{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Checking {endpoint}: {json.dumps(data, indent=2)[:200]}...")
                        
                        # Look for token data
                        if "refresh_token" in str(data) or "access_token" in str(data):
                            print(f"\nFound token data at {endpoint}!")
                            return data
            except Exception:
                pass
        
        # 4. Check if we can use the backend's internal state
        print("\n4. Testing email functionality...")
        
        # The backend is authenticated, so we should be able to use it
        # Let's create a wrapper that uses the backend for everything
        return None


async def create_backend_wrapper():
    """Create a wrapper that uses the backend for all Gmail operations"""
    print("\n5. Creating backend wrapper configuration...")
    
    config = {
        "method": "backend_proxy",
        "api_base": "http://localhost:8081",
        "endpoints": {
            "send": "/gateway/email/google",  # This might actually send emails
            "check": "/gateway/email/check-now",
            "status": "/gateway/google/status"
        }
    }
    
    # Save configuration
    with open("gmail_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("Created gmail_config.json")
    return config


async def test_backend_send():
    """Test if the backend can actually send emails"""
    print("\n6. Testing backend email send...")
    
    async with aiohttp.ClientSession() as session:
        # First, make sure email is configured
        print("Configuring email with Google...")
        async with session.post(
            "http://localhost:8081/gateway/email/google",
            json={},
            headers={"Content-Type": "application/json"}
        ) as response:
            config_result = await response.text()
            print(f"Config result: {config_result}")
        
        # Now try different send endpoints
        test_email = {
            "to": "a@bluelabel.ventures",
            "subject": f"Backend Send Test - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "body": "Testing if backend can send emails"
        }
        
        send_endpoints = [
            "/gateway/email/send",
            "/email/send",
            "/send",
            "/gateway/send",
            "/api/email/send"
        ]
        
        for endpoint in send_endpoints:
            print(f"\nTrying {endpoint}...")
            try:
                async with session.post(
                    f"http://localhost:8081{endpoint}",
                    json=test_email,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    print(f"Status: {response.status}")
                    if response.status in [200, 201]:
                        result = await response.text()
                        print(f"Success: {result}")
                        return True
                    elif response.status == 404:
                        print("Endpoint not found")
                    else:
                        error = await response.text()
                        print(f"Error: {error[:200]}")
            except Exception as e:
                print(f"Exception: {e}")
        
        return False


async def main():
    """Main function"""
    # Try to extract token
    token_data = await monitor_backend_auth()
    
    if token_data:
        print("\nSuccessfully extracted token data!")
        with open("backend_token.json", "w") as f:
            json.dump(token_data, f, indent=2)
        print("Saved to backend_token.json")
    else:
        print("\nCould not extract token directly")
    
    # Create backend wrapper config
    config = await create_backend_wrapper()
    
    # Test backend sending
    can_send = await test_backend_send()
    
    if not can_send:
        print("\n\nNext Steps:")
        print("===========")
        print("Since the backend doesn't support sending, we need to:")
        print("1. Create new OAuth credentials with a different redirect URI")
        print("2. Implement our own OAuth flow")
        print("\nTo do this:")
        print("1. Go to Google Cloud Console")
        print("2. Create new OAuth credentials")
        print("3. Set redirect URI to: http://localhost:8000/auth/callback")
        print("4. Update your .env with the new credentials")
        print("5. Use the complete Gmail implementation we created")
    else:
        print("\n\nSuccess!")
        print("=========")
        print("The backend can send emails. Use the proxy implementation!")


if __name__ == "__main__":
    asyncio.run(main())
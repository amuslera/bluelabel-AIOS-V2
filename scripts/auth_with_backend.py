#!/usr/bin/env python3
"""Authenticate Gmail using the backend API flow"""
import webbrowser
import time
import asyncio
import aiohttp
import json
import os
from pathlib import Path


async def check_backend_auth():
    """Check if backend is authenticated with Gmail"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8081/gateway/google/status") as response:
                data = await response.json()
                return data.get("status") == "authenticated", data
        except Exception as e:
            print(f"Error checking backend: {e}")
            return False, {}


async def start_backend_auth():
    """Start authentication through backend API"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8081/gateway/google/auth") as response:
                data = await response.json()
                return data.get("auth_url")
        except Exception as e:
            print(f"Error starting auth: {e}")
            return None


async def find_backend_token():
    """Try to find where the backend stores its token"""
    print("Searching for backend token file...")
    
    # Common locations where backend might store tokens
    possible_locations = [
        # Backend project directories
        "../bluelabel-backend/token.json",
        "../bluelabel-backend/tokens/gmail_token.json",
        "../bluelabel-backend/.gmail_token.json",
        "../backend/token.json",
        "../backend/tokens/token.json",
        
        # Docker volumes (if backend runs in Docker)
        "/var/lib/docker/volumes/*_backend/_data/token.json",
        
        # Temporary directories
        "/tmp/gmail_token.json",
        "/tmp/backend_token.json",
        
        # Home directory
        f"{Path.home()}/.bluelabel/token.json",
        f"{Path.home()}/.config/bluelabel/token.json",
    ]
    
    # Search parent directory
    parent_path = Path("..").resolve()
    for token_path in parent_path.rglob("*token*.json"):
        if "node_modules" not in str(token_path) and ".git" not in str(token_path):
            try:
                with open(token_path, 'r') as f:
                    data = json.load(f)
                    if "refresh_token" in data or "access_token" in data:
                        return str(token_path)
            except Exception:
                pass
    
    # Check specific paths
    for path in possible_locations:
        if "*" in path:
            continue  # Skip wildcards for now
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if "refresh_token" in data or "access_token" in data:
                        return path
            except Exception:
                pass
    
    return None


async def copy_backend_token():
    """Find and copy the backend's token to our project"""
    token_path = await find_backend_token()
    
    if token_path:
        print(f"Found backend token at: {token_path}")
        
        # Copy to our project
        import shutil
        try:
            shutil.copy(token_path, "token.json")
            print("✓ Token copied to token.json")
            return True
        except Exception as e:
            print(f"Error copying token: {e}")
            
            # Try to read and create new token file
            try:
                with open(token_path, 'r') as f:
                    token_data = json.load(f)
                
                # Create our own token file
                with open("token.json", 'w') as f:
                    json.dump(token_data, f, indent=2)
                print("✓ Created token.json from backend token")
                return True
            except Exception as e:
                print(f"Error creating token: {e}")
    
    return False


async def main():
    """Main authentication flow"""
    print("Gmail Authentication via Backend")
    print("===============================\n")
    
    # 1. Check if backend is already authenticated
    print("1. Checking backend authentication status...")
    is_auth, status = await check_backend_auth()
    
    if is_auth:
        print("✓ Backend is authenticated with Gmail")
        print(f"Status: {status}")
        
        # Try to find and copy the token
        print("\n2. Looking for backend token...")
        if await copy_backend_token():
            print("\n✅ Successfully copied backend token!")
            print("You can now use the complete Gmail service.")
            return
        else:
            print("\n⚠️  Could not find backend token file")
            print("The backend might be storing tokens in a database or different location")
    else:
        print("✗ Backend is not authenticated")
        
        # Start authentication
        print("\n2. Starting authentication through backend...")
        auth_url = await start_backend_auth()
        
        if auth_url:
            print(f"\nOpening browser for authentication...")
            print(f"URL: {auth_url}")
            webbrowser.open(auth_url)
            
            print("\nAfter you see the success page:")
            print("1. Close the browser")
            print("2. Press Enter here to continue")
            input()
            
            # Check if authentication succeeded
            is_auth, status = await check_backend_auth()
            if is_auth:
                print("\n✓ Authentication successful!")
                
                # Try to find the token
                if await copy_backend_token():
                    print("\n✅ Successfully copied backend token!")
                    print("You can now use the complete Gmail service.")
                else:
                    print("\n⚠️  Could not find token file")
                    print("But the backend is authenticated and can be used via proxy")
            else:
                print("\n✗ Authentication failed")
                print("Please try again")
    
    # 3. Alternative approach
    print("\n\nAlternative Approaches:")
    print("======================")
    print("1. Use the working proxy implementation for reading")
    print("2. For sending, we can create a separate authentication")
    print("3. Check the backend source code for token location")
    print("\nTo use the proxy for reading emails:")
    print("  The /api/v1/gmail-proxy endpoints are already working")
    print("\nTo set up separate sending authentication:")
    print("  1. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    print("  2. Use a different redirect URI for this project")
    print("  3. Authenticate separately for sending")


if __name__ == "__main__":
    asyncio.run(main())
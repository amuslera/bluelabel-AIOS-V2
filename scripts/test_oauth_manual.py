#!/usr/bin/env python3
"""
Manual OAuth flow to debug redirect URI issues
"""
import os
import webbrowser
from urllib.parse import urlencode
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    
    # Try different redirect URIs
    redirect_uris = [
        "http://localhost:8080",
        "http://localhost:8080/",
        "http://localhost",
        "http://localhost/",
        "urn:ietf:wg:oauth:2.0:oob",  # For manual copy/paste
    ]
    
    print("🔍 Testing OAuth URLs with different redirect URIs")
    print("=" * 50)
    print(f"Client ID: {client_id[:30]}...")
    print("\nClick on one of these URLs and see which one works:\n")
    
    for i, redirect_uri in enumerate(redirect_uris, 1):
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        print(f"{i}. Redirect URI: {redirect_uri}")
        print(f"   URL: {auth_url[:100]}...")
        print()
    
    print("\n📋 Instructions:")
    print("1. Try each URL above in your browser")
    print("2. Note which one works (doesn't show redirect_uri_mismatch)")
    print("3. Update the .env file with the working redirect URI")
    print("4. Use that exact redirect URI in the authentication script")
    
    # Option for manual flow
    print("\n🔧 Alternative: Manual Authorization")
    print("If none of the above work, try this URL for manual auth:\n")
    
    manual_params = {
        "client_id": client_id,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    manual_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(manual_params)}"
    print(manual_url)
    print("\nThis will give you a code to copy/paste manually.")

if __name__ == "__main__":
    main()
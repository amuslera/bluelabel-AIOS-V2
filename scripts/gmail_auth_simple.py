#!/usr/bin/env python3
"""
Simple Gmail OAuth Authentication
"""
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

def main():
    """Complete Gmail OAuth flow"""
    from dotenv import load_dotenv
    load_dotenv()
    
    creds = None
    token_path = 'data/gmail_credentials/token.json'
    
    # Check existing token
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Create flow
            client_config = {
                "installed": {
                    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                    "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                    "redirect_uris": ["http://localhost:8080"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            
            # Run local server
            print("Starting OAuth flow...")
            creds = flow.run_local_server(
                port=8080,
                prompt='consent',
                access_type='offline',
                include_granted_scopes='true'
            )
        
        # Save token
        os.makedirs('data/gmail_credentials', exist_ok=True)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print("✅ Token saved!")
    
    # Test connection
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        print(f"✅ Authenticated as: {email}")
        
        # Get message count
        messages = service.users().messages().list(userId='me', maxResults=1).execute()
        print(f"📧 Messages in inbox: {messages.get('resultSizeEstimate', 0)}")
        
        print("\n🎉 Gmail authentication complete!")
        print("\nTest the API with:")
        print("curl http://127.0.0.1:8000/api/v1/gmail/auth/status")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
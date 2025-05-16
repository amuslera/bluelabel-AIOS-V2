#!/usr/bin/env python3
"""
Gmail OAuth Authentication with exact redirect URI matching
"""
import os
import sys
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# OAuth2.0 scopes for Gmail
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

def authenticate():
    """Run the Gmail OAuth2.0 flow"""
    from dotenv import load_dotenv
    load_dotenv()
    
    creds = None
    token_path = 'data/gmail_credentials/token.json'
    
    # Check if we have a valid token already
    if os.path.exists(token_path):
        print("Found existing token file...")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if creds and creds.valid:
            print("✅ Token is valid!")
            return creds
            
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
            # Save refreshed token
            os.makedirs('data/gmail_credentials', exist_ok=True)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            print("✅ Token refreshed!")
            return creds
    
    # Need to authenticate from scratch
    print("\n🔐 Starting new authentication flow...")
    
    # Use the exact same configuration as in Google Console
    client_config = {
        "installed": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": ["http://localhost:8080"],  # Must match exactly
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "project_id": "quickstart"
        }
    }
    
    print("Configuration:")
    print(f"Client ID: {client_config['installed']['client_id'][:30]}...")
    print(f"Redirect URI: {client_config['installed']['redirect_uris'][0]}")
    
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    
    # Run with the exact port
    print("\n📌 Starting local server on port 8080...")
    print("Please complete the authentication in your browser.")
    
    try:
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',
            access_type='offline',
            success_message='Authentication successful! You can close this window.'
        )
    except Exception as e:
        print(f"\n❌ Error during authentication: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure no other service is using port 8080")
        print("2. Check that 'http://localhost:8080' is in your Google Console redirect URIs")
        print("3. Try closing all browser windows and running again")
        return None
    
    # Save the credentials
    print("\n💾 Saving credentials...")
    os.makedirs('data/gmail_credentials', exist_ok=True)
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print("✅ Authentication complete! Token saved.")
    return creds

def test_connection(creds):
    """Test the Gmail API connection"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        print(f"\n📧 Connected as: {email}")
        
        # Get message stats
        messages = service.users().messages().list(userId='me', maxResults=1).execute()
        total_messages = messages.get('resultSizeEstimate', 0)
        print(f"📊 Total messages: {total_messages}")
        
        return True
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        return False

def main():
    """Main function"""
    print("Gmail OAuth2.0 Authentication Setup")
    print("==================================")
    
    # Authenticate
    creds = authenticate()
    
    if creds:
        # Test the connection
        if test_connection(creds):
            print("\n🎉 Success! Gmail integration is ready.")
            print("\nNext steps:")
            print("1. Test email operations with the API")
            print("2. Set up email listeners")
            print("3. Process incoming emails automatically")
            
            # Create a quick test script
            test_script = '''#!/usr/bin/env python3
"""Quick test of Gmail API integration"""
import requests

# Test the API endpoints
api_base = "http://127.0.0.1:8000/api/v1"

# Check auth status
response = requests.get(f"{api_base}/gmail/auth/status")
print(f"Auth status: {response.json()}")

# Fetch recent emails
response = requests.get(f"{api_base}/gmail/fetch?max_results=3")
if response.status_code == 200:
    emails = response.json()
    print(f"\\nFound {len(emails)} recent emails:")
    for email in emails:
        print(f"  - {email.get('subject', 'No subject')}")
'''
            
            with open('scripts/quick_gmail_test.py', 'w') as f:
                f.write(test_script)
            
            print("\n📝 Created scripts/quick_gmail_test.py")
            print("Run it to test the Gmail API integration")
    else:
        print("\n❌ Authentication failed")
        print("Please check your Google Console settings and try again")

if __name__ == "__main__":
    main()
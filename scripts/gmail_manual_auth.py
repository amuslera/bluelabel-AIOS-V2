#!/usr/bin/env python3
"""
Gmail OAuth Manual Authentication
Uses the manual flow to avoid redirect URI issues
"""
import os
import sys
import json
import webbrowser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

def manual_auth():
    """Perform manual OAuth authentication"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🔐 Gmail Manual OAuth Authentication")
    print("=" * 40)
    
    # Check for existing token
    token_path = 'data/gmail_credentials/token.json'
    if os.path.exists(token_path):
        print("Found existing token, checking validity...")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds and creds.valid:
            print("✅ Token is valid!")
            return creds
        elif creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            print("✅ Token refreshed!")
            return creds
    
    # Manual flow
    client_config = {
        "installed": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
    )
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    
    print("\n📌 Manual Authorization Required")
    print("1. Visit this URL in your browser:\n")
    print(auth_url)
    print("\n2. Authorize the application")
    print("3. Copy the authorization code")
    print("4. Paste it below\n")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Get code from user
    code = input("Enter the authorization code: ").strip()
    
    # Exchange code for token
    print("\nExchanging code for token...")
    flow.fetch_token(code=code)
    
    # Save credentials
    creds = flow.credentials
    os.makedirs('data/gmail_credentials', exist_ok=True)
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print("✅ Token saved successfully!")
    return creds

def test_connection(creds):
    """Test Gmail API connection"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress', 'Unknown')
        
        messages = service.users().messages().list(userId='me', maxResults=1).execute()
        count = messages.get('resultSizeEstimate', 0)
        
        print(f"\n✅ Connected as: {email}")
        print(f"📧 Messages in inbox: {count}")
        
        # Show recent email
        if messages.get('messages'):
            msg_id = messages['messages'][0]['id']
            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            print(f"\nMost recent email:")
            print(f"  From: {from_header}")
            print(f"  Subject: {subject}")
        
        return True
    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        return False

def main():
    """Main function"""
    creds = manual_auth()
    
    if creds and test_connection(creds):
        print("\n🎉 Gmail authentication successful!")
        print("\nYou can now:")
        print("1. Send and receive emails via the API")
        print("2. Process emails automatically")
        print("3. Set up email listeners")
        
        # Create test script
        script_content = '''#!/usr/bin/env python3
"""Test Gmail integration"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test_email():
    from services.gateway.gmail.direct import GmailDirectGateway
    
    gateway = GmailDirectGateway()
    
    # Test fetching emails
    print("Fetching recent emails...")
    emails = await gateway.fetch_messages(max_results=3)
    print(f"Found {len(emails)} emails")
    
    for email in emails:
        print(f"- {email.get('subject', 'No subject')}")

if __name__ == "__main__":
    asyncio.run(test_email())
'''
        
        with open('scripts/test_gmail_integration.py', 'w') as f:
            f.write(script_content)
        
        print("\n📝 Created scripts/test_gmail_integration.py")
        print("Run it to test the Gmail integration")

if __name__ == "__main__":
    main()
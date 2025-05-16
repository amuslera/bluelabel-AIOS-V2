#!/usr/bin/env python3
"""
Gmail OAuth Setup Script
Handles the OAuth flow with proper redirect URI configuration
"""
import os
import sys
import json
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Scopes required for Gmail access
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    
    def do_GET(self):
        """Handle GET request with authorization code"""
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            self.server.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body>
            <h1>Authentication Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Error: No authorization code received</h1>")
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

def authenticate_gmail():
    """Complete Gmail OAuth authentication"""
    print("🔐 Gmail OAuth Authentication Setup")
    print("=" * 50)
    
    # Check for existing token
    token_path = 'data/gmail_credentials/token.json'
    creds = None
    
    if os.path.exists(token_path):
        print("Found existing token file")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        if creds and creds.valid:
            print("✅ Token is valid")
            return creds
        elif creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            print("✅ Token refreshed")
            return creds
    
    # Need to authenticate
    print("\nStarting new authentication flow...")
    
    # Get environment variables
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8081/gateway/google/callback")
    
    if not client_id or not client_secret:
        print("❌ Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env file")
        return None
    
    # Parse redirect URI to get host and port
    parsed_uri = urlparse(redirect_uri)
    redirect_host = parsed_uri.hostname or 'localhost'
    redirect_port = parsed_uri.port or 8081
    redirect_path = parsed_uri.path or '/gateway/google/callback'
    
    print(f"\nUsing redirect URI: {redirect_uri}")
    print(f"Starting OAuth server on port {redirect_port}...")
    
    # Create OAuth flow
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [redirect_uri],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "project_id": "bluelabel-aios"
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    
    # Get authorization URL
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    print(f"\n🌐 Opening browser for authentication...")
    print(f"If the browser doesn't open, visit this URL:\n{auth_url}\n")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to receive callback
    server = HTTPServer((redirect_host, redirect_port), OAuthCallbackHandler)
    server.auth_code = None
    
    # Handle one request
    print(f"Waiting for authorization callback on {redirect_uri}...")
    server.handle_request()
    
    if server.auth_code:
        print("\n✅ Authorization code received")
        
        # Exchange code for token
        try:
            flow.fetch_token(code=server.auth_code)
            creds = flow.credentials
        except Warning as w:
            # Handle scope change warning
            if "Scope has changed" in str(w):
                print("⚠️  Scope change detected (this is normal)")
                creds = flow.credentials
            else:
                raise w
        
        # Save credentials
        os.makedirs('data/gmail_credentials', exist_ok=True)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print("✅ Token saved successfully")
        
        return creds
    else:
        print("❌ No authorization code received")
        return None

def test_gmail_connection(creds):
    """Test the Gmail connection"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        print(f"\n✅ Successfully authenticated as: {email}")
        
        # Get recent messages
        messages = service.users().messages().list(userId='me', maxResults=5).execute()
        message_count = messages.get('resultSizeEstimate', 0)
        print(f"📧 Found {message_count} messages in inbox")
        
        # Show recent email subjects
        if messages.get('messages'):
            print("\nRecent emails:")
            for msg in messages['messages'][:3]:
                msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = msg_data['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                print(f"  - {subject[:50]}... (from: {from_header})")
        
        return True
    except Exception as e:
        print(f"\n❌ Error testing connection: {e}")
        return False

def main():
    """Main function"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Authenticate
    creds = authenticate_gmail()
    
    if creds:
        # Test connection
        if test_gmail_connection(creds):
            print("\n🎉 Gmail OAuth setup complete!")
            print("\nNext steps:")
            print("1. The API server can now send and receive emails")
            print("2. Run scripts/test_email_flow.py to test email operations")
            print("3. Use /api/v1/gmail endpoints for email functionality")
            
            # Create test script
            test_script = """#!/usr/bin/env python3
import asyncio
import requests

API_BASE = "http://127.0.0.1:8000/api/v1"

async def test_gmail_api():
    # Check authentication status
    response = requests.get(f"{API_BASE}/gmail/auth/status")
    print(f"Auth Status: {response.json()}")
    
    # Fetch recent emails
    response = requests.get(f"{API_BASE}/gmail/fetch?max_results=5")
    if response.status_code == 200:
        emails = response.json()
        print(f"\\nFound {len(emails)} emails")
        for email in emails[:3]:
            print(f"  - {email.get('subject', 'No subject')}")
    
    # Send test email
    test_email = {
        "to": "arielmuslera@gmail.com",
        "subject": "Bluelabel AIOS Test Email",
        "body": "This is a test email from your AI Operating System!"
    }
    response = requests.post(f"{API_BASE}/gmail/send", json=test_email)
    print(f"\\nSend email result: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_gmail_api())
"""
            
            with open('scripts/test_gmail_api.py', 'w') as f:
                f.write(test_script)
            print("\n📝 Created scripts/test_gmail_api.py for testing")
    else:
        print("\n❌ Authentication failed")

if __name__ == "__main__":
    main()
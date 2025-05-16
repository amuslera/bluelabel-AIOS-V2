#!/usr/bin/env python3
"""
Gmail OAuth with Correct Redirect URI
Matches exactly what's in Google Console
"""
import os
import sys
import json
import asyncio
import webbrowser
from aiohttp import web
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

async def run_oauth_server():
    """Run OAuth callback server"""
    auth_code = None
    
    async def handle_callback(request):
        nonlocal auth_code
        code = request.query.get('code')
        if code:
            auth_code = code
            return web.Response(text="""
                <html><body>
                <h1>Authorization successful!</h1>
                <p>You can close this window and return to the application.</p>
                </body></html>
            """, content_type='text/html')
        else:
            error = request.query.get('error', 'Unknown error')
            return web.Response(text=f"""
                <html><body>
                <h1>Authorization failed!</h1>
                <p>Error: {error}</p>
                </body></html>
            """, content_type='text/html')
    
    # Create app
    app = web.Application()
    app.router.add_get('/gateway/google/callback', handle_callback)
    
    # Start server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    print("OAuth server started on http://localhost:8080")
    print("Waiting for authorization...")
    
    # Wait for auth code
    while auth_code is None:
        await asyncio.sleep(0.1)
    
    # Clean up
    await runner.cleanup()
    
    return auth_code

def authenticate():
    """Complete Gmail OAuth authentication"""
    from dotenv import load_dotenv
    load_dotenv()
    
    print("🔐 Gmail OAuth Authentication")
    print("=" * 40)
    
    # Load existing token
    token_path = 'data/gmail_credentials/token.json'
    creds = None
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if creds and creds.valid:
            print("✅ Using existing valid token")
            return creds
    
    # Create OAuth flow
    client_config = {
        "installed": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uris": ["http://localhost:8080/gateway/google/callback"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="http://localhost:8080/gateway/google/callback"
    )
    
    # Get authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    
    print(f"\n🌐 Opening browser for authentication...")
    print(f"If browser doesn't open, visit:\n{auth_url}\n")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Run OAuth server and get code
    auth_code = asyncio.run(run_oauth_server())
    
    print(f"\n✅ Received authorization code")
    
    # Exchange code for token
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    
    # Save token
    os.makedirs('data/gmail_credentials', exist_ok=True)
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print("✅ Token saved successfully")
    return creds

def test_connection(creds):
    """Test Gmail connection"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        
        messages = service.users().messages().list(userId='me', maxResults=1).execute()
        count = messages.get('resultSizeEstimate', 0)
        
        print(f"\n✅ Connected as: {email}")
        print(f"📧 Messages: {count}")
        
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    """Main function"""
    creds = authenticate()
    
    if creds and test_connection(creds):
        print("\n🎉 Gmail authentication successful!")
        print("\nYou can now use the Gmail API")

if __name__ == "__main__":
    main()
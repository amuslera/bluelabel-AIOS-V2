#!/usr/bin/env python3
"""Gmail OAuth with proper web server handling"""

import asyncio
import webbrowser
import json
from pathlib import Path
from aiohttp import web
from urllib.parse import parse_qs
import aiohttp

class GmailOAuthServer:
    """OAuth server that handles the redirect properly"""
    
    def __init__(self):
        self.auth_code = None
        self.error = None
        
    async def handle_callback(self, request):
        """Handle OAuth callback"""
        # Extract code or error from query params
        code = request.query.get('code')
        error = request.query.get('error')
        
        if error:
            self.error = error
            return web.Response(text=f"""
                <html><body>
                <h1>Authentication Failed</h1>
                <p>Error: {error}</p>
                <p>You can close this window.</p>
                </body></html>
            """, content_type='text/html')
        
        if code:
            self.auth_code = code
            return web.Response(text="""
                <html><body>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>window.close();</script>
                </body></html>
            """, content_type='text/html')
            
        return web.Response(text="""
            <html><body>
            <h1>Invalid Request</h1>
            <p>No authorization code received.</p>
            </body></html>
        """, content_type='text/html')
    
    async def run_server(self, port=8080):
        """Run the OAuth callback server"""
        app = web.Application()
        app.router.add_get('/gateway/google/callback', self.handle_callback)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        
        print(f"Starting OAuth server on http://localhost:{port}")
        await site.start()
        
        # Wait for auth code or error
        while self.auth_code is None and self.error is None:
            await asyncio.sleep(0.1)
            
        # Clean up
        await runner.cleanup()
        
        if self.error:
            raise Exception(f"OAuth error: {self.error}")
            
        return self.auth_code

async def main():
    print("Gmail OAuth Authentication")
    print("=" * 40)
    
    # Load credentials
    creds_file = Path('data/mcp/google_credentials.json')
    if not creds_file.exists():
        print(f"❌ Credentials file not found at: {creds_file}")
        return
    
    with open(creds_file, 'r') as f:
        creds_data = json.load(f)
    
    if 'web' not in creds_data:
        print("❌ No web configuration found in credentials file")
        return
    
    web_config = creds_data['web']
    client_id = web_config['client_id']
    client_secret = web_config['client_secret']
    redirect_uri = web_config['redirect_uris'][0]
    
    print(f"Client ID: {client_id[:30]}...")
    print(f"Redirect URI: {redirect_uri}")
    
    # Create OAuth URL
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=https://www.googleapis.com/auth/gmail.readonly+https://www.googleapis.com/auth/gmail.send&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    print("\nOpening browser for authorization...")
    print(f"Auth URL: {auth_url}")
    
    # Start the OAuth server
    server = GmailOAuthServer()
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Run server and wait for callback
    try:
        auth_code = await server.run_server(port=8080)
        print(f"\n✅ Received authorization code: {auth_code[:20]}...")
        
        # Exchange code for token
        print("\nExchanging code for token...")
        
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': auth_code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Save token
                    token_file = Path('data/mcp/gmail_token.json')
                    with open(token_file, 'w') as f:
                        json.dump(token_data, f, indent=2)
                    
                    print("✅ Token saved successfully to data/mcp/gmail_token.json")
                    
                    # Test the token
                    print("\nTesting token with Gmail API...")
                    from google.oauth2.credentials import Credentials
                    from googleapiclient.discovery import build
                    
                    creds = Credentials(
                        token=token_data['access_token'],
                        refresh_token=token_data.get('refresh_token'),
                        token_uri='https://oauth2.googleapis.com/token',
                        client_id=client_id,
                        client_secret=client_secret
                    )
                    
                    service = build('gmail', 'v1', credentials=creds)
                    results = service.users().labels().list(userId='me').execute()
                    labels = results.get('labels', [])
                    
                    print(f"✅ Successfully connected to Gmail! Found {len(labels)} labels.")
                    print("\nYou can now use the Gmail integration!")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Error exchanging code: {response.status}")
                    print(error_text)
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if port 8080 is available
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8080))
    if result == 0:
        print("❌ Port 8080 is already in use!")
        print("Please stop any services using port 8080 and try again")
        print("\nYou can check what's using port 8080 with:")
        print("lsof -i :8080")
        exit(1)
    sock.close()
    
    asyncio.run(main())
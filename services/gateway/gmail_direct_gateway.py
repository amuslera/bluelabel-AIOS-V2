"""Gmail Email Gateway with Direct OAuth - Avoiding Backend Interception"""
import os
import json
import asyncio
import base64
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import aiohttp
from urllib.parse import urlencode, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from services.gateway.base import EmailGateway
from core.event_bus import EventBus
from core.event_patterns import MessageStatus

logger = logging.getLogger(__name__)

class GmailDirectGateway(EmailGateway):
    """Gmail Gateway with direct OAuth flow to avoid backend interception"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        # Use the redirect URI configured in Google Cloud Console
        self.redirect_uri = 'http://localhost:8080/gateway/google/callback'
        self.api_key = os.environ.get('GOOGLE_API_KEY')  # Optional
        
        # Token storage
        self.token_file = Path('data/gmail_token.json')
        self.token_file.parent.mkdir(exist_ok=True)
        
        self.credentials = None
        self.service = None
        self.auth_server = None
        
    async def initialize(self) -> bool:
        """Initialize Gmail service with OAuth 2.0"""
        try:
            # Try to load existing credentials
            self._load_credentials()
            
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Refresh expired token
                    self.credentials.refresh(Request())
                    self._save_credentials()
                else:
                    # Need new authentication
                    logger.info("Starting new OAuth flow on port 8080...")
                    await self._start_auth_flow()
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            return False
    
    def _load_credentials(self):
        """Load stored OAuth credentials"""
        if self.token_file.exists():
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    str(self.token_file), self.SCOPES
                )
                logger.info("Loaded existing credentials")
            except Exception as e:
                logger.warning(f"Could not load credentials: {e}")
    
    def _save_credentials(self):
        """Save OAuth credentials"""
        try:
            with open(self.token_file, 'w') as f:
                f.write(self.credentials.to_json())
            logger.info("Saved credentials to file")
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    async def _start_auth_flow(self):
        """Start OAuth flow with temporary web server"""
        from aiohttp import web
        
        # Create authorization URL
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={' '.join(self.SCOPES)}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        # Authorization code holder
        auth_code = None
        
        # Define callback handler
        async def handle_callback(request):
            nonlocal auth_code
            code = request.query.get('code')
            if code:
                auth_code = code
                return web.Response(text="""
                    <html><body>
                    <h1>Authorization successful!</h1>
                    <p>You can close this window and return to the application.</p>
                    <script>window.close();</script>
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
        
        # Create app with callback route
        app = web.Application()
        app.router.add_get('/gateway/google/callback', handle_callback)
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        
        logger.info(f"Started temporary auth server on port 8080")
        logger.info(f"Please visit this URL to authorize: {auth_url}")
        
        # Wait for authorization code
        while not auth_code:
            await asyncio.sleep(1)
        
        # Stop server
        await runner.cleanup()
        
        # Exchange code for token
        await self._exchange_code_for_token(auth_code)
    
    async def _exchange_code_for_token(self, code: str):
        """Exchange authorization code for access token"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'code': code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Create credentials from token data
                    self.credentials = Credentials(
                        token=token_data['access_token'],
                        refresh_token=token_data.get('refresh_token'),
                        token_uri=token_url,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        scopes=self.SCOPES
                    )
                    
                    # Save credentials
                    self._save_credentials()
                    logger.info("Successfully obtained access token")
                else:
                    error = await response.text()
                    raise Exception(f"Token exchange failed: {error}")
    
    async def send_message(self, to: str, subject: str, body: str, 
                          attachments: Optional[list] = None) -> Dict[str, Any]:
        """Send email via Gmail API"""
        if not self.service:
            raise Exception("Gmail service not initialized")
        
        try:
            # Create message
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            # Handle attachments if provided
            if attachments:
                logger.warning("Attachments not yet implemented")
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Send message
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            # Emit success event
            await self.emit_event(
                "message_sent",
                {
                    'to': to,
                    'subject': subject,
                    'message_id': result['id'],
                    'timestamp': datetime.utcnow().isoformat()
                },
                status=MessageStatus.COMPLETED
            )
            
            logger.info(f"Email sent successfully: {result['id']}")
            return {
                'status': 'success',
                'message_id': result['id'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            
            # Emit failure event
            await self.emit_event(
                "message_failed",
                {
                    'to': to,
                    'subject': subject,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                },
                status=MessageStatus.FAILED
            )
            
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def fetch_messages(self, limit: int = 10) -> list:
        """Fetch recent emails"""
        if not self.service:
            raise Exception("Gmail service not initialized")
        
        try:
            # Fetch message list
            results = self.service.users().messages().list(
                userId='me',
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            # Fetch full message details
            email_list = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Parse message
                headers = msg['payload'].get('headers', [])
                email_data = {
                    'id': msg['id'],
                    'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
                    'from': next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown'),
                    'date': next((h['value'] for h in headers if h['name'] == 'Date'), ''),
                    'snippet': msg.get('snippet', ''),
                    'body': self._get_message_body(msg['payload'])
                }
                email_list.append(email_data)
            
            # Emit event for fetched messages
            await self.emit_event(
                "messages_fetched",
                {
                    'count': len(email_list),
                    'timestamp': datetime.utcnow().isoformat()
                },
                status=MessageStatus.COMPLETED
            )
            
            return email_list
            
        except Exception as e:
            logger.error(f"Failed to fetch messages: {e}")
            return []
    
    def _get_message_body(self, payload: Dict) -> str:
        """Extract message body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        elif payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        
        return body
    
    async def shutdown(self) -> bool:
        """Shutdown Gmail gateway"""
        self.service = None
        self.credentials = None
        logger.info("Gmail gateway shut down")
        return True
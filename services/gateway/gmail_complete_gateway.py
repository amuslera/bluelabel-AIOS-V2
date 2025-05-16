"""Complete Gmail Gateway - Single implementation for both reading and sending"""
import os
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.logging import setup_logging
from core.event_bus import EventBus
from shared.schemas.base import BaseModel


logger = setup_logging(service_name="gmail-complete-gateway")


class GmailMessage(BaseModel):
    """Gmail message model"""
    to: List[str]
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class GmailCompleteGateway:
    """
    Complete Gmail Gateway - handles both reading and sending
    Uses the existing OAuth tokens from the backend API if available
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize complete gateway"""
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
        self.token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")
        
        # Check for backend API token location
        self.backend_token_file = os.getenv("BACKEND_GMAIL_TOKEN", "/path/to/backend/token.json")
        
        self.service = None
        self.credentials = None
        self.event_bus = event_bus or EventBus(simulation_mode=True)
        
        # Try to load credentials from backend first, then local
        self._load_credentials()
    
    def _load_credentials(self):
        """Load OAuth credentials - check backend location first"""
        # First try backend token file
        if os.path.exists(self.backend_token_file):
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    self.backend_token_file, self.SCOPES
                )
                logger.info(f"Loaded credentials from backend: {self.backend_token_file}")
                return
            except Exception as e:
                logger.warning(f"Could not load backend token: {e}")
        
        # Then try local token file
        if os.path.exists(self.token_file):
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, self.SCOPES
                )
                logger.info("Loaded local OAuth credentials")
                return
            except Exception as e:
                logger.error(f"Error loading credentials: {str(e)}")
        
        self.credentials = None
    
    def _save_credentials(self):
        """Save OAuth credentials locally"""
        if self.credentials:
            try:
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
                logger.info("Saved OAuth credentials")
            except Exception as e:
                logger.error(f"Error saving credentials: {str(e)}")
    
    async def authenticate(self, auth_code: str = None) -> Dict[str, Any]:
        """Authenticate with Gmail"""
        try:
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Refresh expired token
                    self.credentials.refresh(Request())
                    self._save_credentials()
                else:
                    # Need new authorization
                    if not auth_code:
                        # Check if we're missing client credentials
                        if not self.client_id or not self.client_secret:
                            return {
                                "status": "error",
                                "message": "Missing Google OAuth credentials. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET",
                                "missing_env": True
                            }
                        
                        # Create flow and return auth URL
                        flow = self._create_flow()
                        auth_url, _ = flow.authorization_url(prompt='consent')
                        
                        return {
                            "status": "authorization_required",
                            "auth_url": auth_url,
                            "message": "Visit the URL to authorize access to Gmail"
                        }
                    
                    # Exchange auth code for token
                    flow = self._create_flow()
                    flow.fetch_token(code=auth_code)
                    self.credentials = flow.credentials
                    self._save_credentials()
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress')
            logger.info(f"Authenticated as: {email}")
            
            return {
                "status": "authenticated",
                "email": email,
                "message": "Successfully authenticated with Gmail"
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to authenticate with Gmail"
            }
    
    def _create_flow(self):
        """Create OAuth flow"""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        return Flow.from_client_config(
            client_config,
            scopes=self.SCOPES,
            redirect_uri=self.redirect_uri
        )
    
    async def send_message(self, message: GmailMessage) -> Dict[str, Any]:
        """Send an email"""
        # Ensure we're authenticated
        if not self.service:
            auth_result = await self.authenticate()
            if auth_result.get("status") != "authenticated":
                return auth_result
        
        try:
            # Create message
            email_message = MIMEMultipart()
            email_message['to'] = ', '.join(message.to)
            email_message['subject'] = message.subject
            
            if message.cc:
                email_message['cc'] = ', '.join(message.cc)
            if message.bcc:
                email_message['bcc'] = ', '.join(message.bcc)
            
            # Add body
            body_part = MIMEText(message.body, 'html' if message.html else 'plain')
            email_message.attach(body_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(
                email_message.as_bytes()
            ).decode('utf-8')
            
            # Send message
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            message_id = result.get('id')
            logger.info(f"Email sent successfully: {message_id}")
            
            return {
                "status": "success",
                "message_id": message_id,
                "message": "Email sent successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to send email via Gmail"
            }
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to send email"
            }
    
    async def fetch_messages(self, query: str = "is:unread", max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch messages from Gmail"""
        if not self.service:
            auth_result = await self.authenticate()
            if auth_result.get("status") != "authenticated":
                return []
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            full_messages = []
            
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                parsed_message = self._parse_message(msg)
                full_messages.append(parsed_message)
            
            return full_messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            return []
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message"""
        headers = message.get('payload', {}).get('headers', [])
        
        header_dict = {}
        for header in headers:
            header_dict[header['name'].lower()] = header['value']
        
        body = self._extract_body(message.get('payload', {}))
        
        return {
            'id': message.get('id'),
            'threadId': message.get('threadId'),
            'from': header_dict.get('from', ''),
            'to': header_dict.get('to', ''),
            'subject': header_dict.get('subject', ''),
            'date': header_dict.get('date', ''),
            'body': body,
            'snippet': message.get('snippet', ''),
            'labelIds': message.get('labelIds', [])
        }
    
    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract body from Gmail message payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'multipart/alternative':
                    body = self._extract_body(part)
        elif payload.get('body', {}).get('data'):
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        
        return body
    
    def is_authenticated(self) -> bool:
        """Check if gateway is authenticated"""
        return self.credentials is not None and self.credentials.valid
    
    async def check_status(self) -> Dict[str, Any]:
        """Check Gmail service status"""
        return {
            "authenticated": self.is_authenticated(),
            "service_ready": self.service is not None,
            "token_location": "backend" if os.path.exists(self.backend_token_file) else "local",
            "client_configured": bool(self.client_id and self.client_secret)
        }
"""Gmail Gateway with OAuth 2.0 authentication"""
import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
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


logger = setup_logging(service_name="gmail-oauth-gateway")


class GmailMessage(BaseModel):
    """Gmail message model"""
    to: List[str]  # list of recipient emails
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class GmailOAuthGateway:
    """
    Gmail API Gateway with OAuth 2.0 authentication
    
    This implementation uses the Gmail API with OAuth 2.0 for secure access.
    Requires:
    - Google Cloud Project with Gmail API enabled
    - OAuth 2.0 credentials (client_id, client_secret)
    - User consent for accessing Gmail
    """
    
    # OAuth scopes required for Gmail operations
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self, 
                 credentials_file: str = None,
                 token_file: str = None,
                 event_bus: Optional[EventBus] = None):
        """Initialize Gmail OAuth gateway"""
        self.credentials_file = credentials_file or os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
        self.token_file = token_file or os.getenv("GMAIL_TOKEN_FILE", "token.json")
        self.event_bus = event_bus or EventBus(simulation_mode=True)
        self.service = None
        self.credentials = None
        
        # Load saved credentials if available
        self._load_credentials()
    
    def _load_credentials(self):
        """Load saved OAuth credentials"""
        if os.path.exists(self.token_file):
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    self.token_file, self.SCOPES
                )
                logger.info("Loaded saved OAuth credentials")
            except Exception as e:
                logger.error(f"Error loading credentials: {str(e)}")
                self.credentials = None
    
    def _save_credentials(self):
        """Save OAuth credentials to file"""
        if self.credentials:
            try:
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
                logger.info("Saved OAuth credentials")
            except Exception as e:
                logger.error(f"Error saving credentials: {str(e)}")
    
    async def authenticate(self, auth_code: str = None) -> Dict[str, Any]:
        """Authenticate with Gmail using OAuth 2.0"""
        try:
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Refresh expired token
                    self.credentials.refresh(Request())
                    self._save_credentials()
                    logger.info("Refreshed OAuth token")
                else:
                    # Need new authorization
                    if not auth_code:
                        # Return authorization URL
                        flow = Flow.from_client_secrets_file(
                            self.credentials_file,
                            scopes=self.SCOPES,
                            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                        )
                        auth_url, _ = flow.authorization_url(prompt='consent')
                        return {
                            "status": "authorization_required",
                            "auth_url": auth_url,
                            "message": "Visit the URL to authorize access to Gmail"
                        }
                    
                    # Exchange auth code for token
                    flow = Flow.from_client_secrets_file(
                        self.credentials_file,
                        scopes=self.SCOPES,
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                    )
                    flow.fetch_token(code=auth_code)
                    self.credentials = flow.credentials
                    self._save_credentials()
                    logger.info("Obtained new OAuth token")
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Authenticated as: {profile.get('emailAddress')}")
            
            return {
                "status": "authenticated",
                "email": profile.get('emailAddress'),
                "message": "Successfully authenticated with Gmail"
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to authenticate with Gmail"
            }
    
    async def send_message(self, message: GmailMessage) -> Dict[str, Any]:
        """Send an email via Gmail API"""
        if not self.service:
            return {
                "status": "error",
                "error": "Not authenticated",
                "message": "Please authenticate with Gmail first"
            }
        
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
            
            # Add attachments if any
            if message.attachments:
                for attachment in message.attachments:
                    # Implementation for attachments would go here
                    pass
            
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
                "message": "Email sent successfully"
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
    
    async def fetch_messages(self, 
                           query: str = "is:unread",
                           max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch messages from Gmail"""
        if not self.service:
            logger.error("Not authenticated with Gmail")
            return []
        
        try:
            # List messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            full_messages = []
            
            for message in messages:
                # Get full message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                # Parse message
                parsed_message = self._parse_message(msg)
                full_messages.append(parsed_message)
            
            logger.info(f"Fetched {len(full_messages)} messages")
            return full_messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            return []
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message into standard format"""
        headers = message.get('payload', {}).get('headers', [])
        
        # Extract headers
        header_dict = {}
        for header in headers:
            header_dict[header['name'].lower()] = header['value']
        
        # Extract body
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
    
    async def process_incoming_email(self, message: Dict[str, Any]) -> str:
        """Process an incoming email and publish to event bus"""
        # Create event data
        event_data = {
            "message_id": message.get('id'),
            "source": "gmail",
            "sender": message.get('from', ''),
            "recipient": message.get('to', ''),
            "subject": message.get('subject', ''),
            "content_source": message.get('body', ''),
            "original_message": message
        }
        
        # Publish to event bus
        task_id = self.event_bus.publish(
            stream="gateway.email",
            message={
                "type": "new_content",
                "source": "gmail_oauth",
                "payload": event_data
            }
        )
        
        # Mark as read
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message['id'],
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            logger.error(f"Failed to mark message as read: {str(e)}")
        
        return task_id
    
    async def start_email_listener(self, check_interval: int = 60):
        """Start listening for new emails"""
        import asyncio
        
        logger.info(f"Starting Gmail listener (interval: {check_interval}s)")
        
        while True:
            try:
                # Fetch unread messages
                messages = await self.fetch_messages(query="is:unread")
                
                # Process each message
                for message in messages:
                    task_id = await self.process_incoming_email(message)
                    logger.info(f"Processed email {message['id']} -> task {task_id}")
                
            except Exception as e:
                logger.error(f"Error in email listener: {str(e)}")
            
            # Wait before checking again
            await asyncio.sleep(check_interval)
    
    def is_authenticated(self) -> bool:
        """Check if gateway is authenticated"""
        return self.credentials is not None and self.credentials.valid
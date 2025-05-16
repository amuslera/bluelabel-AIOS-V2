"""Gmail Hybrid Gateway - Combines proxy for reading and direct OAuth for sending"""
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.logging import setup_logging
from core.event_bus import EventBus
from services.gateway.gmail_proxy_gateway import GmailProxyGateway
from shared.schemas.base import BaseModel


logger = setup_logging(service_name="gmail-hybrid-gateway")


class GmailMessage(BaseModel):
    """Gmail message model"""
    to: List[str]
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class GmailHybridGateway:
    """
    Hybrid Gmail Gateway
    - Uses proxy for reading emails (leverages existing auth)
    - Uses direct OAuth for sending emails
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.readonly'
    ]
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize hybrid gateway"""
        # Proxy for reading
        self.proxy = GmailProxyGateway()
        
        # Direct OAuth for sending
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
        self.token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")
        
        self.service = None
        self.credentials = None
        self.event_bus = event_bus or EventBus(simulation_mode=True)
        
        # Load saved credentials
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
        """Save OAuth credentials"""
        if self.credentials:
            try:
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
                logger.info("Saved OAuth credentials")
            except Exception as e:
                logger.error(f"Error saving credentials: {str(e)}")
    
    async def authenticate_for_sending(self, auth_code: str = None) -> Dict[str, Any]:
        """Authenticate for sending emails"""
        try:
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    # Refresh expired token
                    self.credentials.refresh(Request())
                    self._save_credentials()
                else:
                    # Need new authorization
                    if not auth_code:
                        # Create flow and return auth URL
                        client_config = {
                            "web": {
                                "client_id": self.client_id,
                                "client_secret": self.client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [self.redirect_uri]
                            }
                        }
                        
                        flow = Flow.from_client_config(
                            client_config,
                            scopes=self.SCOPES,
                            redirect_uri=self.redirect_uri
                        )
                        
                        auth_url, _ = flow.authorization_url(prompt='consent')
                        return {
                            "status": "authorization_required",
                            "auth_url": auth_url,
                            "message": "Visit the URL to authorize email sending"
                        }
                    
                    # Exchange auth code for token
                    flow = Flow.from_client_config(
                        {
                            "web": {
                                "client_id": self.client_id,
                                "client_secret": self.client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": [self.redirect_uri]
                            }
                        },
                        scopes=self.SCOPES,
                        redirect_uri=self.redirect_uri
                    )
                    
                    flow.fetch_token(code=auth_code)
                    self.credentials = flow.credentials
                    self._save_credentials()
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            
            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            logger.info(f"Authenticated for sending as: {profile.get('emailAddress')}")
            
            return {
                "status": "authenticated",
                "email": profile.get('emailAddress'),
                "message": "Ready to send emails"
            }
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to authenticate for sending"
            }
    
    async def send_message(self, message: GmailMessage) -> Dict[str, Any]:
        """Send an email using direct Gmail API"""
        # First check if we can send via proxy (in case it starts working)
        proxy_result = await self.proxy.send_message(message)
        
        # If proxy works, use it
        if proxy_result.get("status") == "success" and "configured" not in proxy_result.get("response", {}).get("message", "").lower():
            logger.info("Email sent via proxy")
            return proxy_result
        
        # Otherwise, use direct sending
        if not self.service:
            # Try to authenticate
            auth_result = await self.authenticate_for_sending()
            if auth_result.get("status") != "authenticated":
                return {
                    "status": "error",
                    "message": "Not authenticated for sending. Please authenticate first.",
                    "auth_url": auth_result.get("auth_url")
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
            
            # Publish event
            event_data = {
                "message_id": message_id,
                "to": message.to,
                "subject": message.subject,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.event_bus.publish(
                stream="emails.sent",
                message={
                    "type": "email_sent",
                    "source": "gmail_hybrid",
                    "payload": event_data
                }
            )
            
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
    
    # Proxy methods for reading
    async def check_inbox(self) -> Dict[str, Any]:
        """Check inbox using proxy"""
        return await self.proxy.check_inbox()
    
    async def get_email_config(self) -> Dict[str, Any]:
        """Get email config using proxy"""
        return await self.proxy.get_email_config()
    
    async def check_status(self) -> Dict[str, Any]:
        """Check both proxy and sending status"""
        proxy_status = await self.proxy.check_status()
        
        sending_status = {
            "authenticated": self.credentials is not None and self.credentials.valid,
            "service_ready": self.service is not None
        }
        
        return {
            "reading": proxy_status,
            "sending": sending_status,
            "hybrid_mode": True
        }
    
    def is_authenticated_for_sending(self) -> bool:
        """Check if authenticated for sending"""
        return self.credentials is not None and self.credentials.valid
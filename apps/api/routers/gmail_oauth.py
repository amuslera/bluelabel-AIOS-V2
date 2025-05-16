"""Gmail OAuth 2.0 API endpoints"""
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.logging import setup_logging
from services.gateway.gmail_oauth_env_gateway import GmailOAuthEnvGateway as GmailOAuthGateway, GmailMessage


router = APIRouter()
logger = setup_logging(service_name="gmail-oauth-api")

# Global Gmail gateway instance
gmail_gateway = GmailOAuthGateway()

# Check if configured on startup
if gmail_gateway.is_configured():
    logger.info("Gmail OAuth configured with environment variables")
else:
    logger.warning("Gmail OAuth not configured - set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")


class AuthRequest(BaseModel):
    """OAuth authorization request"""
    auth_code: Optional[str] = None  # Authorization code from Google


class EmailRequest(BaseModel):
    """Email send request"""
    to: List[str]
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class FetchRequest(BaseModel):
    """Email fetch request"""
    query: str = "is:unread"
    max_results: int = 10


@router.post("/auth")
async def authenticate(request: AuthRequest):
    """Authenticate with Gmail using OAuth 2.0"""
    result = await gmail_gateway.authenticate(auth_code=request.auth_code)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/auth/status")
async def auth_status():
    """Check authentication status"""
    return {
        "configured": gmail_gateway.is_configured(),
        "authenticated": gmail_gateway.is_authenticated(),
        "token_file_exists": os.path.exists(gmail_gateway.token_file),
        "client_id_set": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "client_secret_set": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
    }


@router.post("/send")
async def send_email(request: EmailRequest):
    """Send an email via Gmail"""
    if not gmail_gateway.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please authenticate with Gmail first."
        )
    
    message = GmailMessage(
        to=request.to,
        subject=request.subject,
        body=request.body,
        html=request.html,
        cc=request.cc,
        bcc=request.bcc
    )
    
    result = await gmail_gateway.send_message(message)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/fetch")
async def fetch_emails(request: FetchRequest):
    """Fetch emails from Gmail"""
    if not gmail_gateway.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please authenticate with Gmail first."
        )
    
    messages = await gmail_gateway.fetch_messages(
        query=request.query,
        max_results=request.max_results
    )
    
    return {
        "status": "success",
        "count": len(messages),
        "messages": messages
    }


@router.post("/process/{message_id}")
async def process_email(message_id: str, background_tasks: BackgroundTasks):
    """Process a specific email by ID"""
    if not gmail_gateway.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please authenticate with Gmail first."
        )
    
    # Fetch the specific message
    messages = await gmail_gateway.fetch_messages(
        query=f"rfc822msgid:{message_id}",
        max_results=1
    )
    
    if not messages:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Process in background
    async def process_task():
        return await gmail_gateway.process_incoming_email(messages[0])
    
    background_tasks.add_task(process_task)
    
    return {
        "status": "processing",
        "message_id": message_id
    }


@router.post("/listener/start")
async def start_listener(background_tasks: BackgroundTasks, interval: int = 60):
    """Start the email listener"""
    if not gmail_gateway.is_authenticated():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please authenticate with Gmail first."
        )
    
    # Start listener in background
    background_tasks.add_task(
        gmail_gateway.start_email_listener,
        check_interval=interval
    )
    
    return {
        "status": "started",
        "check_interval": interval
    }


@router.get("/setup-instructions")
async def setup_instructions():
    """Get Gmail OAuth setup instructions"""
    return {
        "instructions": [
            "Method 1: Using Environment Variables (Recommended)",
            "1. Go to Google Cloud Console (https://console.cloud.google.com/)",
            "2. Create a new project or select existing one",
            "3. Enable Gmail API for your project",
            "4. Create OAuth 2.0 credentials (Web application type)",
            "5. Copy the Client ID and Client Secret",
            "6. Set environment variables:",
            "   - GOOGLE_CLIENT_ID=your_client_id",
            "   - GOOGLE_CLIENT_SECRET=your_client_secret",
            "   - GOOGLE_REDIRECT_URI=urn:ietf:wg:oauth:2.0:oob (or your redirect URI)",
            "7. Call POST /api/v1/gmail/auth to start authentication",
            "8. Visit the returned URL to authorize access",
            "9. Copy the authorization code and call POST /api/v1/gmail/auth with the code",
            "",
            "Method 2: Using Credentials File",
            "1-4. Same as above",
            "5. Download credentials JSON file",
            "6. Save as 'credentials.json' in the project root"
        ],
        "required_scopes": GmailOAuthGateway.SCOPES,
        "environment_variables": {
            "GOOGLE_CLIENT_ID": "OAuth 2.0 Client ID",
            "GOOGLE_CLIENT_SECRET": "OAuth 2.0 Client Secret",
            "GOOGLE_REDIRECT_URI": "OAuth 2.0 Redirect URI (optional)",
            "GMAIL_TOKEN_FILE": "Path to save OAuth token (default: token.json)"
        }
    }
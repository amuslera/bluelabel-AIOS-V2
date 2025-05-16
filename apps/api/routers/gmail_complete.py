"""Complete Gmail API endpoints"""
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.logging import setup_logging
from services.gateway.gmail_complete_gateway import GmailCompleteGateway, GmailMessage


router = APIRouter()
logger = setup_logging(service_name="gmail-complete-api")

# Global Gmail instance
gmail_gateway = GmailCompleteGateway()


class EmailRequest(BaseModel):
    """Email send request"""
    to: List[str]
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class AuthRequest(BaseModel):
    """OAuth authorization request"""
    auth_code: Optional[str] = None


class FetchRequest(BaseModel):
    """Email fetch request"""
    query: str = "is:unread"
    max_results: int = 10


@router.get("/status")
async def check_status():
    """Check Gmail service status"""
    return await gmail_gateway.check_status()


@router.post("/auth")
async def authenticate(request: AuthRequest):
    """Authenticate with Gmail"""
    result = await gmail_gateway.authenticate(auth_code=request.auth_code)
    
    if result["status"] == "error" and not result.get("missing_env"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/send")
async def send_email(request: EmailRequest):
    """Send an email"""
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
        if "auth_url" in result:
            return result
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/fetch")
async def fetch_emails(request: FetchRequest):
    """Fetch emails from Gmail"""
    messages = await gmail_gateway.fetch_messages(
        query=request.query,
        max_results=request.max_results
    )
    
    return {
        "status": "success",
        "count": len(messages),
        "messages": messages
    }


@router.get("/info")
async def gmail_info():
    """Get Gmail service information"""
    status = await gmail_gateway.check_status()
    
    return {
        "service": "Complete Gmail Service",
        "description": "Full Gmail implementation with reading and sending",
        "status": status,
        "endpoints": {
            "status": "/api/v1/gmail-complete/status",
            "auth": "/api/v1/gmail-complete/auth",
            "send": "/api/v1/gmail-complete/send",
            "fetch": "/api/v1/gmail-complete/fetch"
        },
        "configuration": {
            "client_id_set": bool(os.getenv("GOOGLE_CLIENT_ID")),
            "client_secret_set": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
        }
    }
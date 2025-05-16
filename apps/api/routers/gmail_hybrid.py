"""Gmail Hybrid API endpoints - Reading via proxy, sending via direct OAuth"""
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.logging import setup_logging
from services.gateway.gmail_hybrid_gateway import GmailHybridGateway, GmailMessage


router = APIRouter()
logger = setup_logging(service_name="gmail-hybrid-api")

# Global Gmail hybrid instance
gmail_hybrid = GmailHybridGateway()


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


@router.get("/status")
async def check_status():
    """Check hybrid gateway status"""
    return await gmail_hybrid.check_status()


@router.post("/auth")
async def authenticate(request: AuthRequest):
    """Authenticate for sending emails"""
    result = await gmail_hybrid.authenticate_for_sending(auth_code=request.auth_code)
    
    if result["status"] == "error":
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
    
    result = await gmail_hybrid.send_message(message)
    
    if result["status"] == "error":
        # If authentication required, return the auth URL
        if "auth_url" in result:
            return result
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/check-inbox")
async def check_inbox():
    """Check inbox for new emails"""
    return await gmail_hybrid.check_inbox()


@router.get("/config")
async def get_config():
    """Get email configuration"""
    return await gmail_hybrid.get_email_config()


@router.get("/info")
async def hybrid_info():
    """Get hybrid gateway information"""
    return {
        "service": "Gmail Hybrid Gateway",
        "description": "Reads emails via proxy, sends directly via OAuth",
        "features": {
            "reading": "Via proxy to existing authenticated API",
            "sending": "Direct Gmail API with OAuth",
            "authentication": "Separate auth for sending if needed"
        },
        "endpoints": {
            "status": "/api/v1/gmail-hybrid/status",
            "auth": "/api/v1/gmail-hybrid/auth",
            "send": "/api/v1/gmail-hybrid/send",
            "check_inbox": "/api/v1/gmail-hybrid/check-inbox",
            "config": "/api/v1/gmail-hybrid/config"
        }
    }
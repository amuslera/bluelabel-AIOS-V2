"""Gmail Proxy API endpoints"""
import os
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.logging import setup_logging
from services.gateway.gmail_proxy_gateway import GmailProxyGateway, GmailMessage


router = APIRouter()
logger = setup_logging(service_name="gmail-proxy-api")

# Global Gmail proxy instance
gmail_proxy = GmailProxyGateway()


class EmailRequest(BaseModel):
    """Email send request"""
    to: List[str]
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


@router.get("/status")
async def check_status():
    """Check Gmail proxy status"""
    return await gmail_proxy.check_status()


@router.post("/send")
async def send_email(request: EmailRequest):
    """Send an email via Gmail proxy"""
    message = GmailMessage(
        to=request.to,
        subject=request.subject,
        body=request.body,
        html=request.html,
        cc=request.cc,
        bcc=request.bcc
    )
    
    result = await gmail_proxy.send_message(message)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/check-inbox")
async def check_inbox():
    """Check inbox for new emails"""
    return await gmail_proxy.check_inbox()


@router.get("/config")
async def get_config():
    """Get email configuration"""
    return await gmail_proxy.get_email_config()


@router.post("/listener/start")
async def start_listener():
    """Start email listener"""
    return await gmail_proxy.start_email_listener()


@router.post("/listener/stop")
async def stop_listener():
    """Stop email listener"""
    return await gmail_proxy.stop_email_listener()


@router.get("/info")
async def proxy_info():
    """Get proxy information"""
    return {
        "service": "Gmail Proxy",
        "description": "Forwards Gmail operations to existing API server",
        "api_base_url": gmail_proxy.api_base_url,
        "endpoints": {
            "send": "/api/v1/gmail-proxy/send",
            "status": "/api/v1/gmail-proxy/status",
            "check_inbox": "/api/v1/gmail-proxy/check-inbox",
            "config": "/api/v1/gmail-proxy/config",
            "start_listener": "/api/v1/gmail-proxy/listener/start",
            "stop_listener": "/api/v1/gmail-proxy/listener/stop"
        }
    }
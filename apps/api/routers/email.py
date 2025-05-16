"""Email Gateway API endpoints"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from services.gateway.gmail_direct_gateway import GmailDirectGateway
from core.event_bus import EventBus

router = APIRouter(prefix="/email", tags=["email"])

# Global gateway instance
gmail_gateway: Optional[GmailDirectGateway] = None

class EmailRequest(BaseModel):
    """Email send request schema"""
    to: str
    subject: str
    body: str
    attachments: Optional[list] = None

class GatewayConfig(BaseModel):
    """Gateway configuration schema"""
    provider: str = "gmail"

async def get_gateway():
    """Get or create Gmail gateway instance"""
    global gmail_gateway
    
    if not gmail_gateway:
        event_bus = EventBus()
        gmail_gateway = GmailDirectGateway(event_bus)
        
        # Initialize gateway
        if not await gmail_gateway.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize Gmail gateway")
    
    return gmail_gateway

@router.post("/configure")
async def configure_gateway(config: GatewayConfig):
    """Configure email gateway"""
    try:
        gateway = await get_gateway()
        return {
            "status": "success",
            "message": "Email gateway configured",
            "provider": config.provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_email(email: EmailRequest, gateway: GmailDirectGateway = Depends(get_gateway)):
    """Send an email"""
    try:
        result = await gateway.send_message(
            to=email.to,
            subject=email.subject,
            body=email.body,
            attachments=email.attachments
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages")
async def get_messages(limit: int = 10, gateway: GmailDirectGateway = Depends(get_gateway)):
    """Fetch recent messages"""
    try:
        messages = await gateway.fetch_messages(limit=limit)
        return {
            "status": "success",
            "count": len(messages),
            "messages": messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status(gateway: GmailDirectGateway = Depends(get_gateway)):
    """Check gateway status"""
    return {
        "status": "active" if gateway.service else "not_initialized",
        "provider": "gmail",
        "authenticated": bool(gateway.credentials and gateway.credentials.valid)
    }
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import os

from core.event_bus import EventBus
from core.logging import setup_logging
from services.gateway.whatsapp_gateway import WhatsAppGateway, WhatsAppMessage, WhatsAppResponse

router = APIRouter()
logger = setup_logging(service_name="gateway-api")

# Initialize EventBus with simulation mode if Redis is not available
simulation_mode = os.getenv("REDIS_SIMULATION_MODE", "false").lower() == "true"
event_bus = EventBus(simulation_mode=simulation_mode)

# Initialize WhatsApp gateway
whatsapp_gateway = WhatsAppGateway()


class EmailRequest(BaseModel):
    from_email: str
    to_email: str
    subject: str
    body: str


class WhatsAppRequest(BaseModel):
    from_number: str
    to_number: str
    message: str


class SendWhatsAppRequest(BaseModel):
    to: str  # recipient phone number with country code
    text: str  # message text
    template: Optional[str] = None  # template name if using templates
    template_params: Optional[List[str]] = None  # template parameters


class GatewayResponse(BaseModel):
    task_id: str
    status: str
    details: Optional[Dict[str, Any]] = None


@router.post("/email", response_model=GatewayResponse)
async def process_email(request: EmailRequest, background_tasks: BackgroundTasks):
    """Process an incoming email request"""
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create event data
    event_data = {
        "task_id": task_id,
        "source": "email",
        "sender": request.from_email,
        "recipient": request.to_email,
        "subject": request.subject,
        "content_source": request.body,
        "original_body": request.body
    }
    
    # Publish to event bus in background
    def publish_event():
        event_bus.publish(
            stream="gateway.email",
            message={
                "type": "new_content",
                "source": "email_gateway",
                "payload": event_data
            }
        )
    
    background_tasks.add_task(publish_event)
    logger.info(f"Email queued for processing: {task_id}")
    
    return GatewayResponse(task_id=task_id, status="queued")


@router.post("/whatsapp", response_model=GatewayResponse)
async def process_whatsapp(request: WhatsAppRequest, background_tasks: BackgroundTasks):
    """Process an incoming WhatsApp message"""
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create event data
    event_data = {
        "task_id": task_id,
        "source": "whatsapp",
        "sender": request.from_number,
        "recipient": request.to_number,
        "content_source": request.message,
        "original_message": request.message
    }
    
    # Publish to event bus in background
    def publish_event():
        event_bus.publish(
            stream="gateway.whatsapp",
            message={
                "type": "new_content",
                "source": "whatsapp_gateway",
                "payload": event_data
            }
        )
    
    background_tasks.add_task(publish_event)
    logger.info(f"WhatsApp message queued for processing: {task_id}")
    
    return GatewayResponse(task_id=task_id, status="queued")


@router.post("/whatsapp/send", response_model=WhatsAppResponse)
async def send_whatsapp_message(request: SendWhatsAppRequest):
    """Send a WhatsApp message"""
    if not whatsapp_gateway.is_configured():
        raise HTTPException(
            status_code=503,
            detail="WhatsApp gateway not configured. Please set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID"
        )
    
    message = WhatsAppMessage(
        to=request.to,
        text=request.text,
        template=request.template,
        template_params=request.template_params
    )
    
    response = await whatsapp_gateway.send_message(message)
    
    if response.status == "error":
        raise HTTPException(status_code=500, detail=response.error)
    
    return response


@router.post("/whatsapp/webhook")
async def whatsapp_webhook(webhook_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Handle incoming WhatsApp webhooks"""
    result = await whatsapp_gateway.receive_webhook(webhook_data)
    
    if result["status"] == "success":
        messages = result.get("messages", [])
        
        # Process each message
        for message in messages:
            task_id = str(uuid.uuid4())
            event_data = {
                "task_id": task_id,
                "source": "whatsapp",
                "sender": message.get("from"),
                "recipient": message.get("to"),
                "content_source": message.get("text"),
                "message_id": message.get("message_id"),
                "timestamp": message.get("timestamp"),
                "message_type": message.get("type")
            }
            
            # Publish to event bus
            def publish_event(data):
                event_bus.publish(
                    stream="gateway.whatsapp",
                    message={
                        "type": "new_content",
                        "source": "whatsapp_webhook",
                        "payload": data
                    }
                )
            
            background_tasks.add_task(publish_event, event_data)
        
        return {"status": "success", "processed": len(messages)}
    else:
        logger.error(f"WhatsApp webhook error: {result.get('error')}")
        return {"status": "error", "error": result.get("error")}


@router.get("/whatsapp/webhook")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """Verify WhatsApp webhook for initial setup"""
    if hub_mode == "subscribe":
        try:
            challenge = await whatsapp_gateway.verify_webhook(hub_verify_token, hub_challenge)
            return int(challenge)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Invalid hub mode")


@router.get("/status")
async def gateway_status():
    """Get gateway status and configuration"""
    return {
        "email": {
            "configured": True,  # Email is configured with basic SMTP settings
            "provider": "smtp"
        },
        "whatsapp": {
            "configured": whatsapp_gateway.is_configured(),
            "provider": "meta_business_api"
        }
    }
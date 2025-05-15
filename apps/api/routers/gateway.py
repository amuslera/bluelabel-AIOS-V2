from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid

from core.event_bus import EventBus

router = APIRouter()
event_bus = EventBus()

class EmailRequest(BaseModel):
    from_email: str
    to_email: str
    subject: str
    body: str

class WhatsAppRequest(BaseModel):
    from_number: str
    to_number: str
    message: str

class GatewayResponse(BaseModel):
    task_id: str
    status: str

@router.post("/email", response_model=GatewayResponse)
async def process_email(request: EmailRequest, background_tasks: BackgroundTasks):
    """Process an incoming email request"""
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create event data
    event_data = {
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
            event_type="new_content",
            data=event_data
        )
    
    background_tasks.add_task(publish_event)
    
    return GatewayResponse(task_id=task_id, status="queued")

@router.post("/whatsapp", response_model=GatewayResponse)
async def process_whatsapp(request: WhatsAppRequest, background_tasks: BackgroundTasks):
    """Process an incoming WhatsApp message"""
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create event data
    event_data = {
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
            event_type="new_content",
            data=event_data
        )
    
    background_tasks.add_task(publish_event)
    
    return GatewayResponse(task_id=task_id, status="queued")

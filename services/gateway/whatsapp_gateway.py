"""WhatsApp Business API integration using standard HTTP requests"""
import os
import json
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from core.logging import setup_logging
from shared.schemas.base import BaseModel

logger = setup_logging(service_name="whatsapp-gateway")


class WhatsAppMessage(BaseModel):
    """WhatsApp message model"""
    to: str  # recipient phone number (with country code)
    text: str  # message text
    template: Optional[str] = None  # template name if using templates
    template_params: Optional[List[str]] = None  # template parameters
    media_url: Optional[str] = None  # URL for media messages


class WhatsAppResponse(BaseModel):
    """WhatsApp API response model"""
    status: str
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class WhatsAppGateway:
    """
    WhatsApp Business API Gateway
    
    This implementation uses the Meta WhatsApp Business Cloud API
    Requires:
    - WhatsApp Business Account
    - Access Token
    - Phone Number ID
    """
    
    def __init__(self, access_token: str = None, phone_number_id: str = None):
        """Initialize WhatsApp gateway"""
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.api_version = "v17.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Validate configuration
        if not self.access_token:
            logger.warning("WhatsApp access token not configured")
        if not self.phone_number_id:
            logger.warning("WhatsApp phone number ID not configured")
    
    async def send_message(self, message: WhatsAppMessage) -> WhatsAppResponse:
        """Send a WhatsApp message"""
        if not self.access_token or not self.phone_number_id:
            logger.error("WhatsApp credentials not configured")
            return WhatsAppResponse(
                status="error",
                error="WhatsApp credentials not configured"
            )
        
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            # Build message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": message.to,
                "type": "text"
            }
            
            if message.template:
                payload["type"] = "template"
                payload["template"] = {
                    "name": message.template,
                    "language": {"code": "en_US"}
                }
                if message.template_params:
                    payload["template"]["components"] = [{
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": param}
                            for param in message.template_params
                        ]
                    }]
            else:
                payload["text"] = {"body": message.text}
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        message_id = data.get("messages", [{}])[0].get("id")
                        logger.info(f"WhatsApp message sent successfully: {message_id}")
                        return WhatsAppResponse(
                            status="success",
                            message_id=message_id
                        )
                    else:
                        error = data.get("error", {}).get("message", "Unknown error")
                        logger.error(f"WhatsApp API error: {error}")
                        return WhatsAppResponse(
                            status="error",
                            error=error
                        )
        
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return WhatsAppResponse(
                status="error",
                error=str(e)
            )
    
    async def receive_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming WhatsApp webhook"""
        try:
            # Extract message data from webhook
            entries = webhook_data.get("entry", [])
            messages = []
            
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    if "messages" in value:
                        for message in value["messages"]:
                            messages.append({
                                "from": message.get("from"),
                                "to": value.get("metadata", {}).get("display_phone_number"),
                                "text": message.get("text", {}).get("body"),
                                "timestamp": message.get("timestamp"),
                                "message_id": message.get("id"),
                                "type": message.get("type")
                            })
            
            logger.info(f"Received {len(messages)} WhatsApp messages")
            return {
                "status": "success",
                "messages": messages
            }
        
        except Exception as e:
            logger.error(f"Failed to process WhatsApp webhook: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def verify_webhook(self, verify_token: str, challenge: str) -> str:
        """Verify WhatsApp webhook for initial setup"""
        expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        if verify_token == expected_token:
            logger.info("WhatsApp webhook verified successfully")
            return challenge
        else:
            logger.error("WhatsApp webhook verification failed")
            raise ValueError("Invalid verification token")
    
    def is_configured(self) -> bool:
        """Check if WhatsApp gateway is properly configured"""
        return bool(self.access_token and self.phone_number_id)
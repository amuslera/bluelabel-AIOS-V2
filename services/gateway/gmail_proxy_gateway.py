"""Gmail Proxy Gateway - forwards requests to existing Gmail API"""
import os
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.logging import setup_logging
from core.event_bus import EventBus
from shared.schemas.base import BaseModel


logger = setup_logging(service_name="gmail-proxy-gateway")


class GmailMessage(BaseModel):
    """Gmail message model"""
    to: List[str]  # list of recipient emails
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class GmailProxyGateway:
    """
    Gmail Proxy Gateway that forwards requests to existing Gmail API
    
    This implementation forwards Gmail operations to an existing API server
    that handles OAuth authentication and maintains tokens.
    """
    
    def __init__(self, 
                 api_base_url: str = None,
                 event_bus: Optional[EventBus] = None):
        """Initialize Gmail proxy gateway"""
        self.api_base_url = api_base_url or os.getenv("GMAIL_API_BASE_URL", "http://localhost:8081")
        self.event_bus = event_bus or EventBus(simulation_mode=True)
        
        logger.info(f"Gmail proxy gateway initialized with API: {self.api_base_url}")
    
    async def check_status(self) -> Dict[str, Any]:
        """Check Gmail authentication status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/gateway/google/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "authenticated" if data.get("status") == "authenticated" else "not_authenticated",
                            "authenticated": data.get("status") == "authenticated",
                            "message": data.get("message", ""),
                            "expires_in": data.get("expires_in"),
                            "api_base_url": self.api_base_url
                        }
                    else:
                        return {
                            "status": "error",
                            "authenticated": False,
                            "message": f"Failed to check status: {response.status}",
                            "api_base_url": self.api_base_url
                        }
        except Exception as e:
            logger.error(f"Error checking Gmail status: {str(e)}")
            return {
                "status": "error",
                "authenticated": False,
                "message": str(e),
                "api_base_url": self.api_base_url
            }
    
    async def send_message(self, message: GmailMessage) -> Dict[str, Any]:
        """Send an email via the proxy API"""
        try:
            # Convert to API format
            email_data = {
                "to": message.to,
                "subject": message.subject,
                "body": message.body,
                "html": message.html
            }
            
            if message.cc:
                email_data["cc"] = message.cc
            if message.bcc:
                email_data["bcc"] = message.bcc
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/gateway/email/google",
                    json=email_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_text = await response.text()
                    
                    if response.status in [200, 201]:
                        logger.info(f"Email sent successfully via proxy")
                        
                        # Try to parse JSON response
                        try:
                            data = await response.json()
                        except:
                            data = {"message": response_text}
                        
                        return {
                            "status": "success",
                            "message": "Email sent successfully",
                            "response": data
                        }
                    else:
                        logger.error(f"Failed to send email: {response.status}")
                        return {
                            "status": "error",
                            "message": f"Failed to send email: {response.status}",
                            "response": response_text
                        }
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "response": None
            }
    
    async def check_inbox(self) -> Dict[str, Any]:
        """Check inbox for new emails"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/gateway/email/check-now",
                    json={},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "emails_processed": data.get("emails_processed", 0),
                            "message": data.get("message", "")
                        }
                    else:
                        return {
                            "status": "error",
                            "emails_processed": 0,
                            "message": f"Failed to check inbox: {response.status}"
                        }
        except Exception as e:
            logger.error(f"Error checking inbox: {str(e)}")
            return {
                "status": "error",
                "emails_processed": 0,
                "message": str(e)
            }
    
    async def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration status"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/gateway/email/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "config": data
                        }
                    else:
                        return {
                            "status": "error",
                            "config": None,
                            "message": f"Failed to get config: {response.status}"
                        }
        except Exception as e:
            logger.error(f"Error getting email config: {str(e)}")
            return {
                "status": "error",
                "config": None,
                "message": str(e)
            }
    
    async def start_email_listener(self) -> Dict[str, Any]:
        """Start the email listener"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/gateway/email/start",
                    json={},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "message": data.get("message", "Email listener started")
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to start listener: {response.status}"
                        }
        except Exception as e:
            logger.error(f"Error starting email listener: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def stop_email_listener(self) -> Dict[str, Any]:
        """Stop the email listener"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/gateway/email/stop",
                    json={},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "success",
                            "message": data.get("message", "Email listener stopped")
                        }
                    else:
                        return {
                            "status": "error",
                            "message": f"Failed to stop listener: {response.status}"
                        }
        except Exception as e:
            logger.error(f"Error stopping email listener: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def is_authenticated(self) -> bool:
        """Check if gateway is authenticated"""
        # Since this is a proxy, we need to check with the actual API
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.check_status())
        return result.get("authenticated", False)
"""Gateway Agent for handling communication channels"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from agents.base import Agent, AgentInput, AgentOutput
from services.gateway.gmail_direct_gateway import GmailDirectGateway
from core.event_bus import EventBus
from enum import Enum

class AgentStatus(str, Enum):
    """Status of an agent"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"

class CommunicationChannel(str, Enum):
    """Supported communication channels"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SLACK = "slack"  # Future
    TELEGRAM = "telegram"  # Future

class GatewayAgent(Agent):
    """Agent that manages all communication channels"""
    
    def __init__(self, name: str = "GatewayAgent", description: str = "Communication Gateway Agent"):
        super().__init__(name, description)
        self.version = "1.0.0"
        self.status = AgentStatus.INITIALIZED
        self.channels: Dict[str, Any] = {}
        self.event_bus = EventBus(simulation_mode=True)  # Use simulation mode for now
        self.metrics = {"messages_sent": 0, "messages_fetched": 0, "errors": 0}
        self.logger = logging.getLogger(__name__)
        
        # Initialize available channels
        self._init_email_channel()
        # WhatsApp and other channels will be added here
        
    def _init_email_channel(self):
        """Initialize email channel with Gmail"""
        try:
            self.channels[CommunicationChannel.EMAIL] = GmailDirectGateway(self.event_bus)
            self.logger.info("Email channel (Gmail) initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize email channel: {e}")
    
    def initialize(self) -> None:
        """Initialize the Gateway Agent"""
        self.logger.info(f"Initializing {self.name}")
        self.status = AgentStatus.RUNNING
        self.logger.info(f"{self.name} initialized successfully")
    
    async def initialize_channels(self) -> bool:
        """Initialize all communication channels asynchronously"""
        # Initialize all configured channels
        for channel_name, channel in self.channels.items():
            try:
                self.logger.info(f"Initializing channel: {channel_name}")
                success = await channel.initialize()
                if not success:
                    self.logger.warning(f"Failed to initialize {channel_name}")
            except Exception as e:
                self.logger.error(f"Error initializing {channel_name}: {e}")
        
        return True
    
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process communication requests"""
        start_time = datetime.utcnow()
        
        try:
            # Extract action and channel from input
            action = input_data.content.get("action")
            channel = input_data.content.get("channel", CommunicationChannel.EMAIL)
            
            if action == "send":
                result = await self._handle_send(channel, input_data.content)
            elif action == "fetch":
                result = await self._handle_fetch(channel, input_data.content)
            elif action == "status":
                result = await self._handle_status(channel)
            else:
                result = {"error": f"Unknown action: {action}"}
            
            # Create output
            output = AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result=result
            )
            
            # Update metrics
            # Update metrics - messages_processed doesn't exist yet
            self.metrics["messages_sent"] += 1 if action == "send" else 0
            self.metrics["messages_fetched"] += 1 if action == "fetch" else 0
            
            return output
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.metrics["errors"] += 1
            
            return AgentOutput(
                task_id=input_data.task_id,
                status="error",
                result={"error": str(e)}
            )
    
    async def _handle_send(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send message requests"""
        if channel not in self.channels:
            return {"error": f"Channel not available: {channel}"}
        
        channel_handler = self.channels[channel]
        
        if channel == CommunicationChannel.EMAIL:
            # Send email
            result = await channel_handler.send_message(
                to=payload.get("to"),
                subject=payload.get("subject"),
                body=payload.get("body"),
                attachments=payload.get("attachments")
            )
            self.metrics["messages_sent"] = self.metrics.get("messages_sent", 0) + 1
            return result
        
        # Add other channel handlers here
        return {"error": f"Send not implemented for channel: {channel}"}
    
    async def _handle_fetch(self, channel: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle fetch messages requests"""
        if channel not in self.channels:
            return {"error": f"Channel not available: {channel}"}
        
        channel_handler = self.channels[channel]
        
        if channel == CommunicationChannel.EMAIL:
            # Fetch emails
            messages = await channel_handler.fetch_messages(
                limit=payload.get("limit", 10)
            )
            self.metrics["messages_fetched"] = self.metrics.get("messages_fetched", 0) + len(messages)
            return {"messages": messages, "count": len(messages)}
        
        # Add other channel handlers here
        return {"error": f"Fetch not implemented for channel: {channel}"}
    
    async def _handle_status(self, channel: str) -> Dict[str, Any]:
        """Handle status check requests"""
        if channel not in self.channels:
            return {"error": f"Channel not available: {channel}"}
        
        # Get channel-specific status
        channel_handler = self.channels[channel]
        
        status = {
            "channel": channel,
            "available": True,
            "initialized": hasattr(channel_handler, 'service') and channel_handler.service is not None
        }
        
        if channel == CommunicationChannel.EMAIL:
            status["authenticated"] = bool(
                hasattr(channel_handler, 'credentials') and 
                channel_handler.credentials and 
                channel_handler.credentials.valid
            )
        
        return status
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        return {
            "actions": ["send", "fetch", "status"],
            "channels": list(self.channels.keys()),
            "features": {
                "email": {
                    "send": True,
                    "fetch": True,
                    "attachments": False,  # Not yet implemented
                    "oauth": True
                },
                "whatsapp": {
                    "send": False,  # Not yet implemented
                    "fetch": False,
                    "media": False
                }
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown the Gateway Agent"""
        self.logger.info(f"Shutting down {self.name}")
        
        # Shutdown all channels
        for channel_name, channel in self.channels.items():
            try:
                await channel.shutdown()
                self.logger.info(f"Shut down channel: {channel_name}")
            except Exception as e:
                self.logger.error(f"Error shutting down {channel_name}: {e}")
        
        self.status = AgentStatus.STOPPED
        self.logger.info(f"{self.name} shut down successfully")
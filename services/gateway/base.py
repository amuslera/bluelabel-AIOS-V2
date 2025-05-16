"""Base classes for gateway services"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

from core.event_bus import EventBus
from core.event_patterns import Message, MessagePattern, MessagePriority, MessageStatus

logger = logging.getLogger(__name__)

class BaseGateway(ABC):
    """Base gateway interface"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus or EventBus()
        self.logger = logger
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the gateway"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown the gateway"""
        pass
    
    async def emit_event(self, event_type: str, payload: Dict[str, Any], 
                        status: MessageStatus = MessageStatus.PENDING) -> None:
        """Emit an event to the event bus"""
        message = Message(
            type=event_type,
            source=self.__class__.__name__,
            pattern=MessagePattern.EVENT,
            payload=payload,
            metadata={
                "status": status.value,
                "tenant_id": "default"  # TODO: Get from context
            }
        )
        await self.event_bus.publish(message.dict())
        
class EmailGateway(BaseGateway):
    """Base class for email gateways"""
    
    @abstractmethod
    async def send_message(self, to: str, subject: str, body: str, 
                          attachments: Optional[List] = None) -> Dict[str, Any]:
        """Send an email message"""
        pass
    
    @abstractmethod
    async def fetch_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent messages"""
        pass

class MessagingGateway(BaseGateway):
    """Base class for messaging gateways (WhatsApp, Telegram, etc)"""
    
    @abstractmethod
    async def send_message(self, to: str, body: str, 
                          media: Optional[List] = None) -> Dict[str, Any]:
        """Send a message"""
        pass
    
    @abstractmethod
    async def fetch_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent messages"""
        pass
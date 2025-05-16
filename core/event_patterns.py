from enum import Enum
from typing import Dict, Any, List, Optional, Union, Callable
import json
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class EventMetadata(BaseModel):
    """Metadata for all events"""
    event_id: str
    event_type: str
    event_version: str = "1.0"
    timestamp: datetime
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None

class Event(BaseModel):
    """Base event model for all system events"""
    metadata: EventMetadata
    payload: Dict[str, Any]

class MessagePattern(str, Enum):
    """Common message exchange patterns"""
    PUBLISH_SUBSCRIBE = "publish_subscribe"  # One-to-many broadcast
    REQUEST_RESPONSE = "request_response"    # Synchronous request-response
    COMMAND = "command"                      # Fire-and-forget command
    EVENT = "event"                          # Notification of something that happened

class MessagePriority(str, Enum):
    """Priority levels for messages"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class MessageStatus(str, Enum):
    """Status of a message"""
    PENDING = "pending"      # Message is waiting to be processed
    PROCESSING = "processing" # Message is being processed
    COMPLETED = "completed"  # Message was processed successfully
    FAILED = "failed"        # Message processing failed
    RETRYING = "retrying"    # Message is being retried after failure

class Message(BaseModel):
    """Standard message format for the event bus"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    pattern: MessagePattern = MessagePattern.EVENT
    source: str
    destination: Optional[str] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = Field(default_factory=datetime.now)
    expiration: Optional[datetime] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MessageHandler(BaseModel):
    """Handler for processing messages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    message_types: List[str]
    function: Any  # Callable
    filter_expression: Optional[str] = None

class EventBusConfig(BaseModel):
    """Configuration for the event bus"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    default_stream_max_len: int = 1000
    consumer_group_prefix: str = "bluelabel:"
    default_batch_size: int = 10
    default_block_ms: int = 5000
    retry_count: int = 3
    retry_delay_ms: int = 1000
    dead_letter_stream: str = "dead_letter"
    enable_metrics: bool = True
    enable_logging: bool = True

class DeadLetterMessage(BaseModel):
    """Message that couldn't be processed and was moved to the dead letter queue"""
    original_message: Message
    error: str
    retry_count: int
    last_error_timestamp: datetime = Field(default_factory=datetime.now)
    original_stream: str

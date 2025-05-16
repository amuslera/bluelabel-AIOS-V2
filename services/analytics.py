# services/analytics.py
"""
Analytics and event tracking service for user-facing events.
Implements RULES.md #5: Observability
"""
import datetime
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types across the platform"""
    # File operations
    FILE_UPLOAD_INITIATED = "file_upload_initiated"
    FILE_PROCESSED = "file_processed"
    FILE_FAILED = "file_failed"
    
    # Agent operations
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    
    # Digest operations
    DIGEST_GENERATED = "digest_generated"
    DIGEST_SENT = "digest_sent"
    DIGEST_FAILED = "digest_failed"
    
    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    API_CALLED = "api_called"


class AnalyticsEvent(BaseModel):
    """Standard analytics event format"""
    timestamp: str
    event_type: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    correlation_id: Optional[str]
    metadata: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-05-17T12:00:00Z",
                "event_type": "file_processed",
                "user_id": "user123",
                "tenant_id": "tenant456",
                "correlation_id": "req-789",
                "metadata": {
                    "file_id": "file-abc",
                    "duration_ms": 1234,
                    "status": "success"
                }
            }
        }


class AnalyticsService:
    """Service for tracking and storing analytics events"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.stream_key = "analytics:events"
        
    def log_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an analytics event.
        
        Args:
            event_type: Type of event (use EventType enum values)
            user_id: User who triggered the event
            tenant_id: Tenant context
            correlation_id: Request correlation ID for tracing
            metadata: Additional event-specific data
            
        Returns:
            bool: Success status
        """
        try:
            event = AnalyticsEvent(
                timestamp=datetime.datetime.utcnow().isoformat(),
                event_type=event_type,
                user_id=user_id,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                metadata=metadata or {}
            )
            
            # Log to stdout for development
            logger.info(f"Analytics event: {event.json()}")
            
            # Push to Redis Stream if available
            if self.redis:
                self.redis.xadd(
                    self.stream_key,
                    event.dict(),
                    id="*"  # Auto-generate ID
                )
            
            # TODO: Future - push to analytics service (Segment, Mixpanel, etc)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log analytics event: {e}")
            return False
    
    def query_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        limit: int = 100
    ) -> list[AnalyticsEvent]:
        """Query analytics events with filters"""
        # TODO: Implement event querying from Redis/database
        pass


# Global instance
analytics = AnalyticsService()


# Convenience function for quick logging
def log_event(
    event_type: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> bool:
    """
    Quick helper for logging events.
    
    Usage:
        log_event("file_processed", user_id="123", metadata={"file_id": "abc"})
    """
    return analytics.log_event(
        event_type=event_type,
        user_id=user_id,
        metadata=metadata,
        **kwargs
    )


# Decorator for automatic API call tracking
def track_api_call(event_type: Optional[str] = None):
    """
    Decorator to automatically track API calls.
    
    Usage:
        @track_api_call()
        async def get_file(file_id: str):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.datetime.utcnow()
            user_id = kwargs.get("current_user", {}).get("id")
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((datetime.datetime.utcnow() - start_time).total_seconds() * 1000)
                
                log_event(
                    event_type or EventType.API_CALLED.value,
                    user_id=user_id,
                    metadata={
                        "endpoint": func.__name__,
                        "duration_ms": duration_ms,
                        "status": "success"
                    }
                )
                
                return result
                
            except Exception as e:
                duration_ms = int((datetime.datetime.utcnow() - start_time).total_seconds() * 1000)
                
                log_event(
                    event_type or EventType.API_CALLED.value,
                    user_id=user_id,
                    metadata={
                        "endpoint": func.__name__,
                        "duration_ms": duration_ms,
                        "status": "error",
                        "error": str(e)
                    }
                )
                
                raise
                
        return wrapper
    return decorator
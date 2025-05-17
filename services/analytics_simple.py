# services/analytics_simple.py
"""
Simple analytics and event tracking service without Redis dependency.
"""
import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def log_event(
    event_type: str,
    user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> bool:
    """
    Quick helper for logging events.
    Simply logs to console for development.
    """
    try:
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "metadata": metadata or {},
            **kwargs
        }
        
        # Log to stdout for development
        logger.info(f"Analytics event: {event}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to log analytics event: {e}")
        return False
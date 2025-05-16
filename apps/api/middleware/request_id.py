"""
Request ID middleware for request tracking and correlation.
Implements RULES.md #2: Traceability
"""
import uuid
from fastapi import Request
from fastapi.responses import Response


async def request_id_middleware(request: Request, call_next):
    """
    Add a unique request ID to each request for tracking.
    If X-Request-ID header is provided, use it; otherwise generate one.
    """
    # Get or generate request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())
    
    # Store in request state for access in handlers
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response


def get_request_id(request: Request) -> str:
    """
    Get the request ID from the current request.
    """
    return getattr(request.state, "request_id", None)
"""
Logging middleware for FastAPI
Tracks requests and adds context to all logs
"""

import time
import uuid
from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging_enhanced import logger

# Context variable for request ID
request_id_var = ContextVar('request_id', default=None)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and add request context"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Log request start
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                'extra_data': {
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'client_host': request.client.host if request.client else None
                }
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path}",
                extra={
                    'extra_data': {
                        'request_id': request_id,
                        'method': request.method,
                        'path': request.url.path,
                        'status_code': response.status_code,
                        'duration_seconds': duration
                    }
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    'extra_data': {
                        'request_id': request_id,
                        'method': request.method,
                        'path': request.url.path,
                        'duration_seconds': duration,
                        'error': str(e)
                    }
                }
            )
            raise
"""
Centralized error handling middleware for the API.
Implements RULES.md #18: Error Handling
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from datetime import datetime
from typing import Union

from services.analytics import log_event

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class ValidationError(AppError):
    """Input validation error"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.field = field


class NotFoundError(AppError):
    """Resource not found error"""
    def __init__(self, resource: str, id: str = None):
        message = f"{resource} not found"
        if id:
            message += f": {id}"
        super().__init__(message, "NOT_FOUND", 404)


class AuthenticationError(AppError):
    """Authentication failed error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR", 401)


class AuthorizationError(AppError):
    """Authorization failed error"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "FORBIDDEN", 403)


class RateLimitError(AppError):
    """Rate limit exceeded error"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT", 429)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handling middleware.
    Catches all exceptions and returns consistent error responses.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        return await handle_error(e, request)


async def handle_error(
    exc: Union[Exception, HTTPException, AppError],
    request: Request
) -> JSONResponse:
    """
    Handle various types of errors and return consistent JSON responses.
    """
    # Default error response
    error_response = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    }
    status_code = 500
    
    # Handle different error types
    if isinstance(exc, AppError):
        error_response["error"]["code"] = exc.code
        error_response["error"]["message"] = exc.message
        status_code = exc.status_code
        
        if hasattr(exc, 'field') and exc.field:
            error_response["error"]["field"] = exc.field
    
    elif isinstance(exc, HTTPException):
        error_response["error"]["code"] = f"HTTP_{exc.status_code}"
        error_response["error"]["message"] = exc.detail
        status_code = exc.status_code
    
    elif isinstance(exc, RequestValidationError):
        error_response["error"]["code"] = "VALIDATION_ERROR"
        error_response["error"]["message"] = "Invalid request data"
        error_response["error"]["details"] = exc.errors()
        status_code = 422
    
    else:
        # Log unexpected errors
        logger.error(
            f"Unexpected error: {type(exc).__name__}: {str(exc)}",
            exc_info=True
        )
    
    # Add request ID if available
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    # Log to analytics
    user_id = None
    if hasattr(request.state, "user"):
        user_id = request.state.user.id
    
    log_event(
        event_type="api_error",
        user_id=user_id,
        metadata={
            "error_code": error_response["error"]["code"],
            "status_code": status_code,
            "path": str(request.url.path),
            "method": request.method,
            "error_message": error_response["error"]["message"][:200]  # Truncate for safety
        }
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


def register_error_handlers(app):
    """
    Register error handlers with the FastAPI app.
    """
    # Handle custom app errors
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return await handle_error(exc, request)
    
    # Handle HTTP exceptions
    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException):
        return await handle_error(exc, request)
    
    # Handle validation errors
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return await handle_error(exc, request)
    
    # Handle all other exceptions
    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        return await handle_error(exc, request)
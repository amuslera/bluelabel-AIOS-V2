"""
Response compression middleware for API optimization.
"""
import gzip
import io
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
import brotli

class CompressionMiddleware(BaseHTTPMiddleware):
    """Middleware to compress responses using gzip or brotli"""
    
    def __init__(self, app: ASGIApp, minimum_size: int = 1024):
        super().__init__(app)
        self.minimum_size = minimum_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get the response
        response = await call_next(request)
        
        # Check if compression is supported
        accept_encoding = request.headers.get("accept-encoding", "")
        
        # Skip if already compressed or too small
        if (
            response.headers.get("content-encoding") or
            int(response.headers.get("content-length", 0)) < self.minimum_size
        ):
            return response
        
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Choose compression algorithm
        compressed_body = None
        encoding = None
        
        if "br" in accept_encoding and hasattr(brotli, "compress"):
            # Prefer Brotli if available
            compressed_body = brotli.compress(body, quality=4)
            encoding = "br"
        elif "gzip" in accept_encoding:
            # Fall back to gzip
            compressed_body = gzip.compress(body, compresslevel=6)
            encoding = "gzip"
        
        if compressed_body and len(compressed_body) < len(body):
            # Only use compression if it reduces size
            headers = dict(response.headers)
            headers["content-encoding"] = encoding
            headers["content-length"] = str(len(compressed_body))
            headers["vary"] = "Accept-Encoding"
            
            return Response(
                content=compressed_body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type
            )
        
        # Return original response if compression doesn't help
        return Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )
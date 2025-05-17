"""
Integrated API that combines all routers with proper /api/v1 prefix
This matches frontend expectations for endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uvicorn
import logging
import time
import uuid
from typing import List, Optional

from core.logging_enhanced import setup_logging
from core.config import get_settings

# Import routers - use integrated versions that match frontend expectations
from apps.api.health_simple import router as health_router
from apps.api.routers.status_integrated import router as status_router
from apps.api.routers.agents_integrated import router as agents_router
from apps.api.routers.knowledge_integrated import router as knowledge_router
from apps.api.routers.files_integrated import router as files_router
from apps.api.routers.communication_integrated import router as communication_router

# Setup enhanced logging
setup_logging()
logger = logging.getLogger(__name__)

# Settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Bluelabel AIOS API",
    version="1.0.0",
    description="AI Operating System for Knowledge Work",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request ID middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(
            f"Request {request_id} - {request.method} {request.url.path} - "
            f"{response.status_code} - {process_time:.3f}s"
        )
        
        return response

app.add_middleware(RequestIDMiddleware)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Bluelabel AIOS API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }

# Include routers with proper prefixes
app.include_router(health_router, tags=["health"])
app.include_router(status_router, prefix="/api/v1/status", tags=["status"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(knowledge_router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
app.include_router(communication_router, prefix="/api/v1/communication", tags=["communication"])

# System commands endpoint (for terminal)
@app.post("/api/v1/system/command")
async def run_command(command: dict):
    """Execute system command (mock for now)"""
    return {
        "output": f"Command '{command.get('command', '')}' received",
        "error": None,
        "exitCode": 0
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "request_id": getattr(request.state, "request_id", None)
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "error": "Internal server error",
        "status_code": 500,
        "request_id": getattr(request.state, "request_id", None)
    }

if __name__ == "__main__":
    uvicorn.run(
        "apps.api.main_integrated:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our custom logging
    )
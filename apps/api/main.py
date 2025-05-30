from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from datetime import datetime

# Import our custom logging
from core.logging import setup_logging, logger, LogContext
from core.config import config

# Import middleware
from apps.api.middleware.error_handler import register_error_handlers
from apps.api.middleware.request_id import request_id_middleware
from core.config_validator import validate_config_on_startup

# Import routers
from apps.api.routers import gateway, agents, knowledge, events, gmail_oauth, gmail_proxy, gmail_hybrid, gmail_complete, email, communication, workflows, files_simple, files_process, status, health, setup, digest, marketplace

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logging(
    service_name="bluelabel-api",
    log_level=config.logging.level,
    log_file=config.logging.file,
    json_format=not config.debug
)

# Create FastAPI app
app = FastAPI(
    title="Bluelabel AIOS v2",
    description="Agentic Intelligence Operating System API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    return await request_id_middleware(request, call_next)

# Register error handlers
register_error_handlers(app)

# Add request logging middleware
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Bluelabel AIOS v2 API")
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"Log level: {config.logging.level}")
    
    # Validate configuration
    validate_config_on_startup()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Bluelabel AIOS v2 API")

# Root endpoint
@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {"message": "Welcome to Bluelabel AIOS v2"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "services": {
            "api": {
                "status": "ok",
                "lastCheck": datetime.utcnow().isoformat()
            },
            "database": {
                "status": "ok",
                "lastCheck": datetime.utcnow().isoformat()
            },
            "redis": {
                "status": "ok",
                "lastCheck": datetime.utcnow().isoformat()
            }
        }
    }

# Include routers
app.include_router(health.router)  # Health check at root level
app.include_router(files_simple.router)  # Files at /api/v1/files
app.include_router(files_process.router)  # File processing
app.include_router(status.router)  # Status at /api/v1/status
app.include_router(gateway.router, prefix="/api/v1/gateway", tags=["gateway"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(gmail_oauth.router, prefix="/api/v1/gmail", tags=["gmail"])
app.include_router(gmail_proxy.router, prefix="/api/v1/gmail-proxy", tags=["gmail-proxy"])
app.include_router(gmail_hybrid.router, prefix="/api/v1/gmail-hybrid", tags=["gmail-hybrid"])
app.include_router(gmail_complete.router, prefix="/api/v1/gmail-complete", tags=["gmail-complete"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
app.include_router(communication.router, prefix="/api/v1/communication", tags=["communication"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(digest.router)  # Digest at /api/v1/digest
app.include_router(marketplace.router, prefix="/api/v1", tags=["marketplace"])  # Marketplace at /api/v1/marketplace
app.include_router(setup.router, tags=["setup"])

# Register agent startup events
from apps.api.routers.agents import startup_event as agent_startup
app.add_event_handler("startup", agent_startup)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_DEBUG", "False").lower() == "true",
    )

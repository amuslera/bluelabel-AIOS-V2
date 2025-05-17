from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

# Import our enhanced logging
from core.logging_enhanced import setup_logging, logger, LogContext
from apps.api.middleware.logging_middleware import LoggingMiddleware

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/api.log",
    json_logs=True
)

# Create FastAPI app
app = FastAPI(
    title="Bluelabel AIOS API",
    version="0.1.0",
    description="API with enhanced logging"
)

# Add logging middleware first
app.add_middleware(LoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG") == "true" else "An error occurred",
            "request_id": request.headers.get("X-Request-ID")
        }
    )

# Basic endpoints
@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {"message": "Bluelabel AIOS API is running"}

@app.get("/health")
def health_check():
    with LogContext(logger, check_type="health") as ctx:
        ctx.log("info", "Health check requested")
        
        # Check various components
        components = {
            "database": "checking",
            "redis": "checking",
            "storage": "checking"
        }
        
        # For now, mock the checks
        health_status = {
            "status": "healthy",
            "version": "0.1.0",
            "components": {
                "database": "healthy",
                "redis": "not_connected",
                "storage": "not_configured"
            }
        }
        
        ctx.log("info", "Health check completed", status=health_status)
        return health_status

@app.get("/api/v1/agents")
def list_agents():
    with LogContext(logger, endpoint="agents") as ctx:
        ctx.log("info", "Listing agents")
        
        # Mock response for now
        agents = {
            "agents": [
                {
                    "id": "content_mind",
                    "name": "ContentMind",
                    "status": "available",
                    "capabilities": ["summarize", "extract", "analyze"]
                }
            ]
        }
        
        ctx.log("info", f"Found {len(agents['agents'])} agents")
        return agents

@app.get("/api/v1/knowledge/items")
def list_knowledge():
    with LogContext(logger, endpoint="knowledge") as ctx:
        ctx.log("info", "Listing knowledge items")
        
        # Mock response
        items = {
            "items": [],
            "total": 0
        }
        
        ctx.log("info", f"Found {items['total']} knowledge items")
        return items

@app.get("/api/v1/communication/messages")
def list_messages():
    with LogContext(logger, endpoint="communication") as ctx:
        ctx.log("info", "Listing messages")
        
        # Mock response
        messages = {
            "messages": [],
            "total": 0
        }
        
        ctx.log("info", f"Found {messages['total']} messages")
        return messages

@app.get("/api/v1/communication/inbox")
def list_inbox():
    with LogContext(logger, endpoint="communication") as ctx:
        ctx.log("info", "Listing inbox messages")
        
        # Mock response
        inbox = {
            "messages": [],
            "total": 0
        }
        
        ctx.log("info", f"Found {inbox['total']} inbox messages")
        return inbox

@app.get("/api/v1/knowledge/tags")
def list_tags():
    with LogContext(logger, endpoint="knowledge") as ctx:
        ctx.log("info", "Listing knowledge tags")
        
        # Mock response
        tags = {
            "tags": [],
            "total": 0
        }
        
        ctx.log("info", f"Found {tags['total']} tags")
        return tags

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Bluelabel AIOS API starting up")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Log level: {os.getenv('LOG_LEVEL', 'INFO')}")
    logger.info(f"Debug mode: {os.getenv('DEBUG', 'false')}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Bluelabel AIOS API shutting down")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
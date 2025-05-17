from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Bluelabel AIOS API (Minimal)",
    version="0.1.0",
    description="Minimal working API for Bluelabel AIOS"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic endpoints
@app.get("/")
def root():
    return {"message": "Bluelabel AIOS API (Minimal) is running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "mode": "minimal"
    }

@app.get("/api/v1/agents")
def list_agents():
    # Mock response for frontend compatibility
    return {
        "agents": [
            {
                "id": "content_mind",
                "name": "ContentMind",
                "status": "available",
                "capabilities": ["summarize", "extract", "analyze"]
            }
        ]
    }

@app.get("/api/v1/knowledge/items")
def list_knowledge():
    # Mock response
    return {
        "items": [],
        "total": 0
    }

@app.get("/api/v1/communication/messages")
def list_messages():
    # Mock response
    return {
        "messages": [],
        "total": 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

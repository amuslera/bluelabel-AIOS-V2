from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Import routers
from apps.api.routers import gateway, agents, knowledge

# Load environment variables
load_dotenv()

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
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Bluelabel AIOS v2"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(gateway.router, prefix="/api/v1/gateway", tags=["gateway"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_DEBUG", "False").lower() == "true",
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

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
    allow_origins=["*"],
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

# API docs
@app.get("/api/v1/docs")
async def api_docs():
    return {"message": "API documentation available at /docs"}

if __name__ == "__main__":
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=True)
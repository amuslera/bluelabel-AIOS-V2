"""
Files router that matches frontend expectations
Handles file uploads, status tracking, and listing
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Mock data for now
mock_files = {}

# File model matching frontend interface
class FileInfo:
    def __init__(self, id: str, filename: str, content_type: str, size: int):
        self.id = id
        self.filename = filename
        self.status = "pending"
        self.size = size
        self.contentType = content_type
        self.createdAt = datetime.utcnow().isoformat()
        self.processedAt = None
        self.knowledgeId = None
        self.error = None

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status,
            "size": self.size,
            "contentType": self.contentType,
            "createdAt": self.createdAt,
            "processedAt": self.processedAt,
            "knowledgeId": self.knowledgeId,
            "error": self.error
        }

@router.post("/ingest")
async def initiate_upload(
    filename: str = Query(...),
    content_type: str = Query(...),
    size_bytes: int = Query(...)
):
    """Initiate file upload and return presigned URL"""
    file_id = str(uuid.uuid4())
    
    # Create file record
    file_info = FileInfo(file_id, filename, content_type, size_bytes)
    mock_files[file_id] = file_info
    
    # For MVP, we'll use a mock upload URL
    # In production, this would generate a presigned URL from MinIO/S3
    upload_url = f"http://localhost:8000/api/v1/files/{file_id}/upload"
    
    return {
        "fileId": file_id,
        "status": "pending",
        "uploadUrl": upload_url
    }

@router.put("/{file_id}/upload")
async def upload_file(file_id: str, file: UploadFile = File(...)):
    """Handle direct file upload"""
    if file_id not in mock_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_info = mock_files[file_id]
    
    try:
        # In production, this would save to MinIO/S3
        contents = await file.read()
        
        # Update file status
        file_info.status = "processing"
        
        # Simulate processing
        file_info.status = "completed"
        file_info.processedAt = datetime.utcnow().isoformat()
        file_info.knowledgeId = str(uuid.uuid4())
        
        logger.info(f"File {file_id} uploaded successfully")
        
        return {"status": "success"}
    except Exception as e:
        file_info.status = "failed"
        file_info.error = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}")
async def get_file_status(file_id: str):
    """Get file status - proxies to status endpoint"""
    if file_id not in mock_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    return mock_files[file_id].to_dict()

@router.get("")
async def list_files():
    """List all files for the current user"""
    return [file.to_dict() for file in mock_files.values()]

# Status endpoint
@router.get("/status/{file_id}")
async def file_status(file_id: str):
    """Alternative status endpoint"""
    return await get_file_status(file_id)
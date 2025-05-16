from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class FileIngestRequest(BaseModel):
    """Request model for file ingestion"""
    filename: str
    content_type: str
    size: int
    metadata: Optional[dict] = None

class FileIngestResponse(BaseModel):
    """Response model for file ingestion"""
    file_id: str
    upload_url: str
    expires_at: datetime

class FileConfirmRequest(BaseModel):
    """Request model for confirming file upload"""
    etag: Optional[str] = None

class FileStatusResponse(BaseModel):
    """Response model for file status"""
    id: str
    status: str
    filename: str
    content_type: str
    size: int
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    knowledge_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

class FileDownloadResponse(BaseModel):
    """Response model for file download"""
    download_url: str
    expires_at: datetime
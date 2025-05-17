"""
Simple file upload endpoints that work with current schema.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.schemas.base import User
from apps.api.dependencies.auth import get_current_user
from apps.api.dependencies.database import get_db
from core.config import get_settings

router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post("/ingest")
async def initiate_upload(
    filename: str,
    content_type: str,
    size_bytes: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate a file upload - simplified version.
    Returns a mock presigned URL for now.
    """
    settings = get_settings()
    
    # Validate file size
    max_size_bytes = 100 * 1024 * 1024  # 100MB
    if size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of 100MB"
        )
    
    # Generate file ID
    file_id = str(uuid.uuid4())
    
    # Generate storage path
    storage_path = f"uploads/{current_user.tenant_id}/{file_id}/{filename}"
    
    try:
        # Create file record
        db.execute(
            text("""
            INSERT INTO files (
                id, user_id, tenant_id, filename, content_type, 
                size, storage_path, status, created_at
            ) VALUES (
                :id, :user_id, :tenant_id, :filename, :content_type,
                :size, :storage_path, :status, :created_at
            )
            """),
            {
                "id": file_id,
                "user_id": current_user.id,
                "tenant_id": current_user.tenant_id,
                "filename": filename,
                "content_type": content_type,
                "size": size_bytes,
                "storage_path": storage_path,
                "status": "pending",
                "created_at": datetime.utcnow()
            }
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
    # For now, return a mock upload URL
    # In production, this would use MinIO or S3
    upload_url = f"http://localhost:9000/uploads/{storage_path}"
    
    # TODO: Trigger async processing here
    # from services.content.tasks import process_file_task
    # process_file_task.delay(file_id, current_user.id)
    
    return {
        "fileId": file_id,
        "status": "pending",
        "uploadUrl": upload_url
    }


@router.get("/{file_id}/status")
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the status of a file upload.
    """
    result = db.execute(
        text("""
        SELECT id as id, filename, status, size, content_type, 
               created_at, knowledge_id, error_message
        FROM files 
        WHERE id = :file_id AND user_id = :user_id
        """),
        {"file_id": file_id, "user_id": current_user.id}
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "id": str(result.id),
        "filename": result.filename,
        "status": result.status,
        "size": result.size,
        "contentType": result.content_type,
        "createdAt": result.created_at.isoformat() if result.created_at else None,
        "knowledgeId": str(result.knowledge_id) if result.knowledge_id else None,
        "error": result.error_message
    }


@router.get("/")
async def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all files for the current user.
    """
    results = db.execute(
        text("""
        SELECT id, filename, status, size, content_type, 
               created_at, knowledge_id
        FROM files 
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT 20
        """),
        {"user_id": current_user.id}
    ).all()
    
    return [
        {
            "id": str(row.id),
            "filename": row.filename,
            "status": row.status,
            "size": row.size,
            "contentType": row.content_type,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "knowledgeId": str(row.knowledge_id) if row.knowledge_id else None
        }
        for row in results
    ]
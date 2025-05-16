"""
File upload and management API endpoints.
Implements RULES.md #1: User Scoping, #2: Traceability, #11: Idempotency
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import Optional
import uuid
from datetime import datetime

from shared.schemas.base import User
from services.storage.storage_factory import get_storage
from services.storage.base import StorageService
from services.analytics import log_event, EventType
from apps.api.middleware.error_handler import ValidationError, NotFoundError
from apps.api.middleware.request_id import get_request_id
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
    storage: StorageService = Depends(get_storage),
    db = Depends(get_db),
    request_id: str = Depends(get_request_id),
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Initiate a file upload by generating a presigned URL.
    
    This endpoint creates a file record and returns a presigned URL
    for direct upload to storage. The actual file content is uploaded
    directly to storage, not through this API.
    
    Args:
        filename: Name of the file to upload
        content_type: MIME type of the file
        size_bytes: Size of the file in bytes
        x_idempotency_key: Optional key for idempotent requests
    
    Returns:
        file_id: Unique identifier for the file
        upload_url: Presigned URL for uploading
        expires_in: URL expiration time in seconds
    """
    settings = get_settings()
    
    # Validate file size
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_size_bytes:
        raise ValidationError(
            f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Check idempotency
    if x_idempotency_key:
        existing = await db.fetch_one(
            """
            SELECT id, status FROM files 
            WHERE user_id = :user_id 
            AND metadata->>'idempotency_key' = :key
            """,
            {"user_id": current_user.id, "key": x_idempotency_key}
        )
        
        if existing:
            # Return existing file info
            return {
                "file_id": str(existing["id"]),
                "status": existing["status"],
                "message": "File upload already initiated"
            }
    
    # Generate file ID
    file_id = str(uuid.uuid4())
    
    # Generate storage path
    storage_path = storage.get_storage_path(
        tenant_id=current_user.tenant_id,
        file_id=file_id,
        filename=filename
    )
    
    # Create file record
    await db.execute(
        """
        INSERT INTO files (
            id, user_id, tenant_id, filename, content_type, 
            size, storage_path, status, metadata, created_at
        ) VALUES (
            :id, :user_id, :tenant_id, :filename, :content_type,
            :size, :storage_path, :status, :metadata, :created_at
        )
        """,
        {
            "id": file_id,
            "user_id": current_user.id,
            "tenant_id": current_user.tenant_id,
            "filename": filename,
            "content_type": content_type,
            "size": size_bytes,
            "storage_path": storage_path,
            "status": "pending",
            "metadata": {
                "idempotency_key": x_idempotency_key,
                "request_id": request_id,
                "original_filename": filename
            },
            "created_at": datetime.utcnow()
        }
    )
    
    # Generate presigned upload URL
    upload_url = await storage.generate_upload_url(
        bucket="uploads",
        key=storage_path,
        content_type=content_type,
        metadata={
            "user_id": current_user.id,
            "file_id": file_id,
            "tenant_id": current_user.tenant_id
        },
        expires_in=3600  # 1 hour
    )
    
    # Log analytics event
    log_event(
        EventType.FILE_UPLOAD_INITIATED.value,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        correlation_id=request_id,
        metadata={
            "file_id": file_id,
            "filename": filename,
            "content_type": content_type,
            "size_bytes": size_bytes
        }
    )
    
    return {
        "file_id": file_id,
        "upload_url": upload_url,
        "expires_in": 3600,
        "storage_path": storage_path
    }


@router.post("/{file_id}/confirm")
async def confirm_upload(
    file_id: str,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
    db = Depends(get_db),
    request_id: str = Depends(get_request_id)
):
    """
    Confirm that a file upload has completed and trigger processing.
    
    This endpoint should be called after the client has successfully
    uploaded the file to the presigned URL.
    """
    # Get file record
    file_record = await db.fetch_one(
        """
        SELECT * FROM files 
        WHERE id = :id AND user_id = :user_id
        """,
        {"id": file_id, "user_id": current_user.id}
    )
    
    if not file_record:
        raise NotFoundError("File", file_id)
    
    if file_record["status"] != "pending":
        return {
            "file_id": file_id,
            "status": file_record["status"],
            "message": f"File already in status: {file_record['status']}"
        }
    
    # Verify file exists in storage
    file_exists = await storage.file_exists(
        bucket="uploads",
        key=file_record["storage_path"]
    )
    
    if not file_exists:
        raise ValidationError("File not found in storage. Upload may have failed.")
    
    # Update status to processing
    await db.execute(
        """
        UPDATE files 
        SET status = 'processing', updated_at = :updated_at
        WHERE id = :id
        """,
        {"id": file_id, "updated_at": datetime.utcnow()}
    )
    
    # Queue processing task
    from services.tasks.file_processor import process_file_task
    task = process_file_task.delay(
        file_id=file_id,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id
    )
    
    # Log analytics event
    log_event(
        EventType.FILE_PROCESSING_STARTED.value,
        user_id=current_user.id,
        tenant_id=current_user.tenant_id,
        correlation_id=request_id,
        metadata={
            "file_id": file_id,
            "task_id": task.id
        }
    )
    
    return {
        "file_id": file_id,
        "status": "processing",
        "task_id": task.id,
        "message": "File processing started"
    }


@router.get("/{file_id}/status")
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get the current status of a file."""
    file_record = await db.fetch_one(
        """
        SELECT id, filename, status, created_at, processed_at, 
               error_message, knowledge_id, size, content_type
        FROM files 
        WHERE id = :id AND user_id = :user_id
        """,
        {"id": file_id, "user_id": current_user.id}
    )
    
    if not file_record:
        raise NotFoundError("File", file_id)
    
    return {
        "file_id": file_record["id"],
        "filename": file_record["filename"],
        "status": file_record["status"],
        "size_bytes": file_record["size"],
        "content_type": file_record["content_type"],
        "created_at": file_record["created_at"],
        "processed_at": file_record["processed_at"],
        "error": file_record["error_message"],
        "knowledge_id": file_record["knowledge_id"]
    }


@router.get("/{file_id}/download")
async def get_download_url(
    file_id: str,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage),
    db = Depends(get_db)
):
    """Get a presigned URL to download the original file."""
    file_record = await db.fetch_one(
        """
        SELECT storage_path FROM files 
        WHERE id = :id AND user_id = :user_id
        """,
        {"id": file_id, "user_id": current_user.id}
    )
    
    if not file_record:
        raise NotFoundError("File", file_id)
    
    # Generate download URL
    download_url = await storage.generate_download_url(
        bucket="uploads",
        key=file_record["storage_path"],
        expires_in=3600  # 1 hour
    )
    
    return {
        "file_id": file_id,
        "download_url": download_url,
        "expires_in": 3600
    }


@router.get("/")
async def list_files(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List files for the current user with optional filtering."""
    query = """
        SELECT id, filename, content_type, size, status, 
               created_at, processed_at
        FROM files 
        WHERE user_id = :user_id
    """
    params = {"user_id": current_user.id}
    
    if status:
        query += " AND status = :status"
        params["status"] = status
    
    query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset
    
    files = await db.fetch_all(query, params)
    
    # Get total count
    count_query = "SELECT COUNT(*) as count FROM files WHERE user_id = :user_id"
    if status:
        count_query += " AND status = :status"
    
    total = await db.fetch_one(count_query, params)
    
    return {
        "files": [
            {
                "file_id": f["id"],
                "filename": f["filename"],
                "content_type": f["content_type"],
                "size_bytes": f["size"],
                "status": f["status"],
                "created_at": f["created_at"],
                "processed_at": f["processed_at"]
            }
            for f in files
        ],
        "total": total["count"],
        "limit": limit,
        "offset": offset
    }
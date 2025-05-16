"""
Status and workflow visibility API endpoints.
Implements RULES.md #4: Workflow status must be queryable
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from shared.schemas.base import User
from services.knowledge.repository import get_knowledge_repository
from core.config import get_settings
from apps.api.dependencies.auth import get_current_user
from apps.api.dependencies.database import get_db

router = APIRouter(prefix="/api/v1/status", tags=["status"])

@router.get("/file/{file_id}")
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get the processing status of a file.
    
    Returns:
        - file_id: Unique identifier
        - status: processing, completed, failed
        - created_at: Upload timestamp
        - processed_at: Processing completion time
        - error: Error message if failed
        - knowledge_id: Associated knowledge item if processed
    """
    # Get file record from database
    file = await db.fetch_one(
        "SELECT * FROM files WHERE id = :file_id AND user_id = :user_id",
        {"file_id": file_id, "user_id": current_user.id}
    )
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_id": file["id"],
        "filename": file["filename"],
        "status": file["status"],
        "created_at": file["created_at"],
        "processed_at": file["processed_at"],
        "error": file["error_message"],
        "size": file["size"],
        "content_type": file["content_type"],
        "knowledge_id": file["knowledge_id"]
    }


@router.get("/digest/history")
async def get_digest_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """
    Get the user's digest generation history.
    
    Returns:
        - digests: List of digest records
        - total: Total number of digests
    """
    # Get digest history
    digests = await db.fetch_all(
        """
        SELECT * FROM digests 
        WHERE user_id = :user_id 
        ORDER BY created_at DESC 
        LIMIT :limit OFFSET :offset
        """,
        {
            "user_id": current_user.id,
            "limit": limit,
            "offset": offset
        }
    )
    
    # Get total count
    total = await db.fetch_one(
        "SELECT COUNT(*) as count FROM digests WHERE user_id = :user_id",
        {"user_id": current_user.id}
    )
    
    return {
        "digests": [
            {
                "id": d["id"],
                "created_at": d["created_at"],
                "item_count": d["item_count"],
                "sent_via": d["sent_via"],
                "status": d["status"],
                "summary": d["summary"][:200] if d.get("summary") else None
            }
            for d in digests
        ],
        "total": total["count"],
        "limit": limit,
        "offset": offset
    }


@router.get("/workflow/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get the status of a workflow execution.
    
    Returns:
        - workflow_id: Unique identifier
        - status: pending, running, completed, failed
        - steps: List of workflow steps with statuses
        - started_at: Workflow start time
        - completed_at: Workflow completion time
    """
    # Get workflow record
    workflow = await db.fetch_one(
        """
        SELECT * FROM workflows 
        WHERE id = :workflow_id AND user_id = :user_id
        """,
        {"workflow_id": workflow_id, "user_id": current_user.id}
    )
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get workflow steps
    steps = await db.fetch_all(
        """
        SELECT * FROM workflow_steps 
        WHERE workflow_id = :workflow_id 
        ORDER BY step_order
        """,
        {"workflow_id": workflow_id}
    )
    
    return {
        "workflow_id": workflow["id"],
        "name": workflow["name"],
        "status": workflow["status"],
        "started_at": workflow["started_at"],
        "completed_at": workflow["completed_at"],
        "error": workflow["error_message"],
        "steps": [
            {
                "step_id": s["id"],
                "name": s["name"],
                "status": s["status"],
                "started_at": s["started_at"],
                "completed_at": s["completed_at"],
                "error": s["error_message"]
            }
            for s in steps
        ]
    }


@router.get("/processing/queue")
async def get_processing_queue(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get the current processing queue for the user.
    
    Returns:
        - queued: Number of items waiting
        - processing: Number of items being processed
        - recent_completed: Recently completed items
    """
    # Get queue stats
    stats = await db.fetch_one(
        """
        SELECT 
            COUNT(CASE WHEN status = 'queued' THEN 1 END) as queued,
            COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing
        FROM files 
        WHERE user_id = :user_id AND status IN ('queued', 'processing')
        """,
        {"user_id": current_user.id}
    )
    
    # Get recently completed
    recent = await db.fetch_all(
        """
        SELECT id, filename, status, processed_at 
        FROM files 
        WHERE user_id = :user_id AND status = 'completed'
        ORDER BY processed_at DESC 
        LIMIT 5
        """,
        {"user_id": current_user.id}
    )
    
    return {
        "queued": stats["queued"],
        "processing": stats["processing"],
        "recent_completed": [
            {
                "file_id": r["id"],
                "filename": r["filename"],
                "completed_at": r["processed_at"]
            }
            for r in recent
        ]
    }


@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=30),
    db = Depends(get_db)
):
    """
    Get analytics summary for the user.
    
    Returns:
        - files_processed: Number of files processed
        - digests_generated: Number of digests created
        - total_tokens: Total LLM tokens used
        - storage_used: Storage in bytes
    """
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get file stats
    file_stats = await db.fetch_one(
        """
        SELECT 
            COUNT(*) as total_files,
            SUM(size) as total_size
        FROM files 
        WHERE user_id = :user_id AND created_at >= :since
        """,
        {"user_id": current_user.id, "since": since}
    )
    
    # Get digest stats
    digest_stats = await db.fetch_one(
        """
        SELECT COUNT(*) as total_digests
        FROM digests 
        WHERE user_id = :user_id AND created_at >= :since
        """,
        {"user_id": current_user.id, "since": since}
    )
    
    # Get token usage (if tracked)
    token_stats = await db.fetch_one(
        """
        SELECT SUM(tokens_used) as total_tokens
        FROM llm_usage 
        WHERE user_id = :user_id AND created_at >= :since
        """,
        {"user_id": current_user.id, "since": since}
    )
    
    return {
        "period_days": days,
        "files_processed": file_stats["total_files"] or 0,
        "digests_generated": digest_stats["total_digests"] or 0,
        "total_tokens": token_stats["total_tokens"] or 0,
        "storage_used_bytes": file_stats["total_size"] or 0,
        "storage_used_mb": round((file_stats["total_size"] or 0) / (1024 * 1024), 2)
    }
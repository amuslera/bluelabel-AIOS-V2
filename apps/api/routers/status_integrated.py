"""
Status router that provides system analytics and file status
Matches frontend expectations for dashboard data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import random

router = APIRouter()

@router.get("/file/{file_id}")
async def get_file_status(file_id: str):
    """Get status of a specific file"""
    # This should integrate with the files router
    # For now, return mock data
    return {
        "id": file_id,
        "filename": "example.pdf",
        "status": "completed",
        "size": 1024000,
        "contentType": "application/pdf",
        "createdAt": datetime.utcnow().isoformat(),
        "processedAt": datetime.utcnow().isoformat(),
        "knowledgeId": "knowledge-123",
        "error": None
    }

@router.get("/analytics/summary")
async def get_analytics_summary(days: int = Query(default=7, ge=1, le=90)):
    """Get analytics summary for the specified number of days"""
    # Mock data for dashboard
    return {
        "files_processed": random.randint(10, 100),
        "digests_generated": random.randint(5, 50),
        "total_knowledge_items": random.randint(50, 500),
        "active_agents": random.randint(1, 5),
        "time_range": f"Last {days} days",
        "start_date": (datetime.utcnow() - timedelta(days=days)).isoformat(),
        "end_date": datetime.utcnow().isoformat()
    }

@router.get("/system")
async def get_system_status():
    """Get overall system status"""
    return {
        "status": "online",
        "uptime": "2d 14h 32m",
        "version": "1.0.0",
        "services": {
            "database": {"status": "ok", "lastCheck": datetime.utcnow().isoformat()},
            "redis": {"status": "ok", "lastCheck": datetime.utcnow().isoformat()},
            "storage": {"status": "ok", "lastCheck": datetime.utcnow().isoformat()},
            "email": {"status": "ok", "lastCheck": datetime.utcnow().isoformat()},
        }
    }

@router.get("/agents")
async def get_agents_status():
    """Get status of all agents"""
    return [
        {
            "id": "content_mind",
            "name": "ContentMind",
            "status": "active",
            "lastRun": datetime.utcnow().isoformat(),
            "metrics": {
                "successRate": 0.95,
                "avgExecutionTime": 2.5,
                "totalExecutions": 150
            }
        },
        {
            "id": "digest_agent",
            "name": "DigestAgent",
            "status": "active",
            "lastRun": datetime.utcnow().isoformat(),
            "metrics": {
                "successRate": 0.98,
                "avgExecutionTime": 1.2,
                "totalExecutions": 75
            }
        }
    ]
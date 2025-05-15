from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime

from services.knowledge.repository import KnowledgeRepository, ContentItem

router = APIRouter()
repo = KnowledgeRepository()

class ContentRequest(BaseModel):
    title: str
    source: str
    content_type: str
    text_content: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = {}
    user_id: Optional[str] = None
    tags: List[str] = []

class ContentResponse(BaseModel):
    id: str
    title: str
    source: str
    content_type: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    tags: List[str] = []

@router.post("/content", response_model=ContentResponse)
async def add_content(request: ContentRequest):
    """Add new content to the knowledge repository"""
    # Add content
    item = repo.add_content(
        title=request.title,
        source=request.source,
        content_type=request.content_type,
        text_content=request.text_content,
        summary=request.summary,
        metadata=request.metadata,
        user_id=request.user_id,
        tags=request.tags
    )
    
    # Convert to response
    return ContentResponse(
        id=item.id,
        title=item.title,
        source=item.source,
        content_type=item.content_type,
        summary=item.summary,
        created_at=item.created_at,
        updated_at=item.updated_at,
        user_id=item.user_id,
        tags=item.tags
    )

@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    """Get content by ID"""
    # Get content
    item = repo.get_content(content_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Content with ID '{content_id}' not found")
    
    # Convert to response
    return ContentResponse(
        id=item.id,
        title=item.title,
        source=item.source,
        content_type=item.content_type,
        summary=item.summary,
        created_at=item.created_at,
        updated_at=item.updated_at,
        user_id=item.user_id,
        tags=item.tags
    )

@router.get("/content", response_model=List[ContentResponse])
async def list_content(
    user_id: Optional[str] = None,
    content_type: Optional[str] = None,
    tag: Optional[List[str]] = Query(None),
    limit: int = 100,
    offset: int = 0
):
    """List content with optional filtering"""
    # List content
    items = repo.list_content(
        user_id=user_id,
        content_type=content_type,
        tags=tag,
        limit=limit,
        offset=offset
    )
    
    # Convert to response
    return [
        ContentResponse(
            id=item.id,
            title=item.title,
            source=item.source,
            content_type=item.content_type,
            summary=item.summary,
            created_at=item.created_at,
            updated_at=item.updated_at,
            user_id=item.user_id,
            tags=item.tags
        ) for item in items
    ]

@router.post("/search", response_model=List[ContentResponse])
async def search_content(query: str, limit: int = 10):
    """Search for content"""
    # Search content
    items = repo.search_content(query=query, limit=limit)
    
    # Convert to response
    return [
        ContentResponse(
            id=item.id,
            title=item.title,
            source=item.source,
            content_type=item.content_type,
            summary=item.summary,
            created_at=item.created_at,
            updated_at=item.updated_at,
            user_id=item.user_id,
            tags=item.tags
        ) for item in items
    ]

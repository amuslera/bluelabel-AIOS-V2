"""Knowledge Repository API endpoints"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field

from services.knowledge.factory import get_knowledge_repository
from services.knowledge.repository import ContentItem as FileContentItem

router = APIRouter()


# Pydantic models for API
class ContentRequest(BaseModel):
    """Request model for creating/updating content"""
    title: str
    source: str
    content_type: str = Field(..., description="Type: url, pdf, text, email")
    text_content: str
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None
    tags: List[str] = []


class ContentResponse(BaseModel):
    """Response model for content items"""
    id: str
    title: str
    source: str
    content_type: str
    text_content: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


def _content_to_response(item) -> ContentResponse:
    """Convert content item to response model"""
    # Handle both file-based and PostgreSQL models
    if hasattr(item, 'to_dict'):
        # PostgreSQL model
        data = item.to_dict()
        return ContentResponse(
            id=data['id'],
            title=data['title'],
            source=data['source'],
            content_type=data['content_type'],
            text_content=data['text_content'],
            summary=data.get('summary'),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now()),
            user_id=data.get('user_id'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )
    else:
        # File-based model
        return ContentResponse(
            id=item.id,
            title=item.title,
            source=item.source,
            content_type=item.content_type,
            text_content=item.text_content,
            summary=item.summary,
            created_at=item.created_at,
            updated_at=item.updated_at,
            user_id=item.user_id,
            tags=item.tags,
            metadata=item.metadata
        )


@router.post("/content", response_model=ContentResponse)
async def add_content(
    request: ContentRequest,
    repo=Depends(get_knowledge_repository)
):
    """Add new content to the knowledge repository"""
    try:
        # Check if repo has async method
        if hasattr(repo, 'add_content') and asyncio.iscoroutinefunction(repo.add_content):
            item = await repo.add_content(
                title=request.title,
                source=request.source,
                content_type=request.content_type,
                text_content=request.text_content,
                summary=request.summary,
                metadata=request.metadata,
                user_id=request.user_id,
                tags=request.tags
            )
        else:
            # Sync version
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
        
        return _content_to_response(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: str,
    repo=Depends(get_knowledge_repository)
):
    """Get content by ID"""
    try:
        # Check if repo has async method
        if hasattr(repo, 'get_content') and asyncio.iscoroutinefunction(repo.get_content):
            item = await repo.get_content(content_id)
        else:
            item = repo.get_content(content_id)
        
        if item is None:
            raise HTTPException(status_code=404, detail=f"Content with ID '{content_id}' not found")
        
        return _content_to_response(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content", response_model=List[ContentResponse])
async def list_content(
    user_id: Optional[str] = None,
    content_type: Optional[str] = None,
    tag: Optional[List[str]] = Query(None),
    limit: int = 100,
    offset: int = 0,
    repo=Depends(get_knowledge_repository)
):
    """List content with optional filtering"""
    try:
        # Check if repo has async method
        if hasattr(repo, 'list_content') and asyncio.iscoroutinefunction(repo.list_content):
            items = await repo.list_content(
                user_id=user_id,
                content_type=content_type,
                tags=tag,
                limit=limit,
                offset=offset
            )
        else:
            items = repo.list_content(
                user_id=user_id,
                content_type=content_type,
                tags=tag,
                limit=limit,
                offset=offset
            )
        
        return [_content_to_response(item) for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SearchRequest(BaseModel):
    """Request model for content search"""
    query: str
    limit: int = Field(default=10, ge=1, le=100)


@router.post("/search", response_model=List[ContentResponse])
async def search_content(
    search: SearchRequest,
    repo=Depends(get_knowledge_repository)
):
    """Search for content"""
    try:
        # Check if repo has async method
        if hasattr(repo, 'search_content') and asyncio.iscoroutinefunction(repo.search_content):
            items = await repo.search_content(query=search.query, limit=search.limit)
        else:
            items = repo.search_content(query=search.query, limit=search.limit)
        
        return [_content_to_response(item) for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: str,
    update_data: Dict[str, Any],
    repo=Depends(get_knowledge_repository)
):
    """Update a content item"""
    try:
        # Check if repo has async method
        if hasattr(repo, 'update_content') and asyncio.iscoroutinefunction(repo.update_content):
            item = await repo.update_content(content_id, **update_data)
        else:
            item = repo.update_content(content_id, **update_data)
        
        if item is None:
            raise HTTPException(status_code=404, detail=f"Content with ID '{content_id}' not found")
        
        return _content_to_response(item)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: str,
    repo=Depends(get_knowledge_repository)
):
    """Delete a content item"""
    try:
        # Check if repo has async method
        if hasattr(repo, 'delete_content') and asyncio.iscoroutinefunction(repo.delete_content):
            deleted = await repo.delete_content(content_id)
        else:
            deleted = repo.delete_content(content_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Content with ID '{content_id}' not found")
        
        return {"status": "deleted", "id": content_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
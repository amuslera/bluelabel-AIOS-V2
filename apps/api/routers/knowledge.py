"""Knowledge Repository API endpoints"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.knowledge.factory import get_knowledge_repository
from services.knowledge.repository import ContentItem as FileContentItem
from services.knowledge.models import SourceType, ContentType, KnowledgeStatus, ReviewStatus
from services.knowledge.knowledge_service import KnowledgeService
from apps.api.dependencies.database import get_db

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


# MVP Knowledge Repository Endpoints
# These use the new PostgreSQL-based knowledge_items table

class KnowledgeItemCreate(BaseModel):
    """Schema for creating a knowledge item."""
    agent_id: str
    user_id: str
    source_type: SourceType
    content_type: ContentType
    content_text: str
    source_url: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    content_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    language: str = 'en'
    confidence_score: Optional[float] = None


class KnowledgeItemUpdate(BaseModel):
    """Schema for updating a knowledge item."""
    content_text: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    content_metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    language: Optional[str] = None
    status: Optional[KnowledgeStatus] = None
    confidence_score: Optional[float] = None
    review_status: Optional[ReviewStatus] = None


class KnowledgeItemResponse(BaseModel):
    """Schema for knowledge item response."""
    id: UUID
    agent_id: str
    user_id: str
    source_type: SourceType
    source_url: Optional[str]
    source_metadata: Dict[str, Any]
    content_type: ContentType
    content_text: str
    content_metadata: Dict[str, Any]
    tags: List[str]
    categories: List[str]
    language: str
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    version: int
    parent_id: Optional[UUID]
    status: KnowledgeStatus
    confidence_score: Optional[float]
    review_status: Optional[ReviewStatus]
    
    class Config:
        orm_mode = True


class KnowledgeSearchParams(BaseModel):
    """Schema for search parameters."""
    query: Optional[str] = None
    source_types: Optional[List[SourceType]] = None
    content_types: Optional[List[ContentType]] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[KnowledgeStatus] = KnowledgeStatus.ACTIVE
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)


@router.post("/mvp/items", response_model=KnowledgeItemResponse)
async def create_knowledge_item_mvp(
    item: KnowledgeItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new knowledge item (MVP)."""
    service = KnowledgeService(db)
    try:
        created_item = await service.create_knowledge_item(**item.dict())
        return KnowledgeItemResponse.from_orm(created_item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mvp/items/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge_item_mvp(
    item_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a knowledge item by ID (MVP)."""
    service = KnowledgeService(db)
    item = await service.get_knowledge_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return KnowledgeItemResponse.from_orm(item)


@router.patch("/mvp/items/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge_item_mvp(
    item_id: UUID,
    update: KnowledgeItemUpdate,
    db: Session = Depends(get_db)
):
    """Update a knowledge item (MVP)."""
    service = KnowledgeService(db)
    try:
        updated_item = await service.update_knowledge_item(
            item_id,
            **update.dict(exclude_unset=True)
        )
        return KnowledgeItemResponse.from_orm(updated_item)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mvp/search", response_model=List[KnowledgeItemResponse])
async def search_knowledge_items_mvp(
    user_id: str,
    params: KnowledgeSearchParams,
    db: Session = Depends(get_db)
):
    """Search knowledge items with filters (MVP)."""
    service = KnowledgeService(db)
    items = await service.search_knowledge_items(
        user_id=user_id,
        **params.dict(exclude_unset=True)
    )
    return [KnowledgeItemResponse.from_orm(item) for item in items]


@router.delete("/mvp/items/{item_id}")
async def delete_knowledge_item_mvp(
    item_id: UUID,
    db: Session = Depends(get_db)
):
    """Soft delete a knowledge item (MVP)."""
    service = KnowledgeService(db)
    success = await service.delete_knowledge_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return {"status": "deleted"}
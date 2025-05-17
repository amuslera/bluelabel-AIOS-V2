"""
Unit tests for the Knowledge Repository Service
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.knowledge.models import Base, KnowledgeItem, SourceType, ContentType, KnowledgeStatus
from services.knowledge.knowledge_service import KnowledgeService


@pytest.fixture
def db_session():
    """Create a test database session."""
    # For unit tests, we'll mock the database session
    # or use a test PostgreSQL database if available
    import unittest.mock as mock
    session = mock.Mock()
    
    # Mock the necessary SQLAlchemy methods
    session.add = mock.Mock()
    session.commit = mock.Mock()
    session.rollback = mock.Mock()
    session.refresh = mock.Mock()
    session.query = mock.Mock()
    
    yield session


@pytest.fixture
def knowledge_service(db_session):
    """Create a knowledge service instance."""
    return KnowledgeService(db_session)


@pytest.mark.asyncio
async def test_create_knowledge_item(knowledge_service):
    """Test creating a knowledge item."""
    item = await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.PDF,
        content_type=ContentType.SUMMARY,
        content_text="This is a test summary of a PDF document.",
        source_url="s3://bucket/documents/test.pdf",
        tags=["test", "pdf"],
        categories=["Documents", "Test"],
        confidence_score=0.95
    )
    
    assert item.id is not None
    assert item.agent_id == "contentmind_agent"
    assert item.user_id == "user_123"
    assert item.source_type == SourceType.PDF
    assert item.content_type == ContentType.SUMMARY
    assert item.content_text == "This is a test summary of a PDF document."
    assert item.tags == ["test", "pdf"]
    assert item.categories == ["Documents", "Test"]
    assert item.confidence_score == 0.95
    assert item.status == KnowledgeStatus.ACTIVE


@pytest.mark.asyncio
async def test_get_knowledge_item(knowledge_service):
    """Test retrieving a knowledge item by ID."""
    # Create an item
    created = await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.URL,
        content_type=ContentType.EXTRACTION,
        content_text="Extracted content from a webpage."
    )
    
    # Retrieve it
    retrieved = await knowledge_service.get_knowledge_item(created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.content_text == "Extracted content from a webpage."
    assert retrieved.source_type == SourceType.URL
    assert retrieved.content_type == ContentType.EXTRACTION


@pytest.mark.asyncio
async def test_update_knowledge_item(knowledge_service):
    """Test updating a knowledge item."""
    # Create an item
    item = await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.EMAIL,
        content_type=ContentType.NOTE,
        content_text="Original note content."
    )
    
    # Update it
    updated = await knowledge_service.update_knowledge_item(
        item.id,
        content_text="Updated note content.",
        tags=["updated", "email"],
        confidence_score=0.8
    )
    
    assert updated.content_text == "Updated note content."
    assert updated.tags == ["updated", "email"]
    assert updated.confidence_score == 0.8
    assert updated.updated_at > item.created_at


@pytest.mark.asyncio
async def test_delete_knowledge_item(knowledge_service):
    """Test soft deleting a knowledge item."""
    # Create an item
    item = await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.MANUAL,
        content_type=ContentType.NOTE,
        content_text="To be deleted."
    )
    
    # Delete it
    result = await knowledge_service.delete_knowledge_item(item.id)
    assert result is True
    
    # Check it's marked as deleted
    deleted = await knowledge_service.get_knowledge_item(item.id)
    assert deleted.status == KnowledgeStatus.DELETED


@pytest.mark.asyncio
async def test_search_knowledge_items(knowledge_service):
    """Test searching knowledge items with filters."""
    # Create multiple items
    await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.PDF,
        content_type=ContentType.SUMMARY,
        content_text="Summary of AI research paper.",
        tags=["AI", "research"],
        categories=["Technology"]
    )
    
    await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.URL,
        content_type=ContentType.EXTRACTION,
        content_text="Web article about machine learning.",
        tags=["ML", "tutorial"],
        categories=["Technology"]
    )
    
    await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_456",  # Different user
        source_type=SourceType.PDF,
        content_type=ContentType.SUMMARY,
        content_text="Summary of different document.",
        tags=["other"]
    )
    
    # Search by user and content type
    results = await knowledge_service.search_knowledge_items(
        user_id="user_123",
        content_types=[ContentType.SUMMARY]
    )
    assert len(results) == 1
    assert results[0].content_type == ContentType.SUMMARY
    
    # Search by tags
    results = await knowledge_service.search_knowledge_items(
        user_id="user_123",
        tags=["AI"]
    )
    assert len(results) == 1
    assert "AI" in results[0].tags
    
    # Search by multiple filters
    results = await knowledge_service.search_knowledge_items(
        user_id="user_123",
        source_types=[SourceType.PDF, SourceType.URL],
        categories=["Technology"]
    )
    assert len(results) == 2


@pytest.mark.asyncio
async def test_bulk_create_knowledge_items(knowledge_service):
    """Test bulk creating knowledge items."""
    items_data = [
        {
            "agent_id": "contentmind_agent",
            "user_id": "user_123",
            "source_type": SourceType.PDF,
            "content_type": ContentType.SUMMARY,
            "content_text": f"Summary {i}",
            "tags": [f"tag{i}"]
        }
        for i in range(3)
    ]
    
    created_items = await knowledge_service.bulk_create_knowledge_items(items_data)
    
    assert len(created_items) == 3
    for i, item in enumerate(created_items):
        assert item.content_text == f"Summary {i}"
        assert item.tags == [f"tag{i}"]


@pytest.mark.asyncio
async def test_batch_update_tags(knowledge_service):
    """Test batch updating tags."""
    # Create multiple items
    items = []
    for i in range(3):
        item = await knowledge_service.create_knowledge_item(
            agent_id="contentmind_agent",
            user_id="user_123",
            source_type=SourceType.PDF,
            content_type=ContentType.SUMMARY,
            content_text=f"Summary {i}",
            tags=["original", f"tag{i}"]
        )
        items.append(item)
    
    # Batch update tags
    item_ids = [item.id for item in items]
    updated_count = await knowledge_service.batch_update_tags(
        item_ids=item_ids,
        tags_to_add=["new", "batch"],
        tags_to_remove=["original"]
    )
    
    assert updated_count == 3
    
    # Verify updates
    for item_id in item_ids:
        updated = await knowledge_service.get_knowledge_item(item_id)
        assert "new" in updated.tags
        assert "batch" in updated.tags
        assert "original" not in updated.tags
        assert any(f"tag{i}" in updated.tags for i in range(3))


@pytest.mark.asyncio
async def test_aggregate_by_tag(knowledge_service):
    """Test aggregating knowledge items by tag."""
    # Create items with various tags
    await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.PDF,
        content_type=ContentType.SUMMARY,
        content_text="Summary 1",
        tags=["AI", "research"]
    )
    
    await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.URL,
        content_type=ContentType.EXTRACTION,
        content_text="Summary 2",
        tags=["AI", "tutorial"]
    )
    
    await knowledge_service.create_knowledge_item(
        agent_id="contentmind_agent",
        user_id="user_123",
        source_type=SourceType.EMAIL,
        content_type=ContentType.NOTE,
        content_text="Note 1",
        tags=["research"]
    )
    
    # Aggregate
    tag_counts = await knowledge_service.aggregate_by_tag(user_id="user_123")
    
    assert tag_counts["AI"] == 2
    assert tag_counts["research"] == 2
    assert tag_counts["tutorial"] == 1
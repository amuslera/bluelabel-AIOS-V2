"""Tests for Knowledge Repository implementations"""

import pytest
import asyncio
from datetime import datetime
import tempfile
import os

from services.knowledge.repository import KnowledgeRepository
from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from services.knowledge.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def file_repository():
    """Create a file-based repository for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = KnowledgeRepository(
            data_dir=temp_dir,
            vector_db_host="localhost",
            vector_db_port=8000
        )
        yield repo


@pytest.fixture
def postgres_repository():
    """Create a PostgreSQL-based repository for testing"""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    repo = PostgresKnowledgeRepository(
        db_url="sqlite:///:memory:",
        init_db=True
    )
    repo.engine = engine
    repo.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield repo
    
    # Cleanup
    Base.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_add_content_postgres(postgres_repository):
    """Test adding content to PostgreSQL repository"""
    repo = postgres_repository
    
    # Add content
    content = await repo.add_content(
        title="Test Article",
        source="https://example.com/test",
        content_type="url",
        text_content="This is a test article about AI and machine learning.",
        summary="Test article about AI/ML",
        metadata={"author": "Test Author"},
        user_id="user123",
        tenant_id="tenant456",
        tags=["ai", "ml", "test"],
        concepts=[
            {"name": "Artificial Intelligence", "type": "topic"},
            {"name": "Machine Learning", "type": "topic"}
        ]
    )
    
    # Verify content was added
    assert content is not None
    # Use getter from within session to avoid detached object issues
    content_id = str(content.id)
    
    # Fetch the content again to avoid session issues
    retrieved = await repo.get_content(content_id)
    assert retrieved is not None


@pytest.mark.asyncio
async def test_search_content_postgres(postgres_repository):
    """Test searching content in PostgreSQL repository"""
    repo = postgres_repository
    
    # Add some test content
    await repo.add_content(
        title="AI Revolution",
        source="https://example.com/ai",
        content_type="url",
        text_content="The AI revolution is transforming industries worldwide.",
        user_id="user123",
        tags=["ai", "technology"]
    )
    
    await repo.add_content(
        title="Healthcare Innovation",
        source="https://example.com/health",
        content_type="url",
        text_content="Machine learning is revolutionizing healthcare diagnostics.",
        user_id="user123",
        tags=["healthcare", "ml"]
    )
    
    await repo.add_content(
        title="Finance Report",
        source="https://example.com/finance",
        content_type="pdf",
        text_content="Annual financial results for 2024.",
        user_id="user456",
        tags=["finance", "report"]
    )
    
    # Search tests
    results = await repo.search_content("revolution", user_id="user123")
    assert len(results) >= 1
    assert any("revolution" in r.text_content.lower() for r in results)
    
    # Filter by content type
    results = await repo.search_content("", content_types=["pdf"])
    assert len(results) == 1
    assert results[0].content_type == "pdf"


@pytest.mark.asyncio
async def test_update_content_postgres(postgres_repository):
    """Test updating content in PostgreSQL repository"""
    repo = postgres_repository
    
    # Add content
    content = await repo.add_content(
        title="Original Title",
        source="https://example.com/test",
        content_type="url",
        text_content="Original content",
        user_id="user123"
    )
    
    # Update content
    updated = await repo.update_content(
        content.id,
        title="Updated Title",
        summary="New summary added"
    )
    
    assert updated.title == "Updated Title"
    assert updated.summary == "New summary added"
    assert updated.text_content == "Original content"  # Unchanged


@pytest.mark.asyncio
async def test_delete_content_postgres(postgres_repository):
    """Test deleting content from PostgreSQL repository"""
    repo = postgres_repository
    
    # Add content
    content = await repo.add_content(
        title="To Be Deleted",
        source="https://example.com/delete",
        content_type="url",
        text_content="This will be deleted",
        user_id="user123"
    )
    
    content_id = content.id
    
    # Delete content
    deleted = await repo.delete_content(content_id)
    assert deleted is True
    
    # Verify it's gone
    retrieved = await repo.get_content(content_id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_list_content_with_filters(postgres_repository):
    """Test listing content with various filters"""
    repo = postgres_repository
    
    # Add diverse content
    await repo.add_content(
        title="User1 Article 1",
        source="https://example.com/1",
        content_type="url",
        text_content="Content 1",
        user_id="user1",
        tenant_id="tenant1",
        tags=["tech", "ai"]
    )
    
    await repo.add_content(
        title="User1 Article 2",
        source="https://example.com/2",
        content_type="pdf",
        text_content="Content 2",
        user_id="user1",
        tenant_id="tenant1",
        tags=["finance"]
    )
    
    await repo.add_content(
        title="User2 Article 1",
        source="https://example.com/3",
        content_type="url",
        text_content="Content 3",
        user_id="user2",
        tenant_id="tenant2",
        tags=["tech"]
    )
    
    # Test filters
    results = await repo.list_content(user_id="user1")
    assert len(results) == 2
    
    results = await repo.list_content(content_type="pdf")
    assert len(results) == 1
    assert results[0].content_type == "pdf"
    
    results = await repo.list_content(tags=["tech"])
    assert len(results) == 2
    
    results = await repo.list_content(tenant_id="tenant1")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_tags_management(postgres_repository):
    """Test tag management operations"""
    repo = postgres_repository
    
    # Create tags
    tag1 = await repo.get_or_create_tag("technology", "Technology related content")
    tag2 = await repo.get_or_create_tag("technology")  # Should get existing
    
    assert tag1.id == tag2.id
    assert tag1.name == "technology"
    assert tag1.description == "Technology related content"
    
    # List tags
    tags = await repo.list_tags()
    assert len(tags) >= 1
    assert any(t.name == "technology" for t in tags)


def test_file_repository_add_content(file_repository):
    """Test adding content to file-based repository"""
    repo = file_repository
    
    # Add content
    content = repo.add_content(
        title="Test File Article",
        source="https://example.com/test",
        content_type="url",
        text_content="This is a test article for file storage.",
        summary="Test article",
        metadata={"author": "Test Author"},
        user_id="user123",
        tags=["test", "file"]
    )
    
    # Verify content was added
    assert content.id is not None
    assert content.title == "Test File Article"
    assert len(content.tags) == 2
    
    # Verify file was created
    file_path = os.path.join(repo.data_dir, f"{content.id}.json")
    assert os.path.exists(file_path)


def test_file_repository_search(file_repository):
    """Test searching in file-based repository"""
    repo = file_repository
    
    # Add content
    repo.add_content(
        title="Search Test 1",
        source="https://example.com/1",
        content_type="url",
        text_content="This content contains the word python programming.",
        tags=["python", "programming"]
    )
    
    repo.add_content(
        title="Search Test 2",
        source="https://example.com/2",
        content_type="url",
        text_content="This content is about machine learning with python.",
        tags=["ml", "python"]
    )
    
    # Search by content
    results = repo.search_content("python")
    assert len(results) >= 2
    
    # Search by title
    results = repo.search_content("Search Test")
    assert len(results) >= 2
    
    # Search by tag
    results = repo.search_content("programming")
    assert len(results) >= 1
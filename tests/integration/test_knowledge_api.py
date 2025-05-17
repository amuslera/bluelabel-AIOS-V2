"""
Integration tests for the Knowledge Repository API
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from apps.api.main import app
from services.knowledge.models import SourceType, ContentType, KnowledgeStatus


TEST_USER_ID = "test_user_123"
TEST_AGENT_ID = "contentmind_agent"


@pytest.mark.asyncio
async def test_create_knowledge_item():
    """Test creating a knowledge item via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "agent_id": TEST_AGENT_ID,
            "user_id": TEST_USER_ID,
            "source_type": SourceType.PDF.value,
            "content_type": ContentType.SUMMARY.value,
            "content_text": "This is a test summary of a PDF document.",
            "source_url": "s3://bucket/documents/test.pdf",
            "tags": ["test", "pdf"],
            "categories": ["Documents", "Test"],
            "confidence_score": 0.95
        }
        
        response = await client.post("/api/v1/knowledge/mvp/items", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == TEST_AGENT_ID
        assert data["user_id"] == TEST_USER_ID
        assert data["source_type"] == SourceType.PDF.value
        assert data["content_type"] == ContentType.SUMMARY.value
        assert data["tags"] == ["test", "pdf"]
        assert data["confidence_score"] == 0.95
        assert "id" in data


@pytest.mark.asyncio
async def test_get_knowledge_item():
    """Test retrieving a knowledge item via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create an item
        create_payload = {
            "agent_id": TEST_AGENT_ID,
            "user_id": TEST_USER_ID,
            "source_type": SourceType.URL.value,
            "content_type": ContentType.EXTRACTION.value,
            "content_text": "Extracted content from a webpage."
        }
        
        create_response = await client.post("/api/v1/knowledge/mvp/items", json=create_payload)
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Now retrieve it
        response = await client.get(f"/api/v1/knowledge/mvp/items/{item_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["content_text"] == "Extracted content from a webpage."


@pytest.mark.asyncio
async def test_update_knowledge_item():
    """Test updating a knowledge item via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create an item
        create_payload = {
            "agent_id": TEST_AGENT_ID,
            "user_id": TEST_USER_ID,
            "source_type": SourceType.EMAIL.value,
            "content_type": ContentType.NOTE.value,
            "content_text": "Original note content."
        }
        
        create_response = await client.post("/api/v1/knowledge/mvp/items", json=create_payload)
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Now update it
        update_payload = {
            "content_text": "Updated note content.",
            "tags": ["updated", "email"],
            "confidence_score": 0.8
        }
        
        response = await client.patch(
            f"/api/v1/knowledge/mvp/items/{item_id}", 
            json=update_payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content_text"] == "Updated note content."
        assert data["tags"] == ["updated", "email"]
        assert data["confidence_score"] == 0.8


@pytest.mark.asyncio
async def test_search_knowledge_items():
    """Test searching knowledge items via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create multiple items
        items_to_create = [
            {
                "agent_id": TEST_AGENT_ID,
                "user_id": TEST_USER_ID,
                "source_type": SourceType.PDF.value,
                "content_type": ContentType.SUMMARY.value,
                "content_text": "Summary of AI research paper.",
                "tags": ["AI", "research"],
                "categories": ["Technology"]
            },
            {
                "agent_id": TEST_AGENT_ID,
                "user_id": TEST_USER_ID,
                "source_type": SourceType.URL.value,
                "content_type": ContentType.EXTRACTION.value,
                "content_text": "Web article about machine learning.",
                "tags": ["ML", "tutorial"],
                "categories": ["Technology"]
            }
        ]
        
        for item in items_to_create:
            await client.post("/api/v1/knowledge/mvp/items", json=item)
        
        # Search by content type
        search_params = {
            "content_types": [ContentType.SUMMARY.value]
        }
        
        response = await client.post(
            f"/api/v1/knowledge/mvp/search?user_id={TEST_USER_ID}",
            json=search_params
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(item["content_type"] == ContentType.SUMMARY.value for item in data)


@pytest.mark.asyncio
async def test_delete_knowledge_item():
    """Test deleting a knowledge item via API."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First create an item
        create_payload = {
            "agent_id": TEST_AGENT_ID,
            "user_id": TEST_USER_ID,
            "source_type": SourceType.MANUAL.value,
            "content_type": ContentType.NOTE.value,
            "content_text": "To be deleted."
        }
        
        create_response = await client.post("/api/v1/knowledge/mvp/items", json=create_payload)
        created_item = create_response.json()
        item_id = created_item["id"]
        
        # Now delete it
        response = await client.delete(f"/api/v1/knowledge/mvp/items/{item_id}")
        
        assert response.status_code == 200
        assert response.json() == {"status": "deleted"}
        
        # Verify it's soft deleted by trying to get it
        get_response = await client.get(f"/api/v1/knowledge/mvp/items/{item_id}")
        if get_response.status_code == 200:
            item = get_response.json()
            assert item["status"] == KnowledgeStatus.DELETED.value


@pytest.mark.asyncio
async def test_get_nonexistent_item():
    """Test retrieving a non-existent knowledge item."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        fake_id = str(uuid4())
        response = await client.get(f"/api/v1/knowledge/mvp/items/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
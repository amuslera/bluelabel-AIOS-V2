"""Unit tests for DigestAgentMVP."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from agents.digest_agent_mvp import DigestAgentMVP
from agents.base import AgentInput, AgentOutput
from services.knowledge.models import ContentItem


@pytest.mark.asyncio
async def test_digest_agent_initialization():
    """Test DigestAgent initialization."""
    agent = DigestAgentMVP()
    assert agent.agent_id == "digest_agent_mvp"
    assert not agent._initialized
    
    result = await agent.initialize()
    assert result is True
    assert agent._initialized


@pytest.mark.asyncio
async def test_digest_agent_process_no_summaries():
    """Test digest generation with no summaries."""
    # Mock dependencies
    mock_repo = AsyncMock()
    mock_repo.list_content.return_value = []
    
    agent = DigestAgentMVP(knowledge_repo=mock_repo)
    await agent.initialize()
    
    # Create input
    input_data = AgentInput(
        task_id="test_task",
        content={},
        metadata={"user_id": "test_user", "limit": 5}
    )
    
    # Process
    result = await agent.process(input_data)
    
    assert result.status == "success"
    assert result.result["status"] == "success"
    assert result.result["summary_count"] == 0
    assert "No summaries available" in result.result["digest"]


@pytest.mark.asyncio
async def test_digest_agent_process_with_summaries():
    """Test digest generation with summaries."""
    # Mock content items
    mock_items = [
        MagicMock(
            id="1",
            title="Test Summary 1",
            source="Source 1",
            text_content="Summary content 1",
            summary="Brief summary 1",
            created_at=datetime.now(),
            tags=[]
        ),
        MagicMock(
            id="2",
            title="Test Summary 2",
            source="Source 2",
            text_content="Summary content 2",
            summary="Brief summary 2",
            created_at=datetime.now(),
            tags=[]
        )
    ]
    
    # Mock dependencies
    mock_repo = AsyncMock()
    mock_repo.list_content.return_value = mock_items
    
    mock_router = AsyncMock()
    mock_response = MagicMock()
    mock_response.text = "Generated digest content"
    mock_router.chat.return_value = mock_response
    
    mock_prompt_manager = AsyncMock()
    mock_prompt_manager.render_prompt.return_value = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"}
    ]
    
    agent = DigestAgentMVP(
        knowledge_repo=mock_repo,
        model_router=mock_router,
        prompt_manager=mock_prompt_manager
    )
    await agent.initialize()
    
    # Create input
    input_data = AgentInput(
        task_id="test_task",
        content={},
        metadata={"user_id": "test_user", "limit": 5}
    )
    
    # Process
    result = await agent.process(input_data)
    
    assert result.status == "success"
    assert result.result["status"] == "success"
    assert result.result["summary_count"] == 2
    assert result.result["digest"] == "Generated digest content"
    
    # Verify calls
    mock_repo.list_content.assert_called_once_with(
        user_id="test_user",
        content_type="summary",
        limit=5
    )
    mock_prompt_manager.render_prompt.assert_called_once()
    mock_router.chat.assert_called_once()


@pytest.mark.asyncio
async def test_digest_agent_fallback_rendering():
    """Test fallback rendering when MCP fails."""
    # Mock content items
    mock_items = [
        MagicMock(
            id="1",
            title="Test Summary 1",
            source="Source 1",
            text_content="Summary content 1",
            summary="Brief summary 1",
            created_at=datetime.now(),
            tags=[]
        )
    ]
    
    # Mock dependencies
    mock_repo = AsyncMock()
    mock_repo.list_content.return_value = mock_items
    
    mock_prompt_manager = AsyncMock()
    mock_prompt_manager.render_prompt.side_effect = Exception("MCP error")
    
    agent = DigestAgentMVP(
        knowledge_repo=mock_repo,
        prompt_manager=mock_prompt_manager
    )
    await agent.initialize()
    
    # Create input
    input_data = AgentInput(
        task_id="test_task",
        content={},
        metadata={"user_id": "test_user", "limit": 5}
    )
    
    # Process
    result = await agent.process(input_data)
    
    assert result.status == "success"
    assert result.result["status"] == "success"
    assert result.result["summary_count"] == 1
    assert "# Daily Digest" in result.result["digest"]
    assert "Test Summary 1" in result.result["digest"]


@pytest.mark.asyncio
async def test_digest_agent_error_handling():
    """Test error handling in digest generation."""
    # Mock repository to raise error
    mock_repo = AsyncMock()
    mock_repo.list_content.side_effect = Exception("Database error")
    
    agent = DigestAgentMVP(knowledge_repo=mock_repo)
    await agent.initialize()
    
    # Create input
    input_data = AgentInput(
        task_id="test_task",
        content={},
        metadata={"user_id": "test_user", "limit": 5}
    )
    
    # Process
    result = await agent.process(input_data)
    
    assert result.status == "error"
    assert result.result["status"] == "error"
    assert "Database error" in result.result["error"]


@pytest.mark.asyncio
async def test_digest_agent_capabilities():
    """Test agent capabilities method."""
    agent = DigestAgentMVP()
    
    capabilities = agent.get_capabilities()
    
    assert capabilities["agent_id"] == "digest_agent_mvp"
    assert capabilities["type"] == "digest_generation"
    assert "knowledge_repository_query" in capabilities["features"]
    assert "mcp_prompt_rendering" in capabilities["features"]
    assert capabilities["output_format"] == "json"
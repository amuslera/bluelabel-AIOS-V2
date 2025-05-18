"""Integration tests for the DigestAgent.

This module contains tests for the DigestAgent's functionality, including:
- Unit tests for digest generation
- Error handling tests
- API endpoint tests (if implemented)
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from agents.digest_agent import DigestAgent
from agents.base import AgentInput, AgentOutput
from services.llm_router import LLMRouter, LLMMessage

# Sample test content
SAMPLE_ARTICLE = """
Artificial Intelligence (AI) is transforming industries across the globe. 
Companies like Google, Microsoft, and OpenAI are leading the way in AI research and development.
The impact of AI on healthcare, finance, and transportation is particularly significant.
"""

SAMPLE_DAILY_ITEMS = [
    {
        "title": "AI Breakthrough in Healthcare",
        "type": "article",
        "source": "Tech News",
        "content": "New AI model achieves 95% accuracy in early disease detection..."
    },
    {
        "title": "Market Update: AI Stocks Surge",
        "type": "report",
        "source": "Financial Times",
        "content": "Tech stocks rise on positive AI earnings reports..."
    }
]

@pytest_asyncio.fixture
async def mock_llm_router():
    """Create a mock LLM router for testing."""
    router = AsyncMock(spec=LLMRouter)
    
    async def mock_generate(messages, **kwargs):
        # Return different responses based on content type
        content_type = next((msg.content for msg in messages if "content_type" in msg.content), "article")
        
        if "daily_digest" in content_type:
            return LLMMessage(
                role="assistant",
                content="""# Daily Digest

## Executive Summary
Today's key developments in AI and technology.

## Top Stories
1. AI Breakthrough in Healthcare
   - New model achieves 95% accuracy
   - Potential to revolutionize diagnostics

2. Market Update
   - AI stocks show strong performance
   - Positive earnings reports drive growth

## Key Insights
- Healthcare AI adoption accelerating
- Market confidence in AI sector growing

## Recommended Actions
- Monitor healthcare AI developments
- Review investment opportunities"""
            )
        else:
            return LLMMessage(
                role="assistant",
                content="""# Article Summary

## Main Topic
AI's transformative impact across industries.

## Key Points
- AI is revolutionizing multiple sectors
- Major tech companies leading innovation
- Healthcare, finance, and transportation most affected

## Important Details
- Focus on practical applications
- Emphasis on industry transformation
- Discussion of future implications

## Significance
AI's growing influence on business and society."""
            )
    
    router.generate = AsyncMock(side_effect=mock_generate)
    return router

@pytest_asyncio.fixture
async def digest_agent(mock_llm_router):
    """Create a DigestAgent with mocked dependencies."""
    agent = DigestAgent(
        agent_id="test_digest_agent",
        llm_router=mock_llm_router
    )
    await agent.initialize()
    return agent

@pytest.mark.asyncio
async def test_article_summarization(digest_agent):
    """Test article summarization functionality."""
    # Create test input
    input_data = AgentInput(
        task_id="test-1",
        content=SAMPLE_ARTICLE,
        context={"content_type": "article"},
        metadata={
            "title": "AI Industry Overview",
            "source": "test_source",
            "date": datetime.now().isoformat()
        }
    )
    
    # Process content
    result = await digest_agent.process(input_data)
    
    # Verify result structure
    assert result.status == "success"
    assert "summary" in result.result
    assert "content_type" in result.result
    assert "word_count" in result.result
    assert "timestamp" in result.result
    
    # Verify content
    summary = result.result["summary"]
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "AI" in summary
    assert "industries" in summary.lower()

@pytest.mark.asyncio
async def test_daily_digest_creation(digest_agent):
    """Test daily digest creation from multiple items."""
    # Create test input
    input_data = AgentInput(
        task_id="test-2",
        content="",  # Content is in metadata
        context={"content_type": "daily_digest"},
        metadata={"items": SAMPLE_DAILY_ITEMS}
    )
    
    # Process content
    result = await digest_agent.process(input_data)
    
    # Verify result structure
    assert result.status == "success"
    assert "summary" in result.result
    assert "content_type" in result.result
    assert result.result["content_type"] == "daily_digest"
    
    # Verify digest content
    digest = result.result["summary"]
    assert isinstance(digest, str)
    assert "Daily Digest" in digest
    assert "Executive Summary" in digest
    assert "Top Stories" in digest
    assert "Key Insights" in digest
    assert "Recommended Actions" in digest

@pytest.mark.asyncio
async def test_error_handling(digest_agent):
    """Test error handling in digest generation."""
    # Test with empty content
    input_data = AgentInput(
        task_id="test-3",
        content="",
        context={"content_type": "article"},
        metadata={}
    )
    
    result = await digest_agent.process(input_data)
    assert result.status == "error"
    assert "error" in result.result
    
    # Test with invalid content type
    input_data = AgentInput(
        task_id="test-4",
        content=SAMPLE_ARTICLE,
        context={"content_type": "invalid_type"},
        metadata={}
    )
    
    result = await digest_agent.process(input_data)
    assert result.status == "success"  # Should fall back to article template
    assert "summary" in result.result

@pytest.mark.asyncio
async def test_batch_summarization(digest_agent):
    """Test batch summarization of multiple items."""
    items = [
        {
            "content": "First article about AI.",
            "metadata": {"title": "AI Article 1"}
        },
        {
            "content": "Second article about ML.",
            "metadata": {"title": "ML Article 2"}
        }
    ]
    
    results = await digest_agent.batch_summarize(items)
    
    assert len(results) == 2
    assert all(r.status == "success" for r in results)
    assert all("summary" in r.result for r in results)

@pytest.mark.asyncio
async def test_custom_template(digest_agent):
    """Test custom template addition and usage."""
    # Add custom template
    digest_agent.add_custom_template(
        name="custom_analysis",
        system="You are a custom content analyzer.",
        prompt="Analyze this content: {content}"
    )
    
    # Test with custom template
    input_data = AgentInput(
        task_id="test-5",
        content=SAMPLE_ARTICLE,
        context={"content_type": "custom_analysis"},
        metadata={}
    )
    
    result = await digest_agent.process(input_data)
    assert result.status == "success"
    assert "summary" in result.result

@pytest.mark.asyncio
async def test_agent_capabilities(digest_agent):
    """Test agent capabilities reporting."""
    capabilities = digest_agent.get_capabilities()
    
    assert capabilities["agent_id"] == "test_digest_agent"
    assert capabilities["type"] == "summarization"
    assert "supported_content_types" in capabilities
    assert "features" in capabilities
    assert "max_input_length" in capabilities
    assert capabilities["supports_batch"] is True 
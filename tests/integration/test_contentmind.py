import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from agents.content_mind import ContentMind, ContentType
from agents.base import AgentInput, AgentOutput
from services.mcp.prompt_manager import MCPManager
from services.llm_router import LLMRouter, LLMMessage

# Sample test content
SAMPLE_CONTENT = """
Artificial Intelligence (AI) is transforming industries across the globe. 
Companies like Google, Microsoft, and OpenAI are leading the way in AI research and development.
The impact of AI on healthcare, finance, and transportation is particularly significant.
"""

# Sample MCP component for content analysis
SAMPLE_MCP_COMPONENT = {
    "name": "content_analyzer",
    "description": "Analyzes content for key insights",
    "template": """Analyze the following content:

Title: {title}
Type: {content_type}
Source: {source}

Content:
{content}

Please provide:
1. Main Topic and Theme
2. Key Points (5-7 bullet points)
3. Important Facts and Figures
4. Insights and Implications
5. Related Topics for Further Research
6. Suggested Tags for Classification

Format your response as structured JSON.""",
    "variables": [
        {
            "name": "title",
            "description": "Content title",
            "type": "string",
            "required": True
        },
        {
            "name": "content_type",
            "description": "Type of content",
            "type": "string",
            "required": True
        },
        {
            "name": "source",
            "description": "Content source",
            "type": "string",
            "required": True
        },
        {
            "name": "content",
            "description": "Content to analyze",
            "type": "string",
            "required": True
        }
    ]
}

@pytest_asyncio.fixture
async def mock_llm_router():
    """Create a mock LLM router."""
    router = AsyncMock(spec=LLMRouter)
    
    # Mock the generate method to return a structured response
    async def mock_generate(*args, **kwargs):
        return LLMMessage(
            role="assistant",
            content='''{
                "main_topic": "AI Industry Impact",
                "key_points": [
                    "AI is transforming multiple industries globally",
                    "Major tech companies are leading AI research",
                    "Healthcare, finance, and transportation are key sectors",
                    "Significant impact on business operations",
                    "Ongoing research and development"
                ],
                "facts": {
                    "companies": ["Google", "Microsoft", "OpenAI"],
                    "sectors": ["Healthcare", "Finance", "Transportation"]
                },
                "insights": "AI is becoming a fundamental technology across industries",
                "related_topics": ["Machine Learning", "Deep Learning", "Neural Networks"],
                "tags": ["AI", "Technology", "Industry Transformation"]
            }'''
        )
    
    router.generate = mock_generate
    return router

@pytest_asyncio.fixture
async def mock_mcp_manager():
    """Create a mock MCP manager."""
    manager = MagicMock(spec=MCPManager)
    
    # Mock the render_prompt method
    def mock_render_prompt(template_id: str, variables: Dict[str, Any]) -> str:
        return SAMPLE_MCP_COMPONENT["template"].format(**variables)
    
    manager.render_prompt = mock_render_prompt
    return manager

@pytest_asyncio.fixture
async def content_mind_agent(mock_llm_router, mock_mcp_manager):
    """Create a ContentMind agent with mocked dependencies."""
    agent = ContentMind(
        agent_id="test_content_mind",
        llm_router=mock_llm_router,
        metadata={"test": True}
    )
    await agent.initialize()
    return agent

@pytest.mark.asyncio
async def test_content_processing(content_mind_agent):
    """Test the content processing flow."""
    # Create test input
    input_data = AgentInput(
        source="test",
        content={"text": SAMPLE_CONTENT},
        context={"content_type": ContentType.TEXT},
        metadata={
            "title": "AI Industry Overview",
            "source": "test_source"
        }
    )
    
    # Process content
    result = await content_mind_agent.process(input_data)
    
    # Verify result structure
    assert result.status == "success"
    assert "content_type" in result.result
    assert "analysis" in result.result
    assert "entities" in result.result
    assert "summary" in result.result
    assert "tags" in result.result
    
    # Verify content type
    assert result.result["content_type"] == "text"
    
    # Verify analysis contains expected fields
    analysis = result.result["analysis"]
    assert "main_topic" in analysis
    assert "key_points" in analysis
    assert "facts" in analysis
    assert "insights" in analysis
    assert "related_topics" in analysis
    assert "tags" in analysis

@pytest.mark.asyncio
async def test_prompt_rendering(content_mind_agent):
    """Test that prompts are rendered correctly."""
    # Create test input
    input_data = AgentInput(
        source="test",
        content={"text": SAMPLE_CONTENT},
        context={"content_type": ContentType.TEXT},
        metadata={
            "title": "AI Industry Overview",
            "source": "test_source"
        }
    )
    
    # Process content
    result = await content_mind_agent.process(input_data)
    
    # Verify prompt rendering
    assert result.status == "success"
    analysis = result.result["analysis"]
    
    # Check that the analysis contains structured data
    assert isinstance(analysis["key_points"], list)
    assert len(analysis["key_points"]) > 0
    assert isinstance(analysis["facts"], dict)
    assert isinstance(analysis["tags"], list)
    
    # Verify specific content
    assert "AI" in analysis["main_topic"]
    assert any("transforming" in point.lower() for point in analysis["key_points"])
    assert "Technology" in analysis["tags"]

@pytest.mark.asyncio
async def test_error_handling(content_mind_agent):
    """Test error handling in content processing."""
    # Test with invalid content type
    input_data = AgentInput(
        source="test",
        content={"text": ""},
        context={"content_type": "invalid_type"},
        metadata={}
    )
    
    result = await content_mind_agent.process(input_data)
    assert result.status == "error"
    assert "error" in result.result
    
    # Test with empty content
    input_data = AgentInput(
        source="test",
        content={"text": ""},
        context={"content_type": ContentType.TEXT},
        metadata={}
    )
    
    result = await content_mind_agent.process(input_data)
    assert result.status == "error"
    assert "error" in result.result 
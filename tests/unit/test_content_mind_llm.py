"""Test ContentMindLLM agent with integrated LLM router and MCP framework."""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from copy import deepcopy

from agents.content_mind_llm import ContentMindLLM
from agents.base import AgentInput, AgentOutput
from services.model_router.base import LLMResponse, LLMMessage
from services.mcp.models import PromptComponent, PromptTemplate, PromptVariable

# Mock ModelInfo since it's not yet implemented
from dataclasses import dataclass
@dataclass
class ModelInfo:
    name: str
    provider: str
    type: str
    capabilities: list


@pytest.fixture
def mock_model_router():
    router = Mock()
    router.chat = AsyncMock()
    router.complete = AsyncMock()
    router.embed = AsyncMock()
    router.config = {"default_model": "gpt-4o-mini"}
    router.get_available_models = Mock(return_value=[
        ModelInfo(
            name="gpt-4o-mini",
            provider="openai",
            type="chat",
            capabilities=["chat", "function_calling"]
        )
    ])
    return router


@pytest.fixture
def mock_prompt_manager():
    manager = Mock()
    manager.render_prompt = Mock(return_value=[
        {
            "role": "system",
            "content": "Analyze the content and provide an executive summary.\n\nFocus on key insights, decisions, and actionable items.\nMaximum 5 sentences."
        },
        {
            "role": "user",
            "content": "Content to summarize: Test content for summarization."
        }
    ])
    manager.render_component = Mock(return_value="Prompt text")
    manager.list_prompts = Mock(return_value=["content_summarizer", "extract_key_concepts"])
    return manager


@pytest.mark.asyncio
async def test_init_with_defaults():
    """Test ContentMindLLM initialization with default router and manager."""
    agent = ContentMindLLM()
    assert agent.agent_id is not None
    assert agent.name == "ContentMind LLM"
    # Router and prompt manager will be created lazily on first use
    assert not agent._initialized_router


@pytest.mark.asyncio
async def test_init_with_custom_components(mock_model_router, mock_prompt_manager):
    """Test ContentMindLLM initialization with custom components."""
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager
    )
    assert agent.model_router == mock_model_router
    assert agent.prompt_manager == mock_prompt_manager


@pytest.mark.asyncio
async def test_process_text_content(mock_model_router, mock_prompt_manager):
    """Test processing text content with LLM-based summarization."""
    # Setup
    test_content = "This is a test article about AI and machine learning."
    mock_model_router.chat = AsyncMock(return_value=LLMResponse(
        text="This article discusses AI and ML concepts. Key insight: ML is transforming industries.",
        model="gpt-4o-mini",
        provider="openai",
        metadata={
            "tokens": {"prompt": 50, "completion": 20}
        }
    ))
    
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager
    )
    
    input_data = AgentInput(
        source="email",
        metadata={
            "content_type": "text"
        },
        content={
            "content": test_content,
            "from": "test@example.com"
        }
    )
    
    # Execute
    result = await agent.process(input_data)
    
    # Verify
    assert result.status == "success"
    assert "summary" in result.result
    assert "concepts" in result.result
    assert mock_model_router.chat.call_count >= 1
    assert mock_prompt_manager.render_prompt.called


@pytest.mark.asyncio
async def test_process_url_content(mock_model_router, mock_prompt_manager):
    """Test processing URL content (mocked extraction)."""
    # Setup
    test_url = "https://example.com/article"
    mock_model_router.chat = AsyncMock(return_value=LLMResponse(
        text="Article summary: Tech innovation continues to grow.",
        model="gpt-4o-mini",
        provider="openai"
    ))
    
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager
    )
    
    # Mock the URL extraction method
    agent._extract_url_content = AsyncMock(return_value="Extracted article content about tech innovation.")
    
    input_data = AgentInput(
        source="whatsapp",
        metadata={
            "content_type": "url"
        },
        content={
            "url": test_url,
            "from": "+1234567890"
        }
    )
    
    # Execute
    result = await agent.process(input_data)
    
    # Verify
    assert result.status == "success"
    assert "summary" in result.result
    assert "concepts" in result.result
    agent._extract_url_content.assert_called_with(test_url)
    assert mock_model_router.chat.called


@pytest.mark.asyncio
async def test_extract_key_concepts(mock_model_router, mock_prompt_manager):
    """Test key concepts extraction."""
    # Setup
    test_content = "Machine learning and artificial intelligence are transforming healthcare."
    mock_model_router.complete = AsyncMock(return_value=LLMResponse(
        text="Key concepts: Machine Learning, Artificial Intelligence, Healthcare Transformation",
        model="gpt-4o-mini",
        provider="openai"
    ))
    
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager
    )
    
    # Execute
    concepts = await agent._extract_key_concepts(test_content)
    
    # Verify
    assert isinstance(concepts, list)
    assert len(concepts) >= 2
    assert all(isinstance(c, str) for c in concepts)
    mock_prompt_manager.render_prompt.called_with("extract_key_concepts", {"content": test_content})


@pytest.mark.asyncio
async def test_summarize_content(mock_model_router, mock_prompt_manager):
    """Test content summarization."""
    # Setup
    test_content = "Long article about climate change and its global impacts..."
    expected_summary = "Climate change poses significant global challenges. Immediate action required."
    
    mock_model_router.chat = AsyncMock(return_value=LLMResponse(
        text=expected_summary,
        model="gpt-4o-mini",
        provider="openai"
    ))
    
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager
    )
    
    # Execute
    summary = await agent._summarize_content(test_content)
    
    # Verify
    assert summary == expected_summary
    mock_prompt_manager.render_prompt.called_with("content_summarizer", {"content": test_content})
    mock_model_router.chat.called


@pytest.mark.asyncio
async def test_process_with_fallback(mock_model_router, mock_prompt_manager):
    """Test processing with fallback when primary model fails."""
    # Setup - simulate first call failing, then succeeding
    mock_model_router.chat = AsyncMock(side_effect=[
        Exception("Primary model failed"),
        LLMResponse(text="Fallback summary", model="gpt-3.5-turbo", provider="openai")
    ])
    mock_model_router.complete = AsyncMock(return_value=LLMResponse(
        text="Fallback concepts",
        model="gpt-3.5-turbo",
        provider="openai"
    ))
    
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager
    )
    
    input_data = AgentInput(
        source="email",
        metadata={"content_type": "text"},
        content={"content": "Test content", "from": "test@example.com"}
    )
    
    # Execute
    result = await agent.process(input_data)
    
    # Verify - should still return successful result
    assert result.status == "success"
    assert mock_model_router.chat.call_count == 1  # Only one attempt, then falls back to truncation


@pytest.mark.asyncio
async def test_generate_metadata(mock_model_router, mock_prompt_manager):
    """Test metadata generation."""
    # Setup
    test_content = "Technical article about blockchain technology"
    mock_model_router.complete = AsyncMock(return_value=LLMResponse(
        text="Category: Technology, Topic: Blockchain, Sentiment: Informative",
        model="gpt-4o-mini",
        provider="openai"
    ))
    
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager  
    )
    
    # Execute
    metadata = await agent._generate_metadata(test_content)
    
    # Verify
    assert isinstance(metadata, dict)
    assert "category" in metadata
    assert "timestamp" in metadata


@pytest.mark.asyncio
async def test_get_capabilities():
    """Test capabilities reporting."""
    agent = ContentMindLLM()
    capabilities = agent.get_capabilities()
    
    assert "content_types" in capabilities
    assert "pdf" in capabilities["content_types"]
    assert "url" in capabilities["content_types"]
    assert "text" in capabilities["content_types"]
    assert "models" in capabilities
    assert "prompts" in capabilities


@pytest.mark.asyncio
async def test_error_handling(mock_model_router, mock_prompt_manager):
    """Test error handling in process method."""
    # Setup - simulate consistent failures
    mock_model_router.chat = AsyncMock(side_effect=Exception("Model error"))
    mock_model_router.complete = AsyncMock(side_effect=Exception("Model error"))
    
    agent = ContentMindLLM(
        model_router=mock_model_router,
        prompt_manager=mock_prompt_manager
    )
    
    input_data = AgentInput(
        source="email",
        metadata={"content_type": "text"},
        content={"content": "Test content", "from": "test@example.com"}
    )
    
    # Execute
    result = await agent.process(input_data)
    
    # Verify - should return success status with fallback values
    assert result.status == "success"
    assert "summary" in result.result
    assert "concepts" in result.result
    assert "metadata" in result.result
    # But the content will be fallback values
    assert len(result.result["summary"]) > 0  # Will have truncated content
    assert result.result["concepts"] == []  # Will be empty due to error
    assert result.result["metadata"]["category"] == "Other"  # Fallback value
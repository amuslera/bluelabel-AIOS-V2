"""Unit tests for upgraded ContentMind agent with LLM integration"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from agents.content_mind import ContentMind
from agents.base import AgentInput
from services.model_router.router import ModelRouter, ProviderType
from services.model_router.base import LLMMessage, LLMProviderConfig, LLMResponse


@pytest.fixture
def mock_model_router():
    """Create a mock model router for testing"""
    router = Mock(spec=ModelRouter)
    
    # Mock chat method for different prompts
    async def mock_chat(messages, **kwargs):
        content = messages[-1].content.lower()
        
        if "summarize" in content:
            return LLMResponse(
                text="This is an AI-generated summary of the content.",
                model="mock-model",
                provider="mock-provider"
            )
        elif "extract all named entities" in content:
            return LLMResponse(
                text='[{"text": "John Smith", "type": "PERSON", "confidence": 0.9}, {"text": "TechCorp", "type": "ORGANIZATION", "confidence": 0.85}]',
                model="mock-model",
                provider="mock-provider"
            )
        elif "identify the main topics" in content:
            return LLMResponse(
                text='["technology", "business", "artificial intelligence"]',
                model="mock-model",
                provider="mock-provider"
            )
        elif "analyze the sentiment" in content:
            return LLMResponse(
                text='{"sentiment": "positive", "score": 0.8, "confidence": 0.9, "emotions": ["optimistic", "excited"]}',
                model="mock-model",
                provider="mock-provider"
            )
        else:
            return LLMResponse(
                text="Generic response",
                model="mock-model",
                provider="mock-provider"
            )
    
    router.chat = AsyncMock(side_effect=mock_chat)
    router.complete = AsyncMock(side_effect=lambda prompt, **kwargs: mock_chat([LLMMessage(role="user", content=prompt)], **kwargs))
    
    return router


@pytest.mark.asyncio
async def test_content_mind_initialization_with_router(mock_model_router):
    """Test ContentMind initialization with provided router"""
    agent = ContentMind(model_router=mock_model_router)
    await agent.initialize()
    
    assert agent.initialized is True
    assert agent.model_router is mock_model_router
    assert len(agent.tools) == 4  # Should have 4 tools registered


@pytest.mark.asyncio
async def test_content_mind_initialization_without_router():
    """Test ContentMind initialization without router (creates default)"""
    with patch('agents.content_mind.ContentMind._create_model_router') as mock_create:
        mock_create.return_value = Mock(spec=ModelRouter)
        
        agent = ContentMind()
        await agent.initialize()
        
        assert agent.initialized is True
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_process_with_llm_integration(mock_model_router):
    """Test content processing with LLM integration"""
    agent = ContentMind(model_router=mock_model_router)
    await agent.initialize()
    
    # Test input
    test_content = "John Smith, CEO of TechCorp, announced exciting new AI developments today."
    input_data = AgentInput(
        task_id="test-1",
        source="test",
        content={"text": test_content, "type": "text"},
        metadata={"timestamp": "2024-01-01"}
    )
    
    # Process content
    result = await agent.process(input_data)
    
    # Verify results
    assert result.status == "success"
    assert result.result["summary"] == "This is an AI-generated summary of the content."
    assert len(result.result["entities"]) == 2
    assert result.result["entities"][0]["text"] == "John Smith"
    assert result.result["entities"][1]["text"] == "TechCorp"
    assert "technology" in result.result["topics"]
    assert result.result["sentiment"]["sentiment"] == "positive"
    assert result.result["sentiment"]["score"] == 0.8


@pytest.mark.asyncio
async def test_llm_fallback_on_error():
    """Test fallback to simulation when LLM fails"""
    # Create router that fails
    failing_router = Mock(spec=ModelRouter)
    failing_router.chat = AsyncMock(side_effect=Exception("LLM API Error"))
    
    agent = ContentMind(model_router=failing_router)
    await agent.initialize()
    
    # Test input
    test_content = "This is a test email@example.com with a URL https://example.com"
    input_data = AgentInput(
        task_id="test-fallback",
        source="test",
        content={"text": test_content, "type": "text"},
        metadata={"timestamp": "2024-01-01"}
    )
    
    # Process content - should use fallback methods
    result = await agent.process(input_data)
    
    # Verify fallback results
    assert result.status == "success"
    assert result.result["summary"]  # Should have some summary
    assert any(entity["text"] == "email@example.com" for entity in result.result["entities"])
    assert any(entity["text"] == "https://example.com" for entity in result.result["entities"])


@pytest.mark.asyncio
async def test_empty_content_handling(mock_model_router):
    """Test handling of empty content"""
    agent = ContentMind(model_router=mock_model_router)
    await agent.initialize()
    
    # Empty content
    input_data = AgentInput(
        task_id="test-empty",
        source="test",
        content={"text": "", "type": "text"},
        metadata={"timestamp": "2024-01-01"}
    )
    
    # Process empty content
    result = await agent.process(input_data)
    
    assert result.status == "error"
    assert "No content provided" in result.error


@pytest.mark.asyncio
async def test_json_parsing_errors():
    """Test handling of JSON parsing errors from LLM"""
    router = Mock(spec=ModelRouter)
    
    # Mock chat with invalid JSON responses
    async def mock_chat_invalid_json(messages, **kwargs):
        content = messages[-1].content.lower()
        
        if "extract all named entities" in content:
            return LLMResponse(
                text="This is not valid JSON",
                model="mock-model",
                provider="mock-provider"
            )
        elif "identify the main topics" in content:
            return LLMResponse(
                text="Invalid JSON: {broken}",
                model="mock-model",
                provider="mock-provider"
            )
        else:
            return LLMResponse(
                text="Generic response",
                model="mock-model",
                provider="mock-provider"
            )
    
    router.chat = AsyncMock(side_effect=mock_chat_invalid_json)
    
    agent = ContentMind(model_router=router)
    await agent.initialize()
    
    # Test input
    test_content = "Testing JSON parsing errors"
    input_data = AgentInput(
        task_id="test-json",
        source="test",
        content={"text": test_content, "type": "text"},
        metadata={"timestamp": "2024-01-01"}
    )
    
    # Process content - should handle JSON errors gracefully
    result = await agent.process(input_data)
    
    assert result.status == "success"
    # Should use fallback or return empty results for invalid JSON
    assert isinstance(result.result["entities"], list)
    assert isinstance(result.result["topics"], list)


@pytest.mark.asyncio
async def test_concurrent_processing(mock_model_router):
    """Test that all analysis tasks run concurrently"""
    call_times = []
    
    async def mock_chat_with_timing(messages, **kwargs):
        start_time = asyncio.get_event_loop().time()
        await asyncio.sleep(0.1)  # Simulate processing time
        call_times.append(start_time)
        
        return LLMResponse(
            text="Response",
            model="mock-model",
            provider="mock-provider"
        )
    
    mock_model_router.chat = AsyncMock(side_effect=mock_chat_with_timing)
    
    agent = ContentMind(model_router=mock_model_router)
    await agent.initialize()
    
    # Test input
    input_data = AgentInput(
        task_id="test-concurrent",
        source="test",
        content={"text": "Test concurrent processing", "type": "text"},
        metadata={"timestamp": "2024-01-01"}
    )
    
    # Process content
    await agent.process(input_data)
    
    # All tasks should start at approximately the same time
    assert len(call_times) >= 3  # At least summary, entities, topics
    time_diff = max(call_times) - min(call_times)
    assert time_diff < 0.05  # Should start within 50ms of each other
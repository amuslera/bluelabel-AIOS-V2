"""Tests for the Model Router with multiple LLM providers"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import os

from services.model_router.router import ModelRouter, ProviderType, RouterStrategy
from services.model_router.base import LLMProviderConfig, LLMResponse, LLMMessage
from services.model_router.factory import (
    create_default_router,
    create_cheapest_router,
    create_fastest_router,
    create_quality_router
)


@pytest.fixture
def mock_openai_provider():
    """Create a mock OpenAI provider"""
    provider = Mock()
    provider.name = "openai"
    provider.is_available = AsyncMock(return_value=True)
    provider.chat = AsyncMock(return_value=LLMResponse(
        text="OpenAI response",
        model="gpt-4",
        provider="openai",
        usage={"total_tokens": 100}
    ))
    provider.get_capabilities = Mock(return_value={
        "models": ["gpt-4", "gpt-3.5-turbo"],
        "supports_chat": True
    })
    return provider


@pytest.fixture
def mock_anthropic_provider():
    """Create a mock Anthropic provider"""
    provider = Mock()
    provider.name = "anthropic"
    provider.is_available = AsyncMock(return_value=True)
    provider.chat = AsyncMock(return_value=LLMResponse(
        text="Claude response",
        model="claude-3-sonnet",
        provider="anthropic",
        usage={"total_tokens": 80}
    ))
    provider.get_capabilities = Mock(return_value={
        "models": ["claude-3-sonnet", "claude-3-opus"],
        "supports_chat": True
    })
    return provider


@pytest.fixture
def mock_gemini_provider():
    """Create a mock Gemini provider"""
    provider = Mock()
    provider.name = "gemini"
    provider.is_available = AsyncMock(return_value=True)
    provider.chat = AsyncMock(return_value=LLMResponse(
        text="Gemini response",
        model="gemini-pro",
        provider="gemini",
        usage={"total_tokens": 60}
    ))
    provider.get_capabilities = Mock(return_value={
        "models": ["gemini-pro", "gemini-pro-vision"],
        "supports_chat": True
    })
    return provider


@pytest.mark.asyncio
async def test_router_initialization():
    """Test basic router initialization"""
    router = ModelRouter()
    assert router.providers == {}
    assert router.default_strategy == RouterStrategy.FALLBACK
    assert router.provider_order == []


@pytest.mark.asyncio
async def test_add_provider():
    """Test adding providers to router"""
    router = ModelRouter()
    
    # Mock the provider class
    with patch('services.model_router.router.OpenAIProvider') as MockProvider:
        mock_instance = Mock()
        mock_instance.is_available = AsyncMock(return_value=True)
        MockProvider.return_value = mock_instance
        
        config = LLMProviderConfig(
            provider_name="openai",
            api_key="test-key",
            model_name="gpt-4"
        )
        
        result = await router.add_provider(ProviderType.OPENAI, config)
        assert result is True
        assert "openai" in router.providers
        assert "openai" in router.provider_order


@pytest.mark.asyncio
async def test_routing_strategies(mock_openai_provider, mock_anthropic_provider, mock_gemini_provider):
    """Test different routing strategies"""
    router = ModelRouter()
    
    # Manually add mock providers
    router.providers = {
        "openai": mock_openai_provider,
        "anthropic": mock_anthropic_provider,
        "gemini": mock_gemini_provider
    }
    router.provider_order = ["openai", "anthropic", "gemini"]
    
    # Test CHEAPEST strategy
    providers = await router._get_providers_by_strategy(RouterStrategy.CHEAPEST)
    assert providers[0] == "gemini"  # Cheapest
    assert providers[-1] == "openai"  # Most expensive
    
    # Test FASTEST strategy
    providers = await router._get_providers_by_strategy(RouterStrategy.FASTEST)
    assert providers[0] == "gemini"  # Fastest
    assert providers[-1] == "anthropic"  # Slowest
    
    # Test BEST_QUALITY strategy
    providers = await router._get_providers_by_strategy(RouterStrategy.BEST_QUALITY)
    assert providers[0] == "anthropic"  # Best quality
    assert providers[-1] == "gemini"  # Lower quality


@pytest.mark.asyncio
async def test_chat_with_fallback(mock_openai_provider, mock_anthropic_provider):
    """Test chat with fallback when primary provider fails"""
    router = ModelRouter()
    
    # Set up providers where OpenAI fails
    mock_openai_provider.chat.side_effect = Exception("OpenAI API error")
    
    router.providers = {
        "openai": mock_openai_provider,
        "anthropic": mock_anthropic_provider
    }
    router.provider_order = ["openai", "anthropic"]
    
    messages = [LLMMessage(role="user", content="Hello")]
    response = await router.chat(messages)
    
    # Should fallback to Anthropic
    assert response.provider == "anthropic"
    assert response.text == "Claude response"
    mock_openai_provider.chat.assert_called_once()
    mock_anthropic_provider.chat.assert_called_once()


@pytest.mark.asyncio
async def test_preferred_provider():
    """Test using preferred provider"""
    router = ModelRouter()
    
    with patch('services.model_router.router.OpenAIProvider') as MockOpenAI:
        with patch('services.model_router.router.AnthropicProvider') as MockAnthropic:
            mock_openai = Mock()
            mock_openai.is_available = AsyncMock(return_value=True)
            mock_openai.chat = AsyncMock(return_value=LLMResponse(
                text="OpenAI response",
                model="gpt-4",
                provider="openai"
            ))
            MockOpenAI.return_value = mock_openai
            
            mock_anthropic = Mock()
            mock_anthropic.is_available = AsyncMock(return_value=True)
            mock_anthropic.chat = AsyncMock(return_value=LLMResponse(
                text="Claude response",
                model="claude-3",
                provider="anthropic"
            ))
            MockAnthropic.return_value = mock_anthropic
            
            # Add both providers
            await router.add_provider(ProviderType.OPENAI, LLMProviderConfig(provider_name="openai"))
            await router.add_provider(ProviderType.ANTHROPIC, LLMProviderConfig(provider_name="anthropic"))
            
            # Use preferred provider
            messages = [LLMMessage(role="user", content="Hello")]
            response = await router.chat(messages, preferred_provider="anthropic")
            
            assert response.provider == "anthropic"
            mock_anthropic.chat.assert_called_once()
            mock_openai.chat.assert_not_called()


@pytest.mark.asyncio
async def test_factory_creation():
    """Test router creation through factory"""
    # Mock environment variables
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-openai-key',
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'GEMINI_API_KEY': 'test-gemini-key'
    }):
        with patch('services.model_router.factory.ModelRouter') as MockRouter:
            mock_router_instance = Mock()
            MockRouter.return_value = mock_router_instance
            mock_router_instance.add_provider = AsyncMock(return_value=True)
            mock_router_instance.get_available_providers = Mock(return_value=[
                {"name": "openai"},
                {"name": "anthropic"},
                {"name": "gemini"}
            ])
            
            router = await create_default_router()
            
            # Should have attempted to add all providers
            assert mock_router_instance.add_provider.call_count == 3
            assert mock_router_instance.set_default_strategy.called


@pytest.mark.asyncio
async def test_strategy_factories():
    """Test strategy-specific factory functions"""
    with patch('services.model_router.factory.create_default_router') as mock_create:
        # Test cheapest router
        await create_cheapest_router()
        mock_create.assert_called_with(strategy=RouterStrategy.CHEAPEST)
        
        # Test fastest router
        await create_fastest_router()
        mock_create.assert_called_with(strategy=RouterStrategy.FASTEST)
        
        # Test quality router
        await create_quality_router()
        mock_create.assert_called_with(strategy=RouterStrategy.BEST_QUALITY)


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling when all providers fail"""
    router = ModelRouter()
    
    # Create providers that all fail
    mock_provider = Mock()
    mock_provider.is_available = AsyncMock(return_value=True)
    mock_provider.chat = AsyncMock(side_effect=Exception("Provider error"))
    
    router.providers = {"test": mock_provider}
    router.provider_order = ["test"]
    
    messages = [LLMMessage(role="user", content="Hello")]
    
    with pytest.raises(Exception, match="Provider error"):
        await router.chat(messages)


@pytest.mark.asyncio
async def test_no_available_providers():
    """Test handling when no providers are available"""
    router = ModelRouter()
    
    messages = [LLMMessage(role="user", content="Hello")]
    
    with pytest.raises(RuntimeError, match="No available providers"):
        await router.chat(messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
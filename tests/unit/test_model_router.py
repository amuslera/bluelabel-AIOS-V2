"""Unit tests for Model Router with mocked providers"""

import pytest
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from services.model_router.base import (
    LLMProvider, LLMProviderConfig, LLMResponse, 
    EmbeddingResponse, LLMMessage
)
from services.model_router.router import ModelRouter, ProviderType, RouterStrategy

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self, config: LLMProviderConfig, available: bool = True, 
                 fail_on_use: bool = False):
        super().__init__(config)
        self._available = available
        self._fail_on_use = fail_on_use
        self.call_count = 0
    
    async def complete(self, prompt: str, max_tokens: int = None,
                      temperature: float = None, **kwargs) -> LLMResponse:
        self.call_count += 1
        if self._fail_on_use:
            raise Exception(f"Mock provider {self.name} failed")
            
        return LLMResponse(
            text=f"Mock response to: {prompt}",
            model="mock-model",
            provider=self.name,
            usage={"total_tokens": 10}
        )
    
    async def chat(self, messages: List[LLMMessage], max_tokens: int = None,
                   temperature: float = None, **kwargs) -> LLMResponse:
        self.call_count += 1
        if self._fail_on_use:
            raise Exception(f"Mock provider {self.name} failed")
            
        last_message = messages[-1].content if messages else ""
        return LLMResponse(
            text=f"Mock chat response to: {last_message}",
            model="mock-model",
            provider=self.name,
            usage={"total_tokens": 10}
        )
    
    async def embed(self, text: str, **kwargs) -> EmbeddingResponse:
        self.call_count += 1
        if self._fail_on_use:
            raise Exception(f"Mock provider {self.name} failed")
            
        # Generate mock embedding (10 dimensions)
        mock_embedding = [0.1 * i for i in range(10)]
        return EmbeddingResponse(
            embeddings=mock_embedding,
            model="mock-embedding",
            provider=self.name,
            usage={"total_tokens": 5}
        )
    
    async def is_available(self) -> bool:
        return self._available
    
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "models": {
                "chat": ["mock-model"],
                "embedding": ["mock-embedding"]
            },
            "max_tokens": 1000,
            "supports_functions": False,
            "supports_embeddings": True
        }

@pytest.mark.asyncio
async def test_router_initialization():
    """Test router initialization"""
    router = ModelRouter()
    assert router.providers == {}
    assert router.default_strategy == RouterStrategy.FALLBACK
    assert router.provider_order == []

@pytest.mark.asyncio
async def test_add_provider():
    """Test adding providers to router"""
    router = ModelRouter()
    
    # Create mock provider
    config = LLMProviderConfig(
        provider_name="mock1",
        model_name="mock-model"
    )
    provider = MockLLMProvider(config)
    
    # Manually add provider (since we're testing without real providers)
    router.providers["mock1"] = provider
    router.provider_order.append("mock1")
    
    assert "mock1" in router.providers
    assert "mock1" in router.provider_order

@pytest.mark.asyncio
async def test_complete_with_single_provider():
    """Test completion with single provider"""
    router = ModelRouter()
    
    # Add mock provider
    config = LLMProviderConfig(provider_name="mock1")
    provider = MockLLMProvider(config)
    router.providers["mock1"] = provider
    router.provider_order.append("mock1")
    
    # Test completion
    response = await router.complete("Test prompt")
    
    assert response.text == "Mock response to: Test prompt"
    assert response.provider == "mock1"
    assert provider.call_count == 1

@pytest.mark.asyncio
async def test_chat_with_multiple_providers():
    """Test chat with multiple providers"""
    router = ModelRouter()
    
    # Add multiple mock providers
    provider1 = MockLLMProvider(
        LLMProviderConfig(provider_name="mock1"),
        available=False  # Not available
    )
    provider2 = MockLLMProvider(
        LLMProviderConfig(provider_name="mock2"),
        available=True
    )
    
    router.providers = {"mock1": provider1, "mock2": provider2}
    router.provider_order = ["mock1", "mock2"]
    
    # Test chat - should skip mock1 and use mock2
    messages = [LLMMessage(role="user", content="Hello")]
    response = await router.chat(messages)
    
    assert response.provider == "mock2"
    assert provider1.call_count == 0  # Skipped due to unavailability
    assert provider2.call_count == 1

@pytest.mark.asyncio
async def test_fallback_strategy():
    """Test fallback routing strategy"""
    router = ModelRouter()
    router.set_default_strategy(RouterStrategy.FALLBACK)
    
    # Add providers where first one fails
    provider1 = MockLLMProvider(
        LLMProviderConfig(provider_name="mock1"),
        fail_on_use=True
    )
    provider2 = MockLLMProvider(
        LLMProviderConfig(provider_name="mock2")
    )
    
    router.providers = {"mock1": provider1, "mock2": provider2}
    router.provider_order = ["mock1", "mock2"]
    
    # Should fallback to mock2 after mock1 fails
    response = await router.complete("Test")
    
    assert response.provider == "mock2"
    assert provider1.call_count == 1
    assert provider2.call_count == 1

@pytest.mark.asyncio
async def test_embeddings():
    """Test embedding generation"""
    router = ModelRouter()
    
    # Add mock provider with embedding support
    provider = MockLLMProvider(
        LLMProviderConfig(provider_name="mock1")
    )
    router.providers["mock1"] = provider
    
    # Test embedding
    response = await router.embed("Test text")
    
    assert len(response.embeddings) == 10
    assert response.provider == "mock1"
    assert provider.call_count == 1

@pytest.mark.asyncio
async def test_preferred_provider():
    """Test using preferred provider"""
    router = ModelRouter()
    
    # Add multiple providers
    provider1 = MockLLMProvider(LLMProviderConfig(provider_name="mock1"))
    provider2 = MockLLMProvider(LLMProviderConfig(provider_name="mock2"))
    
    router.providers = {"mock1": provider1, "mock2": provider2}
    router.provider_order = ["mock1", "mock2"]
    
    # Request specific provider
    response = await router.complete("Test", preferred_provider="mock2")
    
    assert response.provider == "mock2"
    assert provider1.call_count == 0  # Not used
    assert provider2.call_count == 1

@pytest.mark.asyncio
async def test_no_available_providers():
    """Test behavior when no providers are available"""
    router = ModelRouter()
    
    # Add unavailable provider
    provider = MockLLMProvider(
        LLMProviderConfig(provider_name="mock1"),
        available=False
    )
    router.providers["mock1"] = provider
    router.provider_order = ["mock1"]
    
    # Should raise error
    with pytest.raises(RuntimeError, match="No available providers"):
        await router.complete("Test")

@pytest.mark.asyncio
async def test_provider_capabilities():
    """Test getting provider capabilities"""
    router = ModelRouter()
    
    # Add mock provider
    provider = MockLLMProvider(LLMProviderConfig(provider_name="mock1"))
    router.providers["mock1"] = provider
    
    # Get capabilities
    available = router.get_available_providers()
    
    assert len(available) == 1
    assert available[0]["name"] == "mock1"
    assert available[0]["available"] == True
    assert "capabilities" in available[0]
    assert available[0]["capabilities"]["max_tokens"] == 1000

@pytest.mark.asyncio
async def test_routing_strategies():
    """Test different routing strategies"""
    router = ModelRouter()
    
    # Add providers
    providers = {
        "openai": MockLLMProvider(LLMProviderConfig(provider_name="openai")),
        "anthropic": MockLLMProvider(LLMProviderConfig(provider_name="anthropic")),
        "ollama": MockLLMProvider(LLMProviderConfig(provider_name="ollama"))
    }
    
    for name, provider in providers.items():
        router.providers[name] = provider
        router.provider_order.append(name)
    
    # Test different strategies
    strategies = [
        RouterStrategy.CHEAPEST,
        RouterStrategy.FASTEST,
        RouterStrategy.BEST_QUALITY
    ]
    
    for strategy in strategies:
        router.set_default_strategy(strategy)
        response = await router.complete(f"Test with {strategy}")
        assert response.provider in providers
        assert response.text.startswith("Mock response")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
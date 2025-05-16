"""Model Router - Smart routing between LLM providers"""

import logging
from typing import Any, Dict, List, Optional, Type
from enum import Enum
import asyncio

from .base import LLMProvider, LLMProviderConfig, LLMResponse, EmbeddingResponse, LLMMessage
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)

class ProviderType(str, Enum):
    """Available LLM provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"

class RouterStrategy(str, Enum):
    """Routing strategies"""
    CHEAPEST = "cheapest"
    FASTEST = "fastest"
    BEST_QUALITY = "best_quality"
    FALLBACK = "fallback"
    ROUND_ROBIN = "round_robin"

class ModelRouter:
    """Routes requests to appropriate LLM providers"""
    
    PROVIDER_CLASSES = {
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.GEMINI: GeminiProvider,
        ProviderType.OLLAMA: OllamaProvider,
    }
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_strategy = RouterStrategy.FALLBACK
        self.provider_order = []
        logger.info("Initialized Model Router")
    
    async def add_provider(self, provider_type: ProviderType, config: LLMProviderConfig) -> bool:
        """Add a new provider to the router"""
        try:
            provider_class = self.PROVIDER_CLASSES.get(provider_type)
            if not provider_class:
                logger.error(f"Unknown provider type: {provider_type}")
                return False
            
            provider = provider_class(config)
            
            # Check if provider is available
            if await provider.is_available():
                self.providers[provider_type.value] = provider
                self.provider_order.append(provider_type.value)
                logger.info(f"Added provider: {provider_type.value}")
                return True
            else:
                logger.warning(f"Provider {provider_type.value} is not available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add provider {provider_type}: {e}")
            return False
    
    async def remove_provider(self, provider_type: ProviderType) -> bool:
        """Remove a provider from the router"""
        if provider_type.value in self.providers:
            del self.providers[provider_type.value]
            self.provider_order.remove(provider_type.value)
            logger.info(f"Removed provider: {provider_type.value}")
            return True
        return False
    
    async def complete(self, prompt: str, strategy: Optional[RouterStrategy] = None,
                      preferred_provider: Optional[str] = None, **kwargs) -> LLMResponse:
        """Route completion request to appropriate provider"""
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat(messages, strategy, preferred_provider, **kwargs)
    
    async def chat(self, messages: List[LLMMessage], strategy: Optional[RouterStrategy] = None,
                   preferred_provider: Optional[str] = None, **kwargs) -> LLMResponse:
        """Route chat request to appropriate provider"""
        strategy = strategy or self.default_strategy
        
        # If preferred provider is specified and available, use it
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if await provider.is_available():
                try:
                    return await provider.chat(messages, **kwargs)
                except Exception as e:
                    logger.warning(f"Preferred provider {preferred_provider} failed: {e}")
        
        # Apply routing strategy
        providers = await self._get_providers_by_strategy(strategy)
        
        # Try providers in order
        last_error = None
        for provider_name in providers:
            provider = self.providers[provider_name]
            try:
                if await provider.is_available():
                    response = await provider.chat(messages, **kwargs)
                    return response
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                last_error = e
                continue
        
        # All providers failed
        if last_error:
            raise last_error
        else:
            raise RuntimeError("No available providers")
    
    async def embed(self, text: str, preferred_provider: Optional[str] = None, 
                    **kwargs) -> EmbeddingResponse:
        """Route embedding request to appropriate provider"""
        # Embeddings typically use a specific provider
        if preferred_provider and preferred_provider in self.providers:
            provider = self.providers[preferred_provider]
            if await provider.is_available():
                return await provider.embed(text, **kwargs)
        
        # Fallback to first available provider with embedding support
        for provider_name, provider in self.providers.items():
            try:
                if await provider.is_available():
                    capabilities = provider.get_capabilities()
                    if capabilities.get("supports_embeddings", False):
                        return await provider.embed(text, **kwargs)
            except Exception as e:
                logger.warning(f"Provider {provider_name} embedding failed: {e}")
                continue
        
        raise RuntimeError("No available providers for embeddings")
    
    async def _get_providers_by_strategy(self, strategy: RouterStrategy) -> List[str]:
        """Get ordered list of providers based on strategy"""
        available_providers = []
        
        # Check availability
        for name, provider in self.providers.items():
            if await provider.is_available():
                available_providers.append(name)
        
        if not available_providers:
            return []
        
        # Apply strategy
        if strategy == RouterStrategy.FALLBACK:
            # Use the order they were added
            return [p for p in self.provider_order if p in available_providers]
        
        elif strategy == RouterStrategy.CHEAPEST:
            # Sort by cost (simplified - in real implementation would use pricing data)
            cost_order = {
                "ollama": 0,     # Free (local)
                "gemini": 1,     # Cheapest cloud
                "anthropic": 2,  # Medium cost
                "openai": 3      # Most expensive
            }
            return sorted(available_providers, key=lambda x: cost_order.get(x, 999))
        
        elif strategy == RouterStrategy.FASTEST:
            # Sort by expected latency (simplified)
            speed_order = {
                "ollama": 0,     # Local is fastest
                "gemini": 1,     # Very fast API
                "openai": 2,     # Fast API
                "anthropic": 3   # Slightly slower
            }
            return sorted(available_providers, key=lambda x: speed_order.get(x, 999))
        
        elif strategy == RouterStrategy.BEST_QUALITY:
            # Sort by expected quality (simplified)
            quality_order = {
                "anthropic": 0,  # Best for many tasks
                "openai": 1,     # Very good
                "gemini": 2,     # Good quality
                "ollama": 3      # Depends on model
            }
            return sorted(available_providers, key=lambda x: quality_order.get(x, 999))
        
        else:  # ROUND_ROBIN or unknown
            return available_providers
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get information about available providers"""
        provider_info = []
        
        for name, provider in self.providers.items():
            try:
                capabilities = provider.get_capabilities()
                provider_info.append({
                    "name": name,
                    "available": True,
                    "capabilities": capabilities
                })
            except Exception as e:
                provider_info.append({
                    "name": name,
                    "available": False,
                    "error": str(e)
                })
        
        return provider_info
    
    def set_default_strategy(self, strategy: RouterStrategy):
        """Set default routing strategy"""
        self.default_strategy = strategy
        logger.info(f"Set default routing strategy to: {strategy.value}")
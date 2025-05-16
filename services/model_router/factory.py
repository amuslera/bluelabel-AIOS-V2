"""Factory for creating model router with configured providers"""

import os
import logging
from typing import Optional, Dict, Any

from .router import ModelRouter, ProviderType, RouterStrategy
from .base import LLMProviderConfig

logger = logging.getLogger(__name__)


async def create_default_router(
    strategy: RouterStrategy = RouterStrategy.FALLBACK,
    include_providers: Optional[list] = None,
    exclude_providers: Optional[list] = None
) -> ModelRouter:
    """Create a model router with default configuration
    
    Args:
        strategy: Default routing strategy to use
        include_providers: List of providers to include (if None, includes all available)
        exclude_providers: List of providers to exclude
        
    Returns:
        Configured ModelRouter instance
    """
    router = ModelRouter()
    router.set_default_strategy(strategy)
    
    # Default to all providers if not specified
    if include_providers is None:
        include_providers = ["openai", "anthropic", "gemini"]
    
    if exclude_providers is None:
        exclude_providers = []
    
    # Configure OpenAI
    if "openai" in include_providers and "openai" not in exclude_providers:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            config = LLMProviderConfig(
                provider_name="openai",
                api_key=openai_key,
                model_name=os.getenv("OPENAI_MODEL", "gpt-4"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            )
            await router.add_provider(ProviderType.OPENAI, config)
            logger.info("Added OpenAI provider to router")
        else:
            logger.warning("OpenAI API key not found, skipping provider")
    
    # Configure Anthropic
    if "anthropic" in include_providers and "anthropic" not in exclude_providers:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            config = LLMProviderConfig(
                provider_name="anthropic",
                api_key=anthropic_key,
                model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-opus"),
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000")),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7"))
            )
            await router.add_provider(ProviderType.ANTHROPIC, config)
            logger.info("Added Anthropic provider to router")
        else:
            logger.warning("Anthropic API key not found, skipping provider")
    
    # Configure Gemini
    if "gemini" in include_providers and "gemini" not in exclude_providers:
        gemini_key = os.getenv("GOOGLE_GENERATIVEAI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if gemini_key:
            config = LLMProviderConfig(
                provider_name="gemini",
                api_key=gemini_key,
                model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "2000")),
                temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
            )
            await router.add_provider(ProviderType.GEMINI, config)
            logger.info("Added Gemini provider to router")
        else:
            logger.warning("Gemini API key not found, skipping provider")
    
    # Log available providers
    available = router.get_available_providers()
    logger.info(f"Model Router initialized with {len(available)} providers: {[p['name'] for p in available]}")
    
    return router


def create_custom_router(
    provider_configs: Dict[str, LLMProviderConfig],
    strategy: RouterStrategy = RouterStrategy.FALLBACK
) -> ModelRouter:
    """Create a model router with custom provider configurations
    
    Args:
        provider_configs: Dictionary mapping provider names to configurations
        strategy: Default routing strategy to use
        
    Returns:
        Configured ModelRouter instance
    """
    router = ModelRouter()
    router.set_default_strategy(strategy)
    
    for provider_name, config in provider_configs.items():
        try:
            provider_type = ProviderType(provider_name)
            router.add_provider(provider_type, config)
            logger.info(f"Added {provider_name} provider to router")
        except ValueError:
            logger.error(f"Unknown provider type: {provider_name}")
        except Exception as e:
            logger.error(f"Failed to add provider {provider_name}: {e}")
    
    return router


# Convenience functions for specific strategies
async def create_cheapest_router(**kwargs) -> ModelRouter:
    """Create a router optimized for cost"""
    return await create_default_router(strategy=RouterStrategy.CHEAPEST, **kwargs)


async def create_fastest_router(**kwargs) -> ModelRouter:
    """Create a router optimized for speed"""
    return await create_default_router(strategy=RouterStrategy.FASTEST, **kwargs)


async def create_quality_router(**kwargs) -> ModelRouter:
    """Create a router optimized for quality"""
    return await create_default_router(strategy=RouterStrategy.BEST_QUALITY, **kwargs)


async def create_balanced_router(**kwargs) -> ModelRouter:
    """Create a router with fallback strategy (balanced)"""
    return await create_default_router(strategy=RouterStrategy.FALLBACK, **kwargs)


# Global instance management
_router_instance: Optional[ModelRouter] = None


async def get_router_instance() -> ModelRouter:
    """Get or create a singleton router instance"""
    global _router_instance
    
    if _router_instance is None:
        _router_instance = await create_default_router()
    
    return _router_instance


def reset_router_instance():
    """Reset the global router instance (mainly for testing)"""
    global _router_instance
    _router_instance = None
"""Factory functions for creating configured Model Router instances"""

import logging
from typing import Optional

from .router import ModelRouter, ProviderType, RouterStrategy
from .config import get_default_router_config

logger = logging.getLogger(__name__)

async def create_default_router() -> ModelRouter:
    """Create a Model Router with default configuration"""
    router = ModelRouter()
    config = get_default_router_config()
    
    # Set default strategy
    router.set_default_strategy(config["default_strategy"])
    
    # Add available providers
    for provider_type, provider_config in config["providers"].items():
        if provider_config:
            try:
                success = await router.add_provider(provider_type, provider_config)
                if success:
                    logger.info(f"Successfully added {provider_type.value} provider")
                else:
                    logger.warning(f"Failed to add {provider_type.value} provider")
            except Exception as e:
                logger.error(f"Error adding {provider_type.value} provider: {e}")
    
    # Log available providers
    available = router.get_available_providers()
    logger.info(f"Model Router initialized with {len(available)} providers")
    
    return router

def get_router_instance() -> Optional[ModelRouter]:
    """Get or create a singleton router instance (for sync contexts)"""
    # This is a placeholder for dependency injection
    # In a real app, this would be managed by the DI container
    return None
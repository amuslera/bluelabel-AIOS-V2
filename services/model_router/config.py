"""Model Router Configuration"""

import os
from typing import Optional, Dict, Any

from core.config import settings
from .base import LLMProviderConfig
from .router import ProviderType, RouterStrategy

def get_openai_config() -> Optional[LLMProviderConfig]:
    """Get OpenAI configuration from environment"""
    api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return None
    
    return LLMProviderConfig(
        provider_name="openai",
        api_key=api_key,
        api_base=os.getenv("OPENAI_API_BASE"),
        model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("OPENAI_RETRY_ATTEMPTS", "3"))
    )

def get_anthropic_config() -> Optional[LLMProviderConfig]:
    """Get Anthropic configuration from environment"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        return None
    
    return LLMProviderConfig(
        provider_name="anthropic",
        api_key=api_key,
        model_name=os.getenv("ANTHROPIC_MODEL", "claude-2"),
        max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000")),
        temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
        timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("ANTHROPIC_RETRY_ATTEMPTS", "3"))
    )

def get_ollama_config() -> Optional[LLMProviderConfig]:
    """Get Ollama configuration from environment"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    return LLMProviderConfig(
        provider_name="ollama",
        api_base=base_url,
        model_name=os.getenv("OLLAMA_MODEL", "llama2"),
        max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "2000")),
        temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
        timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
        retry_attempts=int(os.getenv("OLLAMA_RETRY_ATTEMPTS", "3"))
    )

def get_default_router_config() -> Dict[str, Any]:
    """Get default router configuration"""
    return {
        "default_strategy": RouterStrategy(
            os.getenv("LLM_ROUTER_STRATEGY", RouterStrategy.FALLBACK.value)
        ),
        "providers": {
            ProviderType.OPENAI: get_openai_config(),
            ProviderType.ANTHROPIC: get_anthropic_config(),
            ProviderType.OLLAMA: get_ollama_config()
        }
    }
"""OpenAI LLM Provider Implementation"""

import logging
import os
from typing import Any, Dict, List, Optional
import openai
from openai import AsyncOpenAI
import asyncio

from .base import LLMProvider, LLMProviderConfig, LLMResponse, EmbeddingResponse, LLMMessage

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """OpenAI API provider implementation"""
    
    # Model limits and capabilities
    MODEL_LIMITS = {
        "gpt-4": {"max_tokens": 8192, "supports_functions": True},
        "gpt-4-32k": {"max_tokens": 32768, "supports_functions": True},
        "gpt-3.5-turbo": {"max_tokens": 4097, "supports_functions": True},
        "gpt-3.5-turbo-16k": {"max_tokens": 16385, "supports_functions": True},
        "text-embedding-ada-002": {"max_tokens": 8191, "supports_functions": False},
    }
    
    DEFAULT_CHAT_MODEL = "gpt-3.5-turbo"
    DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        
        # Get API key from config or environment
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided in config or environment")
        
        # Initialize client
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.api_base,
            timeout=config.timeout,
            max_retries=config.retry_attempts
        )
        
        # Set default models if not specified
        if not config.model_name:
            config.model_name = self.DEFAULT_CHAT_MODEL
            
        logger.info(f"Initialized OpenAI provider with model: {config.model_name}")
    
    async def complete(self, prompt: str, max_tokens: Optional[int] = None,
                      temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a completion using OpenAI's chat API"""
        # Convert prompt to chat format
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat(messages, max_tokens, temperature, **kwargs)
    
    async def chat(self, messages: List[LLMMessage], max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a chat completion"""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Prepare parameters
            model = kwargs.get("model", self.config.model_name)
            max_tokens = self.get_max_tokens(max_tokens)
            temperature = self.get_temperature(temperature)
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # Extract response
            choice = response.choices[0]
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return LLMResponse(
                text=choice.message.content,
                model=response.model,
                provider="openai",
                usage=usage_dict,
                metadata={
                    "finish_reason": choice.finish_reason,
                    "response_id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise
    
    async def embed(self, text: str, **kwargs) -> EmbeddingResponse:
        """Generate embeddings using OpenAI"""
        try:
            model = kwargs.get("model", self.DEFAULT_EMBEDDING_MODEL)
            
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            
            embedding_data = response.data[0]
            usage_dict = {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return EmbeddingResponse(
                embeddings=embedding_data.embedding,
                model=response.model,
                provider="openai",
                usage=usage_dict,
                metadata={
                    "embedding_index": embedding_data.index
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if OpenAI API is available"""
        try:
            # Try a simple API call with minimal tokens
            test_response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return bool(test_response.choices)
        except Exception as e:
            logger.warning(f"OpenAI availability check failed: {e}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI provider capabilities"""
        model_info = self.MODEL_LIMITS.get(
            self.config.model_name, 
            self.MODEL_LIMITS[self.DEFAULT_CHAT_MODEL]
        )
        
        return {
            "provider": "openai",
            "models": {
                "chat": list(self.MODEL_LIMITS.keys()),
                "embedding": [self.DEFAULT_EMBEDDING_MODEL]
            },
            "current_model": self.config.model_name,
            "max_tokens": model_info["max_tokens"],
            "supports_functions": model_info["supports_functions"],
            "supports_streaming": True,
            "supports_embeddings": True,
            "rate_limits": {
                "requests_per_minute": 60,  # Default tier
                "tokens_per_minute": 60000  # Default tier
            }
        }
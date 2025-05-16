"""Anthropic (Claude) LLM Provider"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
import anthropic
from anthropic import AsyncAnthropic

from .base import LLMProvider, LLMProviderConfig, LLMResponse, EmbeddingResponse, LLMMessage

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic's Claude models"""
    
    MODEL_MAPPING = {
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-sonnet": "claude-3-sonnet-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        "claude-2.1": "claude-2.1",
        "claude-instant": "claude-instant-1.2"
    }
    
    MAX_TOKENS_BY_MODEL = {
        "claude-3-opus-20240229": 4096,
        "claude-3-sonnet-20240229": 4096,
        "claude-3-haiku-20240307": 4096,
        "claude-2.1": 100000,
        "claude-instant-1.2": 100000
    }
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.client = None
        
        # Initialize Anthropic client
        if config.api_key:
            self.client = AsyncAnthropic(api_key=config.api_key)
        else:
            logger.warning("No API key provided for Anthropic provider")
    
    async def complete(self, prompt: str, max_tokens: Optional[int] = None, 
                      temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a completion for the given prompt"""
        # Convert prompt to chat format for Claude
        messages = [LLMMessage(role="user", content=prompt)]
        return await self.chat(messages, max_tokens=max_tokens, temperature=temperature, **kwargs)
    
    async def chat(self, messages: List[LLMMessage], max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a response to a conversation"""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_prompt = None
        
        for msg in messages:
            if msg.role == "system":
                # Claude handles system prompts separately
                system_prompt = msg.content
            else:
                # Convert role names
                role = "user" if msg.role == "user" else "assistant"
                anthropic_messages.append({
                    "role": role,
                    "content": msg.content
                })
        
        # Get model and parameters
        model = kwargs.get("model", self.config.model_name) or "claude-3-sonnet"
        model_id = self.MODEL_MAPPING.get(model, model)
        
        max_tokens = self.get_max_tokens(max_tokens)
        temperature = self.get_temperature(temperature)
        
        try:
            request_params = {
                "model": model_id,
                "messages": anthropic_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            if system_prompt:
                request_params["system"] = system_prompt
            
            # Add any additional parameters
            for key in ["top_p", "stop_sequences", "stream"]:
                if key in kwargs:
                    request_params[key] = kwargs[key]
            
            # Make request
            response = await self.client.messages.create(**request_params)
            
            # Format response
            return LLMResponse(
                text=response.content[0].text,
                model=model_id,
                provider="anthropic",
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                metadata={
                    "stop_reason": response.stop_reason,
                    "model_id": response.model,
                    "id": response.id
                }
            )
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    async def embed(self, text: str, **kwargs) -> EmbeddingResponse:
        """Generate embeddings for the given text
        
        Note: Anthropic doesn't provide embedding models
        """
        raise NotImplementedError("Anthropic does not provide embedding models")
    
    async def is_available(self) -> bool:
        """Check if the provider is available"""
        if not self.client:
            return False
        
        try:
            # Test with a minimal request
            await self.client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.warning(f"Anthropic availability check failed: {str(e)}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities and limitations"""
        return {
            "models": list(self.MODEL_MAPPING.keys()),
            "max_tokens": self.MAX_TOKENS_BY_MODEL,
            "supports_chat": True,
            "supports_completion": True,
            "supports_embeddings": False,
            "supports_streaming": True,
            "supports_function_calling": False,
            "supports_vision": True,  # Claude 3 models support vision
            "default_model": "claude-3-sonnet",
            "cost_ranking": 2,  # Medium cost
            "quality_ranking": 9,  # High quality
            "speed_ranking": 7,  # Good speed
        }
    
    def get_max_tokens(self, requested: Optional[int] = None) -> int:
        """Get max tokens to use, respecting provider limits"""
        model = self.config.model_name or "claude-3-sonnet"
        model_id = self.MODEL_MAPPING.get(model, model)
        
        provider_max = self.MAX_TOKENS_BY_MODEL.get(model_id, 4096)
        config_max = self.config.max_tokens
        
        # Use the minimum of all limits
        effective_max = min(provider_max, config_max)
        
        if requested:
            return min(requested, effective_max)
        return effective_max
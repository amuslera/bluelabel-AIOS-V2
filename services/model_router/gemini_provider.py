"""Google Gemini LLM Provider"""

import logging
import asyncio
from typing import Any, Dict, List, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import LLMProvider, LLMProviderConfig, LLMResponse, EmbeddingResponse, LLMMessage

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Provider for Google's Gemini models"""
    
    MODEL_MAPPING = {
        "gemini-pro": "gemini-pro",
        "gemini-pro-vision": "gemini-pro-vision",
        "gemini-1.5-pro": "gemini-1.5-pro-latest",
        "gemini-1.5-flash": "gemini-1.5-flash-latest",
    }
    
    MAX_TOKENS_BY_MODEL = {
        "gemini-pro": 32768,
        "gemini-pro-vision": 32768,
        "gemini-1.5-pro-latest": 1048576,  # 1M tokens
        "gemini-1.5-flash-latest": 1048576,  # 1M tokens
    }
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.client = None
        
        # Initialize Gemini client
        if config.api_key:
            genai.configure(api_key=config.api_key)
            self.generation_config = genai.GenerationConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
            )
            # Default to gemini-pro if not specified
            model_name = config.model_name or "gemini-pro"
            model_id = self.MODEL_MAPPING.get(model_name, model_name)
            self.model = genai.GenerativeModel(
                model_name=model_id,
                generation_config=self.generation_config
            )
        else:
            logger.warning("No API key provided for Gemini provider")
    
    async def complete(self, prompt: str, max_tokens: Optional[int] = None, 
                      temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a completion for the given prompt"""
        if not self.model:
            raise RuntimeError("Gemini model not initialized")
        
        # Update generation config if needed
        generation_config = self.generation_config
        if max_tokens or temperature is not None:
            generation_config = genai.GenerationConfig(
                temperature=temperature if temperature is not None else self.config.temperature,
                max_output_tokens=max_tokens or self.config.max_tokens,
            )
        
        try:
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            # Format response
            return LLMResponse(
                text=response.text,
                model=self.model.model_name,
                provider="gemini",
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                },
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    async def chat(self, messages: List[LLMMessage], max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a response to a conversation"""
        if not self.model:
            raise RuntimeError("Gemini model not initialized")
        
        # Update generation config if needed
        generation_config = self.generation_config
        if max_tokens or temperature is not None:
            generation_config = genai.GenerationConfig(
                temperature=temperature if temperature is not None else self.config.temperature,
                max_output_tokens=max_tokens or self.config.max_tokens,
            )
        
        try:
            # Start chat session
            chat = self.model.start_chat(history=[])
            
            # Convert messages to Gemini format and process
            for msg in messages:
                if msg.role == "system":
                    # Gemini doesn't have explicit system messages, prepend to first user message
                    continue
                elif msg.role == "user":
                    # Send user message and get response
                    response = await asyncio.to_thread(
                        chat.send_message,
                        msg.content,
                        generation_config=generation_config
                    )
                elif msg.role == "assistant":
                    # Add assistant messages to history (handled by chat session)
                    pass
            
            # Format response
            return LLMResponse(
                text=response.text,
                model=self.model.model_name,
                provider="gemini",
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count
                },
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                }
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    async def embed(self, text: str, **kwargs) -> EmbeddingResponse:
        """Generate embeddings for the given text"""
        if not self.model:
            raise RuntimeError("Gemini model not initialized")
        
        try:
            # Use the embedding model
            embed_model = genai.GenerativeModel('models/embedding-001')
            response = await asyncio.to_thread(
                embed_model.embed_content,
                text
            )
            
            return EmbeddingResponse(
                embeddings=response.embedding,
                model="embedding-001",
                provider="gemini",
                usage={
                    "tokens": len(text.split())  # Approximate
                },
                metadata={}
            )
            
        except Exception as e:
            logger.error(f"Gemini embedding error: {str(e)}")
            raise
    
    async def is_available(self) -> bool:
        """Check if the provider is available"""
        if not self.model:
            return False
        
        try:
            # Test with a minimal request
            await asyncio.to_thread(
                self.model.generate_content,
                "test",
                generation_config=genai.GenerationConfig(max_output_tokens=1)
            )
            return True
        except Exception as e:
            logger.warning(f"Gemini availability check failed: {str(e)}")
            return False
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities and limitations"""
        return {
            "models": list(self.MODEL_MAPPING.keys()),
            "max_tokens": self.MAX_TOKENS_BY_MODEL,
            "supports_chat": True,
            "supports_completion": True,
            "supports_embeddings": True,
            "supports_streaming": True,
            "supports_function_calling": True,
            "supports_vision": True,  # Pro Vision model
            "default_model": "gemini-pro",
            "cost_ranking": 1,  # Low cost
            "quality_ranking": 8,  # High quality
            "speed_ranking": 8,  # Very fast
        }
    
    def get_max_tokens(self, requested: Optional[int] = None) -> int:
        """Get max tokens to use, respecting provider limits"""
        model = self.config.model_name or "gemini-pro"
        model_id = self.MODEL_MAPPING.get(model, model)
        
        provider_max = self.MAX_TOKENS_BY_MODEL.get(model_id, 32768)
        config_max = self.config.max_tokens
        
        # Use the minimum of all limits
        effective_max = min(provider_max, config_max)
        
        if requested:
            return min(requested, effective_max)
        return effective_max
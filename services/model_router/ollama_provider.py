"""Ollama provider implementation for local LLM inference"""

import httpx
import json
from typing import List, Dict, Any, Optional
from .base import LLMProvider, LLMProviderConfig, LLMMessage, LLMResponse, EmbeddingResponse

class OllamaProvider(LLMProvider):
    """Provider for local Ollama models"""
    
    def __init__(self, config: LLMProviderConfig):
        super().__init__(config)
        self.api_base = config.metadata.get("api_base", "http://localhost:11434")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = await self.client.get(f"{self.api_base}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion using Ollama"""
        data = {
            "model": self.config.model_name,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "stream": False
        }
        
        if self.config.max_tokens:
            data["options"] = {"num_predict": self.config.max_tokens}
        
        try:
            response = await self.client.post(
                f"{self.api_base}/api/generate",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            return LLMResponse(
                text=result["response"],
                provider=self.config.provider_name,
                model=self.config.model_name,
                usage={
                    "total_tokens": len(prompt.split()) + len(result["response"].split())
                }
            )
        except Exception as e:
            return LLMResponse(
                text=f"Error: {str(e)}",
                provider=self.config.provider_name,
                model=self.config.model_name,
                error=str(e)
            )
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """Chat completion using Ollama"""
        # Convert messages to prompt format
        prompt = ""
        for msg in messages:
            if msg.role == "system":
                prompt += f"System: {msg.content}\n\n"
            elif msg.role == "user":
                prompt += f"Human: {msg.content}\n\n"
            elif msg.role == "assistant":
                prompt += f"Assistant: {msg.content}\n\n"
        
        prompt += "Assistant: "
        
        return await self.generate(prompt, **kwargs)
    
    async def embed(self, text: str, **kwargs) -> EmbeddingResponse:
        """Get embeddings using Ollama"""
        data = {
            "model": self.config.model_name,
            "prompt": text
        }
        
        try:
            response = await self.client.post(
                f"{self.api_base}/api/embeddings",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            
            return EmbeddingResponse(
                embedding=result["embedding"],
                provider=self.config.provider_name,
                model=self.config.model_name
            )
        except Exception as e:
            return EmbeddingResponse(
                embedding=[],
                provider=self.config.provider_name,
                model=self.config.model_name,
                error=str(e)
            )
    
    async def list_models(self) -> List[str]:
        """List available Ollama models"""
        try:
            response = await self.client.get(f"{self.api_base}/api/tags")
            response.raise_for_status()
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
        except:
            return []
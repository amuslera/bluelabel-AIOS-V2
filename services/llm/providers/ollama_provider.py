from typing import Dict, Any, List, Optional
from .base import LLMProvider, ChatMessage, LLMResponse
import httpx
import os
import json


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference"""
    
    def __init__(self, api_base: Optional[str] = None, model_name: str = "llama3"):
        """Initialize the Ollama provider
        
        Args:
            api_base: Base URL for Ollama API (default: http://localhost:11434)
            model_name: Name of the model to use (default: llama3)
        """
        self.api_base = api_base or os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        self.model_name = model_name
        self.client = httpx.Client(timeout=60.0)
    
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Make a chat completion request to Ollama
        
        Args:
            messages: List of chat messages
            model: Model to use (overrides default)
            temperature: Temperature for sampling
            max_tokens: Max tokens to generate
            
        Returns:
            LLMResponse with generated text
        """
        model = model or self.model_name
        
        # Convert messages to Ollama format
        prompt = ""
        for msg in messages:
            if msg.role == "system":
                prompt += f"System: {msg.content}\n\n"
            elif msg.role == "user":
                prompt += f"Human: {msg.content}\n\n"
            elif msg.role == "assistant":
                prompt += f"Assistant: {msg.content}\n\n"
        
        # Add final prompt for assistant
        prompt += "Assistant: "
        
        # Prepare request
        data = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False
        }
        
        if max_tokens:
            data["options"] = {"num_predict": max_tokens}
        
        try:
            # Make async request
            async with httpx.AsyncClient() as async_client:
                response = await async_client.post(
                    f"{self.api_base}/api/generate",
                    json=data,
                    timeout=60.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                return LLMResponse(
                    content=result["response"],
                    model=model,
                    usage={
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": len(result["response"].split()),
                        "total_tokens": len(prompt.split()) + len(result["response"].split())
                    },
                    metadata={
                        "provider": "ollama",
                        "model": model,
                        "done": result.get("done", True)
                    }
                )
        except Exception as e:
            return LLMResponse(
                content=f"Error calling Ollama API: {str(e)}",
                model=model,
                error=str(e),
                metadata={"provider": "ollama", "error": True}
            )
    
    async def embedding(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Get embeddings from Ollama
        
        Args:
            text: Text to embed
            model: Model to use for embeddings
            
        Returns:
            LLMResponse with embedding vector
        """
        model = model or self.model_name
        
        # Prepare request
        data = {
            "model": model,
            "prompt": text
        }
        
        try:
            # Make async request
            async with httpx.AsyncClient() as async_client:
                response = await async_client.post(
                    f"{self.api_base}/api/embeddings",
                    json=data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                return LLMResponse(
                    content="",
                    model=model,
                    embeddings=result["embedding"],
                    metadata={
                        "provider": "ollama",
                        "model": model,
                        "embedding_length": len(result["embedding"])
                    }
                )
        except Exception as e:
            return LLMResponse(
                content=f"Error getting embeddings from Ollama: {str(e)}",
                model=model,
                error=str(e),
                metadata={"provider": "ollama", "error": True}
            )
    
    async def list_models(self) -> List[str]:
        """List available models in Ollama
        
        Returns:
            List of model names
        """
        try:
            async with httpx.AsyncClient() as async_client:
                response = await async_client.get(
                    f"{self.api_base}/api/tags",
                    timeout=10.0
                )
                response.raise_for_status()
                
                result = response.json()
                return [model["name"] for model in result.get("models", [])]
        except Exception as e:
            print(f"Error listing Ollama models: {str(e)}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as async_client:
                response = await async_client.post(
                    f"{self.api_base}/api/pull",
                    json={"name": model_name},
                    timeout=600.0  # 10 minutes for large models
                )
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Error pulling model {model_name}: {str(e)}")
            return False
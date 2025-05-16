"""Base interface for all LLM providers"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)

class LLMMessage(BaseModel):
    """Standard message format for chat completions"""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None
    
class LLMProviderConfig(BaseModel):
    """Configuration for LLM providers"""
    provider_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    additional_config: Dict[str, Any] = {}

class LLMResponse(BaseModel):
    """Standard response from LLM providers"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    text: str
    model: str
    provider: str
    usage: Dict[str, int] = {}  # tokens used, etc.
    metadata: Dict[str, Any] = {}
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class EmbeddingResponse(BaseModel):
    """Standard response for embeddings"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    embeddings: List[float]
    model: str
    provider: str
    usage: Dict[str, int] = {}
    metadata: Dict[str, Any] = {}
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        super().__init__(**data)

class LLMProvider(ABC):
    """Base interface for all LLM providers"""
    
    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.name = config.provider_name
        logger.info(f"Initializing {self.name} provider")
    
    @abstractmethod
    async def complete(self, prompt: str, max_tokens: Optional[int] = None, 
                      temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a completion for the given prompt"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[LLMMessage], max_tokens: Optional[int] = None,
                   temperature: Optional[float] = None, **kwargs) -> LLMResponse:
        """Generate a response to a conversation"""
        pass
    
    @abstractmethod
    async def embed(self, text: str, **kwargs) -> EmbeddingResponse:
        """Generate embeddings for the given text"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities and limitations"""
        pass
    
    def get_default_model(self) -> str:
        """Get default model for this provider"""
        return self.config.model_name or "default"
    
    def get_max_tokens(self, requested: Optional[int] = None) -> int:
        """Get max tokens to use, respecting provider limits"""
        if requested:
            return min(requested, self.config.max_tokens)
        return self.config.max_tokens
    
    def get_temperature(self, requested: Optional[float] = None) -> float:
        """Get temperature to use"""
        if requested is not None:
            return requested
        return self.config.temperature
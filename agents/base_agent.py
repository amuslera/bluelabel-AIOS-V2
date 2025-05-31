"""
Simple base agent class for ROI workflow agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import uuid


class BaseAgent(ABC):
    """Simple base class for ROI workflow agents"""
    
    def __init__(self):
        self.agent_id = str(uuid.uuid4())
        self.name = "BaseAgent"
        self.description = "Base agent class"
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input and return an output"""
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return the agent's capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id
        }
    
    async def health_check(self) -> bool:
        """Check if the agent is healthy and can process requests"""
        return True
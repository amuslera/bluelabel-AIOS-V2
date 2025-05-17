from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    """Standardized input for all agents"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Standardized output from all agents"""
    task_id: str
    status: str  # "success", "error", "pending"
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class Tool(BaseModel):
    """Tool that can be used by an agent"""
    name: str
    description: str
    function: Any  # Callable
    parameters: Dict[str, Any] = Field(default_factory=dict)


class Agent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, description: str, agent_id: Optional[str] = None):
        self.name = name
        self.description = description
        self.agent_id = agent_id or str(uuid.uuid4())
        self.tools: List[Tool] = []
        # Initialize is called manually by the runtime manager
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the agent with any necessary setup"""
        pass
    
    @abstractmethod
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process the input and return an output"""
        pass
    
    async def shutdown(self) -> None:
        """Cleanup when the agent is shut down"""
        pass
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool for the agent to use"""
        self.tools.append(tool)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return the agent's capabilities"""
        return {
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "tools": [{
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            } for tool in self.tools]
        }

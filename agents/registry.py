from typing import Dict, Any, List, Optional, Type, Callable
from .base import Agent
from .content_mind import ContentMindAgent
from .gateway_agent import GatewayAgent

# Registry of agent types to agent classes
_AGENT_REGISTRY: Dict[str, Type[Agent]] = {
    "content_mind": ContentMindAgent,
    "gateway": GatewayAgent
}

# Cache of agent instances
_AGENT_INSTANCES: Dict[str, Agent] = {}

def register_agent(agent_type: str, agent_class: Type[Agent]) -> None:
    """Register an agent type
    
    Args:
        agent_type: Type name of the agent
        agent_class: Agent class
    """
    _AGENT_REGISTRY[agent_type] = agent_class

def get_agent(agent_type: str) -> Optional[Agent]:
    """Get an agent instance by type
    
    Args:
        agent_type: Type of the agent
        
    Returns:
        Agent instance or None if not found
    """
    # Check if already instantiated
    if agent_type in _AGENT_INSTANCES:
        return _AGENT_INSTANCES[agent_type]
    
    # Check if registered
    if agent_type not in _AGENT_REGISTRY:
        return None
    
    # Create instance
    agent_class = _AGENT_REGISTRY[agent_type]
    if agent_type == "gateway":
        agent = agent_class(name=agent_type)
    else:
        agent = agent_class(name=agent_type, description=f"{agent_type} Agent")
    
    # Cache instance
    _AGENT_INSTANCES[agent_type] = agent
    
    return agent

def list_agents() -> List[Dict[str, Any]]:
    """List all registered agent types
    
    Returns:
        List of agent type information
    """
    agents = []
    
    for agent_type, agent_class in _AGENT_REGISTRY.items():
        # Get or create agent instance
        agent = get_agent(agent_type)
        
        # Get capabilities
        capabilities = agent.get_capabilities()
        
        agents.append(capabilities)
    
    return agents

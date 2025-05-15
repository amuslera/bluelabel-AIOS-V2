from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid

from agents.base import AgentInput, AgentOutput

router = APIRouter()

class AgentRequest(BaseModel):
    agent_type: str
    source: str
    metadata: Dict[str, Any] = {}
    content: Dict[str, Any] = {}

@router.post("/process", response_model=AgentOutput)
async def process_with_agent(request: AgentRequest, background_tasks: BackgroundTasks):
    """Process a request with a specific agent"""
    # Import agent registry dynamically to avoid circular imports
    from agents.registry import get_agent
    
    # Get agent
    agent = get_agent(request.agent_type)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent type '{request.agent_type}' not found")
    
    # Create agent input
    agent_input = AgentInput(
        task_id=str(uuid.uuid4()),
        source=request.source,
        metadata=request.metadata,
        content=request.content
    )
    
    # Process in background
    def process_task():
        return agent.process(agent_input)
    
    # Start processing
    result = await background_tasks.add_task(process_task)
    
    return result

@router.get("/types", response_model=List[Dict[str, Any]])
async def list_agent_types():
    """List all available agent types"""
    # Import agent registry dynamically to avoid circular imports
    from agents.registry import list_agents
    
    # Get all agent types
    agents = list_agents()
    
    return agents

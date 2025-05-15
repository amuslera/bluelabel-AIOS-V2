from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid

from agents.base import AgentInput, AgentOutput
from services.agent_runtime import AgentRuntimeManager, get_runtime_manager
from core.logging import setup_logging

router = APIRouter()
logger = setup_logging(service_name="agent-api")


class AgentRequest(BaseModel):
    """Request model for agent execution"""
    agent_id: str = Field(..., description="The ID of the agent to execute")
    source: str = Field(..., description="Source of the request")
    content: Dict[str, Any] = Field(..., description="Content to process")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentInfo(BaseModel):
    """Information about an agent"""
    agent_id: str
    name: str
    description: str
    registered: bool
    instantiated: bool
    capabilities: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None


class AgentRegistration(BaseModel):
    """Model for registering a new agent"""
    agent_id: str = Field(..., description="Unique ID for the agent")
    agent_class: str = Field(..., description="Full class path of the agent")
    config: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")


@router.get("/", response_model=List[AgentInfo])
async def list_agents(runtime: AgentRuntimeManager = Depends(get_runtime_manager)):
    """List all available agents"""
    try:
        agents = runtime.list_agents()
        return [
            AgentInfo(
                agent_id=agent["agent_id"],
                name=agent.get("config", {}).get("name", agent["agent_id"]),
                description=agent.get("config", {}).get("description", ""),
                registered=agent["registered"],
                instantiated=agent["instantiated"],
                capabilities=agent.get("capabilities"),
                metrics=agent.get("metrics")
            )
            for agent in agents
        ]
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing agents: {str(e)}")


@router.get("/{agent_id}", response_model=AgentInfo)
async def get_agent_info(
    agent_id: str,
    runtime: AgentRuntimeManager = Depends(get_runtime_manager)
):
    """Get detailed information about a specific agent"""
    try:
        info = runtime.get_agent_info(agent_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        return AgentInfo(
            agent_id=info["agent_id"],
            name=info.get("config", {}).get("name", info["agent_id"]),
            description=info.get("config", {}).get("description", ""),
            registered=info["registered"],
            instantiated=info["instantiated"],
            capabilities=info.get("capabilities"),
            metrics=info.get("metrics")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting agent info: {str(e)}")


@router.post("/{agent_id}/execute", response_model=AgentOutput)
async def execute_agent(
    agent_id: str,
    request: AgentRequest,
    runtime: AgentRuntimeManager = Depends(get_runtime_manager)
):
    """Execute an agent with the given input"""
    try:
        # Validate agent_id matches request
        if agent_id != request.agent_id:
            raise HTTPException(
                status_code=400,
                detail=f"Agent ID mismatch: URL has '{agent_id}', request has '{request.agent_id}'"
            )
        
        # Create agent input
        agent_input = AgentInput(
            source=request.source,
            content=request.content,
            metadata=request.metadata
        )
        
        # Execute agent
        logger.info(f"Executing agent {agent_id} with task {agent_input.task_id}")
        result = await runtime.execute_agent(agent_id, agent_input)
        
        if result.status == "error":
            logger.error(f"Agent {agent_id} execution failed: {result.error}")
            raise HTTPException(status_code=500, detail=f"Agent execution failed: {result.error}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing agent: {str(e)}")


@router.get("/{agent_id}/capabilities")
async def get_agent_capabilities(
    agent_id: str,
    runtime: AgentRuntimeManager = Depends(get_runtime_manager)
):
    """Get the capabilities of a specific agent"""
    try:
        info = runtime.get_agent_info(agent_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        capabilities = info.get("capabilities")
        if not capabilities:
            # Try to create instance to get capabilities
            if info["registered"] and not info["instantiated"]:
                created = await runtime.create_agent_instance(agent_id)
                if created:
                    info = runtime.get_agent_info(agent_id)
                    capabilities = info.get("capabilities")
        
        if not capabilities:
            raise HTTPException(status_code=404, detail=f"No capabilities found for agent '{agent_id}'")
        
        return capabilities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting capabilities: {str(e)}")


@router.get("/metrics/all")
async def get_all_metrics(runtime: AgentRuntimeManager = Depends(get_runtime_manager)):
    """Get metrics for all agents"""
    try:
        return runtime.get_metrics()
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@router.get("/{agent_id}/metrics")
async def get_agent_metrics(
    agent_id: str,
    runtime: AgentRuntimeManager = Depends(get_runtime_manager)
):
    """Get metrics for a specific agent"""
    try:
        info = runtime.get_agent_info(agent_id)
        if not info:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        metrics = info.get("metrics")
        if not metrics:
            return {"message": f"No metrics available for agent '{agent_id}'"}
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@router.post("/register")
async def register_agent(
    registration: AgentRegistration,
    runtime: AgentRuntimeManager = Depends(get_runtime_manager)
):
    """Register a new agent class"""
    try:
        # Dynamically import the agent class
        module_path, class_name = registration.agent_class.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        agent_class = getattr(module, class_name)
        
        # Register the agent
        success = runtime.register_agent_class(
            registration.agent_id,
            agent_class,
            registration.config
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to register agent")
        
        return {"message": f"Agent '{registration.agent_id}' registered successfully"}
        
    except ImportError as e:
        logger.error(f"Failed to import agent class: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to import agent class: {str(e)}")
    except AttributeError as e:
        logger.error(f"Agent class not found: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Agent class not found: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error registering agent: {str(e)}")


# On startup, register known agents
@router.on_event("startup")
async def startup_event():
    """Register default agents on startup"""
    runtime = get_runtime_manager()
    
    # Register ContentMind agent
    try:
        from agents.content_mind import ContentMind
        runtime.register_agent_class(
            "content_mind",
            ContentMind,
            {"description": "Content processing and analysis agent"}
        )
        logger.info("Registered ContentMind agent")
    except Exception as e:
        logger.error(f"Failed to register ContentMind agent: {str(e)}")
    
    # More agents can be registered here as they are implemented
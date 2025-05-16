"""Communication API endpoints for Gateway Agent"""
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

from agents.gateway_agent import GatewayAgent
from agents.base import AgentInput, AgentOutput

router = APIRouter(prefix="/communication", tags=["communication"])

# Global Gateway Agent instance
gateway_agent: Optional[GatewayAgent] = None

async def get_gateway_agent():
    """Get or create Gateway Agent instance"""
    global gateway_agent
    
    if not gateway_agent:
        gateway_agent = GatewayAgent(name="ApiGateway")
        
        # Initialize agent
        gateway_agent.initialize()
        # Initialize channels asynchronously 
        if not await gateway_agent.initialize_channels():
            raise HTTPException(status_code=500, detail="Failed to initialize Gateway Agent channels")
    
    return gateway_agent

from pydantic import BaseModel

class SendMessageRequest(BaseModel):
    """Request model for sending messages"""
    channel: str
    to: str
    subject: Optional[str] = None
    body: str = ""
    attachments: Optional[list] = None

@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    agent: GatewayAgent = Depends(get_gateway_agent)
):
    """Send a message through the specified channel"""
    try:
        # Create agent input
        agent_input = AgentInput(
            source="api",
            content={
                "action": "send",
                "channel": request.channel,
                "to": request.to,
                "subject": request.subject,
                "body": request.body,
                "attachments": request.attachments
            }
        )
        
        # Process with agent
        result = await agent.process(agent_input)
        
        return result.result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fetch")
async def fetch_messages(
    channel: str,
    limit: int = 10,
    agent: GatewayAgent = Depends(get_gateway_agent)
):
    """Fetch messages from the specified channel"""
    try:
        # Create agent input
        agent_input = AgentInput(
            source="api",
            content={
                "action": "fetch",
                "channel": channel,
                "limit": limit
            }
        )
        
        # Process with agent
        result = await agent.process(agent_input)
        
        return result.result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{channel}")
async def channel_status(
    channel: str,
    agent: GatewayAgent = Depends(get_gateway_agent)
):
    """Get status of a specific communication channel"""
    try:
        # Create agent input
        agent_input = AgentInput(
            source="api",
            content={
                "action": "status",
                "channel": channel
            }
        )
        
        # Process with agent
        result = await agent.process(agent_input)
        
        return result.result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_capabilities(agent: GatewayAgent = Depends(get_gateway_agent)):
    """Get Gateway Agent capabilities"""
    return agent.get_capabilities()

@router.get("/metrics")
async def get_metrics(agent: GatewayAgent = Depends(get_gateway_agent)):
    """Get Gateway Agent metrics"""
    return {
        "status": agent.status.value,
        "metrics": agent.metrics,
        "capabilities": agent.get_capabilities()
    }
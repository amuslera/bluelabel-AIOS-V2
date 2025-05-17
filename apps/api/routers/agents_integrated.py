"""
Simplified agents router that matches frontend expectations
Provides mock data until the full agent system is operational
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid

router = APIRouter()

# Mock agents data
MOCK_AGENTS = [
    {
        "id": "content_mind",
        "name": "ContentMind",
        "type": "processor",
        "status": "active",
        "lastRun": datetime.utcnow().isoformat(),
        "metrics": {
            "successRate": 0.95,
            "avgExecutionTime": 2.5,
            "totalExecutions": 150
        }
    },
    {
        "id": "digest_agent",
        "name": "DigestAgent",
        "type": "aggregator",
        "status": "active",
        "lastRun": datetime.utcnow().isoformat(),
        "metrics": {
            "successRate": 0.98,
            "avgExecutionTime": 1.2,
            "totalExecutions": 75
        }
    },
    {
        "id": "email_gateway",
        "name": "EmailGateway",
        "type": "communication",
        "status": "active",
        "lastRun": datetime.utcnow().isoformat(),
        "metrics": {
            "successRate": 0.99,
            "avgExecutionTime": 0.8,
            "totalExecutions": 200
        }
    }
]

@router.get("")
async def list_agents():
    """List all available agents"""
    return MOCK_AGENTS

@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get details for a specific agent"""
    agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@router.post("/{agent_id}/execute")
async def execute_agent(agent_id: str, input_data: Dict[str, Any]):
    """Execute an agent with given input"""
    agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Mock execution
    execution_id = str(uuid.uuid4())
    
    return {
        "agentId": agent_id,
        "executionId": execution_id,
        "input": input_data,
        "output": {
            "result": f"Processed by {agent['name']}",
            "processedAt": datetime.utcnow().isoformat()
        },
        "status": "completed",
        "startTime": datetime.utcnow().isoformat(),
        "endTime": datetime.utcnow().isoformat(),
        "error": None
    }

@router.get("/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get metrics for a specific agent"""
    agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agent.get("metrics", {})
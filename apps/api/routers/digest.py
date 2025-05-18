"""Digest API Router for MVP."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from agents.digest_agent_mvp import DigestAgentMVP
from agents.base import AgentInput
from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from services.model_router.router import ModelRouter
from services.mcp.prompt_manager import MCPManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/digest", tags=["digest"])


# Request and response models
class DigestRequest(BaseModel):
    """Request model for digest generation."""
    user_id: Optional[str] = None
    limit: Optional[int] = 10


class DigestResponse(BaseModel):
    """Response model for digest generation."""
    status: str
    digest: Optional[str] = None
    summary_count: Optional[int] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


# Dependency to get the digest agent
async def get_digest_agent() -> DigestAgentMVP:
    """Get or create a DigestAgent instance."""
    # In production, this should be a singleton or managed instance
    agent = DigestAgentMVP()
    agent.initialize()
    return agent


@router.post("/mvp/", response_model=DigestResponse)
async def generate_digest(
    request: DigestRequest,
    agent: DigestAgentMVP = Depends(get_digest_agent)
) -> DigestResponse:
    """Generate a digest from Knowledge Repository summaries.
    
    Args:
        request: Digest generation request parameters
        agent: DigestAgent instance
        
    Returns:
        Digest response with formatted text or error
    """
    try:
        logger.info(f"Received digest request: user_id={request.user_id}, limit={request.limit}")
        
        # Create agent input
        agent_input = AgentInput(
            task_id=f"digest_{request.user_id or 'all'}_{request.limit}",
            content={},
            metadata={
                "user_id": request.user_id,
                "limit": request.limit
            }
        )
        
        # Process the request
        result = await agent.process(agent_input)
        
        # Return the result
        if result.status == "success":
            return DigestResponse(**result.result)
        else:
            return DigestResponse(
                status="error",
                error=result.result.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        return DigestResponse(
            status="error",
            error=str(e)
        )
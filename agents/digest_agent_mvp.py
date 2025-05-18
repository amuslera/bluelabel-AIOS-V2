"""DigestAgent MVP Implementation.

This agent queries the Knowledge Repository for summaries and uses MCP
to generate formatted digests.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base import Agent, AgentInput, AgentOutput
from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from services.model_router.router import ModelRouter
from services.mcp.prompt_manager import MCPManager

logger = logging.getLogger(__name__)


class DigestAgentMVP(Agent):
    """MVP Digest Agent that generates digests from Knowledge Repository summaries."""
    
    def __init__(
        self,
        agent_id: str = "digest_agent_mvp",
        knowledge_repo: Optional[PostgresKnowledgeRepository] = None,
        model_router: Optional[ModelRouter] = None,
        prompt_manager: Optional[MCPManager] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize the DigestAgent.
        
        Args:
            agent_id: Unique identifier for the agent
            knowledge_repo: Knowledge repository instance
            model_router: Model router for LLM access
            prompt_manager: MCP prompt manager
            metadata: Optional metadata
        """
        super().__init__(
            name="Digest Agent MVP",
            description="Generates digests from Knowledge Repository summaries",
            agent_id=agent_id
        )
        self.knowledge_repo = knowledge_repo
        self.model_router = model_router
        self.prompt_manager = prompt_manager
        self._initialized = False
        self.metadata = metadata or {}
    
    def initialize(self) -> None:
        """Initialize the agent and its dependencies."""
        try:
            # Initialize dependencies if needed
            if not self.knowledge_repo:
                self.knowledge_repo = PostgresKnowledgeRepository()
            
            if not self.model_router:
                # Note: In production, this should be injected as a dependency
                logger.warning("No model router provided, using default (may fail without proper config)")
                # self.model_router = ModelRouter()
            
            if not self.prompt_manager:
                # Note: In production, this should be injected as a dependency
                logger.warning("No prompt manager provided, using default (may fail without proper config)")
                # self.prompt_manager = MCPManager()
            
            self._initialized = True
            logger.info(f"DigestAgent {self.agent_id} initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing DigestAgent: {e}")
            raise
    
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process the request to generate a digest.
        
        Args:
            input_data: Agent input containing parameters for digest generation
            
        Returns:
            Agent output with the generated digest
        """
        if not self._initialized:
            self.initialize()
        
        try:
            logger.info(f"Processing digest request for task: {input_data.task_id}")
            
            # Extract parameters from input
            user_id = input_data.metadata.get("user_id")
            limit = input_data.metadata.get("limit", 10)
            
            # Query Knowledge Repository for summaries
            logger.info("Querying Knowledge Repository for summaries")
            summaries = await self._query_summaries(user_id=user_id, limit=limit)
            
            if not summaries:
                logger.warning("No summaries found in Knowledge Repository")
                return AgentOutput(
                    task_id=input_data.task_id,
                    status="success",
                    result={
                        "status": "success",
                        "digest": "No summaries available for digest generation.",
                        "summary_count": 0,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
            
            # Log the data we're processing
            logger.info(f"Found {len(summaries)} summaries to process")
            
            # Render the digest using MCP
            rendered_digest = await self._render_digest(summaries)
            
            # Log the rendered output
            logger.info(f"Generated digest with {len(rendered_digest)} characters")
            
            # Return structured response
            result = {
                "status": "success",
                "digest": rendered_digest,
                "summary_count": len(summaries),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            return AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result=result
            )
            
        except Exception as e:
            logger.error(f"Error generating digest: {e}")
            return AgentOutput(
                task_id=input_data.task_id,
                status="error",
                result={
                    "status": "error",
                    "error": str(e)
                }
            )
    
    async def _query_summaries(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query the Knowledge Repository for summaries.
        
        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of summaries to retrieve
            
        Returns:
            List of summary dictionaries
        """
        # Query for items with content_type = "summary"
        content_items = await self.knowledge_repo.list_content(
            user_id=user_id,
            content_type="summary",
            limit=limit
        )
        
        # Convert to dictionary format for the prompt
        summaries = []
        for item in content_items:
            summaries.append({
                "id": str(item.id),
                "title": item.title,
                "source": item.source,
                "content": item.text_content,
                "summary": item.summary,
                "created_at": item.created_at.isoformat(),
                "tags": [tag.name for tag in getattr(item, 'tags', [])]
            })
        
        return summaries
    
    async def _render_digest(self, summaries: List[Dict[str, Any]]) -> str:
        """Render the digest using MCP with the digest_summary.yaml template.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            The rendered digest text
        """
        # Prepare the context for the prompt
        context = {
            "summaries": summaries,
            "count": len(summaries),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Render the prompt using MCP
        try:
            # Load and render the digest_summary.yaml template
            messages = await self.prompt_manager.render_prompt(
                "digest_summary",
                context
            )
            
            # Call the LLM to generate the digest
            response = await self.model_router.chat(messages)
            return response.text
            
        except Exception as e:
            logger.error(f"Error rendering digest with MCP: {e}")
            # Fallback to simple concatenation
            return self._fallback_digest(summaries)
    
    def _fallback_digest(self, summaries: List[Dict[str, Any]]) -> str:
        """Generate a simple fallback digest if MCP rendering fails.
        
        Args:
            summaries: List of summary dictionaries
            
        Returns:
            A simple formatted digest
        """
        digest_parts = ["# Daily Digest\n"]
        digest_parts.append(f"Generated at: {datetime.utcnow().isoformat()}\n")
        digest_parts.append(f"Total summaries: {len(summaries)}\n\n")
        
        for i, summary in enumerate(summaries, 1):
            digest_parts.append(f"## {i}. {summary['title']}\n")
            digest_parts.append(f"Source: {summary['source']}\n")
            digest_parts.append(f"Date: {summary['created_at']}\n")
            if summary.get('tags'):
                digest_parts.append(f"Tags: {', '.join(summary['tags'])}\n")
            digest_parts.append(f"\n{summary['content']}\n\n")
            digest_parts.append("---\n\n")
        
        return "".join(digest_parts)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "agent_id": self.agent_id,
            "type": "digest_generation",
            "features": [
                "knowledge_repository_query",
                "mcp_prompt_rendering",
                "structured_digest_output"
            ],
            "supported_content_types": ["summary"],
            "max_summaries": 100,
            "output_format": "json"
        }
    
    async def shutdown(self) -> None:
        """Shutdown the agent."""
        self._initialized = False
        logger.info(f"DigestAgent {self.agent_id} shutdown")
"""Test script for DigestAgentMVP."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from agents.base import AgentInput
from agents.digest_agent_mvp import DigestAgentMVP
from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from services.model_router.router import ModelRouter
from services.mcp.prompt_manager import MCPManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_digest_agent():
    """Test the DigestAgent without external dependencies."""
    try:
        # Create mock dependencies
        mock_repo = AsyncMock()
        mock_repo.list_content.return_value = [
            MagicMock(
                id="1",
                title="Test Summary 1",
                source="Source 1",
                text_content="Content of summary 1",
                summary="Summary 1",
                created_at=datetime.now(),
                tags=[MagicMock(name="tag1"), MagicMock(name="tag2")]
            ),
            MagicMock(
                id="2",
                title="Test Summary 2",
                source="Source 2",
                text_content="Content of summary 2",
                summary="Summary 2",
                created_at=datetime.now(),
                tags=[MagicMock(name="tag3")]
            )
        ]
        
        mock_router = AsyncMock()
        mock_router.chat.return_value = MagicMock(text="Generated digest content")
        
        mock_prompt_manager = AsyncMock()
        mock_prompt_manager.render_prompt.return_value = [
            {"role": "system", "content": "You are a digest generator"},
            {"role": "user", "content": "Generate a digest"}
        ]
        
        # Create agent with mock dependencies
        agent = DigestAgentMVP(
            knowledge_repo=mock_repo,
            model_router=mock_router,
            prompt_manager=mock_prompt_manager
        )
        
        # Initialize agent
        logging.info("Initializing DigestAgent...")
        agent.initialize()  # Removed await since initialize() is not async
        
        # Create input
        input_data = AgentInput(
            task_id="test_digest_001",
            source="test_script",
            content={},
            metadata={
                "user_id": "test_user",
                "limit": 10
            }
        )
        
        # Process the request
        logging.info("Processing digest request...")
        result = await agent.process(input_data)
        
        # Display results
        logging.info(f"Result status: {result.status}")
        logging.info(f"Result data: {result.result}")
        
        if result.status == "success":
            print("\n=== GENERATED DIGEST ===")
            print(result.result["digest"])
            print(f"\nSummary count: {result.result['summary_count']}")
            print(f"Timestamp: {result.result['timestamp']}")
        else:
            print(f"\nError: {result.result.get('error')}")
        
        # Test capabilities
        capabilities = agent.get_capabilities()
        print("\n=== AGENT CAPABILITIES ===")
        for key, value in capabilities.items():
            print(f"{key}: {value}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test_digest_agent: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_digest_agent())
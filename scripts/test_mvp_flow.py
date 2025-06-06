#!/usr/bin/env python3
"""Test harness for MVP flow validation

This script simulates the complete MVP pipeline:
1. ContentMind Agent saves summaries to Knowledge Repository
2. Digest Agent retrieves summaries and generates a digest

Usage:
    PYTHONPATH=. python3 scripts/test_mvp_flow.py [--mock] [--live] [--count N]

Options:
    --mock    Run with mocked dependencies (default)
    --live    Run with real dependencies
    --count N Number of test items to process (default: 1)
"""

import asyncio
import argparse
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from agents.content_mind import ContentMind
from agents.digest_agent_mvp import DigestAgentMVP
from services.model_router.factory import create_default_router
from services.model_router.base import LLMMessage
from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from agents.base import AgentInput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample content for testing
SAMPLE_CONTENT = [
    {
        "title": "AI in Healthcare",
        "content": "Artificial Intelligence is revolutionizing healthcare through improved diagnosis, treatment planning, and patient care. Machine learning algorithms can analyze medical images, predict patient outcomes, and assist in drug discovery.",
        "type": "text",
        "source": "test"
    },
    {
        "title": "Climate Change Report",
        "content": "Global temperatures continue to rise, with 2023 being the hottest year on record. Scientists warn of increasing extreme weather events and rising sea levels. Urgent action is needed to reduce greenhouse gas emissions.",
        "type": "report",
        "source": "test"
    }
]

class MockModelRouter:
    """Mock LLM router for testing"""
    
    async def chat(self, messages: List[LLMMessage], **kwargs) -> Dict[str, Any]:
        """Return mock response"""
        return {
            "content": "This is a mock summary of the content.",
            "model": "mock-model",
            "usage": {"total_tokens": 100}
        }

class MockKnowledgeRepository:
    """Mock knowledge repository for testing"""
    
    def __init__(self):
        self.stored_content = []
    
    async def store_content(self, content: Dict[str, Any]) -> bool:
        """Store content and return success"""
        self.stored_content.append(content)
        return True
    
    async def get_summaries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return stored summaries"""
        return self.stored_content[:limit]

async def process_content(
    content: Dict[str, Any],
    content_mind: ContentMind,
    knowledge_repo: Any
) -> bool:
    """Process content through ContentMind and store in Knowledge Repository"""
    try:
        # Wrap content in AgentInput
        agent_input = AgentInput(
            task_id=f"test_{content['title'].replace(' ', '_')}",
            source="test_mvp_flow",
            content={"text": content["content"]},
            context={"content_type": content["type"]},
            metadata={
                "title": content["title"],
                "source": content["source"],
                "user_id": content.get("user_id", "test_user")
            }
        )
        # Process with ContentMind
        result = await content_mind.process(agent_input)
        logger.info(f"Raw AgentOutput.result: {getattr(result, 'result', result)}")
        
        # Defensive: try to extract summary
        summary = None
        if hasattr(result, "result") and isinstance(result.result, dict):
            summary = result.result.get("summary")
        if not summary:
            logger.error(f"No summary found. Full result: {getattr(result, 'result', result)}")
            return False
        
        # Store in Knowledge Repository
        stored = await knowledge_repo.store_content({
            "title": content["title"],
            "content": summary,
            "type": "summary",
            "source": content["source"],
            "metadata": {
                "original_type": content["type"],
                "processed_at": datetime.utcnow().isoformat(),
                "user_id": content.get("user_id", "test_user")
            }
        })
        
        return stored
        
    except Exception as e:
        logger.error(f"Error processing content: {e}")
        return False

async def generate_digest(
    knowledge_repo: Any,
    digest_agent: DigestAgentMVP
) -> Optional[Dict[str, Any]]:
    """Generate digest from stored content"""
    try:
        # Get summaries from Knowledge Repository
        summaries = await knowledge_repo.get_summaries()
        
        if not summaries:
            logger.error("No summaries found in Knowledge Repository")
            return None
        
        # Generate digest
        digest = await digest_agent.generate_digest(summaries)
        
        return {
            "status": "success",
            "digest": digest,
            "summary_count": len(summaries),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        return None

async def run_test_flow(is_mock: bool = True, count: int = 1) -> None:
    """Run the complete MVP test flow"""
    logger.info(f"Starting MVP test flow (mode: {'mock' if is_mock else 'live'})")
    
    # Initialize components
    if is_mock:
        model_router = MockModelRouter()
        knowledge_repo = MockKnowledgeRepository()
    else:
        model_router = await create_default_router()
        knowledge_repo = PostgresKnowledgeRepository()
    
    content_mind = ContentMind(llm_router=model_router)
    digest_agent = DigestAgentMVP(model_router=model_router)
    
    # Initialize agents
    if not is_mock:
        logger.info("Initializing ContentMind agent...")
        init_success = await content_mind.initialize()
        if not init_success:
            logger.error("Failed to initialize ContentMind agent")
            return
            
        logger.info("Initializing DigestAgent...")
        try:
            digest_agent.initialize()
            logger.info("DigestAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DigestAgent: {e}")
            return
    
    # Process test content
    success_count = 0
    for i, content in enumerate(SAMPLE_CONTENT[:count], 1):
        logger.info(f"Processing content {i}/{count}: {content['title']}")
        
        if await process_content(content, content_mind, knowledge_repo):
            success_count += 1
            logger.info(f"✓ Content {i} processed successfully")
        else:
            logger.error(f"✗ Failed to process content {i}")
    
    # Generate digest
    if success_count > 0:
        logger.info("Generating digest from processed content...")
        digest_result = await generate_digest(knowledge_repo, digest_agent)
        
        if digest_result:
            logger.info("✓ Digest generated successfully")
            print("\nDigest Result:")
            print(json.dumps(digest_result, indent=2))
        else:
            logger.error("✗ Failed to generate digest")
    else:
        logger.error("No content was processed successfully, skipping digest generation")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MVP Flow Test Harness")
    parser.add_argument("--mock", action="store_true", help="Run with mocked dependencies")
    parser.add_argument("--live", action="store_true", help="Run with real dependencies")
    parser.add_argument("--count", type=int, default=1, help="Number of test items to process")
    
    args = parser.parse_args()
    
    # Default to mock mode if neither specified
    is_mock = not args.live if args.live else True
    
    asyncio.run(run_test_flow(is_mock, args.count))

if __name__ == "__main__":
    main() 
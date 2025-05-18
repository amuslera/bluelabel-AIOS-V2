#!/usr/bin/env python3
"""Simplified test harness for MVP flow validation

This script simulates the complete MVP pipeline:
1. ContentMind Agent saves summaries to Knowledge Repository
2. Digest Agent retrieves summaries and generates a digest
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from agents.content_mind import ContentMind
from agents.digest_agent_mvp import DigestAgentMVP
from services.model_router.factory import create_default_router
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
    }
]

class SimpleKnowledgeRepository:
    """Simplified repository that works with the existing schema"""
    
    def __init__(self):
        self.stored_content = []
    
    async def store_content(self, content: Dict[str, Any]) -> bool:
        """Store content in simplified format"""
        try:
            # Extract the actual summary from the ContentMind output
            summary = content.get("content", "")
            if isinstance(summary, dict):
                summary = summary.get("summary", str(summary))
            
            # Map to the old schema
            simplified_content = {
                "title": content.get("title", "Untitled"),
                "content": summary,
                "summary": summary,  # Store in both fields
                "metadata": {
                    "original_type": content.get("metadata", {}).get("original_type", "text"),
                    "processed_at": datetime.utcnow().isoformat(),
                    "source": content.get("source", "test"),
                    "user_id": content.get("metadata", {}).get("user_id", "test_user")
                }
            }
            self.stored_content.append(simplified_content)
            logger.info(f"Stored content: {content.get('title', 'Untitled')}")
            return True
        except Exception as e:
            logger.error(f"Error storing content: {e}")
            return False
    
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
        logger.info(f"ContentMind processing complete for: {content['title']}")
        
        # Extract summary from result
        summary = None
        if hasattr(result, "result") and isinstance(result.result, dict):
            summary = result.result.get("summary", {}).get("summary", "")
        
        if not summary:
            logger.error(f"No summary found for: {content['title']}")
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
        import traceback
        traceback.print_exc()
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
        
        logger.info(f"Found {len(summaries)} summaries for digest generation")
        
        # Generate digest using the agent directly
        input_data = {
            "summaries": summaries,
            "user_id": "test_user"
        }
        
        agent_input = AgentInput(
            task_id="test_digest_generation",
            source="test_mvp_flow",
            content=input_data,
            context={"request_type": "digest"},
            metadata={"user_id": "test_user"}
        )
        
        result = await digest_agent.process(agent_input)
        
        # Extract the digest from the result
        if hasattr(result, "result") and isinstance(result.result, dict):
            digest = result.result
        else:
            digest = str(result)
        
        return {
            "status": "success",
            "digest": digest,
            "summary_count": len(summaries),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_test_flow() -> None:
    """Run the complete MVP test flow"""
    logger.info(f"Starting MVP test flow (simplified)")
    
    # Initialize components
    model_router = await create_default_router()
    knowledge_repo = SimpleKnowledgeRepository()  # Use simplified repository
    
    content_mind = ContentMind(llm_router=model_router)
    digest_agent = DigestAgentMVP(model_router=model_router)
    
    # Initialize agents
    logger.info("Initializing ContentMind agent...")
    init_success = await content_mind.initialize()
    if not init_success:
        logger.error("Failed to initialize ContentMind agent")
        return
    
    logger.info("Initializing DigestAgent...")
    digest_agent.initialize()
    logger.info("DigestAgent initialized successfully")
    
    # Process test content
    success_count = 0
    for i, content in enumerate(SAMPLE_CONTENT, 1):
        logger.info(f"Processing content {i}/{len(SAMPLE_CONTENT)}: {content['title']}")
        
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
    asyncio.run(run_test_flow())


if __name__ == "__main__":
    main()
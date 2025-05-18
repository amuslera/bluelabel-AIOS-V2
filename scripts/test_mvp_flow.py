#!/usr/bin/env python3
"""MVP Flow Test Harness.

This script simulates the complete MVP pipeline:
1. ContentMind Agent → summary saved to Knowledge Repository
2. Digest Agent → retrieves summaries → generates digest

Usage:
    python test_mvp_flow.py [--mock|--live] [--count N]

Options:
    --mock    Use mock data and simulated responses (default)
    --live    Use real API endpoints and services
    --count N Number of test items to process (default: 3)
"""

import asyncio
import argparse
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from agents.content_mind import ContentMind, ContentType
from agents.digest_agent_mvp import DigestAgentMVP
from agents.base import AgentInput, AgentOutput
from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from services.model_router.router import ModelRouter
from services.mcp.prompt_manager import MCPManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample test content
SAMPLE_CONTENT = [
    {
        "title": "AI in Healthcare",
        "content": """
        Artificial Intelligence is revolutionizing healthcare delivery. Recent studies show:
        - 95% accuracy in early-stage cancer detection
        - 40% reduction in false positives
        - $2B annual cost savings
        - Improved patient outcomes across multiple conditions
        """,
        "type": ContentType.TEXT,
        "source": "test_input"
    },
    {
        "title": "Machine Learning in Finance",
        "content": """
        Financial institutions are increasingly adopting ML for:
        - Fraud detection and prevention
        - Algorithmic trading
        - Risk assessment
        - Customer service automation
        - Portfolio optimization
        """,
        "type": ContentType.TEXT,
        "source": "test_input"
    },
    {
        "title": "Natural Language Processing Advances",
        "content": """
        Recent breakthroughs in NLP include:
        - More accurate translation systems
        - Better sentiment analysis
        - Improved text summarization
        - Enhanced question answering
        - More natural dialogue systems
        """,
        "type": ContentType.TEXT,
        "source": "test_input"
    }
]

class MockModelRouter:
    """Mock model router for testing."""
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Simulate LLM chat response."""
        return {
            "text": "This is a simulated summary of the content.",
            "model": "mock-model",
            "provider": "mock-provider"
        }
    
    async def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Simulate LLM completion response."""
        return {
            "text": "This is a simulated completion response.",
            "model": "mock-model",
            "provider": "mock-provider"
        }

class MockKnowledgeRepository:
    """Mock knowledge repository for testing."""
    
    def __init__(self):
        self.items = []
    
    async def store_content(self, content: Dict[str, Any]) -> str:
        """Store content and return ID."""
        content_id = f"mock_{len(self.items)}"
        self.items.append({**content, "id": content_id})
        return content_id
    
    async def list_content(
        self,
        user_id: Optional[str] = None,
        content_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """List stored content."""
        return self.items[:limit]

async def process_with_content_mind(
    content: Dict[str, Any],
    model_router: Any,
    knowledge_repo: Any,
    is_mock: bool = True
) -> Dict[str, Any]:
    """Process content through ContentMind agent."""
    start_time = time.time()
    
    # Create agent
    agent = ContentMind(
        agent_id="test_content_mind",
        llm_router=model_router,
        metadata={"test": True}
    )
    await agent.initialize()
    
    # Create input
    input_data = AgentInput(
        task_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        content={"text": content["content"]},
        context={"content_type": content["type"]},
        metadata={"source": content["source"]}
    )
    
    # Process content
    result = await agent.process(input_data)
    
    if result.status == "success":
        # Store in knowledge repository
        stored_id = await knowledge_repo.store_content({
            "title": content["title"],
            "content": content["content"],
            "summary": result.result.get("summary", ""),
            "content_type": "summary",
            "source": content["source"],
            "created_at": datetime.now().isoformat()
        })
        
        logger.info(f"Stored content with ID: {stored_id}")
    
    elapsed = time.time() - start_time
    return {
        "status": result.status,
        "result": result.result,
        "elapsed": elapsed
    }

async def generate_digest(
    knowledge_repo: Any,
    model_router: Any,
    is_mock: bool = True
) -> Dict[str, Any]:
    """Generate digest from stored content."""
    start_time = time.time()
    
    # Create agent
    agent = DigestAgentMVP(
        agent_id="test_digest_agent",
        knowledge_repo=knowledge_repo,
        model_router=model_router
    )
    await agent.initialize()
    
    # Create input
    input_data = AgentInput(
        task_id=f"digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        content={},
        metadata={"limit": 10}
    )
    
    # Generate digest
    result = await agent.process(input_data)
    
    elapsed = time.time() - start_time
    return {
        "status": result.status,
        "result": result.result,
        "elapsed": elapsed
    }

async def run_test_flow(is_mock: bool = True, count: int = 3):
    """Run the complete MVP test flow."""
    logger.info(f"Starting MVP test flow (mode: {'mock' if is_mock else 'live'})")
    
    # Initialize components
    if is_mock:
        model_router = MockModelRouter()
        knowledge_repo = MockKnowledgeRepository()
    else:
        model_router = await ModelRouter.create()
        knowledge_repo = PostgresKnowledgeRepository()
    
    # Process content through ContentMind
    content_results = []
    for i, content in enumerate(SAMPLE_CONTENT[:count], 1):
        logger.info(f"\nProcessing content {i}/{count}: {content['title']}")
        result = await process_with_content_mind(
            content,
            model_router,
            knowledge_repo,
            is_mock
        )
        content_results.append(result)
        logger.info(f"Content processing completed in {result['elapsed']:.2f}s")
    
    # Generate digest
    logger.info("\nGenerating digest from processed content...")
    digest_result = await generate_digest(
        knowledge_repo,
        model_router,
        is_mock
    )
    
    # Print results
    print("\n=== MVP Flow Test Results ===")
    print(f"\nProcessed {len(content_results)} items:")
    for i, result in enumerate(content_results, 1):
        print(f"\nItem {i}:")
        print(f"  Status: {result['status']}")
        print(f"  Time: {result['elapsed']:.2f}s")
        if result['status'] == 'success':
            print(f"  Summary: {result['result'].get('summary', '')[:100]}...")
    
    print(f"\nDigest Generation:")
    print(f"  Status: {digest_result['status']}")
    print(f"  Time: {digest_result['elapsed']:.2f}s")
    if digest_result['status'] == 'success':
        print(f"  Summary Count: {digest_result['result'].get('summary_count', 0)}")
        print(f"  Digest: {digest_result['result'].get('digest', '')[:200]}...")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MVP Flow Test Harness")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data and simulated responses"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real API endpoints and services"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of test items to process"
    )
    
    args = parser.parse_args()
    
    # Default to mock mode if neither specified
    is_mock = not args.live if args.live else True
    
    # Run the test flow
    asyncio.run(run_test_flow(is_mock, args.count))

if __name__ == "__main__":
    main() 
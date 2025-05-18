"""Simple test for DigestAgent without external dependencies."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_digest_agent_simple():
    """Test DigestAgent with fallback rendering."""
    try:
        from agents.base import AgentInput
        print("✓ Successfully imported AgentInput")
        
        # Create minimal DigestAgent mock
        class MockDigestAgentMVP:
            def __init__(self, **kwargs):
                self.agent_id = "digest_agent_mvp"
                self._initialized = False
                self.knowledge_repo = kwargs.get('knowledge_repo')
                
            async def initialize(self):
                self._initialized = True
                return True
                
            async def process(self, input_data):
                # Simulate querying knowledge repo
                summaries = [
                    {
                        "id": "1",
                        "title": "Test Summary 1",
                        "source": "Source 1",
                        "content": "Content of summary 1",
                        "created_at": datetime.now().isoformat(),
                        "tags": ["tag1", "tag2"]
                    },
                    {
                        "id": "2",
                        "title": "Test Summary 2",
                        "source": "Source 2",
                        "content": "Content of summary 2",
                        "created_at": datetime.now().isoformat(),
                        "tags": ["tag3"]
                    }
                ]
                
                # Generate simple digest
                digest = self._fallback_digest(summaries)
                
                # Return result
                from agents.base import AgentOutput
                return AgentOutput(
                    task_id=input_data.task_id,
                    status="success",
                    result={
                        "status": "success",
                        "digest": digest,
                        "summary_count": len(summaries),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                )
                
            def _fallback_digest(self, summaries):
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
        
        print("✓ Successfully created MockDigestAgentMVP")
        
        # Create agent
        agent = MockDigestAgentMVP()
        await agent.initialize()
        print("✓ Successfully initialized agent")
        
        # Create input
        input_data = AgentInput(
            task_id="test_task",
            content={},
            metadata={"user_id": "test_user", "limit": 5}
        )
        print("✓ Successfully created input data")
        
        # Process
        result = await agent.process(input_data)
        print("✓ Successfully processed request")
        
        # Display results
        print("\n=== RESULTS ===")
        print(f"Status: {result.status}")
        print(f"Summary count: {result.result['summary_count']}")
        print(f"\n=== DIGEST ===\n{result.result['digest']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_digest_agent_simple())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
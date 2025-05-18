"""Test script for DigestAgent MVP implementation."""

import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_digest_agent():
    """Test the DigestAgent without external dependencies."""
    
    # Import after setting up logging
    from agents.digest_agent_mvp import DigestAgentMVP
    from agents.base import AgentInput
    
    # Create mock dependencies
    mock_repo = AsyncMock()
    mock_items = [
        MagicMock(
            id="1",
            title="AI Breakthrough in Medical Diagnostics",
            source="TechNews Daily",
            text_content="Revolutionary AI system achieves 98% accuracy in early cancer detection...",
            summary="New AI model outperforms human doctors in cancer diagnosis",
            created_at=datetime(2025, 5, 17, 10, 0, 0),
            tags=[]
        ),
        MagicMock(
            id="2",
            title="Climate Summit Reaches Historic Agreement",
            source="Environmental Weekly",
            text_content="Global leaders commit to net-zero emissions by 2050...",
            summary="195 countries pledge unprecedented climate action",
            created_at=datetime(2025, 5, 17, 14, 0, 0),
            tags=[]
        ),
        MagicMock(
            id="3",
            title="Tech Stocks Rally on AI Optimism",
            source="Financial Times",
            text_content="NASDAQ reaches new highs as AI companies report record earnings...",
            summary="Technology sector leads market gains",
            created_at=datetime(2025, 5, 17, 16, 0, 0),
            tags=[]
        )
    ]
    mock_repo.list_content.return_value = mock_items
    
    # Create mock model router and prompt manager
    mock_router = AsyncMock()
    mock_response = MagicMock()
    mock_response.text = """# Daily Digest Summary

**Executive Summary**: Today's digest highlights significant advances in AI technology for healthcare, historic climate commitments from global leaders, and strong performance in technology stocks driven by AI optimism.

## Technology & Innovation

### AI Breakthrough in Medical Diagnostics
*Source: TechNews Daily (2025-05-17)*

A revolutionary AI system has achieved 98% accuracy in early cancer detection, outperforming human specialists in clinical trials. This breakthrough could transform preventive healthcare and save millions of lives through earlier intervention.

## Climate & Environment

### Historic Climate Agreement Reached
*Source: Environmental Weekly (2025-05-17)*

At the latest climate summit, 195 countries have pledged unprecedented climate action, committing to net-zero emissions by 2050. This marks the most comprehensive global climate agreement to date.

## Markets & Finance

### Tech Sector Leads Market Rally
*Source: Financial Times (2025-05-17)*

Technology stocks surged today as AI companies reported record earnings. The NASDAQ reached new highs, reflecting investor confidence in the AI revolution's economic impact.

## Looking Ahead

The convergence of AI advancement, climate action, and market optimism suggests a transformative period ahead. Watch for further developments in AI healthcare applications and the implementation of climate commitments."""
    
    mock_router.chat.return_value = mock_response
    
    mock_prompt_manager = AsyncMock()
    mock_prompt_manager.render_prompt.return_value = [
        {"role": "system", "content": "You are an expert digest creator."},
        {"role": "user", "content": "Create a digest from these summaries..."}
    ]
    
    # Create DigestAgent with mocked dependencies
    agent = DigestAgentMVP(
        knowledge_repo=mock_repo,
        model_router=mock_router,
        prompt_manager=mock_prompt_manager
    )
    
    # Initialize agent
    logging.info("Initializing DigestAgent...")
    await agent.initialize()
    
    # Create input
    input_data = AgentInput(
        task_id="test_digest_001",
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


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_digest_agent())
#!/usr/bin/env python3
"""Test script for ContentMindLLM agent"""

import asyncio
import logging
from datetime import datetime

from agents.content_mind_llm import ContentMindLLM
from agents.base import AgentInput
from services.model_router.router import ModelRouter
from services.model_router.config import get_openai_config
from services.mcp.factory import create_prompt_manager, initialize_default_components

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Create model router with OpenAI config
    logger.info("Setting up model router...")
    router = ModelRouter()
    openai_config = get_openai_config()
    
    if openai_config:
        try:
            await router.add_provider("openai", openai_config)
            logger.info("Added OpenAI provider")
        except Exception as e:
            logger.warning(f"Failed to add OpenAI provider: {e}")
    else:
        logger.warning("No OpenAI configuration found")
    
    # Create prompt manager
    logger.info("Setting up prompt manager...")
    prompt_manager = create_prompt_manager()
    await initialize_default_components(prompt_manager)
    
    # Create ContentMindLLM agent
    logger.info("Creating ContentMindLLM agent...")
    agent = ContentMindLLM(
        model_router=router,
        prompt_manager=prompt_manager
    )
    
    # Initialize the agent
    if await agent.initialize():
        logger.info("Agent initialized successfully")
    else:
        logger.error("Failed to initialize agent")
        return
    
    # Test content
    test_content = """
    Artificial Intelligence (AI) is rapidly transforming healthcare by improving diagnostic accuracy,
    personalizing treatment plans, and accelerating drug discovery. Machine learning algorithms can now
    detect diseases like cancer earlier than traditional methods, with some systems achieving 95% accuracy
    in identifying certain types of tumors. AI-powered tools are also helping doctors make better decisions
    by analyzing vast amounts of patient data and medical literature in seconds.
    
    The key applications include:
    - Medical imaging analysis for early disease detection
    - Predictive analytics for patient outcomes
    - Virtual health assistants for patient care
    - Drug discovery and development acceleration
    - Personalized medicine based on genetic data
    
    However, challenges remain including data privacy concerns, regulatory approval processes,
    and the need for physician training on AI systems.
    """
    
    # Create test input
    test_input = AgentInput(
        source="test_script",
        metadata={
            "content_type": "text",
            "timestamp": datetime.now()
        },
        content={
            "content": test_content,
            "title": "AI in Healthcare"
        }
    )
    
    # Process the content
    logger.info("Processing test content...")
    result = await agent.process(test_input)
    
    # Display results
    print("\n=== ContentMindLLM Test Results ===")
    print(f"Status: {result.status}")
    
    if result.status == "success":
        print(f"\nSummary:\n{result.result.get('summary', 'N/A')}")
        print(f"\nKey Concepts: {', '.join(result.result.get('concepts', []))}")
        print(f"\nMetadata:")
        metadata = result.result.get('metadata', {})
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    else:
        print(f"Error: {result.error}")
    
    # Show agent capabilities
    capabilities = agent.get_capabilities()
    print(f"\n=== Agent Capabilities ===")
    print(f"Content Types: {capabilities['content_types']}")
    print(f"Analysis Types: {capabilities['analysis_types']}")
    print(f"Max Content Length: {capabilities['max_content_length']}")
    
    # Shutdown
    await agent.shutdown()
    logger.info("Test completed")


if __name__ == "__main__":
    asyncio.run(main())
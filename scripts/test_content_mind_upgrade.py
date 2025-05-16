#!/usr/bin/env python3
"""Test upgraded ContentMind agent with LLM services"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.content_mind import ContentMind
from agents.base import AgentInput
from services.model_router.router import ModelRouter, ProviderType
from services.model_router.base import LLMProviderConfig
from core.config import settings


async def test_content_mind_with_llm():
    """Test ContentMind agent with real LLM integration"""
    
    # Create model router
    router = ModelRouter()
    
    # Set up providers (using environment variables for API keys)
    if os.getenv("ANTHROPIC_API_KEY"):
        anthropic_config = LLMProviderConfig(
            provider_name="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model_name="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.7
        )
        success = await router.add_provider(ProviderType.ANTHROPIC, anthropic_config)
        print(f"Added Anthropic provider: {success}")
    
    if os.getenv("OPENAI_API_KEY"):
        openai_config = LLMProviderConfig(
            provider_name="openai", 
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7
        )
        success = await router.add_provider(ProviderType.OPENAI, openai_config)
        print(f"Added OpenAI provider: {success}")
    
    # Create ContentMind agent with router
    agent = ContentMind(model_router=router)
    await agent.initialize()
    
    # Test content
    test_content = """
    Artificial Intelligence is transforming the technology landscape. Machine learning algorithms
    are becoming more sophisticated, enabling applications in healthcare, finance, and autonomous vehicles.
    Recent breakthroughs in natural language processing have led to more human-like conversations
    with AI systems. Companies like OpenAI, Anthropic, and Google are leading the charge in
    developing advanced AI models. However, concerns about AI safety and ethics continue to grow
    as these systems become more powerful.
    """
    
    # Create input
    input_data = AgentInput(
        task_id="test-1",
        source="test",
        content={"text": test_content, "type": "text"},
        metadata={"timestamp": "2024-01-01"}
    )
    
    # Process content
    print("\nProcessing content with LLM-powered ContentMind...")
    result = await agent.process(input_data)
    
    # Display results
    print(f"\nStatus: {result.status}")
    if result.status == "success":
        print("\nSummary:")
        print(result.result["summary"])
        
        print("\nEntities:")
        for entity in result.result["entities"]:
            print(f"  - {entity['text']} ({entity['type']}) - Confidence: {entity.get('confidence', 'N/A')}")
        
        print("\nTopics:")
        for topic in result.result["topics"]:
            print(f"  - {topic}")
        
        print("\nSentiment:")
        sentiment = result.result["sentiment"]
        print(f"  - Type: {sentiment['sentiment']}")
        print(f"  - Score: {sentiment['score']}")
        print(f"  - Confidence: {sentiment['confidence']}")
    else:
        print(f"Error: {result.error}")
    
    # Shutdown
    await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(test_content_mind_with_llm())
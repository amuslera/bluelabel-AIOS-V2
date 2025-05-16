#!/usr/bin/env python3
"""Test LLM connections to verify API keys and configuration."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from services.model_router.factory import create_default_router
from services.model_router.router import RouterStrategy
from services.model_router.base import LLMMessage

load_dotenv()


async def test_llm_connection():
    """Test each configured LLM provider."""
    print("🔍 Testing LLM Connections...")
    print("=" * 50)
    
    # Check for API keys
    providers = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "Google Gemini": os.getenv("GOOGLE_GENERATIVEAI_API_KEY")
    }
    
    configured_providers = []
    for name, key in providers.items():
        if key and key != "your_openai_key_here" and key != "your_anthropic_key_here":
            print(f"✅ {name}: API key configured")
            configured_providers.append(name)
        else:
            print(f"❌ {name}: API key not configured")
    
    if not configured_providers:
        print("\n❌ No LLM providers configured! Please set API keys in .env file")
        return
    
    print(f"\n📋 Testing {len(configured_providers)} configured providers...")
    
    # Test each provider
    for strategy in [RouterStrategy.CHEAPEST, RouterStrategy.FASTEST, RouterStrategy.BEST_QUALITY]:
        print(f"\n🔄 Testing with {strategy.value} strategy...")
        
        try:
            router = await create_default_router(strategy=strategy)
            
            # Simple test message
            response = await router.chat([
                LLMMessage(role="user", content="Hello! Please respond with just 'Hello' back.")
            ])
            
            print(f"✅ {strategy.value}: {response.text}")
            print(f"   Provider: {response.provider}")
            print(f"   Model: {response.model}")
            print(f"   Tokens: {response.usage.get('total_tokens', 'N/A') if response.usage else 'N/A'}")
            
        except Exception as e:
            print(f"❌ {strategy.value}: Failed - {str(e)}")
    
    # Test direct provider access
    print("\n🔄 Testing direct provider access...")
    
    try:
        router = await create_default_router()
        
        # Test specific providers if available
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_key_here":
            response = await router.chat([
                LLMMessage(role="user", content="Say 'OpenAI works!'")
            ])
            print(f"✅ OpenAI direct: {response.text}")
        
        if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "your_anthropic_key_here":
            response = await router.chat([
                LLMMessage(role="user", content="Say 'Anthropic works!'")
            ])
            print(f"✅ Anthropic direct: {response.text}")
        
        if os.getenv("GOOGLE_GENERATIVEAI_API_KEY"):
            response = await router.chat([
                LLMMessage(role="user", content="Say 'Gemini works!'")
            ])
            print(f"✅ Gemini direct: {response.text}")
            
    except Exception as e:
        print(f"❌ Direct access failed: {str(e)}")
    
    print("\n✅ LLM connection test complete!")


if __name__ == "__main__":
    print("🚀 LLM Connection Test")
    print("=====================")
    asyncio.run(test_llm_connection())
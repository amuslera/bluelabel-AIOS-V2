#!/usr/bin/env python3
"""Demo script for Model Router with multiple LLM providers"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.model_router.router import ModelRouter, ProviderType, RouterStrategy
from services.model_router.base import LLMProviderConfig, LLMMessage
from services.model_router.factory import (
    create_default_router,
    create_cheapest_router,
    create_fastest_router,
    create_quality_router
)


async def demo_basic_routing():
    """Demonstrate basic model routing functionality"""
    
    print("🤖 Model Router Demo - Basic Routing")
    print("=" * 40)
    
    # Create router
    router = ModelRouter()
    
    # Add OpenAI if available
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        config = LLMProviderConfig(
            provider_name="openai",
            api_key=openai_key,
            model_name="gpt-4",
            max_tokens=500
        )
        success = await router.add_provider(ProviderType.OPENAI, config)
        print(f"✓ Added OpenAI: {success}")
    else:
        print("⚠️  OpenAI API key not found")
    
    # Add Anthropic if available
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        config = LLMProviderConfig(
            provider_name="anthropic",
            api_key=anthropic_key,
            model_name="claude-3-sonnet",
            max_tokens=500
        )
        success = await router.add_provider(ProviderType.ANTHROPIC, config)
        print(f"✓ Added Anthropic: {success}")
    else:
        print("⚠️  Anthropic API key not found")
    
    # Add Gemini if available
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini_key:
        config = LLMProviderConfig(
            provider_name="gemini",
            api_key=gemini_key,
            model_name="gemini-pro",
            max_tokens=500
        )
        success = await router.add_provider(ProviderType.GEMINI, config)
        print(f"✓ Added Gemini: {success}")
    else:
        print("⚠️  Gemini API key not found")
    
    # Show available providers
    providers = router.get_available_providers()
    print(f"\nAvailable providers: {len(providers)}")
    for provider in providers:
        print(f"  - {provider['name']}: {'✓' if provider['available'] else '✗'}")
    
    if not providers:
        print("\n❌ No providers available. Please set API keys.")
        return
    
    # Test different strategies
    strategies = [
        RouterStrategy.FALLBACK,
        RouterStrategy.CHEAPEST,
        RouterStrategy.FASTEST,
        RouterStrategy.BEST_QUALITY
    ]
    
    test_message = "Write a haiku about artificial intelligence."
    
    for strategy in strategies:
        router.set_default_strategy(strategy)
        print(f"\n📍 Testing {strategy.value} strategy")
        
        messages = [LLMMessage(role="user", content=test_message)]
        
        try:
            response = await router.chat(messages, strategy=strategy)
            print(f"  Provider: {response.provider}")
            print(f"  Model: {response.model}")
            print(f"  Response: {response.text[:100]}...")
            print(f"  Tokens: {response.usage.get('total_tokens', 'N/A')}")
        except Exception as e:
            print(f"  Error: {str(e)}")


async def demo_preferred_provider():
    """Demonstrate using preferred providers"""
    
    print("\n\n🎯 Model Router Demo - Preferred Provider")
    print("=" * 40)
    
    router = await create_default_router()
    
    providers = router.get_available_providers()
    if len(providers) < 2:
        print("Need at least 2 providers for this demo")
        return
    
    # Try each available provider
    messages = [LLMMessage(role="user", content="What is 2+2?")]
    
    for provider in providers:
        if provider['available']:
            print(f"\n📍 Using preferred provider: {provider['name']}")
            
            try:
                response = await router.chat(messages, preferred_provider=provider['name'])
                print(f"  Response: {response.text}")
                print(f"  Provider used: {response.provider}")
            except Exception as e:
                print(f"  Error: {str(e)}")


async def demo_fallback():
    """Demonstrate fallback behavior"""
    
    print("\n\n🔄 Model Router Demo - Fallback")
    print("=" * 40)
    
    router = await create_default_router()
    
    # Test with a message that might fail on some providers
    messages = [
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="Generate a very long response about the history of computing.")
    ]
    
    print("Testing fallback with potentially failing request...")
    
    try:
        response = await router.chat(messages)
        print(f"✓ Success with provider: {response.provider}")
        print(f"  Model: {response.model}")
        print(f"  Response length: {len(response.text)} characters")
    except Exception as e:
        print(f"❌ All providers failed: {str(e)}")


async def demo_strategy_comparison():
    """Compare different routing strategies"""
    
    print("\n\n📊 Model Router Demo - Strategy Comparison")
    print("=" * 40)
    
    # Create routers with different strategies
    routers = {
        "Cheapest": await create_cheapest_router(),
        "Fastest": await create_fastest_router(),
        "Quality": await create_quality_router(),
        "Balanced": await create_default_router()
    }
    
    test_messages = [
        LLMMessage(role="user", content="Explain quantum computing in one sentence.")
    ]
    
    results = {}
    
    for name, router in routers.items():
        print(f"\n🔧 Testing {name} strategy")
        
        try:
            response = await router.chat(test_messages)
            results[name] = {
                "provider": response.provider,
                "model": response.model,
                "tokens": response.usage.get("total_tokens", "N/A"),
                "response": response.text[:50] + "..."
            }
            
            print(f"  Provider: {response.provider}")
            print(f"  Tokens: {response.usage.get('total_tokens', 'N/A')}")
            
        except Exception as e:
            results[name] = {"error": str(e)}
            print(f"  Error: {str(e)}")
    
    # Summary
    print("\n📋 Summary:")
    for name, result in results.items():
        if "error" in result:
            print(f"  {name}: Failed - {result['error']}")
        else:
            print(f"  {name}: {result['provider']} ({result['tokens']} tokens)")


async def main():
    """Run all demos"""
    
    print("🚀 Model Router Demo Suite")
    print("=" * 50)
    print("Make sure you have set the following environment variables:")
    print("  - OPENAI_API_KEY")
    print("  - ANTHROPIC_API_KEY")
    print("  - GOOGLE_API_KEY or GEMINI_API_KEY")
    print()
    
    # Run demos
    await demo_basic_routing()
    await demo_preferred_provider()
    await demo_fallback()
    await demo_strategy_comparison()
    
    print("\n\n✅ Demo completed!")


if __name__ == "__main__":
    asyncio.run(main())
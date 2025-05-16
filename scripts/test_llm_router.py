#!/usr/bin/env python3
"""Test the LLM Router implementation"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.model_router import ModelRouter, OpenAIProvider, LLMProviderConfig
from services.model_router.factory import create_default_router
from services.model_router.base import LLMMessage

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_openai_provider():
    """Test OpenAI provider directly"""
    print("\n=== Testing OpenAI Provider Directly ===")
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return False
    
    try:
        # Create provider
        config = LLMProviderConfig(
            provider_name="openai",
            api_key=api_key,
            model_name="gpt-3.5-turbo",
            max_tokens=100,
            temperature=0.7
        )
        
        provider = OpenAIProvider(config)
        
        # Test availability
        print("Testing availability...")
        available = await provider.is_available()
        print(f"✅ Provider available: {available}")
        
        # Test chat completion
        print("\nTesting chat completion...")
        messages = [
            LLMMessage(role="system", content="You are a helpful assistant."),
            LLMMessage(role="user", content="What is the capital of France? Answer in one word.")
        ]
        
        response = await provider.chat(messages)
        print(f"✅ Response: {response.text}")
        print(f"   Model: {response.model}")
        print(f"   Tokens used: {response.usage}")
        
        # Test embeddings
        print("\nTesting embeddings...")
        embedding_response = await provider.embed("Hello, world!")
        print(f"✅ Embedding dimensions: {len(embedding_response.embeddings)}")
        print(f"   Model: {embedding_response.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_model_router():
    """Test the Model Router"""
    print("\n=== Testing Model Router ===")
    
    try:
        # Create router with default configuration
        print("Creating router with default configuration...")
        router = await create_default_router()
        
        # List available providers
        providers = router.get_available_providers()
        print(f"\nAvailable providers: {len(providers)}")
        for p in providers:
            print(f"  - {p['name']}: {'✅' if p['available'] else '❌'}")
            if p.get('capabilities'):
                print(f"    Model: {p['capabilities'].get('current_model')}")
        
        if not providers:
            print("❌ No providers available")
            return False
        
        # Test completion
        print("\nTesting completion via router...")
        response = await router.complete(
            prompt="What is 2+2? Answer with just the number.",
            max_tokens=10
        )
        print(f"✅ Response: {response.text}")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        
        # Test chat
        print("\nTesting chat via router...")
        messages = [
            LLMMessage(role="system", content="You are a calculator. Only respond with numbers."),
            LLMMessage(role="user", content="What is 5 times 7?")
        ]
        
        chat_response = await router.chat(messages, max_tokens=10)
        print(f"✅ Response: {chat_response.text}")
        
        # Test embeddings
        print("\nTesting embeddings via router...")
        try:
            embedding_response = await router.embed("Test embedding")
            print(f"✅ Embedding dimensions: {len(embedding_response.embeddings)}")
        except Exception as e:
            print(f"⚠️  Embedding test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_capabilities():
    """Test provider capabilities"""
    print("\n=== Testing Provider Capabilities ===")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    config = LLMProviderConfig(
        provider_name="openai",
        api_key=api_key
    )
    
    provider = OpenAIProvider(config)
    capabilities = provider.get_capabilities()
    
    print("OpenAI Provider Capabilities:")
    print(f"  Current model: {capabilities['current_model']}")
    print(f"  Max tokens: {capabilities['max_tokens']}")
    print(f"  Supports functions: {capabilities['supports_functions']}")
    print(f"  Available models: {capabilities['models']}")
    
    return True

async def main():
    """Run all tests"""
    print("LLM Router Test Suite")
    print("=" * 50)
    
    # Check environment
    print("\nEnvironment Check:")
    print(f"OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
    print(f"ANTHROPIC_API_KEY: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Not set'}")
    
    # Run tests
    tests = [
        ("OpenAI Provider", test_openai_provider),
        ("Model Router", test_model_router),
        ("Provider Capabilities", test_capabilities)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
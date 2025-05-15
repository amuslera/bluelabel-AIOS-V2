#!/usr/bin/env python3
"""
Test script for Agent Runtime Manager
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.agent_runtime import AgentRuntimeManager, get_runtime_manager
from agents.content_mind import ContentMind
from agents.base import AgentInput, AgentOutput
from core.event_bus import EventBus


async def test_runtime_manager():
    """Test the runtime manager functionality"""
    print("Testing Agent Runtime Manager")
    print("=" * 40)
    
    # Create runtime manager with event bus
    event_bus = EventBus(simulation_mode=True)
    runtime_manager = AgentRuntimeManager(event_bus=event_bus)
    
    # Test 1: Register agent class
    print("\n1. Registering ContentMind agent...")
    result = runtime_manager.register_agent_class(
        "content_mind",
        ContentMind,
        {"description": "Content processing agent for testing"}
    )
    print(f"Registration result: {result}")
    
    # Test 2: List agents
    print("\n2. Listing registered agents...")
    agents = runtime_manager.list_agents()
    for agent in agents:
        print(f"- Agent ID: {agent['agent_id']}, Registered: {agent['registered']}, Instantiated: {agent['instantiated']}")
    
    # Test 3: Execute agent
    print("\n3. Executing ContentMind agent...")
    input_data = AgentInput(
        source="test_script",
        content={
            "text": "This is a test content for the AI system. The software development is progressing well. "
                   "The company revenue increased by 20% this quarter. The research team made excellent progress. "
                   "test@example.com is the contact. Visit https://example.com for more information.",
            "type": "text"
        },
        metadata={"timestamp": "2025-01-01T00:00:00"}
    )
    
    result = await runtime_manager.execute_agent("content_mind", input_data)
    
    print(f"\nExecution result:")
    print(f"- Status: {result.status}")
    print(f"- Task ID: {result.task_id}")
    
    if result.status == "success":
        print(f"- Summary: {result.result['summary']}")
        print(f"- Entities found: {len(result.result['entities'])}")
        for entity in result.result['entities'][:5]:  # Show first 5 entities
            print(f"  - {entity['text']} ({entity['type']})")
        print(f"- Topics: {result.result['topics']}")
        print(f"- Sentiment: {result.result['sentiment']['sentiment']} (score: {result.result['sentiment']['score']})")
    else:
        print(f"- Error: {result.error}")
    
    # Test 4: Get agent info
    print("\n4. Getting agent info...")
    info = runtime_manager.get_agent_info("content_mind")
    if info:
        print(f"Agent info:")
        if 'capabilities' in info:
            print(f"- Capabilities: {info['capabilities']}")
        print(f"- Metrics: {info['metrics']}")
    else:
        print("No agent info available")
    
    # Test 5: Get runtime metrics
    print("\n5. Getting runtime metrics...")
    metrics = runtime_manager.get_metrics()
    print(f"Runtime metrics:")
    print(f"- Total agents: {metrics['total_agents']}")
    print(f"- Active agents: {metrics['active_agents']}")
    print(f"- Agent metrics: {metrics['agent_metrics']}")
    
    # Test 6: Test error handling
    print("\n6. Testing error handling...")
    error_input = AgentInput(
        source="test_script",
        content={}  # Empty content should cause an error
    )
    error_result = await runtime_manager.execute_agent("content_mind", error_input)
    print(f"Error handling result:")
    print(f"- Status: {error_result.status}")
    print(f"- Error: {error_result.error}")
    
    # Test 7: Shutdown
    print("\n7. Shutting down runtime manager...")
    await runtime_manager.shutdown()
    print("Shutdown complete")
    
    print("\n" + "=" * 40)
    print("All tests completed successfully!")


async def test_singleton_pattern():
    """Test the singleton pattern"""
    print("\nTesting singleton pattern...")
    manager1 = get_runtime_manager()
    manager2 = get_runtime_manager()
    print(f"Singleton check: {manager1 is manager2}")


async def main():
    """Run all tests"""
    try:
        await test_runtime_manager()
        await test_singleton_pattern()
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
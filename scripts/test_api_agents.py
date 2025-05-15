#!/usr/bin/env python3
"""
Test script for agent API endpoints
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any
import sys
import time


API_BASE_URL = "http://localhost:8000/api/v1"


async def test_list_agents(session: aiohttp.ClientSession):
    """Test listing all agents"""
    print("\n1. Testing list agents endpoint...")
    async with session.get(f"{API_BASE_URL}/agents/") as response:
        data = await response.json()
        print(f"Status: {response.status}")
        print(f"Agents found: {len(data)}")
        for agent in data:
            print(f"  - {agent['agent_id']}: {agent['description']} (registered: {agent['registered']})")
        return response.status == 200


async def test_get_agent_info(session: aiohttp.ClientSession, agent_id: str = "content_mind"):
    """Test getting specific agent info"""
    print(f"\n2. Testing get agent info for '{agent_id}'...")
    async with session.get(f"{API_BASE_URL}/agents/{agent_id}") as response:
        if response.status == 200:
            data = await response.json()
            print(f"Status: {response.status}")
            print(f"Agent ID: {data['agent_id']}")
            print(f"Name: {data['name']}")
            print(f"Description: {data['description']}")
            print(f"Registered: {data['registered']}")
            print(f"Instantiated: {data['instantiated']}")
            if data.get('metrics'):
                print(f"Metrics: {data['metrics']}")
        else:
            print(f"Status: {response.status}")
            error = await response.json()
            print(f"Error: {error}")
        return response.status == 200


async def test_get_agent_capabilities(session: aiohttp.ClientSession, agent_id: str = "content_mind"):
    """Test getting agent capabilities"""
    print(f"\n3. Testing get agent capabilities for '{agent_id}'...")
    async with session.get(f"{API_BASE_URL}/agents/{agent_id}/capabilities") as response:
        if response.status == 200:
            data = await response.json()
            print(f"Status: {response.status}")
            print(f"Agent: {data['name']}")
            print(f"Tools: {len(data['tools'])}")
            for tool in data['tools']:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print(f"Status: {response.status}")
            error = await response.json()
            print(f"Error: {error}")
        return response.status == 200


async def test_execute_agent(session: aiohttp.ClientSession, agent_id: str = "content_mind"):
    """Test executing an agent"""
    print(f"\n4. Testing execute agent '{agent_id}'...")
    
    request_data = {
        "agent_id": agent_id,
        "source": "api_test",
        "content": {
            "text": "This is a test content for the Bluelabel AIOS system. "
                   "The AI technology is advancing rapidly. Companies are investing heavily in AI research. "
                   "Contact test@example.com for more information.",
            "type": "text"
        },
        "metadata": {
            "test": True,
            "timestamp": time.time()
        }
    }
    
    async with session.post(
        f"{API_BASE_URL}/agents/{agent_id}/execute",
        json=request_data
    ) as response:
        if response.status == 200:
            data = await response.json()
            print(f"Status: {response.status}")
            print(f"Task ID: {data['task_id']}")
            print(f"Result Status: {data['status']}")
            if data['status'] == 'success':
                result = data['result']
                print(f"Summary: {result['summary']}")
                print(f"Topics: {result['topics']}")
                print(f"Sentiment: {result['sentiment']['sentiment']} (score: {result['sentiment']['score']})")
                print(f"Entities: {len(result['entities'])}")
        else:
            print(f"Status: {response.status}")
            error = await response.json()
            print(f"Error: {error}")
        return response.status == 200


async def test_agent_metrics(session: aiohttp.ClientSession, agent_id: str = "content_mind"):
    """Test getting agent metrics"""
    print(f"\n5. Testing get agent metrics for '{agent_id}'...")
    async with session.get(f"{API_BASE_URL}/agents/{agent_id}/metrics") as response:
        if response.status == 200:
            data = await response.json()
            print(f"Status: {response.status}")
            if isinstance(data, dict) and 'message' not in data:
                print(f"Total executions: {data.get('total_executions', 0)}")
                print(f"Successful: {data.get('successful_executions', 0)}")
                print(f"Failed: {data.get('failed_executions', 0)}")
                print(f"Average time: {data.get('average_execution_time', 0):.3f}s")
            else:
                print(f"Response: {data}")
        else:
            print(f"Status: {response.status}")
            error = await response.json()
            print(f"Error: {error}")
        return response.status == 200


async def test_all_metrics(session: aiohttp.ClientSession):
    """Test getting metrics for all agents"""
    print("\n6. Testing get all metrics...")
    async with session.get(f"{API_BASE_URL}/agents/metrics/all") as response:
        if response.status == 200:
            data = await response.json()
            print(f"Status: {response.status}")
            print(f"Total agents: {data['total_agents']}")
            print(f"Active agents: {data['active_agents']}")
            print("Agent metrics:")
            for agent_id, metrics in data['agent_metrics'].items():
                print(f"  - {agent_id}: {metrics['total_executions']} executions")
        else:
            print(f"Status: {response.status}")
            error = await response.json()
            print(f"Error: {error}")
        return response.status == 200


async def test_register_agent(session: aiohttp.ClientSession):
    """Test registering a new agent"""
    print("\n7. Testing register agent...")
    
    # Note: This would fail unless we have a valid agent class
    registration_data = {
        "agent_id": "test_agent",
        "agent_class": "agents.content_mind.ContentMind",  # Reuse existing class for test
        "config": {
            "description": "Test agent registration",
            "test": True
        }
    }
    
    async with session.post(
        f"{API_BASE_URL}/agents/register",
        json=registration_data
    ) as response:
        data = await response.json()
        print(f"Status: {response.status}")
        print(f"Response: {data}")
        return response.status in [200, 400]  # 400 expected if agent already exists


async def main():
    """Run all API tests"""
    print("Testing Agent API Endpoints")
    print("=" * 40)
    
    # Create session
    async with aiohttp.ClientSession() as session:
        tests = [
            ("List Agents", test_list_agents(session)),
            ("Get Agent Info", test_get_agent_info(session)),
            ("Get Agent Capabilities", test_get_agent_capabilities(session)),
            ("Execute Agent", test_execute_agent(session)),
            ("Get Agent Metrics", test_agent_metrics(session)),
            ("Get All Metrics", test_all_metrics(session)),
            ("Register Agent", test_register_agent(session)),
        ]
        
        results = []
        for test_name, test_coro in tests:
            try:
                result = await test_coro
                results.append((test_name, result))
            except Exception as e:
                print(f"\nError in {test_name}: {str(e)}")
                results.append((test_name, False))
        
        print("\n" + "=" * 40)
        print("Test Results")
        print("=" * 40)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        return passed == total


if __name__ == "__main__":
    # First, make sure the API server is running
    print("Make sure the API server is running at http://localhost:8000")
    print("Start it with: python scripts/run_with_logging.py")
    print()
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
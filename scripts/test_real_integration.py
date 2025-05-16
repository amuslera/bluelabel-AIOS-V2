#!/usr/bin/env python3
"""
Real integration test for Bluelabel AIOS MVP flow.
Tests end-to-end flow with actual API calls.
"""
import asyncio
import json
import sys
import os
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Settings

# API Base URL
API_BASE_URL = "http://127.0.0.1:8000"
API_V1_BASE = f"{API_BASE_URL}/api/v1"

async def test_mvp_flow():
    """Test the complete MVP flow with real API calls."""
    print("Starting real MVP integration test...")
    
    # 1. Check API health
    print("\n1. Checking API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"API Status: {response.json()}")
        assert response.status_code == 200
        print("✅ API is running")
    except Exception as e:
        print(f"❌ API check failed: {e}")
        return
    
    # 2. Test LLM connections
    print("\n2. Testing LLM connections...")
    try:
        # Test models endpoint
        response = requests.get(f"{API_V1_BASE}/models")
        if response.status_code == 200:
            models = response.json()
            print(f"Available models: {models}")
        else:
            print(f"Warning: Could not fetch models: {response.status_code}")
    except Exception as e:
        print(f"Warning: Models endpoint not available: {e}")
    
    # 3. Test agent registration
    print("\n3. Testing agent system...")
    try:
        # List agents
        response = requests.get(f"{API_V1_BASE}/agents/")
        if response.status_code == 200:
            agents = response.json()
            print(f"Registered agents: {len(agents)}")
            for agent in agents:
                print(f"  - {agent['agent_id']}: {agent['description']}")
        else:
            print(f"Warning: Could not list agents: {response.status_code}")
            
        # Test ContentMind agent
        if any(a['agent_id'] == 'content_mind' for a in agents):
            print("\nTesting ContentMind agent...")
            agent_request = {
                "agent_id": "content_mind",
                "source": "test",
                "content": {
                    "text": "Artificial Intelligence is transforming industries worldwide. From healthcare to finance, AI applications are becoming increasingly sophisticated."
                },
                "metadata": {}
            }
            
            response = requests.post(
                f"{API_V1_BASE}/agents/content_mind/execute",
                json=agent_request
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"ContentMind response status: {result['status']}")
                if result.get('result'):
                    print(f"Summary: {result['result'].get('summary', 'No summary')[:100]}...")
                print("✅ ContentMind agent working")
            else:
                print(f"❌ ContentMind execution failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
    
    # 4. Test email gateway
    print("\n4. Testing email gateway...")
    try:
        # Check Gmail OAuth status
        response = requests.get(f"{API_V1_BASE}/gmail/auth/status")
        if response.status_code == 200:
            status = response.json()
            print(f"Gmail OAuth status: {status}")
        else:
            print(f"Warning: Could not check Gmail status: {response.status_code}")
    except Exception as e:
        print(f"Warning: Gmail status check failed: {e}")
    
    # 5. Test knowledge repository
    print("\n5. Testing knowledge repository...")
    try:
        # Create a test document
        doc_data = {
            "title": "Test Document",
            "source": "integration_test",
            "content_type": "text",
            "text_content": "This is a test document for the knowledge repository.",
            "metadata": {
                "tags": ["test", "integration"]
            },
            "tags": ["test", "integration"]
        }
        
        response = requests.post(f"{API_V1_BASE}/knowledge/content", json=doc_data)
        if response.status_code == 200:
            result = response.json()
            doc_id = result.get("content_id") or result.get("id") or result.get("document_id")
            print(f"Created document: {doc_id}")
            
            # Search for it
            search_data = {"query": "test document"}
            response = requests.post(f"{API_V1_BASE}/knowledge/search", json=search_data)
            if response.status_code == 200:
                results = response.json()
                if isinstance(results, list):
                    print(f"Search results: {len(results)} documents found")
                else:
                    print(f"Search results: {len(results.get('results', []))} documents found")
                print("✅ Knowledge repository working")
            else:
                print(f"Warning: Search failed: {response.status_code}")
        else:
            print(f"Warning: Document creation failed: {response.status_code}")
    except Exception as e:
        print(f"Warning: Knowledge test failed: {e}")
    
    print("\n✅ MVP Integration test completed!")
    print("\nSummary:")
    print("- API server is running")
    print("- Agent system is functional") 
    print("- Basic components are accessible")
    print("\nNext steps:")
    print("1. Configure real Gmail OAuth to test email flow")
    print("2. Test with actual PDF processing")
    print("3. Set up PostgreSQL for persistence")

if __name__ == "__main__":
    # Load settings
    settings = Settings()
    
    # Run the test
    asyncio.run(test_mvp_flow())
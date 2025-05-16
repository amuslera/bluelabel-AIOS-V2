#!/usr/bin/env python3
"""Full integration test for the API server."""

import asyncio
import httpx
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()


async def test_api_server():
    """Test the API server endpoints."""
    base_url = "http://localhost:8000"
    
    print("🌐 Testing API Server")
    print("=" * 50)
    print(f"Base URL: {base_url}")
    print("\nNote: Make sure the API server is running with ./scripts/run_api.sh")
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Test health endpoint
        print("1️⃣ Testing health endpoint...")
        try:
            resp = await client.get(f"{base_url}/health")
            if resp.status_code == 200:
                print(f"✅ Health check: {resp.json()}")
            else:
                print(f"❌ Health check failed: {resp.status_code}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("\n⚠️  API server is not running. Start it with: ./scripts/run_api.sh")
            return
        
        # 2. Test agent endpoints
        print("\n2️⃣ Testing agent endpoints...")
        try:
            resp = await client.get(f"{base_url}/api/v1/agents")
            if resp.status_code == 200:
                agents = resp.json()
                print(f"✅ Available agents: {len(agents)}")
                for agent in agents:
                    print(f"   - {agent.get('name', 'Unknown')}: {agent.get('type', 'Unknown')}")
            else:
                print(f"❌ Failed to get agents: {resp.status_code}")
        except Exception as e:
            print(f"❌ Agent endpoint error: {e}")
        
        # 3. Test ContentMind execution
        print("\n3️⃣ Testing ContentMind agent...")
        try:
            payload = {
                "content": "This is a test message. Please summarize it briefly.",
                "content_type": "text/plain",
                "operation": "summarize"
            }
            
            resp = await client.post(f"{base_url}/api/v1/agents/content_mind/execute", json=payload)
            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ ContentMind executed successfully")
                print(f"   Status: {result.get('status')}")
                print(f"   Summary: {result.get('content', {}).get('summary', 'N/A')[:100]}...")
            else:
                print(f"❌ ContentMind execution failed: {resp.status_code}")
                print(f"   Error: {resp.text[:200]}")
        except Exception as e:
            print(f"❌ ContentMind error: {e}")
        
        # 4. Test knowledge repository
        print("\n4️⃣ Testing knowledge repository...")
        try:
            # Create an item
            item_data = {
                "source": "test_integration",
                "title": "Integration Test Item",
                "content": "This is test content for integration testing.",
                "content_type": "text"
            }
            
            resp = await client.post(f"{base_url}/api/v1/knowledge/items", json=item_data)
            if resp.status_code == 200:
                item = resp.json()
                item_id = item.get("id")
                print(f"✅ Created item: {item_id}")
                
                # Retrieve the item
                resp = await client.get(f"{base_url}/api/v1/knowledge/items/{item_id}")
                if resp.status_code == 200:
                    print("✅ Retrieved item successfully")
                else:
                    print(f"❌ Failed to retrieve item: {resp.status_code}")
            else:
                print(f"❌ Failed to create item: {resp.status_code}")
                print(f"   Error: {resp.text[:200]}")
        except Exception as e:
            print(f"❌ Knowledge repository error: {e}")
        
        # 5. Test workflow endpoints
        print("\n5️⃣ Testing workflow endpoints...")
        try:
            # Create a workflow
            workflow_data = {
                "name": "Test Integration Workflow",
                "description": "Integration test workflow",
                "steps": [
                    {
                        "name": "Process Content",
                        "agent_type": "content_mind",
                        "input_mappings": [
                            {
                                "source": "input",
                                "source_key": "content",
                                "target_key": "content"
                            }
                        ]
                    }
                ]
            }
            
            resp = await client.post(f"{base_url}/api/v1/workflows/", json=workflow_data)
            if resp.status_code == 200:
                workflow = resp.json()
                workflow_id = workflow.get("id")
                print(f"✅ Created workflow: {workflow_id}")
                
                # Execute the workflow
                execution_data = {
                    "input_data": {"content": "Test workflow content"},
                    "context": {}
                }
                
                resp = await client.post(f"{base_url}/api/v1/workflows/{workflow_id}/execute", json=execution_data)
                if resp.status_code == 200:
                    execution = resp.json()
                    print(f"✅ Started workflow execution: {execution.get('id')}")
                else:
                    print(f"❌ Failed to execute workflow: {resp.status_code}")
            else:
                print(f"❌ Failed to create workflow: {resp.status_code}")
                print(f"   Error: {resp.text[:200]}")
        except Exception as e:
            print(f"❌ Workflow error: {e}")
        
        # 6. Test Gmail OAuth status
        print("\n6️⃣ Testing Gmail OAuth...")
        try:
            resp = await client.get(f"{base_url}/api/v1/gmail-complete/auth/status")
            if resp.status_code == 200:
                status = resp.json()
                print(f"✅ Gmail OAuth status: {status}")
            else:
                print(f"❌ Failed to get Gmail status: {resp.status_code}")
        except Exception as e:
            print(f"❌ Gmail OAuth error: {e}")
        
        # 7. Test event bus status
        print("\n7️⃣ Testing event bus...")
        try:
            resp = await client.get(f"{base_url}/api/v1/events/status")
            if resp.status_code == 200:
                status = resp.json()
                print(f"✅ Event bus status: {status}")
            else:
                print(f"❌ Failed to get event bus status: {resp.status_code}")
        except Exception as e:
            print(f"❌ Event bus error: {e}")


if __name__ == "__main__":
    print("🚀 Bluelabel AIOS v2 Full Integration Test")
    print("=========================================\n")
    
    print("📋 Prerequisites:")
    print("1. LLM API keys configured in .env ✅")
    print("2. API server running (./scripts/run_api.sh)")
    print("3. PostgreSQL (optional - will use file-based storage)")
    print("4. Redis (optional - in simulation mode)")
    print()
    
    asyncio.run(test_api_server())
    
    print("\n" + "=" * 50)
    print("💡 If tests fail:")
    print("1. Make sure the API server is running")
    print("2. Check logs for detailed error messages")
    print("3. Verify all environment variables are set")
    print("4. Try running individual test scripts")
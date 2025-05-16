#!/usr/bin/env python3
"""Comprehensive integration test for all system components."""

import asyncio
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()


async def test_all_integrations():
    """Test all system integrations comprehensively."""
    base_url = "http://localhost:8000"
    results = {
        "passed": 0,
        "failed": 0,
        "warnings": 0
    }
    
    print("🔍 Comprehensive Integration Test")
    print("=" * 50)
    
    # Check environment
    print("\n📋 Environment Check:")
    env_vars = {
        "OPENAI_API_KEY": "LLM Provider",
        "ANTHROPIC_API_KEY": "LLM Provider (Optional)",
        "GOOGLE_GENERATIVEAI_API_KEY": "LLM Provider (Optional)",
        "DATABASE_URL": "PostgreSQL",
        "REDIS_HOST": "Redis",
        "GOOGLE_CLIENT_ID": "Gmail OAuth",
        "GOOGLE_CLIENT_SECRET": "Gmail OAuth"
    }
    
    for var, purpose in env_vars.items():
        value = os.getenv(var)
        if value and not value.startswith("your_"):
            print(f"✅ {var}: Configured ({purpose})")
        else:
            print(f"❌ {var}: Not configured ({purpose})")
            if "Optional" not in purpose:
                results["warnings"] += 1
    
    # Start testing API endpoints
    print("\n🌐 Testing API Endpoints:")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health check
        print("\n1️⃣ Health Check")
        try:
            resp = await client.get(f"{base_url}/health")
            if resp.status_code == 200:
                print(f"✅ Health check passed: {resp.json()}")
                results["passed"] += 1
            else:
                print(f"❌ Health check failed: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Health check error: {e}")
            results["failed"] += 1
            return results
        
        # 2. Test LLM via ContentMind agent
        print("\n2️⃣ LLM Integration (ContentMind)")
        try:
            resp = await client.post(
                f"{base_url}/api/v1/agents/content_mind/execute",
                json={
                    "content": "This is a test. Please summarize this message.",
                    "content_type": "text/plain",
                    "operation": "summarize"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ LLM test passed: {data.get('status')}")
                print(f"   Summary: {data.get('content', {}).get('summary', '')[:100]}...")
                results["passed"] += 1
            else:
                print(f"❌ LLM test failed: {resp.status_code}")
                print(f"   Error: {resp.text}")
                results["failed"] += 1
        except Exception as e:
            print(f"❌ LLM test error: {e}")
            results["failed"] += 1
        
        # 3. Test Database via Knowledge Repository
        print("\n3️⃣ Database Integration")
        try:
            # Create item
            test_item = {
                "source": "integration_test",
                "title": f"Test Item {datetime.now(timezone.utc).isoformat()}",
                "content": "This is a test content item",
                "content_type": "text",
                "metadata": {"test": True}
            }
            
            resp = await client.post(
                f"{base_url}/api/v1/knowledge/items",
                json=test_item
            )
            
            if resp.status_code == 200:
                item_data = resp.json()
                item_id = item_data.get("id")
                print(f"✅ Database write passed: Created item {item_id}")
                
                # Retrieve item
                resp = await client.get(f"{base_url}/api/v1/knowledge/items/{item_id}")
                if resp.status_code == 200:
                    print("✅ Database read passed")
                    results["passed"] += 2
                else:
                    print(f"❌ Database read failed: {resp.status_code}")
                    results["failed"] += 1
                    results["passed"] += 1
            else:
                print(f"❌ Database write failed: {resp.status_code}")
                print(f"   Error: {resp.text}")
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Database test error: {e}")
            results["failed"] += 1
        
        # 4. Test Event Bus
        print("\n4️⃣ Event Bus (Redis)")
        try:
            resp = await client.get(f"{base_url}/api/v1/events/status")
            if resp.status_code == 200:
                status = resp.json()
                if status.get("status") == "connected":
                    print("✅ Event bus connected")
                    results["passed"] += 1
                else:
                    print(f"⚠️  Event bus status: {status}")
                    results["warnings"] += 1
            else:
                print(f"❌ Event bus test failed: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Event bus test error: {e}")
            results["failed"] += 1
        
        # 5. Test Gmail OAuth
        print("\n5️⃣ Gmail OAuth")
        try:
            resp = await client.get(f"{base_url}/api/v1/gmail-complete/auth/status")
            if resp.status_code == 200:
                auth_status = resp.json()
                if auth_status.get("credentials_exist"):
                    print("✅ Gmail OAuth configured")
                    results["passed"] += 1
                else:
                    print("⚠️  Gmail OAuth not configured (run auth flow)")
                    results["warnings"] += 1
            else:
                print(f"❌ Gmail OAuth test failed: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Gmail OAuth test error: {e}")
            results["failed"] += 1
        
        # 6. Test Workflow Engine
        print("\n6️⃣ Workflow Engine")
        try:
            # Create a simple workflow
            workflow_def = {
                "name": "Test Workflow",
                "description": "Integration test workflow",
                "steps": [
                    {
                        "name": "Test Step",
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
            
            resp = await client.post(
                f"{base_url}/api/v1/workflows/",
                json=workflow_def
            )
            
            if resp.status_code == 200:
                workflow = resp.json()
                workflow_id = workflow.get("id")
                print(f"✅ Workflow created: {workflow_id}")
                
                # Execute workflow
                execution_data = {
                    "input_data": {"content": "Test workflow execution"},
                    "context": {},
                    "user_id": "test"
                }
                
                resp = await client.post(
                    f"{base_url}/api/v1/workflows/{workflow_id}/execute",
                    json=execution_data
                )
                
                if resp.status_code == 200:
                    print("✅ Workflow execution started")
                    results["passed"] += 2
                else:
                    print(f"❌ Workflow execution failed: {resp.status_code}")
                    results["failed"] += 1
                    results["passed"] += 1
            else:
                print(f"❌ Workflow creation failed: {resp.status_code}")
                results["failed"] += 1
        except Exception as e:
            print(f"❌ Workflow test error: {e}")
            results["failed"] += 1
        
        # 7. Test Communication Endpoints
        print("\n7️⃣ Communication System")
        try:
            resp = await client.post(
                f"{base_url}/api/v1/communication/process",
                json={
                    "channel": "test",
                    "sender": "test@example.com",
                    "content": "Test message",
                    "metadata": {}
                }
            )
            
            if resp.status_code in [200, 201]:
                print("✅ Communication system active")
                results["passed"] += 1
            else:
                print(f"⚠️  Communication system response: {resp.status_code}")
                results["warnings"] += 1
        except Exception as e:
            print(f"❌ Communication test error: {e}")
            results["failed"] += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⚠️  Warnings: {results['warnings']}")
    
    total_tests = results['passed'] + results['failed']
    if total_tests > 0:
        success_rate = (results['passed'] / total_tests) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Recommendations
    if results['warnings'] > 0 or results['failed'] > 0:
        print("\n💡 Recommendations:")
        if results['warnings'] > 0:
            print("- Configure missing environment variables in .env")
            print("- Run Gmail OAuth flow if needed")
        if results['failed'] > 0:
            print("- Check that all services are running (API, Redis, PostgreSQL)")
            print("- Verify API keys are valid")
            print("- Check logs for detailed error messages")
    
    return results


if __name__ == "__main__":
    print("🚀 Bluelabel AIOS v2 Integration Test")
    print("=====================================")
    print("Note: Ensure the API server is running at localhost:8000")
    print()
    
    asyncio.run(test_all_integrations())
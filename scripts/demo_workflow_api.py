#!/usr/bin/env python3
"""
Demo script for testing workflow API endpoints.
"""
import asyncio
import json
import sys
from uuid import uuid4
from httpx import AsyncClient

from shared.schemas.base import AgentType


async def demo_workflow_api():
    """Demo workflow API operations."""
    base_url = "http://localhost:8000/api/v1/workflows"
    
    async with AsyncClient() as client:
        try:
            # Create a workflow
            print("\n=== Creating workflow ===")
            workflow_data = {
                "name": "Content Analysis Workflow",
                "description": "Analyze and summarize content",
                "version": "1.0.0",
                "steps": [
                    {
                        "name": "Extract Content",
                        "agent_type": "content_mind",
                        "input_mappings": [
                            {
                                "source": "input",
                                "source_key": "url",
                                "target_key": "content"
                            }
                        ],
                        "output_mappings": [
                            {
                                "source_key": "extracted_text",
                                "target": "output",
                                "target_key": "raw_content"
                            }
                        ]
                    },
                    {
                        "name": "Analyze Content",
                        "agent_type": "content_mind",
                        "input_mappings": [
                            {
                                "source": "steps",
                                "source_key": "step-1.extracted_text",
                                "target_key": "content"
                            }
                        ],
                        "output_mappings": [
                            {
                                "source_key": "summary",
                                "target": "output",
                                "target_key": "analysis.summary"
                            },
                            {
                                "source_key": "key_points",
                                "target": "output",
                                "target_key": "analysis.key_points"
                            }
                        ],
                        "condition": "len(steps['step-1']['extracted_text']) > 100"
                    }
                ],
                "metadata": {"category": "content_processing"},
                "tags": ["demo", "analysis"]
            }
            
            response = await client.post(f"{base_url}/", json=workflow_data)
            if response.status_code == 200:
                workflow = response.json()
                workflow_id = workflow["id"]
                print(f"Created workflow: {workflow_id}")
                print(json.dumps(workflow, indent=2))
            else:
                print(f"Failed to create workflow: {response.status_code}")
                print(response.text)
                return
            
            # List workflows
            print("\n=== Listing workflows ===")
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                workflows = response.json()
                print(f"Found {len(workflows)} workflows")
                for w in workflows:
                    print(f"  - {w['name']} (ID: {w['id']})")
            else:
                print(f"Failed to list workflows: {response.status_code}")
            
            # Get workflow by ID
            print(f"\n=== Getting workflow {workflow_id} ===")
            response = await client.get(f"{base_url}/{workflow_id}")
            if response.status_code == 200:
                workflow = response.json()
                print(f"Retrieved workflow: {workflow['name']}")
                print(f"Version: {workflow['version']}")
                print(f"Active: {workflow['active']}")
                print(f"Steps: {len(workflow['steps'])}")
            else:
                print(f"Failed to get workflow: {response.status_code}")
            
            # Execute workflow
            print(f"\n=== Executing workflow {workflow_id} ===")
            execution_data = {
                "input_data": {
                    "url": "https://example.com/article",
                    "content": "This is a test article about artificial intelligence and its applications in modern technology."
                },
                "context": {"source": "demo"},
                "user_id": "demo-user"
            }
            
            response = await client.post(f"{base_url}/{workflow_id}/execute", json=execution_data)
            if response.status_code == 200:
                execution = response.json()
                execution_id = execution["id"]
                print(f"Started execution: {execution_id}")
                print(f"Status: {execution['status']}")
            else:
                print(f"Failed to execute workflow: {response.status_code}")
                print(response.text)
                return
            
            # Wait and check execution status
            print("\n=== Checking execution status ===")
            for i in range(10):
                await asyncio.sleep(2)
                response = await client.get(f"{base_url}/executions/{execution_id}")
                if response.status_code == 200:
                    execution = response.json()
                    print(f"Attempt {i+1}: Status = {execution['status']}")
                    
                    if execution['status'] in ['completed', 'failed']:
                        print(f"\nFinal status: {execution['status']}")
                        if execution['output_data']:
                            print("Output data:")
                            print(json.dumps(execution['output_data'], indent=2))
                        if execution['error']:
                            print(f"Error: {execution['error']}")
                        break
                else:
                    print(f"Failed to get execution status: {response.status_code}")
                    break
            
            # List executions
            print("\n=== Listing executions ===")
            response = await client.get(f"{base_url}/executions")
            if response.status_code == 200:
                executions = response.json()
                print(f"Found {len(executions)} executions")
                for exe in executions:
                    print(f"  - ID: {exe['id']}, Status: {exe['status']}, Created: {exe['created_at']}")
            else:
                print(f"Failed to list executions: {response.status_code}")
            
            # Test workflow update
            print(f"\n=== Updating workflow {workflow_id} ===")
            update_data = {
                "description": "Updated workflow description",
                "tags": ["demo", "analysis", "updated"],
                "metadata": {"category": "content_processing", "updated": True}
            }
            
            response = await client.put(f"{base_url}/{workflow_id}", json=update_data)
            if response.status_code == 200:
                updated_workflow = response.json()
                print(f"Updated workflow: {updated_workflow['name']}")
                print(f"New description: {updated_workflow['description']}")
                print(f"Tags: {updated_workflow['tags']}")
            else:
                print(f"Failed to update workflow: {response.status_code}")
            
            # Cancel an execution (start new one first)
            print(f"\n=== Testing execution cancellation ===")
            response = await client.post(f"{base_url}/{workflow_id}/execute", json=execution_data)
            if response.status_code == 200:
                new_execution = response.json()
                new_execution_id = new_execution["id"]
                print(f"Started new execution: {new_execution_id}")
                
                # Cancel immediately
                await asyncio.sleep(0.5)
                response = await client.post(f"{base_url}/executions/{new_execution_id}/cancel")
                if response.status_code == 200:
                    print("Execution cancelled successfully")
                else:
                    print(f"Failed to cancel execution: {response.status_code}")
                    print(response.text)
            
            # Deactivate workflow
            print(f"\n=== Deactivating workflow {workflow_id} ===")
            response = await client.delete(f"{base_url}/{workflow_id}")
            if response.status_code == 200:
                print("Workflow deactivated successfully")
            else:
                print(f"Failed to deactivate workflow: {response.status_code}")
            
        except Exception as e:
            print(f"Error during demo: {e}")


if __name__ == "__main__":
    print("Starting Workflow API Demo")
    print("=" * 50)
    print("\nNote: Make sure the API server is running at localhost:8000")
    print("Run with: ./scripts/run_api.sh")
    
    asyncio.run(demo_workflow_api())
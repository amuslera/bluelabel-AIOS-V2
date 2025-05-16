#!/usr/bin/env python3
"""Find the actual email sending endpoint"""
import aiohttp
import asyncio
import json


async def find_send_endpoint():
    """Find the correct endpoint for sending emails"""
    base_url = "http://localhost:8081"
    
    print("Finding Email Send Endpoint")
    print("==========================\n")
    
    async with aiohttp.ClientSession() as session:
        # 1. Get the OpenAPI spec to find all endpoints
        print("1. Getting API specification...")
        async with session.get(f"{base_url}/openapi.json") as response:
            spec = await response.json()
            
            # Find all endpoints
            all_paths = spec.get("paths", {})
            
            print("\nAll available endpoints:")
            for path, methods in all_paths.items():
                for method, details in methods.items():
                    summary = details.get("summary", "")
                    if any(word in path.lower() or word in summary.lower() 
                           for word in ["email", "send", "message", "mail"]):
                        print(f"  {method.upper()} {path}: {summary}")
            
            print("\n\nDetailed endpoint information:")
            for path, methods in all_paths.items():
                if "email" in path.lower() or "message" in path.lower():
                    print(f"\n{path}:")
                    for method, details in methods.items():
                        print(f"  {method.upper()}: {details.get('summary', '')}")
                        if "requestBody" in details:
                            schema = details["requestBody"].get("content", {}).get("application/json", {}).get("schema", {})
                            print(f"    Expects: {schema}")
        
        # 2. Test specific endpoints that might be for sending
        print("\n\n2. Testing potential send endpoints...")
        test_endpoints = [
            # Based on common patterns
            "/email/send",
            "/emails/send",
            "/message/send",
            "/messages/send",
            "/gateway/email/send",
            "/gateway/message/send",
            "/gateway/messages/send",
            "/send-email",
            "/send_email",
            "/sendEmail",
            
            # Based on what we found
            "/gateway/email",
            "/gateway/email/google",
            
            # RESTful patterns
            "/emails",
            "/messages",
            "/gateway/emails",
            "/gateway/messages",
        ]
        
        test_payload = {
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test email"
        }
        
        for endpoint in test_endpoints:
            try:
                # Try POST
                async with session.post(
                    f"{base_url}{endpoint}",
                    json=test_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 404:
                        content = await response.text()
                        print(f"\nPOST {endpoint}: {response.status}")
                        if response.status in [200, 201]:
                            print(f"  Success response: {content[:200]}")
                        elif response.status == 422:
                            print(f"  Validation error (good sign!): {content[:200]}")
                        else:
                            print(f"  Response: {content[:200]}")
            except Exception as e:
                print(f"POST {endpoint}: Error - {type(e).__name__}")
        
        # 3. Check if there's a message queue or similar
        print("\n\n3. Looking for message/email related endpoints...")
        for path in all_paths.keys():
            print(f"  {path}")


async def test_agent_endpoint():
    """Check if emails are sent through agents"""
    base_url = "http://localhost:8081"
    
    print("\n\n4. Testing agent endpoints...")
    
    async with aiohttp.ClientSession() as session:
        # Test agent endpoints
        agent_endpoints = [
            "/agents",
            "/agent/process",
            "/agents/process",
            "/process",
        ]
        
        for endpoint in agent_endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    if response.status != 404:
                        print(f"GET {endpoint}: {response.status}")
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(find_send_endpoint())
    asyncio.run(test_agent_endpoint())
    
    print("\n\nConclusions:")
    print("1. The /gateway/email/google endpoint configures the email service")
    print("2. We need to find the actual send endpoint")
    print("3. Check the backend API documentation or code")
    print("4. The email might be sent through a different mechanism (agents, tasks, etc.)")
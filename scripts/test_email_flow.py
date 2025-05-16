#!/usr/bin/env python3
"""Test the complete email flow"""
import aiohttp
import asyncio
import json


async def test_email_flow():
    """Test how emails are actually sent in this system"""
    base_url = "http://localhost:8081"
    
    print("Testing Email Flow")
    print("==================\n")
    
    async with aiohttp.ClientSession() as session:
        # 1. Check if email gateway is configured
        print("1. Checking email gateway configuration...")
        async with session.get(f"{base_url}/gateway/email/status") as response:
            status = await response.json()
            print(f"Email status: {json.dumps(status, indent=2)}")
        
        # 2. Start email gateway if needed
        if status.get("status") != "running":
            print("\n2. Starting email gateway...")
            async with session.post(f"{base_url}/gateway/email/start") as response:
                start_result = await response.json()
                print(f"Start result: {json.dumps(start_result, indent=2)}")
        
        # 3. Simulate an email (this might be how emails are sent)
        print("\n3. Testing email simulation...")
        simulate_payload = {
            "from": "test@example.com",
            "to": "a@bluelabel.ventures",
            "subject": "Test Email from Simulation",
            "body": "This is a test email sent through simulation"
        }
        
        try:
            async with session.post(
                f"{base_url}/gateway/email/simulate",
                json=simulate_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                print(f"Simulate result: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Simulate error: {e}")
        
        # 4. Check if emails are processed through agents
        print("\n4. Checking agent processing...")
        async with session.get(f"{base_url}/agents") as response:
            if response.status == 200:
                agents = await response.json()
                print(f"Available agents: {json.dumps(agents, indent=2)}")
                
                # Look for email-related agents
                for agent in agents:
                    if isinstance(agent, dict):
                        agent_id = agent.get("id", agent.get("name", ""))
                        if any(word in agent_id.lower() for word in ["email", "gateway", "send"]):
                            print(f"\nFound email agent: {agent_id}")
                            
                            # Test processing with this agent
                            process_payload = {
                                "content": {
                                    "to": "a@bluelabel.ventures",
                                    "subject": "Test via Agent",
                                    "body": "Test email through agent processing"
                                }
                            }
                            
                            try:
                                async with session.post(
                                    f"{base_url}/agents/{agent_id}/process",
                                    json=process_payload,
                                    headers={"Content-Type": "application/json"}
                                ) as process_response:
                                    process_result = await process_response.json()
                                    print(f"Process result: {json.dumps(process_result, indent=2)}")
                            except Exception as e:
                                print(f"Process error: {e}")
        
        # 5. Check the actual Gmail sending mechanism
        print("\n5. Looking for Gmail integration...")
        
        # This system might use a different flow
        # Let's check if there's a task or job system
        endpoints_to_check = [
            "/scheduler/digests",
            "/components",
            "/knowledge",
            "/test/process",
        ]
        
        for endpoint in endpoints_to_check:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    if response.status == 200:
                        print(f"\n{endpoint}: Available")
                        data = await response.json()
                        print(f"Data: {json.dumps(data, indent=2)[:200]}...")
            except Exception:
                pass


async def check_backend_logs():
    """Instructions for checking backend logs"""
    print("\n\nTo Check Backend Logs:")
    print("======================")
    print("1. Look at the terminal where the backend API (port 8081) is running")
    print("2. Check for any error messages when 'sending' emails")
    print("3. Look for actual Gmail API calls")
    print("4. Check if emails are being queued but not sent")
    print("\nThe backend might be:")
    print("- Simulating email sends without actually sending")
    print("- Queuing emails for batch processing")
    print("- Missing actual Gmail send implementation")
    print("- Using a different endpoint or mechanism for sending")


if __name__ == "__main__":
    asyncio.run(test_email_flow())
    asyncio.run(check_backend_logs())
    
    print("\n\nNext Steps:")
    print("===========")
    print("1. Check the backend API source code")
    print("2. Look for the actual Gmail send implementation")
    print("3. Verify OAuth scopes include gmail.send")
    print("4. Check if there's a separate worker/job for sending emails")
    print("5. Test with a different email client to confirm Gmail access works")
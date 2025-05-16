#!/usr/bin/env python3
"""Test the Gateway Agent implementation"""
import os
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.gateway_agent import GatewayAgent
from agents.base import AgentInput, AgentOutput

async def test_gateway_agent():
    print("Gateway Agent Test")
    print("==================")
    
    # Check environment variables
    required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {missing_vars}")
        print("\nPlease ensure your .env file contains the required OAuth credentials.")
        return
    
    # Create Gateway Agent
    gateway = GatewayAgent(name="TestGateway")
    
    print("\nInitializing Gateway Agent...")
    try:
        success = await gateway.initialize()
        if not success:
            print("Failed to initialize Gateway Agent")
            return
        
        print("Gateway Agent initialized successfully!")
        print(f"Status: {gateway.status}")
        print(f"Capabilities: {gateway.get_capabilities()}")
        
        # Test status check
        print("\n1. Testing status check...")
        status_input = AgentInput(
            tenant_id="test",
            conversation_id="test-conv",
            timestamp=datetime.utcnow(),
            payload={
                "action": "status",
                "channel": "email"
            }
        )
        
        status_output = await gateway.process(status_input)
        print(f"Status: {status_output.payload}")
        
        # Test sending email
        print("\n2. Testing email send...")
        send_input = AgentInput(
            tenant_id="test",
            conversation_id="test-conv",
            timestamp=datetime.utcnow(),
            payload={
                "action": "send",
                "channel": "email",
                "to": "test@example.com",
                "subject": "Test from Gateway Agent",
                "body": "This is a test email sent through the Gateway Agent."
            }
        )
        
        send_output = await gateway.process(send_input)
        print(f"Send result: {send_output.payload}")
        
        # Test fetching emails
        print("\n3. Testing email fetch...")
        fetch_input = AgentInput(
            tenant_id="test",
            conversation_id="test-conv",
            timestamp=datetime.utcnow(),
            payload={
                "action": "fetch",
                "channel": "email",
                "limit": 5
            }
        )
        
        fetch_output = await gateway.process(fetch_input)
        messages = fetch_output.payload.get("messages", [])
        print(f"Fetched {len(messages)} messages:")
        for msg in messages[:3]:  # Show first 3
            print(f"  - {msg['subject']} (from: {msg['from']})")
        
        # Show metrics
        print(f"\nAgent Metrics: {gateway.metrics}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Shutdown agent
        await gateway.shutdown()
        print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(test_gateway_agent())
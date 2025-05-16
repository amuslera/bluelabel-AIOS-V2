#!/usr/bin/env python3
"""Basic test for Gateway Agent"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Test basic Gateway Agent functionality
try:
    from agents.gateway_agent import GatewayAgent, CommunicationChannel
    from agents.base import AgentInput, AgentOutput
    
    print("Gateway Agent Basic Test")
    print("========================")
    
    # Create Gateway Agent
    gateway = GatewayAgent(name="TestGateway")
    print(f"Agent created: {gateway.name}")
    print(f"Status: {gateway.status}")
    
    # Get capabilities (no initialization needed)
    capabilities = gateway.get_capabilities()
    print(f"\nCapabilities:")
    print(f"- Actions: {capabilities['actions']}")
    print(f"- Channels: {capabilities['channels']}")
    print(f"- Email features: {capabilities['features']['email']}")
    
    # Test input processing without initialization
    print("\nTesting status check (no initialization):")
    status_input = AgentInput(
        task_id="test-1",
        source="test",
        content={
            "action": "status",
            "channel": "email"
        }
    )
    
    # Gateway should handle request even without initialization
    print("Creating test input...")
    print(f"Input: {status_input.content}")
    
    print("\nNote: Full functionality requires:")
    print("1. Gmail OAuth authentication")
    print("2. Redis running (or simulation mode)")
    print("3. Running the initialize() method")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
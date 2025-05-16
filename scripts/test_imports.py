#!/usr/bin/env python3
"""Test imports to debug API startup issues."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("Testing imports...")

try:
    print("1. Testing agents.base...")
    from agents.base import Agent
    print("✅ agents.base imported successfully")
except Exception as e:
    print(f"❌ agents.base failed: {e}")

try:
    print("\n2. Testing agents.content_mind...")
    from agents.content_mind import ContentMind
    print("✅ agents.content_mind imported successfully")
except Exception as e:
    print(f"❌ agents.content_mind failed: {e}")

try:
    print("\n3. Testing agents.content_mind_llm...")
    from agents.content_mind_llm import ContentMindLLM
    print("✅ agents.content_mind_llm imported successfully")
except Exception as e:
    print(f"❌ agents.content_mind_llm failed: {e}")

try:
    print("\n4. Testing agents.gateway_agent...")
    from agents.gateway_agent import GatewayAgent
    print("✅ agents.gateway_agent imported successfully")
except Exception as e:
    print(f"❌ agents.gateway_agent failed: {e}")

try:
    print("\n5. Testing agents.registry...")
    from agents.registry import _AGENT_REGISTRY
    print(f"✅ agents.registry imported successfully")
    print(f"   Available agents: {list(_AGENT_REGISTRY.keys())}")
except Exception as e:
    print(f"❌ agents.registry failed: {e}")

try:
    print("\n6. Testing apps.api.main...")
    from apps.api.main import app
    print("✅ apps.api.main imported successfully")
except Exception as e:
    print(f"❌ apps.api.main failed: {e}")

print("\n✅ All critical imports tested")
#!/usr/bin/env python3
"""Demo script for end-to-end email flow"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.event_bus import EventBus
from agents.content_mind import ContentMind
from agents.gateway import GatewayAgent
from services.llm.router import LLMRouter
from services.mcp.prompt_manager import MCPPromptManager
from services.knowledge.factory import create_knowledge_repository


async def demo_email_flow():
    """Demonstrate the complete email processing flow"""
    
    print("🚀 Starting Email → ContentMind → Knowledge → Email Demo")
    print("=" * 50)
    
    # Initialize components
    print("\n📦 Initializing components...")
    
    # Create event bus
    event_bus = EventBus()
    await event_bus.connect()
    print("✓ Event bus connected")
    
    # Create MCP prompt manager
    template_dir = Path(__file__).parent.parent / "data" / "mcp" / "templates"
    mcp_manager = MCPPromptManager(template_dir=str(template_dir))
    print("✓ MCP prompt manager initialized")
    
    # Create LLM router
    llm_router = LLMRouter()
    print("✓ LLM router initialized")
    
    # Create Knowledge Repository
    knowledge_repo = create_knowledge_repository(use_postgres=False)
    print("✓ Knowledge repository initialized")
    
    # Create ContentMind agent
    content_mind = ContentMind(
        event_bus=event_bus,
        llm_router=llm_router,
        mcp_manager=mcp_manager,
        knowledge_repo=knowledge_repo
    )
    await content_mind.initialize()
    print("✓ ContentMind agent initialized")
    
    # Create Gateway agent
    gateway_agent = GatewayAgent(event_bus=event_bus)
    await gateway_agent.initialize()
    print("✓ Gateway agent initialized")
    
    print("\n🔄 Starting agents...")
    
    # Start agents
    content_mind_task = asyncio.create_task(content_mind.run())
    gateway_task = asyncio.create_task(gateway_agent.run())
    
    # Give agents time to start
    await asyncio.sleep(1)
    
    print("\n📧 Simulating email reception...")
    
    # Create test email
    test_email = {
        'id': f'demo_{datetime.utcnow().timestamp()}',
        'from': 'demo.sender@example.com',
        'to': 'demo.receiver@example.com',
        'subject': 'Latest Developments in AI and Machine Learning',
        'body': """
        Dear colleague,
        
        I wanted to share some exciting news about recent developments in AI:
        
        1. GPT-4 has shown remarkable capabilities in reasoning and problem-solving
        2. New breakthrough in computer vision allows real-time object detection
        3. Reinforcement learning achieves superhuman performance in complex games
        
        These advances have significant implications for our industry. The ability
        to process and understand information at this scale opens up new possibilities
        for automation and intelligent decision-making.
        
        Best regards,
        Demo Sender
        """,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    print(f"From: {test_email['from']}")
    print(f"To: {test_email['to']}")
    print(f"Subject: {test_email['subject']}")
    print(f"Body preview: {test_email['body'][:100]}...")
    
    # Publish email received event
    await event_bus.publish('email.received', test_email)
    print("\n✓ Email event published")
    
    # Wait for processing
    print("\n⏳ Processing email through ContentMind...")
    await asyncio.sleep(5)  # Give time for processing
    
    # Check knowledge repository
    print("\n📚 Checking knowledge repository...")
    
    if hasattr(knowledge_repo, 'search_content') and asyncio.iscoroutinefunction(knowledge_repo.search_content):
        results = await knowledge_repo.search_content('AI developments')
    else:
        results = knowledge_repo.search_content('AI developments')
    
    if results:
        print(f"✓ Found {len(results)} items in knowledge repository")
        for i, item in enumerate(results[:3]):  # Show first 3
            print(f"\n  Item {i+1}:")
            print(f"  - Title: {item.title}")
            print(f"  - Source: {item.source}")
            print(f"  - Tags: {item.tags}")
            if item.summary:
                print(f"  - Summary: {item.summary[:100]}...")
    else:
        print("⚠️  No items found in knowledge repository")
    
    # Simulate content processed event
    print("\n📤 Simulating content processed event...")
    
    if results:
        await event_bus.publish('content.processed', {
            'content_id': results[0].id,
            'original_email_id': test_email['id'],
            'summary': 'This email discusses recent AI developments including GPT-4, computer vision, and reinforcement learning advances.',
            'from': test_email['from'],
            'to': test_email['to']
        })
        print("✓ Content processed event published")
    
    # Wait for response
    await asyncio.sleep(2)
    
    print("\n🎯 Demo completed!")
    print("\nNote: In a real scenario, the Gateway agent would send an actual email")
    print("response to the original sender with the AI-generated summary.")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    content_mind.stop()
    gateway_agent.stop()
    
    # Cancel tasks
    content_mind_task.cancel()
    gateway_task.cancel()
    
    try:
        await content_mind_task
        await gateway_task
    except asyncio.CancelledError:
        pass
    
    await content_mind.shutdown()
    await gateway_agent.shutdown()
    await event_bus.disconnect()
    
    print("✓ Cleanup completed")


if __name__ == "__main__":
    # Check environment
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not set. LLM calls will fail.")
        print("Set it with: export OPENAI_API_KEY=your-key-here")
    
    # Run demo
    asyncio.run(demo_email_flow())
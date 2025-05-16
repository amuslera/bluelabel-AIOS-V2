#!/usr/bin/env python3
"""Test the Gmail Direct Gateway implementation"""
import os
import asyncio
import aiohttp
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.gateway.gmail_direct_gateway import GmailDirectGateway
from core.event_bus import EventBus

async def test_gmail():
    print("Gmail Direct Gateway Test")
    print("========================")
    
    # Check environment variables
    required_vars = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {missing_vars}")
        print("\nTo fix this:")
        print("1. Copy .env.example to .env if not already done")
        print("2. Add your Google OAuth credentials to .env:")
        print("   GOOGLE_CLIENT_ID=your_client_id")
        print("   GOOGLE_CLIENT_SECRET=your_client_secret")
        return
    
    # Create event bus and gateway
    event_bus = EventBus()
    gmail = GmailDirectGateway(event_bus)
    
    print("\nInitializing Gmail Gateway...")
    print("This will open a browser for authentication if needed.")
    print("Note: Using port 9090 for OAuth callback to avoid backend interception.")
    print()
    
    try:
        # Initialize gateway
        success = await gmail.initialize()
        
        if not success:
            print("Failed to initialize Gmail gateway")
            return
        
        print("Gmail gateway initialized successfully!")
        
        # Test sending an email
        print("\nSending test email...")
        result = await gmail.send_message(
            to="test@example.com",  # Replace with actual email
            subject="Test from Bluelabel AIOS",
            body="This is a test email from the Gmail Direct Gateway implementation."
        )
        
        print(f"Send result: {result}")
        
        # Test fetching messages
        print("\nFetching recent messages...")
        messages = await gmail.fetch_messages(limit=5)
        
        print(f"Found {len(messages)} messages:")
        for msg in messages:
            print(f"- {msg['subject']} (from: {msg['from']})")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Shutdown gateway
        await gmail.shutdown()
        print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(test_gmail())
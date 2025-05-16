#!/usr/bin/env python3
"""
Test Gmail Direct Gateway OAuth Flow
Uses the existing implementation that worked before
"""
import os
import sys
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gateway.gmail_direct_gateway import GmailDirectGateway
from core.event_bus import EventBus


async def test_gmail_gateway():
    """Test the Gmail Direct Gateway"""
    print("🔐 Testing Gmail Direct Gateway OAuth Flow")
    print("=" * 40)
    
    # Create event bus and gateway
    event_bus = EventBus(simulation_mode=True)
    gateway = GmailDirectGateway(event_bus)
    
    # Initialize (this will trigger OAuth if needed)
    print("\nInitializing Gmail Gateway...")
    success = await gateway.initialize()
    
    if success:
        print("✅ Gmail Gateway initialized successfully!")
        
        # Test getting user profile
        try:
            service = gateway.service
            profile = service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress')
            print(f"\n📧 Connected as: {email}")
            
            # Test fetching messages
            messages = service.users().messages().list(userId='me', maxResults=5).execute()
            count = messages.get('resultSizeEstimate', 0)
            print(f"📊 Messages in inbox: {count}")
            
            if messages.get('messages'):
                print("\nRecent messages:")
                for msg in messages['messages'][:3]:
                    msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
                    headers = msg_data['payload'].get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                    print(f"  - {subject}")
            
            print("\n🎉 Gmail OAuth setup complete!")
            print("\nNext steps:")
            print("1. Use the API endpoints for email operations")
            print("2. Process incoming emails automatically")
            print("3. Send emails through the gateway")
            
        except Exception as e:
            print(f"\n❌ Error testing connection: {e}")
    else:
        print("❌ Failed to initialize Gmail Gateway")
        print("\nTroubleshooting:")
        print("1. Check that GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set in .env")
        print("2. Make sure 'http://localhost:8080/gateway/google/callback' is in your Google Console redirect URIs")
        print("3. Try opening http://localhost:8080 in your browser during authentication")
    
    # Clean up
    await event_bus.shutdown()


def main():
    """Main function"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check environment variables
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        print("❌ Missing required environment variables")
        print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
        return
    
    # Run the test
    asyncio.run(test_gmail_gateway())


if __name__ == "__main__":
    main()
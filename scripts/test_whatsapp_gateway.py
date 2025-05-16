#!/usr/bin/env python3
"""Test WhatsApp gateway implementation"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gateway.whatsapp_gateway import WhatsAppGateway, WhatsAppMessage, WhatsAppResponse
from core.logging import setup_logging

logger = setup_logging(service_name="test-whatsapp")


async def test_whatsapp_gateway():
    """Test WhatsApp gateway functionality"""
    print("Testing WhatsApp Gateway...")
    
    # Initialize gateway
    gateway = WhatsAppGateway()
    
    # Check configuration
    print(f"WhatsApp configured: {gateway.is_configured()}")
    
    if not gateway.is_configured():
        print("WhatsApp gateway is not configured.")
        print("Please set the following environment variables:")
        print("- WHATSAPP_ACCESS_TOKEN")
        print("- WHATSAPP_PHONE_NUMBER_ID")
        print("\nFor testing without actual credentials, you can use dummy values.")
        return
    
    # Test webhook verification
    print("\nTesting webhook verification...")
    try:
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "test_token")
        challenge = "test_challenge_12345"
        result = await gateway.verify_webhook(verify_token, challenge)
        print(f"✓ Webhook verification: {result}")
    except ValueError as e:
        print(f"✗ Webhook verification failed: {e}")
    
    # Test message sending (simulation)
    print("\nTesting message sending...")
    test_message = WhatsAppMessage(
        to="+1234567890",  # Example number
        text="Hello from Bluelabel AIOS!"
    )
    
    # This will fail without real credentials, but we can test the structure
    response = await gateway.send_message(test_message)
    print(f"Send message response: {response.dict()}")
    
    # Test webhook processing
    print("\nTesting webhook processing...")
    webhook_data = {
        "entry": [{
            "id": "entry_123",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "+1234567890",
                        "phone_number_id": "123456"
                    },
                    "messages": [{
                        "from": "+0987654321",
                        "id": "msg_123",
                        "timestamp": "1234567890",
                        "text": {"body": "Test message"},
                        "type": "text"
                    }]
                }
            }]
        }]
    }
    
    result = await gateway.receive_webhook(webhook_data)
    print(f"Webhook processing result: {result}")


if __name__ == "__main__":
    asyncio.run(test_whatsapp_gateway())
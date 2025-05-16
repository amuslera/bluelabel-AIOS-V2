#!/usr/bin/env python3
"""Debug email sending"""
import asyncio
import aiohttp
import json
from datetime import datetime


async def debug_email_send():
    """Debug email sending through the proxy"""
    proxy_url = "http://localhost:8000/api/v1/gmail-proxy"
    direct_url = "http://localhost:8081"
    
    print("Email Sending Debug")
    print("==================\n")
    
    # Get the authenticated email address
    authenticated_email = None
    
    async with aiohttp.ClientSession() as session:
        # 1. Check status first
        print("1. Checking authentication status...")
        async with session.get(f"{proxy_url}/status") as response:
            status = await response.json()
            print(f"Proxy status: {json.dumps(status, indent=2)}")
        
        # 2. Get email configuration
        print("\n2. Getting email configuration...")
        async with session.get(f"{proxy_url}/config") as response:
            config = await response.json()
            print(f"Email config: {json.dumps(config, indent=2)}")
            
            # Extract authenticated email
            if config.get("status") == "success":
                authenticated_email = config.get("config", {}).get("details", {}).get("username")
                print(f"\nAuthenticated email: {authenticated_email}")
        
        # 3. Send test email with detailed tracking
        if authenticated_email:
            print(f"\n3. Sending test email to {authenticated_email}...")
            
            test_email = {
                "to": [authenticated_email],
                "subject": f"Debug Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "body": f"""
This is a debug test email sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you receive this email, the Gmail integration is working correctly.

Test details:
- Sent from: Bluelabel AIOS Gmail Proxy
- Sent to: {authenticated_email}
- API endpoint: {proxy_url}/send
""",
                "html": False
            }
            
            print(f"Email payload: {json.dumps(test_email, indent=2)}")
            
            # Send through proxy
            print("\nSending through proxy...")
            async with session.post(
                f"{proxy_url}/send",
                json=test_email,
                headers={"Content-Type": "application/json"}
            ) as response:
                result = await response.json()
                print(f"Proxy result: {json.dumps(result, indent=2)}")
            
            # Try sending directly to the backend API
            print("\nSending directly to backend API...")
            async with session.post(
                f"{direct_url}/gateway/email/google",
                json=test_email,
                headers={"Content-Type": "application/json"}
            ) as response:
                direct_result = await response.text()
                print(f"Direct result: {direct_result}")
        
        # 4. Check email service status
        print("\n4. Checking email service status...")
        async with session.get(f"{direct_url}/gateway/email/status") as response:
            email_status = await response.json()
            print(f"Email service: {json.dumps(email_status, indent=2)}")
        
        # 5. Check if email listener is running
        if email_status.get("status") != "running":
            print("\n5. Starting email listener...")
            async with session.post(f"{proxy_url}/listener/start") as response:
                start_result = await response.json()
                print(f"Start result: {json.dumps(start_result, indent=2)}")
        
        # 6. Check inbox for sent items
        print("\n6. Checking inbox...")
        async with session.post(f"{proxy_url}/check-inbox") as response:
            inbox_result = await response.json()
            print(f"Inbox check: {json.dumps(inbox_result, indent=2)}")
        
        # 7. Try a simpler email format
        print("\n7. Trying simple email format...")
        simple_email = {
            "to": authenticated_email if authenticated_email else "test@example.com",
            "subject": "Simple test",
            "body": "Test"
        }
        
        async with session.post(
            f"{direct_url}/gateway/email/google",
            json=simple_email,
            headers={"Content-Type": "application/json"}
        ) as response:
            simple_result = await response.text()
            print(f"Simple email result: {simple_result}")


async def check_outbox():
    """Check if emails are being queued but not sent"""
    print("\n\nChecking for queued emails...")
    
    # This would check if there's a queue or outbox
    # The actual implementation depends on how the backend API works
    pass


if __name__ == "__main__":
    print("Email Debug Script")
    print("==================\n")
    
    asyncio.run(debug_email_send())
    
    print("\n\nPossible issues to check:")
    print("1. Email might be in spam/promotions folder")
    print("2. Gmail might be blocking the email")
    print("3. The backend API might not be actually sending emails")
    print("4. OAuth scopes might be insufficient")
    print("5. Email formatting might be incorrect")
    
    print("\nCheck:")
    print("- Gmail spam folder")
    print("- Gmail 'All Mail' folder")
    print("- Gmail 'Sent' folder")
    print("- Backend API logs for errors")
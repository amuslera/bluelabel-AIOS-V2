#!/usr/bin/env python3
"""Test Gmail integration after successful OAuth"""

import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

def main():
    print("Gmail Integration Test")
    print("=" * 40)
    
    # Load token
    token_file = Path('data/mcp/gmail_token.json')
    if not token_file.exists():
        print("❌ Token file not found")
        return
    
    with open(token_file, 'r') as f:
        token_data = json.load(f)
    
    # Load client credentials
    creds_file = Path('data/mcp/google_credentials.json')
    with open(creds_file, 'r') as f:
        creds_data = json.load(f)
    
    web_config = creds_data['web']
    
    # Create credentials object
    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=web_config['client_id'],
        client_secret=web_config['client_secret']
    )
    
    # Build Gmail service
    service = build('gmail', 'v1', credentials=creds)
    
    # Test 1: List labels
    print("\n1. Testing label listing...")
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        print(f"✅ Found {len(labels)} labels:")
        for label in labels[:5]:  # Show first 5
            print(f"   - {label['name']}")
    except Exception as e:
        print(f"❌ Error listing labels: {e}")
    
    # Test 2: Get profile
    print("\n2. Testing profile access...")
    try:
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Email address: {profile['emailAddress']}")
        print(f"   Messages total: {profile.get('messagesTotal', 'N/A')}")
        print(f"   Threads total: {profile.get('threadsTotal', 'N/A')}")
    except Exception as e:
        print(f"❌ Error getting profile: {e}")
    
    # Test 3: List recent messages
    print("\n3. Testing message listing...")
    try:
        results = service.users().messages().list(
            userId='me',
            maxResults=3
        ).execute()
        messages = results.get('messages', [])
        
        print(f"✅ Found {len(messages)} recent messages:")
        for msg in messages:
            # Get message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id']
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            print(f"   - From: {from_addr[:50]}...")
            print(f"     Subject: {subject[:50]}...")
    except Exception as e:
        print(f"❌ Error listing messages: {e}")
    
    # Test 4: Send a test email (to yourself)
    print("\n4. Testing email sending...")
    try:
        # Get user's email
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']
        
        # Create message
        message_text = "This is a test email from Bluelabel AIOS Gmail integration."
        message = MIMEText(message_text)
        message['to'] = user_email
        message['subject'] = 'Test: Bluelabel AIOS Gmail Integration'
        message['from'] = user_email
        
        # Encode
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✅ Email sent successfully!")
        print(f"   Message ID: {result['id']}")
        print(f"   Sent to: {user_email}")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
    
    print("\n" + "=" * 40)
    print("Gmail integration test complete!")
    print("\nNext steps:")
    print("1. Check your inbox for the test email")
    print("2. Run the full Gmail gateway test")
    print("3. Test the API endpoints")

if __name__ == '__main__':
    main()
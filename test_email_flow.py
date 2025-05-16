#!/usr/bin/env python3
"""Test full email processing flow"""
import requests
import json
import time

# First, let's check if we have emails to process
print("1. Fetching unread emails...")
fetch_url = "http://localhost:8000/api/v1/gmail-complete/fetch"
fetch_data = {
    "query": "is:unread",
    "max_results": 5
}

response = requests.post(fetch_url, json=fetch_data)
print(f"Fetch Status: {response.status_code}")
emails = response.json()
print(f"Found {emails.get('count', 0)} unread emails\n")

# Process the first email if available
if emails.get('count', 0) > 0:
    first_email = emails['messages'][0]
    print(f"2. Processing email from: {first_email['from']}")
    print(f"   Subject: {first_email['subject']}")
    print(f"   Snippet: {first_email['snippet'][:100]}...\n")
    
    # Submit email to gateway for processing
    gateway_url = "http://localhost:8000/api/v1/gateway/email"
    gateway_data = {
        "from_email": first_email['from'],
        "to_email": "a@bluelabel.ventures",
        "subject": first_email['subject'],
        "body": first_email['body']
    }
    
    print("3. Submitting email to gateway for processing...")
    gateway_response = requests.post(gateway_url, json=gateway_data)
    print(f"Gateway Status: {gateway_response.status_code}")
    result = gateway_response.json()
    print(f"Task ID: {result.get('task_id')}")
    print(f"Status: {result.get('status')}\n")
    
    # Check agent status
    print("4. Checking agent status...")
    agents_url = "http://localhost:8000/api/v1/agents/status"
    agent_response = requests.get(agents_url)
    print(json.dumps(agent_response.json(), indent=2))
    
    # Try to trigger ContentMind agent directly
    print("\n5. Triggering ContentMind agent directly...")
    agent_url = "http://localhost:8000/api/v1/agents/content_mind/process"
    agent_data = {
        "content_source": first_email['body'],
        "content_type": "email",
        "metadata": {
            "from": first_email['from'],
            "subject": first_email['subject']
        }
    }
    
    agent_result = requests.post(agent_url, json=agent_data)
    print(f"Agent Status: {agent_result.status_code}")
    if agent_result.status_code == 200:
        agent_output = agent_result.json()
        print("\nAgent Output:")
        print(f"Status: {agent_output.get('status')}")
        print(f"Summary: {agent_output.get('summary', {}).get('summary')}")
        print(f"Key Points: {agent_output.get('summary', {}).get('key_points', [])}")
        print(f"Processing Time: {agent_output.get('processing_time', 0):.2f} seconds")
else:
    print("No unread emails found. Let's create a test workflow...")
    
    # Test with sample content
    print("2. Testing with sample content...")
    test_content = """Subject: AI Investment Opportunities Report
    
    Here's a summary of the latest AI investment opportunities:
    
    1. OpenAI announced a new funding round at $90B valuation
    2. Anthropic is developing Claude 4 with enhanced capabilities
    3. Google's Gemini Ultra shows competitive performance
    4. Microsoft is integrating AI across all products
    
    Key investment themes:
    - LLM infrastructure and platforms
    - AI agents for workflow automation
    - Enterprise AI adoption accelerating
    - Edge AI and mobile deployment
    
    Please review and let me know your thoughts.
    """
    
    agent_url = "http://localhost:8000/api/v1/agents/content_mind/process"
    agent_data = {
        "content_source": test_content,
        "content_type": "email",
        "metadata": {
            "from": "test@example.com",
            "subject": "AI Investment Opportunities Report"
        }
    }
    
    print("\nProcessing test content...")
    agent_result = requests.post(agent_url, json=agent_data)
    print(f"Agent Status: {agent_result.status_code}")
    
    if agent_result.status_code == 200:
        agent_output = agent_result.json()
        print("\nAgent Output:")
        print(f"Status: {agent_output.get('status')}")
        print(f"\nSummary: {agent_output.get('summary', {}).get('summary')}")
        print(f"\nKey Points:")
        for point in agent_output.get('summary', {}).get('key_points', []):
            print(f"  - {point}")
        print(f"\nProcessing Time: {agent_output.get('processing_time', 0):.2f} seconds")
    else:
        print(f"Error: {agent_result.text}")

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

# Check available agents
print("2. Checking available agents...")
agents_url = "http://localhost:8000/api/v1/agents"
agent_response = requests.get(agents_url)
print(f"Agents Status: {agent_response.status_code}")
agents = agent_response.json()
print("Available agents:")
for agent in agents:
    print(f"  - {agent['agent_id']}: {agent['name']} (registered: {agent['registered']}, instantiated: {agent['instantiated']})")
print()

# Process the first email if available
if emails.get('count', 0) > 0:
    first_email = emails['messages'][0]
    print(f"3. Processing email from: {first_email['from']}")
    print(f"   Subject: {first_email['subject']}")
    print(f"   Body preview: {first_email['body'][:200]}...\n")
    
    # Execute ContentMind agent directly
    print("4. Executing ContentMind agent directly...")
    agent_url = "http://localhost:8000/api/v1/agents/content_mind/execute"
    agent_data = {
        "agent_id": "content_mind",
        "source": "email",
        "content": {
            "text": first_email['body'],  # The agent expects "text" key
            "type": "email"
        },
        "metadata": {
            "from": first_email['from'],
            "subject": first_email['subject']
        }
    }
    
    print("Sending request to ContentMind agent...")
    agent_result = requests.post(agent_url, json=agent_data)
    print(f"Agent Status: {agent_result.status_code}")
    
    if agent_result.status_code == 200:
        agent_output = agent_result.json()
        print("\nAgent Output:")
        print(f"Status: {agent_output.get('status')}")
        
        result = agent_output.get('result', {})
        if result:
            print(f"\nSummary: {result.get('summary')}")
            print(f"\nEntities:")
            entities = result.get('entities', [])
            if isinstance(entities, dict):
                for entity_type, entity_list in entities.items():
                    if entity_list:
                        print(f"  {entity_type}: {entity_list}")
            else:
                for entity in entities:
                    print(f"  - {entity}")
            
            print(f"\nTopics: {result.get('topics', [])}")
            print(f"Sentiment: {result.get('sentiment')}")
            print(f"\nMetadata: {result.get('metadata', {})}")
        print(f"\nProcessing Time: {agent_output.get('processing_time', 0):.2f} seconds")
    else:
        print(f"Error: {agent_result.text}")
        
    # Now let's try the email gateway to see how it processes emails
    print("\n5. Testing email gateway processing...")
    gateway_url = "http://localhost:8000/api/v1/gateway/email"
    gateway_data = {
        "from_email": first_email['from'],
        "to_email": "a@bluelabel.ventures",
        "subject": first_email['subject'],
        "body": first_email['body']
    }
    
    print("Submitting email to gateway...")
    gateway_response = requests.post(gateway_url, json=gateway_data)
    print(f"Gateway Status: {gateway_response.status_code}")
    result = gateway_response.json()
    print(f"Task ID: {result.get('task_id')}")
    print(f"Status: {result.get('status')}")
    
else:
    print("No unread emails found. Let's create a test workflow...")
    
    # Test with sample content
    print("3. Testing with sample content...")
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
    
    agent_url = "http://localhost:8000/api/v1/agents/content_mind/execute"
    agent_data = {
        "agent_id": "content_mind",
        "source": "test",
        "content": {
            "text": test_content,
            "type": "email"
        },
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
        
        result = agent_output.get('result', {})
        if result:
            print(f"\nSummary: {result.get('summary')}")
            print(f"\nEntities:")
            entities = result.get('entities', [])
            if isinstance(entities, dict):
                for entity_type, entity_list in entities.items():
                    if entity_list:
                        print(f"  {entity_type}: {entity_list}")
            else:
                for entity in entities:
                    print(f"  - {entity}")
            
            print(f"\nTopics: {result.get('topics', [])}")
            print(f"Sentiment: {result.get('sentiment')}")
        
        print(f"\nProcessing Time: {agent_output.get('processing_time', 0):.2f} seconds")
    else:
        print(f"Error: {agent_result.text}")
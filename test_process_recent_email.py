#!/usr/bin/env python3
"""Process most recent email"""
import requests
import json
import time

# Fetch the most recent email
print("1. Fetching most recent email...")
fetch_url = "http://localhost:8000/api/v1/gmail-complete/fetch"
fetch_data = {
    "query": "is:unread",
    "max_results": 1
}

response = requests.post(fetch_url, json=fetch_data)
emails = response.json()

if emails.get('count', 0) > 0:
    email = emails['messages'][0]
    print(f"\nEmail from: {email['from']}")
    print(f"Subject: {email['subject']}")
    print(f"Body length: {len(email['body'])} characters")
    print(f"First 200 chars: {email['body'][:200]}...\n")
    
    # Process with ContentMind agent
    print("2. Processing with ContentMind agent...")
    agent_url = "http://localhost:8000/api/v1/agents/content_mind/execute"
    agent_data = {
        "agent_id": "content_mind",
        "source": "email",
        "content": {
            "text": email['body'],
            "type": "email"
        },
        "metadata": {
            "from": email['from'],
            "subject": email['subject'],
            "timestamp": email['date']
        }
    }
    
    agent_result = requests.post(agent_url, json=agent_data)
    
    if agent_result.status_code == 200:
        output = agent_result.json()
        result = output.get('result', {})
        
        print("\n=== CONTENT ANALYSIS ===")
        print(f"Status: {output.get('status')}")
        print(f"Processing Time: {output.get('processing_time', 0):.3f} seconds")
        
        print(f"\nSummary: {result.get('summary')}")
        
        print("\nEntities:")
        entities = result.get('entities', [])
        if isinstance(entities, dict):
            for entity_type, entity_list in entities.items():
                if entity_list:
                    print(f"  {entity_type}: {entity_list}")
        else:
            for entity in entities:
                print(f"  - {entity}")
        
        print(f"\nTopics: {result.get('topics', [])}")
        
        sentiment = result.get('sentiment', {})
        print(f"\nSentiment: {sentiment.get('sentiment')} "
              f"(score: {sentiment.get('score')}, confidence: {sentiment.get('confidence')})")
        
        metadata = result.get('metadata', {})
        print(f"\nContent Length: {metadata.get('content_length')} characters")
        
        # Store in knowledge repository
        print("\n3. Storing in knowledge repository...")
        knowledge_url = "http://localhost:8000/api/v1/knowledge/content"
        knowledge_data = {
            "title": email['subject'],
            "source": email['from'],
            "content_type": "email",
            "text_content": email['body'],
            "metadata": {
                "source": "email",
                "from": email['from'],
                "date": email['date'],
                "analysis": result
            }
        }
        
        knowledge_response = requests.post(knowledge_url, json=knowledge_data)
        if knowledge_response.status_code == 200:
            doc = knowledge_response.json()
            doc_id = doc.get('id') or doc.get('document_id')
            print(f"Stored as document: {doc_id}")
        else:
            print(f"Storage error: {knowledge_response.status_code} - {knowledge_response.text}")
            
        # Search knowledge base
        print("\n4. Searching knowledge base for 'AI investment'...")
        search_url = "http://localhost:8000/api/v1/knowledge/search"
        search_data = {
            "query": "AI investment opportunities",
            "max_results": 3
        }
        
        search_response = requests.post(search_url, json=search_data)
        if search_response.status_code == 200:
            search_results = search_response.json()
            if isinstance(search_results, list):
                results = search_results
            else:
                results = search_results.get('results', [])
            print(f"Found {len(results)} relevant documents:")
            for i, doc in enumerate(results):
                print(f"\n  {i+1}. {doc.get('title')}")
                print(f"     Score: {doc.get('score', 0):.3f}")
                print(f"     Source: {doc.get('metadata', {}).get('source')}")
        else:
            print(f"Search error: {search_response.text}")
            
    else:
        print(f"Agent error: {agent_result.text}")
else:
    print("No emails found")
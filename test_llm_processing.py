#!/usr/bin/env python3
"""Test ContentMind with real LLM processing"""
import requests
import json
import time

# Create rich test content
test_content = """Subject: Investment Opportunity: AI Healthcare Startup

Dear Ariel,

I wanted to bring to your attention an exciting opportunity in the AI healthcare space. MedAI Inc, a Series A startup founded by ex-Google engineers Sarah Chen and Dr. James Martinez, is seeking $15M to expand their FDA-approved AI diagnostic platform.

Key Highlights:
- Revenue: $5M ARR, growing 300% YoY
- Customers: 20 hospitals including Mayo Clinic and Johns Hopkins
- Technology: Proprietary deep learning models for early cancer detection
- Team: 25 employees, including 12 PhD researchers from Stanford and MIT

The company's flagship product uses computer vision and NLP to analyze medical imaging and patient records, achieving 94% accuracy in early-stage lung cancer detection - 20% better than current standards.

Valuation: $60M pre-money
Lead investor: Andreessen Horowitz is leading with $10M

Please let me know if you'd like to schedule a meeting with the founders next week.

Best regards,
John Smith
Partner, VC Capital
"""

print("Testing ContentMind with real LLM processing...")
print("=" * 50)

# Process with ContentMind agent
agent_url = "http://localhost:8000/api/v1/agents/content_mind/execute"
agent_data = {
    "agent_id": "content_mind",
    "source": "test",
    "content": {
        "text": test_content,
        "type": "email"
    },
    "metadata": {
        "from": "john.smith@vccapital.com",
        "subject": "Investment Opportunity: AI Healthcare Startup"
    }
}

print("\nProcessing content with ContentMind agent...")
start_time = time.time()
agent_result = requests.post(agent_url, json=agent_data)
end_time = time.time()

if agent_result.status_code == 200:
    output = agent_result.json()
    result = output.get('result', {})
    
    print(f"\nProcessing completed in {end_time - start_time:.2f} seconds")
    print("\n=== LLM-POWERED ANALYSIS ===")
    
    print(f"\nAI-Generated Summary:")
    print(result.get('summary', 'No summary available'))
    
    print("\n\nExtracted Entities:")
    entities = result.get('entities', [])
    entity_types = {}
    for entity in entities:
        entity_type = entity.get('type', 'Unknown')
        if entity_type not in entity_types:
            entity_types[entity_type] = []
        entity_types[entity_type].append(entity.get('text'))
    
    for entity_type, items in entity_types.items():
        print(f"  {entity_type}:")
        for item in items[:10]:  # Limit to first 10
            print(f"    - {item}")
        if len(items) > 10:
            print(f"    ... and {len(items) - 10} more")
    
    print("\n\nIdentified Topics:")
    topics = result.get('topics', [])
    for i, topic in enumerate(topics[:5], 1):
        print(f"  {i}. {topic}")
    
    print("\n\nSentiment Analysis:")
    sentiment = result.get('sentiment', {})
    print(f"  Sentiment: {sentiment.get('sentiment', 'Unknown')}")
    print(f"  Score: {sentiment.get('score', 0):.2f}")
    print(f"  Confidence: {sentiment.get('confidence', 0):.2f}")
    
    # Check if LLM was actually used
    metadata = result.get('metadata', {})
    print(f"\n\nProcessing Details:")
    print(f"  Content Length: {metadata.get('content_length', 0)} characters")
    print(f"  Processing Status: {output.get('status')}")
    
else:
    print(f"\nError: {agent_result.status_code}")
    print(agent_result.text)

print("\n" + "=" * 50)
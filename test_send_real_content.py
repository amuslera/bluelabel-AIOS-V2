#!/usr/bin/env python3
"""Send a real test email with content"""
import requests
import json

# Send a comprehensive test email
url = "http://localhost:8000/api/v1/gmail-complete/send"
headers = {"Content-Type": "application/json"}
email_data = {
    "to": ["a@bluelabel.ventures"],
    "subject": "Investment Update: AI Landscape Q1 2025",
    "body": """Dear Ariel,

I wanted to share this quarterly update on the AI investment landscape:

## Key Developments

1. **Foundation Model Race**
   - OpenAI's GPT-5 showing significant improvements in reasoning
   - Anthropic's Claude 4 focusing on safety and reliability
   - Google's Gemini Ultra competing strongly in multimodal tasks

2. **Investment Highlights**
   - OpenAI: New funding round at $90B valuation
   - Anthropic: Series E at $20B valuation
   - Cohere: Focusing on enterprise deployments
   - Character.AI: Consumer AI applications gaining traction

3. **Emerging Trends**
   - AI Agents for workflow automation (Significant opportunity)
   - Edge AI deployment becoming more feasible
   - Open source models catching up (Llama 3, Mistral)
   - AI infrastructure plays (vector databases, orchestration)

4. **Portfolio Recommendations**
   - Continue focus on infrastructure plays
   - Look at vertical-specific AI applications
   - Consider AI safety and governance startups
   - Monitor regulatory landscape developments

## Action Items
- Review attached pitch decks from 3 AI startups
- Schedule calls with Anthropic and Cohere teams
- Evaluate AI agent framework investments

Please let me know if you'd like to discuss any of these opportunities in detail.

Best regards,
Investment Team

---
This report contains confidential information. Please handle accordingly.
""",
    "html": False
}

print("Sending comprehensive test email...")
response = requests.post(url, json=email_data, headers=headers)
print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")
#!/usr/bin/env python3
"""
MVP Demo for Bluelabel AIOS v2
Demonstrates the complete flow: email → ContentMind → knowledge repository → digest
"""
import asyncio
import json
import requests
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API Base URL
API_BASE_URL = "http://127.0.0.1:8000"
API_V1_BASE = f"{API_BASE_URL}/api/v1"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")

async def demo_mvp_flow():
    """Demonstrate the complete MVP flow"""
    print_section("🚀 Bluelabel AIOS v2 - MVP Demo")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Simulate an incoming email with content
    print_section("1. Simulating Incoming Email")
    email_content = {
        "from": "demo@example.com",
        "subject": "AI Industry Report - Q1 2025",
        "body": """
        Dear Ariel,
        
        Here's the latest industry report on AI developments:
        
        Artificial Intelligence Market Overview Q1 2025:
        
        The AI industry has seen unprecedented growth with several key developments:
        
        1. Generative AI adoption has increased by 300% in enterprise settings
        2. Healthcare AI applications are saving an estimated $150B annually
        3. Autonomous systems are being deployed in 40% of manufacturing facilities
        4. AI governance frameworks are being implemented by 70% of Fortune 500 companies
        
        Key Investment Opportunities:
        - Healthcare AI startups focusing on diagnostic tools
        - Enterprise automation platforms with strong security features
        - Ethical AI and governance solutions
        
        Risks to Monitor:
        - Regulatory changes in EU and US markets
        - Compute costs increasing due to model complexity
        - Talent shortage in specialized AI engineering roles
        
        Attached: Full detailed report (simulated for demo)
        
        Best regards,
        Your Investment Research Team
        """
    }
    print(f"From: {email_content['from']}")
    print(f"Subject: {email_content['subject']}")
    print(f"Preview: {email_content['body'][:100]}...")
    
    # 2. Process with ContentMind Agent
    print_section("2. Processing with ContentMind Agent")
    agent_request = {
        "agent_id": "content_mind",
        "source": "email",
        "content": {
            "text": email_content['body'],
            "metadata": {
                "from": email_content['from'],
                "subject": email_content['subject'],
                "timestamp": datetime.now().isoformat()
            }
        },
        "metadata": {
            "content_type": "email",
            "requires_response": True
        }
    }
    
    try:
        response = requests.post(
            f"{API_V1_BASE}/agents/content_mind/execute",
            json=agent_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result['status']}")
            summary = result.get('result', {}).get('summary', 'No summary available')
            insights = result.get('result', {}).get('insights', [])
            
            print(f"\nSummary:\n{summary[:200]}...")
            print(f"\nKey Insights: {len(insights)} found")
            
            agent_result = result
        else:
            print(f"Error: {response.status_code}")
            return
    except Exception as e:
        print(f"Error processing with agent: {e}")
        return
    
    # 3. Store in Knowledge Repository
    print_section("3. Storing in Knowledge Repository")
    doc_data = {
        "title": email_content['subject'],
        "source": email_content['from'],
        "content_type": "email",
        "text_content": email_content['body'],
        "summary": summary,
        "metadata": {
            "processed_by": "content_mind",
            "email_from": email_content['from'],
            "timestamp": datetime.now().isoformat(),
            "insights": insights
        },
        "tags": ["AI", "industry-report", "Q1-2025", "investment"]
    }
    
    try:
        response = requests.post(f"{API_V1_BASE}/knowledge/content", json=doc_data)
        if response.status_code == 200:
            result = response.json()
            doc_id = result.get("content_id") or result.get("id") 
            print(f"✅ Content stored successfully")
            print(f"Document ID: {doc_id}")
        else:
            print(f"Warning: Storage failed: {response.status_code}")
    except Exception as e:
        print(f"Error storing content: {e}")
    
    # 4. Generate Daily Digest
    print_section("4. Generating Daily Digest")
    digest_content = f"""
    Daily Digest - {datetime.now().strftime('%Y-%m-%d')}
    
    New Content Processed:
    
    📧 {email_content['subject']}
    From: {email_content['from']}
    
    Summary:
    {summary[:300]}...
    
    Key Takeaways:
    • AI industry growth continues at rapid pace
    • Healthcare and enterprise automation are hot sectors
    • Regulatory risks need monitoring
    
    Action Items:
    • Review healthcare AI startup opportunities
    • Assess portfolio exposure to AI regulatory risks
    • Schedule calls with enterprise automation founders
    
    ---
    This digest was automatically generated by Bluelabel AIOS
    """
    
    print(digest_content)
    
    # 5. Simulate sending digest back via email
    print_section("5. Sending Digest via Email Gateway")
    print("📨 Simulating email send...")
    print(f"To: ariel@example.com")
    print(f"Subject: Daily Digest - {datetime.now().strftime('%Y-%m-%d')}")
    print("Status: Ready to send (Gmail OAuth not authenticated in demo)")
    
    # 6. Show search capabilities
    print_section("6. Demonstrating Search Capabilities")
    search_queries = [
        "healthcare AI",
        "investment opportunities",
        "regulatory risks"
    ]
    
    for query in search_queries:
        try:
            response = requests.post(
                f"{API_V1_BASE}/knowledge/search", 
                json={"query": query}
            )
            if response.status_code == 200:
                results = response.json()
                count = len(results) if isinstance(results, list) else len(results.get('results', []))
                print(f"🔍 Query: '{query}' → {count} results")
        except Exception as e:
            print(f"Search error: {e}")
    
    print_section("✅ MVP Demo Complete!")
    print("\nKey Components Demonstrated:")
    print("• ✅ Content ingestion from email")
    print("• ✅ AI processing with ContentMind")
    print("• ✅ Knowledge storage and retrieval")
    print("• ✅ Digest generation")
    print("• ✅ Search capabilities")
    print("• ⏳ Email sending (requires OAuth setup)")
    
    print("\nNext Steps for Production:")
    print("1. Complete Gmail OAuth flow for real email integration")
    print("2. Add PDF processing capabilities")
    print("3. Set up PostgreSQL for persistent storage")
    print("4. Configure WhatsApp Business API")
    print("5. Deploy with Docker for production use")

if __name__ == "__main__":
    print("Starting Bluelabel AIOS v2 MVP Demo...")
    asyncio.run(demo_mvp_flow())
#!/usr/bin/env python3
"""
Script to seed marketplace with sample data for testing
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import uuid
import random

from core.config import settings
from shared.models.marketplace import (
    AgentModel, AgentCategoryModel, AgentTagModel, 
    AgentInstallationModel, AgentReviewModel
)
from shared.models.user import UserModel


def create_database_session():
    """Create database session"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def seed_categories(db):
    """Create sample agent categories"""
    categories = [
        {
            "name": "productivity",
            "display_name": "Productivity",
            "description": "Agents that help increase productivity and efficiency",
            "icon": "productivity",
            "color": "#3B82F6",
            "sort_order": 1
        },
        {
            "name": "development",
            "display_name": "Development",
            "description": "Agents for software development and coding",
            "icon": "code",
            "color": "#10B981",
            "sort_order": 2
        },
        {
            "name": "content",
            "display_name": "Content Creation",
            "description": "Agents for writing, marketing, and content creation",
            "icon": "edit",
            "color": "#8B5CF6",
            "sort_order": 3
        },
        {
            "name": "analysis",
            "display_name": "Data Analysis",
            "description": "Agents for data processing and analysis",
            "icon": "chart",
            "color": "#F59E0B",
            "sort_order": 4
        },
        {
            "name": "automation",
            "display_name": "Automation",
            "description": "Agents for workflow automation and task scheduling",
            "icon": "automation",
            "color": "#EF4444",
            "sort_order": 5
        },
        {
            "name": "communication",
            "display_name": "Communication",
            "description": "Agents for email, messaging, and communication",
            "icon": "chat",
            "color": "#06B6D4",
            "sort_order": 6
        }
    ]
    
    for cat_data in categories:
        category = AgentCategoryModel(
            id=str(uuid.uuid4()),
            name=cat_data["name"],
            display_name=cat_data["display_name"],
            description=cat_data["description"],
            icon=cat_data["icon"],
            color=cat_data["color"],
            sort_order=cat_data["sort_order"],
            is_active=True
        )
        db.add(category)
    
    db.commit()
    print("✅ Created sample categories")


def seed_tags(db):
    """Create sample agent tags"""
    tags = [
        {"name": "ai", "display_name": "AI", "color": "#3B82F6"},
        {"name": "nlp", "display_name": "Natural Language Processing", "color": "#10B981"},
        {"name": "automation", "display_name": "Automation", "color": "#F59E0B"},
        {"name": "productivity", "display_name": "Productivity", "color": "#8B5CF6"},
        {"name": "data-analysis", "display_name": "Data Analysis", "color": "#EF4444"},
        {"name": "machine-learning", "display_name": "Machine Learning", "color": "#06B6D4"},
        {"name": "web-scraping", "display_name": "Web Scraping", "color": "#84CC16"},
        {"name": "email", "display_name": "Email", "color": "#F97316"},
        {"name": "pdf", "display_name": "PDF Processing", "color": "#EC4899"},
        {"name": "scheduling", "display_name": "Scheduling", "color": "#6366F1"},
        {"name": "reporting", "display_name": "Reporting", "color": "#14B8A6"},
        {"name": "integration", "display_name": "Integration", "color": "#A855F7"}
    ]
    
    for tag_data in tags:
        tag = AgentTagModel(
            id=str(uuid.uuid4()),
            name=tag_data["name"],
            display_name=tag_data["display_name"],
            color=tag_data["color"],
            usage_count=random.randint(5, 50),
            is_active=True
        )
        db.add(tag)
    
    db.commit()
    print("✅ Created sample tags")


def seed_users(db):
    """Create sample users"""
    users = [
        {
            "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",  # Matches auth.py
            "email": "ariel@example.com",
            "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
        },
        {
            "id": str(uuid.uuid4()),
            "email": "john.doe@example.com",
            "tenant_id": str(uuid.uuid4())
        },
        {
            "id": str(uuid.uuid4()),
            "email": "jane.smith@example.com", 
            "tenant_id": str(uuid.uuid4())
        }
    ]
    
    for user_data in users:
        # Check if user already exists
        existing = db.query(UserModel).filter(UserModel.id == user_data["id"]).first()
        if not existing:
            user = UserModel(
                id=user_data["id"],
                email=user_data["email"],
                tenant_id=user_data["tenant_id"]
            )
            db.add(user)
    
    db.commit()
    print("✅ Created sample users")


def seed_agents(db):
    """Create sample marketplace agents"""
    
    # Get sample user for author_id
    sample_user = db.query(UserModel).first()
    author_id = sample_user.id if sample_user else "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    
    agents = [
        {
            "name": "PDF Content Analyzer",
            "description": "Advanced AI agent for extracting and analyzing content from PDF documents. Supports multi-language processing and generates comprehensive summaries with key insights.",
            "category": "content",
            "tags": ["pdf", "ai", "nlp", "data-analysis"],
            "agent_type": "content_mind",
            "capabilities": ["PDF extraction", "Text analysis", "Summary generation", "Key insights"],
            "requirements": {"python": ">=3.8", "memory": "512MB"},
            "pricing_model": "free",
            "is_featured": True,
            "is_verified": True
        },
        {
            "name": "Smart Email Assistant",
            "description": "Intelligent email management agent that categorizes, prioritizes, and drafts responses automatically. Integrates with Gmail and Outlook.",
            "category": "communication",
            "tags": ["email", "automation", "ai", "productivity"],
            "agent_type": "gateway",
            "capabilities": ["Email categorization", "Auto-responses", "Priority detection", "Calendar integration"],
            "requirements": {"api_access": "gmail", "memory": "256MB"},
            "pricing_model": "freemium",
            "price": 9.99,
            "is_featured": True,
            "is_verified": True
        },
        {
            "name": "Code Review Assistant",
            "description": "AI-powered code review agent that analyzes pull requests, suggests improvements, and checks for security vulnerabilities.",
            "category": "development",
            "tags": ["ai", "automation", "productivity"],
            "agent_type": "content_mind", 
            "capabilities": ["Code analysis", "Security scanning", "Style checking", "Performance optimization"],
            "requirements": {"github_access": True, "memory": "1GB"},
            "pricing_model": "paid",
            "price": 19.99,
            "is_verified": True
        },
        {
            "name": "Data Insights Engine",
            "description": "Powerful data analysis agent that processes CSV, Excel, and database files to generate automated insights and visualizations.",
            "category": "analysis",
            "tags": ["data-analysis", "machine-learning", "reporting", "automation"],
            "agent_type": "content_mind",
            "capabilities": ["Data processing", "Statistical analysis", "Visualization", "Trend detection"],
            "requirements": {"python": ">=3.9", "memory": "2GB"},
            "pricing_model": "free"
        },
        {
            "name": "Meeting Scheduler Pro",
            "description": "Intelligent scheduling agent that finds optimal meeting times, sends invites, and manages calendar conflicts across teams.",
            "category": "productivity",
            "tags": ["scheduling", "automation", "productivity", "integration"],
            "agent_type": "gateway",
            "capabilities": ["Calendar management", "Time optimization", "Conflict resolution", "Multi-timezone support"],
            "requirements": {"calendar_access": True, "memory": "128MB"},
            "pricing_model": "freemium",
            "price": 14.99
        },
        {
            "name": "Web Research Bot",
            "description": "Autonomous web research agent that gathers information from multiple sources, fact-checks content, and compiles research reports.",
            "category": "content",
            "tags": ["web-scraping", "ai", "nlp", "automation"],
            "agent_type": "content_mind",
            "capabilities": ["Web scraping", "Fact checking", "Source verification", "Report generation"],
            "requirements": {"internet_access": True, "memory": "512MB"},
            "pricing_model": "free",
            "is_featured": True
        },
        {
            "name": "Social Media Manager",
            "description": "Comprehensive social media management agent that creates content, schedules posts, and analyzes engagement across platforms.",
            "category": "content",
            "tags": ["automation", "productivity", "ai", "integration"],
            "agent_type": "gateway",
            "capabilities": ["Content creation", "Post scheduling", "Engagement analysis", "Multi-platform support"],
            "requirements": {"social_api_access": True, "memory": "256MB"},
            "pricing_model": "paid",
            "price": 29.99
        },
        {
            "name": "Customer Support Bot",
            "description": "AI-powered customer support agent that handles inquiries, escalates complex issues, and maintains conversation history.",
            "category": "communication",
            "tags": ["ai", "automation", "nlp", "integration"],
            "agent_type": "content_mind",
            "capabilities": ["Query understanding", "Response generation", "Issue escalation", "Multi-language support"],
            "requirements": {"chat_integration": True, "memory": "512MB"},
            "pricing_model": "freemium",
            "price": 24.99
        },
        {
            "name": "Project Tracker",
            "description": "Smart project management agent that tracks progress, identifies bottlenecks, and sends automated status updates to stakeholders.",
            "category": "productivity",
            "tags": ["automation", "productivity", "reporting", "integration"],
            "agent_type": "gateway", 
            "capabilities": ["Progress tracking", "Bottleneck detection", "Status reporting", "Team coordination"],
            "requirements": {"project_tools_access": True, "memory": "256MB"},
            "pricing_model": "free"
        },
        {
            "name": "Document Translator",
            "description": "Advanced translation agent supporting 50+ languages with context awareness and document formatting preservation.",
            "category": "content",
            "tags": ["ai", "nlp", "automation", "integration"],
            "agent_type": "content_mind",
            "capabilities": ["Multi-language translation", "Context preservation", "Format retention", "Batch processing"],
            "requirements": {"translation_api": True, "memory": "512MB"},
            "pricing_model": "freemium",
            "price": 12.99
        }
    ]
    
    created_agents = []
    for i, agent_data in enumerate(agents):
        agent = AgentModel(
            id=str(uuid.uuid4()),
            name=agent_data["name"],
            description=agent_data["description"],
            author_id=author_id,
            category=agent_data["category"],
            tags=agent_data["tags"],
            version="1.0.0",
            icon_url=f"https://api.dicebear.com/7.x/shapes/svg?seed={agent_data['name'].replace(' ', '')}",
            repository_url=f"https://github.com/example/{agent_data['name'].lower().replace(' ', '-')}",
            agent_type=agent_data["agent_type"],
            capabilities=agent_data["capabilities"],
            requirements=agent_data["requirements"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "api_key": {"type": "string", "description": "API key for external services"},
                    "max_requests": {"type": "integer", "default": 100}
                }
            },
            pricing_model=agent_data["pricing_model"],
            price=agent_data.get("price", 0.0),
            license="MIT",
            install_count=random.randint(50, 5000),
            rating_average=round(random.uniform(3.5, 5.0), 1),
            rating_count=random.randint(10, 500),
            view_count=random.randint(100, 10000),
            is_active=True,
            is_verified=agent_data.get("is_verified", False),
            is_featured=agent_data.get("is_featured", False),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
            published_at=datetime.utcnow() - timedelta(days=random.randint(1, 300))
        )
        db.add(agent)
        created_agents.append(agent)
    
    db.commit()
    print(f"✅ Created {len(agents)} sample agents")
    return created_agents


def seed_installations_and_reviews(db, agents):
    """Create sample installations and reviews"""
    
    users = db.query(UserModel).all()
    if not users:
        print("❌ No users found, skipping installations and reviews")
        return
    
    # Create some installations
    for user in users:
        # Each user installs 2-5 random agents
        num_installs = random.randint(2, min(5, len(agents)))
        installed_agents = random.sample(agents, num_installs)
        
        for agent in installed_agents:
            installation = AgentInstallationModel(
                id=str(uuid.uuid4()),
                user_id=user.id,
                agent_id=agent.id,
                installed_version=agent.version,
                settings={"enabled": True, "notifications": True},
                is_active=True,
                last_used=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                usage_count=random.randint(1, 100),
                installed_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
            )
            db.add(installation)
            
            # 70% chance to leave a review
            if random.random() < 0.7:
                review = AgentReviewModel(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    agent_id=agent.id,
                    rating=random.randint(3, 5),
                    title=f"Great {agent.name.split()[0]} agent!",
                    review_text=f"This agent has been very helpful for my {agent.category} needs. Highly recommended!",
                    helpful_count=random.randint(0, 20),
                    is_verified_purchase=True,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60))
                )
                db.add(review)
    
    db.commit()
    print("✅ Created sample installations and reviews")


def main():
    """Main function to seed all marketplace data"""
    print("🌱 Seeding marketplace data...")
    
    try:
        db = create_database_session()
        
        # Check if data already exists
        existing_agents = db.query(AgentModel).count()
        if existing_agents > 0:
            print(f"⚠️  Found {existing_agents} existing agents. Skipping seed.")
            return
        
        # Seed data in order
        seed_categories(db)
        seed_tags(db)
        seed_users(db)
        agents = seed_agents(db)
        seed_installations_and_reviews(db, agents)
        
        print("✅ Marketplace data seeded successfully!")
        print(f"📊 Created: {len(agents)} agents, 6 categories, 12 tags")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
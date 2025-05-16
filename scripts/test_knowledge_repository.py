#!/usr/bin/env python3
"""Test script for Knowledge Repository with PostgreSQL"""

import asyncio
import logging
from datetime import datetime
import os

from services.knowledge.repository_postgres import PostgresKnowledgeRepository
from services.knowledge.factory import create_knowledge_repository
from agents.content_mind_llm import ContentMindLLM
from agents.base import AgentInput

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Test the Knowledge Repository with ContentMindLLM integration"""
    
    # Create Knowledge Repository (will use settings to determine type)
    logger.info("Creating Knowledge Repository...")
    repo = create_knowledge_repository(
        use_postgres=True,  # Force PostgreSQL
        db_url=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/bluelabel_aios'),
        vector_db_path="./data/chroma"
    )
    
    # Create ContentMindLLM agent
    logger.info("Creating ContentMindLLM agent...")
    content_mind = ContentMindLLM()
    await content_mind.initialize()
    
    # Test content
    test_content = """
    Artificial Intelligence is revolutionizing the healthcare industry through
    advanced diagnostic tools, personalized treatment plans, and drug discovery
    acceleration. Machine learning algorithms can now detect diseases earlier
    than traditional methods, with some systems achieving 95% accuracy in
    identifying certain cancers. The integration of AI in healthcare promises
    to reduce costs while improving patient outcomes significantly.
    """
    
    # Process content with ContentMindLLM
    logger.info("Processing content with ContentMindLLM...")
    agent_input = AgentInput(
        source="test_script",
        metadata={
            "content_type": "text",
            "timestamp": datetime.now()
        },
        content={
            "content": test_content,
            "title": "AI in Healthcare Revolution"
        }
    )
    
    result = await content_mind.process(agent_input)
    
    if result.status == "success":
        # Extract results
        summary = result.result.get('summary', '')
        concepts = result.result.get('concepts', [])
        metadata = result.result.get('metadata', {})
        
        # Store in Knowledge Repository
        logger.info("Storing processed content in Knowledge Repository...")
        content_item = await repo.add_content(
            title="AI in Healthcare Revolution",
            source="test_script",
            content_type="text",
            text_content=test_content,
            summary=summary,
            metadata=metadata,
            user_id="test_user",
            tenant_id="test_tenant",
            tags=["ai", "healthcare", "technology"],
            concepts=[{"name": c, "type": "topic"} for c in concepts]
        )
        
        logger.info(f"Content stored with ID: {content_item.id}")
        
        # Test search
        logger.info("Testing search functionality...")
        search_results = await repo.search_content(
            query="healthcare AI",
            user_id="test_user"
        )
        
        logger.info(f"Found {len(search_results)} search results")
        for result in search_results:
            logger.info(f"  - {result.title}: {result.summary[:100]}...")
        
        # Test listing with filters
        logger.info("Testing list with filters...")
        filtered_items = await repo.list_content(
            user_id="test_user",
            tags=["healthcare"],
            limit=5
        )
        
        logger.info(f"Found {len(filtered_items)} items with healthcare tag")
        
        # Test update
        logger.info("Testing content update...")
        updated_item = await repo.update_content(
            content_item.id,
            summary="Updated summary: " + summary,
            tags=["ai", "healthcare", "technology", "innovation"]
        )
        
        logger.info(f"Content updated: {updated_item.title}")
        
        # Test tag management
        logger.info("Testing tag management...")
        tag = await repo.get_or_create_tag("machine-learning", "Machine Learning related content")
        all_tags = await repo.list_tags()
        logger.info(f"Total tags: {len(all_tags)}")
        
        # Test concepts
        logger.info("Testing concept extraction...")
        if hasattr(repo, 'get_concepts_by_type'):
            concepts = await repo.get_concepts_by_type("topic", limit=10)
            logger.info(f"Found {len(concepts)} topic concepts")
        
    else:
        logger.error(f"ContentMindLLM processing failed: {result.error}")
    
    logger.info("Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
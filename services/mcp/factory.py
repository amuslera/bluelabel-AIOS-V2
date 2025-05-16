"""Factory functions for MCP components"""

import logging
from typing import Optional

from .manager import PromptManager
from .storage import PromptStorage, InMemoryPromptStorage

logger = logging.getLogger(__name__)

# Global instance for singleton pattern
_prompt_manager_instance: Optional[PromptManager] = None

def create_prompt_manager(storage: Optional[PromptStorage] = None) -> PromptManager:
    """Create a new prompt manager instance"""
    if storage is None:
        storage = InMemoryPromptStorage()
        logger.info("Created PromptManager with in-memory storage")
    
    return PromptManager(storage=storage)

def get_prompt_manager() -> PromptManager:
    """Get or create singleton prompt manager instance"""
    global _prompt_manager_instance
    
    if _prompt_manager_instance is None:
        _prompt_manager_instance = create_prompt_manager()
    
    return _prompt_manager_instance

async def initialize_default_components(manager: PromptManager) -> None:
    """Initialize default prompt components"""
    # Create some default components for common use cases
    
    # Content summarization component
    await manager.create_component(
        name="content_summarizer",
        description="Summarizes content into key points",
        template="""Please summarize the following content into {num_points} key points:

{content}

Summary:""",
        variables=[
            {
                "name": "content",
                "description": "The content to summarize",
                "type": "string",
                "required": True
            },
            {
                "name": "num_points",
                "description": "Number of key points to extract",
                "type": "number",
                "required": False,
                "default": 3
            }
        ],
        created_by="system",
        tags=["summarization", "content"],
        examples=[
            {
                "content": "This is a long article about AI...",
                "num_points": 3
            }
        ]
    )
    
    # Entity extraction component
    await manager.create_component(
        name="entity_extractor", 
        description="Extracts named entities from text",
        template="""Extract the following types of entities from the text:
{entity_types}

Text:
{text}

Entities:""",
        variables=[
            {
                "name": "text",
                "description": "Text to extract entities from",
                "type": "string",
                "required": True
            },
            {
                "name": "entity_types",
                "description": "Types of entities to extract",
                "type": "array",
                "required": False,
                "default": ["person", "organization", "location"]
            }
        ],
        created_by="system",
        tags=["extraction", "entities"],
        examples=[
            {
                "text": "John Smith works at OpenAI in San Francisco.",
                "entity_types": ["person", "organization", "location"]
            }
        ]
    )
    
    # Question answering component
    await manager.create_component(
        name="qa_component",
        description="Answers questions based on context",
        template="""Based on the following context, please answer the question:

Context:
{context}

Question: {question}

Answer:""",
        variables=[
            {
                "name": "context",
                "description": "Context information",
                "type": "string",
                "required": True
            },
            {
                "name": "question",
                "description": "Question to answer",
                "type": "string",
                "required": True
            }
        ],
        created_by="system",
        tags=["qa", "contextual"],
        examples=[
            {
                "context": "The weather is sunny and 75 degrees.",
                "question": "What's the temperature?"
            }
        ]
    )
    
    logger.info("Initialized default prompt components")
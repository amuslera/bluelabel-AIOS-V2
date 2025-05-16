"""Factory for creating Knowledge Repository instances"""

import os
from typing import Optional

from .repository import KnowledgeRepository
from .repository_postgres import PostgresKnowledgeRepository
from core.config import settings

def create_knowledge_repository(
    use_postgres: Optional[bool] = None,
    db_url: Optional[str] = None,
    vector_db_host: Optional[str] = None,
    vector_db_port: Optional[int] = None,
    vector_db_path: Optional[str] = None
) -> KnowledgeRepository:
    """Create a knowledge repository instance
    
    Args:
        use_postgres: Whether to use PostgreSQL backend (defaults to settings)
        db_url: Database URL for PostgreSQL
        vector_db_host: ChromaDB host
        vector_db_port: ChromaDB port
        vector_db_path: ChromaDB persistent path
        
    Returns:
        KnowledgeRepository instance
    """
    # Determine which implementation to use
    if use_postgres is None:
        use_postgres = getattr(settings, 'USE_POSTGRES_KNOWLEDGE', True)
    
    if use_postgres:
        # Use PostgreSQL-backed repository
        return PostgresKnowledgeRepository(
            db_url=db_url,
            vector_db_host=vector_db_host or os.getenv('CHROMA_HOST'),
            vector_db_port=vector_db_port or int(os.getenv('CHROMA_PORT', '8000')),
            vector_db_path=vector_db_path
        )
    else:
        # Use simple file-based repository
        return KnowledgeRepository(
            data_dir=os.getenv('KNOWLEDGE_DATA_DIR', 'data/knowledge'),
            vector_db_host=vector_db_host or os.getenv('CHROMA_HOST', 'localhost'),
            vector_db_port=vector_db_port or int(os.getenv('CHROMA_PORT', '8000'))
        )

# Global instance (singleton pattern)
_repository_instance = None

def get_knowledge_repository() -> KnowledgeRepository:
    """Get the global knowledge repository instance"""
    global _repository_instance
    
    if _repository_instance is None:
        _repository_instance = create_knowledge_repository()
    
    return _repository_instance

def reset_repository():
    """Reset the global repository instance (mainly for testing)"""
    global _repository_instance
    _repository_instance = None
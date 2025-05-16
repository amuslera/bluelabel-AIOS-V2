"""PostgreSQL-backed Knowledge Repository implementation"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, select, and_, or_, func
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError
import chromadb
from chromadb.config import Settings

from .models import Base, ContentItem, Tag, Concept, SearchQuery
from core.config import settings

logger = logging.getLogger(__name__)


class PostgresKnowledgeRepository:
    """PostgreSQL-backed repository for storing and retrieving content"""
    
    def __init__(
        self,
        db_url: Optional[str] = None,
        vector_db_host: Optional[str] = None,
        vector_db_port: Optional[int] = None,
        vector_db_path: Optional[str] = None,
        init_db: bool = True
    ):
        """Initialize the knowledge repository with PostgreSQL and ChromaDB
        
        Args:
            db_url: PostgreSQL connection URL
            vector_db_host: ChromaDB host (for HTTP client)
            vector_db_port: ChromaDB port (for HTTP client)
            vector_db_path: ChromaDB persistent path (for local client)
            init_db: Whether to create tables on init
        """
        # PostgreSQL setup
        self.db_url = db_url or settings.DATABASE_URL or "postgresql://localhost/bluelabel_aios"
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if needed
        if init_db:
            Base.metadata.create_all(bind=self.engine)
        
        # ChromaDB setup
        self.chroma_client = None
        self.content_collection = None
        
        try:
            if vector_db_host and vector_db_port:
                # Use HTTP client for remote ChromaDB
                self.chroma_client = chromadb.HttpClient(
                    host=vector_db_host,
                    port=vector_db_port
                )
            else:
                # Use persistent local client
                persist_path = vector_db_path or "./data/chroma"
                os.makedirs(persist_path, exist_ok=True)
                self.chroma_client = chromadb.PersistentClient(path=persist_path)
            
            # Get or create collection
            self.content_collection = self.chroma_client.get_or_create_collection(
                name="content_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB connection established")
            
        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}")
    
    @contextmanager
    def get_session(self):
        """Get a database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def add_content(
        self,
        title: str,
        source: str,
        content_type: str,
        text_content: str,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        concepts: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[float]] = None
    ) -> ContentItem:
        """Add a new content item to the repository
        
        Args:
            title: Title of the content
            source: Source of the content (URL, file path, etc.)
            content_type: Type of content ("url", "pdf", "text", "email")
            text_content: Text content
            summary: Optional summary
            metadata: Optional metadata dict
            user_id: Optional user ID
            tenant_id: Optional tenant ID
            tags: Optional list of tag names
            concepts: Optional list of concept dicts with name, type, confidence
            embeddings: Optional pre-computed embeddings
            
        Returns:
            The created content item
        """
        with self.get_session() as session:
            # Create content item
            content_item = ContentItem(
                title=title,
                source=source,
                content_type=content_type,
                text_content=text_content,
                summary=summary,
                content_metadata=metadata or {},
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            # Handle tags
            if tags:
                for tag_name in tags:
                    # Get or create tag
                    tag = session.query(Tag).filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                    content_item.tags.append(tag)
            
            # Handle concepts
            if concepts:
                for concept_data in concepts:
                    concept = Concept(
                        name=concept_data['name'],
                        type=concept_data.get('type'),
                        confidence=concept_data.get('confidence')
                    )
                    content_item.concepts.append(concept)
            
            # Add to database
            session.add(content_item)
            session.flush()  # Get the ID
            
            # Add to vector store if available
            if self.content_collection:
                try:
                    # Create metadata for ChromaDB
                    chroma_metadata = {
                        "title": title,
                        "source": source,
                        "content_type": content_type,
                        "user_id": user_id or "",
                        "tenant_id": tenant_id or "",
                        "tags": ",".join(tags or []),
                        "created_at": datetime.utcnow().isoformat()
                    }
                    
                    # Add to ChromaDB
                    if embeddings:
                        self.content_collection.add(
                            ids=[str(content_item.id)],
                            embeddings=[embeddings],
                            documents=[text_content],
                            metadatas=[chroma_metadata]
                        )
                    else:
                        self.content_collection.add(
                            ids=[str(content_item.id)],
                            documents=[text_content],
                            metadatas=[chroma_metadata]
                        )
                    
                    # Update embedding ID
                    content_item.embedding_id = str(content_item.id)
                    
                except Exception as e:
                    logger.error(f"Error adding to ChromaDB: {e}")
            
            session.commit()
            # Force loading of all attributes to avoid detached instance issues
            session.refresh(content_item)
            
            # Eagerly load relationships
            _ = content_item.tags  # Force load tags
            _ = content_item.concepts  # Force load concepts
            
            # Create a detached copy with all required attributes
            content_dict = {
                'id': content_item.id,
                'title': content_item.title,
                'source': content_item.source,
                'content_type': content_item.content_type,
                'text_content': content_item.text_content,
                'summary': content_item.summary,
                'content_metadata': content_item.content_metadata,
                'user_id': content_item.user_id,
                'tenant_id': content_item.tenant_id,
                'embedding_id': content_item.embedding_id,
                'created_at': content_item.created_at,
                'updated_at': content_item.updated_at,
                'tags': [{'id': t.id, 'name': t.name} for t in content_item.tags],
                'concepts': [{'id': c.id, 'name': c.name, 'type': c.type, 'confidence': c.confidence} 
                           for c in content_item.concepts]
            }
            
            # Create a new detached instance
            detached_item = ContentItem(**{k: v for k, v in content_dict.items() 
                                         if k not in ['tags', 'concepts']})
            
            # Set the ID
            detached_item.id = content_dict['id']
            
            return detached_item
    
    async def get_content(self, content_id: str) -> Optional[ContentItem]:
        """Get a content item by ID"""
        with self.get_session() as session:
            content_item = session.query(ContentItem).filter_by(id=content_id).first()
            if not content_item:
                return None
            
            # Force load relationships
            _ = content_item.tags
            _ = content_item.concepts
            session.refresh(content_item)
            
            # Create detached copy
            detached = ContentItem(
                id=content_item.id,
                title=content_item.title,
                source=content_item.source,
                content_type=content_item.content_type,
                text_content=content_item.text_content,
                summary=content_item.summary,
                content_metadata=content_item.content_metadata,
                user_id=content_item.user_id,
                tenant_id=content_item.tenant_id,
                embedding_id=content_item.embedding_id,
                created_at=content_item.created_at,
                updated_at=content_item.updated_at
            )
            
            return detached
    
    async def update_content(
        self,
        content_id: str,
        **kwargs
    ) -> Optional[ContentItem]:
        """Update a content item
        
        Args:
            content_id: ID of the content item
            **kwargs: Fields to update
            
        Returns:
            The updated content item, or None if not found
        """
        with self.get_session() as session:
            content_item = session.query(ContentItem).filter_by(id=content_id).first()
            if not content_item:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(content_item, key) and key not in ['id', 'created_at']:
                    setattr(content_item, key, value)
            
            # Update vector store if text_content changed
            if 'text_content' in kwargs and self.content_collection and content_item.embedding_id:
                try:
                    self.content_collection.update(
                        ids=[content_item.embedding_id],
                        documents=[content_item.text_content],
                        metadatas=[{
                            "title": content_item.title,
                            "source": content_item.source,
                            "content_type": content_item.content_type,
                            "user_id": content_item.user_id or "",
                            "tenant_id": content_item.tenant_id or "",
                            "tags": ",".join([tag.name for tag in content_item.tags]),
                            "updated_at": datetime.utcnow().isoformat()
                        }]
                    )
                except Exception as e:
                    logger.error(f"Error updating ChromaDB: {e}")
            
            session.commit()
            session.refresh(content_item)
            
            # Force load relationships
            _ = content_item.tags
            _ = content_item.concepts
            
            # Create detached copy
            detached = ContentItem(
                id=content_item.id,
                title=content_item.title,
                source=content_item.source,
                content_type=content_item.content_type,
                text_content=content_item.text_content,
                summary=content_item.summary,
                content_metadata=content_item.content_metadata,
                user_id=content_item.user_id,
                tenant_id=content_item.tenant_id,
                embedding_id=content_item.embedding_id,
                created_at=content_item.created_at,
                updated_at=content_item.updated_at
            )
            
            return detached
    
    async def delete_content(self, content_id: str) -> bool:
        """Delete a content item
        
        Args:
            content_id: ID of the content item
            
        Returns:
            True if deleted, False if not found
        """
        with self.get_session() as session:
            content_item = session.query(ContentItem).filter_by(id=content_id).first()
            if not content_item:
                return False
            
            # Delete from vector store if available
            if self.content_collection and content_item.embedding_id:
                try:
                    self.content_collection.delete(ids=[content_item.embedding_id])
                except Exception as e:
                    logger.error(f"Error deleting from ChromaDB: {e}")
            
            session.delete(content_item)
            session.commit()
            return True
    
    async def search_content(
        self,
        query: str,
        limit: int = 10,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        content_types: Optional[List[str]] = None,
        embeddings: Optional[List[float]] = None
    ) -> List[ContentItem]:
        """Search for content items using vector similarity and/or text search
        
        Args:
            query: Search query text
            limit: Maximum number of results
            user_id: Filter by user ID
            tenant_id: Filter by tenant ID
            content_types: Filter by content types
            embeddings: Pre-computed query embeddings
            
        Returns:
            List of matching content items
        """
        # Track search query
        with self.get_session() as session:
            search_query = SearchQuery(
                query_text=query,
                user_id=user_id
            )
            session.add(search_query)
            session.commit()
        
        # Vector search if available
        if self.content_collection:
            try:
                # Build where clause for metadata filtering
                where_conditions = []
                if user_id:
                    where_conditions.append({"user_id": user_id})
                if tenant_id:
                    where_conditions.append({"tenant_id": tenant_id})
                if content_types:
                    where_conditions.append({"content_type": {"$in": content_types}})
                
                # Perform search
                if embeddings:
                    results = self.content_collection.query(
                        query_embeddings=[embeddings],
                        n_results=limit,
                        where={"$and": where_conditions} if where_conditions else None
                    )
                else:
                    results = self.content_collection.query(
                        query_texts=[query],
                        n_results=limit,
                        where={"$and": where_conditions} if where_conditions else None
                    )
                
                # Get content items from database
                content_ids = results.get("ids", [[]])[0]
                if content_ids:
                    with self.get_session() as session:
                        items = session.query(ContentItem).filter(
                            ContentItem.id.in_(content_ids)
                        ).all()
                        
                        # Sort by the order returned from vector search
                        id_to_item = {str(item.id): item for item in items}
                        sorted_items = [id_to_item[id] for id in content_ids if id in id_to_item]
                        
                        # Convert to detached objects before returning
                        detached_items = []
                        for item in sorted_items:
                            # Force load relationships
                            _ = item.tags
                            _ = item.concepts
                            session.refresh(item)
                            
                            # Create detached copy
                            detached = ContentItem(
                                id=item.id,
                                title=item.title,
                                source=item.source,
                                content_type=item.content_type,
                                text_content=item.text_content,
                                summary=item.summary,
                                content_metadata=item.content_metadata,
                                user_id=item.user_id,
                                tenant_id=item.tenant_id,
                                embedding_id=item.embedding_id,
                                created_at=item.created_at,
                                updated_at=item.updated_at
                            )
                            detached_items.append(detached)
                        
                        return detached_items
                
            except Exception as e:
                logger.error(f"Error in vector search: {e}")
        
        # Fallback to database text search
        with self.get_session() as session:
            query_lower = f"%{query.lower()}%"
            
            conditions = [
                or_(
                    func.lower(ContentItem.title).like(query_lower),
                    func.lower(ContentItem.text_content).like(query_lower),
                    func.lower(ContentItem.summary).like(query_lower)
                )
            ]
            
            if user_id:
                conditions.append(ContentItem.user_id == user_id)
            if tenant_id:
                conditions.append(ContentItem.tenant_id == tenant_id)
            if content_types:
                conditions.append(ContentItem.content_type.in_(content_types))
            
            items = session.query(ContentItem).filter(
                and_(*conditions)
            ).limit(limit).all()
            
            # Convert to detached objects before returning
            detached_items = []
            for item in items:
                # Force load relationships
                _ = item.tags
                _ = item.concepts
                session.refresh(item)
                
                # Create detached copy
                detached = ContentItem(
                    id=item.id,
                    title=item.title,
                    source=item.source,
                    content_type=item.content_type,
                    text_content=item.text_content,
                    summary=item.summary,
                    content_metadata=item.content_metadata,
                    user_id=item.user_id,
                    tenant_id=item.tenant_id,
                    embedding_id=item.embedding_id,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                )
                detached_items.append(detached)
            
            return detached_items
    
    async def list_content(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        content_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ContentItem]:
        """List content items with optional filtering
        
        Args:
            user_id: Filter by user ID
            tenant_id: Filter by tenant ID
            content_type: Filter by content type
            tags: Filter by tags (any match)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of content items
        """
        with self.get_session() as session:
            query = session.query(ContentItem)
            
            if user_id:
                query = query.filter(ContentItem.user_id == user_id)
            if tenant_id:
                query = query.filter(ContentItem.tenant_id == tenant_id)
            if content_type:
                query = query.filter(ContentItem.content_type == content_type)
            if tags:
                query = query.join(ContentItem.tags).filter(Tag.name.in_(tags))
            
            # Order by newest first
            query = query.order_by(ContentItem.created_at.desc())
            
            # Apply pagination
            items = query.offset(offset).limit(limit).all()
            
            # Convert to detached objects before returning
            detached_items = []
            for item in items:
                # Force load relationships
                _ = item.tags
                _ = item.concepts
                session.refresh(item)
                
                # Create detached copy
                detached = ContentItem(
                    id=item.id,
                    title=item.title,
                    source=item.source,
                    content_type=item.content_type,
                    text_content=item.text_content,
                    summary=item.summary,
                    content_metadata=item.content_metadata,
                    user_id=item.user_id,
                    tenant_id=item.tenant_id,
                    embedding_id=item.embedding_id,
                    created_at=item.created_at,
                    updated_at=item.updated_at
                )
                detached_items.append(detached)
            
            return detached_items
    
    async def get_or_create_tag(self, tag_name: str, description: Optional[str] = None) -> Tag:
        """Get or create a tag by name"""
        with self.get_session() as session:
            tag = session.query(Tag).filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, description=description)
                session.add(tag)
                session.commit()
                session.refresh(tag)
            
            # Create detached copy
            detached = Tag(
                name=tag.name,
                description=tag.description,
                created_at=tag.created_at
            )
            detached.id = tag.id
            
            return detached
    
    async def list_tags(self) -> List[Tag]:
        """List all available tags"""
        with self.get_session() as session:
            tags = session.query(Tag).order_by(Tag.name).all()
            
            # Convert to detached objects
            detached_tags = []
            for tag in tags:
                detached = Tag(
                    name=tag.name,
                    description=tag.description,
                    created_at=tag.created_at
                )
                detached.id = tag.id
                detached_tags.append(detached)
            
            return detached_tags
    
    async def get_concepts_by_type(
        self,
        concept_type: str,
        limit: int = 100
    ) -> List[Concept]:
        """Get concepts by type"""
        with self.get_session() as session:
            concepts = session.query(Concept).filter_by(
                type=concept_type
            ).order_by(Concept.name).limit(limit).all()
            
            # Convert to detached objects
            detached_concepts = []
            for concept in concepts:
                detached = Concept(
                    name=concept.name,
                    type=concept.type,
                    confidence=concept.confidence,
                    content_id=concept.content_id
                )
                detached.id = concept.id
                detached_concepts.append(detached)
            
            return detached_concepts
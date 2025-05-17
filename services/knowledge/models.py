"""Database models for Knowledge Repository using SQLAlchemy"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import json

from enum import Enum
from sqlalchemy import (
    Column, String, Text, DateTime, JSON, Integer, Float,
    ForeignKey, Table, create_engine, Index, Enum as SQLEnum, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.types import TypeDecorator, String as SA_String
from sqlalchemy.sql import func

class UUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses PostgreSQL's UUID type when available, 
    otherwise uses String(36) to store as hex values.
    """
    
    impl = SA_String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(SA_String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            else:
                return value

Base = declarative_base()


# Knowledge Repository Enums
class SourceType(str, Enum):
    """Enumeration of knowledge source types."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PDF = "pdf"
    URL = "url"
    MANUAL = "manual"


class ContentType(str, Enum):
    """Enumeration of content types."""
    SUMMARY = "summary"
    TRANSCRIPT = "transcript"
    EXTRACTION = "extraction"
    NOTE = "note"


class KnowledgeStatus(str, Enum):
    """Enumeration of knowledge item statuses."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ReviewStatus(str, Enum):
    """Enumeration of review statuses."""
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    REJECTED = "rejected"


class RelationshipType(str, Enum):
    """Enumeration of relationship types between knowledge items."""
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"
    SUMMARIZES = "summarizes"
    REFERENCES = "references"

# Association table for many-to-many relationship between content and tags
content_tags = Table(
    'content_tags',
    Base.metadata,
    Column('content_id', UUID(), ForeignKey('content_items.id'), primary_key=True),
    Column('tag_id', UUID(), ForeignKey('tags.id'), primary_key=True)
)


class ContentItem(Base):
    """Content item model for PostgreSQL"""
    __tablename__ = 'content_items'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    source = Column(String(1024), nullable=False)
    content_type = Column(String(50), nullable=False, index=True)  # url, pdf, text, email
    text_content = Column(Text, nullable=False)
    summary = Column(Text)
    embedding_id = Column(String(255), index=True)  # ChromaDB vector ID
    
    # Content metadata stored as JSON (renamed to avoid SQLAlchemy reserved word conflict)
    content_metadata = Column('metadata', JSON, default=dict)
    
    # User and tenant support
    user_id = Column(String(255), index=True)
    tenant_id = Column(String(255), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tags = relationship('Tag', secondary=content_tags, back_populates='content_items')
    concepts = relationship('Concept', back_populates='content_item', cascade='all, delete-orphan')
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_content_created_at', 'created_at'),
        Index('idx_content_user_tenant', 'user_id', 'tenant_id'),
        Index('idx_content_type_user', 'content_type', 'user_id'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'title': self.title,
            'source': self.source,
            'content_type': self.content_type,
            'text_content': self.text_content,
            'summary': self.summary,
            'embedding_id': self.embedding_id,
            'metadata': self.content_metadata,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': [tag.name for tag in self.tags],
            'concepts': [concept.to_dict() for concept in self.concepts]
        }


class Tag(Base):
    """Tag model for categorizing content"""
    __tablename__ = 'tags'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    content_items = relationship('ContentItem', secondary=content_tags, back_populates='tags')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Concept(Base):
    """Extracted concepts from content"""
    __tablename__ = 'concepts'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    content_id = Column(UUID(), ForeignKey('content_items.id'), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50))  # person, organization, location, topic, etc.
    confidence = Column(JSON)  # Store confidence scores or additional AI metadata
    
    # Relationships
    content_item = relationship('ContentItem', back_populates='concepts')
    
    # Index for concept search
    __table_args__ = (
        Index('idx_concept_name_type', 'name', 'type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'content_id': str(self.content_id),
            'name': self.name,
            'type': self.type,
            'confidence': self.confidence
        }


class SearchQuery(Base):
    """Track search queries for analytics and improvement"""
    __tablename__ = 'search_queries'
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    user_id = Column(String(255), index=True)
    results_count = Column(JSON)  # Store result counts by type
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for analytics
    __table_args__ = (
        Index('idx_search_timestamp', 'timestamp'),
        Index('idx_search_user', 'user_id'),
    )


# Knowledge Repository Models (MVP)
class KnowledgeItem(Base):
    """Main table for storing processed content from various sources."""
    __tablename__ = "knowledge_items"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Source information
    source_type = Column(SQLEnum(SourceType), nullable=False, index=True)
    source_url = Column(Text)
    source_metadata = Column(JSON)
    
    # Content information
    content_type = Column(SQLEnum(ContentType), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    content_metadata = Column(JSON)
    
    # Organization and searchability
    tags = Column(ARRAY(Text), default=list)
    categories = Column(ARRAY(Text), default=list)
    language = Column(String(10), default='en')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Versioning and relationships
    version = Column(Integer, default=1)
    parent_id = Column(UUID(), ForeignKey("knowledge_items.id"))
    
    # Status and quality
    status = Column(SQLEnum(KnowledgeStatus), default=KnowledgeStatus.ACTIVE, nullable=False, index=True)
    confidence_score = Column(Float)
    review_status = Column(SQLEnum(ReviewStatus))
    
    # Relationships
    parent = relationship("KnowledgeItem", remote_side=[id], backref="children")
    source_relationships = relationship("KnowledgeRelationship", foreign_keys="KnowledgeRelationship.source_id", back_populates="source")
    target_relationships = relationship("KnowledgeRelationship", foreign_keys="KnowledgeRelationship.target_id", back_populates="target")
    attachments = relationship("KnowledgeAttachment", back_populates="knowledge_item", cascade="all, delete-orphan")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_knowledge_items_created_at', 'created_at'),
        Index('idx_knowledge_items_tags', 'tags', postgresql_using='gin'),
        Index('idx_knowledge_items_categories', 'categories', postgresql_using='gin'),
        Index('idx_knowledge_items_text_search', func.to_tsvector('english', 'content_text'), postgresql_using='gin'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'agent_id': self.agent_id,
            'user_id': self.user_id,
            'source_type': self.source_type.value if self.source_type else None,
            'source_url': self.source_url,
            'source_metadata': self.source_metadata,
            'content_type': self.content_type.value if self.content_type else None,
            'content_text': self.content_text,
            'content_metadata': self.content_metadata,
            'tags': self.tags or [],
            'categories': self.categories or [],
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'version': self.version,
            'parent_id': str(self.parent_id) if self.parent_id else None,
            'status': self.status.value if self.status else None,
            'confidence_score': self.confidence_score,
            'review_status': self.review_status.value if self.review_status else None
        }


class KnowledgeRelationship(Base):
    """Table for storing relationships between knowledge items."""
    __tablename__ = "knowledge_relationships"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(), ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(UUID(), ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(SQLEnum(RelationshipType), nullable=False)
    relationship_metadata = Column('metadata', JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    source = relationship("KnowledgeItem", foreign_keys=[source_id], back_populates="source_relationships")
    target = relationship("KnowledgeItem", foreign_keys=[target_id], back_populates="target_relationships")
    
    __table_args__ = (
        Index('idx_knowledge_relationships_type', 'relationship_type'),
    )


class KnowledgeAttachment(Base):
    """Table for storing references to attachments associated with knowledge items."""
    __tablename__ = "knowledge_attachments"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    knowledge_item_id = Column(UUID(), ForeignKey("knowledge_items.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    attachment_metadata = Column('metadata', JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    knowledge_item = relationship("KnowledgeItem", back_populates="attachments")
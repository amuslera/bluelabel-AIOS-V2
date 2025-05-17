"""
Knowledge Repository Service Implementation (MVP)

This module provides the service layer for the MVP knowledge repository,
implementing CRUD operations and search functionality for knowledge items.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from services.knowledge.models import (
    KnowledgeItem, KnowledgeRelationship, KnowledgeAttachment,
    SourceType, ContentType, KnowledgeStatus, ReviewStatus, RelationshipType
)


logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service class for managing knowledge repository operations."""
    
    def __init__(self, session: Session):
        """Initialize the service with a database session."""
        self.session = session
    
    async def create_knowledge_item(
        self,
        agent_id: str,
        user_id: str,
        source_type: SourceType,
        content_type: ContentType,
        content_text: str,
        source_url: Optional[str] = None,
        source_metadata: Optional[Dict[str, Any]] = None,
        content_metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        language: str = 'en',
        processed_at: Optional[datetime] = None,
        parent_id: Optional[UUID] = None,
        status: KnowledgeStatus = KnowledgeStatus.ACTIVE,
        confidence_score: Optional[float] = None,
        review_status: Optional[ReviewStatus] = None
    ) -> KnowledgeItem:
        """Create a new knowledge item."""
        try:
            knowledge_item = KnowledgeItem(
                agent_id=agent_id,
                user_id=user_id,
                source_type=source_type,
                content_type=content_type,
                content_text=content_text,
                source_url=source_url,
                source_metadata=source_metadata or {},
                content_metadata=content_metadata or {},
                tags=tags or [],
                categories=categories or [],
                language=language,
                processed_at=processed_at or datetime.utcnow(),
                parent_id=parent_id,
                status=status,
                confidence_score=confidence_score,
                review_status=review_status
            )
            
            self.session.add(knowledge_item)
            self.session.commit()
            self.session.refresh(knowledge_item)
            
            logger.info(f"Created knowledge item {knowledge_item.id} for user {user_id}")
            return knowledge_item
            
        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Integrity error creating knowledge item: {e}")
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error creating knowledge item: {e}")
            raise
    
    async def get_knowledge_item(self, item_id: UUID) -> Optional[KnowledgeItem]:
        """Retrieve a knowledge item by ID."""
        try:
            return self.session.query(KnowledgeItem).options(
                selectinload(KnowledgeItem.attachments),
                selectinload(KnowledgeItem.parent),
                selectinload(KnowledgeItem.children)
            ).filter(KnowledgeItem.id == item_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving knowledge item {item_id}: {e}")
            raise
    
    async def update_knowledge_item(
        self,
        item_id: UUID,
        **updates
    ) -> KnowledgeItem:
        """Update a knowledge item."""
        try:
            knowledge_item = await self.get_knowledge_item(item_id)
            if not knowledge_item:
                raise ValueError(f"Knowledge item {item_id} not found")
            
            # Update allowed fields
            allowed_fields = {
                'content_text', 'source_metadata', 'content_metadata',
                'tags', 'categories', 'language', 'status',
                'confidence_score', 'review_status'
            }
            
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(knowledge_item, field, value)
            
            knowledge_item.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(knowledge_item)
            
            logger.info(f"Updated knowledge item {item_id}")
            return knowledge_item
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating knowledge item {item_id}: {e}")
            raise
    
    async def delete_knowledge_item(self, item_id: UUID) -> bool:
        """Soft delete a knowledge item by setting status to DELETED."""
        try:
            knowledge_item = await self.get_knowledge_item(item_id)
            if not knowledge_item:
                return False
            
            knowledge_item.status = KnowledgeStatus.DELETED
            knowledge_item.updated_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"Soft deleted knowledge item {item_id}")
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting knowledge item {item_id}: {e}")
            raise
    
    async def search_knowledge_items(
        self,
        user_id: str,
        query: Optional[str] = None,
        source_types: Optional[List[SourceType]] = None,
        content_types: Optional[List[ContentType]] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[KnowledgeStatus] = KnowledgeStatus.ACTIVE,
        limit: int = 50,
        offset: int = 0
    ) -> List[KnowledgeItem]:
        """Search knowledge items with filters."""
        try:
            filters = [KnowledgeItem.user_id == user_id]
            
            if status:
                filters.append(KnowledgeItem.status == status)
            
            if source_types:
                filters.append(KnowledgeItem.source_type.in_(source_types))
            
            if content_types:
                filters.append(KnowledgeItem.content_type.in_(content_types))
            
            if tags:
                # Filter items that have any of the specified tags
                tag_filters = []
                for tag in tags:
                    tag_filters.append(KnowledgeItem.tags.contains([tag]))
                filters.append(or_(*tag_filters))
            
            if categories:
                # Filter items that have any of the specified categories
                category_filters = []
                for category in categories:
                    category_filters.append(KnowledgeItem.categories.contains([category]))
                filters.append(or_(*category_filters))
            
            if date_from:
                filters.append(KnowledgeItem.created_at >= date_from)
            
            if date_to:
                filters.append(KnowledgeItem.created_at <= date_to)
            
            # Text search if query provided
            if query:
                filters.append(
                    func.to_tsvector('english', KnowledgeItem.content_text).match(query)
                )
            
            # Build and execute query
            query_builder = self.session.query(KnowledgeItem).filter(
                and_(*filters)
            ).order_by(
                KnowledgeItem.created_at.desc()
            ).limit(limit).offset(offset)
            
            results = query_builder.all()
            
            logger.info(f"Found {len(results)} knowledge items for user {user_id}")
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Error searching knowledge items: {e}")
            raise
    
    async def get_related_items(
        self,
        item_id: UUID,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> List[KnowledgeItem]:
        """Get items related to a specific knowledge item."""
        try:
            # Query relationships where this item is the source
            relationship_query = self.session.query(KnowledgeRelationship).filter(
                KnowledgeRelationship.source_id == item_id
            )
            
            if relationship_types:
                relationship_query = relationship_query.filter(
                    KnowledgeRelationship.relationship_type.in_(relationship_types)
                )
            
            relationships = relationship_query.all()
            
            # Get target items
            target_ids = [rel.target_id for rel in relationships]
            if not target_ids:
                return []
            
            related_items = self.session.query(KnowledgeItem).filter(
                KnowledgeItem.id.in_(target_ids),
                KnowledgeItem.status == KnowledgeStatus.ACTIVE
            ).all()
            
            return related_items
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting related items for {item_id}: {e}")
            raise
    
    async def aggregate_by_tag(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Aggregate knowledge items by tag for a user."""
        try:
            filters = [
                KnowledgeItem.user_id == user_id,
                KnowledgeItem.status == KnowledgeStatus.ACTIVE
            ]
            
            if date_from:
                filters.append(KnowledgeItem.created_at >= date_from)
            
            if date_to:
                filters.append(KnowledgeItem.created_at <= date_to)
            
            # Get all items for the user
            items = self.session.query(KnowledgeItem).filter(
                and_(*filters)
            ).all()
            
            # Aggregate tags
            tag_counts = {}
            for item in items:
                for tag in item.tags or []:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            return tag_counts
            
        except SQLAlchemyError as e:
            logger.error(f"Error aggregating tags for user {user_id}: {e}")
            raise
    
    async def bulk_create_knowledge_items(
        self,
        items: List[Dict[str, Any]]
    ) -> List[KnowledgeItem]:
        """Create multiple knowledge items in a single transaction."""
        created_items = []
        try:
            for item_data in items:
                knowledge_item = KnowledgeItem(**item_data)
                self.session.add(knowledge_item)
                created_items.append(knowledge_item)
            
            self.session.commit()
            
            # Refresh all items
            for item in created_items:
                self.session.refresh(item)
            
            logger.info(f"Bulk created {len(created_items)} knowledge items")
            return created_items
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error bulk creating knowledge items: {e}")
            raise
    
    async def batch_update_tags(
        self,
        item_ids: List[UUID],
        tags_to_add: List[str],
        tags_to_remove: List[str]
    ) -> int:
        """Batch update tags for multiple knowledge items."""
        updated_count = 0
        try:
            items = self.session.query(KnowledgeItem).filter(
                KnowledgeItem.id.in_(item_ids)
            ).all()
            
            for item in items:
                current_tags = set(item.tags or [])
                
                # Add new tags
                current_tags.update(tags_to_add)
                
                # Remove specified tags
                current_tags.difference_update(tags_to_remove)
                
                item.tags = list(current_tags)
                item.updated_at = datetime.utcnow()
                updated_count += 1
            
            self.session.commit()
            
            logger.info(f"Updated tags for {updated_count} knowledge items")
            return updated_count
            
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error batch updating tags: {e}")
            raise
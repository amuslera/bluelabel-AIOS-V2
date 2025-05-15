from typing import Dict, Any, List, Optional, Union
import json
import os
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

# Try to import ChromaDB, but don't fail if it's not available
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

class ContentItem(BaseModel):
    """A content item stored in the knowledge repository"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source: str
    content_type: str  # "url", "pdf", "text"
    text_content: str
    summary: Optional[str] = None
    vector_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class KnowledgeRepository:
    """Repository for storing and retrieving content"""
    
    def __init__(self, data_dir: str = "data/knowledge", vector_db_host: str = "localhost", vector_db_port: int = 8000):
        """Initialize the knowledge repository
        
        Args:
            data_dir: Directory to store content items
            vector_db_host: Host for ChromaDB
            vector_db_port: Port for ChromaDB
        """
        self.data_dir = data_dir
        self.vector_db_host = vector_db_host
        self.vector_db_port = vector_db_port
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize content store
        self.content_items: Dict[str, ContentItem] = self._load_content_items()
        
        # Initialize vector store if available
        self.vector_client = None
        self.vector_collection = None
        if CHROMADB_AVAILABLE:
            try:
                self.vector_client = chromadb.HttpClient(
                    host=vector_db_host,
                    port=vector_db_port
                )
                self.vector_collection = self.vector_client.get_or_create_collection(
                    name="content_embeddings"
                )
            except Exception as e:
                print(f"Error connecting to ChromaDB: {str(e)}")
    
    def _load_content_items(self) -> Dict[str, ContentItem]:
        """Load all content items from disk"""
        items = {}
        
        if not os.path.exists(self.data_dir):
            return items
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.data_dir, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                    item = ContentItem(**data)
                    items[item.id] = item
        
        return items
    
    def add_content(self, title: str, source: str, content_type: str, text_content: str, 
                   summary: Optional[str] = None, metadata: Dict[str, Any] = None, 
                   user_id: Optional[str] = None, tags: List[str] = None) -> ContentItem:
        """Add a new content item to the repository
        
        Args:
            title: Title of the content
            source: Source of the content (URL, file path, etc.)
            content_type: Type of content ("url", "pdf", "text")
            text_content: Text content
            summary: Optional summary
            metadata: Optional metadata
            user_id: Optional user ID
            tags: Optional tags
            
        Returns:
            The created content item
        """
        # Create content item
        item = ContentItem(
            title=title,
            source=source,
            content_type=content_type,
            text_content=text_content,
            summary=summary,
            metadata=metadata or {},
            user_id=user_id,
            tags=tags or []
        )
        
        # Add to vector store if available
        if self.vector_collection is not None:
            try:
                # Add to vector store
                self.vector_collection.add(
                    ids=[item.id],
                    documents=[text_content],
                    metadatas=[{
                        "title": title,
                        "source": source,
                        "content_type": content_type,
                        "user_id": user_id or "",
                        "tags": ",".join(tags or [])
                    }]
                )
                
                # Set vector ID
                item.vector_id = item.id
            
            except Exception as e:
                print(f"Error adding to vector store: {str(e)}")
        
        # Save to disk
        filepath = os.path.join(self.data_dir, f"{item.id}.json")
        with open(filepath, "w") as f:
            f.write(item.model_dump_json(indent=2))
        
        # Add to in-memory store
        self.content_items[item.id] = item
        
        return item
    
    def get_content(self, content_id: str) -> Optional[ContentItem]:
        """Get a content item by ID"""
        return self.content_items.get(content_id)
    
    def update_content(self, content_id: str, **kwargs) -> Optional[ContentItem]:
        """Update a content item
        
        Args:
            content_id: ID of the content item
            **kwargs: Fields to update
            
        Returns:
            The updated content item, or None if not found
        """
        if content_id not in self.content_items:
            return None
        
        # Get existing item
        item = self.content_items[content_id]
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        # Update timestamp
        item.updated_at = datetime.now()
        
        # Save to disk
        filepath = os.path.join(self.data_dir, f"{item.id}.json")
        with open(filepath, "w") as f:
            f.write(item.model_dump_json(indent=2))
        
        # Update vector store if text_content changed and vector store is available
        if "text_content" in kwargs and self.vector_collection is not None and item.vector_id:
            try:
                self.vector_collection.update(
                    ids=[item.vector_id],
                    documents=[item.text_content],
                    metadatas=[{
                        "title": item.title,
                        "source": item.source,
                        "content_type": item.content_type,
                        "user_id": item.user_id or "",
                        "tags": ",".join(item.tags)
                    }]
                )
            except Exception as e:
                print(f"Error updating vector store: {str(e)}")
        
        return item
    
    def delete_content(self, content_id: str) -> bool:
        """Delete a content item
        
        Args:
            content_id: ID of the content item
            
        Returns:
            True if deleted, False if not found
        """
        if content_id not in self.content_items:
            return False
        
        # Get item
        item = self.content_items[content_id]
        
        # Delete from vector store if available
        if self.vector_collection is not None and item.vector_id:
            try:
                self.vector_collection.delete(ids=[item.vector_id])
            except Exception as e:
                print(f"Error deleting from vector store: {str(e)}")
        
        # Delete from disk
        filepath = os.path.join(self.data_dir, f"{item.id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Delete from in-memory store
        del self.content_items[content_id]
        
        return True
    
    def search_content(self, query: str, limit: int = 10) -> List[ContentItem]:
        """Search for content items
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching content items
        """
        if self.vector_collection is not None:
            try:
                # Search vector store
                results = self.vector_collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                # Get content items
                items = []
                for i, item_id in enumerate(results.get("ids", [[]])[0]):
                    if item_id in self.content_items:
                        items.append(self.content_items[item_id])
                
                return items
            
            except Exception as e:
                print(f"Error searching vector store: {str(e)}")
        
        # Fallback to simple text search
        query = query.lower()
        matches = []
        
        for item in self.content_items.values():
            # Check title, content, and summary
            if query in item.title.lower() or \
               query in item.text_content.lower() or \
               (item.summary and query in item.summary.lower()):
                matches.append(item)
            
            # Check tags
            if any(query in tag.lower() for tag in item.tags):
                matches.append(item)
            
            # Limit results
            if len(matches) >= limit:
                break
        
        return matches
    
    def list_content(self, user_id: Optional[str] = None, content_type: Optional[str] = None, 
                    tags: List[str] = None, limit: int = 100, offset: int = 0) -> List[ContentItem]:
        """List content items with optional filtering
        
        Args:
            user_id: Filter by user ID
            content_type: Filter by content type
            tags: Filter by tags (any match)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of content items
        """
        # Filter items
        filtered_items = list(self.content_items.values())
        
        if user_id is not None:
            filtered_items = [item for item in filtered_items if item.user_id == user_id]
        
        if content_type is not None:
            filtered_items = [item for item in filtered_items if item.content_type == content_type]
        
        if tags:
            filtered_items = [item for item in filtered_items if any(tag in item.tags for tag in tags)]
        
        # Sort by created_at (newest first)
        filtered_items.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return filtered_items[offset:offset+limit]

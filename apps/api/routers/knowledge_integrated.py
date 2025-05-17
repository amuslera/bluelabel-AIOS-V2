"""
Knowledge router that matches frontend expectations
Handles knowledge items, tags, and export functionality
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()

# Mock knowledge storage
mock_knowledge_items = {}
mock_tags = set()

class KnowledgeItem:
    def __init__(self, title: str, type: str, source: str, summary: str, tags: List[str]):
        self.id = str(uuid.uuid4())
        self.title = title
        self.type = type
        self.source = source
        self.timestamp = datetime.utcnow().isoformat()
        self.summary = summary
        self.tags = tags
        self.processedBy = "content_mind"
        
        # Add tags to global set
        mock_tags.update(tags)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "tags": self.tags,
            "processedBy": self.processedBy
        }

@router.get("/items")
async def get_knowledge_items(
    search: Optional[str] = None,
    tag: Optional[str] = None,
    type: Optional[str] = None
):
    """Get all knowledge items with optional filtering"""
    items = list(mock_knowledge_items.values())
    
    # Apply filters
    if search:
        items = [item for item in items if search.lower() in item["title"].lower() or search.lower() in item["summary"].lower()]
    
    if tag:
        items = [item for item in items if tag in item["tags"]]
    
    if type:
        items = [item for item in items if item["type"] == type]
    
    return items

@router.get("/items/{item_id}")
async def get_knowledge_item(item_id: str):
    """Get a specific knowledge item"""
    if item_id not in mock_knowledge_items:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    return mock_knowledge_items[item_id]

@router.post("/items")
async def create_knowledge_item(item: dict):
    """Create a new knowledge item"""
    knowledge_item = KnowledgeItem(
        title=item.get("title", "Untitled"),
        type=item.get("type", "document"),
        source=item.get("source", "manual"),
        summary=item.get("summary", ""),
        tags=item.get("tags", [])
    )
    
    mock_knowledge_items[knowledge_item.id] = knowledge_item.to_dict()
    
    return knowledge_item.to_dict()

@router.get("/items/{item_id}/export")
async def export_knowledge_item(item_id: str, format: str = Query(..., regex="^(json|pdf|md)$")):
    """Export a knowledge item in specified format"""
    if item_id not in mock_knowledge_items:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    item = mock_knowledge_items[item_id]
    
    # For now, just return the item data
    # In production, this would generate actual files
    return {
        "format": format,
        "content": item,
        "exportedAt": datetime.utcnow().isoformat()
    }

@router.get("/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    items = list(mock_knowledge_items.values())
    
    doc_count = len([item for item in items if item["type"] == "document"])
    unique_tags = len(mock_tags)
    agents_used = set(item["processedBy"] for item in items)
    
    return {
        "totalItems": len(items),
        "documents": doc_count,
        "uniqueTags": unique_tags,
        "agentsUsed": list(agents_used)
    }

@router.get("/tags")
async def get_all_tags():
    """Get all unique tags"""
    return sorted(list(mock_tags))

# Initialize with sample data
def init_sample_knowledge():
    sample_items = [
        KnowledgeItem(
            "Q1 Financial Analysis",
            "document",
            "email",
            "Analysis of Q1 2024 financial performance showing 15% revenue growth",
            ["finance", "quarterly", "analysis"]
        ),
        KnowledgeItem(
            "Market Research Summary",
            "article",
            "web",
            "Overview of emerging trends in AI and machine learning for enterprise",
            ["market", "AI", "trends", "research"]
        ),
        KnowledgeItem(
            "Team Meeting Notes",
            "note",
            "manual",
            "Key decisions from product strategy meeting on March 15",
            ["meeting", "product", "strategy"]
        )
    ]
    
    for item in sample_items:
        mock_knowledge_items[item.id] = item.to_dict()

# Initialize on import
init_sample_knowledge()
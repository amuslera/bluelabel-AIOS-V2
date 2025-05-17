# Knowledge Repository Schema Draft

## Overview
This schema defines the data model for the Knowledge Repository service, which stores processed content from the ContentMind agent. The design focuses on relational storage with PostgreSQL, providing flexible querying capabilities for the Digest agent and future extensions.

## PostgreSQL Models

### 1. knowledge_items
Primary table for storing processed content from various sources.

```sql
CREATE TABLE knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,  -- ID of the agent that created this item
    user_id VARCHAR(255) NOT NULL,   -- User/tenant this knowledge belongs to
    
    -- Source information
    source_type ENUM('email', 'whatsapp', 'pdf', 'url', 'manual') NOT NULL,
    source_url TEXT,                 -- URL or file path of the source
    source_metadata JSONB,           -- Additional source-specific data
    
    -- Content information
    content_type ENUM('summary', 'transcript', 'extraction', 'note') NOT NULL,
    content_text TEXT NOT NULL,      -- The actual processed content
    content_metadata JSONB,          -- Additional content-specific data
    
    -- Organization and searchability
    tags TEXT[],                     -- Array of tags for categorization
    categories TEXT[],               -- Hierarchical categories
    language VARCHAR(10) DEFAULT 'en',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,  -- When the content was processed
    
    -- Versioning and relationships
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES knowledge_items(id),  -- For content versioning
    
    -- Status and quality
    status ENUM('draft', 'active', 'archived', 'deleted') DEFAULT 'active',
    confidence_score FLOAT,          -- Agent's confidence in the processing
    review_status ENUM('pending', 'reviewed', 'approved', 'rejected')
);

-- Indexes for efficient querying
CREATE INDEX idx_knowledge_items_user_id ON knowledge_items(user_id);
CREATE INDEX idx_knowledge_items_agent_id ON knowledge_items(agent_id);
CREATE INDEX idx_knowledge_items_source_type ON knowledge_items(source_type);
CREATE INDEX idx_knowledge_items_content_type ON knowledge_items(content_type);
CREATE INDEX idx_knowledge_items_tags ON knowledge_items USING GIN(tags);
CREATE INDEX idx_knowledge_items_categories ON knowledge_items USING GIN(categories);
CREATE INDEX idx_knowledge_items_created_at ON knowledge_items(created_at DESC);
CREATE INDEX idx_knowledge_items_status ON knowledge_items(status);
CREATE INDEX idx_knowledge_items_text_search ON knowledge_items USING GIN(to_tsvector('english', content_text));
```

### 2. knowledge_relationships
Table for storing relationships between knowledge items.

```sql
CREATE TABLE knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    relationship_type ENUM('derived_from', 'related_to', 'summarizes', 'references') NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(source_id, target_id, relationship_type)
);

CREATE INDEX idx_knowledge_relationships_source_id ON knowledge_relationships(source_id);
CREATE INDEX idx_knowledge_relationships_target_id ON knowledge_relationships(target_id);
```

### 3. knowledge_attachments
Table for storing references to attachments associated with knowledge items.

```sql
CREATE TABLE knowledge_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_item_id UUID NOT NULL REFERENCES knowledge_items(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,  -- S3/MinIO path
    file_size BIGINT,
    mime_type VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_attachments_item_id ON knowledge_attachments(knowledge_item_id);
```

## Repository Service Interface

The Knowledge Repository service will provide the following key methods:

### Basic CRUD Operations
```python
async def create_knowledge_item(
    agent_id: str,
    user_id: str,
    source_type: str,
    content_type: str,
    content_text: str,
    **kwargs
) -> KnowledgeItem

async def get_knowledge_item(item_id: UUID) -> Optional[KnowledgeItem]

async def update_knowledge_item(
    item_id: UUID,
    **updates
) -> KnowledgeItem

async def delete_knowledge_item(item_id: UUID) -> bool
```

### Retrieval and Filtering
```python
async def search_knowledge_items(
    user_id: str,
    query: Optional[str] = None,
    source_types: Optional[List[str]] = None,
    content_types: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0
) -> List[KnowledgeItem]

async def get_related_items(
    item_id: UUID,
    relationship_types: Optional[List[str]] = None
) -> List[KnowledgeItem]

async def aggregate_by_tag(
    user_id: str,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None
) -> Dict[str, int]
```

### Batch Operations
```python
async def bulk_create_knowledge_items(
    items: List[KnowledgeItemCreate]
) -> List[KnowledgeItem]

async def batch_update_tags(
    item_ids: List[UUID],
    tags_to_add: List[str],
    tags_to_remove: List[str]
) -> int
```

## Example Usage

### Creating a knowledge item from ContentMind:
```python
knowledge_item = await repository.create_knowledge_item(
    agent_id="contentmind_agent",
    user_id="user_123",
    source_type="pdf",
    source_url="s3://bucket/documents/paper.pdf",
    content_type="summary",
    content_text="This paper discusses advanced AI architectures...",
    tags=["AI", "research", "architecture"],
    categories=["Technology", "Research Papers"],
    source_metadata={
        "file_name": "paper.pdf",
        "page_count": 15,
        "author": "John Doe"
    },
    confidence_score=0.95
)
```

### Querying for digest generation:
```python
recent_summaries = await repository.search_knowledge_items(
    user_id="user_123",
    content_types=["summary"],
    date_from=datetime.now() - timedelta(days=7),
    tags=["AI"],
    limit=10
)
```

## Future Extensions

This schema is designed to be extensible for future enhancements:

1. **Vector Embeddings**: Add a `knowledge_embeddings` table with columns for vector data and embedding model info
2. **Full-text Search**: Leverage PostgreSQL's built-in full-text search capabilities (already indexed)
3. **Content Versioning**: Use the `parent_id` field to track content evolution
4. **Multi-tenancy**: The `user_id` field supports tenant isolation
5. **Advanced Relationships**: The relationship table can support graph-like queries
6. **Analytics**: The schema supports time-based aggregations and tag analysis

## Notes

- All text fields use TEXT type for flexibility
- JSONB fields provide schema-less extensibility for metadata
- Indexes are created for common query patterns
- The design prioritizes read performance for the Digest agent
- Status fields allow soft deletion and workflow management
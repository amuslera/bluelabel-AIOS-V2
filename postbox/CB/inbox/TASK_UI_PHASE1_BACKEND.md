# Task Assignment: UI Phase 1 Backend Support - Navigation & Command APIs

**Task ID**: TASK_UI_PHASE1_BACKEND  
**Priority**: HIGH  
**Estimated Time**: 6-8 hours  
**Assigned To**: CB (Backend Specialist)  
**Date**: 2025-06-01  

## Objective

Build backend APIs and services to support the new navigation system, including user preferences, command palette data, navigation analytics, and search functionality. Work in parallel with CA's frontend implementation.

## Backend Requirements

### 1. User Preferences API

Create endpoints to persist navigation preferences:

```python
# New endpoints needed
POST   /api/user/preferences/navigation
GET    /api/user/preferences/navigation
PATCH  /api/user/preferences/navigation

# Preference schema
class NavigationPreferences(BaseModel):
    sidebar_collapsed: bool = False
    default_view: str = "dashboard"
    recent_commands: List[str] = []
    favorite_pages: List[str] = []
    theme_overrides: Dict[str, Any] = {}
    mobile_nav_order: List[str] = []
```

### 2. Command Palette Search API

Implement intelligent search across multiple data types:

```python
POST /api/search/commands

# Request
{
    "query": "string",
    "context": "navigation|agents|knowledge|all",
    "limit": 20,
    "include_recent": true
}

# Response
{
    "results": [
        {
            "type": "navigation|action|agent|document",
            "title": "string",
            "subtitle": "string", 
            "icon": "string",
            "action": "navigate|execute|open",
            "data": {},
            "score": 0.95,
            "recent": true
        }
    ],
    "total": 42,
    "query_time_ms": 23
}
```

### 3. Navigation Analytics API

Track navigation patterns for optimization:

```python
POST /api/analytics/navigation/event

# Event schema
class NavigationEvent(BaseModel):
    event_type: Literal["page_view", "sidebar_toggle", "command_used", "search"]
    timestamp: datetime
    user_id: str
    session_id: str
    details: Dict[str, Any]
    
# Aggregation endpoints
GET /api/analytics/navigation/patterns
GET /api/analytics/navigation/popular-routes
GET /api/analytics/navigation/command-usage
```

### 4. Dynamic Navigation Configuration

Support dynamic menu items based on permissions/features:

```python
GET /api/navigation/menu

# Response
{
    "items": [
        {
            "id": "dashboard",
            "label": "Dashboard",
            "icon": "terminal",
            "route": "/dashboard",
            "permissions": ["read"],
            "badge": null,
            "children": []
        },
        {
            "id": "agents",
            "label": "Agents",
            "icon": "bot",
            "route": "/agents",
            "permissions": ["read", "execute"],
            "badge": { "count": 3, "type": "info" },
            "children": [...]
        }
    ],
    "shortcuts": [...],
    "recent": [...]
}
```

### 5. Search Indexing Service

Build efficient search index for command palette:

```python
class SearchIndexService:
    def __init__(self):
        self.redis_client = redis.Redis()
        
    async def index_navigation_items(self):
        """Index all navigable items for fast search"""
        
    async def index_agent_commands(self):
        """Index available agent commands"""
        
    async def index_recent_items(self, user_id: str):
        """Index user's recent activities"""
        
    async def fuzzy_search(self, query: str, limit: int = 20):
        """Perform fuzzy search across all indexed items"""
```

### 6. WebSocket Updates for Navigation State

Extend WebSocket to sync navigation state:

```python
# New WebSocket events
class NavigationWebSocketEvents:
    SIDEBAR_STATE_CHANGED = "navigation.sidebar_changed"
    ACTIVE_ROUTE_CHANGED = "navigation.route_changed"
    COMMAND_EXECUTED = "navigation.command_executed"
    PREFERENCES_UPDATED = "navigation.preferences_updated"
```

### 7. Performance Optimizations

#### Caching Strategy
```python
# Cache frequently accessed navigation data
@cache_result(ttl=300)  # 5 minutes
async def get_navigation_menu(user_id: str):
    ...

@cache_result(ttl=60)   # 1 minute
async def get_popular_commands(user_id: str):
    ...
```

#### Database Indexes
```sql
-- Add indexes for navigation analytics
CREATE INDEX idx_nav_events_user_timestamp ON navigation_events(user_id, timestamp);
CREATE INDEX idx_nav_events_type_timestamp ON navigation_events(event_type, timestamp);
CREATE INDEX idx_user_prefs_user_id ON user_preferences(user_id);
```

## Implementation Details

### 1. Database Schema

```sql
-- User navigation preferences
CREATE TABLE user_navigation_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL UNIQUE,
    preferences JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Navigation analytics events
CREATE TABLE navigation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Command palette usage
CREATE TABLE command_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    command VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    execution_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(command, user_id)
);
```

### 2. API Response Time Requirements

- Navigation menu: <50ms
- Command search: <100ms  
- Preference updates: <200ms
- Analytics events: Fire-and-forget (async)

### 3. Search Implementation

Use combination of:
- PostgreSQL full-text search for documents
- Redis for real-time command matching
- Fuzzy matching algorithm (Levenshtein distance)
- Weighted scoring based on:
  - Exact matches (1.0)
  - Prefix matches (0.8)
  - Fuzzy matches (0.6)
  - Recent usage (0.2 bonus)

## Testing Requirements

### 1. Unit Tests
- Search algorithm accuracy
- Preference persistence
- Analytics event processing
- WebSocket event handling

### 2. Integration Tests  
- Full search flow with multiple data types
- Preference sync across sessions
- Navigation menu generation with permissions

### 3. Performance Tests
- Search response time under load
- WebSocket broadcast latency
- Database query optimization

### 4. Load Tests
- 1000 concurrent search requests
- 10,000 navigation events/minute
- WebSocket with 500 connections

## Deliverables

1. **API Endpoints**: All navigation support endpoints
2. **Search Service**: Fast, fuzzy command palette search
3. **Analytics Pipeline**: Navigation tracking system
4. **WebSocket Events**: Real-time navigation updates
5. **Database Migrations**: Schema and indexes
6. **Tests**: Comprehensive test coverage
7. **Documentation**: API docs and integration guide

## Success Criteria

- [ ] All endpoints respond in under specified time limits
- [ ] Search returns relevant results with <100ms latency
- [ ] Analytics events process without blocking UI
- [ ] WebSocket updates work across multiple clients
- [ ] 95%+ test coverage on new code
- [ ] Zero data loss on preference updates

## Integration Notes

- Coordinate with CA on API contracts
- Ensure backward compatibility with existing systems
- Use existing Redis and WebSocket infrastructure
- Follow established error handling patterns
- Document all new endpoints in OpenAPI spec

## Priority Order

1. User preferences API (enables persistent state)
2. Navigation menu endpoint (core functionality)
3. Command search API (enhances UX)
4. WebSocket events (real-time sync)
5. Analytics (future optimization)

Begin with preferences API to unblock CA's state management needs.
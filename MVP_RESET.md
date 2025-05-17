# MVP Reset Plan

**Created**: May 17, 2025  
**Branch**: `mvp-reset`  
**Status**: Active Implementation Guide

## 🎯 MVP Goal (Focused)

**Email → PDF/URL → ContentMind → Summary → Digest → Email Response**

That's it. Nothing else until this works perfectly.

## ✅ What We Keep (Reuse)

- [ ] Email gateway (Gmail OAuth only)
- [ ] Agent base class
- [ ] Redis simulation (in-memory event queue)
- [ ] File upload scaffolding
- [ ] Database models
- [ ] API structure

## ❌ What We Ignore (For Now)

- WhatsApp integration
- Vector database (ChromaDB)
- MCP system
- Complex workflow engine
- Multiple LLM providers (use one)
- Advanced UI features

## 🏗️ What We Build/Fix

1. **End-to-end email flow**
   - Gmail OAuth authentication
   - Email polling with codeword filter
   - PDF attachment handling
   - URL extraction from email body

2. **ContentMind Agent (Simplified)**
   - PDF text extraction
   - URL content fetching
   - Basic summarization with one LLM
   - Error handling

3. **Knowledge Repository (Basic)**
   - PostgreSQL storage only
   - Simple document model
   - No vector embeddings yet

4. **Digest Generation**
   - Query recent summaries
   - Format as email-friendly text
   - Basic templating

5. **Email Response**
   - Reply to original thread
   - Include summary
   - Mark as processed

## 📋 Implementation Order

Following TASK_CARDS.md strictly:

1. TASK-005: Stabilize File Upload System
2. TASK-006: Implement ContentMind Agent  
3. TASK-007: Implement Knowledge Repository
4. TASK-008: Implement Email Gateway
5. TASK-009: Implement Digest Agent
6. TASK-010: Complete MVP Flow Integration

## 🔧 Technical Decisions

### Docker Setup
```yaml
services:
  api:
    build: .
    environment:
      - REDIS_MODE=simulation
      - LLM_PROVIDER=anthropic
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=bluelabel_aios
      - POSTGRES_USER=aios
      - POSTGRES_PASSWORD=aios123
```

### Configuration
```env
# MVP Configuration
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
ANTHROPIC_API_KEY=your_key

# Feature Flags (all false for MVP)
ENABLE_WHATSAPP=false
ENABLE_VECTOR_DB=false
ENABLE_MCP=false
ENABLE_WORKFLOW_ENGINE=false
```

### Code Structure
```
bluelabel-aios-v2/
├── apps/
│   └── api/            # Single API service
├── agents/             
│   ├── base.py         # Keep
│   └── content_mind.py # Simplify
├── services/
│   ├── gateway/        
│   │   └── gmail.py    # Focus here
│   ├── knowledge/      
│   │   └── repository.py # Basic version
│   └── storage/        
│       └── file.py     # Local/S3 only
└── tests/              # Test everything
```

## 🚀 Success Criteria

MVP is complete when:

1. User sends email with PDF to designated address
2. System detects codeword in subject/body
3. PDF is processed and summarized
4. Summary is stored in PostgreSQL
5. Digest email is sent back to user
6. Entire flow takes < 2 minutes

## 📝 Daily Progress Tracking

### Day 1 (Today)
- [ ] Create mvp-reset branch ✓
- [ ] Document reset plan ✓
- [ ] Archive old roadmaps
- [ ] Update README.md
- [ ] Start TASK-005

### Day 2-3
- [ ] Complete TASK-005 (File uploads)
- [ ] Complete TASK-006 (ContentMind)

### Day 4-5  
- [ ] Complete TASK-007 (Knowledge Repository)
- [ ] Complete TASK-008 (Email Gateway)

### Day 6-7
- [ ] Complete TASK-009 (Digest Agent)
- [ ] Complete TASK-010 (Integration)
- [ ] End-to-end testing

## Notes

- No new features until MVP works
- Test each component in isolation
- Document any deviations in architecture.md
- Keep TASK_CARDS.md updated with progress
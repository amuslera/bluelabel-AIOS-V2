# Bluelabel AIOS v2 - Task Cards (Improved)

## Overview
This roadmap contains all development tasks organized by phase and priority. Each task follows a standardized format with status tracking, tags, and explicit ordering.

## MVP Goal
**Initial MVP**: Process PDFs/URLs sent via email or WhatsApp → ContentMind agent processes → MCP system generates summary → Knowledge Repository stores → Digest returns via original channel

### Critical MVP Components:
1. **Email Gateway** (TASK-008) - Receive emails with attachments/URLs
2. **ContentMind Agent** (TASK-006) - Process PDFs and URLs
3. **Knowledge Repository** (TASK-007) - Store processed content
4. **Digest Agent** (TASK-009) - Generate summaries
5. **Email Response** (TASK-008) - Send summaries back
6. **Complete Integration** (TASK-010) - Wire everything together

### MVP Flow:
```
Email arrives → Gateway extracts content → ContentMind processes → 
Knowledge Repository stores → Digest Agent summarizes → Email response sent
```

## Task Format
```
### TASK-XXX: Task Title
**Status**: pending | in_progress | completed | cancelled  
**Tags**: #backend #frontend #database #testing #infrastructure  
**Order**: Sequential execution order  
**Priority**: Critical | High | Medium | Low  
**Phase**: Implementation phase number  
**Estimated Time**: Hours required  
**Dependencies**: Prerequisites tasks  

**Description**: Clear explanation of what needs to be done

**Acceptance Criteria**:
- [ ] Specific measurable outcomes
- [ ] Requirements for completion

**Technical Details**:
- Implementation specifics
- Technology choices
- Architecture decisions

**Known Issues** (if applicable):
- Current problems to solve
- Blockers to address
```

---

## Phase 1: Critical Foundation (Week 1)

### TASK-001: Implement Centralized Logging System
**Status**: completed ✓  
**Tags**: #backend #infrastructure #debugging  
**Order**: 1  
**Priority**: Critical  
**Phase**: 1  
**Estimated Time**: 4 hours  
**Dependencies**: None  

**Description**: Create a centralized logging system to help debug all other issues.

**Acceptance Criteria**:
- [x] All API endpoints log request/response with unique request ID
- [x] Errors include full stack traces and context
- [x] Logs are structured (JSON) for easy parsing
- [x] Log levels are configurable via environment variables
- [x] Logs are written to both console and file

**Technical Details**:
- Enhanced `core/logging_enhanced.py` with structured logging
- Added logging middleware to FastAPI
- Created JSON formatters for machine-readable logs
- Implemented correlation IDs for request tracking

---

### TASK-002: Debug API Startup Failures
**Status**: completed ✓  
**Tags**: #backend #api #bugfix  
**Order**: 2  
**Priority**: Critical  
**Phase**: 1  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-001  

**Description**: Fix API startup issues preventing the server from running properly.

**Acceptance Criteria**:
- [x] API starts without errors
- [x] All middleware loads correctly
- [x] Configuration validates on startup
- [x] Database connection established
- [x] Health check endpoint responds

**Technical Details**:
- Created minimal API in `apps/api/main_minimal.py`
- Fixed middleware configuration issues
- Added startup validation
- Implemented health check endpoint

---

### TASK-003: Execute Initial Database Migrations
**Status**: completed ✓  
**Tags**: #database #backend #infrastructure  
**Order**: 3  
**Priority**: Critical  
**Phase**: 1  
**Estimated Time**: 3 hours  
**Dependencies**: TASK-002  

**Description**: Create and execute the initial Alembic migration to set up database schema.

**Acceptance Criteria**:
- [x] Initial migration created with all tables
- [x] Migration runs without errors
- [x] Database schema matches models
- [x] SQLAlchemy metadata conflicts resolved

**Technical Details**:
- Fixed alembic configuration to import all models
- Resolved metadata naming conflicts
- Generated initial migration
- Tested migration execution

---

### TASK-004: Fix Frontend-Backend API Integration
**Status**: completed ✓  
**Tags**: #frontend #backend #api  
**Order**: 4  
**Priority**: High  
**Phase**: 1  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-002  

**Description**: Align API endpoints with frontend expectations and fix integration issues.

**Acceptance Criteria**:
- [x] All frontend API calls reach correct endpoints
- [x] CORS configured correctly
- [x] Authentication headers handled properly
- [x] Error responses match frontend expectations
- [x] API versioning consistent (v1)

**Technical Details**:
- Audited all API routes in frontend code
- Created integrated API with matching endpoints
- Configured CORS middleware properly
- Implemented consistent error response format
- Added request/response logging

**Resolution**:
- Created new integrated API in `main_integrated.py`
- Implemented mock routers for all expected endpoints
- Fixed CORS configuration for localhost:3000/3001
- Standardized response formats to match frontend interfaces
- Added request ID tracking and enhanced logging

---

### TASK-005: Stabilize File Upload System
**Status**: pending  
**Tags**: #backend #storage #api  
**Order**: 5  
**Priority**: High  
**Phase**: 1  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-001, TASK-002  

**Description**: Fix file upload flow to work with MinIO/S3 storage.

**Acceptance Criteria**:
- [ ] Presigned URLs generated correctly
- [ ] Files upload successfully to storage
- [ ] File metadata saved to database
- [ ] Download URLs work properly
- [ ] Error handling for large files

**Technical Details**:
- Fix MinIO client configuration
- Implement presigned URL generation
- Add file size and type validation
- Create file processing queue
- Add progress tracking

**Known Issues**:
- MinIO connection errors
- Presigned URL generation fails
- Missing S3 bucket configuration

---

## Phase 2: Core Workflow (Week 2)

### TASK-006: Implement ContentMind Agent
**Status**: Done ✓  
**Tags**: #backend #agents #ai  

**Completion Summary**: Implemented YAML-based prompt system for ContentMind agent with configurable templates, loader, and test suite. Supports multiple LLM configurations and includes error handling.
**Order**: 6  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-001, TASK-002  

**Description**: Create the ContentMind agent for processing PDFs and URLs.

**Acceptance Criteria**:
- [ ] Agent interface implementation complete
- [ ] PDF extraction working
- [ ] URL content extraction working
- [ ] Text summarization functional
- [ ] Integration with event bus

**Technical Details**:
- Implement base Agent interface
- Add PDF parsing capabilities
- Add URL scraping functionality
- Connect to LLM for summarization
- Handle error cases gracefully

---

### TASK-007: Implement Knowledge Repository
**Status**: pending  
**Tags**: #backend #database #storage  
**Order**: 7  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-003  

**Description**: Create knowledge repository for storing processed content.

**Acceptance Criteria**:
- [ ] PostgreSQL models created
- [ ] ChromaDB integration working
- [ ] Content storage functional
- [ ] Vector embeddings stored
- [ ] Retrieval methods implemented

**Technical Details**:
- Create knowledge models
- Implement storage service
- Add vector database integration
- Create search functionality
- Add content versioning

---

### TASK-008: Implement Email Gateway
**Status**: pending  
**Tags**: #backend #email #communication  
**Order**: 8  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-006, TASK-007  

**Description**: Create Gmail gateway for receiving and sending emails.

**Acceptance Criteria**:
- [ ] OAuth 2.0 authentication working
- [ ] Email polling functional
- [ ] [codeword] filtering implemented
- [ ] Attachment handling working
- [ ] Reply sending functional

**Technical Details**:
- Implement Gmail OAuth flow
- Create email polling service
- Handle PDF attachments
- Extract URLs from email body
- Send summary responses

---

### TASK-009: Implement Digest Agent
**Status**: pending  
**Tags**: #backend #agents  
**Order**: 9  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-007  

**Description**: Create digest agent for generating summaries from knowledge repository.

**Acceptance Criteria**:
- [ ] Aggregate knowledge entries
- [ ] Generate coherent summaries
- [ ] Format for email response
- [ ] Handle multiple content types
- [ ] Personalization support

**Technical Details**:
- Query knowledge repository
- Aggregate related content
- Generate digest with LLM
- Format for email delivery
- Add user preferences

---

### TASK-010: Complete MVP Flow Integration
**Status**: pending  
**Tags**: #backend #integration #mvp  
**Order**: 10  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 10 hours  
**Dependencies**: TASK-006 through TASK-009  

**Description**: Wire together the complete MVP flow from email to response.

**Acceptance Criteria**:
- [ ] Email triggers ContentMind processing
- [ ] ContentMind stores in Knowledge Repository
- [ ] Digest Agent generates summary
- [ ] Summary sent back via email
- [ ] End-to-end flow tested

**Technical Details**:
- Connect all components via event bus
- Implement workflow orchestration
- Add error handling and retries
- Create integration tests
- Document the complete flow

---

### TASK-011: Add System Health Monitoring
**Status**: In Progress: CC  
**Tags**: #backend #monitoring #infrastructure  
**Order**: 11  
**Priority**: High  
**Phase**: 2  
**Estimated Time**: 4 hours  
**Dependencies**: TASK-001  

**Description**: Create health check and monitoring endpoints.

**Acceptance Criteria**:
- [ ] `/health` endpoint returns system status
- [ ] Component health checks (DB, Redis, Storage)
- [ ] External service status (Gmail, LLMs)
- [ ] Response includes version and uptime
- [ ] Monitoring dashboard data available

**Technical Details**:
- Create health check service
- Add component status checks
- Implement timeout handling
- Return structured health data
- Add Prometheus metrics

---

## Phase 3: Testing Framework (Week 3)

### TASK-012: Reorganize Test Structure
**Status**: pending  
**Tags**: #testing #infrastructure  
**Order**: 12  
**Priority**: Medium  
**Phase**: 3  
**Estimated Time**: 6 hours  
**Dependencies**: None  

**Description**: Move tests from scripts/ to proper test structure.

**Acceptance Criteria**:
- [ ] All tests moved to tests/ directory
- [ ] Tests organized by type (unit/integration/e2e)
- [ ] Duplicate tests removed
- [ ] Test naming conventions applied
- [ ] README updated with test information

**Technical Details**:
- Create tests/ directory structure
- Move and rename test files
- Update import paths
- Remove obsolete tests
- Create test documentation

---

### TASK-013: Add Test Coverage Reporting
**Status**: In Progress: CA 🔄  
**Tags**: #testing #ci-cd  
**Order**: 9  
**Priority**: Medium  
**Phase**: 3  
**Estimated Time**: 3 hours  
**Dependencies**: TASK-008  

**Description**: Configure pytest coverage reporting.

**Acceptance Criteria**:
- [ ] Coverage reports generated on test runs
- [ ] HTML coverage reports available
- [ ] Coverage integrated with CI/CD
- [ ] Coverage badge in README
- [ ] Minimum coverage threshold enforced

**Technical Details**:
- Install pytest-cov
- Configure coverage settings
- Add coverage to test commands
- Create coverage scripts
- Set up coverage gates

---

### TASK-014: Create Test Fixtures and Mocks
**Status**: pending  
**Tags**: #testing #backend  
**Order**: 14  
**Priority**: Medium  
**Phase**: 3  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-012  

**Description**: Build comprehensive test fixtures and mocks.

**Acceptance Criteria**:
- [ ] Mock services for external APIs
- [ ] Sample data fixtures created
- [ ] Database test fixtures
- [ ] File upload test fixtures
- [ ] Authentication mocks

**Technical Details**:
- Create fixture factories
- Mock LLM providers
- Mock email services
- Create test data generators
- Document fixture usage

---

## Phase 4: Integration Testing (Week 4)

### TASK-015: Create E2E Test Suite
**Status**: pending  
**Tags**: #testing #e2e  
**Order**: 15  
**Priority**: High  
**Phase**: 4  
**Estimated Time**: 10 hours  
**Dependencies**: TASK-014  

**Description**: Build end-to-end tests for complete MVP flow.

**Acceptance Criteria**:
- [ ] Test email submission flow
- [ ] Test agent processing
- [ ] Test knowledge storage
- [ ] Test digest generation
- [ ] All tests run in CI/CD

**Technical Details**:
- Use pytest with async support
- Create test scenarios
- Mock external services
- Verify data flow
- Add performance checks

---

### TASK-016: API Contract Testing
**Status**: pending  
**Tags**: #testing #api  
**Order**: 16  
**Priority**: Medium  
**Phase**: 4  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-012  

**Description**: Validate all API endpoints with contract tests.

**Acceptance Criteria**:
- [ ] All endpoints have contract tests
- [ ] Request/response schemas validated
- [ ] Error scenarios tested
- [ ] API documentation generated
- [ ] Breaking changes detected

**Technical Details**:
- Use pytest with schemas
- Test all HTTP methods
- Validate response formats
- Check error handling
- Generate OpenAPI docs

---

### TASK-017: Performance Testing Setup
**Status**: pending  
**Tags**: #testing #performance  
**Order**: 17  
**Priority**: Low  
**Phase**: 4  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-015  

**Description**: Establish performance testing infrastructure.

**Acceptance Criteria**:
- [ ] Load testing scripts created
- [ ] Performance baselines established
- [ ] Bottlenecks identified
- [ ] Optimization recommendations
- [ ] Performance monitoring added

**Technical Details**:
- Use locust or k6
- Create test scenarios
- Measure response times
- Test concurrent users
- Profile database queries

---

## Additional Tasks (Phase 5+)

### TASK-018: Implement MCP Framework
**Status**: pending  
**Tags**: #backend #ai #agents  
**Order**: 18  
**Priority**: High  
**Phase**: 5  
**Estimated Time**: 12 hours  
**Dependencies**: TASK-006  

**Description**: Complete Multi-Component Prompting system for structured agent prompts.

**Acceptance Criteria**:
- [ ] MCP renderer working with templates
- [ ] Prompt caching implemented
- [ ] Component system functional
- [ ] Validation layer complete
- [ ] Integration with agents tested

---

### TASK-019: WhatsApp Integration
**Status**: pending  
**Tags**: #backend #communication  
**Order**: 19  
**Priority**: Medium  
**Phase**: 5  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-006  

**Description**: Add WhatsApp Business API integration for message processing.

**Acceptance Criteria**:
- [ ] WhatsApp webhook configured
- [ ] Message receiving working
- [ ] Media downloads functional
- [ ] Response sending implemented
- [ ] Error handling complete

---

## Quick Start Tasks (Immediate Relief)

### QUICK-001: Emergency API Fix
**Status**: completed ✓  
**Tags**: #backend #bugfix #urgent  
**Order**: 0.1  
**Priority**: URGENT  
**Phase**: 0  
**Estimated Time**: 2 hours  
**Dependencies**: None  

**Description**: Minimal fixes to get API running.

**Steps**:
1. Comment out problematic middleware
2. Add missing config properties with defaults
3. Use in-memory storage if DB fails
4. Create minimal health endpoint
5. Document temporary workarounds

---

## Task Execution Dashboard

### Currently Active
- TASK-005: Stabilize File Upload System (ready to start)

### Up Next (MVP Core)
1. TASK-006: Implement ContentMind Agent
2. TASK-007: Implement Knowledge Repository
3. TASK-008: Implement Email Gateway
4. TASK-009: Implement Digest Agent
5. TASK-010: Complete MVP Flow Integration

### Completed
- TASK-001: Implement Centralized Logging System ✓
- TASK-002: Debug API Startup Failures ✓
- TASK-003: Execute Initial Database Migrations ✓
- TASK-004: Fix Frontend-Backend API Integration ✓
- QUICK-001: Emergency API Fix ✓

### Progress Summary
- Phase 1: 4/5 tasks completed (80%)
- Phase 2: 0/6 tasks completed (0%) - MVP Core Components
- Phase 3: 0/3 tasks completed (0%) - Testing Framework
- Phase 4: 0/3 tasks completed (0%) - Integration Testing
- Phase 5: 0/2 tasks completed (0%) - Additional Features
- Overall: 4/19 core tasks completed (21%)

---

## Notes

### Benefits of This Format:
1. **Status Tracking**: Clear visibility of task progress
2. **Tags**: Easy filtering and categorization
3. **Order**: Explicit execution sequence
4. **Dashboard**: Quick progress overview
5. **Standardized**: Consistent format across all tasks

### Usage Guidelines:
- Update status field as work progresses
- Use tags to filter related tasks
- Follow order for sequential execution
- Check dependencies before starting tasks
- Update progress summary regularly
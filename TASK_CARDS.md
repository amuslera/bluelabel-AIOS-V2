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

### TASK-006: ContentMind Prompt System
**Status**: ✅ Done  
**Owner**: WA  
**Tags**: #backend #agents #ai  
**Order**: 6  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-001, TASK-002  
**Branch**: `feat/TASK-006-contentmind-prompt-core`  

**Description**: Implemented MCP-based prompt system using YAML templates.

**Completion Summary**: Implemented YAML-based prompt system for ContentMind agent with configurable templates, loader, and test suite. Supports multiple LLM configurations and includes error handling.

**Deliverables**:
- `summarization.yaml` template
- Loader implementation
- Validation system
- Test suite

**Acceptance Criteria**:
- [x] Agent interface implementation complete
- [x] PDF extraction working
- [x] URL content extraction working
- [x] Text summarization functional
- [x] Integration with event bus

**Technical Details**:
- Implement base Agent interface
- Add PDF parsing capabilities
- Add URL scraping functionality
- Connect to LLM for summarization
- Handle error cases gracefully

---

### TASK-007: Knowledge Repository
**Status**: ✅ Done  
**Owner**: CC  
**Tags**: #backend #database #storage  
**Order**: 7  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-003  
**Branch**: `feat/TASK-007-knowledge-repository`  

**Description**: Create knowledge repository for storing processed content.

**Completion Summary**: Designed PostgreSQL schema, implemented full CRUD service, created API endpoints.

**Deliverables**:
- PostgreSQL models
- Alembic migration
- Comprehensive test suite
- `TASK-007-SUMMARY.md` documentation

**Acceptance Criteria**:
- [x] PostgreSQL models created
- [ ] ChromaDB integration working (deferred to later)
- [x] Content storage functional
- [ ] Vector embeddings stored (deferred to later)
- [x] Retrieval methods implemented

**Technical Details**:
- Create knowledge models
- Implement storage service
- Add vector database integration
- Create search functionality
- Add content versioning

**Resolution**:
- Created comprehensive PostgreSQL models (knowledge_items, relationships, attachments)
- Implemented full CRUD service layer with advanced search capabilities
- Added MVP API endpoints for knowledge operations
- Created database migration for all tables
- Deferred vector/ChromaDB integration to post-MVP phase
- Full-text search implemented using PostgreSQL native capabilities

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
**Status**: completed ✓  
**Tags**: #backend #monitoring #infrastructure  
**Order**: 11  
**Priority**: High  
**Phase**: 2  
**Estimated Time**: 4 hours  
**Dependencies**: TASK-001  

**Description**: Create health check and monitoring endpoints.

**Acceptance Criteria**:
- [x] `/health` endpoint returns system status
- [x] Component health checks (DB, Redis, Storage)
- [x] External service status (Gmail, LLMs)
- [x] Response includes version and uptime
- [x] Monitoring dashboard data available

**Technical Details**:
- Create health check service
- Add component status checks
- Implement timeout handling
- Return structured health data
- Add Prometheus metrics

**Resolution**:
- Created `/health` endpoint with comprehensive system checks
- Added component health checks for database, Redis, storage, Gmail, and LLM
- Included system resource monitoring (CPU, memory, disk)
- Created simplified version for MVP without DB dependency
- Returns structured JSON data suitable for monitoring dashboards

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
**Status**: In Progress: WA  
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

### TASK-019: MCP Integration with ContentMind
**Status**: ✅ Done  
**Owner**: WA  
**Tags**: #backend #agents #ai  
**Order**: 19  
**Priority**: High  
**Phase**: 5  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-006  
**Branch**: `feat/TASK-019-contentmind-mcp-integration`  

**Description**: Integrated MCP with ContentMind agent and created adoption guide.

**Completion Summary**: Successfully integrated MCP framework with ContentMind agent, implemented prompt management system, and created comprehensive adoption documentation.

**Deliverables**:
- Prompt integration with ContentMind
- Fallback handling
- MCP adoption documentation

**Acceptance Criteria**:
- [x] MCP prompt system integrated
- [x] Fallback mechanism implemented
- [x] Error handling complete
- [x] Documentation created
- [x] Tests passing

---

### TASK-020: ContentMind Agent Tests + Fixes
**Status**: ✅ Done  
**Owner**: CA  
**Tags**: #backend #testing #integration  
**Order**: 20  
**Priority**: High  
**Phase**: 3  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-018  
**Branch**: `feat/TASK-020-contentmind-agent-tests`  

**Description**: Fixed prompt rendering bugs and added integration tests for error handling.

**Completion Summary**: Fixed critical slice error in prompt rendering, implemented empty content handling, and created comprehensive integration tests covering both success and error scenarios.

**Deliverables**:
- Fix for slice error in prompt rendering
- Empty content handling implementation  
- Success path integration tests
- Error path integration tests

**Acceptance Criteria**:
- [x] Integration tests cover successful content processing
- [x] Tests verify output structure and data types
- [x] Error handling scenarios are tested
- [x] Tests use mocked dependencies for LLM and MCP

**Technical Details**:
- Use pytest and pytest-asyncio for async testing
- Mock LLM router and MCP manager
- Test various content types and error scenarios

**Known Issues** (if applicable):
- None

---

### TASK-021: Digest Agent Implementation
**Status**: ✅ Done  
**Owner**: CC  
**Tags**: #backend #agents #mvp  
**Order**: 21  
**Priority**: Critical  
**Phase**: 2  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-007, TASK-019  
**Branch**: `feat/TASK-021-digest-agent`  

**Description**: Build a new DigestAgent that queries the Knowledge Repository and generates digests using MCP.

**Deliverables**:
- DigestAgent class using the shared Agent base
- MCP integration to load the digest prompt and inject summaries
- API endpoint at `/api/v1/digest/mvp/`
- JSON response structure with status, digest, summary_count, and timestamp

**Acceptance Criteria**:
- [ ] DigestAgent queries Knowledge Repository for summaries
- [ ] Loads and renders prompt using MCP (`digest_summary.yaml`)
- [ ] Returns structured digest response
- [ ] API endpoint functional at `/api/v1/digest/mvp/`
- [ ] Error handling returns appropriate error response
- [ ] Logging of input data and rendered output
- [ ] Basic test functions implemented

**Technical Details**:
- Query Knowledge Repository for `content_type = "summary"`
- Integrate with MCP for prompt rendering
- MVP-simple implementation (no email delivery, scheduling, or triggers)
- JSON response format specified in deliverables

---

### TASK-022: Create Test Suite for DigestAgent
**Status**: completed ✓  
**Tags**: #testing #backend #agents  
**Order**: 22  
**Priority**: High  
**Phase**: 3  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-008, TASK-010  
**Owner**: CA (Claude)

**Description**: Create comprehensive test suite for the DigestAgent.

**Acceptance Criteria**:
- [x] Unit tests for all agent methods
- [x] Integration tests with API endpoints
- [x] Mock LLM responses
- [x] Error handling coverage
- [x] Test fixtures created

**Technical Details**:
- Created test suite in `tests/integration/test_digest_agent.py`
- Added mock LLM router with realistic responses
- Implemented test fixtures for different content types
- Added validation for agent output structure
- Includes both agent and `/api/v1/digest/mvp/` endpoint implementation

**Implementation Notes**:
- Full MVP implementation completed including:
  - DigestAgent MVP class with Knowledge Repository integration
  - FastAPI router with request/response models
  - MCP-based digest generation
  - Comprehensive test coverage for both agent and API
  - Updated main.py with new router integration

---

### TASK-030: DigestAgent MVP Test Harness Fixes
**Status**: ✅ Done  
**Owner**: GPT-4 (AI Assistant)  
**Tags**: #backend #testing #agents  
**Order**: 30  
**Priority**: High  
**Phase**: 3  
**Estimated Time**: 2 hours  
**Dependencies**: TASK-021, TASK-022  
**Branch**: `fix/TASK-030-digestagent-test-harness`  

**Description**: Fix and validate the DigestAgentMVP test harness to ensure the agent is fully testable and produces valid output.

**Acceptance Criteria**:
- [x] Test harness runs without errors
- [x] AgentInput fields are correct
- [x] Mocks return objects with expected attributes
- [x] Digest output is valid JSON
- [x] Logging and capabilities output as expected

**Technical Details**:
- Added required `source` field to AgentInput
- Updated mock for knowledge_repo.list_content to return objects (MagicMock) with required attributes
- Ensured agent is initialized with all dependencies
- Fixed async/sync initialization call

**Completion Notes**:
This task documents the fixes and validation of the DigestAgentMVP test harness, ensuring the agent is fully testable and produces valid output.

- **AgentInput Construction:**
  - Added the required `source` field to the `AgentInput` instantiation in the test script.
- **Mock Structure:**
  - Updated the mock for `knowledge_repo.list_content` to return objects (using `MagicMock`) with the expected attributes (`id`, `title`, `source`, `text_content`, `summary`, `created_at`, `tags`), instead of plain dictionaries.
- **Initialization:**
  - Ensured the agent is initialized with all required dependencies (mocked knowledge repo, model router, and prompt manager).
- **Async/Sync Correction:**
  - Fixed the test to call `agent.initialize()` without `await`, as the method is synchronous.

**Confirmation:**
- The test script now runs successfully, and the agent returns a valid JSON output with the expected fields:
    - `status`
    - `digest`
    - `summary_count`
    - `timestamp`
- The script prints the digest, summary count, timestamp, and agent capabilities, confirming the agent logic, summary aggregation, and formatting all work as intended.

No further action required for fallback rendering or integration tests at this time. The core test harness is complete and validated. Future work may include integration tests with a real database or agent chaining.

**Status:**
✅ Complete

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
- None (Awaiting next task assignment)

### Up Next (MVP Core)
1. TASK-005: Stabilize File Upload System
2. TASK-008: Implement Email Gateway
3. TASK-009: Implement Digest Agent (now replaced by TASK-021)
4. TASK-010: Complete MVP Flow Integration

### Completed
- TASK-001: Implement Centralized Logging System ✓
- TASK-002: Debug API Startup Failures ✓
- TASK-003: Execute Initial Database Migrations ✓
- TASK-004: Fix Frontend-Backend API Integration ✓
- TASK-006: ContentMind Prompt System ✓ (Owner: WA)
- TASK-007: Knowledge Repository ✓ (Owner: CC)
- TASK-011: Add System Health Monitoring ✓
- TASK-019: MCP Integration with ContentMind ✓ (Owner: WA)
- TASK-020: ContentMind Agent Tests + Fixes ✓ (Owner: CA)
- TASK-021: Digest Agent Implementation ✓ (Owner: CC)
- QUICK-001: Emergency API Fix ✓

### Progress Summary
- Phase 1: 4/5 tasks completed (80%)
- Phase 2: 4/7 tasks completed (57%) - MVP Core Components
- Phase 3: 1/3 tasks completed (33%) - Testing Framework (TASK-020)
- Phase 4: 0/3 tasks completed (0%) - Integration Testing
- Phase 5: 1/2 tasks completed (50%) - Additional Features (TASK-019)
- Overall: 10/21 total tasks completed (48%)

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

---


### TASK-025: MVP Docs & Architecture Summary
**Status**: pending  
**Tags**: #documentation #readme #release  
**Order**: 25  
**Priority**: High  
**Phase**: 5  
**Estimated Time**: 4 hours  
**Dependencies**: TASK-021  

**Description**: Create MVP launch documentation, system diagrams, and onboarding notes.

**Acceptance Criteria**:
- [ ] MVP README created
- [ ] Architecture diagram drafted
- [ ] Summary of agents and API routes
- [ ] Developer onboarding section
- [ ] Released as part of /docs or repo root

---

### TASK-026: MCP Prompt Registry CLI
**Status**: ✅ Done  
**Tags**: #backend #cli #mcp  
**Order**: 26  
**Priority**: Medium  
**Phase**: 5  
**Estimated Time**: 5 hours  
**Dependencies**: TASK-006, TASK-019  
**Agent**: WA

**Description**: CLI tool to list all MCP prompt templates, required fields, and metadata.

**Deliverables**:
- `scripts/list_prompts.py` with:
  - `--summary`, `--verbose`, `--json` modes
  - Jinja2 field extraction
  - YAML structure parsing
- Graceful error handling
- Test cases:
  - Valid templates
  - Invalid YAML
  - Field extraction from Jinja2
  - Metadata parsing

**Completion Notes**:
- CLI tested with current `/prompts/`
- JSON output suitable for API/UI extension
- Fault-tolerant and extensible
- Ready for integration with other tools
- Added comprehensive test suite
- Supports both summary and detailed views
- Handles invalid YAML gracefully
- Extracts fields from both explicit declarations and Jinja2 templates

---

### TASK-027: Workflow Engine MVP
**Status**: pending  
**Tags**: #backend #workflow #orchestration  
**Order**: 27  
**Priority**: High  
**Phase**: 6  
**Estimated Time**: 10 hours  
**Dependencies**: TASK-010  

**Description**: Build a basic agent chaining engine to allow conditional multi-agent workflows.

**Acceptance Criteria**:
- [ ] Define minimal workflow schema
- [ ] Chain ContentMind → Digest
- [ ] Support input mapping between agents
- [ ] Implement simple orchestrator class
- [ ] Add tests and at least one example workflow

---

### TASK-028: LLM Router Layer
**Status**: pending  
**Tags**: #backend #ai #llm  
**Order**: 28  
**Priority**: Medium  
**Phase**: 6  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-006  

**Description**: Create router to choose among LLM providers (OpenAI, Anthropic, Ollama, etc).

**Acceptance Criteria**:
- [ ] Select LLM provider based on cost/priority
- [ ] Include fallback logic
- [ ] Log all decisions and failures
- [ ] Unit tests for routing logic
- [ ] Configurable routing policy

---

### TASK-029: ChromaDB Integration
**Status**: pending  
**Tags**: #database #semanticsearch #vector  
**Order**: 29  
**Priority**: Medium  
**Phase**: 6  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-007  

**Description**: Add semantic search layer to Knowledge Repository using ChromaDB.

**Acceptance Criteria**:
- [ ] Store vector embeddings from content
- [ ] Enable semantic query API
- [ ] Add similarity scoring
- [ ] Fallback to keyword search if unavailable
- [ ] Covered by tests and examples

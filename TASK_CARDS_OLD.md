# Bluelabel AIOS v2 - Task Cards

## Phase 1, Week 1: Critical Bug Fixes

### TASK-001: Implement Centralized Logging System
**Priority**: Critical  
**Estimated Time**: 4 hours  
**Dependencies**: None  

**Description**: Create a centralized logging system to help debug all other issues.

**Acceptance Criteria**:
- [ ] All API endpoints log request/response with unique request ID
- [ ] Errors include full stack traces and context
- [ ] Logs are structured (JSON) for easy parsing
- [ ] Log levels are configurable via environment variables
- [ ] Logs are written to both console and file

**Technical Details**:
- Enhance existing `core/logging.py`
- Add logging middleware to FastAPI
- Create log formatters for different environments
- Add correlation IDs to track requests across services

---

### TASK-002: Debug API Startup Failures
**Priority**: Critical  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-001  

**Description**: Fix API startup issues preventing the server from running properly.

**Acceptance Criteria**:
- [ ] API starts without errors
- [ ] All middleware loads correctly
- [ ] Configuration validates on startup
- [ ] Database connection established
- [ ] Health check endpoint responds

**Technical Details**:
- Debug FastAPI app initialization in `apps/api/main.py`
- Fix middleware configuration issues
- Validate all config properties exist
- Add startup event handlers for validation
- Create health check that verifies all services

**Known Issues**:
- `str object is not callable` middleware error
- Missing configuration properties
- Database connection failures

---

### TASK-003: Execute Initial Database Migrations
**Priority**: Critical  
**Estimated Time**: 3 hours  
**Dependencies**: TASK-002  

**Description**: Create and execute the initial Alembic migration to set up database schema.

**Acceptance Criteria**:
- [ ] Initial migration created with all tables
- [ ] Migration runs without errors
- [ ] Rollback tested and working
- [ ] Migration documented in MIGRATIONS.md
- [ ] Database schema matches models

**Technical Details**:
- Run `alembic revision --autogenerate -m "Initial schema"`
- Verify generated migration file
- Test migration with `alembic upgrade head`
- Test rollback with `alembic downgrade -1`
- Document migration procedures

---

### TASK-004: Fix Frontend-Backend API Integration
**Priority**: High  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-002  

**Description**: Align API endpoints with frontend expectations and fix integration issues.

**Acceptance Criteria**:
- [ ] All frontend API calls reach correct endpoints
- [ ] CORS configured correctly
- [ ] Authentication headers handled properly
- [ ] Error responses match frontend expectations
- [ ] API versioning consistent (v1)

**Technical Details**:
- Audit all API routes in frontend code
- Update backend routes to match
- Configure CORS middleware properly
- Implement consistent error response format
- Add request/response logging

**Known Issues**:
- Frontend expects `/api/v1/` prefix
- CORS errors on some endpoints
- Mismatched response formats

---

### TASK-005: Stabilize File Upload System
**Priority**: High  
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

## Phase 1, Week 2: Core Workflow Completion

### TASK-006: Implement Email Processing Flow
**Priority**: Critical  
**Estimated Time**: 10 hours  
**Dependencies**: TASK-001 through TASK-004  

**Description**: Complete the email → agent → knowledge → digest flow.

**Acceptance Criteria**:
- [ ] Gmail gateway fetches emails with [codeword]
- [ ] ContentMind agent processes email content
- [ ] Knowledge repository stores processed data
- [ ] Digest generated from stored knowledge
- [ ] Summary sent back via email

**Technical Details**:
- Wire up Gmail gateway with event bus
- Connect event handlers for email processing
- Implement knowledge repository storage
- Create digest generation logic
- Add email sending for responses

**Test Plan**:
1. Send test email with PDF attachment
2. Verify agent processes content
3. Check knowledge repository for stored data
4. Confirm digest email received

---

### TASK-007: Add System Health Monitoring
**Priority**: High  
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

## Phase 2, Week 3: Test Framework Setup

### TASK-008: Reorganize Test Structure
**Priority**: Medium  
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

### TASK-009: Add Test Coverage Reporting
**Priority**: Medium  
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

### TASK-010: Create Test Fixtures and Mocks
**Priority**: Medium  
**Estimated Time**: 8 hours  
**Dependencies**: TASK-008  

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

## Phase 2, Week 4: Integration Testing

### TASK-011: Create E2E Test Suite
**Priority**: High  
**Estimated Time**: 10 hours  
**Dependencies**: TASK-010  

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

### TASK-012: API Contract Testing
**Priority**: Medium  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-008  

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

### TASK-013: Performance Testing Setup
**Priority**: Low  
**Estimated Time**: 6 hours  
**Dependencies**: TASK-011  

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

## Quick Start Cards (Immediate Priority)

### QUICK-001: Emergency API Fix
**Priority**: URGENT  
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

### QUICK-002: Frontend Connection Test
**Priority**: URGENT  
**Estimated Time**: 1 hour  
**Dependencies**: QUICK-001  

**Description**: Verify frontend can connect to backend.

**Steps**:
1. Start API with minimal config
2. Start frontend dev server
3. Check browser console for errors
4. Test one API call
5. Document working configuration

---

### QUICK-003: Database Quick Setup
**Priority**: URGENT  
**Estimated Time**: 2 hours  
**Dependencies**: Docker running  

**Description**: Get database working minimally.

**Steps**:
1. Start PostgreSQL in Docker
2. Create database and user
3. Test connection string
4. Run one simple query
5. Document working setup

---

## Task Prioritization Guide

### Do First (This Week)
1. QUICK-001: Emergency API Fix
2. QUICK-002: Frontend Connection Test
3. QUICK-003: Database Quick Setup
4. TASK-001: Centralized Logging
5. TASK-002: Debug API Startup

### Do Next (Next Week)
1. TASK-003: Database Migrations
2. TASK-004: Frontend-Backend Integration
3. TASK-005: File Upload System
4. TASK-006: Email Processing Flow
5. TASK-007: Health Monitoring

### Do Later (Week 3+)
1. TASK-008: Test Structure
2. TASK-009: Coverage Reporting
3. TASK-010: Test Fixtures
4. TASK-011: E2E Tests
5. TASK-012: API Contract Tests

## Notes

- Each task can be discussed individually before implementation
- Tasks include specific acceptance criteria for clarity
- Dependencies are clearly marked to avoid blocking
- Quick fixes are provided for immediate relief
- Time estimates are conservative to account for unknowns
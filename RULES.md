# Bluelabel AIOS – Rules File

This file outlines architectural and operational principles for all agents, workflows, and services built within the Bluelabel AIOS platform.

## Core Rules

1. **User Scoping**
   - All content, uploads, and agent actions must be associated with a specific user or tenant.
   - Anonymous workflows are only allowed in designated sandbox flows.

2. **Traceability**
   - Every piece of processed content must link back to:
     - The original source (file, email, URL)
     - The time of ingestion
     - The processing agent(s)
     - The output record(s)

3. **Output Delivery**
   - All agents must define a default output method (e.g., email, WhatsApp, DB insert).
   - Outputs must be human-readable unless explicitly marked system-only.

4. **Workflow Orchestration**
   - Workflows must be event-driven and stateful.
   - Failures must be logged and retryable.
   - Workflow status must be queryable via API or dashboard.

5. **Observability**
   - All user-facing events (uploads, summaries, digests, replies) must emit an analytics event.
   - Logging must distinguish between system logs and user-level metrics.

6. **Security by Default**
   - No file, response, or internal endpoint should be exposed without authentication.
   - API routes must validate tenant permissions for every action.

7. **Extensibility**
   - New agents must conform to the platform's `Agent` interface.
   - New tools should follow the plugin pattern unless core to system function.

8. **Resilience**
   - All agents must support graceful failure and expose retry metadata.
   - External service failures must degrade functionally, not catastrophically.

9. **Versioning**
   - Agent logic and output formats must be versioned when changed.
   - Prompt templates must be tracked in version-controlled files.

10. **Fallbacks**
    - For each critical agent or integration, define a fallback or "safe mode" behavior.

11. **Idempotency**
    - All operations must be idempotent where possible
    - File uploads, agent executions, and API calls must handle duplicate requests gracefully
    - Use unique request IDs to prevent double-processing

12. **Resource Limits**
    - All file uploads must have size limits (configurable per tenant)
    - Agent processing must have timeout limits
    - API endpoints must implement rate limiting per user/tenant

13. **Data Retention**
    - Original files must have defined retention policies
    - Processed content must specify TTL for vector store entries
    - User data deletion must cascade through all systems (GDPR compliance)

14. **Cost Attribution**
    - LLM API calls must track token usage per tenant
    - Storage usage must be monitored per user
    - Processing costs must be attributable to specific operations

15. **Testing Requirements**
    - New agents must include unit tests with >80% coverage
    - Integration tests must cover happy path + error scenarios
    - Load testing required before production deployment

## Technical Implementation Rules

16. **Storage Hierarchy**
    - Original files: Object storage (R2/MinIO) with presigned URLs
    - Metadata: PostgreSQL with proper indexing
    - Vectors: Qdrant with tenant partitioning
    - Temporary: Redis with TTL

17. **Event Standards**
    - Events must follow CloudEvents specification
    - Event names must be namespaced: `aios.{service}.{action}`
    - Events must include correlation IDs for tracing

18. **Error Handling**
    - Transient errors: Exponential backoff with jitter
    - Permanent errors: Dead letter queue with alerting
    - User errors: Clear error messages with remediation steps

19. **API Conventions**
    - RESTful endpoints: `/api/v1/{resource}/{id}`
    - Batch operations: POST to `/api/v1/{resource}/batch`
    - Async operations: Return task IDs with status endpoints

20. **Agent Communication**
    - Inter-agent communication only via event bus
    - No direct agent-to-agent calls
    - Shared state only through knowledge repository

## Prompt Engineering Rules

21. **Prompt Management**
    - All prompts must be managed via MCP framework
    - Prompt changes require version bump
    - Production prompts must be tested against sample data

22. **Prompt Variables**
    - User-specific data must be injected via variables
    - System prompts must be separate from user content
    - Sensitive data must never be hardcoded in prompts

23. **Prompt Optimization**
    - Monitor token usage per prompt template
    - A/B test prompt variations for quality
    - Document prompt performance metrics

## Enforcement Strategy

1. **Code Reviews**: Check against rules file
2. **CI/CD Checks**: Automated rule validation
3. **Architecture Decision Records**: Document deviations
4. **Regular Audits**: Quarterly rule compliance review

## Last Updated: May 2025
## Description

Please include a summary of the changes and the related issue. List any dependencies required for this change.

Fixes # (issue)

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## 🔍 Architecture Review

**ALL PULL REQUESTS MUST COMPLY WITH [RULES.md](../RULES.md)**

### Core Rules Checklist
- [ ] User Scoping: All operations are associated with a user/tenant ID
- [ ] Traceability: Content links back to source, time, agent, and output
- [ ] Output Delivery: Agents define default output methods
- [ ] Workflow Orchestration: Changes are event-driven and stateful
- [ ] Observability: User-facing events emit analytics events
- [ ] Security: No unauthenticated endpoints or data exposure
- [ ] Extensibility: New agents conform to base Agent interface
- [ ] Resilience: Graceful failure with retry metadata
- [ ] Versioning: Agent logic and prompts are versioned
- [ ] Fallbacks: Critical paths have safe mode behavior

### Technical Implementation
- [ ] File uploads use presigned URLs with size limits
- [ ] Events follow CloudEvents spec with correlation IDs
- [ ] API endpoints follow RESTful conventions
- [ ] Errors use exponential backoff for transient failures
- [ ] LLM calls track token usage per tenant

### Testing Requirements
- [ ] Unit tests achieve >80% coverage
- [ ] Integration tests cover happy path + errors
- [ ] New agents include test fixtures
- [ ] API changes include OpenAPI documentation

### MCP/Prompt Management
- [ ] Prompts managed via MCP framework
- [ ] No hardcoded sensitive data in prompts
- [ ] Prompt changes increment version

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Checklist

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)

## Additional Notes
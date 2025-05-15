# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bluelabel AIOS (Agentic Intelligence Operating System) is a modular AI agent platform for automating knowledge work, originally built for Ariel Muslera (angel investor and solo GP). It's designed for internal use first, then to open selectively to founders, investors, and builders.

**Initial MVP**: Process PDFs/URLs sent via email or WhatsApp → ContentMind agent processes → MCP system generates summary → Knowledge Repository stores → Digest returns via original channel

## Development Commands

```bash
# Setup environment
./scripts/setup_basic.sh

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run API server
uvicorn apps.api.main:app --reload

# Alternative run script
./scripts/run_api.sh

# Run tests
pytest

# Code formatting/linting
black .
isort .
flake8

# Start Docker services
docker-compose up -d

# Database migrations
alembic upgrade head  # When implemented
```

## Architecture Overview

The system follows a modular monorepo structure with clear service boundaries:

```
bluelabel-aios-v2/
├── apps/           # API (FastAPI) and UI (React) entry points
├── agents/         # Agent implementations (ContentMind, Gateway, etc.)
├── services/       # Core services (MCP prompts, workflows, knowledge)
├── core/           # Shared core (events, config, auth)
├── shared/         # Schemas and utilities
├── tests/          # Unit, integration, E2E tests
└── docker/         # Docker configurations
```

### Key Architectural Components

1. **Agent System**: Base Agent interface with standardized AgentInput/AgentOutput
2. **Event Bus**: Redis Streams for event-driven communication (Kafka-ready)
3. **MCP Framework**: Multi-Component Prompting for structured prompt management
4. **Gateway Services**: Email (OAuth 2.0) and WhatsApp Business API integration
5. **Knowledge Repository**: PostgreSQL + ChromaDB for content storage
6. **Workflow Engine**: Multi-agent orchestration system

### Agent Interface Pattern

All agents must implement:
```python
class Agent(ABC):
    async def process(self, input: AgentInput) -> AgentOutput
    def get_capabilities(self) -> Dict[str, Any]
    async def initialize(self) -> bool
    async def shutdown(self) -> bool
```

### Event Format

Standard event format:
```python
class Event(BaseModel):
    metadata: EventMetadata  # event_id, type, timestamp, tenant_id
    payload: Dict[str, Any]
```

## Configuration Strategy

Configuration is managed through:
- `.env` files (see `.env.example`)
- Pydantic settings for validation
- Per-tenant overrides where applicable
- Support for secrets managers in production

## Testing Strategy

- **Unit Tests**: Test components in isolation
- **Integration Tests**: Test service interactions
- **E2E Tests**: Test complete user flows
- Focus on mocking external dependencies (LLMs, email, WhatsApp)

## Git Workflow

- Feature branches for development
- Comprehensive tests required for PRs
- Follow conventional commit messages
- Run formatters/linters before committing

## Security Considerations

- OAuth 2.0 for email authentication
- Tenant isolation from day one
- No hardcoding of secrets/keys
- Input validation on all endpoints
- Use environment variables for sensitive data

## Development Tips

1. Start with the Agent base class when creating new agents
2. Use the Event Bus for all inter-service communication
3. Implement comprehensive error handling
4. Use dependency injection patterns
5. Write tests alongside implementation
6. Document API endpoints with OpenAPI

## Current Implementation Status

- Phase 0: Project Foundation ✓
- Phase 1: Core Framework (MVP) - In Progress
  - Base Agent interface
  - Event Bus implementation
  - API service foundation
- Phase 2: Communication Channels - Upcoming
- Phase 3: Content Processing - Upcoming
- Phase 4: LLM Integration - Upcoming

## Quick Reference

- **Main API**: `http://localhost:8000`
- **Redis**: `localhost:6379`
- **PostgreSQL**: `localhost:5432`
- **ChromaDB**: `localhost:8000` (when running)
- **Logs**: `logs/` directory
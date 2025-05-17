# Bluelabel AIOS v2

**Version:** `bluelabel-aios-v2-alpha`  
**Status:** MVP Development (Phase 1)  
**Author:** Ariel Muslera / Bluelabel Ventures

## 🎯 Project Focus

Bluelabel AIOS (Agentic Intelligence Operating System) is a modular AI agent platform for automating knowledge work. Originally built for Ariel Muslera (angel investor and solo GP), it will eventually support founders, investors, and builders.

**Current MVP Goal**: Email → PDF/URL → AI Summary → Email Response

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository_url>
   cd bluelabel-aios-v2
   git checkout mvp-reset  # Use MVP-focused branch
   ./scripts/setup_basic.sh
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with:
   # - GMAIL_CLIENT_ID
   # - GMAIL_CLIENT_SECRET  
   # - ANTHROPIC_API_KEY (or OPENAI_API_KEY)
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ./scripts/run_integrated_api.sh
   ```

4. **Test the MVP flow**:
   ```bash
   # Send test email with PDF
   python scripts/test_mvp_flow.py
   ```

## 📋 Development Roadmap

All tasks are tracked in [`TASK_CARDS.md`](./TASK_CARDS.md)

**Current Phase 1 Tasks**:
- [x] TASK-001: Centralized Logging ✓
- [x] TASK-002: Debug API Startup ✓
- [x] TASK-003: Database Migrations ✓
- [x] TASK-004: Frontend-Backend Integration ✓
- [ ] TASK-005: File Upload System (current)
- [ ] TASK-006: ContentMind Agent
- [ ] TASK-007: Knowledge Repository
- [ ] TASK-008: Email Gateway
- [ ] TASK-009: Digest Agent
- [ ] TASK-010: MVP Integration

## 🏗️ Architecture

```
Email (Gmail) → Gateway → ContentMind → Knowledge Repo → Digest → Email Reply
```

For full architecture details, see [`architecture.md`](./architecture.md)

## 📁 Project Structure

```
bluelabel-aios-v2/
├── apps/               # Applications (API, UI)
├── agents/             # AI agent implementations
├── services/           # Core services (gateway, knowledge, storage)
├── core/              # Shared utilities (config, logging, events)
├── tests/             # Test suites
├── scripts/           # Development scripts
└── docs/              # Documentation
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run specific MVP test
python scripts/test_mvp_flow.py
```

## 🔧 Development

1. **Follow task cards**: Use [`TASK_CARDS.md`](./TASK_CARDS.md) for all work
2. **Update progress**: Mark tasks complete as you finish
3. **Test everything**: Each component should have tests
4. **Document changes**: Update CHANGELOG.md

## 📚 Documentation

- [`MVP_RESET.md`](./MVP_RESET.md) - Current MVP implementation plan
- [`TASK_CARDS.md`](./TASK_CARDS.md) - All development tasks
- [`architecture.md`](./architecture.md) - System architecture
- [`CLAUDE.md`](./CLAUDE.md) - AI assistant guidance

## ⚠️ Important Notes

- This is an MVP reset focused on one flow: Email → Summary → Reply
- Advanced features (WhatsApp, vector DB, complex workflows) are deferred
- Using simulation mode for Redis, single LLM provider
- Docker-based development environment

## 📧 Support

For questions about the project, contact Ariel Muslera.
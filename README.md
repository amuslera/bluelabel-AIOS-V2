# Bluelabel AIOS v2 - MVP Implementation

**Version:** `bluelabel-aios-v2-mvp`  
**Status:** Active Development  
**Branch:** `mvp-reset`  

## 🎯 Project Overview

Bluelabel AIOS (Agentic Intelligence Operating System) is a modular AI agent platform for automating knowledge work. This MVP implementation focuses on a single, hardened flow to prove the core concept.

## 📊 MVP Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│   Gmail     │────▶│   Gateway    │────▶│ ContentMind  │────▶│  Knowledge   │────▶│   Gmail     │
│   Inbox     │     │    Agent     │     │    Agent     │     │  Repository  │     │   Reply     │
└─────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
     Email               Extract             Process             Store              Send Digest
   with PDF             Content              & Summarize         Summary
```

### MVP Flow
1. **Email Ingestion**: User sends email with PDF attachment to designated Gmail address
2. **Content Extraction**: Gateway agent extracts PDF and triggers processing
3. **AI Processing**: ContentMind agent analyzes and summarizes the document
4. **Storage**: Summary stored in PostgreSQL knowledge repository  
5. **Digest Creation**: Digest agent creates formatted summary
6. **Email Response**: Summary sent back via Gmail to original sender

## 🤖 AI Team Structure

Our development is driven by an AI-first team:

| Role | Agent | Responsibilities |
|------|-------|-----------------|
| **Systems Architect** | ChatGPT (Arch) | Maintains roadmap, coordinates team |
| **Lead Developer** | Claude Code (CC) | Implements tasks from task cards |
| **Dev Assistant** | Cursor AI (CA) | Refactors code, scaffolds boilerplate |
| **Prompt Engineer** | Windsurf AI (WA) | Develops prompts, handles LLM config |
| **Reviewer Agent** | Anthropic AI (RA) | Reviews code, ensures quality |
| **Product Manager** | Human (PM) | Sets direction, approves scope |

See [`team_structure.md`](./team_structure.md) for detailed roles and responsibilities.

## 🚀 Quick Start

1. **Clone repository**:
   ```bash
   git clone <repository>
   cd bluelabel-aios-v2
   git checkout mvp-reset
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Add required keys:
   # - GMAIL_CLIENT_ID
   # - GMAIL_CLIENT_SECRET
   # - ANTHROPIC_API_KEY
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ./scripts/run_api.sh
   ```

## 📋 Development Plan

All development tasks are tracked in [`TASK_CARDS.md`](./TASK_CARDS.md).

Current focus areas:
- Phase 1: Critical foundation (80% complete)
- Phase 2: MVP core workflow (starting)
- Phase 3: Testing framework (planned)

## 🏗️ Technical Stack

- **Backend**: Python/FastAPI
- **Database**: PostgreSQL  
- **Queue**: Redis (simulated in MVP)
- **AI/LLM**: Anthropic Claude
- **Email**: Gmail API with OAuth 2.0
- **Storage**: Local filesystem (S3 compatible)

## 📁 Repository Structure

```
bluelabel-aios-v2/
├── apps/               # Applications
│   └── api/           # FastAPI backend
├── agents/            # Agent implementations
├── services/          # Core services
├── core/             # Shared utilities
├── tests/            # Test suites
├── scripts/          # Dev scripts
└── docs/             # Documentation
```

## 🔗 Key Documentation

- [`TASK_CARDS.md`](./TASK_CARDS.md) - Primary execution roadmap
- [`MVP_RESET.md`](./MVP_RESET.md) - MVP implementation strategy
- [`team_structure.md`](./team_structure.md) - AI team organization
- [`architecture.md`](./architecture.md) - Long-term system design

## ⚠️ MVP Limitations

This MVP implementation intentionally excludes:
- WhatsApp integration
- Vector databases
- Complex UI
- Multi-provider LLM routing
- Advanced workflow orchestration

These features are planned for post-MVP phases.
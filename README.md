# Bluelabel AIOS v2

**Version:** `bluelabel-aios-v2-alpha`  
**Status:** In Development (Official Implementation Plan – May 2025)  
**Author:** Ariel Muslera / Bluelabel Ventures

Bluelabel AIOS (Agentic Intelligence Operating System) is a modular AI agent platform originally built to support the workflows of Ariel Muslera, an angel investor and solo GP. It is designed to scale personal productivity and decision-making using composable AI agents. The system is intended for internal use first, and then will open up to select founders, investors, and builders.

Bluelabel AIOS is a platform for developing, deploying, and orchestrating modular AI agents. It supports content processing, research, knowledge management, and workflow automation using both local and cloud-based LLMs.


---

## 🚀 Initial MVP: Digest via Email

1. User sends a PDF or URL via email or WhatsApp  
2. The **Gateway Agent** receives and parses the content  
3. The **ContentMind Agent** processes and summarizes it via MCP (Multi-Component Prompting)  
4. Output is stored in the **Knowledge Repository**  
5. A summary digest is sent back via the original channel

---

## 🧱 Architecture Overview

- **Frontend:** React (web), React Native (mobile – planned)
- **Backend:** Python 3.10+ with FastAPI
- **Storage:** PostgreSQL, ChromaDB (vector), file storage
- **Event Bus:** Redis Streams (Kafka-ready)
- **LLM Router:** OpenAI, Anthropic, Ollama
- **Prompt Engine:** MCP (templated, versioned)
- **Containerization:** Docker (Kubernetes-ready)
- **Observability:** Prometheus, Grafana, OpenTelemetry

📊 [See Full Architecture Diagram](docs/assets/architecture.png)

---

## 🗂 Repository Structure

```txt
bluelabel-aios-v2/
├── apps/                 # API and UI entry points
├── agents/               # Agent implementations (e.g., ContentMind)
├── services/             # Core platform services (MCP, gateway, workflows)
├── core/                 # Shared logic (auth, config, messaging, etc.)
├── shared/               # Schemas, utils, cross-cutting concerns
├── ui/                   # React component system and design tokens
├── tests/                # Unit, integration, and e2e tests
├── docker/               # Docker and orchestration files
├── scripts/              # Setup and dev tooling
└── README.md             # This file
```

---

## 🧩 Core System Components

| Component         | Description |
|------------------|-------------|
| **Agent Runtime**     | Unified agent interface, lifecycle, and tool registry |
| **MCP Framework**     | Prompt component system with validation and templating |
| **Workflow Engine**   | Conditional, multi-step task orchestration |
| **LLM Router**        | Smart routing and fallback for OpenAI, Anthropic, Ollama |
| **Gateway Agents**    | Interfaces with email and WhatsApp channels |
| **Knowledge Store**   | Content storage, semantic tagging, and retrieval |
| **Event Bus**         | Redis Streams-based messaging (Kafka-compatible) |

---

## 📅 Current Implementation Plan

### ✅ Phase 0: Project Foundation
- [x] Project structure & monorepo
- [x] CI/CD setup (GitHub Actions)
- [x] Dockerized dev environment
- [ ] Base Agent interface
- [ ] Redis event bus

### 🏗️ Phase 1: Core Framework (MVP)
- [ ] `ContentMind` Agent
- [ ] Email Gateway with OAuth
- [ ] Knowledge Repository (PostgreSQL + Chroma)
- [ ] End-to-end test: Email → Digest → Email

_See full roadmap in [architecture.md](docs/architecture.md)_

---

## 👥 Contributing

Bluelabel AIOS is currently in its alpha phase. If you're interested in contributing, please reach out via [email] or [Telegram]. Contribution guidelines and roadmap will be added soon.

---

## 📄 License

MIT License  
© 2025 Ariel Muslera / Bluelabel Ventures

# Bluelabel AIOS V2

**Version:** `bluelabel-aios-v2-alpha`  
**Status:** In development (official implementation plan as of May 2025)

Bluelabel AIOS (Agentic Intelligence Operating System) is a platform for developing, deploying, and orchestrating modular AI agents. It supports content processing, research, knowledge management, and workflow automation using both local and cloud-based LLMs.

---

## 🚀 Initial MVP Use Case

Submit a URL or PDF via email →  
Process it through the `ContentMind` agent →  
Summarize it using the MCP framework →  
Store in knowledge base →  
Send digest via email.

---

## 🧱 Architecture Overview

- **Backend:** Python (FastAPI)
- **Frontend:** React (web), React Native (mobile) _(planned)_
- **Database:** PostgreSQL + ChromaDB
- **Event Bus:** Redis Streams (Kafka-ready)
- **LLMs:** OpenAI, Anthropic, Ollama (via unified router)
- **Prompt System:** MCP (Multi-Component Prompting)
- **Deployment:** Docker (Kubernetes-ready)

![Architecture Diagram](docs/assets/architecture.png)

---

## 🗂 Repo Structure

```
bluelabel-aios-v2/
├── apps/                 # API and UI entry points
├── agents/               # AI agents (ContentMind, Researcher, etc.)
├── services/             # Core services (MCP, gateway, workflow, etc.)
├── core/                 # Shared logic (auth, config, telemetry, etc.)
├── shared/               # Common models, schemas, utilities
├── tests/                # Unit, integration, e2e tests
├── docker/               # Container setup
├── scripts/              # Dev tools
└── README.md             # You're here
```

---

## 🧩 Key Components

| Component        | Description |
|------------------|-------------|
| **Agent Interface** | Unified lifecycle, tool access, and execution model |
| **MCP System**       | Structured prompt component engine with templating |
| **Workflow Engine**  | Multi-agent task orchestration with triggers and conditionals |
| **Model Router**     | Unified access to OpenAI, Anthropic, Ollama |
| **Email Gateway**    | Email-to-agent routing and delivery system |

---

## ✅ Immediate Roadmap

1. Scaffold project structure and CI/CD
2. Implement `ContentMind` agent and Gateway
3. Set up Redis Streams for event passing
4. Build the knowledge store with Chroma
5. Deliver first end-to-end MVP: email → digest

---

## 📄 License

MIT © 2025 Ariel Muslera / Bluelabel Ventures


# Bluelabel AIOS v2

**Version:** `bluelabel-aios-v2-alpha`  
**Status:** In Development (Official Implementation Plan – May 2025)  
**Author:** Ariel Muslera / Bluelabel Ventures

Bluelabel AIOS (Agentic Intelligence Operating System) is a modular AI agent platform originally built to support the workflows of Ariel Muslera, an angel investor and solo GP. It is designed to scale personal productivity and decision-making using composable AI agents. The system is intended for internal use first, and then will open up to select founders, investors, and builders.

Bluelabel AIOS is a platform for developing, deploying, and orchestrating modular AI agents. It supports content processing, research, knowledge management, and workflow automation using both local and cloud-based LLMs.


---

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository_url>
   cd bluelabel-aios-v2
   ./scripts/setup_basic.sh
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - OPENAI_API_KEY
   # - ANTHROPIC_API_KEY (optional)
   # - GOOGLE_GENERATIVEAI_API_KEY (optional)
   # - Google OAuth credentials
   ```

3. **Start the API server**:
   ```bash
   ./scripts/run_api.sh
   ```

4. **Test the system**:
   ```bash
   # In another terminal
   python scripts/test_full_integration.py
   ```

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

## ✅ Current Status (May 2025)

### Completed Components
- **Core Framework**: Event Bus, Configuration, Logging
- **API Service**: FastAPI server with comprehensive endpoints
- **LLM Integration**: Multi-provider support (OpenAI, Anthropic, Gemini, Ollama) with smart routing
- **Gmail OAuth**: Full OAuth 2.0 implementation with complete authentication flow
- **Knowledge Repository**: In-memory + file storage with search capabilities
- **MCP Framework**: Complete prompt management system
- **ContentMind Agent**: Full implementation with real LLM processing
- **Workflow Engine**: Async execution with persistence and monitoring
- **Integration Testing**: End-to-end tests with real services working

### Latest Updates (May 16, 2025)
- ✅ **Real LLM Integration**: ContentMind now uses actual AI models (tested with Anthropic & OpenAI)
- ✅ **Gmail Authentication**: Successfully connected to a@bluelabel.ventures via OAuth
- ✅ **Full MVP Demo**: Email → AI Processing → Knowledge Storage → Summary generation
- ✅ **Stable API Server**: Running with proper background execution
- ✅ **Email Filtering**: Only emails with [codeword] in subject are processed
- ✅ **Ollama Support**: Added local LLM support for offline processing
- ✅ **Production-Ready**: All external integrations tested and working

### In Progress
- Frontend UI (React)
- WhatsApp Business API integration
- Additional agents (ContextMind, WebFetcher)
- PostgreSQL migration (currently using in-memory storage)

### Ready for Production Testing
The system is now fully functional with real API integrations:
```bash
# Start API server (runs in background)
cd bluelabel-aios-v2
source .venv/bin/activate
PYTHONPATH=. nohup uvicorn apps.api.main:app --reload > api.log 2>&1 &

# Test email processing
python3 test_email_flow_final.py

# Test LLM processing
python3 test_llm_processing.py
```

### Configuration
Ensure these environment variables are set in `.env`:
```
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GOOGLE_GENERATIVEAI_API_KEY=your_key
GOOGLE_CLIENT_ID=your_oauth_client_id
GOOGLE_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8081/gateway/google/callback
GMAIL_TOKEN_FILE=data/gmail_token.json
EMAIL_TRIGGER_CODEWORD=process
OLLAMA_API_BASE=http://localhost:11434
```

### Email Processing Filter
The system now filters incoming emails to avoid processing all messages automatically. Only emails containing a specific codeword in square brackets in the subject line will be processed.

Example:
- ✅ Processed: "Please analyze this document [process]"
- ❌ Skipped: "Regular email without codeword"
- ✅ Processed: "[process] Check this article"

The default codeword is "process" but can be configured via the `EMAIL_TRIGGER_CODEWORD` environment variable.

### Local LLM with Ollama
To use local LLM processing with Ollama:

```bash
# Install and setup Ollama
./scripts/setup_ollama.sh

# The script will:
# - Install Ollama (macOS/Linux)
# - Start the Ollama service
# - Pull recommended models (llama3, mistral, codellama)

# Test Ollama is working
curl http://localhost:11434/api/generate -d '{"model": "llama3", "prompt": "Hello"}'
```

Ollama is automatically detected and used as the primary provider when available, providing fast local LLM processing without API keys.

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
- [x] Base Agent interface
- [x] Redis event bus (with simulation mode)
- [x] Structured logging system
- [x] Development environment setup scripts

### 🏗️ Phase 1: Core Framework (MVP) - In Progress
- [x] Agent Runtime Manager
- [x] Basic API service endpoints
- [x] `ContentMind` Agent
- [x] Email Gateway with Gmail OAuth 2.0
- [ ] Knowledge Repository (PostgreSQL + Chroma)
- [ ] End-to-end test: Email → Digest → Email

_See full roadmap in [architecture.md](docs/architecture.md)_

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Git
- Virtual environment support
- (Optional) Docker, Redis, PostgreSQL

### Development Setup

```bash
# Clone the repository
git clone https://github.com/bluelabel/aios-v2.git
cd bluelabel-aios-v2

# Run complete development setup
./setup_dev.sh

# Or manually:
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Start the API server
python3 scripts/run_with_logging.py
# Or: uvicorn apps.api.main:app --reload
```

### Verify Your Setup

```bash
# Check if everything is configured correctly
python3 scripts/verify_setup.py

# Quick environment check
./scripts/check_dev_tools.sh
```

### Access the API

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Logs: `logs/bluelabel_aios.log`

### Environment Configuration

The system uses `.env` for configuration. Key settings:

```bash
# Enable Redis simulation (no Redis required)
REDIS_SIMULATION_MODE=true

# Set logging level
LOG_LEVEL=INFO

# Enable debug mode
API_DEBUG=true

# Optional: Configure LLM providers
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

---

## 👥 Contributing

Bluelabel AIOS is currently in its alpha phase. If you're interested in contributing, please reach out via [email] or [Telegram]. Contribution guidelines and roadmap will be added soon.

---

## 📄 License

MIT License  
© 2025 Ariel Muslera / Bluelabel Ventures

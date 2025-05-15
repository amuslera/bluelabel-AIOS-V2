# Bluelabel AIOS v2: High-Level Technical Overview

**Project Name:** Bluelabel AIOS v2  
**Version:** `v2-alpha`  
**Lead:** Ariel Muslera  
**Status:** Official implementation plan (May 2025)

---

## 🎯 Why This Exists: Context & Audience

Bluelabel AIOS is being built as a personal productivity platform for Ariel Muslera — an angel investor and solo GP — to automate and scale his research, portfolio monitoring, and knowledge workflows.

Once the system proves valuable for personal use, it will be opened selectively to:
- Founders from Ariel’s portfolio
- Other early-stage investors and solo GPs
- Builders and domain experts seeking AI-powered research copilots

The aim is to create **a composable agent system for intelligent information workflows**, starting small and iterating with real-world feedback.

---

## 🧠 What Are We Building?

Bluelabel AIOS (Agentic Intelligence Operating System) is a modular AI infrastructure for developing and orchestrating autonomous agents that perform knowledge-intensive tasks. These agents interact via an event-driven system, communicate through natural channels like email and WhatsApp, and generate personalized outputs (e.g., digests, research, insights) using both local and cloud-based LLMs.

---

## 🚀 First Use Case: Digest via Email or WhatsApp

1. User sends a URL or PDF via email or WhatsApp  
2. The **Gateway Agent** parses the content  
3. The **ContentMind Agent** summarizes it using the MCP (Multi-Component Prompting) system  
4. Output is stored in the **Knowledge Repository**  
5. A digest is returned to the user via the original channel

---

## 🧩 Core Architecture

- **Agent Runtime Layer** – Manages agent lifecycles, tooling, and task execution  
- **Core Services** – Content processing, prompt rendering, workflows, and knowledge management  
- **Event Bus** – Redis Streams for now, Kafka-ready  
- **Communication Gateways** – Email + WhatsApp (OAuth-secured)  
- **Knowledge Repository** – PostgreSQL + ChromaDB  
- **Frontend** – React (web), React Native (planned)  
- **Monitoring** – Prometheus, Grafana, OpenTelemetry

---

## 🧱 Design Principles

- Modular, monorepo-first architecture  
- API-first: all functionality exposed through REST  
- Agents built to be composable and testable  
- Prompt logic treated as versioned code  
- Security and multi-tenancy from day one  
- Use cases first, scalability later

---

## 🗂 Repo Structure (Simplified)

```
bluelabel-aios-v2/
├── apps/        # API and UI entry points
├── agents/      # Agent implementations
├── services/    # Core systems (mcp, workflows, etc.)
├── core/        # Messaging, config, auth
├── shared/      # Schemas, utils, cross-service logic
├── tests/       # Unit, integration, e2e
├── docs/        # Architecture + onboarding
└── README.md
```

---

## 👣 Getting Started

1. Read `architecture.md`  
2. Familiarize with `Agent` base class and event structure  
3. Follow `README.md` for project setup  
4. Join an implementation track:
   - Agent logic
   - Service integration
   - Prompt tooling
   - UI/API dev

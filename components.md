# Bluelabel AIOS v2: Component Glossary

Quick reference for key concepts in the architecture.

---

## Agents

Modular workers that process tasks. All agents extend from the `Agent` base class and support:
- Initialization
- Tool registration
- `.process(input)` method
- Capability introspection

Examples:
- `ContentMindAgent`
- `ResearcherAgent`
- `DigestAgent`

---

## MCP (Multi-Component Prompting)

Prompt management system:
- Templates with variables (`{{content}}`, `{{summary}}`)
- Supports versioning, tags, and tests
- Core for LLM-driven workflows

---

## Gateway Agent

Entry point for user messages via email or WhatsApp.
- Parses messages into standardized events
- Routes to the correct agent/task pipeline

---

## Event Bus

Redis Streams handles async event flow between agents and services.
- Follows a `metadata + payload` structure
- Kafka-compatible design

---

## Workflow Engine

Coordinates multi-agent flows.
- Steps with inputs, outputs, conditions
- Future support for branching, retries, DAGs

---

## Model Router

Selects LLM backend (OpenAI, Anthropic, Ollama) based on:
- Task type
- Availability
- User or tenant preferences


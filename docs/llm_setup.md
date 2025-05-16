# LLM Integration Setup Guide

## Prerequisites

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Anthropic API Key** (optional): Get from [Anthropic Console](https://console.anthropic.com/)
3. **Ollama** (optional): Install locally from [ollama.ai](https://ollama.ai/)

## Setup Steps

### 1. Set Environment Variables

Add your API keys to `.env`:

```bash
# Copy example env file if you haven't already
cp .env.example .env

# Edit .env and add your actual API keys
OPENAI_API_KEY=sk-...your-actual-key...
ANTHROPIC_API_KEY=sk-ant-...your-actual-key... (optional)
```

### 2. Test the LLM Integration

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the test
python scripts/test_llm_router.py
```

### 3. Using the LLM Router

The Model Router provides a unified interface for multiple LLM providers:

```python
from services.model_router.factory import create_default_router
from services.model_router.base import LLMMessage

# Create router
router = await create_default_router()

# Simple completion
response = await router.complete("What is the capital of France?")
print(response.text)

# Chat with conversation history
messages = [
    LLMMessage(role="system", content="You are a helpful assistant."),
    LLMMessage(role="user", content="Hello!")
]
response = await router.chat(messages)
print(response.text)

# Generate embeddings
embedding = await router.embed("Some text to embed")
print(f"Embedding dimensions: {len(embedding.embeddings)}")
```

### 4. Configuration Options

You can configure LLM behavior through environment variables:

```bash
# OpenAI Configuration
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4
OPENAI_MAX_TOKENS=2000
OPENAI_TEMPERATURE=0.7
OPENAI_TIMEOUT=30
OPENAI_RETRY_ATTEMPTS=3

# Router Configuration
LLM_ROUTER_STRATEGY=fallback  # or cheapest, fastest, best_quality
```

## Troubleshooting

### Invalid API Key Error

If you see:
```
Error code: 401 - {'error': {'message': 'Incorrect API key provided...
```

1. Check that your `.env` file contains the correct API key
2. Make sure the key starts with `sk-` for OpenAI
3. Verify the key is active in your OpenAI account

### No Providers Available

If the router reports no available providers:

1. Check your internet connection
2. Verify API keys are correctly set
3. Check provider service status

### Rate Limiting

If you encounter rate limit errors:

1. Implement exponential backoff
2. Use the router's retry mechanism
3. Consider upgrading your API tier

## Next Steps

1. Integrate LLM into ContentMind agent
2. Implement MCP framework for prompt management
3. Add support for additional providers (Anthropic, Ollama)
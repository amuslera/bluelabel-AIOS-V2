# Real Integration Testing Setup Guide

This guide will help you configure Bluelabel AIOS v2 for real-world testing with actual external services.

## Prerequisites Checklist

- [ ] OpenAI API Key
- [ ] Anthropic API Key (optional)
- [ ] Google Gemini API Key (optional)
- [ ] Google Cloud Project with Gmail API enabled
- [ ] PostgreSQL database running
- [ ] Redis server running
- [ ] ChromaDB instance (optional, for vector storage)

## Step 1: LLM Provider Configuration

### OpenAI
1. Sign up at https://platform.openai.com
2. Create an API key
3. Update `.env`:
   ```
   OPENAI_API_KEY=sk-proj-...your_actual_key...
   ```

### Anthropic (Optional)
1. Sign up at https://console.anthropic.com
2. Create an API key
3. Update `.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-...your_actual_key...
   ```

### Google Gemini (Optional)
1. Get API key from https://makersuite.google.com/app/apikey
2. Update `.env`:
   ```
   GOOGLE_GENERATIVEAI_API_KEY=...your_actual_key...
   ```

## Step 2: Gmail OAuth Setup

The Google Cloud credentials in the current `.env` need to be verified and properly configured:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8081/gateway/google/callback`
6. Update `.env` with your credentials:
   ```
   GOOGLE_CLIENT_ID=your_actual_client_id
   GOOGLE_CLIENT_SECRET=your_actual_client_secret
   ```

## Step 3: Database Setup

### PostgreSQL
1. Install PostgreSQL if not already installed
2. Create database:
   ```bash
   createdb bluelabel_aios
   ```
3. Verify connection in `.env`:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bluelabel_aios
   ```

### Redis
1. Install Redis if not already installed
2. Start Redis server:
   ```bash
   redis-server
   ```
3. Update `.env` to use real Redis:
   ```
   REDIS_SIMULATION_MODE=false
   ```

## Step 4: Test External Connections

Create test scripts to verify each integration:

### 1. Test LLM Connection
```python
# scripts/test_llm_connection.py
import asyncio
from services.model_router.factory import create_default_router

async def test_llm():
    router = await create_default_router()
    response = await router.chat([
        {"role": "user", "content": "Say hello"}
    ])
    print(f"LLM Response: {response.content}")

asyncio.run(test_llm())
```

### 2. Test Gmail OAuth
```python
# scripts/test_gmail_oauth.py
# Use the existing demo_gmail_complete.py script
./scripts/demo_gmail_complete.py
```

### 3. Test Database Connection
```python
# scripts/test_database.py
import asyncio
from services.knowledge.repository import PostgresKnowledgeRepository

async def test_db():
    repo = PostgresKnowledgeRepository("postgresql://postgres:postgres@localhost:5432/bluelabel_aios")
    await repo.initialize()
    print("Database connected successfully!")

asyncio.run(test_db())
```

## Step 5: Environment File Template

Create `.env.example` for the team:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Database (Required)
DATABASE_URL=postgresql://user:password@localhost:5432/bluelabel_aios

# Redis (Required)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_SIMULATION_MODE=false

# LLM Providers (At least one required)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_GENERATIVEAI_API_KEY=your_gemini_key_here

# Default LLM Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4-turbo-preview
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2000

# Gmail OAuth (Required for email features)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8081/gateway/google/callback

# Email Gateway (Optional - for SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_USE_TLS=true

# Vector DB (Optional)
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bluelabel_aios.log
```

## Step 6: Quick Start Testing

Once configured, run these commands to test:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python scripts/init_database.py

# 3. Start services
docker-compose up -d redis postgres

# 4. Run API server
./scripts/run_api.sh

# 5. Test endpoints
# In another terminal:
python scripts/test_integration.py
```

## Step 7: Integration Test Script

Create a comprehensive test script:

```python
# scripts/test_integration.py
import asyncio
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

async def test_all_integrations():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test health
        resp = await client.get(f"{base_url}/health")
        print(f"✓ Health check: {resp.json()}")
        
        # Test LLM
        resp = await client.post(f"{base_url}/api/v1/agents/content_mind/execute", 
            json={
                "content": "Test content",
                "content_type": "text/plain",
                "operation": "summarize"
            })
        print(f"✓ LLM test: {resp.status_code}")
        
        # Test database
        resp = await client.post(f"{base_url}/api/v1/knowledge/items",
            json={
                "source": "test",
                "title": "Test Item",
                "content": "Test content",
                "content_type": "text"
            })
        print(f"✓ Database test: {resp.status_code}")
        
        # Test Gmail OAuth flow
        resp = await client.get(f"{base_url}/api/v1/gmail-complete/auth/start")
        print(f"✓ Gmail OAuth: {resp.json()}")

if __name__ == "__main__":
    asyncio.run(test_all_integrations())
```

## Troubleshooting

### Common Issues:

1. **LLM API Errors**
   - Verify API keys are correct
   - Check API credit/limits
   - Test with curl first

2. **Database Connection Failed**
   - Ensure PostgreSQL is running
   - Check credentials and database name
   - Verify port 5432 is not blocked

3. **Redis Connection Failed**
   - Start Redis server
   - Check port 6379 is available
   - Set REDIS_SIMULATION_MODE=false

4. **Gmail OAuth Issues**
   - Verify redirect URI matches exactly
   - Check Google Cloud project settings
   - Ensure Gmail API is enabled

## Next Steps

After verifying all connections:

1. Run the demo scripts to test workflows
2. Create test workflows using the API
3. Monitor logs for any issues
4. Set up proper API keys for production

## Security Notes

- Never commit `.env` files with real API keys
- Use environment variables in production
- Rotate keys regularly
- Set up proper access controls
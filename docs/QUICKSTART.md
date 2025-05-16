# Quick Start Guide

## Testing the System

With the server running, try these tests:

### 1. List Available Agents
Open: http://localhost:8000/api/v1/agents/

You should see:
```json
[
  {
    "id": "content_mind",
    "name": "ContentMind",
    "version": "1.0.0",
    "description": "Content analysis and insights extraction agent",
    "status": "active"
  }
]
```

### 2. Test the ContentMind Agent
Go to: http://localhost:8000/docs

1. Expand `/api/v1/agents/{agent_id}/execute`
2. Click "Try it out"
3. Set `agent_id` to: `content_mind`
4. Use this request body:
```json
{
  "input_type": "text",
  "input_data": "OpenAI announced GPT-4o, their latest multimodal AI model. The new model is faster and more cost-effective than GPT-4, while maintaining similar capabilities. It can process text, images, and audio inputs.",
  "context": {
    "source": "tech_news",
    "title": "GPT-4o Announcement"
  }
}
```
5. Click "Execute"

Expected response:
```json
{
  "agent_id": "content_mind",
  "status": "success",
  "output_data": {
    "summary": "OpenAI launched GPT-4o, a multimodal AI model that's faster and more cost-effective than GPT-4, capable of processing text, images, and audio inputs",
    "entities": ["OpenAI", "GPT-4o", "GPT-4"],
    "topics": ["artificial intelligence", "multimodal AI"],
    "sentiment": {
      "label": "positive",
      "score": 0.85
    }
  },
  "metadata": {
    "processing_time": 0.05,
    "model_version": "1.0.0"
  }
}
```

### 3. Check Agent Metrics
After running the agent, check metrics:
http://localhost:8000/api/v1/agents/content_mind/metrics

### 4. Test Event System
In the API docs, try publishing an event:

1. Expand `/api/v1/events/publish`
2. Use this request:
```json
{
  "stream": "test_stream",
  "event_type": "test_event",
  "data": {
    "message": "Hello from the event system!"
  }
}
```

### 5. Monitor Events with WebSocket
You can connect to the WebSocket endpoint using a tool like wscat:
```bash
npm install -g wscat
wscat -c ws://localhost:8000/api/v1/events/ws/test_stream
```

## What's Working Now

✅ Agent Runtime Manager
✅ ContentMind Agent
✅ API endpoints for agents and events
✅ WebSocket support for real-time events
✅ Comprehensive logging system
✅ Metrics collection
✅ Event bus (simulation mode)

## Next Steps

Based on the TODO list:
1. Fix python-whatsapp dependency (TODO #3)
2. Implement Email Gateway OAuth 2.0 (TODO #5)
3. Create Gateway Agent (TODO #6)
4. Knowledge Repository (PostgreSQL + ChromaDB)
5. End-to-end test: Email → Digest → Email
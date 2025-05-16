# Running the Bluelabel AIOS v2 API

## Quick Start

1. **Start the development server:**
   ```bash
   cd /Users/arielmuslera/Development/Projects/bluelabel-AIOS-V2
   source .venv/bin/activate
   python3 scripts/run_development.py
   ```

2. **Access the API in your browser:**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## Available Endpoints

### Agent Management
- `GET /api/v1/agents/` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get agent info
- `GET /api/v1/agents/{agent_id}/capabilities` - Get agent capabilities
- `POST /api/v1/agents/{agent_id}/execute` - Execute an agent
- `GET /api/v1/agents/{agent_id}/metrics` - Get agent metrics
- `GET /api/v1/agents/metrics/all` - Get all agent metrics
- `POST /api/v1/agents/register` - Register a new agent

### Event Management
- `POST /api/v1/events/publish` - Publish an event
- `POST /api/v1/events/subscribe` - Create subscription
- `GET /api/v1/events/streams` - List event streams
- `GET /api/v1/events/events` - Get events from a stream
- `WebSocket /api/v1/events/ws/{stream}` - Real-time event streaming
- `GET /api/v1/events/metrics` - Get event system metrics

## Testing the API

### Using the Interactive Docs

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out" to test the endpoint
4. Fill in the parameters and click "Execute"

### Example API Calls

**List all agents:**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/"
```

**Execute ContentMind agent:**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/content_mind/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "content_mind",
    "source": "api_test",
    "content": {
      "text": "This is test content for the AI system.",
      "type": "text"
    },
    "metadata": {}
  }'
```

**Get agent metrics:**
```bash
curl -X GET "http://localhost:8000/api/v1/agents/content_mind/metrics"
```

## WebSocket Example

To test WebSocket event streaming:

1. Open the WebSocket tester in the API docs
2. Or use a WebSocket client:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/events/ws/agent_events');

ws.onopen = () => {
  console.log('Connected to event stream');
  ws.send(JSON.stringify({action: 'ping'}));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

## Monitoring

- Check logs in the terminal where the server is running
- Access metrics at `/api/v1/agents/metrics/all`
- Monitor events at `/api/v1/events/metrics`

## Troubleshooting

If the server doesn't start:
1. Check that the virtual environment is activated
2. Ensure Redis simulation mode is enabled
3. Check that port 8000 is not in use
4. Verify all dependencies are installed: `pip install -r requirements.txt`
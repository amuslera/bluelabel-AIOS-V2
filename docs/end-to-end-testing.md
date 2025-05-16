# End-to-End Testing Guide

This document describes the end-to-end testing implementation for the Bluelabel AIOS email processing flow.

## Overview

The end-to-end test validates the complete flow:
1. Email reception
2. Content processing via ContentMind agent
3. Storage in Knowledge Repository
4. Response generation and sending

## Test Files

### Integration Tests

1. **`tests/integration/test_end_to_end_email_flow.py`**
   - Full integration test with mocked external services
   - Tests normal flow, error handling, and concurrent processing
   - Uses pytest fixtures for setup and teardown

2. **`tests/integration/test_flow_with_mocks.py`**
   - Simplified test that mocks Redis and external services
   - Can run without any services running
   - Good for CI/CD pipelines

### Demo Scripts

1. **`scripts/demo_email_flow.py`**
   - Interactive demo of the complete flow
   - Shows real-time processing with console output
   - Useful for manual testing and demonstrations

## Running the Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Set environment variables (if using real LLM)
export OPENAI_API_KEY=your-key-here
```

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_flow_with_mocks.py -v

# Run with coverage
pytest tests/integration/ --cov=agents --cov=services
```

### Running the Demo

```bash
# Make sure script is executable
chmod +x scripts/demo_email_flow.py

# Run the demo
./scripts/demo_email_flow.py

# Or with Python directly
python scripts/demo_email_flow.py
```

## Test Scenarios

### 1. Normal Flow Test
- Receives an email about AI developments
- Processes through ContentMind agent
- Stores in Knowledge Repository with extracted tags and concepts
- Sends response with AI-generated summary

### 2. Error Handling Test
- Simulates LLM service failures
- Verifies graceful error handling
- Ensures error notifications are sent

### 3. Concurrent Processing Test
- Processes multiple emails simultaneously
- Verifies all emails are handled correctly
- Tests system under load

## Architecture Validation

The tests validate:

1. **Event-Driven Architecture**
   - Events are published and consumed correctly
   - Agents respond to appropriate events
   - Event data flows through the system

2. **Agent Communication**
   - Gateway agent receives and publishes email events
   - ContentMind agent processes content and stores in repository
   - Agents communicate via event bus

3. **Data Persistence**
   - Content is correctly stored in Knowledge Repository
   - Metadata, tags, and concepts are preserved
   - Search functionality works as expected

4. **LLM Integration**
   - LLM router correctly routes requests
   - MCP framework generates appropriate prompts
   - Responses are properly formatted

## Debugging

If tests fail:

1. Check environment variables (especially API keys)
2. Ensure Redis is running (for full integration tests)
3. Verify file permissions and paths
4. Check logs for detailed error messages

## Extending Tests

To add new test scenarios:

1. Add test methods to existing test files
2. Use provided fixtures for setup
3. Mock external services as needed
4. Follow existing patterns for consistency

## CI/CD Integration

The tests are designed to run in CI/CD pipelines:

1. Use `test_flow_with_mocks.py` for quick validation
2. No external service dependencies required
3. Fast execution time
4. Clear pass/fail indicators

## Performance Considerations

- Tests use file-based Knowledge Repository for speed
- LLM calls are mocked to avoid API limits
- Redis is mocked in unit tests
- Concurrent tests limited to prevent resource exhaustion
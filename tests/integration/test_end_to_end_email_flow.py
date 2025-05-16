"""End-to-end integration test for Email → ContentMind → Knowledge → Email flow"""

import asyncio
import pytest
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from agents.content_mind import ContentMind
from agents.gateway import GatewayAgent
from services.gateway.email_gateway import EmailGateway
from services.knowledge.factory import create_knowledge_repository
from services.llm.router import LLMRouter
from services.mcp.prompt_manager import MCPPromptManager
from apps.api.main import app
from core.event_bus import EventBus


class MockEmailService:
    """Mock email service for testing"""
    
    def __init__(self):
        self.sent_emails = []
        self.received_emails = []
    
    async def receive_email(self, to_address: str):
        """Simulate receiving an email"""
        # Return a test email if we have one
        if self.received_emails:
            return self.received_emails.pop(0)
        return None
    
    async def send_email(self, to_address: str, subject: str, body: str, **kwargs):
        """Capture sent emails"""
        self.sent_emails.append({
            'to': to_address,
            'subject': subject,
            'body': body,
            'kwargs': kwargs
        })
        return True
    
    def add_test_email(self, email_data):
        """Add a test email to be 'received'"""
        self.received_emails.append(email_data)


@pytest.fixture
def mock_email_service():
    """Provide mock email service"""
    return MockEmailService()


@pytest.fixture
async def test_components(tmp_path):
    """Set up test components"""
    # Create test config
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'
    
    # Create components
    event_bus = EventBus()
    await event_bus.connect()
    
    # Create MCP prompt manager
    mcp_manager = MCPPromptManager(template_dir=str(tmp_path / "templates"))
    
    # Create LLM router with mock
    llm_router = LLMRouter()
    
    # Create Knowledge Repository (file-based for testing)
    knowledge_repo = create_knowledge_repository(
        use_postgres=False,
        data_dir=str(tmp_path / "knowledge")
    )
    
    # Create ContentMind agent
    content_mind = ContentMind(
        event_bus=event_bus,
        llm_router=llm_router,
        mcp_manager=mcp_manager,
        knowledge_repo=knowledge_repo
    )
    await content_mind.initialize()
    
    # Create Gateway agent with mock email
    gateway_agent = GatewayAgent(event_bus=event_bus)
    await gateway_agent.initialize()
    
    components = {
        'event_bus': event_bus,
        'mcp_manager': mcp_manager,
        'llm_router': llm_router,
        'knowledge_repo': knowledge_repo,
        'content_mind': content_mind,
        'gateway_agent': gateway_agent,
        'tmp_path': tmp_path
    }
    
    yield components
    
    # Cleanup
    await content_mind.shutdown()
    await gateway_agent.shutdown()
    await event_bus.disconnect()


@pytest.mark.asyncio
async def test_email_to_knowledge_flow(test_components, mock_email_service):
    """Test the complete flow from email to knowledge repository"""
    
    # Unpack components
    event_bus = test_components['event_bus']
    content_mind = test_components['content_mind']
    gateway_agent = test_components['gateway_agent']
    knowledge_repo = test_components['knowledge_repo']
    llm_router = test_components['llm_router']
    
    # Mock LLM response
    mock_llm_response = {
        "content": "This is a summary of the email about AI advances.",
        "metadata": {
            "topics": ["AI", "machine learning"],
            "sentiment": "positive"
        }
    }
    
    with patch.object(llm_router, 'route_request', new_callable=AsyncMock) as mock_route:
        mock_route.return_value = mock_llm_response
        
        # Mock email gateway
        with patch.object(gateway_agent, 'email_gateway', mock_email_service):
            
            # Create test email
            test_email = {
                'id': 'test123',
                'from': 'sender@example.com',
                'to': 'receiver@example.com',
                'subject': 'Latest AI Advances',
                'body': 'This email discusses recent breakthroughs in artificial intelligence...',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add test email to mock service
            mock_email_service.add_test_email(test_email)
            
            # Step 1: Gateway receives email and publishes event
            await event_bus.publish('email.received', {
                'email_id': test_email['id'],
                'from': test_email['from'],
                'to': test_email['to'],
                'subject': test_email['subject'],
                'body': test_email['body'],
                'timestamp': test_email['timestamp']
            })
            
            # Allow time for async processing
            await asyncio.sleep(0.1)
            
            # Step 2: ContentMind should process the email
            # Verify LLM was called
            assert mock_route.called
            call_args = mock_route.call_args[0][0]  # Get the prompt
            assert 'Latest AI Advances' in str(call_args)
            
            # Step 3: Check knowledge repository
            # Search for stored content
            if hasattr(knowledge_repo, 'search_content') and asyncio.iscoroutinefunction(knowledge_repo.search_content):
                results = await knowledge_repo.search_content('AI advances')
            else:
                results = knowledge_repo.search_content('AI advances')
            
            assert len(results) > 0
            stored_content = results[0]
            assert stored_content.title == test_email['subject']
            assert stored_content.source == f"email:{test_email['id']}"
            assert 'AI' in stored_content.tags
            
            # Step 4: Check if response email was sent
            # ContentMind should publish processed event
            await event_bus.publish('content.processed', {
                'content_id': stored_content.id,
                'original_email_id': test_email['id'],
                'summary': mock_llm_response['content'],
                'from': test_email['from']
            })
            
            # Allow time for gateway to process
            await asyncio.sleep(0.1)
            
            # Verify response email was sent
            assert len(mock_email_service.sent_emails) == 1
            sent_email = mock_email_service.sent_emails[0]
            assert sent_email['to'] == test_email['from']
            assert 'Re: Latest AI Advances' in sent_email['subject']
            assert mock_llm_response['content'] in sent_email['body']


@pytest.mark.asyncio
async def test_error_handling_in_flow(test_components, mock_email_service):
    """Test error handling throughout the flow"""
    
    event_bus = test_components['event_bus']
    content_mind = test_components['content_mind']
    gateway_agent = test_components['gateway_agent']
    llm_router = test_components['llm_router']
    
    # Mock LLM to raise an error
    with patch.object(llm_router, 'route_request', new_callable=AsyncMock) as mock_route:
        mock_route.side_effect = Exception("LLM service unavailable")
        
        # Mock email gateway
        with patch.object(gateway_agent, 'email_gateway', mock_email_service):
            
            # Create test email
            test_email = {
                'id': 'test456',
                'from': 'sender@example.com',
                'to': 'receiver@example.com',
                'subject': 'Test Error Handling',
                'body': 'This should trigger error handling...',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add test email
            mock_email_service.add_test_email(test_email)
            
            # Publish email received event
            await event_bus.publish('email.received', {
                'email_id': test_email['id'],
                'from': test_email['from'],
                'to': test_email['to'],
                'subject': test_email['subject'],
                'body': test_email['body'],
                'timestamp': test_email['timestamp']
            })
            
            # Allow time for processing
            await asyncio.sleep(0.1)
            
            # Verify error was handled gracefully
            # Should send error notification email
            assert len(mock_email_service.sent_emails) >= 1
            error_email = mock_email_service.sent_emails[-1]
            assert 'Error' in error_email['subject'] or 'error' in error_email['body'].lower()


@pytest.mark.asyncio
async def test_concurrent_email_processing(test_components, mock_email_service):
    """Test handling multiple emails concurrently"""
    
    event_bus = test_components['event_bus']
    content_mind = test_components['content_mind']
    gateway_agent = test_components['gateway_agent']
    knowledge_repo = test_components['knowledge_repo']
    llm_router = test_components['llm_router']
    
    # Mock LLM responses
    call_count = 0
    async def mock_llm_response(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return {
            "content": f"Summary of email {call_count}",
            "metadata": {"call_number": call_count}
        }
    
    with patch.object(llm_router, 'route_request', new_callable=AsyncMock) as mock_route:
        mock_route.side_effect = mock_llm_response
        
        # Mock email gateway
        with patch.object(gateway_agent, 'email_gateway', mock_email_service):
            
            # Create multiple test emails
            test_emails = []
            for i in range(3):
                email = {
                    'id': f'test{i}',
                    'from': f'sender{i}@example.com',
                    'to': 'receiver@example.com',
                    'subject': f'Email {i}',
                    'body': f'Content of email {i}',
                    'timestamp': datetime.utcnow().isoformat()
                }
                test_emails.append(email)
                mock_email_service.add_test_email(email)
            
            # Publish all emails concurrently
            tasks = []
            for email in test_emails:
                task = event_bus.publish('email.received', {
                    'email_id': email['id'],
                    'from': email['from'],
                    'to': email['to'],
                    'subject': email['subject'],
                    'body': email['body'],
                    'timestamp': email['timestamp']
                })
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # Allow time for processing
            await asyncio.sleep(0.5)
            
            # Verify all emails were processed
            assert call_count == 3
            
            # Check knowledge repository has all content
            if hasattr(knowledge_repo, 'list_content') and asyncio.iscoroutinefunction(knowledge_repo.list_content):
                all_content = await knowledge_repo.list_content()
            else:
                all_content = knowledge_repo.list_content()
            
            # Should have at least 3 items (might have more from other tests)
            assert len(all_content) >= 3
            
            # Verify responses were sent
            assert len(mock_email_service.sent_emails) >= 3


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
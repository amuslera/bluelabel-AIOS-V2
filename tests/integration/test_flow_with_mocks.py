"""Integration test with mocked external services"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from core.event_bus import EventBus
from agents.content_mind import ContentMind
from agents.gateway import GatewayAgent
from services.llm.router import LLMRouter
from services.mcp.prompt_manager import MCPPromptManager
from services.knowledge.factory import create_knowledge_repository


@pytest.fixture
async def test_setup(tmp_path):
    """Set up test environment with mocked services"""
    
    # Mock Redis
    with patch('core.event_bus.aioredis.from_url') as mock_redis:
        # Create mock Redis client
        mock_redis_client = MagicMock()
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_redis_client.xadd = AsyncMock()
        mock_redis_client.xread = AsyncMock(return_value=[])
        mock_redis_client.close = AsyncMock()
        mock_redis.return_value = mock_redis_client
        
        # Create event bus
        event_bus = EventBus()
        event_bus._redis = mock_redis_client
        event_bus._connected = True
        
        # Create components
        mcp_manager = MCPPromptManager(template_dir=str(tmp_path / "templates"))
        llm_router = LLMRouter()
        knowledge_repo = create_knowledge_repository(
            use_postgres=False,
            data_dir=str(tmp_path / "knowledge")
        )
        
        # Create agents
        content_mind = ContentMind(
            event_bus=event_bus,
            llm_router=llm_router,
            mcp_manager=mcp_manager,
            knowledge_repo=knowledge_repo
        )
        
        gateway_agent = GatewayAgent(event_bus=event_bus)
        
        yield {
            'event_bus': event_bus,
            'content_mind': content_mind,
            'gateway_agent': gateway_agent,
            'llm_router': llm_router,
            'knowledge_repo': knowledge_repo,
            'mock_redis': mock_redis_client
        }


@pytest.mark.asyncio
async def test_email_processing_flow(test_setup):
    """Test the email processing flow with mocked services"""
    
    # Get components
    event_bus = test_setup['event_bus']
    content_mind = test_setup['content_mind']
    gateway_agent = test_setup['gateway_agent']
    llm_router = test_setup['llm_router']
    knowledge_repo = test_setup['knowledge_repo']
    
    # Mock LLM response
    with patch.object(llm_router, 'route_request') as mock_route:
        mock_route.return_value = {
            "content": "Summary: This email discusses AI advancements.",
            "metadata": {
                "topics": ["AI", "technology"],
                "entities": ["GPT-4", "computer vision"]
            }
        }
        
        # Mock email sending
        with patch.object(gateway_agent, '_send_email_response') as mock_send:
            mock_send.return_value = True
            
            # Create test email data
            email_data = {
                'id': 'test_email_123',
                'from': 'sender@example.com',
                'to': 'receiver@example.com',
                'subject': 'AI Advances in 2024',
                'body': 'Recent developments in AI include GPT-4 and computer vision breakthroughs.',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Simulate email received event
            await event_bus.publish('email.received', email_data)
            
            # Process the email through ContentMind
            input_data = {
                "operation": "extract",
                "channel": "email",
                "content": {
                    **email_data,
                    "channel_metadata": {
                        "email_id": email_data['id'],
                        "thread_id": None,
                        "labels": []
                    }
                }
            }
            
            # Process directly through ContentMind
            result = await content_mind.process(input_data)
            
            assert result['success'] is True
            assert result['result']['content_id'] is not None
            
            # Verify content was stored
            stored_items = knowledge_repo.list_content()
            assert len(stored_items) == 1
            
            stored_item = stored_items[0]
            assert stored_item.title == email_data['subject']
            assert stored_item.source == f"email:{email_data['id']}"
            assert 'AI' in stored_item.tags
            
            # Simulate content processed event
            await event_bus.publish('content.processed', {
                'content_id': stored_item.id,
                'original_email_id': email_data['id'],
                'summary': 'Summary: This email discusses AI advancements.',
                'from': email_data['from'],
                'to': email_data['to']
            })
            
            # Process through Gateway
            gateway_input = {
                "operation": "send",
                "channel": "email",
                "content": {
                    "to": email_data['from'],
                    "subject": f"Re: {email_data['subject']}",
                    "body": "Summary: This email discusses AI advancements.",
                    "in_reply_to": email_data['id']
                }
            }
            
            gateway_result = await gateway_agent.process(gateway_input)
            
            # Verify the flow completed
            assert gateway_result['success'] is True


@pytest.mark.asyncio
async def test_error_handling(test_setup):
    """Test error handling in the flow"""
    
    # Get components
    content_mind = test_setup['content_mind']
    llm_router = test_setup['llm_router']
    
    # Mock LLM to fail
    with patch.object(llm_router, 'route_request') as mock_route:
        mock_route.side_effect = Exception("LLM service error")
        
        # Process with error
        input_data = {
            "operation": "extract",
            "channel": "email",
            "content": {
                "id": "error_test",
                "from": "sender@example.com",
                "subject": "Test Error",
                "body": "This should fail",
                "channel_metadata": {}
            }
        }
        
        result = await content_mind.process(input_data)
        
        # Should handle error gracefully
        assert result['success'] is False
        assert 'error' in result


@pytest.mark.asyncio
async def test_concurrent_processing(test_setup):
    """Test processing multiple emails concurrently"""
    
    # Get components
    content_mind = test_setup['content_mind']
    llm_router = test_setup['llm_router']
    knowledge_repo = test_setup['knowledge_repo']
    
    # Mock LLM responses
    call_count = 0
    def mock_llm_response(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return {
            "content": f"Summary {call_count}",
            "metadata": {"call": call_count}
        }
    
    with patch.object(llm_router, 'route_request') as mock_route:
        mock_route.side_effect = mock_llm_response
        
        # Create multiple email inputs
        tasks = []
        for i in range(3):
            input_data = {
                "operation": "extract",
                "channel": "email",
                "content": {
                    "id": f"email_{i}",
                    "from": f"sender{i}@example.com",
                    "subject": f"Email {i}",
                    "body": f"Content {i}",
                    "channel_metadata": {
                        "email_id": f"email_{i}"
                    }
                }
            }
            
            task = content_mind.process(input_data)
            tasks.append(task)
        
        # Process concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all processed
        assert all(r['success'] for r in results)
        assert call_count == 3
        
        # Check knowledge repository
        stored_items = knowledge_repo.list_content()
        assert len(stored_items) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
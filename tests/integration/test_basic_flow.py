"""Basic integration test for email flow components"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

from core.event_bus import EventBus
from agents.base import AgentInput, AgentOutput
from services.knowledge.factory import create_knowledge_repository


@pytest.mark.asyncio
async def test_basic_email_flow(tmp_path):
    """Test basic email flow without all dependencies"""
    
    # Create file-based knowledge repository
    import os
    os.environ['KNOWLEDGE_DATA_DIR'] = str(tmp_path / "knowledge")
    knowledge_repo = create_knowledge_repository(use_postgres=False)
    
    # Test email data
    email_data = {
        'id': 'test_123',
        'from': 'sender@example.com',
        'to': 'receiver@example.com',
        'subject': 'AI Technology Update',
        'body': 'Recent advances in AI include GPT-4 and computer vision improvements.',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Step 1: Store content in knowledge repository
    content_id = knowledge_repo.add_content(
        title=email_data['subject'],
        source=f"email:{email_data['id']}",
        content_type='email',
        text_content=email_data['body'],
        summary='Email about AI advances',
        metadata={
            'from': email_data['from'],
            'to': email_data['to'],
            'timestamp': email_data['timestamp']
        },
        tags=['ai', 'technology', 'gpt-4']
    )
    
    assert content_id is not None
    
    # Step 2: Retrieve and verify stored content
    stored_item = knowledge_repo.get_content(content_id.id)
    assert stored_item is not None
    assert stored_item.title == email_data['subject']
    assert stored_item.source == f"email:{email_data['id']}"
    assert 'ai' in stored_item.tags
    
    # Step 3: Search for content
    search_results = knowledge_repo.search_content('AI advances')
    assert len(search_results) > 0
    assert any(result.id == content_id.id for result in search_results)
    
    # Step 4: Verify agent input/output structure
    agent_input = AgentInput(
        source='email',
        metadata={
            'channel': 'email',
            'email_id': email_data['id'],
            'operation': 'extract'
        },
        content={
            'subject': email_data['subject'],
            'body': email_data['body'],
            'from': email_data['from']
        }
    )
    
    # Simulate agent output
    agent_output = AgentOutput(
        task_id=agent_input.task_id,
        status='success',
        result={
            'content_id': content_id.id,
            'summary': 'Email discusses AI advances including GPT-4',
            'tags': ['ai', 'technology'],
            'extracted_entities': ['GPT-4', 'computer vision']
        },
        error=None
    )
    
    assert agent_output.status == 'success'
    assert agent_output.result['content_id'] == content_id.id


def test_event_flow():
    """Test event bus communication pattern"""
    
    # Create event bus in simulation mode
    event_bus = EventBus(simulation_mode=True)
    
    # Test event publishing
    test_event = {
        'type': 'email.received',
        'payload': {
            'email_id': 'test_789',
            'from': 'test@example.com',
            'subject': 'Test Email'
        }
    }
    
    stream_name = 'email.received'
    message_id = event_bus.publish(stream_name, test_event)
    
    # Verify event was published 
    assert message_id is not None
    assert stream_name in event_bus.simulated_streams
    assert len(event_bus.simulated_streams[stream_name]) == 1
    
    # Test message handling directly
    from core.event_patterns import Message, MessageHandler
    
    # Create handler
    handled_messages = []
    
    def test_handler(message):
        handled_messages.append(message)
    
    # Register handler
    event_bus.subscribe(stream_name, test_handler)
    
    # Get the simulated message and handle it
    simulated_message = event_bus.simulated_streams[stream_name][0]
    parsed_message = event_bus._parse_message(simulated_message['id'], simulated_message['data'])
    event_bus._handle_message(stream_name, parsed_message)
    
    # Verify handler was called
    assert len(handled_messages) == 1
    # The data should be in the payload field
    assert handled_messages[0].payload.get('email_id') == 'test_789'
    assert handled_messages[0].type == 'email.received'


@pytest.mark.asyncio
async def test_knowledge_repository_operations(tmp_path):
    """Test knowledge repository CRUD operations"""
    
    import os
    os.environ['KNOWLEDGE_DATA_DIR'] = str(tmp_path / "knowledge")
    repo = create_knowledge_repository(use_postgres=False)
    
    # Test create
    content = repo.add_content(
        title="Test Content",
        source="test_source",
        content_type="test",
        text_content="Test content body",
        tags=["test", "integration"]
    )
    
    assert content.id is not None
    
    # Test read
    retrieved = repo.get_content(content.id)
    assert retrieved is not None
    assert retrieved.title == "Test Content"
    
    # Test update
    updated = repo.update_content(
        content.id,
        title="Updated Content",
        tags=["test", "integration", "updated"]
    )
    assert updated.title == "Updated Content"
    assert "updated" in updated.tags
    
    # Test search
    results = repo.search_content("Test")
    assert len(results) >= 1
    
    # Test delete
    deleted = repo.delete_content(content.id)
    assert deleted
    
    # Verify deleted
    gone = repo.get_content(content.id)
    assert gone is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
import pytest
from core.event_patterns import MessagePattern

def test_message_pattern():
    pattern = MessagePattern.EVENT
    assert pattern == MessagePattern.EVENT
    assert pattern != MessagePattern.COMMAND
    assert pattern.value == "event"
    assert str(pattern) == "MessagePattern.EVENT" 
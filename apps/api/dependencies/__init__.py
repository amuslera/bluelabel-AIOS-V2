# API dependencies
from typing import Generator
from fastapi import Depends
from core.event_bus import EventBus
from agents.registry import AgentRegistry

# Event bus singleton
_event_bus: EventBus = None

def get_event_bus() -> EventBus:
    """Get the global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

# Agent registry singleton
_agent_registry: AgentRegistry = None

def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance"""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
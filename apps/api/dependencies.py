"""
Dependency injection for FastAPI endpoints.
"""
from functools import lru_cache
from typing import Optional

from fastapi import Depends

from core.event_bus import EventBus
from core.config import settings
from agents.registry import AgentRegistry
from services.agent_runtime import AgentRuntimeManager
from services.workflow.repository import WorkflowRepository, InMemoryWorkflowRepository


@lru_cache()
def get_event_bus() -> EventBus:
    """Get the event bus instance."""
    return EventBus(simulation_mode=settings.REDIS_SIMULATION_MODE)


@lru_cache()
def get_agent_registry() -> AgentRegistry:
    """Get the agent registry instance."""
    return AgentRegistry()


@lru_cache()
def get_workflow_repository() -> WorkflowRepository:
    """Get the workflow repository instance."""
    return InMemoryWorkflowRepository()


def get_runtime_manager(
    event_bus: EventBus = Depends(get_event_bus),
    agent_registry: AgentRegistry = Depends(get_agent_registry),
) -> AgentRuntimeManager:
    """Get the agent runtime manager instance."""
    return AgentRuntimeManager(
        event_bus=event_bus,
        agent_registry=agent_registry,
    )
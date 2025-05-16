"""
Tests for the async workflow engine.
"""
import asyncio
import pytest
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock
from uuid import uuid4

from agents.base import Agent, AgentInput, AgentOutput
from agents.registry import AgentRegistry
from core.event_bus import EventBus
from shared.schemas.base import AgentType

from services.workflow.engine_async import AsyncWorkflowEngine
from services.workflow.models import (
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatus,
    StepStatus,
    InputMapping,
    OutputMapping
)
from services.workflow.repository import InMemoryWorkflowRepository


# Mock agent for testing
class MockAgent(Agent):
    """Mock agent implementation for testing."""
    
    def __init__(self, agent_type: AgentType, response: Dict[str, Any]):
        self.agent_type = agent_type
        self.response = response
        self.process_count = 0
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """Mock process implementation."""
        self.process_count += 1
        return AgentOutput(
            content=self.response,
            content_type="application/json",
            metadata={"mock": True}
        )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Mock capabilities."""
        return {"type": "mock"}
    
    async def initialize(self) -> bool:
        """Mock initialization."""
        return True
    
    async def shutdown(self) -> bool:
        """Mock shutdown."""
        return True


@pytest.fixture
async def event_bus():
    """Create a mock event bus."""
    bus = AsyncMock(spec=EventBus)
    bus.publish = AsyncMock()
    bus.subscribe = AsyncMock()
    return bus


@pytest.fixture
async def agent_registry():
    """Create a mock agent registry."""
    registry = AgentRegistry()
    return registry


@pytest.fixture
async def repository():
    """Create an in-memory repository."""
    repo = InMemoryWorkflowRepository()
    await repo.initialize()
    return repo


@pytest.fixture
async def workflow_engine(event_bus, agent_registry, repository):
    """Create a workflow engine instance."""
    engine = AsyncWorkflowEngine(
        event_bus=event_bus,
        agent_registry=agent_registry,
        repository=repository
    )
    await engine.initialize()
    return engine


@pytest.fixture
def simple_workflow():
    """Create a simple test workflow."""
    return Workflow(
        id="test-workflow-1",
        name="Test Workflow",
        description="A simple test workflow",
        steps=[
            WorkflowStep(
                id="step-1",
                name="First Step",
                agent_type=AgentType.CONTENT_MIND,
                input_mappings=[
                    InputMapping(
                        source="input",
                        source_key="data",
                        target_key="content"
                    )
                ],
                output_mappings=[
                    OutputMapping(
                        source_key="result",
                        target="output",
                        target_key="step1_result"
                    )
                ]
            ),
            WorkflowStep(
                id="step-2",
                name="Second Step",
                agent_type=AgentType.CONTEXT_MIND,
                input_mappings=[
                    InputMapping(
                        source="steps",
                        source_key="step-1.result",
                        target_key="input_data"
                    )
                ],
                output_mappings=[
                    OutputMapping(
                        source_key="final",
                        target="output",
                        target_key="final_result"
                    )
                ]
            )
        ]
    )


class TestAsyncWorkflowEngine:
    """Test suite for AsyncWorkflowEngine."""
    
    @pytest.mark.asyncio
    async def test_initialize(self, workflow_engine, event_bus):
        """Test engine initialization."""
        assert workflow_engine is not None
        assert workflow_engine.event_bus == event_bus
        
        # Verify event subscriptions
        event_bus.subscribe.assert_called()
    
    @pytest.mark.asyncio
    async def test_register_workflow(self, workflow_engine, simple_workflow, event_bus):
        """Test workflow registration."""
        await workflow_engine.register_workflow(simple_workflow)
        
        # Verify workflow is saved
        saved_workflow = await workflow_engine.repository.get_workflow(simple_workflow.id)
        assert saved_workflow is not None
        assert saved_workflow.name == simple_workflow.name
        
        # Verify event is published
        event_bus.publish.assert_called()
        call_args = event_bus.publish.call_args
        assert call_args[0][0] == "workflow.registered"
    
    @pytest.mark.asyncio
    async def test_execute_simple_workflow(
        self,
        workflow_engine,
        simple_workflow,
        agent_registry,
        event_bus
    ):
        """Test execution of a simple workflow."""
        # Register agents
        agent1 = MockAgent(
            AgentType.CONTENT_MIND,
            {"result": "processed content"}
        )
        agent2 = MockAgent(
            AgentType.CONTEXT_MIND,
            {"final": "final result"}
        )
        
        await agent_registry.register(AgentType.CONTENT_MIND, agent1)
        await agent_registry.register(AgentType.CONTEXT_MIND, agent2)
        
        # Register workflow
        await workflow_engine.register_workflow(simple_workflow)
        
        # Execute workflow
        input_data = {"data": "test input"}
        execution = await workflow_engine.execute_workflow(
            workflow_id=simple_workflow.id,
            input_data=input_data
        )
        
        assert execution is not None
        assert execution.status == WorkflowStatus.PENDING
        assert execution.input_data == input_data
        
        # Wait for execution to complete
        await asyncio.sleep(0.5)
        
        # Verify execution completed
        final_execution = await workflow_engine.get_execution_status(execution.id)
        assert final_execution.status == WorkflowStatus.COMPLETED
        assert final_execution.output_data == {
            "step1_result": "processed content",
            "final_result": "final result"
        }
        
        # Verify agents were called
        assert agent1.process_count == 1
        assert agent2.process_count == 1
        
        # Verify events were published
        assert event_bus.publish.call_count > 2  # Start, steps, complete
    
    @pytest.mark.asyncio
    async def test_step_failure_handling(
        self,
        workflow_engine,
        agent_registry,
        event_bus
    ):
        """Test workflow behavior when a step fails."""
        # Create workflow with failure handling
        workflow = Workflow(
            id="test-fail-workflow",
            name="Fail Test Workflow",
            steps=[
                WorkflowStep(
                    id="step-1",
                    name="Failing Step",
                    agent_type=AgentType.CONTENT_MIND,
                    on_failure="fail",
                    retries=1
                )
            ]
        )
        
        # Register failing agent
        failing_agent = Mock(spec=Agent)
        failing_agent.process = AsyncMock(side_effect=Exception("Test failure"))
        failing_agent.get_capabilities = Mock(return_value={})
        failing_agent.initialize = AsyncMock(return_value=True)
        failing_agent.shutdown = AsyncMock(return_value=True)
        
        await agent_registry.register(AgentType.CONTENT_MIND, failing_agent)
        
        # Register and execute workflow
        await workflow_engine.register_workflow(workflow)
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow.id,
            input_data={}
        )
        
        # Wait for execution
        await asyncio.sleep(0.5)
        
        # Verify execution failed
        final_execution = await workflow_engine.get_execution_status(execution.id)
        assert final_execution.status == WorkflowStatus.FAILED
        
        # Verify retries happened
        assert failing_agent.process.call_count == 2  # Initial + 1 retry
    
    @pytest.mark.asyncio
    async def test_conditional_step_execution(
        self,
        workflow_engine,
        agent_registry
    ):
        """Test conditional step execution."""
        # Create workflow with conditional step
        workflow = Workflow(
            id="test-conditional-workflow",
            name="Conditional Test Workflow",
            steps=[
                WorkflowStep(
                    id="step-1",
                    name="Always Run",
                    agent_type=AgentType.CONTENT_MIND,
                    output_mappings=[
                        OutputMapping(
                            source_key="value",
                            target="output",
                            target_key="step1_value"
                        )
                    ]
                ),
                WorkflowStep(
                    id="step-2",
                    name="Conditional Step",
                    agent_type=AgentType.CONTEXT_MIND,
                    condition="steps['step-1']['value'] > 5"
                )
            ]
        )
        
        # Register agents
        agent1 = MockAgent(AgentType.CONTENT_MIND, {"value": 10})
        agent2 = MockAgent(AgentType.CONTEXT_MIND, {"result": "conditional"})
        
        await agent_registry.register(AgentType.CONTENT_MIND, agent1)
        await agent_registry.register(AgentType.CONTEXT_MIND, agent2)
        
        # Register and execute workflow
        await workflow_engine.register_workflow(workflow)
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow.id,
            input_data={}
        )
        
        # Wait for execution
        await asyncio.sleep(0.5)
        
        # Verify both steps ran
        final_execution = await workflow_engine.get_execution_status(execution.id)
        assert agent1.process_count == 1
        assert agent2.process_count == 1  # Should run because 10 > 5
        
        # Test with condition not met
        agent1.response = {"value": 3}
        agent1.process_count = 0
        agent2.process_count = 0
        
        execution2 = await workflow_engine.execute_workflow(
            workflow_id=workflow.id,
            input_data={}
        )
        
        await asyncio.sleep(0.5)
        
        # Verify conditional step was skipped
        assert agent1.process_count == 1
        assert agent2.process_count == 0  # Should not run because 3 < 5
    
    @pytest.mark.asyncio
    async def test_cancel_execution(
        self,
        workflow_engine,
        agent_registry
    ):
        """Test cancelling a running workflow."""
        # Create workflow with long-running step
        workflow = Workflow(
            id="test-cancel-workflow",
            name="Cancel Test Workflow",
            steps=[
                WorkflowStep(
                    id="step-1",
                    name="Long Step",
                    agent_type=AgentType.CONTENT_MIND,
                    timeout=10
                )
            ]
        )
        
        # Register slow agent
        slow_agent = Mock(spec=Agent)
        slow_agent.process = AsyncMock(
            side_effect=lambda x: asyncio.sleep(5)
        )
        slow_agent.get_capabilities = Mock(return_value={})
        slow_agent.initialize = AsyncMock(return_value=True)
        slow_agent.shutdown = AsyncMock(return_value=True)
        
        await agent_registry.register(AgentType.CONTENT_MIND, slow_agent)
        
        # Register and execute workflow
        await workflow_engine.register_workflow(workflow)
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow.id,
            input_data={}
        )
        
        # Cancel after short delay
        await asyncio.sleep(0.1)
        cancelled = await workflow_engine.cancel_execution(execution.id)
        assert cancelled
        
        # Wait a bit more
        await asyncio.sleep(0.5)
        
        # Verify execution was cancelled
        final_execution = await workflow_engine.get_execution_status(execution.id)
        assert final_execution.status == WorkflowStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_input_output_mappings(
        self,
        workflow_engine,
        agent_registry
    ):
        """Test complex input/output mappings."""
        # Create workflow with mappings
        workflow = Workflow(
            id="test-mapping-workflow",
            name="Mapping Test Workflow",
            steps=[
                WorkflowStep(
                    id="step-1",
                    name="Transform Step",
                    agent_type=AgentType.CONTENT_MIND,
                    input_mappings=[
                        InputMapping(
                            source="input",
                            source_key="user.name",
                            target_key="username"
                        ),
                        InputMapping(
                            source="context",
                            source_key="session.id",
                            target_key="session_id"
                        )
                    ],
                    output_mappings=[
                        OutputMapping(
                            source_key="processed",
                            target="output",
                            target_key="results.step1"
                        ),
                        OutputMapping(
                            source_key="metadata",
                            target="context",
                            target_key="step1_meta"
                        )
                    ]
                )
            ]
        )
        
        # Register agent
        agent = MockAgent(
            AgentType.CONTENT_MIND,
            {
                "processed": {"data": "transformed"},
                "metadata": {"timestamp": "2024-01-01"}
            }
        )
        
        await agent_registry.register(AgentType.CONTENT_MIND, agent)
        
        # Register and execute workflow
        await workflow_engine.register_workflow(workflow)
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow.id,
            input_data={"user": {"name": "John"}},
            context={"session": {"id": "abc123"}}
        )
        
        # Wait for execution
        await asyncio.sleep(0.5)
        
        # Verify mappings worked correctly
        final_execution = await workflow_engine.get_execution_status(execution.id)
        assert final_execution.status == WorkflowStatus.COMPLETED
        assert final_execution.output_data == {
            "results": {
                "step1": {"data": "transformed"}
            }
        }
        assert final_execution.context["step1_meta"] == {"timestamp": "2024-01-01"}
    
    @pytest.mark.asyncio
    async def test_list_executions(
        self,
        workflow_engine,
        simple_workflow,
        agent_registry
    ):
        """Test listing workflow executions."""
        # Register agents
        agent1 = MockAgent(AgentType.CONTENT_MIND, {"result": "data"})
        agent2 = MockAgent(AgentType.CONTEXT_MIND, {"final": "output"})
        
        await agent_registry.register(AgentType.CONTENT_MIND, agent1)
        await agent_registry.register(AgentType.CONTEXT_MIND, agent2)
        
        # Register workflow
        await workflow_engine.register_workflow(simple_workflow)
        
        # Execute workflow multiple times
        executions = []
        for i in range(3):
            execution = await workflow_engine.execute_workflow(
                workflow_id=simple_workflow.id,
                input_data={"data": f"input-{i}"},
                user_id=f"user-{i % 2}"  # Alternate between two users
            )
            executions.append(execution)
        
        # Wait for executions
        await asyncio.sleep(1)
        
        # List all executions
        all_executions = await workflow_engine.list_executions()
        assert len(all_executions) >= 3
        
        # List by workflow
        workflow_executions = await workflow_engine.list_executions(
            workflow_id=simple_workflow.id
        )
        assert len(workflow_executions) == 3
        
        # List by user
        user0_executions = await workflow_engine.list_executions(user_id="user-0")
        assert len(user0_executions) == 2  # 0 and 2
        
        user1_executions = await workflow_engine.list_executions(user_id="user-1")
        assert len(user1_executions) == 1  # 1
        
        # List by status
        completed_executions = await workflow_engine.list_executions(
            status=WorkflowStatus.COMPLETED
        )
        assert len(completed_executions) == 3
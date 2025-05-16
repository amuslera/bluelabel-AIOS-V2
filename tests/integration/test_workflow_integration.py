"""
Integration tests for workflow engine with real components.
"""
import asyncio
import pytest
from datetime import datetime, timezone
from typing import Dict, Any

from agents.content_mind import ContentMindLLM
from agents.registry import AgentRegistry
from core.event_bus import EventBus
from core.config import settings
from shared.schemas.base import AgentType
from services.model_router.router import ModelRouter
from services.model_router.factory import create_default_router
from services.mcp.prompt_manager import PromptManager

from services.workflow.engine_async import AsyncWorkflowEngine
from services.workflow.models import (
    Workflow,
    WorkflowStep,
    WorkflowStatus,
    InputMapping,
    OutputMapping
)
from services.workflow.repository import InMemoryWorkflowRepository


@pytest.fixture
async def event_bus():
    """Create a real event bus."""
    bus = EventBus()
    await bus.initialize()
    yield bus
    await bus.shutdown()


@pytest.fixture
async def model_router():
    """Create a model router."""
    # Create router with minimal setup
    router = await create_default_router()
    return router


@pytest.fixture
async def agent_registry(model_router):
    """Create an agent registry with real agents."""
    registry = AgentRegistry()
    
    # Create prompt manager
    prompt_manager = PromptManager(templates_dir="data/mcp/templates")
    prompt_manager.load_templates()
    
    # Create ContentMind agent
    content_mind = ContentMindLLM(
        model_router=model_router,
        prompt_manager=prompt_manager
    )
    await content_mind.initialize()
    
    # Register agent
    await registry.register(AgentType.CONTENT_MIND, content_mind)
    
    return registry


@pytest.fixture
async def workflow_engine(event_bus, agent_registry):
    """Create a workflow engine with real components."""
    repository = InMemoryWorkflowRepository()
    await repository.initialize()
    
    engine = AsyncWorkflowEngine(
        event_bus=event_bus,
        agent_registry=agent_registry,
        repository=repository
    )
    await engine.initialize()
    
    yield engine
    
    await engine.shutdown()


@pytest.fixture
def content_processing_workflow():
    """Create a content processing workflow."""
    return Workflow(
        id="content-processing",
        name="Content Processing Workflow",
        description="Process and summarize content",
        steps=[
            WorkflowStep(
                id="analyze-content",
                name="Analyze Content",
                agent_type=AgentType.CONTENT_MIND,
                input_mappings=[
                    InputMapping(
                        source="input",
                        source_key="content",
                        target_key="content"
                    ),
                    InputMapping(
                        source="input",
                        source_key="content_type",
                        target_key="content_type"
                    )
                ],
                output_mappings=[
                    OutputMapping(
                        source_key="summary",
                        target="output",
                        target_key="analysis.summary"
                    ),
                    OutputMapping(
                        source_key="key_points",
                        target="output",
                        target_key="analysis.key_points"
                    ),
                    OutputMapping(
                        source_key="content_type",
                        target="context",
                        target_key="detected_type"
                    )
                ]
            ),
            WorkflowStep(
                id="generate-digest",
                name="Generate Digest",
                agent_type=AgentType.CONTENT_MIND,
                condition="context.get('detected_type') == 'article'",
                input_mappings=[
                    InputMapping(
                        source="steps",
                        source_key="analyze-content.summary",
                        target_key="original_summary"
                    ),
                    InputMapping(
                        source="steps",
                        source_key="analyze-content.key_points",
                        target_key="key_points"
                    )
                ],
                output_mappings=[
                    OutputMapping(
                        source_key="digest",
                        target="output",
                        target_key="final_digest"
                    )
                ]
            )
        ]
    )


class TestWorkflowIntegration:
    """Integration tests for workflow engine."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_content_processing_workflow(
        self,
        workflow_engine,
        content_processing_workflow
    ):
        """Test a complete content processing workflow."""
        # Register workflow
        await workflow_engine.register_workflow(content_processing_workflow)
        
        # Prepare test content
        test_content = """
        Artificial Intelligence (AI) is rapidly transforming various industries.
        Machine learning models are becoming more sophisticated, enabling
        tasks that were previously thought impossible. The impact on healthcare,
        finance, and transportation is particularly significant.
        """
        
        # Execute workflow
        execution = await workflow_engine.execute_workflow(
            workflow_id=content_processing_workflow.id,
            input_data={
                "content": test_content,
                "content_type": "article"
            }
        )
        
        # Wait for completion with timeout
        max_wait = 30  # seconds
        start_time = datetime.now(timezone.utc)
        
        while True:
            current_execution = await workflow_engine.get_execution_status(execution.id)
            
            if current_execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                break
            
            if (datetime.now(timezone.utc) - start_time).total_seconds() > max_wait:
                pytest.fail(f"Workflow execution timed out after {max_wait} seconds")
            
            await asyncio.sleep(1)
        
        # Verify execution completed successfully
        assert current_execution.status == WorkflowStatus.COMPLETED
        assert current_execution.output_data is not None
        
        # Verify output structure
        output = current_execution.output_data
        assert "analysis" in output
        assert "summary" in output["analysis"]
        assert "key_points" in output["analysis"]
        
        # Since this is an article, the digest step should have run
        assert "final_digest" in output
        
        # Verify context was updated
        assert current_execution.context.get("detected_type") == "article"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_with_invalid_input(
        self,
        workflow_engine,
        content_processing_workflow
    ):
        """Test workflow behavior with invalid input."""
        # Register workflow
        await workflow_engine.register_workflow(content_processing_workflow)
        
        # Execute with missing required input
        execution = await workflow_engine.execute_workflow(
            workflow_id=content_processing_workflow.id,
            input_data={}  # Missing content and content_type
        )
        
        # Wait for completion
        await asyncio.sleep(5)
        
        # Check execution status
        final_execution = await workflow_engine.get_execution_status(execution.id)
        
        # The workflow should handle missing input gracefully
        # (either fail or provide default behavior)
        assert final_execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_event_notifications(
        self,
        workflow_engine,
        content_processing_workflow,
        event_bus
    ):
        """Test that workflow events are properly published."""
        events_received = []
        
        # Subscribe to workflow events
        async def event_handler(message: Dict[str, Any]):
            events_received.append(message)
        
        await event_bus.subscribe("workflow.*", event_handler)
        
        # Register and execute workflow
        await workflow_engine.register_workflow(content_processing_workflow)
        
        execution = await workflow_engine.execute_workflow(
            workflow_id=content_processing_workflow.id,
            input_data={
                "content": "Test content",
                "content_type": "article"
            }
        )
        
        # Wait for completion
        await asyncio.sleep(10)
        
        # Verify events were received
        event_types = [msg.get("type") for msg in events_received]
        
        assert "workflow.registered" in event_types
        assert "workflow.started" in event_types
        assert any("workflow.step" in t for t in event_types)
        assert any(t in ["workflow.completed", "workflow.failed"] for t in event_types)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_workflow_executions(
        self,
        workflow_engine,
        content_processing_workflow
    ):
        """Test running multiple workflows concurrently."""
        # Register workflow
        await workflow_engine.register_workflow(content_processing_workflow)
        
        # Execute multiple workflows concurrently
        executions = []
        for i in range(3):
            execution = await workflow_engine.execute_workflow(
                workflow_id=content_processing_workflow.id,
                input_data={
                    "content": f"Test content {i}",
                    "content_type": "article"
                },
                user_id=f"user-{i}"
            )
            executions.append(execution)
        
        # Wait for all to complete
        await asyncio.sleep(15)
        
        # Verify all completed
        completed_count = 0
        for execution in executions:
            final_execution = await workflow_engine.get_execution_status(execution.id)
            if final_execution.status == WorkflowStatus.COMPLETED:
                completed_count += 1
        
        assert completed_count >= 2  # At least 2 should complete successfully
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_workflow_cancellation(
        self,
        workflow_engine,
        content_processing_workflow
    ):
        """Test cancelling a running workflow."""
        # Register workflow
        await workflow_engine.register_workflow(content_processing_workflow)
        
        # Execute workflow
        execution = await workflow_engine.execute_workflow(
            workflow_id=content_processing_workflow.id,
            input_data={
                "content": "Long content to process",
                "content_type": "article"
            }
        )
        
        # Cancel after a short delay
        await asyncio.sleep(1)
        cancelled = await workflow_engine.cancel_execution(execution.id)
        
        # Verify cancellation
        assert cancelled
        
        # Wait a bit more
        await asyncio.sleep(2)
        
        # Check final status
        final_execution = await workflow_engine.get_execution_status(execution.id)
        assert final_execution.status == WorkflowStatus.CANCELLED
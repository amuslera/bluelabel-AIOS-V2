"""
Tests for workflow API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from apps.api.main import app
from apps.api.dependencies import get_event_bus, get_agent_registry
from shared.schemas.base import AgentType

from services.workflow.models import (
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatus,
    StepStatus,
    InputMapping,
    OutputMapping
)
from services.workflow.engine_async import AsyncWorkflowEngine
from services.workflow.repository import InMemoryWorkflowRepository


@pytest.fixture
def test_client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = AsyncMock()
    return bus


@pytest.fixture
def mock_agent_registry():
    """Create a mock agent registry."""
    registry = Mock()
    registry.get_agent = AsyncMock()
    return registry


@pytest.fixture
def mock_workflow_engine(mock_event_bus, mock_agent_registry):
    """Create a mock workflow engine."""
    repository = InMemoryWorkflowRepository()
    engine = AsyncMock(spec=AsyncWorkflowEngine)
    engine.repository = repository
    engine.event_bus = mock_event_bus
    engine.agent_registry = mock_agent_registry
    
    # Mock methods
    engine.register_workflow = AsyncMock()
    engine.execute_workflow = AsyncMock()
    engine.get_execution_status = AsyncMock()
    engine.list_executions = AsyncMock()
    engine.cancel_execution = AsyncMock()
    
    return engine


class TestWorkflowAPI:
    """Test suite for workflow API endpoints."""
    
    def test_create_workflow(self, test_client, monkeypatch, mock_workflow_engine):
        """Test creating a workflow."""
        # Mock dependencies
        async def mock_get_workflow_engine():
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        # Create workflow request
        workflow_data = {
            "name": "Test Workflow",
            "description": "Test workflow description",
            "steps": [
                {
                    "name": "Step 1",
                    "agent_type": "content_mind",
                    "input_mappings": [
                        {
                            "source": "input",
                            "source_key": "data",
                            "target_key": "content"
                        }
                    ],
                    "output_mappings": [
                        {
                            "source_key": "result",
                            "target": "output",
                            "target_key": "step1_result"
                        }
                    ]
                }
            ]
        }
        
        # Mock the registered workflow
        mock_workflow_engine.register_workflow.return_value = None
        
        response = test_client.post("/api/v1/workflows/", json=workflow_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert len(data["steps"]) == 1
        assert data["id"] is not None
        
        # Verify the workflow was registered
        mock_workflow_engine.register_workflow.assert_called_once()
    
    def test_get_workflow(self, test_client, monkeypatch, mock_workflow_engine):
        """Test getting a workflow by ID."""
        # Mock dependencies
        workflow_id = "test-workflow-123"
        test_workflow = Workflow(
            id=workflow_id,
            name="Test Workflow",
            description="Test description",
            steps=[
                WorkflowStep(
                    name="Step 1",
                    agent_type=AgentType.CONTENT_MIND
                )
            ]
        )
        
        async def mock_get_workflow_engine():
            mock_workflow_engine.repository.save_workflow = AsyncMock()
            await mock_workflow_engine.repository.save_workflow(test_workflow)
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        response = test_client.get(f"/api/v1/workflows/{workflow_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == "Test Workflow"
    
    def test_list_workflows(self, test_client, monkeypatch, mock_workflow_engine):
        """Test listing workflows."""
        # Mock dependencies
        workflows = [
            Workflow(id="workflow-1", name="Workflow 1"),
            Workflow(id="workflow-2", name="Workflow 2")
        ]
        
        async def mock_get_workflow_engine():
            for w in workflows:
                mock_workflow_engine.repository.save_workflow = AsyncMock()
                await mock_workflow_engine.repository.save_workflow(w)
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        response = test_client.get("/api/v1/workflows/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Workflow 1"
        assert data[1]["name"] == "Workflow 2"
    
    def test_execute_workflow(self, test_client, monkeypatch, mock_workflow_engine):
        """Test executing a workflow."""
        # Mock dependencies
        workflow_id = "test-workflow-123"
        execution_id = "execution-456"
        
        test_workflow = Workflow(
            id=workflow_id,
            name="Test Workflow",
            active=True
        )
        
        test_execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            input_data={"test": "data"}
        )
        
        async def mock_get_workflow_engine():
            mock_workflow_engine.repository.save_workflow = AsyncMock()
            await mock_workflow_engine.repository.save_workflow(test_workflow)
            mock_workflow_engine.execute_workflow.return_value = test_execution
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        execution_data = {
            "input_data": {"test": "data"},
            "context": {},
            "user_id": "test-user"
        }
        
        response = test_client.post(f"/api/v1/workflows/{workflow_id}/execute", json=execution_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution_id
        assert data["workflow_id"] == workflow_id
        assert data["status"] == "pending"
        
        # Verify the workflow was executed
        mock_workflow_engine.execute_workflow.assert_called_once()
    
    def test_get_execution(self, test_client, monkeypatch, mock_workflow_engine):
        """Test getting an execution by ID."""
        # Mock dependencies
        execution_id = "execution-456"
        
        test_execution = WorkflowExecution(
            id=execution_id,
            workflow_id="workflow-123",
            status=WorkflowStatus.RUNNING,
            input_data={"test": "data"}
        )
        
        async def mock_get_workflow_engine():
            mock_workflow_engine.get_execution_status.return_value = test_execution
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        response = test_client.get(f"/api/v1/workflows/executions/{execution_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == execution_id
        assert data["status"] == "running"
    
    def test_list_executions(self, test_client, monkeypatch, mock_workflow_engine):
        """Test listing executions."""
        # Mock dependencies
        executions = [
            WorkflowExecution(
                id="exec-1",
                workflow_id="workflow-1",
                status=WorkflowStatus.COMPLETED
            ),
            WorkflowExecution(
                id="exec-2",
                workflow_id="workflow-2",
                status=WorkflowStatus.RUNNING
            )
        ]
        
        async def mock_get_workflow_engine():
            mock_workflow_engine.list_executions.return_value = executions
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        response = test_client.get("/api/v1/workflows/executions")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "exec-1"
        assert data[0]["status"] == "completed"
        assert data[1]["id"] == "exec-2"
        assert data[1]["status"] == "running"
    
    def test_cancel_execution(self, test_client, monkeypatch, mock_workflow_engine):
        """Test cancelling an execution."""
        # Mock dependencies
        execution_id = "execution-456"
        
        async def mock_get_workflow_engine():
            mock_workflow_engine.cancel_execution.return_value = True
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        response = test_client.post(f"/api/v1/workflows/executions/{execution_id}/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Execution cancelled successfully"
        
        # Verify the execution was cancelled
        mock_workflow_engine.cancel_execution.assert_called_once_with(execution_id)
    
    def test_update_workflow(self, test_client, monkeypatch, mock_workflow_engine):
        """Test updating a workflow."""
        # Mock dependencies
        workflow_id = "test-workflow-123"
        test_workflow = Workflow(
            id=workflow_id,
            name="Original Workflow",
            description="Original description"
        )
        
        async def mock_get_workflow_engine():
            mock_workflow_engine.repository.save_workflow = AsyncMock()
            await mock_workflow_engine.repository.save_workflow(test_workflow)
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        update_data = {
            "name": "Updated Workflow",
            "description": "Updated description"
        }
        
        response = test_client.put(f"/api/v1/workflows/{workflow_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Workflow"
        assert data["description"] == "Updated description"
    
    def test_delete_workflow(self, test_client, monkeypatch, mock_workflow_engine):
        """Test deleting (deactivating) a workflow."""
        # Mock dependencies
        workflow_id = "test-workflow-123"
        test_workflow = Workflow(
            id=workflow_id,
            name="Test Workflow",
            active=True
        )
        
        async def mock_get_workflow_engine():
            mock_workflow_engine.repository.save_workflow = AsyncMock()
            await mock_workflow_engine.repository.save_workflow(test_workflow)
            return mock_workflow_engine
        
        monkeypatch.setattr("apps.api.routers.workflows.get_workflow_engine", mock_get_workflow_engine)
        
        response = test_client.delete(f"/api/v1/workflows/{workflow_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Workflow deactivated successfully"
        
        # Verify the workflow was deactivated
        assert test_workflow.active == False
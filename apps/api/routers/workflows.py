"""
Workflow API endpoints.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from agents.registry import AgentRegistry
from core.event_bus import EventBus
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
from services.workflow.repository import (
    InMemoryWorkflowRepository,
    PostgresWorkflowRepository
)
from shared.schemas.base import AgentType

from ..dependencies import get_event_bus, get_agent_registry


router = APIRouter(prefix="/workflows", tags=["workflows"])


# Pydantic models for API
class InputMappingSchema(BaseModel):
    """Input mapping schema."""
    source: str = Field(..., description="Source of the data: input, context, or steps")
    source_key: str = Field(..., description="JSON path in the source")
    target_key: str = Field(..., description="JSON path in the target")
    transform: Optional[str] = Field(None, description="Optional transformation")
    default: Optional[Any] = Field(None, description="Default value if source not found")


class OutputMappingSchema(BaseModel):
    """Output mapping schema."""
    source_key: str = Field(..., description="JSON path in step output")
    target: str = Field(..., description="Target location: output or context")
    target_key: str = Field(..., description="JSON path in the target")
    transform: Optional[str] = Field(None, description="Optional transformation")


class WorkflowStepSchema(BaseModel):
    """Workflow step schema."""
    id: Optional[str] = Field(None, description="Step ID (auto-generated if not provided)")
    name: str = Field(..., description="Step name")
    description: Optional[str] = Field(None, description="Step description")
    agent_type: AgentType = Field(..., description="Type of agent to use")
    
    input_mappings: List[InputMappingSchema] = Field(default_factory=list)
    output_mappings: List[OutputMappingSchema] = Field(default_factory=list)
    
    condition: Optional[str] = Field(None, description="Conditional execution expression")
    timeout: int = Field(300, description="Timeout in seconds")
    retries: int = Field(3, description="Number of retries on failure")
    retry_delay: int = Field(1, description="Initial retry delay in seconds")
    
    on_failure: str = Field("fail", description="Action on failure: fail, continue, skip")
    on_timeout: str = Field("fail", description="Action on timeout: fail, continue, skip")
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow."""
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    version: str = Field("1.0.0", description="Workflow version")
    
    steps: List[WorkflowStepSchema] = Field(..., description="Workflow steps")
    
    max_parallel_steps: int = Field(1, description="Maximum parallel steps")
    timeout: int = Field(3600, description="Overall workflow timeout")
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    active: bool = Field(True, description="Whether the workflow is active")
    draft: bool = Field(False, description="Whether this is a draft")


class WorkflowUpdateRequest(BaseModel):
    """Request to update a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    
    steps: Optional[List[WorkflowStepSchema]] = None
    
    max_parallel_steps: Optional[int] = None
    timeout: Optional[int] = None
    
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    active: Optional[bool] = None
    draft: Optional[bool] = None


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""
    input_data: Dict[str, Any] = Field(..., description="Input data for the workflow")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    user_id: Optional[str] = Field(None, description="User ID")


class WorkflowResponse(BaseModel):
    """Workflow response model."""
    id: str
    name: str
    description: Optional[str]
    version: str
    
    steps: List[WorkflowStepSchema]
    
    max_parallel_steps: int
    timeout: int
    
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    
    metadata: Dict[str, Any]
    tags: List[str]
    
    active: bool
    draft: bool


class ExecutionStepResponse(BaseModel):
    """Execution step response."""
    step_id: str
    status: StepStatus
    
    input: Optional[Dict[str, Any]]
    output: Optional[Dict[str, Any]]
    error: Optional[str]
    
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    attempts: int
    last_retry_at: Optional[datetime]


class WorkflowExecutionResponse(BaseModel):
    """Workflow execution response."""
    id: str
    workflow_id: str
    workflow_version: Optional[str]
    
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    context: Dict[str, Any]
    
    status: WorkflowStatus
    error: Optional[str]
    
    steps: List[ExecutionStepResponse]
    current_step_index: int
    
    user_id: Optional[str]
    triggered_by: Optional[str]
    
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    metadata: Dict[str, Any]
    tags: List[str]


# Dependency to get workflow engine
async def get_workflow_engine(
    event_bus: EventBus = Depends(get_event_bus),
    agent_registry: AgentRegistry = Depends(get_agent_registry)
) -> AsyncWorkflowEngine:
    """Get the workflow engine instance."""
    # For now, use in-memory repository
    # In production, switch to PostgresWorkflowRepository
    repository = InMemoryWorkflowRepository()
    await repository.initialize()
    
    engine = AsyncWorkflowEngine(
        event_bus=event_bus,
        agent_registry=agent_registry,
        repository=repository
    )
    await engine.initialize()
    
    return engine


def workflow_to_response(workflow: Workflow) -> WorkflowResponse:
    """Convert workflow model to response."""
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        version=workflow.version,
        steps=[
            WorkflowStepSchema(
                id=step.id,
                name=step.name,
                description=step.description,
                agent_type=step.agent_type,
                input_mappings=[InputMappingSchema(**m.__dict__) for m in step.input_mappings],
                output_mappings=[OutputMappingSchema(**m.__dict__) for m in step.output_mappings],
                condition=step.condition,
                timeout=step.timeout,
                retries=step.retries,
                retry_delay=step.retry_delay,
                on_failure=step.on_failure,
                on_timeout=step.on_timeout,
                metadata=step.metadata,
                tags=step.tags
            )
            for step in workflow.steps
        ],
        max_parallel_steps=workflow.max_parallel_steps,
        timeout=workflow.timeout,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
        created_by=workflow.created_by,
        metadata=workflow.metadata,
        tags=workflow.tags,
        active=workflow.active,
        draft=workflow.draft
    )


def execution_to_response(execution: WorkflowExecution) -> WorkflowExecutionResponse:
    """Convert execution model to response."""
    return WorkflowExecutionResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        workflow_version=execution.workflow_version,
        input_data=execution.input_data,
        output_data=execution.output_data,
        context=execution.context,
        status=execution.status,
        error=execution.error,
        steps=[
            ExecutionStepResponse(
                step_id=step.step_id,
                status=step.status,
                input=step.input,
                output=step.output,
                error=step.error,
                created_at=step.created_at,
                started_at=step.started_at,
                completed_at=step.completed_at,
                attempts=step.attempts,
                last_retry_at=step.last_retry_at
            )
            for step in execution.steps
        ],
        current_step_index=execution.current_step_index,
        user_id=execution.user_id,
        triggered_by=execution.triggered_by,
        created_at=execution.created_at,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        metadata=execution.metadata,
        tags=execution.tags
    )


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    request: WorkflowCreateRequest,
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> WorkflowResponse:
    """Create a new workflow."""
    # Convert request to workflow model
    workflow = Workflow(
        name=request.name,
        description=request.description,
        version=request.version,
        steps=[
            WorkflowStep(
                id=step.id,
                name=step.name,
                description=step.description,
                agent_type=step.agent_type,
                input_mappings=[InputMapping(**m.dict()) for m in step.input_mappings],
                output_mappings=[OutputMapping(**m.dict()) for m in step.output_mappings],
                condition=step.condition,
                timeout=step.timeout,
                retries=step.retries,
                retry_delay=step.retry_delay,
                on_failure=step.on_failure,
                on_timeout=step.on_timeout,
                metadata=step.metadata,
                tags=step.tags
            )
            for step in request.steps
        ],
        max_parallel_steps=request.max_parallel_steps,
        timeout=request.timeout,
        metadata=request.metadata,
        tags=request.tags,
        active=request.active,
        draft=request.draft
    )
    
    # Register workflow
    await engine.register_workflow(workflow)
    
    return workflow_to_response(workflow)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> WorkflowResponse:
    """Get a workflow by ID."""
    workflow = await engine.repository.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow_to_response(workflow)


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    active_only: bool = Query(True, description="Filter for active workflows only"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> List[WorkflowResponse]:
    """List workflows."""
    workflows = await engine.repository.list_workflows(
        active_only=active_only,
        limit=limit,
        offset=offset
    )
    
    return [workflow_to_response(w) for w in workflows]


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> WorkflowResponse:
    """Update a workflow."""
    # Get existing workflow
    workflow = await engine.repository.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Update fields
    if request.name is not None:
        workflow.name = request.name
    if request.description is not None:
        workflow.description = request.description
    if request.version is not None:
        workflow.version = request.version
    if request.steps is not None:
        workflow.steps = [
            WorkflowStep(
                id=step.id,
                name=step.name,
                description=step.description,
                agent_type=step.agent_type,
                input_mappings=[InputMapping(**m.dict()) for m in step.input_mappings],
                output_mappings=[OutputMapping(**m.dict()) for m in step.output_mappings],
                condition=step.condition,
                timeout=step.timeout,
                retries=step.retries,
                retry_delay=step.retry_delay,
                on_failure=step.on_failure,
                on_timeout=step.on_timeout,
                metadata=step.metadata,
                tags=step.tags
            )
            for step in request.steps
        ]
    if request.max_parallel_steps is not None:
        workflow.max_parallel_steps = request.max_parallel_steps
    if request.timeout is not None:
        workflow.timeout = request.timeout
    if request.metadata is not None:
        workflow.metadata = request.metadata
    if request.tags is not None:
        workflow.tags = request.tags
    if request.active is not None:
        workflow.active = request.active
    if request.draft is not None:
        workflow.draft = request.draft
    
    workflow.updated_at = datetime.now(timezone.utc)
    
    # Save updated workflow
    await engine.repository.save_workflow(workflow)
    
    return workflow_to_response(workflow)


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, str]:
    """Delete a workflow (soft delete by deactivating)."""
    workflow = await engine.repository.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Soft delete by deactivating
    workflow.active = False
    workflow.updated_at = datetime.now(timezone.utc)
    
    await engine.repository.save_workflow(workflow)
    
    return {"message": "Workflow deactivated successfully"}


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> WorkflowExecutionResponse:
    """Execute a workflow."""
    # Check if workflow exists
    workflow = await engine.repository.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if not workflow.active:
        raise HTTPException(status_code=400, detail="Workflow is not active")
    
    # Execute workflow
    execution = await engine.execute_workflow(
        workflow_id=workflow_id,
        input_data=request.input_data,
        context=request.context,
        user_id=request.user_id
    )
    
    return execution_to_response(execution)


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: str,
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> WorkflowExecutionResponse:
    """Get a workflow execution by ID."""
    execution = await engine.get_execution_status(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution_to_response(execution)


@router.get("/executions", response_model=List[WorkflowExecutionResponse])
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> List[WorkflowExecutionResponse]:
    """List workflow executions."""
    executions = await engine.list_executions(
        workflow_id=workflow_id,
        user_id=user_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return [execution_to_response(e) for e in executions]


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    engine: AsyncWorkflowEngine = Depends(get_workflow_engine)
) -> Dict[str, str]:
    """Cancel a running workflow execution."""
    success = await engine.cancel_execution(execution_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Unable to cancel execution. It may have already completed."
        )
    
    return {"message": "Execution cancelled successfully"}
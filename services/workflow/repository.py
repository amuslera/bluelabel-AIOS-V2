"""
Repository pattern for workflow persistence.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .models import (
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatus,
    StepStatus,
    ExecutionStep,
    InputMapping,
    OutputMapping
)
from shared.schemas.base import AgentType

logger = logging.getLogger(__name__)

Base = declarative_base()


# SQLAlchemy Models
class WorkflowDB(Base):
    """SQLAlchemy model for workflows."""
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), nullable=False)
    
    # Configuration
    max_parallel_steps = Column(Integer, default=1)
    timeout = Column(Integer, default=3600)
    
    # Metadata
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    created_by = Column(String(255))
    metadata_json = Column(Text)
    tags_json = Column(Text)
    
    # Status
    active = Column(Boolean, default=True)
    draft = Column(Boolean, default=False)
    
    # Relationships
    steps = relationship("WorkflowStepDB", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStepDB(Base):
    """SQLAlchemy model for workflow steps."""
    __tablename__ = "workflow_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    agent_type = Column(SQLEnum(AgentType), nullable=False)
    
    # Mappings (stored as JSON)
    input_mappings_json = Column(Text)
    output_mappings_json = Column(Text)
    
    # Execution control
    condition = Column(Text)
    timeout = Column(Integer, default=300)
    retries = Column(Integer, default=3)
    retry_delay = Column(Integer, default=1)
    
    # Error handling
    on_failure = Column(String(50), default="fail")
    on_timeout = Column(String(50), default="fail")
    
    # Metadata
    metadata_json = Column(Text)
    tags_json = Column(Text)
    
    # Order
    step_order = Column(Integer, nullable=False)
    
    # Relationships
    workflow = relationship("WorkflowDB", back_populates="steps")


class WorkflowExecutionDB(Base):
    """SQLAlchemy model for workflow executions."""
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    workflow_version = Column(String(50))
    
    # Execution data
    input_data_json = Column(Text)
    output_data_json = Column(Text)
    context_json = Column(Text)
    
    # Status
    status = Column(SQLEnum(WorkflowStatus), nullable=False)
    error = Column(Text)
    
    # Tracking
    current_step_index = Column(Integer, default=0)
    user_id = Column(String(255))
    triggered_by = Column(String(50))
    
    # Timing
    created_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Metadata
    metadata_json = Column(Text)
    tags_json = Column(Text)
    
    # Relationships
    steps = relationship("ExecutionStepDB", back_populates="execution", cascade="all, delete-orphan")


class ExecutionStepDB(Base):
    """SQLAlchemy model for execution steps."""
    __tablename__ = "execution_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False)
    step_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(SQLEnum(StepStatus), nullable=False)
    
    # Execution data
    input_json = Column(Text)
    output_json = Column(Text)
    error = Column(Text)
    
    # Timing
    created_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Retry
    attempts = Column(Integer, default=0)
    last_retry_at = Column(DateTime)
    
    # Relationships
    execution = relationship("WorkflowExecutionDB", back_populates="steps")


class WorkflowRepository(ABC):
    """Abstract base class for workflow persistence."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository."""
        pass
    
    @abstractmethod
    async def save_workflow(self, workflow: Workflow) -> None:
        """Save a workflow definition."""
        pass
    
    @abstractmethod
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        pass
    
    @abstractmethod
    async def list_workflows(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows."""
        pass
    
    @abstractmethod
    async def save_execution(self, execution: WorkflowExecution) -> None:
        """Save a workflow execution."""
        pass
    
    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        pass
    
    @abstractmethod
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List workflow executions."""
        pass


class InMemoryWorkflowRepository(WorkflowRepository):
    """In-memory implementation of workflow repository."""
    
    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
    
    async def initialize(self) -> None:
        """Initialize the repository."""
        logger.info("InMemoryWorkflowRepository initialized")
    
    async def save_workflow(self, workflow: Workflow) -> None:
        """Save a workflow definition."""
        workflow.updated_at = datetime.now(timezone.utc)
        self._workflows[workflow.id] = workflow
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)
    
    async def list_workflows(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows."""
        workflows = list(self._workflows.values())
        
        if active_only:
            workflows = [w for w in workflows if w.active]
        
        # Sort by created_at descending
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        
        # Apply pagination
        return workflows[offset:offset + limit]
    
    async def save_execution(self, execution: WorkflowExecution) -> None:
        """Save a workflow execution."""
        self._executions[execution.id] = execution
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        return self._executions.get(execution_id)
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List workflow executions."""
        executions = list(self._executions.values())
        
        # Apply filters
        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]
        
        if user_id:
            executions = [e for e in executions if e.user_id == user_id]
        
        if status:
            executions = [e for e in executions if e.status == status]
        
        # Sort by created_at descending
        executions.sort(key=lambda e: e.created_at, reverse=True)
        
        # Apply pagination
        return executions[offset:offset + limit]


class PostgresWorkflowRepository(WorkflowRepository):
    """PostgreSQL implementation of workflow repository."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def initialize(self) -> None:
        """Initialize the repository and create tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("PostgresWorkflowRepository initialized")
    
    def _workflow_to_db(self, workflow: Workflow) -> WorkflowDB:
        """Convert domain model to DB model."""
        db_workflow = WorkflowDB(
            id=uuid.UUID(workflow.id) if isinstance(workflow.id, str) else workflow.id,
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            max_parallel_steps=workflow.max_parallel_steps,
            timeout=workflow.timeout,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            created_by=workflow.created_by,
            metadata_json=json.dumps(workflow.metadata),
            tags_json=json.dumps(workflow.tags),
            active=workflow.active,
            draft=workflow.draft
        )
        
        # Add steps
        for i, step in enumerate(workflow.steps):
            db_step = WorkflowStepDB(
                id=uuid.UUID(step.id) if isinstance(step.id, str) else step.id,
                workflow_id=db_workflow.id,
                name=step.name,
                description=step.description,
                agent_type=step.agent_type,
                input_mappings_json=json.dumps([m.__dict__ for m in step.input_mappings]),
                output_mappings_json=json.dumps([m.__dict__ for m in step.output_mappings]),
                condition=step.condition,
                timeout=step.timeout,
                retries=step.retries,
                retry_delay=step.retry_delay,
                on_failure=step.on_failure,
                on_timeout=step.on_timeout,
                metadata_json=json.dumps(step.metadata),
                tags_json=json.dumps(step.tags),
                step_order=i
            )
            db_workflow.steps.append(db_step)
        
        return db_workflow
    
    def _db_to_workflow(self, db_workflow: WorkflowDB) -> Workflow:
        """Convert DB model to domain model."""
        workflow = Workflow(
            id=str(db_workflow.id),
            name=db_workflow.name,
            description=db_workflow.description,
            version=db_workflow.version,
            max_parallel_steps=db_workflow.max_parallel_steps,
            timeout=db_workflow.timeout,
            created_at=db_workflow.created_at,
            updated_at=db_workflow.updated_at,
            created_by=db_workflow.created_by,
            metadata=json.loads(db_workflow.metadata_json) if db_workflow.metadata_json else {},
            tags=json.loads(db_workflow.tags_json) if db_workflow.tags_json else [],
            active=db_workflow.active,
            draft=db_workflow.draft
        )
        
        # Convert steps
        workflow.steps = []
        for db_step in sorted(db_workflow.steps, key=lambda s: s.step_order):
            input_mappings = [
                InputMapping(**m) for m in json.loads(db_step.input_mappings_json or "[]")
            ]
            output_mappings = [
                OutputMapping(**m) for m in json.loads(db_step.output_mappings_json or "[]")
            ]
            
            step = WorkflowStep(
                id=str(db_step.id),
                name=db_step.name,
                description=db_step.description,
                agent_type=db_step.agent_type,
                input_mappings=input_mappings,
                output_mappings=output_mappings,
                condition=db_step.condition,
                timeout=db_step.timeout,
                retries=db_step.retries,
                retry_delay=db_step.retry_delay,
                on_failure=db_step.on_failure,
                on_timeout=db_step.on_timeout,
                metadata=json.loads(db_step.metadata_json) if db_step.metadata_json else {},
                tags=json.loads(db_step.tags_json) if db_step.tags_json else []
            )
            workflow.steps.append(step)
        
        return workflow
    
    async def save_workflow(self, workflow: Workflow) -> None:
        """Save a workflow definition."""
        async with self.async_session() as session:
            db_workflow = self._workflow_to_db(workflow)
            session.add(db_workflow)
            await session.commit()
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        async with self.async_session() as session:
            result = await session.execute(
                select(WorkflowDB).where(WorkflowDB.id == uuid.UUID(workflow_id))
            )
            db_workflow = result.scalar_one_or_none()
            
            if db_workflow:
                return self._db_to_workflow(db_workflow)
            
            return None
    
    async def list_workflows(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows."""
        async with self.async_session() as session:
            query = select(WorkflowDB)
            
            if active_only:
                query = query.where(WorkflowDB.active == True)
            
            query = query.order_by(WorkflowDB.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            db_workflows = result.scalars().all()
            
            return [self._db_to_workflow(w) for w in db_workflows]
    
    def _execution_to_db(self, execution: WorkflowExecution) -> WorkflowExecutionDB:
        """Convert domain model to DB model."""
        db_execution = WorkflowExecutionDB(
            id=uuid.UUID(execution.id) if isinstance(execution.id, str) else execution.id,
            workflow_id=uuid.UUID(execution.workflow_id) if isinstance(execution.workflow_id, str) else execution.workflow_id,
            workflow_version=execution.workflow_version,
            input_data_json=json.dumps(execution.input_data),
            output_data_json=json.dumps(execution.output_data) if execution.output_data else None,
            context_json=json.dumps(execution.context),
            status=execution.status,
            error=execution.error,
            current_step_index=execution.current_step_index,
            user_id=execution.user_id,
            triggered_by=execution.triggered_by,
            created_at=execution.created_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            metadata_json=json.dumps(execution.metadata),
            tags_json=json.dumps(execution.tags)
        )
        
        # Add steps
        for step in execution.steps:
            db_step = ExecutionStepDB(
                execution_id=db_execution.id,
                step_id=uuid.UUID(step.step_id) if isinstance(step.step_id, str) else step.step_id,
                status=step.status,
                input_json=json.dumps(step.input) if step.input else None,
                output_json=json.dumps(step.output) if step.output else None,
                error=step.error,
                created_at=step.created_at,
                started_at=step.started_at,
                completed_at=step.completed_at,
                attempts=step.attempts,
                last_retry_at=step.last_retry_at
            )
            db_execution.steps.append(db_step)
        
        return db_execution
    
    def _db_to_execution(self, db_execution: WorkflowExecutionDB) -> WorkflowExecution:
        """Convert DB model to domain model."""
        execution = WorkflowExecution(
            id=str(db_execution.id),
            workflow_id=str(db_execution.workflow_id),
            workflow_version=db_execution.workflow_version,
            input_data=json.loads(db_execution.input_data_json) if db_execution.input_data_json else {},
            output_data=json.loads(db_execution.output_data_json) if db_execution.output_data_json else None,
            context=json.loads(db_execution.context_json) if db_execution.context_json else {},
            status=db_execution.status,
            error=db_execution.error,
            current_step_index=db_execution.current_step_index,
            user_id=db_execution.user_id,
            triggered_by=db_execution.triggered_by,
            created_at=db_execution.created_at,
            started_at=db_execution.started_at,
            completed_at=db_execution.completed_at,
            metadata=json.loads(db_execution.metadata_json) if db_execution.metadata_json else {},
            tags=json.loads(db_execution.tags_json) if db_execution.tags_json else []
        )
        
        # Convert steps
        execution.steps = []
        for db_step in db_execution.steps:
            step = ExecutionStep(
                step_id=str(db_step.step_id),
                status=db_step.status,
                input=json.loads(db_step.input_json) if db_step.input_json else None,
                output=json.loads(db_step.output_json) if db_step.output_json else None,
                error=db_step.error,
                created_at=db_step.created_at,
                started_at=db_step.started_at,
                completed_at=db_step.completed_at,
                attempts=db_step.attempts,
                last_retry_at=db_step.last_retry_at
            )
            execution.steps.append(step)
        
        return execution
    
    async def save_execution(self, execution: WorkflowExecution) -> None:
        """Save a workflow execution."""
        async with self.async_session() as session:
            # Check if execution exists
            result = await session.execute(
                select(WorkflowExecutionDB).where(
                    WorkflowExecutionDB.id == uuid.UUID(execution.id)
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing
                db_execution = self._execution_to_db(execution)
                await session.merge(db_execution)
            else:
                # Create new
                db_execution = self._execution_to_db(execution)
                session.add(db_execution)
            
            await session.commit()
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        async with self.async_session() as session:
            result = await session.execute(
                select(WorkflowExecutionDB).where(
                    WorkflowExecutionDB.id == uuid.UUID(execution_id)
                )
            )
            db_execution = result.scalar_one_or_none()
            
            if db_execution:
                return self._db_to_execution(db_execution)
            
            return None
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List workflow executions."""
        async with self.async_session() as session:
            query = select(WorkflowExecutionDB)
            
            if workflow_id:
                query = query.where(WorkflowExecutionDB.workflow_id == uuid.UUID(workflow_id))
            
            if user_id:
                query = query.where(WorkflowExecutionDB.user_id == user_id)
            
            if status:
                query = query.where(WorkflowExecutionDB.status == status)
            
            query = query.order_by(WorkflowExecutionDB.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            db_executions = result.scalars().all()
            
            return [self._db_to_execution(e) for e in db_executions]
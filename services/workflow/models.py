"""
Workflow models and data structures.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shared.schemas.base import AgentType


class StepStatus(Enum):
    """Status of a workflow step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class InputMapping:
    """Mapping for step input data."""
    source: str  # "input", "context", "steps"
    source_key: str  # JSON path in source
    target_key: str  # JSON path in target
    transform: Optional[str] = None  # Optional transformation
    default: Optional[Any] = None  # Default value if source not found


@dataclass
class OutputMapping:
    """Mapping for step output data."""
    source_key: str  # JSON path in step output
    target: str  # "output", "context"
    target_key: str  # JSON path in target
    transform: Optional[str] = None  # Optional transformation


@dataclass
class WorkflowStep:
    """Definition of a workflow step."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: Optional[str] = None
    agent_type: AgentType = AgentType.CONTENT_MIND
    
    # Input/output mappings
    input_mappings: List[InputMapping] = field(default_factory=list)
    output_mappings: List[OutputMapping] = field(default_factory=list)
    
    # Execution control
    condition: Optional[str] = None  # Conditional execution
    timeout: int = 300  # Timeout in seconds
    retries: int = 3  # Number of retries on failure
    retry_delay: int = 1  # Initial retry delay in seconds
    
    # Error handling
    on_failure: str = "fail"  # "fail", "continue", "skip"
    on_timeout: str = "fail"  # "fail", "continue", "skip"
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class Workflow:
    """Workflow definition."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Workflow steps
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # Configuration
    max_parallel_steps: int = 1  # Sequential by default
    timeout: int = 3600  # Overall workflow timeout
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Status
    active: bool = True
    draft: bool = False


@dataclass
class ExecutionStep:
    """Step execution record."""
    step_id: str
    status: StepStatus = StepStatus.PENDING
    
    # Execution data
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Retry information
    attempts: int = 0
    last_retry_at: Optional[datetime] = None


@dataclass
class WorkflowExecution:
    """Workflow execution instance."""
    id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str = ""
    workflow_version: Optional[str] = None
    
    # Execution data
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Status tracking
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: Optional[str] = None
    
    # Step tracking
    steps: List[ExecutionStep] = field(default_factory=list)
    current_step_index: int = 0
    
    # User tracking
    user_id: Optional[str] = None
    triggered_by: Optional[str] = None  # "manual", "schedule", "event"
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
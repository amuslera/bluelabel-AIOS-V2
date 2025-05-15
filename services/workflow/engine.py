from typing import Dict, Any, List, Optional, Callable, Union
import json
import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class StepStatus(str, Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class WorkflowStatus(str, Enum):
    """Status of a workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStep(BaseModel):
    """A step in a workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    agent_type: str  # Type of agent to execute this step
    input_mapping: Dict[str, str] = Field(default_factory=dict)  # Maps workflow inputs to step inputs
    output_mapping: Dict[str, str] = Field(default_factory=dict)  # Maps step outputs to workflow outputs
    condition: Optional[str] = None  # Python expression to evaluate whether to run this step
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    status: StepStatus = StepStatus.PENDING
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class Workflow(BaseModel):
    """A workflow definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str
    steps: List[WorkflowStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowExecution(BaseModel):
    """An execution instance of a workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    steps: List[WorkflowStep] = Field(default_factory=list)
    current_step_index: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    user_id: Optional[str] = None

class WorkflowEngine:
    """Engine for executing workflows"""
    
    def __init__(self, agent_registry: Dict[str, Any] = None):
        """Initialize the workflow engine
        
        Args:
            agent_registry: Registry of available agents
        """
        self.agent_registry = agent_registry or {}
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
    
    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow
        
        Args:
            workflow: Workflow to register
        """
        self.workflows[workflow.id] = workflow
    
    def register_agent(self, agent_type: str, agent_factory: Callable) -> None:
        """Register an agent factory
        
        Args:
            agent_type: Type of the agent
            agent_factory: Factory function to create agent instances
        """
        self.agent_registry[agent_type] = agent_factory
    
    def create_execution(self, workflow_id: str, input_data: Dict[str, Any], 
                        user_id: Optional[str] = None) -> WorkflowExecution:
        """Create a new workflow execution
        
        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            user_id: Optional user ID
            
        Returns:
            The created workflow execution
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        
        # Create a copy of the workflow steps
        steps = [WorkflowStep(**step.model_dump()) for step in workflow.steps]
        
        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            input_data=input_data,
            steps=steps,
            user_id=user_id
        )
        
        # Store execution
        self.executions[execution.id] = execution
        
        return execution
    
    def start_execution(self, execution_id: str) -> WorkflowExecution:
        """Start a workflow execution
        
        Args:
            execution_id: ID of the execution to start
            
        Returns:
            The updated workflow execution
        """
        if execution_id not in self.executions:
            raise ValueError(f"Execution {execution_id} not found")
        
        execution = self.executions[execution_id]
        
        # Update status
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.now()
        execution.updated_at = datetime.now()
        
        # Start first step
        self._execute_next_step(execution)
        
        return execution
    
    def _execute_next_step(self, execution: WorkflowExecution) -> None:
        """Execute the next step in the workflow
        
        Args:
            execution: The workflow execution
        """
        # Check if workflow is completed or failed
        if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return
        
        # Check if all steps are completed
        if execution.current_step_index >= len(execution.steps):
            self._complete_execution(execution)
            return
        
        # Get current step
        step = execution.steps[execution.current_step_index]
        
        # Check condition
        if step.condition and not self._evaluate_condition(step.condition, execution):
            # Skip step
            step.status = StepStatus.SKIPPED
            execution.current_step_index += 1
            self._execute_next_step(execution)
            return
        
        # Update step status
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        # Get agent
        agent_type = step.agent_type
        if agent_type not in self.agent_registry:
            step.status = StepStatus.FAILED
            step.error = f"Agent type {agent_type} not found"
            self._handle_step_failure(execution, step)
            return
        
        # Create agent
        agent_factory = self.agent_registry[agent_type]
        agent = agent_factory()
        
        # Prepare input data
        input_data = self._map_inputs(step, execution)
        
        try:
            # Process with agent
            from agents.base import AgentInput, AgentOutput
            agent_input = AgentInput(
                task_id=step.id,
                source="workflow",
                metadata={"workflow_id": execution.workflow_id, "execution_id": execution.id},
                content=input_data
            )
            
            # Execute agent
            result = agent.process(agent_input)
            
            # Handle result
            if result.status == "success":
                self._handle_step_success(execution, step, result.result)
            else:
                self._handle_step_failure(execution, step, result.error)
        
        except Exception as e:
            # Handle error
            self._handle_step_failure(execution, step, str(e))
    
    def _map_inputs(self, step: WorkflowStep, execution: WorkflowExecution) -> Dict[str, Any]:
        """Map workflow inputs to step inputs
        
        Args:
            step: The workflow step
            execution: The workflow execution
            
        Returns:
            Mapped input data for the step
        """
        input_data = {}
        
        # Map from workflow input
        for step_input, workflow_input in step.input_mapping.items():
            if workflow_input in execution.input_data:
                input_data[step_input] = execution.input_data[workflow_input]
        
        # Map from previous steps
        for i in range(execution.current_step_index):
            prev_step = execution.steps[i]
            if prev_step.status == StepStatus.COMPLETED:
                for output_key, output_value in prev_step.result.items():
                    # Use step_id.output_key as the key
                    input_data[f"{prev_step.id}.{output_key}"] = output_value
        
        return input_data
    
    def _handle_step_success(self, execution: WorkflowExecution, step: WorkflowStep, 
                           result: Dict[str, Any]) -> None:
        """Handle successful step completion
        
        Args:
            execution: The workflow execution
            step: The completed step
            result: The step result
        """
        # Update step
        step.status = StepStatus.COMPLETED
        step.result = result
        step.completed_at = datetime.now()
        
        # Map outputs to workflow outputs
        for step_output, workflow_output in step.output_mapping.items():
            if step_output in result:
                execution.output_data[workflow_output] = result[step_output]
        
        # Move to next step
        execution.current_step_index += 1
        execution.updated_at = datetime.now()
        
        # Execute next step
        self._execute_next_step(execution)
    
    def _handle_step_failure(self, execution: WorkflowExecution, step: WorkflowStep, 
                           error: Optional[str] = None) -> None:
        """Handle step failure
        
        Args:
            execution: The workflow execution
            step: The failed step
            error: Optional error message
        """
        # Update step
        step.status = StepStatus.FAILED
        step.error = error
        step.completed_at = datetime.now()
        
        # Check if retry is possible
        if step.retry_count < step.max_retries:
            # Retry step
            step.retry_count += 1
            step.status = StepStatus.PENDING
            step.error = None
            step.started_at = None
            step.completed_at = None
            
            # Execute step again
            self._execute_next_step(execution)
        else:
            # Mark workflow as failed
            execution.status = WorkflowStatus.FAILED
            execution.error = f"Step '{step.name}' failed: {error}"
            execution.completed_at = datetime.now()
            execution.updated_at = datetime.now()
    
    def _complete_execution(self, execution: WorkflowExecution) -> None:
        """Complete a workflow execution
        
        Args:
            execution: The workflow execution
        """
        execution.status = WorkflowStatus.COMPLETED
        execution.completed_at = datetime.now()
        execution.updated_at = datetime.now()
    
    def _evaluate_condition(self, condition: str, execution: WorkflowExecution) -> bool:
        """Evaluate a step condition
        
        Args:
            condition: Python expression to evaluate
            execution: The workflow execution
            
        Returns:
            True if the condition is met, False otherwise
        """
        try:
            # Create context for evaluation
            context = {
                "input": execution.input_data,
                "output": execution.output_data,
                "steps": {}
            }
            
            # Add step results to context
            for i in range(execution.current_step_index):
                step = execution.steps[i]
                context["steps"][step.id] = {
                    "status": step.status,
                    "result": step.result
                }
            
            # Evaluate condition
            return eval(condition, {"__builtins__": {}}, context)
        
        except Exception as e:
            print(f"Error evaluating condition: {str(e)}")
            return False
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID"""
        return self.executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a workflow execution
        
        Args:
            execution_id: ID of the execution to cancel
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        if execution_id not in self.executions:
            return False
        
        execution = self.executions[execution_id]
        
        # Check if already completed
        if execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return False
        
        # Cancel execution
        execution.status = WorkflowStatus.CANCELLED
        execution.completed_at = datetime.now()
        execution.updated_at = datetime.now()
        
        return True

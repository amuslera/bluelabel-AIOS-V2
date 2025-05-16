"""
Asynchronous workflow execution engine with event bus integration.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from core.event_bus import EventBus
from core.event_patterns import EventMetadata
from agents.registry import AgentRegistry
from agents.base import AgentInput, AgentOutput
from shared.schemas.base import AgentType

from .models import (
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatus,
    StepStatus,
    ExecutionStep
)
from .repository import WorkflowRepository, InMemoryWorkflowRepository

logger = logging.getLogger(__name__)


class AsyncWorkflowEngine:
    """Enhanced workflow engine with async execution and event bus integration."""
    
    def __init__(
        self,
        event_bus: EventBus,
        agent_registry: AgentRegistry,
        repository: Optional[WorkflowRepository] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.event_bus = event_bus
        self.agent_registry = agent_registry
        self.repository = repository or InMemoryWorkflowRepository()
        self.config = config or {}
        
        # Running executions tracking
        self._running_executions: Dict[str, asyncio.Task] = {}
        self._execution_lock = asyncio.Lock()
        
        # Subscribe to workflow events
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Set up event bus subscriptions for workflow control."""
        # Event patterns for workflow control
        self.workflow_patterns = {
            "workflow.cancel": "workflow.*.cancel",
            "workflow.pause": "workflow.*.pause",
            "workflow.resume": "workflow.*.resume"
        }
        
    async def initialize(self):
        """Initialize the workflow engine."""
        logger.info("Initializing AsyncWorkflowEngine")
        
        # Subscribe to workflow control events
        await self.event_bus.subscribe(
            self.workflow_patterns["workflow.cancel"],
            self._handle_cancel_event
        )
        
        # Initialize repository
        await self.repository.initialize()
        
        logger.info("AsyncWorkflowEngine initialized successfully")
    
    async def shutdown(self):
        """Shutdown the workflow engine."""
        logger.info("Shutting down AsyncWorkflowEngine")
        
        # Cancel all running executions
        async with self._execution_lock:
            for execution_id, task in self._running_executions.items():
                logger.info(f"Cancelling execution {execution_id}")
                task.cancel()
        
        # Wait for all executions to complete
        if self._running_executions:
            await asyncio.gather(*self._running_executions.values(), return_exceptions=True)
        
        logger.info("AsyncWorkflowEngine shutdown complete")
    
    async def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow definition."""
        await self.repository.save_workflow(workflow)
        
        # Emit workflow registration event
        await self._emit_event(
            "workflow.registered",
            {
                "workflow_id": workflow.id,
                "name": workflow.name,
                "version": workflow.version
            }
        )
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a workflow asynchronously."""
        # Load workflow definition
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create execution instance
        execution = WorkflowExecution(
            id=str(uuid4()),
            workflow_id=workflow_id,
            input_data=input_data,
            context=context or {},
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            status=WorkflowStatus.PENDING
        )
        
        # Save initial execution state
        await self.repository.save_execution(execution)
        
        # Emit workflow started event
        await self._emit_event(
            "workflow.started",
            {
                "execution_id": execution.id,
                "workflow_id": workflow_id,
                "user_id": user_id
            }
        )
        
        # Start async execution
        async with self._execution_lock:
            task = asyncio.create_task(self._execute_workflow_async(workflow, execution))
            self._running_executions[execution.id] = task
        
        return execution
    
    async def _execute_workflow_async(
        self,
        workflow: Workflow,
        execution: WorkflowExecution
    ) -> None:
        """Execute workflow steps asynchronously."""
        try:
            execution.status = WorkflowStatus.RUNNING
            execution.started_at = datetime.now(timezone.utc)
            await self.repository.save_execution(execution)
            
            # Execute each step
            for step in workflow.steps:
                # Check if execution is cancelled
                if execution.status == WorkflowStatus.CANCELLED:
                    break
                
                # Check step condition
                if not await self._evaluate_condition(step, execution):
                    await self._skip_step(execution, step)
                    continue
                
                # Execute step with retries
                success = await self._execute_step_with_retries(workflow, execution, step)
                
                if not success and step.on_failure == "fail":
                    execution.status = WorkflowStatus.FAILED
                    break
            
            # Complete workflow if not failed or cancelled
            if execution.status == WorkflowStatus.RUNNING:
                execution.status = WorkflowStatus.COMPLETED
                execution.completed_at = datetime.now(timezone.utc)
            
            await self.repository.save_execution(execution)
            
            # Emit completion event
            await self._emit_event(
                f"workflow.{execution.status.value}",
                {
                    "execution_id": execution.id,
                    "workflow_id": workflow.id,
                    "output": execution.output_data,
                    "error": execution.error
                }
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now(timezone.utc)
            await self.repository.save_execution(execution)
            
            # Emit failure event
            await self._emit_event(
                "workflow.failed",
                {
                    "execution_id": execution.id,
                    "workflow_id": workflow.id,
                    "error": str(e)
                }
            )
        
        finally:
            # Remove from running executions
            async with self._execution_lock:
                self._running_executions.pop(execution.id, None)
    
    async def _execute_step_with_retries(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        step: WorkflowStep
    ) -> bool:
        """Execute a step with retry logic."""
        attempts = 0
        max_attempts = step.retries + 1
        
        while attempts < max_attempts:
            try:
                await self._execute_step(workflow, execution, step)
                return True
            
            except Exception as e:
                attempts += 1
                logger.warning(
                    f"Step {step.name} failed (attempt {attempts}/{max_attempts}): {e}"
                )
                
                if attempts < max_attempts:
                    await asyncio.sleep(2 ** attempts)  # Exponential backoff
                else:
                    # Final failure
                    exec_step = self._get_execution_step(execution, step.id)
                    if exec_step:
                        exec_step.status = StepStatus.FAILED
                        exec_step.error = str(e)
                        exec_step.completed_at = datetime.now(timezone.utc)
                    
                    await self.repository.save_execution(execution)
                    return False
        
        return False
    
    async def _execute_step(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        step: WorkflowStep
    ) -> None:
        """Execute a single workflow step."""
        # Create/update execution step
        exec_step = self._get_or_create_execution_step(execution, step)
        exec_step.status = StepStatus.RUNNING
        exec_step.started_at = datetime.now(timezone.utc)
        await self.repository.save_execution(execution)
        
        # Emit step started event
        await self._emit_event(
            "workflow.step.started",
            {
                "execution_id": execution.id,
                "step_id": step.id,
                "step_name": step.name,
                "agent_type": step.agent_type.value
            }
        )
        
        try:
            # Get the agent
            agent = await self.agent_registry.get_agent(step.agent_type)
            if not agent:
                raise ValueError(f"Agent {step.agent_type} not found")
            
            # Prepare input data
            step_input = self._prepare_step_input(execution, step)
            
            # Create agent input
            agent_input = AgentInput(
                content=step_input,
                content_type="application/json",
                metadata={"workflow_execution_id": execution.id},
                source="workflow_engine"
            )
            
            # Execute agent with timeout
            agent_output = await asyncio.wait_for(
                agent.process(agent_input),
                timeout=step.timeout
            )
            
            # Update execution with output
            exec_step.output = agent_output.content
            exec_step.status = StepStatus.COMPLETED
            exec_step.completed_at = datetime.now(timezone.utc)
            
            # Apply output mappings
            self._apply_output_mappings(execution, step, agent_output.content)
            
            await self.repository.save_execution(execution)
            
            # Emit step completed event
            await self._emit_event(
                "workflow.step.completed",
                {
                    "execution_id": execution.id,
                    "step_id": step.id,
                    "output": agent_output.content
                }
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Step {step.name} timed out after {step.timeout}s")
            exec_step.status = StepStatus.FAILED
            exec_step.error = f"Timeout after {step.timeout}s"
            exec_step.completed_at = datetime.now(timezone.utc)
            await self.repository.save_execution(execution)
            raise
        
        except Exception as e:
            logger.error(f"Step {step.name} failed: {e}")
            exec_step.status = StepStatus.FAILED
            exec_step.error = str(e)
            exec_step.completed_at = datetime.now(timezone.utc)
            await self.repository.save_execution(execution)
            raise
    
    async def _evaluate_condition(
        self,
        step: WorkflowStep,
        execution: WorkflowExecution
    ) -> bool:
        """Evaluate step execution condition."""
        if not step.condition:
            return True
        
        try:
            # Prepare context for condition evaluation
            context = {
                "input": execution.input_data,
                "context": execution.context,
                "steps": {
                    s.step_id: s.output
                    for s in execution.steps
                    if s.status == StepStatus.COMPLETED
                }
            }
            
            # Simple condition evaluation
            # In production, use a sandboxed evaluator
            return eval(step.condition, {"__builtins__": {}}, context)
        
        except Exception as e:
            logger.error(f"Condition evaluation failed for step {step.name}: {e}")
            return False
    
    async def _skip_step(self, execution: WorkflowExecution, step: WorkflowStep) -> None:
        """Mark a step as skipped."""
        exec_step = self._get_or_create_execution_step(execution, step)
        exec_step.status = StepStatus.SKIPPED
        exec_step.completed_at = datetime.now(timezone.utc)
        await self.repository.save_execution(execution)
        
        await self._emit_event(
            "workflow.step.skipped",
            {
                "execution_id": execution.id,
                "step_id": step.id,
                "step_name": step.name
            }
        )
    
    def _get_execution_step(
        self,
        execution: WorkflowExecution,
        step_id: str
    ) -> Optional[ExecutionStep]:
        """Get execution step by ID."""
        for exec_step in execution.steps:
            if exec_step.step_id == step_id:
                return exec_step
        return None
    
    def _get_or_create_execution_step(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep
    ) -> ExecutionStep:
        """Get or create an execution step."""
        exec_step = self._get_execution_step(execution, step.id)
        
        if not exec_step:
            exec_step = ExecutionStep(
                step_id=step.id,
                status=StepStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
            execution.steps.append(exec_step)
        
        return exec_step
    
    def _prepare_step_input(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep
    ) -> Dict[str, Any]:
        """Prepare input data for a step using input mappings."""
        step_input = {}
        
        for mapping in step.input_mappings:
            value = None
            
            # Get value from source
            if mapping.source == "input":
                value = self._get_nested_value(execution.input_data, mapping.source_key)
            elif mapping.source == "context":
                value = self._get_nested_value(execution.context, mapping.source_key)
            elif mapping.source == "steps":
                # Get output from a previous step
                parts = mapping.source_key.split(".", 1)
                if len(parts) == 2:
                    step_id, output_key = parts
                    for exec_step in execution.steps:
                        if exec_step.step_id == step_id and exec_step.output:
                            value = self._get_nested_value(exec_step.output, output_key)
                            break
            
            # Apply transformation if specified
            if value is not None and mapping.transform:
                value = self._apply_transform(value, mapping.transform)
            
            # Set the value in step input
            self._set_nested_value(step_input, mapping.target_key, value)
        
        return step_input
    
    def _apply_output_mappings(
        self,
        execution: WorkflowExecution,
        step: WorkflowStep,
        output: Dict[str, Any]
    ) -> None:
        """Apply output mappings from step output to execution context."""
        if not execution.output_data:
            execution.output_data = {}
        
        for mapping in step.output_mappings:
            value = self._get_nested_value(output, mapping.source_key)
            
            if value is not None and mapping.transform:
                value = self._apply_transform(value, mapping.transform)
            
            # Determine target location
            if mapping.target == "output":
                self._set_nested_value(execution.output_data, mapping.target_key, value)
            elif mapping.target == "context":
                self._set_nested_value(execution.context, mapping.target_key, value)
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = key.split(".")
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation."""
        keys = key.split(".")
        target = data
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
    
    def _apply_transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to a value."""
        # Simple transformations
        if transform == "json_parse":
            return json.loads(value) if isinstance(value, str) else value
        elif transform == "json_stringify":
            return json.dumps(value) if not isinstance(value, str) else value
        elif transform == "to_upper":
            return value.upper() if isinstance(value, str) else value
        elif transform == "to_lower":
            return value.lower() if isinstance(value, str) else value
        
        return value
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running workflow execution."""
        async with self._execution_lock:
            if execution_id in self._running_executions:
                # Update execution status
                execution = await self.repository.get_execution(execution_id)
                if execution:
                    execution.status = WorkflowStatus.CANCELLED
                    execution.completed_at = datetime.now(timezone.utc)
                    await self.repository.save_execution(execution)
                
                # Cancel the task
                task = self._running_executions[execution_id]
                task.cancel()
                
                # Emit cancellation event
                await self._emit_event(
                    "workflow.cancelled",
                    {"execution_id": execution_id}
                )
                
                return True
        
        return False
    
    async def get_execution_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get the current status of a workflow execution."""
        return await self.repository.get_execution(execution_id)
    
    async def list_executions(
        self,
        workflow_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters."""
        return await self.repository.list_executions(
            workflow_id=workflow_id,
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to the event bus."""
        event_metadata = EventMetadata(
            event_id=str(uuid4()),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            source="workflow_engine"
        )
        
        await self.event_bus.publish(event_type, {"metadata": event_metadata.dict(), "payload": data})
    
    async def _handle_cancel_event(self, message: Dict[str, Any]) -> None:
        """Handle workflow cancellation events."""
        try:
            data = message.get("data", {})
            execution_id = data.get("payload", {}).get("execution_id")
            
            if execution_id:
                await self.cancel_execution(execution_id)
        
        except Exception as e:
            logger.error(f"Failed to handle cancel event: {e}")
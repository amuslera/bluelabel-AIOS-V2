"""
Agent Runtime Manager - Core component for managing agent lifecycle and execution
"""
import asyncio
import time
from typing import Dict, Any, List, Type, Optional
from datetime import datetime
import threading
from collections import defaultdict
import traceback

from agents.base import Agent, AgentInput, AgentOutput
from core.logging import setup_logging, LogContext
from core.event_bus import EventBus
from core.event_patterns import Message
from shared.schemas.base import BaseModel

# Set up logging
logger = setup_logging(service_name="agent-runtime")


class AgentMetrics(BaseModel):
    """Metrics for agent execution"""
    agent_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    last_execution_time: Optional[datetime] = None
    errors: List[Dict[str, Any]] = []


class AgentRuntimeManager:
    """
    Manages agent lifecycle and execution
    
    Responsibilities:
    - Agent registration and discovery
    - Input/output validation
    - Execution orchestration
    - Metrics collection
    - Error handling and recovery
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize the runtime manager"""
        self.agents: Dict[str, Agent] = {}
        self.agent_classes: Dict[str, Type[Agent]] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.metrics: Dict[str, AgentMetrics] = defaultdict(
            lambda: AgentMetrics(agent_id="unknown")
        )
        self.event_bus = event_bus or EventBus(simulation_mode=True)
        self._lock = threading.RLock()
        
        logger.info("Agent Runtime Manager initialized")
    
    def register_agent_class(self, agent_id: str, agent_class: Type[Agent], config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register an agent class for later instantiation
        
        Args:
            agent_id: Unique identifier for the agent
            agent_class: The agent class to register
            config: Optional configuration for the agent
            
        Returns:
            bool: True if registration successful
        """
        with self._lock:
            try:
                # Validate the agent class
                if not issubclass(agent_class, Agent):
                    raise ValueError(f"{agent_class} is not a subclass of Agent")
                
                # Store the class and config
                self.agent_classes[agent_id] = agent_class
                self.agent_configs[agent_id] = config or {}
                
                logger.info(f"Registered agent class: {agent_id} ({agent_class.__name__})")
                
                # Publish registration event
                event = Message(
                    type="agent.class.registered",
                    source="agent_runtime",
                    payload={
                        "agent_id": agent_id,
                        "agent_class": agent_class.__name__,
                        "config": config
                    }
                )
                self.event_bus.publish("agent_events", event)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to register agent class {agent_id}: {str(e)}")
                return False
    
    async def create_agent_instance(self, agent_id: str) -> bool:
        """
        Create an instance of a registered agent
        
        Args:
            agent_id: The ID of the agent to instantiate
            
        Returns:
            bool: True if instantiation successful
        """
        with self._lock:
            try:
                # Check if already instantiated
                if agent_id in self.agents:
                    logger.warning(f"Agent {agent_id} already instantiated")
                    return True
                
                # Get the class and config
                agent_class = self.agent_classes.get(agent_id)
                if not agent_class:
                    raise ValueError(f"Agent class {agent_id} not registered")
                
                config = self.agent_configs.get(agent_id, {})
                
                # Create the instance
                agent_instance = agent_class(
                    name=agent_id,
                    description=config.get("description", f"Agent {agent_id}")
                )
                
                # Initialize the agent
                agent_instance.initialize()
                
                # Store the instance
                self.agents[agent_id] = agent_instance
                
                # Initialize metrics
                self.metrics[agent_id] = AgentMetrics(agent_id=agent_id)
                
                logger.info(f"Created agent instance: {agent_id}")
                
                # Publish creation event
                event = Message(
                    type="agent.instance.created",
                    source="agent_runtime",
                    payload={
                        "agent_id": agent_id,
                        "agent_class": agent_class.__name__,
                        "capabilities": agent_instance.get_capabilities()
                    }
                )
                self.event_bus.publish("agent_events", event)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to create agent instance {agent_id}: {str(e)}")
                return False
    
    async def execute_agent(self, agent_id: str, input_data: AgentInput) -> AgentOutput:
        """
        Execute an agent with the given input
        
        Args:
            agent_id: The ID of the agent to execute
            input_data: The input data for the agent
            
        Returns:
            AgentOutput: The agent's execution result
        """
        start_time = time.time()
        
        # Add context for logging
        with LogContext(logger, agent_id=agent_id, task_id=input_data.task_id):
            logger.info(f"Executing agent {agent_id}")
            
            try:
                # Get the agent instance
                agent = self.agents.get(agent_id)
                if not agent:
                    # Try to create the instance if not exists
                    if agent_id in self.agent_classes:
                        created = await self.create_agent_instance(agent_id)
                        if created:
                            agent = self.agents[agent_id]
                        else:
                            raise ValueError(f"Failed to create agent instance {agent_id}")
                    else:
                        raise ValueError(f"Agent {agent_id} not found")
                
                # Execute the agent
                result = await self._execute_with_timeout(agent, input_data)
                
                # Update metrics
                execution_time = time.time() - start_time
                self._update_metrics(agent_id, "success", execution_time)
                
                logger.info(f"Agent {agent_id} executed successfully in {execution_time:.3f}s")
                
                # Publish execution event
                event = Message(
                    type="agent.execution.completed",
                    source="agent_runtime",
                    payload={
                        "agent_id": agent_id,
                        "task_id": input_data.task_id,
                        "status": result.status,
                        "execution_time": execution_time
                    }
                )
                self.event_bus.publish("agent_events", event)
                
                return result
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                error_msg = f"Agent {agent_id} execution timed out after {execution_time:.3f}s"
                logger.error(error_msg)
                self._update_metrics(agent_id, "timeout", execution_time, error_msg)
                
                return AgentOutput(
                    task_id=input_data.task_id,
                    status="error",
                    error=error_msg
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"Agent {agent_id} execution failed: {str(e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                self._update_metrics(agent_id, "error", execution_time, error_msg)
                
                return AgentOutput(
                    task_id=input_data.task_id,
                    status="error",
                    error=error_msg
                )
    
    async def _execute_with_timeout(self, agent: Agent, input_data: AgentInput, timeout: float = 300.0) -> AgentOutput:
        """
        Execute an agent with a timeout
        
        Args:
            agent: The agent instance to execute
            input_data: The input data
            timeout: Timeout in seconds (default 5 minutes)
            
        Returns:
            AgentOutput: The execution result
        """
        # Check if the process method is async
        import inspect
        if inspect.iscoroutinefunction(agent.process):
            # Async execution
            return await asyncio.wait_for(agent.process(input_data), timeout=timeout)
        else:
            # Sync execution in thread pool
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, agent.process, input_data),
                timeout=timeout
            )
    
    def _update_metrics(self, agent_id: str, status: str, execution_time: float, error: Optional[str] = None):
        """Update metrics for an agent execution"""
        with self._lock:
            metrics = self.metrics[agent_id]
            metrics.total_executions += 1
            
            if status == "success":
                metrics.successful_executions += 1
            else:
                metrics.failed_executions += 1
                if error:
                    metrics.errors.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": error,
                        "type": status
                    })
                    # Keep only last 10 errors
                    metrics.errors = metrics.errors[-10:]
            
            # Update average execution time
            if metrics.average_execution_time == 0:
                metrics.average_execution_time = execution_time
            else:
                metrics.average_execution_time = (
                    (metrics.average_execution_time * (metrics.total_executions - 1) + execution_time) /
                    metrics.total_executions
                )
            
            metrics.last_execution_time = datetime.utcnow()
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent"""
        with self._lock:
            if agent_id not in self.agents and agent_id not in self.agent_classes:
                return None
            
            info = {
                "agent_id": agent_id,
                "registered": agent_id in self.agent_classes,
                "instantiated": agent_id in self.agents,
                "config": self.agent_configs.get(agent_id, {}),
                "metrics": self.metrics[agent_id].dict() if agent_id in self.metrics else None
            }
            
            if agent_id in self.agents:
                info["capabilities"] = self.agents[agent_id].get_capabilities()
            
            return info
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        with self._lock:
            agents = []
            
            # Include all registered agents
            for agent_id in set(list(self.agent_classes.keys()) + list(self.agents.keys())):
                info = self.get_agent_info(agent_id)
                if info:
                    agents.append(info)
            
            return agents
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for all agents"""
        with self._lock:
            return {
                "total_agents": len(self.agent_classes),
                "active_agents": len(self.agents),
                "agent_metrics": {
                    agent_id: metrics.dict()
                    for agent_id, metrics in self.metrics.items()
                }
            }
    
    async def shutdown(self):
        """Shutdown the runtime manager"""
        logger.info("Shutting down Agent Runtime Manager")
        
        # Shutdown all agent instances
        for agent_id, agent in self.agents.items():
            try:
                if hasattr(agent, 'shutdown'):
                    await agent.shutdown()
                logger.info(f"Shut down agent {agent_id}")
            except Exception as e:
                logger.error(f"Error shutting down agent {agent_id}: {str(e)}")
        
        self.agents.clear()
        self.agent_classes.clear()
        self.agent_configs.clear()
        self.metrics.clear()
        
        logger.info("Agent Runtime Manager shutdown complete")


# Global instance (optional, for singleton pattern)
_runtime_manager: Optional[AgentRuntimeManager] = None


def get_runtime_manager() -> AgentRuntimeManager:
    """Get the global runtime manager instance"""
    global _runtime_manager
    if _runtime_manager is None:
        _runtime_manager = AgentRuntimeManager()
    return _runtime_manager
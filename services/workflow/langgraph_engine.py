"""LangGraph-based workflow orchestration engine.

This module wraps LangGraph to provide workflow orchestration capabilities
while maintaining compatibility with our Agent interface.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, TypedDict
from datetime import datetime
import logging

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from agents.base import Agent, AgentInput, AgentOutput
from core.event_bus import EventBus
from core.config import get_settings

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State that flows through the workflow."""
    messages: List[BaseMessage]
    step_outputs: Dict[str, AgentOutput]
    current_step: str
    context: Dict[str, Any]
    error: Optional[str]
    completed_steps: List[str]
    timestamp: str


class LangGraphWorkflowEngine:
    """Workflow orchestration engine using LangGraph."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize the workflow engine.
        
        Args:
            event_bus: Optional event bus for publishing workflow events
        """
        self.event_bus = event_bus
        self.workflows: Dict[str, CompiledStateGraph] = {}
        self.agents: Dict[str, Agent] = {}
        self.settings = get_settings()
    
    def register_agent(self, name: str, agent: Agent):
        """Register an agent that can be used in workflows.
        
        Args:
            name: Unique name for the agent
            agent: Agent instance
        """
        self.agents[name] = agent
        logger.info(f"Registered agent: {name}")
    
    def _create_agent_node(self, agent_name: str) -> Callable:
        """Create a node function for an agent.
        
        Args:
            agent_name: Name of the registered agent
            
        Returns:
            Node function for LangGraph
        """
        async def agent_node(state: WorkflowState) -> Dict[str, Any]:
            try:
                agent = self.agents.get(agent_name)
                if not agent:
                    raise ValueError(f"Agent '{agent_name}' not found")
                
                # Prepare input for agent
                last_message = state["messages"][-1] if state["messages"] else None
                content = last_message.content if last_message else ""
                
                agent_input = AgentInput(
                    content=content,
                    context=state.get("context", {}),
                    metadata={
                        "workflow_state": state,
                        "previous_steps": state.get("completed_steps", [])
                    }
                )
                
                # Execute agent
                logger.info(f"Executing agent: {agent_name}")
                output = await agent.process(agent_input)
                
                # Update state
                new_state = state.copy()
                new_state["step_outputs"][agent_name] = output
                new_state["completed_steps"].append(agent_name)
                new_state["current_step"] = agent_name
                
                # Add agent response to messages
                new_state["messages"].append(
                    AIMessage(
                        content=output.content.get("response", ""),
                        name=agent_name
                    )
                )
                
                # Publish event if event bus is available
                if self.event_bus:
                    await self.event_bus.publish({
                        "event_type": "workflow.step.completed",
                        "payload": {
                            "workflow_id": state.get("context", {}).get("workflow_id"),
                            "step": agent_name,
                            "output": output.dict()
                        }
                    })
                
                return new_state
                
            except Exception as e:
                logger.error(f"Error in agent node {agent_name}: {e}")
                state["error"] = str(e)
                return state
        
        return agent_node
    
    def create_workflow(self, 
                       name: str,
                       agent_sequence: List[str],
                       conditional_routing: Optional[Dict[str, Callable]] = None) -> str:
        """Create a new workflow with a sequence of agents.
        
        Args:
            name: Unique name for the workflow
            agent_sequence: List of agent names to execute in order
            conditional_routing: Optional conditional routing logic
            
        Returns:
            Workflow ID
        """
        try:
            # Create state graph
            workflow = StateGraph(WorkflowState)
            
            # Add start node
            def start_node(state: WorkflowState) -> Dict[str, Any]:
                state["timestamp"] = datetime.utcnow().isoformat()
                state["completed_steps"] = []
                state["step_outputs"] = {}
                state["current_step"] = "start"
                return state
            
            workflow.add_node("start", start_node)
            workflow.set_entry_point("start")
            
            # Add agent nodes
            for i, agent_name in enumerate(agent_sequence):
                node_func = self._create_agent_node(agent_name)
                workflow.add_node(agent_name, node_func)
                
                # Add edge from previous node
                prev_node = "start" if i == 0 else agent_sequence[i-1]
                
                if conditional_routing and agent_name in conditional_routing:
                    # Add conditional routing
                    workflow.add_conditional_edges(
                        prev_node,
                        conditional_routing[agent_name],
                        {agent_name: agent_name, "end": END}
                    )
                else:
                    # Add direct edge
                    workflow.add_edge(prev_node, agent_name)
            
            # Add edge from last agent to END
            if agent_sequence:
                last_agent = agent_sequence[-1]
                if not (conditional_routing and last_agent in conditional_routing):
                    workflow.add_edge(last_agent, END)
            
            # Compile workflow
            compiled_workflow = workflow.compile()
            self.workflows[name] = compiled_workflow
            
            logger.info(f"Created workflow: {name} with agents: {agent_sequence}")
            return name
            
        except Exception as e:
            logger.error(f"Error creating workflow {name}: {e}")
            raise
    
    async def execute_workflow(self,
                              workflow_name: str,
                              input_data: Dict[str, Any],
                              config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow.
        
        Args:
            workflow_name: Name of the workflow to execute
            input_data: Input data for the workflow
            config: Optional configuration for the workflow
            
        Returns:
            Workflow execution result
        """
        workflow = self.workflows.get(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        # Initialize state
        initial_state: WorkflowState = {
            "messages": [HumanMessage(content=input_data.get("content", ""))],
            "step_outputs": {},
            "current_step": "start",
            "context": {
                "workflow_id": f"{workflow_name}_{datetime.utcnow().timestamp()}",
                "workflow_name": workflow_name,
                "input_data": input_data,
                **(config or {})
            },
            "error": None,
            "completed_steps": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Publish workflow start event
            if self.event_bus:
                await self.event_bus.publish({
                    "event_type": "workflow.started",
                    "payload": {
                        "workflow_id": initial_state["context"]["workflow_id"],
                        "workflow_name": workflow_name,
                        "input_data": input_data
                    }
                })
            
            # Execute workflow
            logger.info(f"Executing workflow: {workflow_name}")
            final_state = await workflow.ainvoke(initial_state)
            
            # Publish workflow completion event
            if self.event_bus:
                await self.event_bus.publish({
                    "event_type": "workflow.completed",
                    "payload": {
                        "workflow_id": initial_state["context"]["workflow_id"],
                        "workflow_name": workflow_name,
                        "completed_steps": final_state["completed_steps"],
                        "outputs": final_state["step_outputs"]
                    }
                })
            
            return {
                "status": "completed",
                "workflow_id": initial_state["context"]["workflow_id"],
                "completed_steps": final_state["completed_steps"],
                "outputs": final_state["step_outputs"],
                "messages": [msg.content for msg in final_state["messages"]],
                "error": final_state.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_name}: {e}")
            
            # Publish workflow error event
            if self.event_bus:
                await self.event_bus.publish({
                    "event_type": "workflow.error",
                    "payload": {
                        "workflow_id": initial_state["context"]["workflow_id"],
                        "workflow_name": workflow_name,
                        "error": str(e)
                    }
                })
            
            return {
                "status": "error",
                "workflow_id": initial_state["context"]["workflow_id"],
                "error": str(e)
            }
    
    def list_workflows(self) -> List[str]:
        """List all registered workflows."""
        return list(self.workflows.keys())
    
    def get_workflow_info(self, workflow_name: str) -> Dict[str, Any]:
        """Get information about a workflow."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        # This is a simplified implementation
        # In a real system, we'd store more metadata about workflows
        return {
            "name": workflow_name,
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
    
    def create_conditional_workflow(self,
                                   name: str,
                                   decision_points: Dict[str, Dict[str, Any]]) -> str:
        """Create a workflow with conditional branching.
        
        Args:
            name: Workflow name
            decision_points: Dictionary defining decision points and branches
            
        Returns:
            Workflow ID
        """
        # This is a more complex workflow creation method that supports
        # conditional branching based on agent outputs
        
        workflow = StateGraph(WorkflowState)
        
        # Add start node
        def start_node(state: WorkflowState) -> Dict[str, Any]:
            state["timestamp"] = datetime.utcnow().isoformat()
            state["completed_steps"] = []
            state["step_outputs"] = {}
            state["current_step"] = "start"
            return state
        
        workflow.add_node("start", start_node)
        workflow.set_entry_point("start")
        
        # Process decision points
        for point_name, config in decision_points.items():
            agent_name = config["agent"]
            branches = config["branches"]
            
            # Add agent node
            node_func = self._create_agent_node(agent_name)
            workflow.add_node(agent_name, node_func)
            
            # Create routing function
            def create_router(branches_config):
                def router(state: WorkflowState) -> str:
                    agent_output = state["step_outputs"].get(agent_name)
                    if not agent_output:
                        return "end"
                    
                    # Evaluate conditions
                    for condition, next_step in branches_config.items():
                        if condition == "default":
                            continue
                        # Simple condition evaluation (can be made more sophisticated)
                        if condition in str(agent_output.content):
                            return next_step
                    
                    return branches_config.get("default", "end")
                return router
            
            # Add conditional edges
            workflow.add_conditional_edges(
                agent_name,
                create_router(branches),
                {next_step: next_step for next_step in branches.values()}
            )
        
        # Compile workflow
        compiled_workflow = workflow.compile()
        self.workflows[name] = compiled_workflow
        
        logger.info(f"Created conditional workflow: {name}")
        return name


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create workflow engine
        engine = LangGraphWorkflowEngine()
        
        # Create mock agents
        class MockAgent(Agent):
            def __init__(self, name: str):
                self.name = name
            
            async def process(self, input: AgentInput) -> AgentOutput:
                return AgentOutput(
                    success=True,
                    content={"response": f"{self.name} processed: {input.content}"},
                    metadata={"agent": self.name}
                )
            
            def get_capabilities(self) -> Dict[str, Any]:
                return {"name": self.name}
            
            async def initialize(self) -> bool:
                return True
            
            async def shutdown(self) -> bool:
                return True
        
        # Register agents
        engine.register_agent("analyzer", MockAgent("analyzer"))
        engine.register_agent("processor", MockAgent("processor"))
        engine.register_agent("formatter", MockAgent("formatter"))
        
        # Create workflow
        workflow_id = engine.create_workflow(
            name="content_pipeline",
            agent_sequence=["analyzer", "processor", "formatter"]
        )
        
        # Execute workflow
        result = await engine.execute_workflow(
            workflow_name="content_pipeline",
            input_data={"content": "Test content to process"}
        )
        
        print(f"Workflow result: {result}")
    
    # Run example
    asyncio.run(example_usage())
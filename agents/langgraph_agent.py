"""LangGraph agent wrapper.

This module provides a wrapper that allows LangGraph workflows to be used
as agents within our system, maintaining compatibility with the Agent interface.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from agents.base import Agent, AgentInput, AgentOutput
from services.workflow.langgraph_engine import LangGraphWorkflowEngine

logger = logging.getLogger(__name__)


class LangGraphAgent(Agent):
    """Wrapper to use LangGraph workflows as agents."""
    
    def __init__(self, 
                 agent_id: str,
                 workflow_name: str,
                 workflow_engine: LangGraphWorkflowEngine,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize the LangGraph agent wrapper.
        
        Args:
            agent_id: Unique identifier for this agent
            workflow_name: Name of the LangGraph workflow to execute
            workflow_engine: LangGraph workflow engine instance
            metadata: Optional metadata for the agent
        """
        super().__init__(agent_id, metadata)
        self.workflow_name = workflow_name
        self.workflow_engine = workflow_engine
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the agent."""
        try:
            # Verify workflow exists
            workflows = self.workflow_engine.list_workflows()
            if self.workflow_name not in workflows:
                logger.error(f"Workflow '{self.workflow_name}' not found")
                return False
            
            self._initialized = True
            logger.info(f"LangGraphAgent {self.agent_id} initialized with workflow {self.workflow_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing LangGraphAgent: {e}")
            return False
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process input using the LangGraph workflow.
        
        Args:
            input: Agent input
            
        Returns:
            Agent output
        """
        if not self._initialized:
            return AgentOutput(
                success=False,
                content={"error": "Agent not initialized"},
                metadata={"agent_id": self.agent_id}
            )
        
        try:
            # Prepare workflow input
            workflow_input = {
                "content": input.content,
                "context": input.context,
                "metadata": input.metadata
            }
            
            # Execute workflow
            logger.info(f"Executing workflow {self.workflow_name} for agent {self.agent_id}")
            result = await self.workflow_engine.execute_workflow(
                workflow_name=self.workflow_name,
                input_data=workflow_input,
                config={
                    "agent_id": self.agent_id,
                    "execution_id": f"{self.agent_id}_{datetime.utcnow().timestamp()}"
                }
            )
            
            # Process workflow result
            if result["status"] == "completed":
                # Aggregate outputs from all workflow steps
                aggregated_content = {}
                for step, output in result.get("outputs", {}).items():
                    aggregated_content[step] = output.content
                
                return AgentOutput(
                    success=True,
                    content={
                        "workflow_outputs": aggregated_content,
                        "completed_steps": result["completed_steps"],
                        "final_message": result["messages"][-1] if result["messages"] else ""
                    },
                    metadata={
                        "agent_id": self.agent_id,
                        "workflow_id": result["workflow_id"],
                        "workflow_name": self.workflow_name,
                        "completed_steps": result["completed_steps"]
                    }
                )
            else:
                return AgentOutput(
                    success=False,
                    content={"error": result.get("error", "Unknown error")},
                    metadata={
                        "agent_id": self.agent_id,
                        "workflow_id": result.get("workflow_id"),
                        "workflow_name": self.workflow_name
                    }
                )
            
        except Exception as e:
            logger.error(f"Error processing with LangGraphAgent: {e}")
            return AgentOutput(
                success=False,
                content={"error": str(e)},
                metadata={"agent_id": self.agent_id}
            )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "agent_id": self.agent_id,
            "type": "langgraph_workflow",
            "workflow_name": self.workflow_name,
            "supports_streaming": False,
            "supports_async": True
        }
    
    async def shutdown(self) -> bool:
        """Shutdown the agent."""
        self._initialized = False
        logger.info(f"LangGraphAgent {self.agent_id} shutdown")
        return True


class LangGraphAgentFactory:
    """Factory for creating LangGraph agents."""
    
    def __init__(self, workflow_engine: LangGraphWorkflowEngine):
        """Initialize the factory.
        
        Args:
            workflow_engine: LangGraph workflow engine instance
        """
        self.workflow_engine = workflow_engine
    
    def create_agent(self,
                    agent_id: str,
                    workflow_name: str,
                    metadata: Optional[Dict[str, Any]] = None) -> LangGraphAgent:
        """Create a new LangGraph agent.
        
        Args:
            agent_id: Unique identifier for the agent
            workflow_name: Name of the workflow to use
            metadata: Optional metadata
            
        Returns:
            LangGraphAgent instance
        """
        return LangGraphAgent(
            agent_id=agent_id,
            workflow_name=workflow_name,
            workflow_engine=self.workflow_engine,
            metadata=metadata
        )
    
    def create_agent_from_definition(self,
                                    definition: Dict[str, Any]) -> LangGraphAgent:
        """Create an agent from a definition dictionary.
        
        Args:
            definition: Agent definition containing workflow configuration
            
        Returns:
            LangGraphAgent instance
        """
        # Extract workflow configuration
        workflow_config = definition.get("workflow", {})
        
        # Create workflow if it doesn't exist
        workflow_name = workflow_config.get("name", f"workflow_{definition['agent_id']}")
        
        if workflow_name not in self.workflow_engine.list_workflows():
            # Create workflow based on definition
            agent_sequence = workflow_config.get("agent_sequence", [])
            conditional_routing = workflow_config.get("conditional_routing")
            
            if conditional_routing:
                # Create conditional workflow
                self.workflow_engine.create_conditional_workflow(
                    name=workflow_name,
                    decision_points=conditional_routing
                )
            else:
                # Create sequential workflow
                self.workflow_engine.create_workflow(
                    name=workflow_name,
                    agent_sequence=agent_sequence
                )
        
        # Create agent
        return self.create_agent(
            agent_id=definition["agent_id"],
            workflow_name=workflow_name,
            metadata=definition.get("metadata")
        )


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create workflow engine
        engine = LangGraphWorkflowEngine()
        
        # Create mock sub-agents
        class MockSubAgent(Agent):
            def __init__(self, name: str):
                super().__init__(agent_id=name)
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
        
        # Register sub-agents
        engine.register_agent("extractor", MockSubAgent("extractor"))
        engine.register_agent("analyzer", MockSubAgent("analyzer"))
        engine.register_agent("summarizer", MockSubAgent("summarizer"))
        
        # Create workflow
        engine.create_workflow(
            name="content_processing",
            agent_sequence=["extractor", "analyzer", "summarizer"]
        )
        
        # Create LangGraph agent
        factory = LangGraphAgentFactory(engine)
        agent = factory.create_agent(
            agent_id="content_processor",
            workflow_name="content_processing"
        )
        
        # Initialize and use agent
        await agent.initialize()
        
        result = await agent.process(
            AgentInput(
                content="Process this content through the workflow",
                context={"user_id": "123"},
                metadata={"source": "api"}
            )
        )
        
        print(f"Agent result: {result.dict()}")
        
        await agent.shutdown()
    
    # Run example
    asyncio.run(example_usage())
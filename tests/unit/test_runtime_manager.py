"""
Unit tests for Agent Runtime Manager
"""
import pytest
import asyncio
from unittest.mock import Mock, patch

from agents.base import Agent, AgentInput, AgentOutput
from services.agent_runtime import AgentRuntimeManager, get_runtime_manager
from core.event_bus import EventBus


class MockAgent(Agent):
    """Mock agent for testing"""
    
    def initialize(self) -> None:
        """Initialize mock agent"""
        self.initialized = True
    
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process mock input"""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        if input_data.content.get("fail"):
            raise ValueError("Mock failure")
        
        return AgentOutput(
            task_id=input_data.task_id,
            status="success",
            result={"processed": input_data.content}
        )


class TestAgentRuntimeManager:
    """Test suite for Agent Runtime Manager"""
    
    @pytest.fixture
    def runtime_manager(self):
        """Create a runtime manager instance"""
        event_bus = EventBus(simulation_mode=True)
        return AgentRuntimeManager(event_bus=event_bus)
    
    @pytest.fixture
    def mock_agent_class(self):
        """Get the mock agent class"""
        return MockAgent
    
    def test_initialization(self, runtime_manager):
        """Test runtime manager initialization"""
        assert runtime_manager.agents == {}
        assert runtime_manager.agent_classes == {}
        assert runtime_manager.agent_configs == {}
        assert runtime_manager.event_bus is not None
    
    def test_register_agent_class(self, runtime_manager, mock_agent_class):
        """Test agent class registration"""
        config = {"description": "Test agent"}
        result = runtime_manager.register_agent_class(
            "test_agent",
            mock_agent_class,
            config
        )
        
        assert result is True
        assert "test_agent" in runtime_manager.agent_classes
        assert runtime_manager.agent_classes["test_agent"] == mock_agent_class
        assert runtime_manager.agent_configs["test_agent"] == config
    
    def test_register_invalid_agent_class(self, runtime_manager):
        """Test registration with invalid agent class"""
        class NotAnAgent:
            pass
        
        result = runtime_manager.register_agent_class(
            "invalid_agent",
            NotAnAgent,
            {}
        )
        
        assert result is False
        assert "invalid_agent" not in runtime_manager.agent_classes
    
    @pytest.mark.asyncio
    async def test_create_agent_instance(self, runtime_manager, mock_agent_class):
        """Test agent instance creation"""
        # Register the class first
        runtime_manager.register_agent_class("test_agent", mock_agent_class)
        
        # Create instance
        result = await runtime_manager.create_agent_instance("test_agent")
        
        assert result is True
        assert "test_agent" in runtime_manager.agents
        assert isinstance(runtime_manager.agents["test_agent"], MockAgent)
        assert runtime_manager.agents["test_agent"].initialized is True
    
    @pytest.mark.asyncio
    async def test_create_instance_without_registration(self, runtime_manager):
        """Test creating instance without registering class"""
        result = await runtime_manager.create_agent_instance("unknown_agent")
        
        assert result is False
        assert "unknown_agent" not in runtime_manager.agents
    
    @pytest.mark.asyncio
    async def test_execute_agent_success(self, runtime_manager, mock_agent_class):
        """Test successful agent execution"""
        # Register and create agent
        runtime_manager.register_agent_class("test_agent", mock_agent_class)
        
        # Execute agent
        input_data = AgentInput(
            source="test",
            content={"data": "test_data"}
        )
        
        result = await runtime_manager.execute_agent("test_agent", input_data)
        
        assert result.status == "success"
        assert result.task_id == input_data.task_id
        assert result.result["processed"]["data"] == "test_data"
        assert result.error is None
        
        # Check metrics
        metrics = runtime_manager.metrics["test_agent"]
        assert metrics.total_executions == 1
        assert metrics.successful_executions == 1
        assert metrics.failed_executions == 0
    
    @pytest.mark.asyncio
    async def test_execute_agent_failure(self, runtime_manager, mock_agent_class):
        """Test agent execution with failure"""
        # Register and create agent
        runtime_manager.register_agent_class("test_agent", mock_agent_class)
        
        # Execute agent with failure flag
        input_data = AgentInput(
            source="test",
            content={"fail": True}
        )
        
        result = await runtime_manager.execute_agent("test_agent", input_data)
        
        assert result.status == "error"
        assert result.task_id == input_data.task_id
        assert "Mock failure" in result.error
        
        # Check metrics
        metrics = runtime_manager.metrics["test_agent"]
        assert metrics.total_executions == 1
        assert metrics.successful_executions == 0
        assert metrics.failed_executions == 1
        assert len(metrics.errors) == 1
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_agent(self, runtime_manager):
        """Test executing a non-existent agent"""
        input_data = AgentInput(
            source="test",
            content={"data": "test"}
        )
        
        result = await runtime_manager.execute_agent("unknown_agent", input_data)
        
        assert result.status == "error"
        assert "not found" in result.error
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, runtime_manager):
        """Test agent execution with timeout"""
        class SlowAgent(Agent):
            def initialize(self) -> None:
                pass
            
            async def process(self, input_data: AgentInput) -> AgentOutput:
                await asyncio.sleep(10)  # Sleep longer than timeout
                return AgentOutput(
                    task_id=input_data.task_id,
                    status="success"
                )
        
        runtime_manager.register_agent_class("slow_agent", SlowAgent)
        
        input_data = AgentInput(source="test", content={})
        
        # Execute with short timeout
        with patch.object(runtime_manager, '_execute_with_timeout', 
                         wraps=runtime_manager._execute_with_timeout) as mock_execute:
            result = await runtime_manager.execute_agent("slow_agent", input_data)
            
            # Modify the timeout in the wrapped call
            args, kwargs = mock_execute.call_args
            kwargs['timeout'] = 0.1
            result = await runtime_manager._execute_with_timeout(*args, **kwargs)
        
        assert result.status == "error"
        assert "timed out" in result.error.lower()
    
    def test_get_agent_info(self, runtime_manager, mock_agent_class):
        """Test getting agent information"""
        # Register agent
        config = {"description": "Test agent", "version": "1.0"}
        runtime_manager.register_agent_class("test_agent", mock_agent_class, config)
        
        # Get info before instantiation
        info = runtime_manager.get_agent_info("test_agent")
        
        assert info is not None
        assert info["agent_id"] == "test_agent"
        assert info["registered"] is True
        assert info["instantiated"] is False
        assert info["config"] == config
        
        # Get info for non-existent agent
        info = runtime_manager.get_agent_info("unknown_agent")
        assert info is None
    
    def test_list_agents(self, runtime_manager, mock_agent_class):
        """Test listing all agents"""
        # Register multiple agents
        runtime_manager.register_agent_class("agent1", mock_agent_class)
        runtime_manager.register_agent_class("agent2", mock_agent_class)
        
        agents = runtime_manager.list_agents()
        
        assert len(agents) == 2
        agent_ids = [agent["agent_id"] for agent in agents]
        assert "agent1" in agent_ids
        assert "agent2" in agent_ids
    
    def test_get_metrics(self, runtime_manager, mock_agent_class):
        """Test getting metrics"""
        runtime_manager.register_agent_class("test_agent", mock_agent_class)
        
        metrics = runtime_manager.get_metrics()
        
        assert metrics["total_agents"] == 1
        assert metrics["active_agents"] == 0
        assert "agent_metrics" in metrics
    
    @pytest.mark.asyncio
    async def test_shutdown(self, runtime_manager, mock_agent_class):
        """Test runtime manager shutdown"""
        # Register and create an agent
        runtime_manager.register_agent_class("test_agent", mock_agent_class)
        await runtime_manager.create_agent_instance("test_agent")
        
        # Shutdown
        await runtime_manager.shutdown()
        
        assert len(runtime_manager.agents) == 0
        assert len(runtime_manager.agent_classes) == 0
        assert len(runtime_manager.agent_configs) == 0
        assert len(runtime_manager.metrics) == 0
    
    def test_singleton_pattern(self):
        """Test global runtime manager singleton"""
        manager1 = get_runtime_manager()
        manager2 = get_runtime_manager()
        
        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__])
# Bluelabel AIOS v2: Architecture & Implementation Plan

**Version**: `bluelabel-aios-v2-alpha` **Status**: Official implementation plan as of May 2025

## System Overview

Bluelabel AIOS (Agentic Intelligence Operating System) is a platform for developing, deploying, and orchestrating AI agents that perform automated and semi-automated tasks. The system integrates multiple LLM models (local and cloud), enables agent composition for complex workflows, and provides multiple access methods including API, web UI, mobile, email, and messaging platforms.

**Initial MVP Use Case**: Allow a user to submit a URL or PDF via email, have it processed by the ContentMind agent, summarized using a prompt from the MCP system, stored in the knowledge repository, and returned as a digest via email.

## Design Principles

1. **Modular Design with Service Boundaries**: Clear domain separation without premature microservice complexity
2. **API-First Development**: All functionality exposed via consistent REST APIs
3. **Multi-Tenant & Secure by Design**: Data isolation and security from first principles
4. **Event-Driven Communication**: Message-based interaction between components
5. **Compositional Agents**: Standard interfaces enabling reuse and workflow composition
6. **Prompt Engineering as Code**: Structured management of prompts via MCP framework
7. **Progressive Scaling**: Design for personal use with path to hundreds of users

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                            Client Applications                         │
│                                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    ┌────────────────┐  │
│  │            │  │            │  │            │    │                │  │
│  │  Web UI    │  │ Mobile App │  │ CLI Client │    │ Messaging      │  │
│  │  (React)   │  │ (React    │  │ (Python)   │    │ Integrations   │  │
│  │            │  │  Native)   │  │            │    │                │  │
│  └────────────┘  └────────────┘  └────────────┘    └────────────────┘  │
│                                                                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                             API Gateway                                │
│                                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    ┌────────────────┐  │
│  │            │  │            │  │            │    │                │  │
│  │ Auth &     │  │ Rate       │  │ Request    │    │ Response       │  │
│  │ Tenancy    │  │ Limiting   │  │ Routing    │    │ Caching        │  │
│  │            │  │            │  │            │    │                │  │
│  └────────────┘  └────────────┘  └────────────┘    └────────────────┘  │
│                                                                        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          Core Service Layer                            │
│                                                                        │
│  ┌────────────────────────┐   ┌──────────────────────────────────┐    │
│  │                        │   │                                  │    │
│  │   Agent Management     │   │      Content Management          │    │
│  │   Service              │   │      Service                     │    │
│  │                        │   │                                  │    │
│  └────────────────────────┘   └──────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────┐   ┌──────────────────────────────────┐    │
│  │                        │   │                                  │    │
│  │   Workflow Engine      │   │      Knowledge Repository        │    │
│  │                        │   │                                  │    │
│  │                        │   │                                  │    │
│  └────────────────────────┘   └──────────────────────────────────┘    │
│                                                                        │
│  ┌────────────────────────┐   ┌──────────────────────────────────┐    │
│  │                        │   │                                  │    │
│  │   Prompt Management    │   │      User Management             │    │
│  │   (MCP)                │   │                                  │    │
│  │                        │   │                                  │    │
│  └────────────────────────┘   └──────────────────────────────────┘    │
│                                                                        │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         Event Streaming Layer                          │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                 │   │
│  │                   Event Bus / Message Broker                    │   │
│  │                   (Redis Streams → Kafka)                       │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Agent Runtime Layer                             │
│                                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    ┌────────────────┐  │
│  │            │  │            │  │            │    │                │  │
│  │ ContentMind│  │ Researcher │  │ Gateway    │    │ Custom Agent   │  │
│  │ Agent      │  │ Agent      │  │ Agent      │    │ Types          │  │
│  │            │  │            │  │            │    │                │  │
│  └────────────┘  └────────────┘  └────────────┘    └────────────────┘  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                 │   │
│  │                Agent Runtime Manager                            │   │
│  │                                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Shared Infrastructure                           │
│                                                                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    ┌────────────────┐  │
│  │            │  │            │  │            │    │                │  │
│  │ Model      │  │ Vector     │  │ Document   │    │ Observability  │  │
│  │ Router     │  │ Database   │  │ Storage    │    │ & Monitoring   │  │
│  │            │  │            │  │            │    │                │  │
│  └────────────┘  └────────────┘  └────────────┘    └────────────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Implementation Approach

### Monorepo Structure

We will start with a modular monorepo approach to maintain development velocity while ensuring clear component boundaries:

```
bluelabel-aios-v2/
├── apps/                 # API and UI entry points
│   ├── api/              # FastAPI application
│   └── web/              # React frontend (future)
├── agents/               # Agent implementations
│   ├── base/             # Base agent interface and utilities
│   ├── contentmind/      # Content processing agent
│   ├── researcher/       # Research agent
│   ├── gateway/          # Communications gateway agent
│   └── digest/           # Content digest agent
├── services/             # Core services
│   ├── gateway/          # Communication channel services
│   ├── knowledge/        # Knowledge repository
│   ├── mcp/              # Multi-Component Prompting system
│   ├── workflow/         # Workflow orchestration
│   └── model_router/     # LLM routing and management
├── core/                 # Shared core functionality
│   ├── messaging/        # Event bus and message passing
│   ├── storage/          # Database and storage interfaces
│   ├── auth/             # Authentication and authorization
│   ├── config/           # Configuration management
│   └── telemetry/        # Logging, metrics, and tracing
├── shared/               # Cross-cutting concerns
│   ├── schemas/          # Data models and validation
│   └── utils/            # Utility functions
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
├── docker/               # Docker configuration
├── scripts/              # Development and deployment scripts
├── docker-compose.yml    # Local development setup
└── README.md             # Project documentation
```

### Config Strategy

All services load from a centralized `config` module, which supports:
* `.env` and environment overrides
* per-tenant config overrides (e.g. LLM providers, rate limits)
* optional support for secrets managers (e.g. Vault, AWS SSM)

```python
# Example config module
from pydantic_settings import BaseSettings
import os
from typing import Dict, Any, Optional

class Settings(BaseSettings):
    # Basic settings
    PROJECT_NAME: str = "Bluelabel AIOS"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/bluelabel")
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    DEFAULT_LLM_PROVIDER: str = "openai"
    
    # Tenant-specific overrides
    TENANT_CONFIGS: Dict[str, Dict[str, Any]] = {}
    
    # Load tenant-specific configs
    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        return self.TENANT_CONFIGS.get(tenant_id, {})
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### Agent Interface

The foundational `Agent` interface will standardize how all agents in the system operate:

```python
class AgentInput(BaseModel):
    """Standardized input for all agents"""
    task_id: str
    tenant_id: str
    task_type: str
    content: Dict[str, Any]
    parameters: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class AgentOutput(BaseModel):
    """Standardized output from all agents"""
    task_id: str
    status: Literal["success", "error", "pending"]
    result: Dict[str, Any] = {}
    error: Optional[Dict[str, Any]] = None
    metrics: Dict[str, Any] = {}
    artifacts: List[Dict[str, Any]] = []
    next_steps: List[Dict[str, Any]] = []

class AgentTool(BaseModel):
    """Tool that an agent can use"""
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass

class Agent(ABC):
    """Base class for all Bluelabel AIOS agents"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tools = self._register_tools()
    
    @abstractmethod
    def _register_tools(self) -> List[AgentTool]:
        """Register tools available to this agent"""
        pass
    
    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process a request using this agent"""
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities for discovery"""
        pass
    
    async def initialize(self) -> bool:
        """Initialize the agent (load models, connect to services)"""
        pass
    
    async def shutdown(self) -> bool:
        """Clean up resources when shutting down"""
        pass
```

### Agent Runtime Manager

A service responsible for:
- Instantiating agent instances
- Validating input/output schemas
- Managing tool registrations
- Reporting metrics and performance data
- Hot-reloading agents (optional)
- Sandboxed execution (e.g., subprocess) (optional)
- Scheduled agent runs (optional)

```python
class AgentRuntimeManager:
    """Manager for agent lifecycle and execution"""
    
    def __init__(self):
        self.agents = {}
        self.metrics = {}
    
    async def register_agent(self, agent_id: str, agent_class: Type[Agent], config: Dict[str, Any]) -> bool:
        """Register and initialize an agent"""
        agent = agent_class(config)
        initialized = await agent.initialize()
        if initialized:
            self.agents[agent_id] = agent
            return True
        return False
    
    async def execute_agent(self, agent_id: str, input: AgentInput) -> AgentOutput:
        """Execute an agent with the given input"""
        agent = self.agents.get(agent_id)
        if not agent:
            return AgentOutput(
                task_id=input.task_id,
                status="error",
                error={"message": f"Agent {agent_id} not found"}
            )
        
        # Validate input schema
        # Start metrics collection
        start_time = time.time()
        
        try:
            result = await agent.process(input)
            
            # Record metrics
            execution_time = time.time() - start_time
            self._record_metrics(agent_id, input.task_type, execution_time, result.status)
            
            return result
        except Exception as e:
            # Handle and log error
            execution_time = time.time() - start_time
            self._record_metrics(agent_id, input.task_type, execution_time, "error")
            
            return AgentOutput(
                task_id=input.task_id,
                status="error",
                error={"message": str(e), "type": type(e).__name__}
            )
```

### Event Format

Standardized event format for communication between components:

```python
class EventMetadata(BaseModel):
    """Metadata for all events"""
    event_id: str
    event_type: str
    event_version: str = "1.0"
    timestamp: datetime
    source: str
    tenant_id: str
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    user_id: Optional[str] = None

class Event(BaseModel):
    """Base event model for all system events"""
    metadata: EventMetadata
    payload: Dict[str, Any]
```

### LLM Provider Abstraction

The Model Router includes a unified interface for all LLM providers:

```python
class LLMProvider(ABC):
    """Base interface for all LLM providers"""
    
    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """Generate a completion for the given prompt"""
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, Any]], max_tokens: int = 500, temperature: float = 0.7, **kwargs) -> Dict[str, Any]:
        """Generate a response to a conversation"""
        pass
    
    @abstractmethod
    async def embed(self, text: str, **kwargs) -> List[float]:
        """Generate embeddings for the given text"""
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider is available"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities and limitations"""
        pass
```

### MCP Component Schema

The Multi-Component Prompting system will use this structure:

```python
class PromptVariable(BaseModel):
    """Variable definition for prompt components"""
    name: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    type: str = "string"  # string, number, boolean, object, array
    schema: Optional[Dict[str, Any]] = None
    
class PromptComponent(BaseModel):
    """Reusable prompt component with versioning"""
    id: str
    name: str
    description: str
    version: str
    template: str
    variables: List[PromptVariable] = []
    tags: List[str] = []
    examples: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    parent_version: Optional[str] = None
```

### Workflow Definition

For orchestrating multi-agent workflows:

```python
class WorkflowStep(BaseModel):
    """Single step in a workflow"""
    id: str
    name: str
    agent: str
    task_type: str
    parameters: Dict[str, Any] = {}
    inputs: Dict[str, str] = {}  # Maps input name to output from previous step
    condition: Optional[str] = None  # Expression to evaluate for conditional execution
    retry: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    
class Workflow(BaseModel):
    """Definition of a multi-agent workflow"""
    id: str
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    triggers: List[Dict[str, Any]] = []
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    error_handling: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
```

### OpenAPI + Agent Discovery API

The system will expose a comprehensive API for agent discovery and management:

```python
@app.get("/agents")
async def list_agents(agent_runtime: AgentRuntimeManager = Depends(get_agent_runtime)):
    """
    List all available agents with their capabilities
    
    Returns a list of available agents including:
    - Agent ID and name
    - Supported task types
    - Required/optional parameters
    - Available tools
    - Input/output schemas
    """
    agents = {}
    for agent_id, agent in agent_runtime.agents.items():
        agents[agent_id] = agent.get_capabilities()
    
    return {
        "count": len(agents),
        "agents": agents
    }

@app.get("/agents/{agent_id}")
async def get_agent_details(agent_id: str, agent_runtime: AgentRuntimeManager = Depends(get_agent_runtime)):
    """
    Get detailed information about a specific agent
    """
    agent = agent_runtime.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agent.get_capabilities()
```

## Implementation Plan

### Phase 1: Foundation (Weeks 1-4)
Focus on one complete flow: PDF submission via email → digest generation → email delivery

1. **Week 1: Core Framework**
   - Set up project structure and CI pipeline
   - Implement base `Agent` interface
   - Create agent registry mechanism
   - Build initial event bus using Redis Streams

2. **Week 2: Email Gateway**
   - Implement email processing service
   - Build Gateway agent for email monitoring
   - Create content extraction and routing

3. **Week 3: Content Processing**
   - Implement ContentMind agent
   - Build PDF processor
   - Implement content storage in knowledge repository

4. **Week 4: Digest Generation**
   - Implement Digest agent
   - Create email delivery mechanism
   - Complete the end-to-end flow

### Phase 2: Enrichment (Weeks 5-8)
Add core capabilities and improve existing components

1. **Week 5: MCP System**
   - Implement component registry
   - Build template rendering engine
   - Create version management system

2. **Week 6: Workflow Engine**
   - Implement workflow definition schema
   - Build workflow execution engine
   - Create workflow monitoring tools

3. **Week 7: Knowledge Repository**
   - Implement vector database integration
   - Build semantic search capabilities
   - Create content relationship discovery

4. **Week 8: Model Router**
   - Implement LLM routing logic
   - Build provider management
   - Create prompt optimization

### Phase 3: User Interface (Weeks 9-12)
Develop user interfaces and additional channels

1. **Week 9-10: API Refinement**
   - Complete REST API documentation
   - Implement comprehensive error handling
   - Add pagination, filtering, and sorting

2. **Week 11-12: Web UI**
   - Implement React frontend
   - Create agent management UI
   - Build workflow editor

### Phase 4: Scale Preparation (Weeks 13-16)
Prepare for multi-user deployment and scaling

1. **Week 13-14: Multi-Tenancy**
   - Implement tenant isolation
   - Build user management system
   - Create permission system

2. **Week 15-16: Monitoring & Deployment**
   - Implement observability stack
   - Build deployment automation
   - Create scaling mechanisms

## Immediate Next Steps

1. Define detailed `Agent` interface implementation
2. Create project structure and repository
3. Implement basic messaging infrastructure
4. Build Gateway agent for email processing
5. Implement ContentMind agent with PDF processing
6. Create simple API for testing and monitoring

## Technology Stack

- **Backend**: Python 3.10+ with FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Store**: ChromaDB
- **Message Bus**: Redis Streams (initial), Kafka (future)
- **Caching**: Redis
- **LLM Integration**: OpenAI, Anthropic, Ollama
- **Frontend**: React (web), React Native (mobile)
- **Infrastructure**: Docker, Kubernetes (future)
- **Observability**: Prometheus, Grafana, OpenTelemetry

## Testing Strategy

1. **Unit Testing**: Test individual components in isolation
   - Agent implementations
   - Service functions
   - MCP component rendering

2. **Integration Testing**: Test interactions between components
   - Agent-to-agent communication
   - Service API contracts
   - Database interactions

3. **End-to-End Testing**: Test complete user flows
   - Email submission to digest delivery
   - Web UI interactions
   - API workflows

4. **LLM Testing**: Specialized testing for LLM interactions
   - Prompt effectiveness
   - Consistent outputs
   - Error handling

## Conclusion

This architecture balances immediate practical implementation needs with a long-term vision for a scalable, multi-tenant agent platform. The approach starts with a cohesive, modular system that delivers real value quickly, while establishing patterns and interfaces that can evolve as the platform grows.

By focusing on one complete flow first and building API-first, we ensure the system provides value from day one while creating a solid foundation for future enhancements. The modular monorepo approach gives us the separation of concerns we need without prematurely introducing distributed systems complexity.

As the system evolves, individual components can be extracted into separate services when scale or team structure demands it, while maintaining the same logical architecture and communication patterns established from the beginning.
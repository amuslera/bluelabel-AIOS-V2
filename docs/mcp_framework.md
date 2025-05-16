# MCP (Multi-Component Prompting) Framework

The MCP framework provides a structured system for managing, versioning, and rendering prompts in the Bluelabel AIOS system.

## Overview

MCP allows you to:
- Create reusable prompt components with variables
- Version and track changes to prompts
- Combine components into complex templates
- Validate inputs and render prompts dynamically
- Store and retrieve prompts from various backends

## Core Concepts

### 1. Prompt Components

A prompt component is a reusable unit with:
- **Template**: The prompt text with variable placeholders `{variable_name}`
- **Variables**: Defined inputs with types, defaults, and validation
- **Examples**: Sample inputs for testing and documentation
- **Tags**: For categorization and discovery
- **Versioning**: Automatic version tracking

Example:
```python
component = await manager.create_component(
    name="summarizer",
    description="Summarizes content",
    template="Summarize this in {num_points} points:\n{content}",
    variables=[
        {
            "name": "content",
            "description": "Content to summarize",
            "type": "string",
            "required": True
        },
        {
            "name": "num_points",
            "description": "Number of points",
            "type": "number",
            "required": False,
            "default": 3
        }
    ],
    created_by="user@example.com"
)
```

### 2. Prompt Templates

Templates combine multiple components into complex prompts:
- **Components**: List of component IDs to include
- **Layout**: How to arrange and combine components
- **Variables**: Additional template-level variables

Example:
```python
template = await manager.create_template(
    name="report_template",
    description="Complete report template",
    component_ids=[intro_id, body_id, conclusion_id],
    layout="""
# {title}

{component:intro_id}

## Main Content
{component:body_id}

## Conclusion
{component:conclusion_id}

Generated on: {date}
""",
    variables=[
        {
            "name": "title",
            "description": "Report title",
            "type": "string",
            "required": True
        }
    ],
    created_by="user@example.com"
)
```

### 3. Variables

Variables define the inputs for components:
- **Types**: `string`, `number`, `boolean`, `array`, `object`
- **Validation**: Required/optional, defaults, schemas
- **Documentation**: Description for each variable

### 4. Storage

MCP supports different storage backends:
- **InMemoryPromptStorage**: For development/testing
- **PostgreSQLPromptStorage**: For production (coming soon)
- **FileSystemPromptStorage**: For simple deployments (coming soon)

## Usage

### Basic Setup

```python
from services.mcp import create_prompt_manager

# Create manager with default (in-memory) storage
manager = create_prompt_manager()

# Or with custom storage
from services.mcp.storage import PostgreSQLPromptStorage
storage = PostgreSQLPromptStorage(connection_string)
manager = create_prompt_manager(storage)
```

### Creating Components

```python
# Create a question-answering component
qa_component = await manager.create_component(
    name="qa_prompt",
    description="Question answering prompt",
    template="""Based on this context:
{context}

Please answer: {question}

Answer:""",
    variables=[
        {
            "name": "context",
            "description": "Background information",
            "type": "string",
            "required": True
        },
        {
            "name": "question",
            "description": "Question to answer",
            "type": "string",
            "required": True
        }
    ],
    created_by="system",
    tags=["qa", "contextual"],
    examples=[
        {
            "context": "The sky is blue during the day.",
            "question": "What color is the sky?"
        }
    ]
)
```

### Rendering Components

```python
# Render with inputs
rendered = await manager.render_component(
    component_id=qa_component.id,
    inputs={
        "context": "Python is a programming language created by Guido van Rossum.",
        "question": "Who created Python?"
    }
)
print(rendered)
# Output: Based on this context:
# Python is a programming language created by Guido van Rossum.
# 
# Please answer: Who created Python?
# 
# Answer:
```

### Versioning

```python
# Update a component (creates new version)
updated = await manager.update_component(
    component_id=qa_component.id,
    updates={
        "template": "Context: {context}\n\nQuestion: {question}\n\nDetailed Answer:"
    },
    updated_by="user@example.com"
)

# Get version history
versions = await manager.get_component_versions(qa_component.id)
for v in versions:
    print(f"Version {v['version']} - {v['created_at']}")
```

### Using Templates

```python
# Create a complex template
analysis_template = await manager.create_template(
    name="content_analysis",
    description="Full content analysis",
    component_ids=[
        summarizer_component.id,
        entity_extractor.id,
        sentiment_analyzer.id
    ],
    created_by="user@example.com"
)

# Render template
result = await manager.render_template(
    template_id=analysis_template.id,
    inputs={
        "content": "Your content here...",
        "num_points": 5,
        "entity_types": ["person", "organization"]
    }
)
```

## Default Components

The framework includes several default components:

1. **content_summarizer**: Summarizes text into key points
2. **entity_extractor**: Extracts named entities
3. **qa_component**: Question answering based on context

Initialize defaults:
```python
from services.mcp import initialize_default_components
await initialize_default_components(manager)
```

## Integration with Agents

Agents can use MCP for structured prompting:

```python
class ContentMindAgent(Agent):
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
    
    async def process(self, input: AgentInput) -> AgentOutput:
        # Render prompt
        prompt = await self.prompt_manager.render_component(
            "content_summarizer",
            {"content": input.content["text"]}
        )
        
        # Use with LLM
        response = await self.llm.complete(prompt)
        
        return AgentOutput(
            task_id=input.task_id,
            status="success",
            result={"summary": response.text}
        )
```

## Best Practices

1. **Component Design**:
   - Keep components focused on a single task
   - Use clear variable names and descriptions
   - Provide meaningful examples
   - Tag components for easy discovery

2. **Versioning**:
   - Document changes when updating components
   - Test with examples before deploying
   - Keep backward compatibility when possible

3. **Variable Usage**:
   - Use appropriate types for variables
   - Provide defaults for optional variables
   - Validate with JSON schemas for complex types

4. **Template Organization**:
   - Group related components with tags
   - Create templates for common workflows
   - Document template purpose and usage

## Testing

```bash
# Run MCP tests
python scripts/test_mcp.py

# Run unit tests
pytest tests/unit/test_mcp.py
```

## Future Enhancements

1. **Storage Backends**:
   - PostgreSQL storage with full SQL queries
   - Redis storage for caching
   - S3/GCS storage for large deployments

2. **Advanced Features**:
   - A/B testing for prompt variants
   - Performance metrics and analytics
   - Collaborative editing with permissions
   - Prompt marketplace/sharing

3. **LLM Integration**:
   - Direct execution with LLM providers
   - Response parsing and validation
   - Automatic prompt optimization

4. **UI Components**:
   - Visual prompt builder
   - Version comparison tools
   - Testing playground

The MCP framework provides a solid foundation for prompt engineering in the Bluelabel AIOS system, enabling teams to collaborate on, version, and deploy prompts effectively.
# MCP Framework

The Multi-Component Prompting (MCP) Framework is a modular system for managing and combining multiple prompt components into cohesive LLM prompts.

## Features

- **Component-based architecture**: Break down prompts into reusable components
- **Template support**: Use Jinja2/YAML templates for dynamic content
- **Configuration-driven**: Define components via YAML or programmatically
- **Type-safe**: Uses Pydantic for validation
- **Extensible**: Easy to add new component types
- **Error handling**: Robust error handling for missing variables and invalid configurations

## Component Types

### Base Component
```python
from core.mcp.components import MCPComponent, MCPComponentConfig

class MyComponent(MCPComponent):
    def __init__(self, config: MCPComponentConfig):
        super().__init__(config)
        
    def validate_config(self):
        # Validate component-specific configuration
        pass
        
    def render(self, context: Dict[str, Any]) -> str:
        # Render the component with the given context
        pass
```

### Template Component
```python
from core.mcp.components import TemplateComponent

component = TemplateComponent(
    config=MCPComponentConfig(
        name="greeting",
        description="Greeting component",
        type="greeting"
    ),
    template="Hello, {name}! Today is {date}"
)
```

### YAML Template Component
```python
from core.mcp.components import YAMLTemplateComponent

component = YAMLTemplateComponent(
    config=MCPComponentConfig(
        name="greeting",
        description="Greeting component",
        type="greeting"
    ),
    template_path="path/to/template.yaml"
)
```

## Usage

```python
from core.mcp.framework import MCPFramework
from core.mcp.components import TemplateComponent, MCPComponentConfig

# Create framework instance
framework = MCPFramework()

# Create components
config = MCPComponentConfig(
    name="greeting",
    description="Greeting component",
    type="greeting"
)
component = TemplateComponent(config, "Hello, {name}!")

# Register component
framework.register_component(component)

# Render with context
context = {"name": "World"}
rendered = framework.render(context)
```

## YAML Configuration

```yaml
components:
  - name: greeting
    description: Greeting component
    type: greeting
    template: "Hello, {name}! Today is {date}"
  - name: farewell
    description: Farewell component
    type: farewell
    template: "Goodbye, {name}!"
```

## Error Handling

The framework includes robust error handling for:
- Missing required template variables
- Invalid component configurations
- Duplicate component registrations
- Failed component validations

## Testing

Run tests with:
```bash
pytest tests/test_mcp.py
```

## Integration with ContentMind

The MCP framework is designed to work seamlessly with the ContentMind agent. Components can be registered and used to create complex, configurable prompts for different summarization tasks.

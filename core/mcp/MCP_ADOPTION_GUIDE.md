# MCP Framework Adoption Guide

This guide provides a step-by-step process for integrating the MCP (Multi-Component Prompting) framework into new agents. The MCP framework enables modular, configurable prompt management for LLM interactions.

## 1. Create a New Agent-Specific Component

### Step 1: Define Component Configuration
Create a new configuration class that inherits from `MCPComponentConfig`:

```python
from core.mcp.components import MCPComponentConfig

class MyAgentComponentConfig(MCPComponentConfig):
    """Configuration for MyAgent components."""
    
    # Required fields
    role: str = Field(description="Role description for the LLM")
    instruction: str = Field(description="Instruction template")
    input_format: str = Field(description="Input format template")
    output_format: str = Field(description="Output format template")
    
    # Agent-specific fields
    agent_type: str = Field(description="Type of agent")
    context_size: int = Field(default=4096, description="Maximum context size")
    
    class Config:
        extra = "allow"  # Allow additional fields
```

### Step 2: Implement Component Class
Create a new component class that inherits from `MCPComponent`:

```python
from core.mcp.components import MCPComponent
from core.mcp.components.contentmind import ContentMindComponentConfig

class MyAgentComponent(MCPComponent):
    """Component specialized for MyAgent prompts."""
    
    def __init__(self, config: MyAgentComponentConfig):
        super().__init__(config)
        self.role = config.role
        self.instruction = config.instruction
        self.input_format = config.input_format
        self.output_format = config.output_format
        
    def validate_config(self) -> None:
        """Validate MyAgent component configuration."""
        if not self.config.role:
            raise ValueError("Role description is required")
        if not self.config.instruction:
            raise ValueError("Instruction template is required")
        if not self.config.input_format:
            raise ValueError("Input format template is required")
        if not self.config.output_format:
            raise ValueError("Output format template is required")
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render the complete MyAgent prompt."""
        try:
            # Format input content
            input_content = self.input_format.format(**context)
            
            # Format role and instruction
            role = self.role.format(**context)
            instruction = self.instruction.format(**context)
            
            # Format output
            output_format = self.output_format.format(**context)
            
            # Combine all parts
            return f"""{role}

{instruction}

{input_content}

{output_format}"""
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")
```

## 2. Create YAML Template
Create a YAML template file in your agent's prompts directory:

```yaml
name: my_agent_prompt
version: 1.0
description: MyAgent prompt template

type: my_agent

role: """
You are a specialized [agent_type] agent.
Your role is to [specific_role_description]

Key characteristics:
- [characteristic_1]
- [characteristic_2]
- [characteristic_3]
"""

instruction: """
Analyze the following [content_type] from [source]:
[specific_instructions]

Context size limit: {context_size} tokens
"""

input_format: """
Content to analyze:
{content}

Additional context:
{context}
"""

output_format: """
Analysis:
{analysis}

Key findings:
{findings}

Recommended actions:
{actions}
"""

# Optional configuration
max_length: 2000
model: "gpt-4"
temperature: 0.7
```

## 3. Implement Loader and Usage
Create a loader class similar to `ContentMindPromptLoader`:

```python
from core.mcp.components.contentmind import ContentMindPromptLoader

class MyAgentPromptLoader(ContentMindPromptLoader):
    """Loader for MyAgent prompts."""
    
    def __init__(self, template_path: str):
        super().__init__(template_path)
        
    def render(self, context: Dict[str, Any]) -> str:
        """Render the prompt with agent-specific validation."""
        # Add agent-specific validation
        if len(context.get('content', '')) > self.component.config.context_size:
            raise ValueError("Content exceeds maximum context size")
            
        return super().render(context)
```

## 4. Best Practices

### Template Design
1. Keep role descriptions consistent but agent-specific
2. Use clear, descriptive variable names in templates
3. Include validation for all required fields
4. Use version numbers in templates for tracking changes

### Error Handling
1. Always validate template variables before rendering
2. Implement fallback mechanisms for missing templates
3. Log errors with descriptive messages
4. Include context in error messages for debugging

### Logging
1. Log rendered prompts for debugging
2. Include template version in logs
3. Log validation failures
4. Track template load times if performance is critical

### Configuration Management
1. Keep templates in version control
2. Use environment variables for sensitive values
3. Document all template variables
4. Maintain a changelog for template versions

## 5. Example Integration
Here's how to integrate the MCP framework in your agent:

```python
from core.mcp.components.contentmind import ContentMindPromptLoader
from pathlib import Path
import logging

# Set up logging
logger = logging.getLogger(__name__)

async def create_prompt(content: str, content_type: str, source: str) -> str:
    """Create a prompt using the MCP framework."""
    try:
        # Get template path
        template_path = Path(__file__).parent.parent / "prompts" / "my_agent" / "my_agent.yaml"
        
        # Create and load loader
        loader = MyAgentPromptLoader(str(template_path))
        loader.load()
        
        # Prepare context
        context = {
            "content_type": content_type,
            "source": source,
            "content": content,
            "analysis": "",  # Will be filled by LLM
            "findings": "",  # Will be filled by LLM
            "actions": ""  # Will be filled by LLM
        }
        
        # Render prompt
        prompt = loader.render(context)
        
        # Log the rendered prompt
        logger.info("Rendered MyAgent prompt:")
        logger.info(prompt)
        
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating MyAgent prompt: {str(e)}")
        # Fallback to simple prompt
        return f"""Analyze the following {content_type} from {source}:

{content}

Analysis:"""
```

## 6. Common Patterns

### Role Templates
- Define clear agent roles
- Include agent-specific capabilities
- Specify expected behavior
- Maintain consistent tone

### Instruction Templates
- Break down tasks into steps
- Specify format requirements
- Include validation criteria
- Define output structure

### Input/Output Formats
- Use consistent variable names
- Define clear data structures
- Include validation rules
- Document expected formats

## 7. Testing Recommendations

### Unit Tests
1. Test template loading
2. Validate configuration
3. Test rendering with sample data
4. Verify fallback behavior

### Integration Tests
1. Test with different content types
2. Verify template versions
3. Test error handling
4. Validate output format

### Performance Tests
1. Measure template load times
2. Test with maximum content sizes
3. Verify memory usage
4. Test concurrent requests

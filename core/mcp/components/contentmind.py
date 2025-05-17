from typing import Dict, Any, Optional
from ..components import MCPComponent, MCPComponentConfig
from pydantic import Field
import yaml
from pathlib import Path

class ContentMindComponentConfig(MCPComponentConfig):
    """Configuration for ContentMind components."""
    role: str = Field(description="Role description for the LLM")
    instruction: str = Field(description="Instruction template")
    input_format: str = Field(description="Input format template")
    output_format: str = Field(description="Output format template")
    
    class Config:
        extra = "allow"

class ContentMindComponent(MCPComponent):
    """Component specialized for ContentMind agent prompts."""
    
    def __init__(self, config: ContentMindComponentConfig):
        super().__init__(config)
        self.role = config.role
        self.instruction = config.instruction
        self.input_format = config.input_format
        self.output_format = config.output_format
        
    def validate_config(self) -> None:
        """Validate ContentMind component configuration."""
        if not self.config.role:
            raise ValueError("Role description is required")
        if not self.config.instruction:
            raise ValueError("Instruction template is required")
        if not self.config.input_format:
            raise ValueError("Input format template is required")
        if not self.config.output_format:
            raise ValueError("Output format template is required")
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render the complete ContentMind prompt."""
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

class ContentMindPromptLoader:
    """Helper class to load and configure ContentMind prompts."""
    
    def __init__(self, template_path: str):
        self.template_path = Path(template_path)
        self.component = None
        
    def load(self) -> ContentMindComponent:
        """Load and configure the ContentMind component."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
            
        with open(self.template_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        # Create component config
        config = ContentMindComponentConfig(
            name=config_data.get('name', 'contentmind'),
            description=config_data.get('description', 'ContentMind agent prompt'),
            type='contentmind',
            role=config_data.get('role', ''),
            instruction=config_data.get('instruction', ''),
            input_format=config_data.get('input_format', ''),
            output_format=config_data.get('output_format', '')
        )
        
        # Create and validate component
        component = ContentMindComponent(config)
        component.validate_config()
        self.component = component
        return component
        
    def render(self, context: Dict[str, Any]) -> str:
        """Render the prompt with context."""
        if not self.component:
            raise ValueError("Component not loaded. Call load() first.")
            
        return self.component.render(context)
        
    def validate(self) -> None:
        """Validate the loaded component."""
        if not self.component:
            raise ValueError("Component not loaded. Call load() first.")
        self.component.validate_config()

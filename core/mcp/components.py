from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel
from abc import ABC, abstractmethod
import yaml
from pathlib import Path


class MCPComponentConfig(BaseModel):
    """Base configuration for MCP components."""
    name: str
    description: str
    version: str = "1.0"
    type: str
    
    class Config:
        extra = "allow"  # Allow additional fields


class MCPComponent(ABC):
    """Base class for all MCP components."""
    
    def __init__(self, config: MCPComponentConfig):
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> None:
        """Validate component configuration."""
        pass
    
    @abstractmethod
    def render(self, context: Dict[str, Any]) -> str:
        """Render the component with the given context."""
        pass


class TemplateComponent(MCPComponent):
    """Component that renders using a template."""
    
    def __init__(self, config: MCPComponentConfig, template: str):
        super().__init__(config)
        self.template = template
        
    def validate_config(self) -> None:
        """Validate template component configuration."""
        if not self.config.type:
            raise ValueError("Template component must specify a type")
    
    def render(self, context: Dict[str, Any]) -> str:
        """Render the template with the given context."""
        try:
            return self.template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")


class YAMLTemplateComponent(TemplateComponent):
    """Component that loads templates from YAML files."""
    
    def __init__(self, config: MCPComponentConfig, template_path: str):
        """Initialize from a YAML file."""
        template_path = Path(template_path)
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
            
        with open(template_path, 'r') as f:
            template_data = yaml.safe_load(f)
            template = template_data.get('template', '')
            
        super().__init__(config, template)


class ComponentRegistry:
    """Registry for MCP components."""
    
    def __init__(self):
        self.components: Dict[str, Type[MCPComponent]] = {}
        
    def register(self, component_type: str, component_class: Type[MCPComponent]) -> None:
        """Register a component type."""
        if component_type in self.components:
            raise ValueError(f"Component type already registered: {component_type}")
        self.components[component_type] = component_class
        
    def get(self, component_type: str) -> Optional[Type[MCPComponent]]:
        """Get a registered component type."""
        return self.components.get(component_type)
        
    def list(self) -> List[str]:
        """List all registered component types."""
        return list(self.components.keys())

# Global registry instance
registry = ComponentRegistry()

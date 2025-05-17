from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .components import MCPComponent, ComponentRegistry, YAMLTemplateComponent
import yaml
from pathlib import Path


class MCPFramework:
    """Multi-Component Prompting Framework."""
    
    def __init__(self, registry: ComponentRegistry = None):
        """Initialize the MCP framework."""
        self.registry = registry or ComponentRegistry()
        self.components: Dict[str, MCPComponent] = {}
        
    def register_component(self, component: MCPComponent) -> None:
        """Register a component in the framework."""
        if component.config.name in self.components:
            raise ValueError(f"Component already registered: {component.config.name}")
        self.components[component.config.name] = component
        
    def load_from_yaml(self, yaml_path: str) -> None:
        """Load components from a YAML file."""
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")
            
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
            
        for component_config in config.get('components', []):
            component_type = component_config.get('type')
            component_class = self.registry.get(component_type)
            
            if not component_class:
                raise ValueError(f"Unknown component type: {component_type}")
                
            component = component_class(
                MCPComponentConfig(**component_config),
                component_config.get('template', '')
            )
            self.register_component(component)
            
    def render(self, context: Dict[str, Any]) -> str:
        """Render all components with the given context."""
        rendered_components = []
        
        for component in self.components.values():
            try:
                rendered = component.render(context)
                rendered_components.append(rendered)
            except Exception as e:
                raise ValueError(f"Error rendering component {component.config.name}: {str(e)}")
                
        return "\n\n".join(rendered_components)

    def validate(self) -> None:
        """Validate all components in the framework."""
        for component in self.components.values():
            try:
                component.validate_config()
            except Exception as e:
                raise ValueError(f"Invalid component {component.config.name}: {str(e)}")

    def get_component(self, name: str) -> Optional[MCPComponent]:
        """Get a component by name."""
        return self.components.get(name)

    def list_components(self) -> List[str]:
        """List all registered components."""
        return list(self.components.keys())

# Global framework instance
framework = MCPFramework()

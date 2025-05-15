from typing import Dict, Any, List, Optional
import json
import os
import re
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class PromptComponent(BaseModel):
    """A reusable prompt component"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str
    template: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PromptTemplate(BaseModel):
    """A complete prompt template composed of components"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str
    components: List[str]  # List of component IDs
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MCPManager:
    """Manager for Multi-Component Prompting system"""
    
    def __init__(self, components_dir: str = "data/mcp/components", templates_dir: str = "data/mcp/templates"):
        """Initialize the MCP Manager
        
        Args:
            components_dir: Directory to store prompt components
            templates_dir: Directory to store prompt templates
        """
        self.components_dir = components_dir
        self.templates_dir = templates_dir
        
        # Create directories if they don't exist
        os.makedirs(components_dir, exist_ok=True)
        os.makedirs(templates_dir, exist_ok=True)
        
        # Load components and templates
        self.components: Dict[str, PromptComponent] = self._load_components()
        self.templates: Dict[str, PromptTemplate] = self._load_templates()
    
    def _load_components(self) -> Dict[str, PromptComponent]:
        """Load all prompt components from disk"""
        components = {}
        
        if not os.path.exists(self.components_dir):
            return components
        
        for filename in os.listdir(self.components_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.components_dir, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                    component = PromptComponent(**data)
                    components[component.id] = component
        
        return components
    
    def _load_templates(self) -> Dict[str, PromptTemplate]:
        """Load all prompt templates from disk"""
        templates = {}
        
        if not os.path.exists(self.templates_dir):
            return templates
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.templates_dir, filename)
                with open(filepath, "r") as f:
                    data = json.load(f)
                    template = PromptTemplate(**data)
                    templates[template.id] = template
        
        return templates
    
    def create_component(self, name: str, description: str, template: str, 
                        version: str = "1.0.0", tags: List[str] = None) -> PromptComponent:
        """Create a new prompt component
        
        Args:
            name: Name of the component
            description: Description of the component
            template: Template string with variables in {{variable}} format
            version: Version string
            tags: List of tags
            
        Returns:
            The created component
        """
        component = PromptComponent(
            name=name,
            description=description,
            template=template,
            version=version,
            tags=tags or []
        )
        
        # Save to disk
        filepath = os.path.join(self.components_dir, f"{component.id}.json")
        with open(filepath, "w") as f:
            f.write(component.model_dump_json(indent=2))
        
        # Add to in-memory store
        self.components[component.id] = component
        
        return component
    
    def create_template(self, name: str, description: str, components: List[str], 
                       version: str = "1.0.0", tags: List[str] = None) -> PromptTemplate:
        """Create a new prompt template
        
        Args:
            name: Name of the template
            description: Description of the template
            components: List of component IDs
            version: Version string
            tags: List of tags
            
        Returns:
            The created template
        """
        # Verify all components exist
        for component_id in components:
            if component_id not in self.components:
                raise ValueError(f"Component {component_id} does not exist")
        
        template = PromptTemplate(
            name=name,
            description=description,
            components=components,
            version=version,
            tags=tags or []
        )
        
        # Save to disk
        filepath = os.path.join(self.templates_dir, f"{template.id}.json")
        with open(filepath, "w") as f:
            f.write(template.model_dump_json(indent=2))
        
        # Add to in-memory store
        self.templates[template.id] = template
        
        return template
    
    def render_component(self, component_id: str, variables: Dict[str, Any]) -> str:
        """Render a prompt component with variables
        
        Args:
            component_id: ID of the component
            variables: Dictionary of variables to substitute
            
        Returns:
            Rendered prompt string
        """
        if component_id not in self.components:
            raise ValueError(f"Component {component_id} does not exist")
        
        component = self.components[component_id]
        template = component.template
        
        # Replace variables
        for key, value in variables.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Render a complete prompt template with variables
        
        Args:
            template_id: ID of the template
            variables: Dictionary of variables to substitute
            
        Returns:
            Rendered prompt string
        """
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} does not exist")
        
        template = self.templates[template_id]
        rendered_parts = []
        
        # Render each component
        for component_id in template.components:
            rendered_part = self.render_component(component_id, variables)
            rendered_parts.append(rendered_part)
        
        # Join all parts
        return "\n\n".join(rendered_parts)
    
    def get_component(self, component_id: str) -> Optional[PromptComponent]:
        """Get a prompt component by ID"""
        return self.components.get(component_id)
    
    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a prompt template by ID"""
        return self.templates.get(template_id)
    
    def list_components(self, tags: List[str] = None) -> List[PromptComponent]:
        """List all prompt components, optionally filtered by tags"""
        if not tags:
            return list(self.components.values())
        
        return [c for c in self.components.values() if any(tag in c.tags for tag in tags)]
    
    def list_templates(self, tags: List[str] = None) -> List[PromptTemplate]:
        """List all prompt templates, optionally filtered by tags"""
        if not tags:
            return list(self.templates.values())
        
        return [t for t in self.templates.values() if any(tag in t.tags for tag in tags)]

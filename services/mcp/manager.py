"""Main prompt management interface"""

import logging
from typing import Any, Dict, List, Optional

from .models import PromptComponent, PromptTemplate, PromptExecution
from .storage import PromptStorage, InMemoryPromptStorage
from .renderer import PromptRenderer
from .validator import PromptValidator

logger = logging.getLogger(__name__)

class PromptManager:
    """Main interface for managing and using prompts"""
    
    def __init__(self, storage: Optional[PromptStorage] = None):
        self.storage = storage or InMemoryPromptStorage()
        self.renderer = PromptRenderer()
        self.validator = PromptValidator()
        logger.info("Initialized Prompt Manager")
    
    async def create_component(
        self,
        name: str,
        description: str,
        template: str,
        variables: List[Dict[str, Any]],
        created_by: str,
        tags: Optional[List[str]] = None,
        examples: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptComponent:
        """Create a new prompt component"""
        # Create component
        component = PromptComponent(
            name=name,
            description=description,
            template=template,
            variables=variables,
            created_by=created_by,
            tags=tags or [],
            examples=examples or [],
            metadata=metadata or {}
        )
        
        # Validate component
        errors = self.validator.validate_component(component)
        if errors:
            raise ValueError(f"Component validation failed: {errors}")
        
        # Save to storage
        component_id = await self.storage.save_component(component)
        component.id = component_id
        
        logger.info(f"Created component '{name}' with ID {component_id}")
        return component
    
    async def get_component(
        self, 
        component_id: str, 
        version: Optional[str] = None
    ) -> Optional[PromptComponent]:
        """Get a component by ID and optional version"""
        return await self.storage.get_component(component_id, version)
    
    async def update_component(
        self,
        component_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> PromptComponent:
        """Update an existing component"""
        # Get existing component
        existing = await self.storage.get_component(component_id)
        if not existing:
            raise ValueError(f"Component {component_id} not found")
        
        # Apply updates
        updated_data = existing.model_dump()
        updated_data.update(updates)
        updated_data["created_by"] = updated_by
        
        # Create new component with updates
        updated_component = PromptComponent(**updated_data)
        
        # Validate
        errors = self.validator.validate_component(updated_component)
        if errors:
            raise ValueError(f"Component validation failed: {errors}")
        
        # Save as new version
        await self.storage.update_component(component_id, updated_component)
        
        logger.info(f"Updated component {component_id}")
        return updated_component
    
    async def list_components(
        self, 
        tags: Optional[List[str]] = None
    ) -> List[PromptComponent]:
        """List components, optionally filtered by tags"""
        return await self.storage.list_components(tags)
    
    async def create_template(
        self,
        name: str,
        description: str,
        component_ids: List[str],
        created_by: str,
        layout: Optional[str] = None,
        variables: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """Create a new prompt template"""
        # Verify all components exist
        for component_id in component_ids:
            component = await self.storage.get_component(component_id)
            if not component:
                raise ValueError(f"Component {component_id} not found")
        
        # Create template
        template = PromptTemplate(
            name=name,
            description=description,
            components=component_ids,
            layout=layout or "",
            variables=variables or [],
            created_by=created_by,
            metadata=metadata or {}
        )
        
        # Save to storage
        template_id = await self.storage.save_template(template)
        template.id = template_id
        
        logger.info(f"Created template '{name}' with ID {template_id}")
        return template
    
    async def render_component(
        self,
        component_id: str,
        inputs: Dict[str, Any],
        version: Optional[str] = None
    ) -> str:
        """Render a component with given inputs"""
        # Get component
        component = await self.storage.get_component(component_id, version)
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        # Render
        rendered = self.renderer.render_component(component, inputs)
        
        # Log execution
        execution = PromptExecution(
            component_id=component_id,
            inputs=inputs,
            rendered_prompt=rendered
        )
        logger.info(f"Rendered component {component_id}")
        
        return rendered
    
    async def render_template(
        self,
        template_id: str,
        inputs: Dict[str, Any]
    ) -> str:
        """Render a template with given inputs"""
        # Get template
        template = await self.storage.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Get all components
        components = {}
        for component_id in template.components:
            component = await self.storage.get_component(component_id)
            if component:
                components[component_id] = component
        
        # Render
        rendered = self.renderer.render_template(template, components, inputs)
        
        # Log execution
        execution = PromptExecution(
            template_id=template_id,
            inputs=inputs,
            rendered_prompt=rendered
        )
        logger.info(f"Rendered template {template_id}")
        
        return rendered
    
    async def preview_component(
        self,
        component_id: str,
        example_index: int = 0
    ) -> Optional[str]:
        """Preview a component using its examples"""
        component = await self.storage.get_component(component_id)
        if not component:
            return None
            
        return self.renderer.preview_component(component, example_index)
    
    async def validate_component(
        self,
        component_id: str
    ) -> List[str]:
        """Validate a component"""
        component = await self.storage.get_component(component_id)
        if not component:
            return ["Component not found"]
            
        return self.validator.validate_component(component)
    
    async def get_component_versions(
        self,
        component_id: str
    ) -> List[Dict[str, Any]]:
        """Get version history for a component"""
        versions = await self.storage.get_component_versions(component_id)
        
        return [
            {
                "version": v.version,
                "created_at": v.created_at,
                "created_by": v.created_by,
                "changes": v.changes,
                "parent_version": v.parent_version
            }
            for v in versions
        ]
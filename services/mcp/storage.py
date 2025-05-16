"""Storage interface for MCP components"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

from .models import PromptComponent, PromptTemplate, PromptVersion

logger = logging.getLogger(__name__)

class PromptStorage(ABC):
    """Abstract base class for prompt storage"""
    
    @abstractmethod
    async def save_component(self, component: PromptComponent) -> str:
        """Save a prompt component"""
        pass
    
    @abstractmethod
    async def get_component(self, component_id: str, version: Optional[str] = None) -> Optional[PromptComponent]:
        """Get a prompt component by ID and optional version"""
        pass
    
    @abstractmethod
    async def list_components(self, tags: Optional[List[str]] = None) -> List[PromptComponent]:
        """List all components, optionally filtered by tags"""
        pass
    
    @abstractmethod
    async def update_component(self, component_id: str, component: PromptComponent) -> str:
        """Update an existing component (creates new version)"""
        pass
    
    @abstractmethod
    async def delete_component(self, component_id: str) -> bool:
        """Delete a component (soft delete)"""
        pass
    
    @abstractmethod
    async def save_template(self, template: PromptTemplate) -> str:
        """Save a prompt template"""
        pass
    
    @abstractmethod
    async def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a prompt template by ID"""
        pass
    
    @abstractmethod
    async def list_templates(self) -> List[PromptTemplate]:
        """List all templates"""
        pass
    
    @abstractmethod
    async def get_component_versions(self, component_id: str) -> List[PromptVersion]:
        """Get version history for a component"""
        pass

class InMemoryPromptStorage(PromptStorage):
    """In-memory implementation of prompt storage (for development/testing)"""
    
    def __init__(self):
        self.components: Dict[str, PromptComponent] = {}
        self.templates: Dict[str, PromptTemplate] = {}
        self.versions: Dict[str, List[PromptVersion]] = {}
        logger.info("Initialized in-memory prompt storage")
    
    async def save_component(self, component: PromptComponent) -> str:
        """Save a prompt component"""
        self.components[component.id] = component
        
        # Create initial version
        version = PromptVersion(
            component_id=component.id,
            version=component.version,
            changes="Initial version",
            created_at=component.created_at,
            created_by=component.created_by,
            content=component
        )
        
        if component.id not in self.versions:
            self.versions[component.id] = []
        self.versions[component.id].append(version)
        
        logger.info(f"Saved component {component.id} version {component.version}")
        return component.id
    
    async def get_component(self, component_id: str, version: Optional[str] = None) -> Optional[PromptComponent]:
        """Get a prompt component by ID and optional version"""
        if version:
            # Get specific version
            versions = self.versions.get(component_id, [])
            for v in versions:
                if v.version == version:
                    return v.content
            return None
        else:
            # Get latest version
            return self.components.get(component_id)
    
    async def list_components(self, tags: Optional[List[str]] = None) -> List[PromptComponent]:
        """List all components, optionally filtered by tags"""
        components = list(self.components.values())
        
        if tags:
            # Filter by tags
            components = [
                c for c in components
                if any(tag in c.tags for tag in tags)
            ]
        
        return components
    
    async def update_component(self, component_id: str, component: PromptComponent) -> str:
        """Update an existing component (creates new version)"""
        existing = self.components.get(component_id)
        if not existing:
            raise ValueError(f"Component {component_id} not found")
        
        # Increment version
        version_parts = existing.version.split('.')
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        new_version = '.'.join(version_parts)
        
        component.id = component_id
        component.version = new_version
        component.parent_version = existing.version
        component.updated_at = datetime.utcnow()
        
        # Save new version
        self.components[component_id] = component
        
        # Create version record
        version = PromptVersion(
            component_id=component_id,
            version=new_version,
            changes=f"Updated from version {existing.version}",
            created_at=component.updated_at,
            created_by=component.created_by,
            parent_version=existing.version,
            content=component
        )
        self.versions[component_id].append(version)
        
        logger.info(f"Updated component {component_id} to version {new_version}")
        return component_id
    
    async def delete_component(self, component_id: str) -> bool:
        """Delete a component (soft delete)"""
        if component_id in self.components:
            # Mark as deleted (in real implementation)
            del self.components[component_id]
            logger.info(f"Deleted component {component_id}")
            return True
        return False
    
    async def save_template(self, template: PromptTemplate) -> str:
        """Save a prompt template"""
        self.templates[template.id] = template
        logger.info(f"Saved template {template.id}")
        return template.id
    
    async def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a prompt template by ID"""
        return self.templates.get(template_id)
    
    async def list_templates(self) -> List[PromptTemplate]:
        """List all templates"""
        return list(self.templates.values())
    
    async def get_component_versions(self, component_id: str) -> List[PromptVersion]:
        """Get version history for a component"""
        return self.versions.get(component_id, [])
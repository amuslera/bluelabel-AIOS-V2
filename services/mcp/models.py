"""MCP Data Models - Based on architecture.md specifications"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from uuid import uuid4

class PromptVariable(BaseModel):
    """Variable definition for prompt components"""
    name: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    type: str = "string"  # string, number, boolean, object, array
    json_schema: Optional[Dict[str, Any]] = None
    
    @model_validator(mode='after')
    def validate_default(self):
        """Ensure default is provided for non-required variables"""
        if not self.required and self.default is None:
            raise ValueError(f"Non-required variable '{self.name}' must have a default value")
        return self

class PromptComponent(BaseModel):
    """Reusable prompt component with versioning"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    version: str = "1.0.0"
    template: str
    variables: List[PromptVariable] = []
    tags: List[str] = []
    examples: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: Optional[datetime] = None
    parent_version: Optional[str] = None
    
    def get_required_variables(self) -> List[PromptVariable]:
        """Get list of required variables"""
        return [var for var in self.variables if var.required]
    
    def get_optional_variables(self) -> List[PromptVariable]:
        """Get list of optional variables"""
        return [var for var in self.variables if not var.required]
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize inputs against variable definitions"""
        validated = {}
        
        # Check required variables
        for var in self.get_required_variables():
            if var.name not in inputs:
                raise ValueError(f"Required variable '{var.name}' not provided")
            validated[var.name] = inputs[var.name]
        
        # Process optional variables
        for var in self.get_optional_variables():
            if var.name in inputs:
                validated[var.name] = inputs[var.name]
            else:
                validated[var.name] = var.default
        
        return validated

class PromptTemplate(BaseModel):
    """Template that combines multiple components"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    version: str = "1.0.0"
    components: List[str] = []  # List of component IDs
    layout: str = ""  # Template for combining components
    variables: List[PromptVariable] = []  # Additional template-level variables
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_at: Optional[datetime] = None
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize inputs against template variables"""
        validated = {}
        
        # Check required variables
        for var in self.variables:
            if var.required and var.name not in inputs:
                raise ValueError(f"Required variable '{var.name}' not provided")
                
            if var.name in inputs:
                validated[var.name] = inputs[var.name]
            elif not var.required:
                validated[var.name] = var.default
        
        return validated
    
    def get_all_variables(self, components: List[PromptComponent]) -> List[PromptVariable]:
        """Get all variables from template and its components"""
        all_vars = self.variables.copy()
        
        # Add variables from components
        for component in components:
            all_vars.extend(component.variables)
        
        # Remove duplicates by name
        seen = set()
        unique_vars = []
        for var in all_vars:
            if var.name not in seen:
                seen.add(var.name)
                unique_vars.append(var)
        
        return unique_vars

class PromptExecution(BaseModel):
    """Record of a prompt execution"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    component_id: Optional[str] = None
    template_id: Optional[str] = None
    inputs: Dict[str, Any]
    rendered_prompt: str
    execution_time: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}
    
class PromptVersion(BaseModel):
    """Version history for components"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    component_id: str
    version: str
    changes: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    parent_version: Optional[str] = None
    content: PromptComponent
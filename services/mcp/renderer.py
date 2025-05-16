"""Prompt rendering engine"""

import re
import logging
from typing import Any, Dict, List, Optional

from .models import PromptComponent, PromptTemplate
from .validator import PromptValidator

logger = logging.getLogger(__name__)

class PromptRenderer:
    """Renders prompts from components and templates"""
    
    @staticmethod
    def render_component(component: PromptComponent, inputs: Dict[str, Any]) -> str:
        """Render a single component with given inputs"""
        # Validate inputs
        validated = PromptValidator.validate_inputs(component, inputs)
        
        # Render template
        template = component.template
        
        # Replace variables
        for name, value in validated.items():
            # Convert value to string representation
            str_value = PromptRenderer._format_value(value)
            # Replace {variable_name} with value
            template = template.replace(f"{{{name}}}", str_value)
        
        return template
    
    @staticmethod
    def render_template(
        template: PromptTemplate, 
        components: Dict[str, PromptComponent],
        inputs: Dict[str, Any]
    ) -> str:
        """Render a complete template with multiple components"""
        # First, render individual components
        rendered_components = {}
        
        for component_id in template.components:
            component = components.get(component_id)
            if not component:
                raise ValueError(f"Component {component_id} not found")
            
            # Extract inputs for this component
            component_inputs = PromptRenderer._extract_component_inputs(
                component, inputs
            )
            
            # Render component
            rendered = PromptRenderer.render_component(component, component_inputs)
            rendered_components[component_id] = rendered
        
        # Apply template layout
        if template.layout:
            # Replace component placeholders in layout
            result = template.layout
            for component_id, rendered in rendered_components.items():
                result = result.replace(f"{{component:{component_id}}}", rendered)
        else:
            # Default layout: join components with double newline
            result = "\n\n".join(rendered_components.values())
        
        # Apply any template-level variables
        template_validated = template.validate_inputs(inputs)
        for name, value in template_validated.items():
            str_value = PromptRenderer._format_value(value)
            result = result.replace(f"{{{name}}}", str_value)
        
        return result
    
    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a value for insertion into prompt"""
        if isinstance(value, str):
            return value
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            # Format list as comma-separated values
            return ", ".join(PromptRenderer._format_value(v) for v in value)
        elif isinstance(value, dict):
            # Format dict as key-value pairs
            pairs = [f"{k}: {PromptRenderer._format_value(v)}" 
                    for k, v in value.items()]
            return "; ".join(pairs)
        else:
            return str(value)
    
    @staticmethod
    def _extract_component_inputs(
        component: PromptComponent, 
        all_inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract relevant inputs for a specific component"""
        component_inputs = {}
        
        for var in component.variables:
            if var.name in all_inputs:
                component_inputs[var.name] = all_inputs[var.name]
        
        return component_inputs
    
    @staticmethod
    def preview_component(
        component: PromptComponent,
        example_index: int = 0
    ) -> Optional[str]:
        """Preview a component using its examples"""
        if not component.examples:
            return None
            
        if example_index >= len(component.examples):
            example_index = 0
        
        example = component.examples[example_index]
        
        try:
            return PromptRenderer.render_component(component, example)
        except Exception as e:
            logger.error(f"Failed to preview component {component.id}: {e}")
            return None
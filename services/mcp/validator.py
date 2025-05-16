"""Prompt validation utilities"""

import re
import logging
from typing import Any, Dict, List, Set
from jsonschema import validate, ValidationError

from .models import PromptComponent, PromptVariable

logger = logging.getLogger(__name__)

class PromptValidator:
    """Validates prompts and their inputs"""
    
    @staticmethod
    def extract_variables(template: str) -> Set[str]:
        """Extract variable names from a template string"""
        # Match {variable_name} pattern
        pattern = r'\{(\w+)\}'
        matches = re.findall(pattern, template)
        return set(matches)
    
    @staticmethod
    def validate_component(component: PromptComponent) -> List[str]:
        """Validate a prompt component"""
        errors = []
        
        # Extract variables from template
        template_vars = PromptValidator.extract_variables(component.template)
        defined_vars = {var.name for var in component.variables}
        
        # Check for undefined variables
        undefined = template_vars - defined_vars
        if undefined:
            errors.append(f"Template uses undefined variables: {undefined}")
        
        # Check for unused variables
        unused = defined_vars - template_vars
        if unused:
            logger.warning(f"Component has unused variables: {unused}")
        
        # Validate variable schemas
        for var in component.variables:
            if var.json_schema:
                try:
                    # Validate schema format
                    if var.type == "object" and "type" not in var.json_schema:
                        var.json_schema["type"] = "object"
                    elif var.type == "array" and "type" not in var.json_schema:
                        var.json_schema["type"] = "array"
                except Exception as e:
                    errors.append(f"Invalid schema for variable '{var.name}': {e}")
        
        # Validate examples
        for i, example in enumerate(component.examples):
            try:
                component.validate_inputs(example)
            except Exception as e:
                errors.append(f"Example {i} validation failed: {e}")
        
        return errors
    
    @staticmethod
    def validate_inputs(component: PromptComponent, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs against component variables"""
        validated = {}
        
        # Process each variable
        for var in component.variables:
            value = inputs.get(var.name)
            
            # Check required
            if var.required and value is None:
                raise ValueError(f"Required variable '{var.name}' not provided")
            
            # Use default if not provided
            if value is None:
                value = var.default
            
            # Type validation
            if value is not None:
                validated_value = PromptValidator.validate_type(var, value)
                validated[var.name] = validated_value
        
        return validated
    
    @staticmethod
    def validate_type(variable: PromptVariable, value: Any) -> Any:
        """Validate value against variable type and schema"""
        # Basic type validation
        type_map = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_type = type_map.get(variable.type)
        if expected_type and not isinstance(value, expected_type):
            # Try type conversion
            try:
                if variable.type == "string":
                    value = str(value)
                elif variable.type == "number":
                    value = float(value)
                elif variable.type == "boolean":
                    value = bool(value)
                else:
                    raise TypeError(f"Cannot convert {type(value)} to {variable.type}")
            except Exception:
                raise TypeError(
                    f"Variable '{variable.name}' expects {variable.type}, got {type(value).__name__}"
                )
        
        # Schema validation
        if variable.json_schema:
            try:
                validate(instance=value, schema=variable.json_schema)
            except ValidationError as e:
                raise ValueError(f"Schema validation failed for '{variable.name}': {e.message}")
        
        return value
    
    @staticmethod
    def validate_template_syntax(template: str) -> List[str]:
        """Validate template syntax"""
        errors = []
        
        # Check for balanced braces
        open_braces = template.count('{')
        close_braces = template.count('}')
        if open_braces != close_braces:
            errors.append("Unbalanced braces in template")
        
        # Check for empty variables
        if '{}' in template:
            errors.append("Empty variable placeholders found")
        
        # Check for nested braces
        if '{{' in template or '}}' in template:
            errors.append("Nested braces detected - use single braces for variables")
        
        return errors
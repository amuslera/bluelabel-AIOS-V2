import pytest
from scripts.list_prompts import PromptRegistry
from pathlib import Path
import os
import yaml

def test_scan_prompts(tmp_path):
    """Test scanning of prompt files."""
    # Create test prompts directory
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    
    # Create test YAML files
    test_content = {
        'name': 'test_prompt',
        'type': 'test',
        'description': 'Test description',
        'input_format': 'Content: {{content}}',
        'input_fields': ['content', 'context']
    }
    
    (prompts_dir / "test1.yaml").write_text(yaml.dump(test_content))
    (prompts_dir / "test2.yaml").write_text(yaml.dump(test_content))
    
    # Initialize registry
    registry = PromptRegistry(str(prompts_dir))
    prompts = registry.scan_prompts()
    
    assert len(prompts) == 2
    assert all(p['name'] == 'test_prompt' for p in prompts)
    assert all(p['type'] == 'test' for p in prompts)
    assert all(p['input_fields'] == ['content', 'context'] for p in prompts)

def test_extract_input_fields():
    """Test extraction of input fields."""
    registry = PromptRegistry('.')
    
    # Test with explicit input_fields
    content = {
        'input_fields': ['content', 'context']
    }
    fields = registry._extract_input_fields(content)
    assert fields == ['content', 'context']
    
    # Test with Jinja2 variables
    content = {
        'input_format': 'Content: {{content}}\nContext: {{context}}'
    }
    fields = registry._extract_input_fields(content)
    assert fields == ['content', 'context']
    
    # Test with both methods
    content = {
        'input_fields': ['content'],
        'input_format': 'Context: {{context}}'
    }
    fields = registry._extract_input_fields(content)
    assert sorted(fields) == ['content', 'context']

def test_extract_jinja_vars():
    """Test extraction of Jinja2 variables."""
    registry = PromptRegistry('.')
    
    test_text = """
    Content: {{content}}
    Context: {{context}}
    Metadata: {{metadata}}
    """
    
    vars = registry._extract_jinja_vars(test_text)
    assert sorted(vars) == ['content', 'context', 'metadata']

def test_invalid_yaml(tmp_path):
    """Test handling of invalid YAML."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    
    # Create invalid YAML
    (prompts_dir / "invalid.yaml").write_text("invalid: yaml")
    
    registry = PromptRegistry(str(prompts_dir))
    prompts = registry.scan_prompts()
    
    assert len(prompts) == 0

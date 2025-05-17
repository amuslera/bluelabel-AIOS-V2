import pytest
from core.mcp.framework import MCPFramework
from core.mcp.components import MCPComponent, YAMLTemplateComponent, TemplateComponent
from core.mcp.components import MCPComponentConfig
from pathlib import Path
import yaml

def test_component_registration():
    """Test component registration and retrieval."""
    framework = MCPFramework()
    
    # Create test component
    config = MCPComponentConfig(
        name="test_component",
        description="Test component",
        type="test"
    )
    component = TemplateComponent(config, "Hello, {name}!")
    
    # Register component
    framework.register_component(component)
    
    # Test retrieval
    assert framework.get_component("test_component") == component
    assert "test_component" in framework.list_components()

def test_component_rendering():
    """Test component rendering with context."""
    framework = MCPFramework()
    
    # Create and register component
    config = MCPComponentConfig(
        name="greeting",
        description="Greeting component",
        type="greeting"
    )
    component = TemplateComponent(config, "Hello, {name}! Today is {date}")
    framework.register_component(component)
    
    # Test rendering
    context = {
        "name": "World",
        "date": "2025-05-17"
    }
    rendered = framework.render(context)
    assert "Hello, World! Today is 2025-05-17" in rendered

def test_yaml_template_loading(tmp_path):
    """Test loading components from YAML."""
    # Create temporary YAML file
    yaml_content = """
    components:
      - name: greeting
        description: Greeting component
        type: greeting
        template: "Hello, {name}! Today is {date}"
      - name: farewell
        description: Farewell component
        type: farewell
        template: "Goodbye, {name}!"
    """
    
    yaml_file = tmp_path / "components.yaml"
    yaml_file.write_text(yaml_content)
    
    # Load components
    framework = MCPFramework()
    framework.load_from_yaml(str(yaml_file))
    
    # Test components
    assert "greeting" in framework.list_components()
    assert "farewell" in framework.list_components()
    
    # Test rendering
    context = {"name": "World", "date": "2025-05-17"}
    rendered = framework.render(context)
    assert "Hello, World! Today is 2025-05-17" in rendered
    assert "Goodbye, World!" in rendered

def test_component_validation():
    """Test component validation."""
    framework = MCPFramework()
    
    # Create invalid component (missing required field)
    config = MCPComponentConfig(
        name="invalid",
        description="Invalid component",
        type=""  # Empty type should fail validation
    )
    
    with pytest.raises(ValueError):
        component = TemplateComponent(config, "Hello")
        component.validate_config()

def test_error_handling():
    """Test error handling during rendering."""
    framework = MCPFramework()
    
    # Create component with missing template variable
    config = MCPComponentConfig(
        name="error",
        description="Error component",
        type="error"
    )
    component = TemplateComponent(config, "Hello, {missing}!")
    framework.register_component(component)
    
    # Test rendering with missing variable
    context = {"name": "World"}  # missing 'missing' variable
    with pytest.raises(ValueError):
        framework.render(context)

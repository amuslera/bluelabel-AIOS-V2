import pytest
from core.mcp.components.contentmind import ContentMindPromptLoader
from pathlib import Path
import os

def test_contentmind_prompt_loading():
    """Test loading ContentMind prompt from YAML."""
    # Get path to test template
    template_path = Path(__file__).parent.parent / "prompts" / "contentmind" / "contentmind.yaml"
    
    # Create loader and load template
    loader = ContentMindPromptLoader(str(template_path))
    component = loader.load()
    
    # Verify component properties
    assert component.config.name == "contentmind_summarizer"
    assert component.config.version == "1.0"
    assert component.config.type == "contentmind"
    
    # Test rendering with sample context
    context = {
        "content_type": "business report",
        "source": "company quarterly report",
        "content": "Sample content to be summarized...",
        "summary": "This is a summary...",
        "key_points": "- Point 1\n- Point 2",
        "action_items": "- Action 1\n- Action 2"
    }
    
    # Render prompt
    prompt = loader.render(context)
    
    # Verify rendered prompt contains all parts
    assert "You are a professional content summarizer" in prompt
    assert "Content type: business report" in prompt
    assert "Sample content to be summarized..." in prompt
    assert "Summary:" in prompt
    assert "Key points:" in prompt
    assert "Action items:" in prompt

def test_contentmind_prompt_validation():
    """Test prompt validation."""
    # Get path to test template
    template_path = Path(__file__).parent.parent / "prompts" / "contentmind" / "contentmind.yaml"
    
    # Create loader
    loader = ContentMindPromptLoader(str(template_path))
    
    # Test with missing required context
    with pytest.raises(ValueError):
        loader.render({"content_type": "test"})  # Missing other required fields

def test_contentmind_prompt_fallback():
    """Test fallback behavior with invalid template."""
    # Create loader with non-existent template
    loader = ContentMindPromptLoader("nonexistent.yaml")
    
    with pytest.raises(FileNotFoundError):
        loader.load()

def test_contentmind_prompt_customization():
    """Test customizing the prompt with different configurations."""
    # Get path to test template
    template_path = Path(__file__).parent.parent / "prompts" / "contentmind" / "contentmind.yaml"
    
    # Create loader and load template
    loader = ContentMindPromptLoader(str(template_path))
    component = loader.load()
    
    # Test with different content type
    context = {
        "content_type": "technical documentation",
        "source": "API reference",
        "content": "Technical content...",
        "summary": "Technical summary...",
        "key_points": "- Technical point 1\n- Technical point 2",
        "action_items": "- Technical action 1\n- Technical action 2"
    }
    
    prompt = loader.render(context)
    assert "Content type: technical documentation" in prompt
    assert "Technical content..." in prompt
    assert "Technical summary..." in prompt

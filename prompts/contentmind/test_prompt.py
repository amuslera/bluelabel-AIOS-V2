from loader import ContentMindPromptLoader
import pytest

def test_prompt_loader():
    """Test the prompt loader with various configurations."""
    loader = ContentMindPromptLoader()
    
    # Test basic prompt generation
    test_content = """
    Machine learning is a subset of AI that enables computers to learn from data.
    It includes techniques like neural networks and decision trees.
    """
    
    prompt = loader.get_prompt(test_content)
    
    assert 'system' in prompt
    assert 'user' in prompt
    assert 'config' in prompt
    
    # Test configuration overrides
    custom_config = {
        'temperature': 0.5,
        'max_tokens': 1500,
        'summary_style': 'detailed'
    }
    
    custom_prompt = loader.get_prompt(test_content, custom_config)
    assert custom_prompt['config']['temperature'] == 0.5
    
    # Test input validation
    assert loader.validate_input("short text")
    assert not loader.validate_input("a" * 10001)  # Exceeds max length
    
    # Test error message generation
def test_error_messages():
    loader = ContentMindPromptLoader()
    
    # Test input too long error
    error_msg = loader.get_error_message(
        "input_too_long",
        max_input_length=10000
    )
    assert "exceeds maximum length" in error_msg
    
    # Test empty content error
    error_msg = loader.get_error_message("empty_content")
    assert "No content provided" in error_msg

def test_prompt_structure():
    """Test the structure of generated prompts."""
    loader = ContentMindPromptLoader()
    
    test_content = """
    Title: Introduction to Neural Networks
    
    Neural networks are a series of algorithms that mimic the operation of a human brain.
    They can be used to recognize patterns and make decisions.
    """
    
    prompt = loader.get_prompt(test_content)
    
    # Check system prompt structure
    assert "professional technical content summarizer" in prompt['system']
    assert "Key requirements" in prompt['system']
    
    # Check user prompt structure
    assert "Please summarize the following technical content" in prompt['user']
    assert test_content in prompt['user']
    
    # Check config structure
    assert 'model' in prompt['config']
    assert 'temperature' in prompt['config']
    assert 'max_tokens' in prompt['config']

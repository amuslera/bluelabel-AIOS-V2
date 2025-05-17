# ContentMind Prompt System

This directory contains the prompt templates and utilities for the ContentMind agent. The system is designed to be modular, configurable, and testable.

## Template Structure

Templates are defined in YAML format and follow this structure:

```yaml
config:
  # Model and processing parameters
  model: "{{ model }}"
  temperature: 0.7
  max_tokens: 2000
  
  # Content processing settings
  max_input_length: 10000
  chunk_size: 2000
  overlap: 300

prompt_template:
  system: """System prompt content"""
  user: """User prompt content with {{ variables }}"""
  assistant: """Expected assistant response format"""

examples:
  - input: "Example input"
    output: "Expected output"

error_handling:
  - type: "error_type"
    message: "Error message template"
```

## Usage

1. **Create/Modify Templates**:
   - Edit YAML files in this directory
   - Use Jinja2 templating for dynamic values
   - Follow the template structure above

2. **Load Prompts**:
   ```python
   from loader import ContentMindPromptLoader
   
   loader = ContentMindPromptLoader()
   prompt = loader.get_prompt(
       content="Your content here",
       config={
           "temperature": 0.5,
           "max_tokens": 1500
       }
   )
   ```

3. **Run Tests**:
   ```bash
   pytest test_prompt.py
   ```

## Template Variables

Available variables in templates:

- `{{ content }}`: The input content to process
- `{{ model }}`: Current model configuration
- Any additional variables passed in config

## Error Handling

The system includes built-in error handling for:
- Input length validation
- Empty content detection
- Invalid model configurations

## Adding New Templates

To add a new template:
1. Create a new YAML file in this directory
2. Follow the template structure above
3. Add example inputs/outputs
4. Add error handling as needed
5. Add test cases in `test_prompt.py`

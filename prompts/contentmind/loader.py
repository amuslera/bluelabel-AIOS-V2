import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from jinja2 import Template


class ContentMindPromptLoader:
    def __init__(self, template_path: str = "summarization.yaml"):
        """
        Initialize the prompt loader with the template path.
        """
        self.template_path = Path(__file__).parent / template_path
        self.template_data = self._load_template()
        
    def _load_template(self) -> Dict[str, Any]:
        """
        Load and parse the YAML template file.
        """
        with open(self.template_path, 'r') as f:
            return yaml.safe_load(f)
            
    def get_prompt(self, content: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        Generate a complete prompt structure from the template.
        
        Args:
            content: The text content to summarize
            config: Optional configuration overrides
            
        Returns:
            A dictionary containing the complete prompt structure
        """
        if config is None:
            config = {}
            
        # Get base configuration
        base_config = self.template_data['config']
        
        # Override with provided config
        for key, value in config.items():
            if key in base_config:
                base_config[key] = value
                
        # Create Jinja2 template from prompt components
        system_template = Template(self.template_data['prompt_template']['system'])
        user_template = Template(self.template_data['prompt_template']['user'])
        
        # Render templates
        system_prompt = system_template.render()
        user_prompt = user_template.render(
            content=content,
            **config
        )
        
        return {
            'system': system_prompt,
            'user': user_prompt,
            'config': base_config
        }
        
    def validate_input(self, content: str) -> bool:
        """
        Validate the input content against template constraints.
        """
        max_length = self.template_data['config']['max_input_length']
        return len(content) <= max_length
        
    def get_error_message(self, error_type: str, **kwargs) -> str:
        """
        Get an appropriate error message for a given error type.
        """
        for error in self.template_data['error_handling']:
            if error['type'] == error_type:
                return Template(error['message']).render(**kwargs)
        return "Unknown error occurred"

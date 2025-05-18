import sys
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

class PromptRegistry:
    """Registry for MCP prompt templates."""
    
    def __init__(self, prompts_dir: str):
        """Initialize with prompts directory."""
        self.prompts_dir = Path(prompts_dir)
        self.console = Console()
        
    def scan_prompts(self) -> List[Dict[str, Any]]:
        """Scan directory for YAML prompt files."""
        prompts = []
        
        if not self.prompts_dir.exists():
            self.console.print(f"[red]Error: Directory not found: {self.prompts_dir}[/]")
            sys.exit(1)
            
        for file_path in self.prompts_dir.rglob("*.yaml"):
            try:
                with open(file_path, 'r') as f:
                    content = yaml.safe_load(f)
                prompts.append({
                    'path': file_path,
                    'content': content,
                    'name': content.get('name', 'N/A'),
                    'type': content.get('type', 'N/A'),
                    'input_fields': self._extract_input_fields(content)
                })
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to process {file_path}: {str(e)}[/]")
                continue
                
        return prompts
        
    def _extract_input_fields(self, content: Dict[str, Any]) -> List[str]:
        """Extract input fields from template."""
        fields = set()
        
        # Check input_format section
        if 'input_format' in content:
            fields.update(self._extract_jinja_vars(content['input_format']))
            
        # Check for explicit input_fields declaration
        if 'input_fields' in content:
            fields.update(content['input_fields'])
            
        return sorted(fields)
        
    def _extract_jinja_vars(self, text: str) -> set:
        """Extract Jinja2 variable names from text."""
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        return set(re.findall(pattern, text))
        
    def print_summary(self, prompts: List[Dict[str, Any]]) -> None:
        """Print summary table."""
        table = Table(title="MCP Prompt Registry Summary", box=box.ROUNDED)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Path", style="yellow")
        table.add_column("Fields", style="magenta")
        
        for prompt in prompts:
            table.add_row(
                prompt['name'],
                prompt['type'],
                str(prompt['path']),
                ", ".join(prompt['input_fields'])
            )
            
        self.console.print(table)
        
    def print_verbose(self, prompts: List[Dict[str, Any]]) -> None:
        """Print detailed information about each prompt."""
        for prompt in prompts:
            panel_content = f"""
Name: {prompt['name']}
Type: {prompt['type']}
Path: {prompt['path']}

Input Fields: {', '.join(prompt['input_fields'])}

Metadata:
"""
            
            # Add metadata sections
            for key in ['description', 'role', 'instruction', 'input_format', 'output_format']:
                if key in prompt['content']:
                    panel_content += f"\n{key.title()}:\n{prompt['content'][key]}\n"
                    
            self.console.print(Panel(panel_content, title=f"Prompt: {prompt['name']}", box=box.ROUNDED))
            
    def print_json(self, prompts: List[Dict[str, Any]]) -> None:
        """Print prompts in JSON format."""
        import json
        json_output = [{
            'name': p['name'],
            'type': p['type'],
            'path': str(p['path']),
            'input_fields': p['input_fields'],
            'metadata': {
                k: v for k, v in p['content'].items() 
                if k not in ['name', 'type', 'input_format', 'output_format']
            }
        } for p in prompts]
        
        print(json.dumps(json_output, indent=2))

@click.command()
@click.argument('directory', default='prompts')
@click.option('--summary', '-s', is_flag=True, help='Show compact summary table')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
@click.option('--json', '-j', is_flag=True, help='Output in JSON format')
def main(directory: str, summary: bool, verbose: bool, json: bool):
    """List and inspect MCP prompt templates."""
    registry = PromptRegistry(directory)
    prompts = registry.scan_prompts()
    
    if not prompts:
        registry.console.print("[yellow]No prompt templates found[/]")
        sys.exit(0)
        
    if json:
        registry.print_json(prompts)
    elif summary:
        registry.print_summary(prompts)
    elif verbose:
        registry.print_verbose(prompts)
    else:
        registry.print_summary(prompts)

if __name__ == '__main__':
    main()

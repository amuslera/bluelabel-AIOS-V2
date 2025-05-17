from core.mcp.components.contentmind import ContentMindPromptLoader
from pathlib import Path
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def create_contentmind_prompt(content: str, content_type: str, source: str) -> str:
    """
    Create a ContentMind prompt using the MCP framework.
    
    Args:
        content: The content to be summarized
        content_type: Type of content (e.g., "business report", "technical documentation")
        source: Source of the content
        
    Returns:
        str: The complete rendered prompt
    """
    try:
        # Get template path
        template_path = Path(__file__).parent.parent / "prompts" / "contentmind" / "contentmind.yaml"
        
        # Create and load loader
        loader = ContentMindPromptLoader(str(template_path))
        loader.load()
        
        # Prepare context
        context = {
            "content_type": content_type,
            "source": source,
            "content": content,
            "summary": "",  # Will be filled by LLM
            "key_points": "",  # Will be filled by LLM
            "action_items": ""  # Will be filled by LLM
        }
        
        # Render prompt
        prompt = loader.render(context)
        
        # Log the rendered prompt for debugging
        logger.info("Rendered ContentMind prompt:")
        logger.info(prompt)
        
        return prompt
        
    except Exception as e:
        logger.error(f"Error creating ContentMind prompt: {str(e)}")
        # Fallback to simple prompt if MCP fails
        return f"""Summarize the following {content_type} from {source}:

{content}

Summary:"""

def main():
    # Example usage
    sample_content = """
    This is a sample business report containing important financial metrics and strategic insights.
    The company reported Q1 revenue of $10M, an increase of 20% YoY.
    Key initiatives include expanding into international markets and launching new product lines.
    """
    
    # Create prompt
    prompt = create_contentmind_prompt(
        content=sample_content,
        content_type="business report",
        source="company quarterly report"
    )
    
    # Output the prompt
    print("\nFinal prompt:")
    print(prompt)

if __name__ == "__main__":
    main()

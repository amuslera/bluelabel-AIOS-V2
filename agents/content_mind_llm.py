"""ContentMind agent with LLM integration."""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

from .base import Agent, AgentInput, AgentOutput
from core.config import settings
from services.model_router.router import ModelRouter
from services.model_router.factory import create_default_router
from services.mcp.manager import PromptManager
from services.mcp.factory import create_prompt_manager

logger = logging.getLogger(__name__)


class ContentMindLLM(Agent):
    """ContentMind agent with integrated LLM routing and prompt management."""
    
    def __init__(
        self,
        model_router: Optional[ModelRouter] = None,
        prompt_manager: Optional[PromptManager] = None
    ):
        super().__init__(
            name="ContentMind LLM",
            description="AI-powered content processing and analysis agent"
        )
        
        # Generate unique agent ID
        self.agent_id = f"content_mind_llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.capabilities = ["content_analysis", "summarization", "llm_powered"]
        
        # Initialize or use provided components
        self.model_router = model_router
        self.prompt_manager = prompt_manager
        self._initialized_router = False
    
    async def _ensure_initialized(self):
        """Ensure components are initialized"""
        if not self._initialized_router and not self.model_router:
            self.model_router = await create_default_router()
            self._initialized_router = True
        if not self.prompt_manager:
            self.prompt_manager = create_prompt_manager()
    
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process content using LLM-powered analysis."""
        try:
            await self._ensure_initialized()
            content_type = input_data.metadata.get("content_type", "text")
            
            # Extract content based on type
            if content_type == "text":
                content = input_data.content.get("content", "")
            elif content_type == "url":
                content = await self._extract_url_content(input_data.content.get("url"))
            elif content_type == "pdf":
                content = await self._extract_pdf_content(input_data.content.get("file_path"))
            else:
                raise ValueError(f"Unknown content type: {content_type}")
            
            # Perform LLM-powered analysis
            summary = await self._summarize_content(content)
            concepts = await self._extract_key_concepts(content)
            metadata = await self._generate_metadata(content)
            
            # Build results
            results = {
                "summary": summary,
                "concepts": concepts,
                "metadata": metadata,
                "content_type": content_type,
                "processed_at": datetime.now().isoformat()
            }
            
            return AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result=results
            )
            
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            return AgentOutput(
                task_id=input_data.task_id,
                status="error",
                error=str(e),
                result={}
            )
    
    async def _summarize_content(self, content: str) -> str:
        """Generate an executive summary using LLM."""
        try:
            prompt_messages = self.prompt_manager.render_prompt(
                "content_summarizer",
                {"content": content}
            )
            
            response = await self.model_router.chat(prompt_messages)
            return response.text
            
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            # Fallback to simple truncation
            return content[:500] + "..." if len(content) > 500 else content
    
    async def _extract_key_concepts(self, content: str) -> List[str]:
        """Extract key concepts from content."""
        try:
            # Use a simple prompt for concept extraction
            prompt = f"Extract 5-7 key concepts from the following content. List them as comma-separated terms:\n\n{content[:1000]}"
            
            response = await self.model_router.complete(prompt)
            
            # Parse comma-separated concepts
            concepts = [c.strip() for c in response.text.split(",")]
            return concepts[:7]  # Limit to 7 concepts
            
        except Exception as e:
            logger.error(f"Error extracting concepts: {e}")
            return []
    
    async def _generate_metadata(self, content: str) -> Dict[str, Any]:
        """Generate metadata about the content."""
        try:
            # Simple metadata generation
            return {
                "word_count": len(content.split()),
                "char_count": len(content),
                "category": await self._categorize_content(content),
                "sentiment": await self._analyze_sentiment(content),
                "language": "en",  # Would use LLM to detect in production
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating metadata: {e}")
            return {"error": str(e)}
    
    async def _categorize_content(self, content: str) -> str:
        """Categorize content using LLM."""
        try:
            prompt = f"Categorize this content into one of: Technology, Business, Science, Politics, Entertainment, Sports, Other. Content: {content[:500]}"
            response = await self.model_router.complete(prompt)
            
            categories = ["Technology", "Business", "Science", "Politics", "Entertainment", "Sports", "Other"]
            for cat in categories:
                if cat.lower() in response.text.lower():
                    return cat
            return "Other"
            
        except Exception:
            return "Other"
    
    async def _analyze_sentiment(self, content: str) -> str:
        """Analyze sentiment of content."""
        try:
            prompt = f"Analyze the sentiment of this content as positive, negative, or neutral: {content[:300]}"
            response = await self.model_router.complete(prompt)
            
            sentiment = response.text.lower()
            if "positive" in sentiment:
                return "positive"
            elif "negative" in sentiment:
                return "negative"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    async def _extract_url_content(self, url: str) -> str:
        """Extract content from URL (mock implementation)."""
        # In production, would use actual web scraping
        return f"Mock content extracted from URL: {url}"
    
    async def _extract_pdf_content(self, file_path: str) -> str:
        """Extract content from PDF (mock implementation)."""
        # In production, would use PDF parsing library
        return f"Mock content extracted from PDF: {file_path}"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities including supported models and prompts."""
        return {
            "content_types": ["text", "url", "pdf"],
            "analysis_types": ["summary", "concepts", "metadata", "sentiment"],
            "models": self.model_router.get_available_models() if self.model_router and hasattr(self.model_router, 'get_available_models') else [],
            "prompts": list(self.prompt_manager.list_prompts()) if self.prompt_manager else [],
            "max_content_length": 100000
        }
    
    async def initialize(self) -> bool:
        """Initialize the agent."""
        try:
            # Ensure prompt templates are loaded
            if self.prompt_manager and len(list(self.prompt_manager.list_prompts())) == 0:
                from services.mcp.factory import initialize_default_components
                await initialize_default_components(self.prompt_manager)
            
            logger.info(f"ContentMindLLM initialized with {len(list(self.prompt_manager.list_prompts()))} prompts")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ContentMindLLM: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown the agent."""
        logger.info("ContentMindLLM shutting down")
        return True
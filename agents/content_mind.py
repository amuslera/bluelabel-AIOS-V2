"""ContentMind Agent - The primary content processing agent.

ContentMind is the core agent responsible for:
- Processing incoming content (PDFs, URLs, audio)
- Extracting and structuring information
- Creating summaries and insights
- Coordinating with other agents for specialized tasks
"""

import asyncio
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime
import logging
from enum import Enum

from agents.base import Agent, AgentInput, AgentOutput
from agents.digest_agent import DigestAgent
from services.content.pdf_extractor import PDFExtractor
from services.content.url_extractor import URLExtractor
from services.content.audio_transcriber import AudioTranscriber
from services.llm_router import LLMRouter, LLMMessage
from core.event_bus import EventBus

if TYPE_CHECKING:
    from services.workflow.langgraph_engine import LangGraphWorkflowEngine

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Supported content types."""
    TEXT = "text"
    PDF = "pdf"
    URL = "url"
    AUDIO = "audio"
    VIDEO = "video"


class ContentMind(Agent):
    """Primary agent for content processing and knowledge creation."""
    
    def __init__(self,
                 agent_id: str = "content_mind",
                 event_bus: Optional[EventBus] = None,
                 workflow_engine: Optional['LangGraphWorkflowEngine'] = None,
                 llm_router: Optional[LLMRouter] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize ContentMind agent.
        
        Args:
            agent_id: Unique identifier for the agent
            event_bus: Event bus for publishing events
            workflow_engine: Workflow engine for orchestration
            llm_router: LLM router for model access
            metadata: Optional metadata
        """
        super().__init__(
            name="ContentMind",
            description="Primary agent for content processing and knowledge creation",
            agent_id=agent_id
        )
        self.event_bus = event_bus
        self.workflow_engine = workflow_engine
        self.llm_router = llm_router or LLMRouter()
        self.metadata = metadata or {}
        
        # Initialize content processors
        self.pdf_extractor = PDFExtractor()
        self.url_extractor = URLExtractor()
        self.audio_transcriber = AudioTranscriber(model_size="base")
        self.digest_agent = DigestAgent(llm_router=self.llm_router)
        
        self._initialized = False
        
        # Processing templates
        self.templates = {
            "content_analysis": {
                "system": """You are ContentMind, an expert content analysis agent.
                Your task is to analyze content deeply and extract valuable insights.
                Focus on understanding the main ideas, key facts, and implications.""",
                
                "prompt": """Analyze the following content:

Title: {title}
Type: {content_type}
Source: {source}

Content:
{content}

Please provide:
1. Main Topic and Theme
2. Key Points (5-7 bullet points)
3. Important Facts and Figures
4. Insights and Implications
5. Related Topics for Further Research
6. Suggested Tags for Classification

Format your response as structured JSON."""
            },
            
            "entity_extraction": {
                "system": """You are an expert at extracting entities and relationships from text.
                Focus on people, organizations, locations, dates, and their relationships.""",
                
                "prompt": """Extract entities from this content:

{content}

Identify:
1. People (names, roles, affiliations)
2. Organizations (companies, institutions)
3. Locations (cities, countries, addresses)
4. Dates and Time References
5. Key Relationships between entities
6. Important Events

Format as structured data."""
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize the ContentMind agent."""
        try:
            # Initialize sub-components
            await self.llm_router.initialize()
            await self.digest_agent.initialize()
            
            # Initialize workflow if available
            if self.workflow_engine:
                # Register this agent with the workflow engine
                self.workflow_engine.register_agent(self.agent_id, self)
            
            self._initialized = True
            logger.info(f"ContentMind agent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing ContentMind: {e}")
            return False
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process incoming content and create structured knowledge.
        
        Args:
            input: Agent input containing content to process
            
        Returns:
            Agent output with processed content
        """
        if not self._initialized:
            return AgentOutput(
                task_id=input.task_id,
                status="error",
                result={"error": "Agent not initialized"},
                error="Agent not initialized"
            )
        try:
            # Determine content type
            content_type = input.context.get("content_type", ContentType.TEXT)

            # Extract content based on type
            extracted_content = await self._extract_content(input, content_type)
            if not extracted_content["success"]:
                return AgentOutput(
                    task_id=input.task_id,
                    status="error",
                    result={"error": extracted_content.get("error", "Extraction failed")},
                    error=extracted_content.get("error", "Extraction failed")
                )

            # Always get the string content for downstream steps
            content_str = extracted_content["content"]
            if isinstance(content_str, dict):
                # Try to extract 'text' key if present
                content_str = content_str.get("text", "")
            if not isinstance(content_str, str):
                content_str = str(content_str)
            if not content_str.strip():
                return AgentOutput(
                    task_id=input.task_id,
                    status="error",
                    result={"error": "Content is empty after extraction"},
                    error="Content is empty after extraction"
                )

            # Analyze content
            analysis = await self._analyze_content(
                content=content_str,
                metadata=extracted_content["metadata"]
            )
            if "error" in analysis:
                return AgentOutput(
                    task_id=input.task_id,
                    status="error",
                    result={"error": f"Analysis failed: {analysis['error']}"},
                    error=f"Analysis failed: {analysis['error']}"
                )

            # Extract entities
            entities = await self._extract_entities(content_str)
            if "error" in entities:
                return AgentOutput(
                    task_id=input.task_id,
                    status="error",
                    result={"error": f"Entity extraction failed: {entities['error']}"},
                    error=f"Entity extraction failed: {entities['error']}"
                )

            # Create summary
            summary = await self._create_summary(content_str, analysis)
            if "error" in summary:
                return AgentOutput(
                    task_id=input.task_id,
                    status="error",
                    result={"error": f"Summary generation failed: {summary['error']}"},
                    error=f"Summary generation failed: {summary['error']}"
                )

            # Generate tags
            tags = self._generate_tags(analysis, entities)

            # Compile results
            result = {
                "content_type": content_type.value,
                "extracted_content": extracted_content,
                "analysis": analysis,
                "entities": entities,
                "summary": summary,
                "tags": tags,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Publish event if available
            if self.event_bus:
                await self.event_bus.publish({
                    "event_type": "content.processed",
                    "payload": {
                        "agent_id": self.agent_id,
                        "content_type": content_type.value,
                        "tags": tags,
                        "summary_length": len(summary.get("text", "")),
                        "entity_count": len(entities.get("entities", []))
                    }
                })

            return AgentOutput(
                task_id=input.task_id,
                status="success",
                result=result,
                error=None
            )
        except Exception as e:
            logger.error(f"Error in ContentMind processing: {e}")
            return AgentOutput(
                task_id=input.task_id,
                status="error",
                result={"error": str(e)},
                error=str(e)
            )
    
    async def _extract_content(self, input: AgentInput, content_type: ContentType) -> Dict[str, Any]:
        """Extract content based on type."""
        try:
            if content_type == ContentType.TEXT:
                # Accept both dict and str for input.content
                if isinstance(input.content, dict):
                    text = input.content.get("text", "")
                else:
                    text = str(input.content)
                if not text.strip():
                    return {"success": False, "error": "No text content provided"}
                return {
                    "success": True,
                    "content": text,
                    "metadata": {
                        "source": "direct_input",
                        "length": len(text)
                    }
                }
            
            elif content_type == ContentType.PDF:
                file_path = input.metadata.get("file_path")
                if not file_path:
                    return {"success": False, "error": "No file path provided"}
                
                extracted = await self.pdf_extractor.extract(file_path)
                return {
                    "success": bool(extracted["text"]),
                    "content": extracted["text"],
                    "metadata": extracted["metadata"]
                }
            
            elif content_type == ContentType.URL:
                url = input.content or input.metadata.get("url")
                if not url:
                    return {"success": False, "error": "No URL provided"}
                
                extracted = await self.url_extractor.extract(url)
                return {
                    "success": bool(extracted["content"].get("text")),
                    "content": extracted["content"].get("text", ""),
                    "metadata": {
                        **extracted["metadata"],
                        "title": extracted["content"].get("title"),
                        "source": url
                    }
                }
            
            elif content_type == ContentType.AUDIO:
                file_path = input.metadata.get("file_path")
                if not file_path:
                    return {"success": False, "error": "No file path provided"}
                
                transcribed = await self.audio_transcriber.transcribe(file_path)
                return {
                    "success": transcribed["status"] == "completed",
                    "content": transcribed["transcription"].get("text", ""),
                    "metadata": {
                        **transcribed["metadata"],
                        "language": transcribed["transcription"].get("language")
                    }
                }
            
            else:
                return {"success": False, "error": f"Unsupported content type: {content_type}"}
                
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_content(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using LLM."""
        try:
            template = self.templates["content_analysis"]
            
            messages = [
                LLMMessage(role="system", content=template["system"]),
                LLMMessage(
                    role="user",
                    content=template["prompt"].format(
                        title=metadata.get("title", "Untitled"),
                        content_type=metadata.get("content_type", "text"),
                        source=metadata.get("source", "Unknown"),
                        content=content[:3000]  # Limit content length
                    )
                )
            ]
            
            response = await self.llm_router.generate(
                messages=messages,
                model_preferences=["gpt-4", "claude-3-opus"],
                max_tokens=800
            )
            
            # Parse JSON response
            import json
            try:
                analysis = json.loads(response.content)
            except:
                # Fallback to text response
                analysis = {"raw_response": response.content}
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {"error": str(e)}
    
    async def _extract_entities(self, content: str) -> Dict[str, Any]:
        """Extract entities from content."""
        try:
            template = self.templates["entity_extraction"]
            
            messages = [
                LLMMessage(role="system", content=template["system"]),
                LLMMessage(
                    role="user",
                    content=template["prompt"].format(content=content[:2000])
                )
            ]
            
            response = await self.llm_router.generate(
                messages=messages,
                model_preferences=["gpt-4", "claude-3-opus"],
                max_tokens=500
            )
            
            # Parse response
            import json
            try:
                entities = json.loads(response.content)
            except:
                entities = {"raw_response": response.content}
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {"error": str(e)}
    
    async def _create_summary(self, content: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create content summary using DigestAgent."""
        try:
            # Prepare input for DigestAgent
            digest_input = AgentInput(
                source="contentmind",
                content={"text": content},
                context={"content_type": "article"},
                metadata={
                    "title": analysis.get("title", "Untitled"),
                    "analysis": analysis
                }
            )
            result = await self.digest_agent.process(digest_input)
            if hasattr(result, "status") and result.status == "success":
                return result.result
            else:
                return {"error": "Summary generation failed"}
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return {"error": str(e)}
    
    def _generate_tags(self, analysis: Dict[str, Any], entities: Dict[str, Any]) -> List[str]:
        """Generate tags from analysis and entities."""
        tags = []
        
        # Extract tags from analysis
        if "suggested_tags" in analysis:
            tags.extend(analysis["suggested_tags"])
        
        # Extract tags from entities
        if "organizations" in entities:
            tags.extend([org.get("name", "") for org in entities["organizations"]][:3])
        
        if "topics" in analysis:
            tags.extend(analysis["topics"][:5])
        
        # Clean and deduplicate
        tags = list(set(tag.lower().strip() for tag in tags if tag))
        
        return tags[:10]  # Limit to 10 tags
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "agent_id": self.agent_id,
            "type": "content_processing",
            "supported_content_types": [ct.value for ct in ContentType],
            "features": [
                "pdf_extraction",
                "url_extraction",
                "audio_transcription",
                "content_analysis",
                "entity_extraction",
                "summarization",
                "tag_generation"
            ],
            "sub_agents": ["digest_agent"],
            "max_content_size": 10_000_000  # 10MB
        }
    
    async def process_batch(self, items: List[Dict[str, Any]]) -> List[AgentOutput]:
        """Process multiple content items in batch."""
        tasks = []
        
        for item in items:
            input_data = AgentInput(
                content=item.get("content", ""),
                context=item.get("context", {}),
                metadata=item.get("metadata", {})
            )
            tasks.append(self.process(input_data))
        
        return await asyncio.gather(*tasks)
    
    async def shutdown(self) -> bool:
        """Shutdown the agent."""
        try:
            # Shutdown sub-agents
            await self.digest_agent.shutdown()
            
            self._initialized = False
            logger.info(f"ContentMind agent {self.agent_id} shutdown successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error shutting down ContentMind: {e}")
            return False


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create ContentMind agent
        agent = ContentMind()
        
        # Initialize
        await agent.initialize()
        
        # Example 1: Process text content
        text_input = AgentInput(
            content="Artificial Intelligence is transforming industries...",
            context={"content_type": ContentType.TEXT},
            metadata={"source": "manual_input"}
        )
        
        result = await agent.process(text_input)
        print("Text processing result:", result.content.get("summary"))
        
        # Example 2: Process URL
        url_input = AgentInput(
            content="https://example.com/article",
            context={"content_type": ContentType.URL},
            metadata={}
        )
        
        # This would process the URL if valid
        # url_result = await agent.process(url_input)
        
        # Shutdown
        await agent.shutdown()
    
    # Run example
    asyncio.run(example_usage())
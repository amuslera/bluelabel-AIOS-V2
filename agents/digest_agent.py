"""DigestAgent for content summarization.

This agent takes various types of content (text, articles, documents)
and creates concise, well-structured summaries for daily digests.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

from agents.base import Agent, AgentInput, AgentOutput
from services.llm_router import LLMRouter, LLMMessage
from core.event_bus import EventBus

logger = logging.getLogger(__name__)


class DigestAgent(Agent):
    """Agent specialized in creating content digests and summaries."""
    
    def __init__(self,
                 agent_id: str = "digest_agent",
                 llm_router: Optional[LLMRouter] = None,
                 event_bus: Optional[EventBus] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize the DigestAgent.
        
        Args:
            agent_id: Unique identifier for the agent
            llm_router: LLM router for model access
            event_bus: Event bus for publishing events
            metadata: Optional metadata
        """
        super().__init__(agent_id, metadata)
        self.llm_router = llm_router or LLMRouter()
        self.event_bus = event_bus
        self._initialized = False
        
        # Default summarization templates
        self.templates = {
            "article": {
                "system": """You are a professional content summarizer. Your task is to create concise, 
                informative summaries that capture the key points while maintaining readability.
                
                Guidelines:
                - Focus on main ideas and key takeaways
                - Use clear, concise language
                - Maintain objectivity
                - Structure with bullet points when appropriate
                - Keep summaries under 200 words unless specified otherwise""",
                
                "prompt": """Please summarize the following article:

Title: {title}
Source: {source}
Date: {date}

Content:
{content}

Create a summary that includes:
1. Main topic/thesis (1-2 sentences)
2. Key points (3-5 bullet points)
3. Important details or conclusions
4. Relevance/significance (1 sentence)

Keep the summary concise but comprehensive."""
            },
            
            "document": {
                "system": """You are an expert at analyzing and summarizing documents. 
                Create structured summaries that highlight key information.""",
                
                "prompt": """Summarize this document:

Document Type: {doc_type}
Title: {title}

Content:
{content}

Provide:
1. Document overview
2. Main sections/topics
3. Key findings or decisions
4. Action items (if any)
5. Conclusions"""
            },
            
            "daily_digest": {
                "system": """You are creating a daily digest of important content. 
                The digest should be engaging, informative, and easy to scan.""",
                
                "prompt": """Create a daily digest from the following content items:

{items}

Format the digest as:
1. Executive Summary (2-3 sentences)
2. Top Stories/Items (with brief summaries)
3. Key Insights
4. Recommended Actions (if applicable)

Make it scannable and highlight the most important information."""
            },
            
            "conversation": {
                "system": """You are summarizing conversations and discussions. 
                Focus on key points, decisions, and action items.""",
                
                "prompt": """Summarize this conversation:

Participants: {participants}
Topic: {topic}

Conversation:
{content}

Include:
1. Main discussion points
2. Decisions made
3. Action items and assignments
4. Next steps
5. Key takeaways"""
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize the agent."""
        try:
            # Initialize LLM router if needed
            if hasattr(self.llm_router, 'initialize'):
                await self.llm_router.initialize()
            
            self._initialized = True
            logger.info(f"DigestAgent {self.agent_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing DigestAgent: {e}")
            return False
    
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process input to create a summary or digest.
        
        Args:
            input: Agent input containing content to summarize
            
        Returns:
            Agent output with summary
        """
        if not self._initialized:
            return AgentOutput(
                success=False,
                content={"error": "Agent not initialized"},
                metadata={"agent_id": self.agent_id}
            )
        
        try:
            # Extract content and context
            content_type = input.context.get("content_type", "article")
            content = input.content
            metadata = input.metadata or {}
            
            # Choose appropriate template
            template = self.templates.get(content_type, self.templates["article"])
            
            # Prepare the prompt
            if content_type == "daily_digest":
                # Handle multiple items for daily digest
                items = metadata.get("items", [])
                formatted_items = self._format_digest_items(items)
                prompt_vars = {"items": formatted_items}
            else:
                # Single content summarization
                prompt_vars = {
                    "content": content,
                    "title": metadata.get("title", "Untitled"),
                    "source": metadata.get("source", "Unknown"),
                    "date": metadata.get("date", datetime.now().isoformat()),
                    "doc_type": metadata.get("doc_type", "General"),
                    "topic": metadata.get("topic", "General Discussion"),
                    "participants": metadata.get("participants", "Unknown")
                }
            
            # Format the prompt
            system_message = template["system"]
            user_prompt = template["prompt"].format(**prompt_vars)
            
            # Call LLM for summarization
            messages = [
                LLMMessage(role="system", content=system_message),
                LLMMessage(role="user", content=user_prompt)
            ]
            
            logger.info(f"Generating {content_type} summary")
            response = await self.llm_router.generate(
                messages=messages,
                model_preferences=["gpt-4", "gpt-3.5-turbo", "claude-instant"],
                max_tokens=500
            )
            
            summary = response.content
            
            # Post-process the summary
            processed_summary = self._post_process_summary(summary, content_type)
            
            # Publish event if available
            if self.event_bus:
                await self.event_bus.publish({
                    "event_type": "digest.created",
                    "payload": {
                        "agent_id": self.agent_id,
                        "content_type": content_type,
                        "summary_length": len(processed_summary),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                })
            
            return AgentOutput(
                success=True,
                content={
                    "summary": processed_summary,
                    "content_type": content_type,
                    "word_count": len(processed_summary.split()),
                    "timestamp": datetime.utcnow().isoformat()
                },
                metadata={
                    "agent_id": self.agent_id,
                    "template_used": content_type,
                    "model_used": response.model if hasattr(response, 'model') else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error in DigestAgent processing: {e}")
            return AgentOutput(
                success=False,
                content={"error": str(e)},
                metadata={"agent_id": self.agent_id}
            )
    
    def _format_digest_items(self, items: List[Dict[str, Any]]) -> str:
        """Format multiple items for daily digest."""
        formatted_items = []
        
        for i, item in enumerate(items, 1):
            item_text = f"""
Item {i}:
Title: {item.get('title', 'Untitled')}
Type: {item.get('type', 'Unknown')}
Source: {item.get('source', 'Unknown')}
Content: {item.get('content', '')[:500]}...
---"""
            formatted_items.append(item_text)
        
        return "\n\n".join(formatted_items)
    
    def _post_process_summary(self, summary: str, content_type: str) -> str:
        """Post-process the summary for better formatting."""
        # Clean up the summary
        summary = summary.strip()
        
        # Add formatting based on content type
        if content_type == "daily_digest":
            # Ensure proper markdown formatting for digests
            lines = summary.split('\n')
            processed_lines = []
            
            for line in lines:
                line = line.strip()
                if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    # Ensure proper list formatting
                    processed_lines.append('\n' + line)
                elif line.startswith(('-', '•', '*')):
                    # Bullet points
                    processed_lines.append('  ' + line)
                else:
                    processed_lines.append(line)
            
            summary = '\n'.join(processed_lines)
        
        return summary
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "agent_id": self.agent_id,
            "type": "summarization",
            "supported_content_types": list(self.templates.keys()),
            "features": [
                "article_summarization",
                "document_analysis",
                "daily_digest_creation",
                "conversation_summary",
                "custom_templates"
            ],
            "max_input_length": 10000,  # tokens
            "supports_batch": True
        }
    
    async def create_daily_digest(self, items: List[Dict[str, Any]]) -> AgentOutput:
        """Create a daily digest from multiple content items.
        
        Args:
            items: List of content items to include in digest
            
        Returns:
            Agent output with daily digest
        """
        # Prepare input for daily digest
        digest_input = AgentInput(
            content="",  # Content is in metadata
            context={"content_type": "daily_digest"},
            metadata={"items": items}
        )
        
        return await self.process(digest_input)
    
    async def batch_summarize(self, 
                             items: List[Dict[str, Any]], 
                             content_type: str = "article") -> List[AgentOutput]:
        """Batch summarize multiple items.
        
        Args:
            items: List of items to summarize
            content_type: Type of content for all items
            
        Returns:
            List of agent outputs
        """
        tasks = []
        
        for item in items:
            input_data = AgentInput(
                content=item.get("content", ""),
                context={"content_type": content_type},
                metadata=item.get("metadata", {})
            )
            tasks.append(self.process(input_data))
        
        return await asyncio.gather(*tasks)
    
    def add_custom_template(self, name: str, system: str, prompt: str):
        """Add a custom summarization template.
        
        Args:
            name: Template name
            system: System message
            prompt: User prompt template
        """
        self.templates[name] = {
            "system": system,
            "prompt": prompt
        }
        logger.info(f"Added custom template: {name}")
    
    async def shutdown(self) -> bool:
        """Shutdown the agent."""
        self._initialized = False
        logger.info(f"DigestAgent {self.agent_id} shutdown")
        return True


# Example usage
if __name__ == "__main__":
    async def example_usage():
        # Create DigestAgent
        agent = DigestAgent()
        
        # Initialize
        await agent.initialize()
        
        # Example 1: Summarize an article
        article_input = AgentInput(
            content="""
            Artificial Intelligence is rapidly transforming the technology landscape. 
            Recent advances in large language models have made AI more accessible to 
            developers and businesses. Companies are now integrating AI into their 
            products at an unprecedented rate. The impact extends beyond tech, 
            affecting healthcare, education, and finance sectors.
            
            However, challenges remain. Ethical considerations, data privacy, and 
            the need for regulation are ongoing concerns. The industry is working 
            to address these issues while continuing innovation.
            """,
            context={"content_type": "article"},
            metadata={
                "title": "AI Transformation in 2024",
                "source": "Tech News Daily",
                "date": "2024-05-16"
            }
        )
        
        result = await agent.process(article_input)
        print("Article Summary:", result.content.get("summary"))
        
        # Example 2: Create daily digest
        digest_items = [
            {
                "title": "AI Breakthrough",
                "type": "article",
                "source": "Research Journal",
                "content": "New AI model achieves significant performance improvements..."
            },
            {
                "title": "Market Update",
                "type": "report",
                "source": "Financial Times",
                "content": "Tech stocks surge on positive AI earnings reports..."
            }
        ]
        
        digest_result = await agent.create_daily_digest(digest_items)
        print("\nDaily Digest:", digest_result.content.get("summary"))
        
        # Shutdown
        await agent.shutdown()
    
    # Run example
    asyncio.run(example_usage())
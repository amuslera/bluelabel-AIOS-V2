from agents.base import Agent, AgentInput, AgentOutput, Tool
from core.logging import setup_logging
from typing import Dict, Any, List
import asyncio
import re

logger = setup_logging(service_name="content-mind")

class ContentMind(Agent):
    """
    Agent for processing and understanding content
    
    Capabilities:
    - Content summarization
    - Entity extraction
    - Topic identification
    - Sentiment analysis
    """
    
    def __init__(self, name: str = "ContentMind", description: str = "Content processing and analysis agent"):
        super().__init__(name, description)
        self.logger = logger
        self.initialized = False
        
    def initialize(self) -> None:
        """Initialize the ContentMind agent"""
        self.logger.info(f"{self.name} agent initializing")
        
        # Register tools
        self._register_tools()
        
        self.logger.info(f"{self.name} agent initialized with {len(self.tools)} tools")
    
    def _register_tools(self) -> None:
        """Register available tools for content processing"""
        self.register_tool(Tool(
            name="extract_summary",
            description="Extract a summary from content",
            function=self._extract_summary,
            parameters={"content": "str", "max_length": "int"}
        ))
        
        self.register_tool(Tool(
            name="extract_entities",
            description="Extract named entities from content",
            function=self._extract_entities,
            parameters={"content": "str"}
        ))
        
        self.register_tool(Tool(
            name="identify_topics",
            description="Identify main topics in content",
            function=self._identify_topics,
            parameters={"content": "str"}
        ))
        
        self.register_tool(Tool(
            name="analyze_sentiment",
            description="Analyze sentiment of content",
            function=self._analyze_sentiment,
            parameters={"content": "str"}
        ))
    
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """Process content and extract insights"""
        self.logger.info(f"Processing content from {input_data.source}")
        
        try:
            content = input_data.content.get("text", "")
            content_type = input_data.content.get("type", "text")
            
            if not content:
                raise ValueError("No content provided")
            
            # Run all analysis tasks concurrently
            tasks = [
                self._extract_summary(content, max_length=200),
                self._extract_entities(content),
                self._identify_topics(content),
                self._analyze_sentiment(content)
            ]
            
            summary, entities, topics, sentiment = await asyncio.gather(*tasks)
            
            result = {
                "content_type": content_type,
                "summary": summary,
                "entities": entities,
                "topics": topics,
                "sentiment": sentiment,
                "metadata": {
                    "source": input_data.source,
                    "processed_at": input_data.metadata.get("timestamp"),
                    "content_length": len(content)
                }
            }
            
            self.logger.info(f"Successfully processed content: {len(entities)} entities, {len(topics)} topics")
            
            return AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing content: {str(e)}")
            return AgentOutput(
                task_id=input_data.task_id,
                status="error",
                error=str(e)
            )
    
    async def _extract_summary(self, content: str, max_length: int = 200) -> str:
        """Extract a summary from content"""
        # Simulate async processing
        await asyncio.sleep(0.1)
        
        # Simple implementation - take first sentences
        sentences = re.split(r'[.!?]', content)
        summary = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(summary) + len(sentence) <= max_length:
                summary += sentence + ". "
            elif summary:
                break
        
        return summary.strip() or content[:max_length] + "..."
    
    async def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract named entities from content"""
        # Simulate async processing
        await asyncio.sleep(0.1)
        
        # Simple pattern matching for demo
        entities = []
        
        # Extract capitalized words as potential entities
        words = content.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 1:
                entity_type = "PERSON" if i == 0 or words[i-1].lower() in ["mr", "mrs", "dr"] else "ORGANIZATION"
                entities.append({
                    "text": word,
                    "type": entity_type,
                    "confidence": 0.8
                })
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, content):
            entities.append({
                "text": match.group(),
                "type": "EMAIL",
                "confidence": 0.95
            })
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        for match in re.finditer(url_pattern, content):
            entities.append({
                "text": match.group(),
                "type": "URL",
                "confidence": 0.95
            })
        
        return entities
    
    async def _identify_topics(self, content: str) -> List[str]:
        """Identify main topics in content"""
        # Simulate async processing
        await asyncio.sleep(0.1)
        
        # Simple keyword extraction for demo
        topics = []
        
        # Common topic keywords
        topic_keywords = {
            "technology": ["software", "hardware", "AI", "machine learning", "data"],
            "business": ["company", "revenue", "profit", "market", "strategy"],
            "science": ["research", "study", "experiment", "hypothesis", "theory"],
            "health": ["medical", "health", "disease", "treatment", "patient"]
        }
        
        content_lower = content.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    async def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of content"""
        # Simulate async processing
        await asyncio.sleep(0.1)
        
        # Simple sentiment analysis for demo
        positive_words = ["good", "great", "excellent", "positive", "happy", "success"]
        negative_words = ["bad", "poor", "negative", "sad", "failure", "problem"]
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(positive_count / 10, 1.0)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = min(negative_count / 10, 1.0)
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": 0.7
        }
    
    async def shutdown(self) -> None:
        """Cleanup when the agent is shut down"""
        self.logger.info(f"Shutting down {self.name} agent")
        # Add any cleanup code here
        self.tools.clear()
from agents.base import Agent, AgentInput, AgentOutput, Tool
from core.logging import setup_logging
from typing import Dict, Any, List, Optional
from services.model_router.router import ModelRouter, ProviderType
from services.model_router.base import LLMMessage, LLMProviderConfig
import asyncio
import re
import json

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
    
    def __init__(self, name: str = "ContentMind", description: str = "Content processing and analysis agent", 
                 model_router: Optional[ModelRouter] = None):
        super().__init__(name, description)
        self.logger = logger
        self.initialized = False
        self.model_router = model_router
        
    async def initialize(self) -> None:
        """Initialize the ContentMind agent"""
        self.logger.info(f"{self.name} agent initializing")
        
        # Initialize model router if not provided
        if not self.model_router:
            self.model_router = await self._create_model_router()
        
        # Register tools
        self._register_tools()
        
        self.initialized = True
        self.logger.info(f"{self.name} agent initialized with {len(self.tools)} tools")
    
    async def _create_model_router(self) -> ModelRouter:
        """Create a default model router with available providers"""
        import os
        router = ModelRouter()
        
        # Try to add available providers
        try:
            # Try Ollama first (local provider)
            from services.model_router.ollama_provider import OllamaProvider
            import httpx
            ollama_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
            
            # Check if Ollama is running
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{ollama_base}/api/tags", timeout=2.0)
                    if response.status_code == 200:
                        ollama_config = LLMProviderConfig(
                            provider_name="ollama",
                            api_key="",  # Ollama doesn't need API key
                            model_name="llama3",
                            max_tokens=1000,
                            temperature=0.7,
                            metadata={"api_base": ollama_base}
                        )
                        await router.add_provider(ProviderType.OLLAMA, ollama_config)
                        self.logger.info("Added Ollama provider to model router")
            except:
                self.logger.debug("Ollama not available")
        except Exception as e:
            self.logger.warning(f"Could not add Ollama provider: {e}")
        
        try:
            # Try Anthropic
            from services.model_router.anthropic_provider import AnthropicProvider
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key:
                anthropic_config = LLMProviderConfig(
                    provider_name="anthropic",
                    api_key=anthropic_key,
                    model_name="claude-3-haiku-20240307",
                    max_tokens=1000,
                    temperature=0.7
                )
                await router.add_provider(ProviderType.ANTHROPIC, anthropic_config)
                self.logger.info("Added Anthropic provider to model router")
        except Exception as e:
            self.logger.warning(f"Could not add Anthropic provider: {e}")
        
        try:
            # Try OpenAI
            from services.model_router.openai_provider import OpenAIProvider
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                openai_config = LLMProviderConfig(
                    provider_name="openai",
                    api_key=openai_key,
                    model_name="gpt-3.5-turbo",
                    max_tokens=1000,
                    temperature=0.7
                )
                await router.add_provider(ProviderType.OPENAI, openai_config)
                self.logger.info("Added OpenAI provider to model router")
        except Exception as e:
            self.logger.warning(f"Could not add OpenAI provider: {e}")
        
        try:
            # Try Google Gemini
            from services.model_router.google_provider import GoogleProvider
            google_key = os.getenv("GOOGLE_GENERATIVEAI_API_KEY")
            if google_key:
                google_config = LLMProviderConfig(
                    provider_name="google",
                    api_key=google_key,
                    model_name="gemini-1.5-flash",
                    max_tokens=1000,
                    temperature=0.7
                )
                await router.add_provider(ProviderType.GEMINI, google_config)
                self.logger.info("Added Google provider to model router")
        except Exception as e:
            self.logger.warning(f"Could not add Google provider: {e}")
        
        # Router will use default fallback strategy
        
        return router
    
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
        
        # Ensure agent is initialized
        if not self.initialized:
            await self.initialize()
        
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
        """Extract a summary from content using LLM"""
        try:
            # Create prompt for summarization
            messages = [
                LLMMessage(
                    role="system",
                    content="You are a content summarization expert. Create concise, informative summaries that capture the key points."
                ),
                LLMMessage(
                    role="user",
                    content=f"Please summarize the following content in {max_length} characters or less. Focus on the main ideas and key points:\n\n{content[:2000]}"
                )
            ]
            
            # Get LLM response
            response = await self.model_router.chat(messages, max_tokens=100)
            summary = response.text.strip()
            
            # Ensure summary doesn't exceed max_length
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in LLM summarization: {e}")
            # Fallback to simple method
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
        """Extract named entities from content using LLM"""
        try:
            # Create prompt for entity extraction
            messages = [
                LLMMessage(
                    role="system",
                    content="You are an entity extraction expert. Identify and extract named entities from text, categorizing them accurately."
                ),
                LLMMessage(
                    role="user",
                    content=f"""Extract all named entities from the following text. Return them as a JSON array with this format:
                    [{{
                        "text": "entity text",
                        "type": "PERSON/ORGANIZATION/LOCATION/EMAIL/URL/DATE/etc",
                        "confidence": 0.0-1.0
                    }}]
                    
                    Text: {content[:1500]}
                    
                    JSON:"""
                )
            ]
            
            # Get LLM response
            response = await self.model_router.chat(messages, max_tokens=500, temperature=0.1)
            
            # Parse the JSON response
            try:
                entities = json.loads(response.text)
                if not isinstance(entities, list):
                    entities = []
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    try:
                        entities = json.loads(json_match.group())
                    except:
                        entities = []
                else:
                    entities = []
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Error in LLM entity extraction: {e}")
            # Fallback to pattern matching
            entities = []
            
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
        """Identify main topics in content using LLM"""
        try:
            # Create prompt for topic identification
            messages = [
                LLMMessage(
                    role="system",
                    content="You are a content analysis expert. Identify the main topics and themes in text accurately."
                ),
                LLMMessage(
                    role="user",
                    content=f"""Identify the main topics in the following text. Return them as a simple JSON array of topic strings.
                    Focus on broad categories like: technology, business, science, health, politics, education, entertainment, sports, etc.
                    
                    Text: {content[:1500]}
                    
                    Topics (JSON array):"""
                )
            ]
            
            # Get LLM response
            response = await self.model_router.chat(messages, max_tokens=100, temperature=0.3)
            
            # Parse the JSON response
            try:
                topics = json.loads(response.text)
                if not isinstance(topics, list):
                    topics = []
                # Ensure all items are strings
                topics = [str(topic) for topic in topics]
            except json.JSONDecodeError:
                # Try to extract JSON array from response
                import re
                json_match = re.search(r'\[.*\]', response.text)
                if json_match:
                    try:
                        topics = json.loads(json_match.group())
                        topics = [str(topic) for topic in topics]
                    except:
                        topics = []
                else:
                    # Try to extract comma-separated topics
                    topics = [t.strip() for t in response.text.split(',') if t.strip()]
            
            return topics[:5]  # Limit to 5 topics
            
        except Exception as e:
            self.logger.error(f"Error in LLM topic identification: {e}")
            # Fallback to keyword matching
            topics = []
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
        """Analyze sentiment of content using LLM"""
        try:
            # Create prompt for sentiment analysis
            messages = [
                LLMMessage(
                    role="system",
                    content="You are a sentiment analysis expert. Analyze the emotional tone and sentiment of text accurately."
                ),
                LLMMessage(
                    role="user",
                    content=f"""Analyze the sentiment of the following text and return a JSON object with this format:
                    {{
                        "sentiment": "positive/negative/neutral/mixed",
                        "score": 0.0-1.0,
                        "confidence": 0.0-1.0,
                        "emotions": ["list", "of", "detected", "emotions"]
                    }}
                    
                    Text: {content[:1000]}
                    
                    Sentiment analysis (JSON):"""
                )
            ]
            
            # Get LLM response
            response = await self.model_router.chat(messages, max_tokens=150, temperature=0.1)
            
            # Parse the JSON response
            try:
                sentiment_data = json.loads(response.text)
                # Ensure required fields exist
                if not all(key in sentiment_data for key in ["sentiment", "score", "confidence"]):
                    raise ValueError("Missing required fields")
                return sentiment_data
            except (json.JSONDecodeError, ValueError):
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    try:
                        sentiment_data = json.loads(json_match.group())
                        return sentiment_data
                    except:
                        pass
                
                # Fallback parsing
                sentiment = "neutral"
                if "positive" in response.text.lower():
                    sentiment = "positive"
                elif "negative" in response.text.lower():
                    sentiment = "negative"
                
                return {
                    "sentiment": sentiment,
                    "score": 0.5,
                    "confidence": 0.7
                }
            
        except Exception as e:
            self.logger.error(f"Error in LLM sentiment analysis: {e}")
            # Fallback to simple analysis
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
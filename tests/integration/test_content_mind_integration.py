"""Integration test for ContentMindLLM with MCP and Model Router."""
import pytest
from datetime import datetime
import json

from agents.content_mind_llm import ContentMindLLM
from services.model_router.router import ModelRouter
from services.mcp.factory import create_prompt_manager
from agents.base import AgentInput, AgentOutput


@pytest.mark.integration
@pytest.mark.asyncio
async def test_content_mind_full_flow():
    """Test ContentMindLLM with real MCP prompts and mock router."""
    # Setup - create real MCP prompts
    prompt_manager = create_prompt_manager()
    
    # Create mock model router
    model_router = ModelRouter(config={
        "providers": {
            "mock": {
                "api_key": "mock",
                "provider_class": "mock_provider"
            }
        },
        "default_provider": "mock",
        "default_model": "mock-model"
    })
    
    # Mock the provider responses
    class MockProvider:
        async def chat(self, messages, **kwargs):
            if "summarize" in str(messages):
                return type('Response', (), {
                    'text': "This document discusses AI advancements in healthcare. Key points include improved diagnostics and personalized treatment.",
                    'metadata': {'model': 'mock', 'tokens': {'prompt': 100, 'completion': 50}}
                })()
            elif "concepts" in str(messages):
                return type('Response', (), {
                    'text': "AI, Healthcare, Diagnostics, Personalized Medicine, Machine Learning",
                    'metadata': {'model': 'mock'}
                })()
            else:
                return type('Response', (), {
                    'text': "General response",
                    'metadata': {'model': 'mock'}
                })()
        
        async def complete(self, prompt, **kwargs):
            return await self.chat([{"role": "user", "content": prompt}], **kwargs)
        
        def get_models(self):
            return [type('Model', (), {
                'name': 'mock-model',
                'type': 'chat',
                'capabilities': ['chat']
            })()]
    
    # Patch the router to use mock provider
    model_router.providers = {"mock": MockProvider()}
    
    # Create agent
    agent = ContentMindLLM(
        model_router=model_router,
        prompt_manager=prompt_manager
    )
    
    # Create test input
    test_input = AgentInput(
        metadata={
            "source": "email",
            "content_type": "text",
            "from": "investor@example.com",
            "timestamp": datetime.now()
        },
        payload={
            "content": """
            Dear Ariel,
            
            I wanted to share this fascinating article about the latest AI developments 
            in healthcare. The use of machine learning for early disease detection is 
            showing remarkable results, particularly in cancer diagnosis.
            
            Key findings:
            - 95% accuracy in early-stage cancer detection
            - Reduced false positives by 40%
            - Cost savings of $2B annually
            
            I think this could be a great investment opportunity for your fund.
            
            Best regards,
            John
            """,
            "subject": "AI Healthcare Investment Opportunity"
        }
    )
    
    # Process the input
    result = await agent.process(test_input)
    
    # Verify results
    assert result.status == "processed"
    assert "summary" in result.results
    assert "concepts" in result.results
    assert "metadata" in result.results
    
    # Check summary quality
    summary = result.results["summary"]
    assert isinstance(summary, str)
    assert len(summary) > 50
    assert "healthcare" in summary.lower() or "ai" in summary.lower()
    
    # Check concepts
    concepts = result.results["concepts"]
    assert isinstance(concepts, list)
    assert len(concepts) >= 3
    assert any("AI" in c or "Healthcare" in c for c in concepts)
    
    # Check metadata
    metadata = result.results["metadata"]
    assert "category" in metadata
    assert "timestamp" in metadata
    assert "processed_by" in metadata
    assert metadata["processed_by"] == "ContentMind LLM"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_content_mind_error_recovery():
    """Test ContentMindLLM error handling and recovery."""
    # Setup with a router that fails initially
    model_router = ModelRouter(config={
        "providers": {
            "failing": {
                "api_key": "test",
                "provider_class": "failing"
            },
            "backup": {
                "api_key": "test",
                "provider_class": "backup"
            }
        },
        "default_provider": "failing",
        "fallback_provider": "backup"
    })
    
    # Mock providers
    class FailingProvider:
        def __init__(self):
            self.call_count = 0
        
        async def chat(self, messages, **kwargs):
            self.call_count += 1
            if self.call_count <= 2:
                raise Exception("Temporary failure")
            return type('Response', (), {
                'text': "Recovery successful",
                'metadata': {'model': 'failing'}
            })()
        
        async def complete(self, prompt, **kwargs):
            return await self.chat([{"role": "user", "content": prompt}], **kwargs)
        
        def get_models(self):
            return [type('Model', (), {
                'name': 'failing-model',
                'type': 'chat',
                'capabilities': ['chat']
            })()]
    
    class BackupProvider:
        async def chat(self, messages, **kwargs):
            return type('Response', (), {
                'text': "Backup provider response: Content processed successfully",
                'metadata': {'model': 'backup'}
            })()
        
        async def complete(self, prompt, **kwargs):
            return await self.chat([{"role": "user", "content": prompt}], **kwargs)
        
        def get_models(self):
            return [type('Model', (), {
                'name': 'backup-model',
                'type': 'chat',
                'capabilities': ['chat']
            })()]
    
    failing_provider = FailingProvider()
    model_router.providers = {
        "failing": failing_provider,
        "backup": BackupProvider()
    }
    
    # Create agent with real MCP
    prompt_manager = create_prompt_manager()
    
    agent = ContentMindLLM(
        model_router=model_router,
        prompt_manager=prompt_manager
    )
    
    # Create test input
    test_input = AgentInput(
        metadata={"source": "email", "content_type": "text"},
        payload={"content": "Test content for error recovery"}
    )
    
    # Process - should recover after failures
    result = await agent.process(test_input)
    
    # Should succeed despite initial failures
    assert result.status == "processed"
    assert "summary" in result.results
    assert failing_provider.call_count >= 2  # Should have tried multiple times


@pytest.mark.integration
@pytest.mark.asyncio
async def test_content_mind_with_templates():
    """Test ContentMindLLM using custom prompt templates."""
    # Create custom templates
    prompt_manager = create_prompt_manager()
    
    # Add a custom analysis template
    from services.mcp.models import PromptTemplate, PromptComponent, PromptVariable
    
    custom_template = PromptTemplate(
        name="investor_analysis",
        description="Analyze content for investment opportunities",
        variables=[
            PromptVariable(name="content", required=True),
            PromptVariable(name="focus_areas", default="technology, healthcare, fintech")
        ],
        components=[
            PromptComponent(
                name="system",
                content="You are an expert investment analyst. Analyze the content for investment opportunities in {focus_areas}.",
                role="system"
            ),
            PromptComponent(
                name="user",
                content="Analyze this for investment potential: {content}",
                role="user"
            )
        ]
    )
    
    await prompt_manager.create_prompt("investor_analysis", custom_template)
    
    # Create mock router
    model_router = ModelRouter(config={
        "providers": {"mock": {"api_key": "test"}},
        "default_provider": "mock"
    })
    
    class MockProvider:
        async def chat(self, messages, **kwargs):
            return type('Response', (), {
                'text': "Investment opportunity identified: High growth potential in AI healthcare sector. Valuation: $50M, Expected ROI: 3x in 5 years.",
                'metadata': {'model': 'mock'}
            })()
        
        def get_models(self):
            return [type('Model', (), {'name': 'mock', 'type': 'chat', 'capabilities': ['chat']})()]
    
    model_router.providers = {"mock": MockProvider()}
    
    # Create agent
    agent = ContentMindLLM(
        model_router=model_router,
        prompt_manager=prompt_manager
    )
    
    # Process with custom template
    result = await agent.process(AgentInput(
        metadata={"source": "email", "content_type": "text"},
        payload={
            "content": "New AI startup in healthcare with innovative diagnostic platform",
            "template": "investor_analysis"
        }
    ))
    
    assert result.status == "processed"
    assert "summary" in result.results
    
    # Should detect investment-related content
    summary = result.results["summary"]
    assert "investment" in summary.lower() or "roi" in summary.lower() or "valuation" in summary.lower()
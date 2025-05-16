#!/usr/bin/env python3
"""Test the MCP (Multi-Component Prompting) framework"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services.mcp import (
    PromptManager, PromptComponent, PromptTemplate,
    PromptVariable, create_prompt_manager, initialize_default_components
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_component_creation():
    """Test creating and using a prompt component"""
    print("\n=== Testing Component Creation ===")
    
    manager = create_prompt_manager()
    
    # Create a simple component
    component = await manager.create_component(
        name="greeting_component",
        description="Generates personalized greetings",
        template="Hello {name}! Welcome to {location}. The weather is {weather} today.",
        variables=[
            {
                "name": "name",
                "description": "Person's name",
                "type": "string",
                "required": True
            },
            {
                "name": "location", 
                "description": "Location name",
                "type": "string",
                "required": True
            },
            {
                "name": "weather",
                "description": "Weather description",
                "type": "string",
                "required": False,
                "default": "nice"
            }
        ],
        created_by="test_user",
        tags=["greeting", "welcome"],
        examples=[
            {
                "name": "Alice",
                "location": "San Francisco",
                "weather": "sunny"
            }
        ]
    )
    
    print(f"✅ Created component: {component.name} (ID: {component.id})")
    
    # Test rendering
    inputs = {
        "name": "Bob",
        "location": "New York"
        # weather will use default
    }
    
    rendered = await manager.render_component(component.id, inputs)
    print(f"✅ Rendered: {rendered}")
    
    return component

async def test_component_validation():
    """Test component validation"""
    print("\n=== Testing Component Validation ===")
    
    manager = create_prompt_manager()
    
    # Try to create component with undefined variable
    try:
        await manager.create_component(
            name="invalid_component",
            description="This should fail validation",
            template="Hello {name}! Your age is {age}.",  # age not defined
            variables=[
                {
                    "name": "name",
                    "description": "Person's name",
                    "type": "string",
                    "required": True
                }
            ],
            created_by="test_user"
        )
        print("❌ Validation should have failed")
    except ValueError as e:
        print(f"✅ Validation correctly failed: {e}")

async def test_component_versioning():
    """Test component versioning"""
    print("\n=== Testing Component Versioning ===")
    
    manager = create_prompt_manager()
    
    # Create initial component
    component = await manager.create_component(
        name="versioned_component",
        description="Component to test versioning",
        template="Version 1: Hello {name}!",
        variables=[
            {
                "name": "name",
                "description": "Person's name",
                "type": "string",
                "required": True
            }
        ],
        created_by="test_user"
    )
    
    print(f"✅ Created component v{component.version}")
    
    # Update component
    updated = await manager.update_component(
        component.id,
        {
            "template": "Version 2: Greetings {name}!",
            "description": "Updated greeting component"
        },
        updated_by="test_user"
    )
    
    print(f"✅ Updated to v{updated.version}")
    
    # Get version history
    versions = await manager.get_component_versions(component.id)
    print(f"✅ Version history: {len(versions)} versions")
    for v in versions:
        print(f"   - v{v['version']} by {v['created_by']}")

async def test_template_creation():
    """Test template creation with multiple components"""
    print("\n=== Testing Template Creation ===")
    
    manager = create_prompt_manager()
    
    # Create components
    intro = await manager.create_component(
        name="intro_component",
        description="Introduction section",
        template="Welcome to our newsletter about {topic}!",
        variables=[
            {
                "name": "topic",
                "description": "Newsletter topic",
                "type": "string",
                "required": True
            }
        ],
        created_by="test_user"
    )
    
    content = await manager.create_component(
        name="content_component",
        description="Main content section",
        template="Today we'll discuss:\n{points}",
        variables=[
            {
                "name": "points",
                "description": "Discussion points",
                "type": "array",
                "required": True
            }
        ],
        created_by="test_user"
    )
    
    outro = await manager.create_component(
        name="outro_component",
        description="Closing section",
        template="Thanks for reading! See you {next_time}.",
        variables=[
            {
                "name": "next_time",
                "description": "Next newsletter date",
                "type": "string",
                "required": False,
                "default": "next week"
            }
        ],
        created_by="test_user"
    )
    
    # Create template
    template = await manager.create_template(
        name="newsletter_template",
        description="Complete newsletter template",
        component_ids=[intro.id, content.id, outro.id],
        created_by="test_user",
        layout="""Newsletter: {title}

{component:""" + intro.id + """}

{component:""" + content.id + """}

{component:""" + outro.id + """}

---
Generated on: {date}""",
        variables=[
            {
                "name": "title",
                "description": "Newsletter title",
                "type": "string",
                "required": True
            },
            {
                "name": "date",
                "description": "Generation date",
                "type": "string",
                "required": True
            }
        ]
    )
    
    print(f"✅ Created template: {template.name}")
    
    # Render template
    inputs = {
        "title": "AI Weekly",
        "topic": "Large Language Models",
        "points": ["GPT-4 updates", "Open source alternatives", "Fine-tuning techniques"],
        "next_time": "next Monday",
        "date": "2024-01-15"
    }
    
    rendered = await manager.render_template(template.id, inputs)
    print(f"\n✅ Rendered template:\n{rendered}")
    
    return template

async def test_default_components():
    """Test default components initialization"""
    print("\n=== Testing Default Components ===")
    
    manager = create_prompt_manager()
    
    # Initialize defaults
    await initialize_default_components(manager)
    
    # List components
    components = await manager.list_components()
    print(f"✅ Found {len(components)} components:")
    for comp in components:
        print(f"   - {comp.name}: {comp.description}")
    
    # Test content summarizer
    components_by_name = {c.name: c for c in components}
    summarizer = components_by_name.get("content_summarizer")
    
    if summarizer:
        inputs = {
            "content": """Artificial Intelligence (AI) has revolutionized many industries. 
            Machine learning models can now understand natural language, recognize images, 
            and even generate creative content. The impact of AI continues to grow as 
            technology advances and more applications are discovered.""",
            "num_points": 3
        }
        
        rendered = await manager.render_component(summarizer.id, inputs)
        print(f"\n✅ Content summarizer output:\n{rendered}")

async def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    manager = create_prompt_manager()
    
    # Try to render non-existent component
    try:
        await manager.render_component("non-existent-id", {"test": "value"})
        print("❌ Should have raised error")
    except ValueError as e:
        print(f"✅ Correctly raised error: {e}")
    
    # Try to render with missing required inputs
    component = await manager.create_component(
        name="test_component",
        description="Test component",
        template="Hello {required_field}!",
        variables=[
            {
                "name": "required_field",
                "description": "Required field",
                "type": "string",
                "required": True
            }
        ],
        created_by="test_user"
    )
    
    try:
        await manager.render_component(component.id, {})
        print("❌ Should have raised error for missing required field")
    except ValueError as e:
        print(f"✅ Correctly raised error: {e}")

async def main():
    """Run all tests"""
    print("MCP Framework Test Suite")
    print("=" * 50)
    
    tests = [
        ("Component Creation", test_component_creation),
        ("Component Validation", test_component_validation),
        ("Component Versioning", test_component_versioning),
        ("Template Creation", test_template_creation),
        ("Default Components", test_default_components),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            await test_func()
            results.append((test_name, True))
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
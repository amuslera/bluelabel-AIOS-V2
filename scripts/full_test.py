#!/usr/bin/env python3
"""Comprehensive test of the current implementation status"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Test that all basic modules can be imported"""
    print("Testing module imports...")
    
    modules = [
        ("FastAPI app", "apps.api.main"),
        ("Event Bus", "core.event_bus"),
        ("Event Patterns", "core.event_patterns"),
        ("Config", "core.config"),
        ("Agents Base", "agents.base"),
        ("ContentMind Agent", "agents.content_mind"),
        ("Agent Registry", "agents.registry"),
        ("Gateway Router", "apps.api.routers.gateway"),
        ("Agents Router", "apps.api.routers.agents"),
        ("Knowledge Router", "apps.api.routers.knowledge"),
    ]
    
    failed = []
    for name, module in modules:
        try:
            __import__(module)
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ {name}: {e}")
            failed.append(name)
    
    return len(failed) == 0

def test_event_bus():
    """Test event bus functionality in simulation mode"""
    print("\nTesting Event Bus...")
    
    from core.event_bus import EventBus
    from core.event_patterns import Message
    
    try:
        # Create event bus in simulation mode
        bus = EventBus(simulation_mode=True)
        print("✓ Event bus created in simulation mode")
        
        # Test publishing a message
        message = Message(
            type="test",
            source="test_script",
            payload={"test": "data"}
        )
        
        result = bus.publish("test_stream", message)
        print(f"✓ Published message with ID: {result}")
        
        # Check metrics
        metrics = bus.get_metrics()
        print(f"✓ Metrics: {metrics}")
        
        return True
    except Exception as e:
        print(f"✗ Event bus test failed: {e}")
        return False

def test_existing_functionality():
    """Test what's already implemented"""
    print("\nTesting existing functionality...")
    
    tests = []
    
    # Test agent base class
    try:
        from agents.base import Agent, AgentInput, AgentOutput
        print("✓ Agent base classes available")
        tests.append(True)
    except Exception as e:
        print(f"✗ Agent base classes: {e}")
        tests.append(False)
    
    # Test ContentMind agent
    try:
        from agents.content_mind import ContentMind
        print("✓ ContentMind agent available")
        tests.append(True)
    except Exception as e:
        print(f"✗ ContentMind agent: {e}")
        tests.append(False)
    
    # Test agent registry
    try:
        from agents.registry import AgentRegistry
        registry = AgentRegistry()
        print("✓ Agent registry initialized")
        tests.append(True)
    except Exception as e:
        print(f"✗ Agent registry: {e}")
        tests.append(False)
    
    return all(tests)

def main():
    """Run all tests"""
    print("=" * 50)
    print("Bluelabel AIOS v2 - Implementation Status Test")
    print("=" * 50)
    
    results = []
    
    # Test imports
    results.append(("Module Imports", test_imports()))
    
    # Test event bus
    results.append(("Event Bus", test_event_bus()))
    
    # Test existing functionality
    results.append(("Existing Functionality", test_existing_functionality()))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Recommendations
    print("\n" + "=" * 50)
    print("Current Status & Recommendations")
    print("=" * 50)
    
    print("\nIMPLEMENTED:")
    print("- Basic FastAPI structure")
    print("- Event Bus with simulation mode")
    print("- Basic agent structure")
    print("- API routers (gateway, agents, knowledge)")
    print("- Basic configuration")
    
    print("\nNEXT STEPS:")
    print("1. Complete Agent Runtime Manager")
    print("2. Complete Basic API Service endpoints")
    print("3. Fix dependency issues")
    print("4. Implement Email Gateway with OAuth")
    print("5. Implement WhatsApp Gateway")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
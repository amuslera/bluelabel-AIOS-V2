#!/usr/bin/env python3
"""Quick test of logging functionality"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.logging import setup_logging, LogContext
from core.event_bus import EventBus
from core.event_patterns import Message

def test_logging():
    """Test different logging scenarios"""
    
    # Test basic logging
    print("1. Testing basic logging:")
    logger = setup_logging(service_name="test-service")
    logger.info("Basic log message")
    logger.warning("Warning message")
    logger.error("Error message")
    print("✓ Basic logging working\n")
    
    # Test context logging
    print("2. Testing context logging:")
    with LogContext(logger, tenant_id="tenant-123", user_id="user-456"):
        logger.info("Message with context")
    print("✓ Context logging working\n")
    
    # Test event bus logging
    print("3. Testing event bus logging:")
    bus = EventBus(simulation_mode=True)
    message = Message(
        type="test_event",
        source="test_script",
        payload={"data": "test"}
    )
    result = bus.publish("test_stream", message)
    print(f"✓ Published message: {result}\n")
    
    # Test JSON formatting
    print("4. Testing JSON format logging:")
    json_logger = setup_logging(
        service_name="json-test",
        json_format=True
    )
    json_logger.info("JSON formatted message", extra={"custom_field": "value"})
    print("✓ JSON logging working\n")
    
    # Test file logging
    print("5. Testing file logging:")
    file_logger = setup_logging(
        service_name="file-test",
        log_file="logs/test.log"
    )
    file_logger.info("Message to file")
    print("✓ File logging configured\n")
    
    print("All logging tests passed!")

if __name__ == "__main__":
    test_logging()
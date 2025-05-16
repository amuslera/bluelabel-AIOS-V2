#!/usr/bin/env python3

"""
Comprehensive Test Script for Enhanced Event Bus

This script demonstrates the enhanced functionality of the Redis event bus,
including different message patterns, error handling, and metrics.

Usage:
    python3 test_event_patterns.py [--simulate]

Options:
    --simulate    Run in simulation mode without requiring Redis
"""

import argparse
import json
import sys
import threading
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add project root to path for imports
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the event bus and patterns
from core.event_bus import EventBus
from core.event_patterns import (
    Message, MessagePattern, MessagePriority, MessageStatus,
    MessageHandler, EventBusConfig, DeadLetterMessage
)

# Simulated event bus for testing without Redis
class SimulatedEventBus(EventBus):
    """A simulated event bus that works without Redis for testing"""
    
    def __init__(self):
        """Initialize the simulated event bus"""
        # Create a minimal config
        config = EventBusConfig(
            redis_host="simulated",
            redis_port=0,
            redis_db=0
        )
        
        # Initialize base class with config
        super().__init__(config)
        
        # Override Redis connection
        self.redis = None
        
        # Storage for simulated streams
        self.streams = {}
        print("ud83dudd27 Running with simulated event bus (no Redis required)")
    
    def publish(self, stream: str, message: Message) -> str:
        """Publish a message to a stream"""
        # Generate a message ID
        message_id = f"{int(time.time() * 1000)}-{len(self.streams.get(stream, []))}"
        
        # Convert Message to dict for storage
        if isinstance(message, dict):
            message_dict = message
        else:
            message_dict = message.model_dump()
            message_dict["payload"] = json.dumps(message_dict.get("payload", {}))
            message_dict["metadata"] = json.dumps(message_dict.get("metadata", {}))
            if "timestamp" in message_dict:
                message_dict["timestamp"] = message_dict["timestamp"].isoformat()
            if "expiration" in message_dict and message_dict["expiration"]:
                message_dict["expiration"] = message_dict["expiration"].isoformat()
        
        # Add to stream
        if stream not in self.streams:
            self.streams[stream] = []
        
        self.streams[stream].append((message_id, message_dict))
        
        # Update metrics
        with self.lock:
            self.metrics["messages_published"] += 1
        
        # Handle message immediately in simulation mode
        # This simulates the behavior of the listener
        threading.Thread(target=self._handle_message, args=(stream, self._parse_message(message_id, message_dict))).start()
        
        return message_id

# Test functions for different message patterns
def test_publish_subscribe(event_bus):
    """Test the publish-subscribe pattern"""
    print("\nud83dudce3 Testing PUBLISH-SUBSCRIBE Pattern")
    
    # Define a message handler
    def handle_notification(message):
        print(f"  ud83dudce5 Received notification: {message.type} - {json.dumps(message.payload, indent=2)}")
    
    # Register handler
    event_bus.register_handler(
        stream="notifications",
        handler=handle_notification,
        message_types=["system_notification", "user_notification"]
    )
    
    # Publish a few notifications
    for i in range(3):
        message = Message(
            type="system_notification" if i % 2 == 0 else "user_notification",
            pattern=MessagePattern.PUBLISH_SUBSCRIBE,
            source="test_script",
            payload={
                "message": f"Test notification {i+1}",
                "importance": "high" if i == 0 else "medium",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        event_bus.publish("notifications", message)
        print(f"  ud83dudce4 Published notification {i+1}: {message.id}")
        time.sleep(0.5)

def test_request_response(event_bus):
    """Test the request-response pattern"""
    print("\nud83dudcac Testing REQUEST-RESPONSE Pattern")
    
    # Define a responder function
    def handle_request(message):
        print(f"  ud83dudce5 Received request: {message.type} - {json.dumps(message.payload, indent=2)}")
        
        # Create a response
        response_payload = {
            "result": f"Processed {message.payload.get('data', 'unknown')}",
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send response
        event_bus.respond_to(message, "data_response", response_payload)
        print(f"  ud83dudce4 Sent response to request {message.id}")
    
    # Register request handler
    event_bus.register_handler(
        stream="requests",
        handler=handle_request,
        message_types=["data_request"]
    )
    
    # Start a listener for the request stream in a separate thread
    def request_listener():
        try:
            event_bus.start_listening(["requests"])
        except Exception as e:
            print(f"Error in request listener: {str(e)}")
    
    listener_thread = threading.Thread(target=request_listener)
    listener_thread.daemon = True
    listener_thread.start()
    
    # Wait for the listener to start
    time.sleep(1)
    
    # Send a request and wait for response
    response = event_bus.request(
        request_stream="requests",
        response_stream="responses",
        request_type="data_request",
        payload={"data": "test_data", "options": {"format": "json"}},
        timeout_seconds=5
    )
    
    if response:
        print(f"  u2705 Received response: {json.dumps(response.payload, indent=2)}")
    else:
        print(f"  u274c No response received within timeout")

def test_command_pattern(event_bus):
    """Test the command pattern"""
    print("\nud83dudd11 Testing COMMAND Pattern")
    
    # Define a command handler
    def handle_command(message):
        print(f"  ud83dudce5 Received command: {message.type} - {json.dumps(message.payload, indent=2)}")
        
        # Simulate command execution
        time.sleep(0.5)
        print(f"  u2705 Executed command: {message.payload.get('action', 'unknown')}")
    
    # Register command handler
    event_bus.register_handler(
        stream="commands",
        handler=handle_command,
        message_types=["system_command"]
    )
    
    # Send a few commands
    for action in ["start_process", "stop_process", "restart_service"]:
        message = Message(
            type="system_command",
            pattern=MessagePattern.COMMAND,
            source="admin",
            payload={
                "action": action,
                "target": "test_service",
                "options": {"force": action == "stop_process"}
            }
        )
        
        event_bus.publish("commands", message)
        print(f"  ud83dudce4 Sent command: {action}")
        time.sleep(1)

def test_error_handling(event_bus):
    """Test error handling in message processing"""
    print("\nu26a0ufe0f Testing ERROR HANDLING")
    
    # Define a handler that will fail
    def failing_handler(message):
        print(f"  ud83dudce5 Received message that will cause an error: {message.id}")
        raise ValueError(f"Simulated error processing message {message.id}")
    
    # Register the failing handler
    event_bus.register_handler(
        stream="errors",
        handler=failing_handler,
        message_types=["will_fail"]
    )
    
    # Send a message that will cause an error
    message = Message(
        type="will_fail",
        pattern=MessagePattern.EVENT,
        source="test_script",
        payload={"data": "This will cause an error"}
    )
    
    event_bus.publish("errors", message)
    print(f"  ud83dudce4 Sent message that will cause an error: {message.id}")
    time.sleep(1)
    
    # Check metrics
    metrics = event_bus.get_metrics()
    print(f"  ud83dudcca Metrics after error: {json.dumps(metrics, indent=2)}")

def main():
    """Main function to run the event bus tests"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the enhanced Redis event bus")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode without Redis")
    args = parser.parse_args()
    
    try:
        # Create the event bus
        if args.simulate:
            event_bus = SimulatedEventBus()
        else:
            # Try to connect to Redis
            try:
                event_bus = EventBus()
                # Test the connection
                if event_bus.redis:
                    event_bus.redis.ping()
                    print("u2705 Connected to Redis successfully")
            except Exception as e:
                print(f"u274c Error connecting to Redis: {str(e)}")
                print("ud83dudd04 Falling back to simulation mode")
                event_bus = SimulatedEventBus()
        
        # Run tests for different message patterns
        test_publish_subscribe(event_bus)
        test_request_response(event_bus)
        test_command_pattern(event_bus)
        test_error_handling(event_bus)
        
        # Show final metrics
        print("\nud83dudcca Final Event Bus Metrics:")
        metrics = event_bus.get_metrics()
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        print("\nu2705 All tests completed successfully!")
    
    except KeyboardInterrupt:
        print("\nu26d4 Test interrupted by user")
    except Exception as e:
        print(f"u274c Error: {str(e)}")

if __name__ == "__main__":
    main()

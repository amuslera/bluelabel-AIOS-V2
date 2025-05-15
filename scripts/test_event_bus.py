#!/usr/bin/env python

"""
Test script for the Redis Event Bus

This script demonstrates the functionality of the Redis event bus by creating
a simple producer and consumer that exchange messages. It can work with a real
Redis server if available, or fall back to a simulated mode for testing.

Usage:
    python test_event_bus.py [--simulate]

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

# Add project root to path for imports
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the event bus
from core.event_bus import EventBus

# Simulated event bus for testing without Redis
class SimulatedEventBus:
    """A simulated event bus that works without Redis for testing"""
    
    def __init__(self):
        """Initialize the simulated event bus"""
        self.streams = {}
        self.subscribers = {}
        self.lock = threading.Lock()
        print("🔧 Running with simulated event bus (no Redis required)")
    
    def publish(self, stream: str, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event to a stream"""
        event_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        
        # Create event payload
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": str(timestamp),
            "data": json.dumps(data)
        }
        
        # Add to stream
        with self.lock:
            if stream not in self.streams:
                self.streams[stream] = []
            
            self.streams[stream].append((event_id, event))
            
            # Notify subscribers
            if stream in self.subscribers:
                for callback in self.subscribers[stream]:
                    threading.Thread(target=callback, args=(event_type, data)).start()
        
        return event_id
    
    def subscribe(self, stream: str, callback):
        """Subscribe to a stream"""
        with self.lock:
            if stream not in self.subscribers:
                self.subscribers[stream] = []
            
            self.subscribers[stream].append(callback)
    
    def start_listening(self, streams: List[str], batch_size: int = 10, block_ms: int = 5000):
        """Start listening for events (simulation mode just waits)"""
        print(f"🔄 Listening to streams: {', '.join(streams)}")
        while True:
            time.sleep(1)

# Test producer function
def test_producer(event_bus, num_messages=5, delay=1):
    """Produce test messages to the event bus"""
    stream = "test.events"
    
    for i in range(num_messages):
        # Create a test message
        message_data = {
            "message_number": i + 1,
            "content": f"Test message {i + 1}",
            "timestamp": time.time()
        }
        
        # Publish to the event bus
        event_id = event_bus.publish(
            stream=stream,
            event_type="test_message",
            data=message_data
        )
        
        print(f"📤 Published message {i + 1} with ID: {event_id}")
        
        # Wait before sending the next message
        time.sleep(delay)
    
    # Send a special termination message
    event_bus.publish(
        stream=stream,
        event_type="test_complete",
        data={"final": True}
    )
    
    print("✅ Producer completed")

# Test consumer function
def message_handler(event_type, data):
    """Handle received messages"""
    if event_type == "test_complete":
        print("🏁 Received test completion signal")
        return
    
    print(f"📥 Received {event_type}: {json.dumps(data, indent=2)}")

def main():
    """Main function to run the event bus test"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test the Redis event bus")
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
                event_bus.redis.ping()
                print("✅ Connected to Redis successfully")
            except Exception as e:
                print(f"❌ Error connecting to Redis: {str(e)}")
                print("🔄 Falling back to simulation mode")
                event_bus = SimulatedEventBus()
        
        # Subscribe to test events
        event_bus.subscribe("test.events", message_handler)
        print("✅ Subscribed to test events")
        
        # Start the producer in a separate thread
        producer_thread = threading.Thread(
            target=test_producer,
            args=(event_bus, 5, 1)
        )
        producer_thread.daemon = True
        producer_thread.start()
        
        # Start listening for events (this will block)
        print("🔄 Starting event listener...")
        event_bus.start_listening(["test.events"])
    
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()

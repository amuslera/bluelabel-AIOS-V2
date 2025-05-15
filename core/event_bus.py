import json
import redis
from typing import Dict, Any, List, Callable, Optional
import uuid
import time
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class EventBus:
    """Redis Streams-based event bus for asynchronous communication"""
    
    def __init__(self):
        """Initialize the event bus with Redis connection"""
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = int(os.getenv("REDIS_DB", 0))
        
        self.redis = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            decode_responses=True
        )
        
        # Map of stream names to callback functions
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def publish(self, stream: str, event_type: str, data: Dict[str, Any]) -> str:
        """Publish an event to a stream
        
        Args:
            stream: The name of the stream
            event_type: The type of event
            data: The event data
            
        Returns:
            The ID of the published event
        """
        event_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        
        # Create event payload
        event = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": str(timestamp),
            "data": json.dumps(data)
        }
        
        # Publish to Redis Stream
        self.redis.xadd(stream, event)
        
        return event_id
    
    def subscribe(self, stream: str, callback: Callable) -> None:
        """Subscribe to a stream
        
        Args:
            stream: The name of the stream
            callback: Function to call when an event is received
        """
        if stream not in self.subscribers:
            self.subscribers[stream] = []
        
        self.subscribers[stream].append(callback)
    
    def start_listening(self, streams: List[str], batch_size: int = 10, block_ms: int = 5000) -> None:
        """Start listening for events on the specified streams
        
        Args:
            streams: List of stream names to listen to
            batch_size: Maximum number of events to process at once
            block_ms: Time to block waiting for events (milliseconds)
        """
        # Create a dict of stream names to last processed IDs
        stream_ids = {stream: '0-0' for stream in streams}
        
        while True:
            try:
                # Read new messages from streams
                response = self.redis.xread(stream_ids, count=batch_size, block=block_ms)
                
                for stream_name, messages in response:
                    for message_id, data in messages:
                        # Update last processed ID
                        stream_ids[stream_name] = message_id
                        
                        # Parse event data
                        event_data = json.loads(data.get('data', '{}'))
                        event_type = data.get('event_type')
                        
                        # Call subscribers
                        if stream_name in self.subscribers:
                            for callback in self.subscribers[stream_name]:
                                callback(event_type, event_data)
            
            except Exception as e:
                print(f"Error processing events: {str(e)}")
                time.sleep(1)  # Avoid tight loop on error
    
    def create_consumer_group(self, stream: str, group_name: str) -> None:
        """Create a consumer group for a stream
        
        Args:
            stream: The name of the stream
            group_name: The name of the consumer group
        """
        try:
            # Create the stream if it doesn't exist
            self.redis.xgroup_create(stream, group_name, id='0-0', mkstream=True)
        except redis.exceptions.ResponseError as e:
            # Group already exists
            if 'BUSYGROUP' not in str(e):
                raise
    
    def process_group_events(self, stream: str, group_name: str, consumer_name: str, 
                            callback: Callable, batch_size: int = 10, block_ms: int = 5000) -> None:
        """Process events for a consumer group
        
        Args:
            stream: The name of the stream
            group_name: The name of the consumer group
            consumer_name: The name of this consumer
            callback: Function to call for each event
            batch_size: Maximum number of events to process at once
            block_ms: Time to block waiting for events (milliseconds)
        """
        while True:
            try:
                # Read new messages from the consumer group
                response = self.redis.xreadgroup(
                    group_name, 
                    consumer_name, 
                    {stream: '>'}, 
                    count=batch_size, 
                    block=block_ms
                )
                
                if not response:
                    continue
                
                for stream_name, messages in response:
                    for message_id, data in messages:
                        try:
                            # Parse event data
                            event_data = json.loads(data.get('data', '{}'))
                            event_type = data.get('event_type')
                            
                            # Process the event
                            callback(event_type, event_data)
                            
                            # Acknowledge the message
                            self.redis.xack(stream_name, group_name, message_id)
                        
                        except Exception as e:
                            print(f"Error processing message {message_id}: {str(e)}")
            
            except Exception as e:
                print(f"Error in consumer group processing: {str(e)}")
                time.sleep(1)  # Avoid tight loop on error

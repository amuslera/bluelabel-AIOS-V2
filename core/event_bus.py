import json
import redis
import threading
import logging
import time
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional, Union, Tuple
from dotenv import load_dotenv

# Import message patterns
from core.event_patterns import (
    Message, MessagePattern, MessagePriority, MessageStatus,
    MessageHandler, EventBusConfig, DeadLetterMessage
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('event_bus')

class EventBus:
    """Redis Streams-based event bus for asynchronous communication
    
    This class provides a robust implementation of an event bus using Redis Streams.
    It supports various message exchange patterns, error handling, and metrics.
    """
    
    def __init__(self, config: Optional[EventBusConfig] = None):
        """Initialize the event bus with Redis connection
        
        Args:
            config: Optional configuration for the event bus
        """
        # Use provided config or create default
        self.config = config or EventBusConfig(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            redis_db=int(os.getenv("REDIS_DB", 0)),
            redis_password=os.getenv("REDIS_PASSWORD")
        )
        
        # Initialize Redis connection
        try:
            self.redis = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True
            )
            logger.info(f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
        
        # Map of stream names to message handlers
        self.handlers: Dict[str, List[MessageHandler]] = {}
        
        # Map of correlation IDs to response futures for request-response pattern
        self.response_futures: Dict[str, threading.Event] = {}
        self.responses: Dict[str, Message] = {}
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Metrics
        self.metrics = {
            "messages_published": 0,
            "messages_consumed": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "dead_letter_count": 0
        }
        
        # Create dead letter stream if enabled
        if self.config.dead_letter_stream:
            try:
                self.redis.xgroup_create(
                    self.config.dead_letter_stream,
                    self.config.consumer_group_prefix + "dead_letter",
                    id="0-0",
                    mkstream=True
                )
                logger.info(f"Created dead letter stream: {self.config.dead_letter_stream}")
            except redis.exceptions.ResponseError as e:
                # Group already exists
                if "BUSYGROUP" not in str(e):
                    logger.warning(f"Error creating dead letter stream: {str(e)}")
    
    def publish(self, stream: str, message: Union[Message, Dict[str, Any]]) -> str:
        """Publish a message to a stream
        
        Args:
            stream: The name of the stream
            message: The message to publish (either a Message object or a dict)
            
        Returns:
            The ID of the published message
        """
        # Convert dict to Message if needed
        if isinstance(message, dict):
            if "type" not in message:
                raise ValueError("Message dict must contain 'type' field")
            
            message = Message(
                type=message["type"],
                source=message.get("source", "unknown"),
                payload=message.get("payload", {}),
                metadata=message.get("metadata", {})
            )
        
        # Convert Message to Redis format
        message_dict = {
            "id": message.id,
            "type": message.type,
            "pattern": message.pattern,
            "source": message.source,
            "timestamp": message.timestamp.isoformat(),
            "payload": json.dumps(message.payload),
            "metadata": json.dumps(message.metadata)
        }
        
        # Add optional fields if present
        if message.destination:
            message_dict["destination"] = message.destination
        
        if message.correlation_id:
            message_dict["correlation_id"] = message.correlation_id
        
        if message.reply_to:
            message_dict["reply_to"] = message.reply_to
        
        if message.expiration:
            message_dict["expiration"] = message.expiration.isoformat()
        
        # Publish to Redis Stream
        try:
            # Use maxlen if configured
            result = self.redis.xadd(
                stream, 
                message_dict,
                maxlen=self.config.default_stream_max_len
            )
            
            # Update metrics
            with self.lock:
                self.metrics["messages_published"] += 1
            
            logger.debug(f"Published message {message.id} to stream {stream}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error publishing message to stream {stream}: {str(e)}")
            raise
    
    def publish_event(self, stream: str, event_type: str, data: Dict[str, Any], 
                     source: str = "system", metadata: Dict[str, Any] = None) -> str:
        """Publish an event to a stream (simplified API for backward compatibility)
        
        Args:
            stream: The name of the stream
            event_type: The type of event
            data: The event data
            source: The source of the event
            metadata: Optional metadata
            
        Returns:
            The ID of the published event
        """
        # Create a Message object
        message = Message(
            type=event_type,
            pattern=MessagePattern.EVENT,
            source=source,
            payload=data,
            metadata=metadata or {}
        )
        
        # Publish the message
        return self.publish(stream, message)
    
    def register_handler(self, stream: str, handler: Union[MessageHandler, Callable], message_types: List[str] = None) -> str:
        """Register a handler for messages on a stream
        
        Args:
            stream: The name of the stream
            handler: Either a MessageHandler object or a callback function
            message_types: List of message types to handle (only used if handler is a function)
            
        Returns:
            The ID of the registered handler
        """
        # Convert function to MessageHandler if needed
        if not isinstance(handler, MessageHandler):
            if not message_types:
                raise ValueError("message_types must be provided when registering a function handler")
                
            handler = MessageHandler(
                name=f"handler_{str(uuid.uuid4())[:8]}",
                message_types=message_types,
                function=handler
            )
        
        # Add to handlers
        with self.lock:
            if stream not in self.handlers:
                self.handlers[stream] = []
            
            self.handlers[stream].append(handler)
        
        logger.info(f"Registered handler {handler.name} for stream {stream} with types {handler.message_types}")
        return handler.id
    
    def subscribe(self, stream: str, callback: Callable) -> None:
        """Subscribe to a stream (legacy method for backward compatibility)
        
        Args:
            stream: The name of the stream
            callback: Function to call when an event is received
        """
        # Register a handler that accepts all message types
        self.register_handler(stream, callback, message_types=["*"])
    
    def _parse_message(self, message_id: str, data: Dict[str, str]) -> Message:
        """Parse a Redis message into a Message object
        
        Args:
            message_id: The Redis message ID
            data: The message data from Redis
            
        Returns:
            A Message object
        """
        try:
            # Parse basic fields
            message_dict = {
                "id": data.get("id", str(uuid.uuid4())),
                "type": data.get("type"),
                "pattern": data.get("pattern", MessagePattern.EVENT),
                "source": data.get("source", "unknown"),
            }
            
            # Add optional fields if present
            if "destination" in data:
                message_dict["destination"] = data["destination"]
                
            if "correlation_id" in data:
                message_dict["correlation_id"] = data["correlation_id"]
                
            if "reply_to" in data:
                message_dict["reply_to"] = data["reply_to"]
            
            # Parse timestamp
            if "timestamp" in data:
                try:
                    message_dict["timestamp"] = datetime.fromisoformat(data["timestamp"])
                except ValueError:
                    # Fall back to current time if parsing fails
                    message_dict["timestamp"] = datetime.now()
            
            # Parse expiration
            if "expiration" in data:
                try:
                    message_dict["expiration"] = datetime.fromisoformat(data["expiration"])
                except ValueError:
                    pass
            
            # Parse payload and metadata
            if "payload" in data:
                try:
                    message_dict["payload"] = json.loads(data["payload"])
                except json.JSONDecodeError:
                    message_dict["payload"] = {"raw": data["payload"]}
            
            if "metadata" in data:
                try:
                    message_dict["metadata"] = json.loads(data["metadata"])
                except json.JSONDecodeError:
                    message_dict["metadata"] = {}
            
            # Add Redis message ID to metadata
            if "metadata" not in message_dict:
                message_dict["metadata"] = {}
            
            message_dict["metadata"]["redis_message_id"] = message_id
            
            # Create Message object
            return Message(**message_dict)
        
        except Exception as e:
            logger.error(f"Error parsing message {message_id}: {str(e)}")
            # Create a minimal valid message
            return Message(
                id=str(uuid.uuid4()),
                type="unknown",
                source="error",
                metadata={"error": str(e), "original_data": data, "redis_message_id": message_id}
            )
    
    def _handle_message(self, stream: str, message: Message) -> None:
        """Handle a received message
        
        Args:
            stream: The stream the message was received from
            message: The message to handle
        """
        # Check for response to a request
        if message.pattern == MessagePattern.REQUEST_RESPONSE and message.correlation_id in self.response_futures:
            with self.lock:
                # Store the response
                self.responses[message.correlation_id] = message
                # Signal that the response is ready
                self.response_futures[message.correlation_id].set()
            return
        
        # Check for handlers
        if stream in self.handlers:
            handled = False
            
            for handler in self.handlers[stream]:
                # Check if handler accepts this message type
                if "*" in handler.message_types or message.type in handler.message_types:
                    # Check filter expression if present
                    if handler.filter_expression:
                        try:
                            # Create context for evaluation
                            context = {
                                "message": message.model_dump(),
                                "payload": message.payload,
                                "metadata": message.metadata
                            }
                            
                            # Evaluate filter expression
                            if not eval(handler.filter_expression, {"__builtins__": {}}, context):
                                continue
                        
                        except Exception as e:
                            logger.error(f"Error evaluating filter expression: {str(e)}")
                            continue
                    
                    # Call handler
                    try:
                        # For backward compatibility, check function signature
                        import inspect
                        sig = inspect.signature(handler.function)
                        
                        if len(sig.parameters) == 2:
                            # Legacy handler: (event_type, data)
                            handler.function(message.type, message.payload)
                        else:
                            # New handler: (message)
                            handler.function(message)
                        
                        handled = True
                    
                    except Exception as e:
                        logger.error(f"Error in message handler {handler.name}: {str(e)}")
            
            if not handled:
                logger.warning(f"No handler processed message {message.id} of type {message.type}")
    
    def start_listening(self, streams: List[str], batch_size: int = None, block_ms: int = None) -> None:
        """Start listening for messages on the specified streams
        
        Args:
            streams: List of stream names to listen to
            batch_size: Maximum number of messages to process at once (default from config)
            block_ms: Time to block waiting for messages in milliseconds (default from config)
        """
        # Use defaults from config if not specified
        batch_size = batch_size or self.config.default_batch_size
        block_ms = block_ms or self.config.default_block_ms
        
        # Create a dict of stream names to last processed IDs
        stream_ids = {stream: '0-0' for stream in streams}
        
        logger.info(f"Starting to listen on streams: {', '.join(streams)}")
        
        while True:
            try:
                # Read new messages from streams
                response = self.redis.xread(stream_ids, count=batch_size, block=block_ms)
                
                if not response:
                    continue
                
                for stream_name, messages in response:
                    for message_id, data in messages:
                        # Update last processed ID
                        stream_ids[stream_name] = message_id
                        
                        # Parse message
                        message = self._parse_message(message_id, data)
                        
                        # Update metrics
                        with self.lock:
                            self.metrics["messages_consumed"] += 1
                        
                        # Handle message
                        self._handle_message(stream_name, message)
            
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {str(e)}")
                time.sleep(5)  # Wait before reconnecting
            
            except Exception as e:
                logger.error(f"Error processing messages: {str(e)}")
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
            logger.info(f"Created consumer group {group_name} for stream {stream}")
        except redis.exceptions.ResponseError as e:
            # Group already exists
            if 'BUSYGROUP' not in str(e):
                logger.error(f"Error creating consumer group: {str(e)}")
                raise
    
    def process_group_events(self, stream: str, group_name: str, consumer_name: str, 
                           batch_size: int = None, block_ms: int = None) -> None:
        """Process messages for a consumer group
        
        Args:
            stream: The name of the stream
            group_name: The name of the consumer group
            consumer_name: The name of this consumer
            batch_size: Maximum number of messages to process at once (default from config)
            block_ms: Time to block waiting for messages in milliseconds (default from config)
        """
        # Use defaults from config if not specified
        batch_size = batch_size or self.config.default_batch_size
        block_ms = block_ms or self.config.default_block_ms
        
        # Ensure the consumer group exists
        self.create_consumer_group(stream, group_name)
        
        logger.info(f"Starting consumer {consumer_name} in group {group_name} for stream {stream}")
        
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
                            # Parse message
                            message = self._parse_message(message_id, data)
                            
                            # Update metrics
                            with self.lock:
                                self.metrics["messages_consumed"] += 1
                            
                            # Handle message
                            self._handle_message(stream_name, message)
                            
                            # Acknowledge the message
                            self.redis.xack(stream_name, group_name, message_id)
                        
                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {str(e)}")
                            
                            # Update metrics
                            with self.lock:
                                self.metrics["messages_failed"] += 1
                            
                            # Move to dead letter queue if configured
                            if self.config.dead_letter_stream:
                                try:
                                    # Create dead letter message
                                    dead_letter = DeadLetterMessage(
                                        original_message=message,
                                        error=str(e),
                                        retry_count=0,
                                        original_stream=stream_name
                                    )
                                    
                                    # Add to dead letter stream
                                    self.redis.xadd(
                                        self.config.dead_letter_stream,
                                        {
                                            "original_id": message.id,
                                            "error": str(e),
                                            "original_stream": stream_name,
                                            "original_message": json.dumps(message.model_dump())
                                        }
                                    )
                                    
                                    # Update metrics
                                    with self.lock:
                                        self.metrics["dead_letter_count"] += 1
                                
                                except Exception as dead_letter_error:
                                    logger.error(f"Error adding to dead letter queue: {str(dead_letter_error)}")
            
            except redis.exceptions.ConnectionError as e:
                logger.error(f"Redis connection error: {str(e)}")
                time.sleep(5)  # Wait before reconnecting
            
            except Exception as e:
                logger.error(f"Error in consumer group processing: {str(e)}")
                time.sleep(1)  # Avoid tight loop on error
    
    def request(self, request_stream: str, response_stream: str, request_type: str, 
               payload: Dict[str, Any], timeout_seconds: int = 30) -> Optional[Message]:
        """Send a request and wait for a response (request-response pattern)
        
        Args:
            request_stream: Stream to send the request to
            response_stream: Stream to listen for the response on
            request_type: Type of request
            payload: Request payload
            timeout_seconds: How long to wait for a response
            
        Returns:
            The response message, or None if timed out
        """
        # Create correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Create event to wait for response
        response_event = threading.Event()
        
        # Register response handler
        with self.lock:
            self.response_futures[correlation_id] = response_event
        
        # Create request message
        request_message = Message(
            type=request_type,
            pattern=MessagePattern.REQUEST_RESPONSE,
            source="requester",
            destination="responder",
            correlation_id=correlation_id,
            reply_to=response_stream,
            payload=payload
        )
        
        # Send request
        self.publish(request_stream, request_message)
        
        # Wait for response
        response_received = response_event.wait(timeout=timeout_seconds)
        
        # Get response if available
        response = None
        with self.lock:
            if response_received and correlation_id in self.responses:
                response = self.responses[correlation_id]
                # Clean up
                del self.responses[correlation_id]
            
            # Clean up event
            if correlation_id in self.response_futures:
                del self.response_futures[correlation_id]
        
        return response
    
    def respond_to(self, request: Message, response_type: str, payload: Dict[str, Any]) -> Optional[str]:
        """Respond to a request (request-response pattern)
        
        Args:
            request: The request message
            response_type: Type of response
            payload: Response payload
            
        Returns:
            The ID of the published response, or None if unable to respond
        """
        # Check if this is a request-response message
        if request.pattern != MessagePattern.REQUEST_RESPONSE:
            logger.warning(f"Cannot respond to message {request.id} - not a request-response message")
            return None
        
        # Check if we have the necessary information
        if not request.reply_to or not request.correlation_id:
            logger.warning(f"Cannot respond to message {request.id} - missing reply_to or correlation_id")
            return None
        
        # Create response message
        response_message = Message(
            type=response_type,
            pattern=MessagePattern.REQUEST_RESPONSE,
            source="responder",
            destination=request.source,
            correlation_id=request.correlation_id,
            payload=payload
        )
        
        # Send response
        return self.publish(request.reply_to, response_message)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for the event bus
        
        Returns:
            Dictionary of metrics
        """
        with self.lock:
            return self.metrics.copy()

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Set
import asyncio
from datetime import datetime
import json

from core.event_bus import EventBus
from core.event_patterns import Message, MessagePattern
from core.logging import setup_logging

router = APIRouter()
logger = setup_logging(service_name="events-api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        # Remove from all subscriptions
        for stream, sockets in self.subscriptions.items():
            sockets.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    def subscribe(self, websocket: WebSocket, stream: str):
        if stream not in self.subscriptions:
            self.subscriptions[stream] = set()
        self.subscriptions[stream].add(websocket)
        logger.info(f"WebSocket subscribed to stream: {stream}")
    
    def unsubscribe(self, websocket: WebSocket, stream: str):
        if stream in self.subscriptions:
            self.subscriptions[stream].discard(websocket)
            logger.info(f"WebSocket unsubscribed from stream: {stream}")
    
    async def send_to_stream(self, stream: str, message: dict):
        if stream in self.subscriptions:
            disconnected = set()
            for websocket in self.subscriptions[stream]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    disconnected.add(websocket)
            # Clean up disconnected sockets
            for websocket in disconnected:
                self.disconnect(websocket)

manager = ConnectionManager()

# Request/Response models
class EventMessage(BaseModel):
    type: str = Field(..., description="Type of the event")
    source: str = Field(..., description="Source of the event")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Event metadata")
    stream: str = Field(default="default", description="Stream to publish to")
    pattern: MessagePattern = Field(default=MessagePattern.EVENT, description="Message pattern")


class EventSubscription(BaseModel):
    stream: str = Field(..., description="Stream to subscribe to")
    consumer_group: str = Field(default="default", description="Consumer group name")


class EventFilter(BaseModel):
    types: Optional[List[str]] = Field(None, description="Filter by event types")
    source: Optional[str] = Field(None, description="Filter by source")
    after: Optional[datetime] = Field(None, description="Events after this time")
    limit: int = Field(default=100, description="Maximum number of events")


@router.post("/publish")
async def publish_event(event: EventMessage, event_bus: EventBus = Depends(lambda: EventBus(simulation_mode=True))):
    """Publish an event to the event bus"""
    try:
        message = Message(
            type=event.type,
            source=event.source,
            payload=event.payload,
            metadata=event.metadata,
            pattern=event.pattern
        )
        
        # Publish to event bus
        event_id = event_bus.publish(event.stream, message)
        
        # Also send to WebSocket subscribers
        await manager.send_to_stream(event.stream, {
            "event_id": event_id,
            "stream": event.stream,
            "message": message.dict()
        })
        
        logger.info(f"Published event {event_id} to stream {event.stream}")
        
        return {
            "event_id": event_id,
            "stream": event.stream,
            "timestamp": message.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error publishing event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error publishing event: {str(e)}")


@router.post("/subscribe")
async def create_subscription(subscription: EventSubscription, event_bus: EventBus = Depends(lambda: EventBus(simulation_mode=True))):
    """Create a subscription to a stream"""
    try:
        # In a real implementation, this would create a consumer group
        # For now, we'll just acknowledge the subscription
        logger.info(f"Created subscription to stream {subscription.stream} for group {subscription.consumer_group}")
        
        return {
            "stream": subscription.stream,
            "consumer_group": subscription.consumer_group,
            "status": "subscribed"
        }
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating subscription: {str(e)}")


@router.get("/streams")
async def list_streams(event_bus: EventBus = Depends(lambda: EventBus(simulation_mode=True))):
    """List all available event streams"""
    try:
        # In a real implementation, this would list actual streams
        # For now, return common streams
        streams = [
            {
                "name": "agent_events",
                "description": "Events from agent operations",
                "message_count": 0
            },
            {
                "name": "gateway_events",
                "description": "Events from gateway communications",
                "message_count": 0
            },
            {
                "name": "workflow_events",
                "description": "Events from workflow executions",
                "message_count": 0
            },
            {
                "name": "default",
                "description": "Default event stream",
                "message_count": 0
            }
        ]
        
        return {"streams": streams}
        
    except Exception as e:
        logger.error(f"Error listing streams: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing streams: {str(e)}")


@router.get("/events")
async def get_events(
    stream: str = "default",
    filter: EventFilter = Depends(),
    event_bus: EventBus = Depends(lambda: EventBus(simulation_mode=True))
):
    """Get events from a stream with optional filtering"""
    try:
        # In a real implementation, this would read from the actual stream
        # For now, return empty results in simulation mode
        logger.info(f"Getting events from stream {stream} with filter {filter}")
        
        return {
            "stream": stream,
            "events": [],
            "count": 0,
            "filter": filter.dict()
        }
        
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting events: {str(e)}")


@router.websocket("/ws/{stream}")
async def websocket_endpoint(websocket: WebSocket, stream: str):
    """WebSocket endpoint for real-time event streaming"""
    await manager.connect(websocket)
    manager.subscribe(websocket, stream)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({"action": "pong"})
            elif message.get("action") == "unsubscribe":
                manager.unsubscribe(websocket, stream)
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/metrics")
async def get_event_metrics(event_bus: EventBus = Depends(lambda: EventBus(simulation_mode=True))):
    """Get metrics for the event system"""
    try:
        metrics = event_bus.get_metrics()
        
        return {
            "metrics": metrics,
            "websocket_connections": len(manager.active_connections),
            "active_subscriptions": {
                stream: len(sockets) 
                for stream, sockets in manager.subscriptions.items()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")
"""
Communication router for inbox functionality
Handles email messages and processing
"""

from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import uuid

router = APIRouter()

# Mock messages storage
mock_messages = {}

class EmailMessage:
    def __init__(self, sender: str, subject: str, content: str):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.subject = subject
        self.timestamp = datetime.utcnow().isoformat()
        self.content = content
        self.status = "unread"
        self.codeword = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender,
            "subject": self.subject,
            "timestamp": self.timestamp,
            "content": self.content,
            "status": self.status,
            "codeword": self.codeword
        }

@router.get("/inbox")
async def get_messages():
    """Get all email messages"""
    return list(mock_messages.values())

@router.get("/inbox/{message_id}")
async def get_message(message_id: str):
    """Get a specific message"""
    if message_id not in mock_messages:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return mock_messages[message_id]

@router.patch("/inbox/{message_id}/read")
async def mark_as_read(message_id: str):
    """Mark message as read"""
    if message_id not in mock_messages:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message = mock_messages[message_id]
    message["status"] = "read"
    
    return {"status": "success"}

@router.post("/inbox/{message_id}/process")
async def process_message(message_id: str):
    """Process a message through the agent system"""
    if message_id not in mock_messages:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message = mock_messages[message_id]
    message["status"] = "processing"
    
    # In production, this would trigger the agent workflow
    # For now, just update status
    message["status"] = "processed"
    
    return {"status": "success"}

@router.get("/inbox/stats")
async def get_inbox_stats():
    """Get inbox statistics"""
    messages = list(mock_messages.values())
    
    return {
        "unread": len([m for m in messages if m.get("status") == "unread"]),
        "processing": len([m for m in messages if m.get("status") == "processing"]),
        "processed": len([m for m in messages if m.get("status") == "processed"]),
        "total": len(messages)
    }

# Initialize with some sample messages
def init_sample_data():
    sample_messages = [
        EmailMessage(
            "john@example.com",
            "Quarterly Report Analysis",
            "Please analyze the attached quarterly report"
        ),
        EmailMessage(
            "sarah@example.com",
            "Market Research Document",
            "Could you summarize this market research?"
        )
    ]
    
    for msg in sample_messages:
        mock_messages[msg.id] = msg.to_dict()

# Initialize on import
init_sample_data()
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime


class TaskSchema(BaseModel):
    """Schema for a task in the system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    status: str  # "pending", "processing", "completed", "failed"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class ContentSchema(BaseModel):
    """Schema for content in the knowledge repository"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source: str
    content_type: str  # "url", "pdf", "text"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    text_content: str
    summary: Optional[str] = None
    vector_id: Optional[str] = None


class UserSchema(BaseModel):
    """Schema for a user in the system"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class AgentSchema(BaseModel):
    """Schema for agent metadata"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    type: str
    capabilities: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True

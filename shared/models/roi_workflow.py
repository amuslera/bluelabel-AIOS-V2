"""
Database models for ROI workflow system.
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from enum import Enum

from shared.models.base import Base


class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Step status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ROIWorkflow(Base):
    """ROI workflow main table"""
    __tablename__ = "roi_workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), nullable=False, default=WorkflowStatus.UPLOADED.value)
    
    # Audio file information
    audio_file_path = Column(String(255), nullable=False)
    audio_file_name = Column(String(255), nullable=False)
    audio_file_size = Column(Integer, nullable=True)
    audio_format = Column(String(10), nullable=True)
    
    # Processing results
    language_detected = Column(String(10), nullable=True)
    transcription = Column(Text, nullable=True)
    # transcription_english = Column(Text, nullable=True)  # TODO: Add migration for this
    transcription_confidence = Column(Float, nullable=True)
    extracted_data = Column(JSONB, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # User tracking (optional)
    user_id = Column(String(255), nullable=True)
    
    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ROIWorkflow(id={self.id}, status={self.status}, file={self.audio_file_name})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "status": self.status,
            "audio_file_name": self.audio_file_name,
            "audio_file_size": self.audio_file_size,
            "audio_format": self.audio_format,
            "language_detected": self.language_detected,
            "transcription": self.transcription,
            "transcription_confidence": self.transcription_confidence,
            "extracted_data": self.extracted_data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "user_id": self.user_id,
            "steps": [step.to_dict() for step in self.steps] if self.steps else []
        }
    
    def get_progress_percentage(self):
        """Calculate completion percentage based on steps"""
        if not self.steps:
            return 0
        
        total_steps = len(self.steps)
        completed_steps = len([step for step in self.steps if step.status == StepStatus.COMPLETED.value])
        
        return int((completed_steps / total_steps) * 100)
    
    def get_current_step(self):
        """Get the currently running or next step"""
        if not self.steps:
            return None
        
        # Find running step
        for step in self.steps:
            if step.status == StepStatus.RUNNING.value:
                return step
        
        # Find next pending step
        for step in self.steps:
            if step.status == StepStatus.PENDING.value:
                return step
        
        return None


class WorkflowStep(Base):
    """Individual workflow step tracking"""
    __tablename__ = "workflow_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey('roi_workflows.id', ondelete='CASCADE'), nullable=False)
    
    # Step information
    step_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default=StepStatus.PENDING.value)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Results and errors
    error_message = Column(Text, nullable=True)
    step_data = Column(JSONB, nullable=True)
    
    # Relationships
    workflow = relationship("ROIWorkflow", back_populates="steps")
    
    def __repr__(self):
        return f"<WorkflowStep(id={self.id}, name={self.step_name}, status={self.status})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "workflow_id": str(self.workflow_id),
            "step_name": self.step_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time_ms": self.processing_time_ms,
            "error_message": self.error_message,
            "step_data": self.step_data
        }
    
    def start(self):
        """Mark step as started"""
        self.status = StepStatus.RUNNING.value
        self.started_at = datetime.utcnow()
    
    def complete(self, step_data=None):
        """Mark step as completed"""
        self.status = StepStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        if step_data:
            self.step_data = step_data
        
        # Calculate processing time
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.processing_time_ms = int(delta.total_seconds() * 1000)
    
    def fail(self, error_message: str):
        """Mark step as failed"""
        self.status = StepStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        
        # Calculate processing time
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.processing_time_ms = int(delta.total_seconds() * 1000)
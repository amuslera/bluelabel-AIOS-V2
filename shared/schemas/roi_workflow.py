"""
Pydantic schemas for ROI workflow API.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


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


class ContactType(str, Enum):
    """Contact type enumeration"""
    PROSPECTIVE = "Prospective"
    EXISTING = "Existing"


class PriorityLevel(str, Enum):
    """Priority level enumeration"""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ExtractedData(BaseModel):
    """Structured data extracted from meeting transcript"""
    name: Optional[str] = Field(None, description="Person's name")
    company: Optional[str] = Field(None, description="Company name")
    position: Optional[str] = Field(None, description="Person's role/title")
    discussion: Optional[str] = Field(None, description="Summary of what was discussed")
    contact_type: Optional[ContactType] = Field(None, description="Prospective or Existing client")
    priority: Optional[PriorityLevel] = Field(None, description="Priority level")
    action_items: Optional[List[str]] = Field(None, description="List of follow-up actions")
    
    class Config:
        use_enum_values = True


class WorkflowStepResponse(BaseModel):
    """Workflow step response model"""
    id: str
    workflow_id: str
    step_name: str
    status: StepStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_ms: Optional[int]
    error_message: Optional[str]
    step_data: Optional[Dict[str, Any]]
    
    class Config:
        use_enum_values = True


class WorkflowResponse(BaseModel):
    """ROI workflow response model"""
    id: str
    status: WorkflowStatus
    audio_file_name: str
    audio_file_size: Optional[int]
    audio_format: Optional[str]
    language_detected: Optional[str]
    transcription: Optional[str]
    transcription_confidence: Optional[float]
    extracted_data: Optional[ExtractedData]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    user_id: Optional[str]
    steps: Optional[List[WorkflowStepResponse]]
    progress_percentage: Optional[int] = Field(None, description="Completion percentage 0-100")
    
    class Config:
        use_enum_values = True


class WorkflowSummaryResponse(BaseModel):
    """Workflow summary response for list endpoints"""
    id: str
    status: WorkflowStatus
    audio_file_name: str
    language_detected: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    progress_percentage: int
    
    class Config:
        use_enum_values = True


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a workflow"""
    user_id: Optional[str] = Field(None, description="Optional user ID for tracking")


class WorkflowUploadResponse(BaseModel):
    """Response after uploading audio file"""
    workflow_id: str
    status: WorkflowStatus
    message: str
    
    class Config:
        use_enum_values = True


class WorkflowStatusUpdate(BaseModel):
    """WebSocket status update model"""
    workflow_id: str
    status: WorkflowStatus
    step_name: Optional[str]
    progress_percentage: int
    message: Optional[str]
    error: Optional[str]
    
    class Config:
        use_enum_values = True


class CSVExportRequest(BaseModel):
    """Request model for CSV export"""
    workflow_ids: Optional[List[str]] = Field(None, description="Specific workflow IDs to export")
    date_from: Optional[datetime] = Field(None, description="Export workflows from this date")
    date_to: Optional[datetime] = Field(None, description="Export workflows until this date")
    status_filter: Optional[List[WorkflowStatus]] = Field(None, description="Filter by status")
    
    @validator('workflow_ids', pre=True)
    def validate_workflow_ids(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError('Cannot export more than 100 workflows at once')
        return v


class WorkflowListResponse(BaseModel):
    """Paginated workflow list response"""
    workflows: List[WorkflowSummaryResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class WorkflowStats(BaseModel):
    """Workflow statistics"""
    total_workflows: int
    completed_workflows: int
    failed_workflows: int
    processing_workflows: int
    average_processing_time_seconds: Optional[float]
    languages_detected: Dict[str, int]
    success_rate_percentage: float
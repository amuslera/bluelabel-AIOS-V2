"""
ROI workflow API endpoints.
Handles audio upload, processing, and results retrieval for ROI analysis workflows.
"""
import io
import csv
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Set
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from apps.api.dependencies.database import get_db
from services.roi_workflow_service import ROIWorkflowService
from shared.schemas.roi_workflow import (
    WorkflowResponse, WorkflowUploadResponse, WorkflowCreateRequest,
    WorkflowListResponse, WorkflowSummaryResponse, CSVExportRequest,
    WorkflowStats, ExtractedData, WorkflowStatus
)
from shared.models.roi_workflow import ROIWorkflow
from core.config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows/roi-report", tags=["ROI Workflows"])

# Initialize workflow service
workflow_service = ROIWorkflowService()

# WebSocket connection manager for real-time progress updates
class ROIWorkflowConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, workflow_id: str):
        await websocket.accept()
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = set()
        self.active_connections[workflow_id].add(websocket)
        logger.info(f"WebSocket connected for workflow {workflow_id}")
    
    def disconnect(self, websocket: WebSocket, workflow_id: str):
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].discard(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        logger.info(f"WebSocket disconnected for workflow {workflow_id}")
    
    async def send_progress_update(self, workflow_id: str, update: dict):
        if workflow_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[workflow_id]:
                try:
                    await websocket.send_json(update)
                except Exception as e:
                    logger.error(f"Error sending progress update: {e}")
                    disconnected.add(websocket)
            
            # Clean up disconnected sockets
            for websocket in disconnected:
                self.disconnect(websocket, workflow_id)

websocket_manager = ROIWorkflowConnectionManager()

# Set up WebSocket callback for workflow service
async def websocket_callback(update_data: dict):
    """Callback function for workflow progress updates"""
    workflow_id = update_data.get("workflow_id")
    if workflow_id:
        await websocket_manager.send_progress_update(workflow_id, update_data)

workflow_service.set_websocket_callback(websocket_callback)


@router.post("/", response_model=WorkflowUploadResponse)
async def upload_audio_for_roi_analysis(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    user_id: Optional[str] = Query(None, description="Optional user ID for tracking"),
    db: Session = Depends(get_db)
):
    """
    Upload audio file and create ROI workflow.
    Starts background processing for transcription and data extraction.
    """
    try:
        # Validate file upload
        if not audio_file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (25MB limit)
        max_size = 25 * 1024 * 1024
        content = await audio_file.read()
        if len(content) > max_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {max_size / (1024*1024)}MB"
            )
        
        # Validate audio format
        file_extension = audio_file.filename.split('.')[-1].lower()
        if file_extension not in workflow_service.supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported formats: {', '.join(workflow_service.supported_formats)}"
            )
        
        logger.info(f"Creating workflow for audio file: {audio_file.filename}")
        
        # Create workflow
        workflow = await workflow_service.create_workflow(
            db=db,
            audio_file_name=audio_file.filename,
            audio_file_content=content,
            user_id=user_id
        )
        
        # Start background processing
        background_tasks.add_task(
            _process_workflow_background,
            workflow_id=str(workflow.id),
            db_session=db
        )
        
        logger.info(f"Started background processing for workflow {workflow.id}")
        
        return WorkflowUploadResponse(
            workflow_id=str(workflow.id),
            status=workflow.status,
            message="Audio uploaded successfully. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload audio file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_status(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed workflow status and results."""
    try:
        workflow = workflow_service.get_workflow_status(db, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Convert to response model
        response_data = workflow.to_dict()
        response_data["progress_percentage"] = workflow.get_progress_percentage()
        
        return WorkflowResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow status")


@router.get("/{workflow_id}/results")
async def get_workflow_results(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Get workflow results in structured format."""
    try:
        workflow = workflow_service.get_workflow_status(db, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != WorkflowStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400, 
                detail=f"Workflow not completed. Current status: {workflow.status}"
            )
        
        if not workflow.extracted_data:
            raise HTTPException(status_code=404, detail="No extracted data available")
        
        return {
            "workflow_id": str(workflow.id),
            "status": workflow.status,
            "transcription": workflow.transcription,
            "language_detected": workflow.language_detected,
            "transcription_confidence": workflow.transcription_confidence,
            "extracted_data": workflow.extracted_data,
            "created_at": workflow.created_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow results: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve results")


@router.get("/{workflow_id}/csv")
async def download_workflow_csv(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Download workflow results as CSV file."""
    try:
        workflow = workflow_service.get_workflow_status(db, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != WorkflowStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400, 
                detail=f"Workflow not completed. Current status: {workflow.status}"
            )
        
        # Generate CSV content
        csv_content = _generate_single_workflow_csv(workflow)
        
        # Create response
        filename = f"roi_workflow_{workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate CSV")


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """List workflows with pagination and filtering."""
    try:
        offset = (page - 1) * per_page
        
        # Get workflows
        workflows = workflow_service.list_workflows(
            db=db,
            user_id=user_id,
            status=status,
            limit=per_page,
            offset=offset
        )
        
        # Get total count for pagination
        from sqlalchemy import func
        query = db.query(func.count(ROIWorkflow.id))
        if user_id:
            query = query.filter(ROIWorkflow.user_id == user_id)
        if status:
            query = query.filter(ROIWorkflow.status == status.value)
        total = query.scalar()
        
        total_pages = (total + per_page - 1) // per_page
        
        # Convert to summary responses
        workflow_summaries = []
        for workflow in workflows:
            workflow_summaries.append(WorkflowSummaryResponse(
                id=str(workflow.id),
                status=workflow.status,
                audio_file_name=workflow.audio_file_name,
                language_detected=workflow.language_detected,
                created_at=workflow.created_at,
                completed_at=workflow.completed_at,
                progress_percentage=workflow.get_progress_percentage()
            ))
        
        return WorkflowListResponse(
            workflows=workflow_summaries,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to list workflows")


@router.post("/export-csv")
async def export_workflows_csv(
    export_request: CSVExportRequest,
    db: Session = Depends(get_db)
):
    """Export multiple workflows to CSV."""
    try:
        # Build query based on filters
        query = db.query(ROIWorkflow)
        
        if export_request.workflow_ids:
            query = query.filter(ROIWorkflow.id.in_(export_request.workflow_ids))
        
        if export_request.date_from:
            query = query.filter(ROIWorkflow.created_at >= export_request.date_from)
        
        if export_request.date_to:
            query = query.filter(ROIWorkflow.created_at <= export_request.date_to)
        
        if export_request.status_filter:
            status_values = [status.value for status in export_request.status_filter]
            query = query.filter(ROIWorkflow.status.in_(status_values))
        
        # Limit to prevent abuse
        workflows = query.limit(100).all()
        
        if not workflows:
            raise HTTPException(status_code=404, detail="No workflows found matching criteria")
        
        # Generate CSV content
        csv_content = _generate_multi_workflow_csv(workflows)
        
        # Create response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"roi_workflows_export_{timestamp}.csv"
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to export CSV")


@router.get("/stats/summary", response_model=WorkflowStats)
async def get_workflow_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db)
):
    """Get workflow statistics and analytics."""
    try:
        from sqlalchemy import func
        
        # Base query
        query = db.query(ROIWorkflow)
        if user_id:
            query = query.filter(ROIWorkflow.user_id == user_id)
        
        # Total workflows
        total_workflows = query.count()
        
        # Status counts
        completed_workflows = query.filter(ROIWorkflow.status == WorkflowStatus.COMPLETED.value).count()
        failed_workflows = query.filter(ROIWorkflow.status == WorkflowStatus.FAILED.value).count()
        processing_statuses = [
            WorkflowStatus.UPLOADED.value,
            WorkflowStatus.TRANSCRIBING.value,
            WorkflowStatus.EXTRACTING.value
        ]
        processing_workflows = query.filter(ROIWorkflow.status.in_(processing_statuses)).count()
        
        # Average processing time (completed workflows only)
        completed_query = query.filter(
            ROIWorkflow.status == WorkflowStatus.COMPLETED.value,
            ROIWorkflow.completed_at.isnot(None),
            ROIWorkflow.created_at.isnot(None)
        )
        
        avg_time = None
        if completed_workflows > 0:
            # Calculate average in database
            time_diff = func.extract('epoch', ROIWorkflow.completed_at - ROIWorkflow.created_at)
            avg_time = completed_query.with_entities(func.avg(time_diff)).scalar()
        
        # Language distribution
        language_dist = {}
        if total_workflows > 0:
            lang_results = db.query(
                ROIWorkflow.language_detected,
                func.count(ROIWorkflow.id)
            ).filter(
                ROIWorkflow.language_detected.isnot(None)
            ).group_by(ROIWorkflow.language_detected).all()
            
            language_dist = {lang: count for lang, count in lang_results}
        
        # Success rate
        success_rate = 0.0
        if total_workflows > 0:
            success_rate = (completed_workflows / total_workflows) * 100
        
        return WorkflowStats(
            total_workflows=total_workflows,
            completed_workflows=completed_workflows,
            failed_workflows=failed_workflows,
            processing_workflows=processing_workflows,
            average_processing_time_seconds=avg_time,
            languages_detected=language_dist,
            success_rate_percentage=success_rate
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Delete workflow and associated files."""
    try:
        success = await workflow_service.delete_workflow(db, workflow_id)
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {"message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workflow")


@router.websocket("/ws/{workflow_id}")
async def websocket_workflow_progress(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for real-time workflow progress updates."""
    await websocket_manager.connect(websocket, workflow_id)
    
    try:
        while True:
            # Keep connection alive and handle heartbeat
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "ping":
                await websocket.send_json({"action": "pong", "timestamp": datetime.utcnow().isoformat()})
            elif message.get("action") == "disconnect":
                break
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, workflow_id)
    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {e}")
        websocket_manager.disconnect(websocket, workflow_id)


@router.get("/performance/stats")
async def get_performance_statistics():
    """Get comprehensive performance statistics for ROI workflows."""
    try:
        stats = await workflow_service.get_performance_stats()
        
        return {
            "performance_stats": stats,
            "websocket_connections": sum(len(connections) for connections in websocket_manager.active_connections.values()),
            "active_workflow_connections": len(websocket_manager.active_connections),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance statistics")


@router.post("/performance/cache/clear")
async def clear_performance_cache(
    cache_type: Optional[str] = Query(None, description="Cache type to clear: transcription, translation, extraction, or all")
):
    """Clear performance cache for better testing or troubleshooting."""
    try:
        await workflow_service.clear_cache(cache_type)
        
        return {
            "message": f"Cache cleared successfully {'for ' + cache_type if cache_type else 'for all types'}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/health/check")
async def health_check():
    """Check health of ROI workflow components."""
    try:
        health_status = await workflow_service.health_check()
        
        all_healthy = all(health_status.values())
        status_code = 200 if all_healthy else 503
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "components": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Helper functions

async def _process_workflow_background(workflow_id: str, db_session: Session):
    """Background task to process workflow."""
    try:
        logger.info(f"Starting background processing for workflow {workflow_id}")
        result = await workflow_service.process_workflow(db_session, workflow_id)
        
        if result["success"]:
            logger.info(f"Successfully completed background processing for workflow {workflow_id}")
        else:
            logger.error(f"Background processing failed for workflow {workflow_id}: {result['error']}")
            
    except Exception as e:
        logger.error(f"Background processing error for workflow {workflow_id}: {e}")


def _generate_single_workflow_csv(workflow: ROIWorkflow) -> str:
    """Generate CSV content for a single workflow."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Workflow ID', 'Audio File', 'Status', 'Language', 'Created At', 'Completed At',
        'Name', 'Company', 'Position', 'Discussion', 'Contact Type', 'Priority', 'Action Items'
    ])
    
    # Data
    extracted = workflow.extracted_data or {}
    action_items = '; '.join(extracted.get('action_items', [])) if extracted.get('action_items') else ''
    
    writer.writerow([
        str(workflow.id),
        workflow.audio_file_name,
        workflow.status,
        workflow.language_detected or '',
        workflow.created_at.isoformat() if workflow.created_at else '',
        workflow.completed_at.isoformat() if workflow.completed_at else '',
        extracted.get('name', ''),
        extracted.get('company', ''),
        extracted.get('position', ''),
        extracted.get('discussion', ''),
        extracted.get('contact_type', ''),
        extracted.get('priority', ''),
        action_items
    ])
    
    return output.getvalue()


def _generate_multi_workflow_csv(workflows: List[ROIWorkflow]) -> str:
    """Generate CSV content for multiple workflows."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Workflow ID', 'Audio File', 'Status', 'Language', 'Created At', 'Completed At',
        'Name', 'Company', 'Position', 'Discussion', 'Contact Type', 'Priority', 'Action Items'
    ])
    
    # Data rows
    for workflow in workflows:
        extracted = workflow.extracted_data or {}
        action_items = '; '.join(extracted.get('action_items', [])) if extracted.get('action_items') else ''
        
        writer.writerow([
            str(workflow.id),
            workflow.audio_file_name,
            workflow.status,
            workflow.language_detected or '',
            workflow.created_at.isoformat() if workflow.created_at else '',
            workflow.completed_at.isoformat() if workflow.completed_at else '',
            extracted.get('name', ''),
            extracted.get('company', ''),
            extracted.get('position', ''),
            extracted.get('discussion', ''),
            extracted.get('contact_type', ''),
            extracted.get('priority', ''),
            action_items
        ])
    
    return output.getvalue()
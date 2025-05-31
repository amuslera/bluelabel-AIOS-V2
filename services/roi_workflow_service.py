"""
ROI workflow orchestration service.
Coordinates the complete workflow from audio upload to data extraction.
"""
import os
import asyncio
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from shared.models.roi_workflow import ROIWorkflow, WorkflowStep, WorkflowStatus, StepStatus
from shared.schemas.roi_workflow import WorkflowStatusUpdate
from agents.transcription_agent import TranscriptionAgent
from agents.extraction_agent import ExtractionAgent
# from agents.translation_agent import TranslationAgent  # TODO: Enable when ready
from core.config import config

logger = logging.getLogger(__name__)


class ROIWorkflowService:
    """Service for orchestrating ROI workflow processing"""
    
    def __init__(self):
        self.transcription_agent = TranscriptionAgent()
        self.extraction_agent = ExtractionAgent()
        # self.translation_agent = TranslationAgent()  # Disabled for now
        
        # Storage configuration
        self.storage_path = Path(config.local_storage_path) / "roi_workflows"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Supported audio formats
        self.supported_formats = {
            'mp3', 'mp4', 'm4a', 'wav', 'webm', 'flac', 'oga', 'ogg'
        }
        
        # WebSocket callback for real-time updates
        self.websocket_callback = None
    
    def set_websocket_callback(self, callback):
        """Set callback function for WebSocket updates"""
        self.websocket_callback = callback
    
    async def create_workflow(
        self, 
        db: Session,
        audio_file_name: str,
        audio_file_content: bytes,
        user_id: Optional[str] = None
    ) -> ROIWorkflow:
        """
        Create a new ROI workflow and store the audio file.
        
        Args:
            db: Database session
            audio_file_name: Original filename
            audio_file_content: Audio file binary content
            user_id: Optional user ID for tracking
        
        Returns:
            ROIWorkflow: Created workflow instance
        """
        try:
            # Validate file format
            file_extension = Path(audio_file_name).suffix.lower().lstrip('.')
            if file_extension not in self.supported_formats:
                raise ValueError(f"Unsupported audio format: {file_extension}")
            
            # Generate unique workflow ID and file path
            workflow_id = uuid.uuid4()
            safe_filename = f"{workflow_id}_{audio_file_name}"
            audio_file_path = self.storage_path / safe_filename
            
            # Store audio file
            async with aiofiles.open(audio_file_path, 'wb') as f:
                await f.write(audio_file_content)
            
            # Create workflow record
            workflow = ROIWorkflow(
                id=workflow_id,
                status=WorkflowStatus.UPLOADED.value,
                audio_file_path=str(audio_file_path),
                audio_file_name=audio_file_name,
                audio_file_size=len(audio_file_content),
                audio_format=file_extension,
                user_id=user_id
            )
            
            # Create workflow steps
            steps = [
                WorkflowStep(
                    workflow_id=workflow_id,
                    step_name="transcription",
                    status=StepStatus.PENDING.value
                ),
                WorkflowStep(
                    workflow_id=workflow_id,
                    step_name="extraction",
                    status=StepStatus.PENDING.value
                )
            ]
            
            workflow.steps = steps
            
            # Save to database
            db.add(workflow)
            db.add_all(steps)
            db.commit()
            db.refresh(workflow)
            
            logger.info(f"Created workflow {workflow_id} for file {audio_file_name}")
            
            # Send initial status update
            await self._send_status_update(workflow, "Workflow created, ready for processing")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            # Clean up file if it was created
            if 'audio_file_path' in locals() and os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            raise
    
    async def process_workflow(self, db: Session, workflow_id: str) -> Dict[str, Any]:
        """
        Process a complete ROI workflow asynchronously.
        
        Args:
            db: Database session
            workflow_id: Workflow ID to process
        
        Returns:
            Dict containing final results
        """
        workflow = db.query(ROIWorkflow).filter(ROIWorkflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        try:
            logger.info(f"Starting processing for workflow {workflow_id}")
            
            # Step 1: Transcription
            transcription_result = await self._process_transcription_step(db, workflow)
            if not transcription_result["success"]:
                await self._fail_workflow(db, workflow, transcription_result["error"])
                return transcription_result
            
            # Step 2: Data Extraction
            extraction_result = await self._process_extraction_step(db, workflow)
            if not extraction_result["success"]:
                await self._fail_workflow(db, workflow, extraction_result["error"])
                return extraction_result
            
            # Mark workflow as completed
            await self._complete_workflow(db, workflow)
            
            logger.info(f"Successfully completed workflow {workflow_id}")
            
            return {
                "success": True,
                "workflow_id": str(workflow_id),
                "transcription": workflow.transcription,
                "extracted_data": workflow.extracted_data,
                "language": workflow.language_detected
            }
            
        except Exception as e:
            logger.error(f"Workflow processing failed for {workflow_id}: {e}")
            await self._fail_workflow(db, workflow, str(e))
            return {
                "success": False,
                "error": str(e),
                "workflow_id": str(workflow_id)
            }
    
    async def _process_transcription_step(self, db: Session, workflow: ROIWorkflow) -> Dict[str, Any]:
        """Process the transcription step"""
        step = next((s for s in workflow.steps if s.step_name == "transcription"), None)
        if not step:
            return {"success": False, "error": "Transcription step not found"}
        
        try:
            # Update workflow and step status
            workflow.status = WorkflowStatus.TRANSCRIBING.value
            step.start()
            db.commit()
            
            await self._send_status_update(workflow, "Starting transcription...")
            
            # Process transcription
            result = await self.transcription_agent.process({
                "audio_file_path": workflow.audio_file_path,
                "language": None,  # Auto-detect
                "prompt": "This is a business meeting summary with client information."
            })
            
            if result["success"]:
                # Update workflow with original transcription
                workflow.transcription = result["transcription"]
                workflow.language_detected = result["language"]
                workflow.transcription_confidence = result["confidence"]
                
                # Store English version (for now, same as original)
                # TODO: Add proper translation when translation agent is ready
                # workflow.transcription_english = result["transcription"]
                
                # Complete step
                step.complete({
                    "transcription_length": len(result["transcription"]),
                    "language_detected": result["language"],
                    "confidence": result["confidence"],
                    "duration": result["duration"],
                    "translated": result["language"] == "spanish"
                })
                
                db.commit()
                
                await self._send_status_update(workflow, "Transcription completed successfully")
                
                logger.info(
                    f"Transcription completed for workflow {workflow.id}: "
                    f"{len(result['transcription'])} chars, {result['language']}"
                )
                
                return {"success": True}
            else:
                step.fail(result["error"])
                db.commit()
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            step.fail(str(e))
            db.commit()
            logger.error(f"Transcription step failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_extraction_step(self, db: Session, workflow: ROIWorkflow) -> Dict[str, Any]:
        """Process the data extraction step"""
        step = next((s for s in workflow.steps if s.step_name == "extraction"), None)
        if not step:
            return {"success": False, "error": "Extraction step not found"}
        
        try:
            # Update workflow status
            workflow.status = WorkflowStatus.EXTRACTING.value
            step.start()
            db.commit()
            
            await self._send_status_update(workflow, "Extracting structured data...")
            
            # Process extraction
            result = await self.extraction_agent.process({
                "transcription": workflow.transcription,
                "language": workflow.language_detected,
                "context": f"Audio file: {workflow.audio_file_name}"
            })
            
            if result["success"]:
                # Update workflow with results
                workflow.extracted_data = result["extracted_data"]
                
                # Complete step
                step.complete({
                    "extraction_confidence": result["confidence"],
                    "language_used": result["language_used"],
                    "fields_extracted": len([k for k, v in result["extracted_data"].items() if v])
                })
                
                db.commit()
                
                await self._send_status_update(workflow, "Data extraction completed successfully")
                
                logger.info(
                    f"Data extraction completed for workflow {workflow.id}: "
                    f"confidence {result['confidence']:.2f}"
                )
                
                return {"success": True}
            else:
                step.fail(result["error"])
                db.commit()
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            step.fail(str(e))
            db.commit()
            logger.error(f"Extraction step failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _complete_workflow(self, db: Session, workflow: ROIWorkflow):
        """Mark workflow as completed"""
        workflow.status = WorkflowStatus.COMPLETED.value
        workflow.completed_at = datetime.utcnow()
        db.commit()
        
        await self._send_status_update(workflow, "Workflow completed successfully")
    
    async def _fail_workflow(self, db: Session, workflow: ROIWorkflow, error_message: str):
        """Mark workflow as failed"""
        workflow.status = WorkflowStatus.FAILED.value
        workflow.error_message = error_message
        workflow.completed_at = datetime.utcnow()
        db.commit()
        
        await self._send_status_update(workflow, f"Workflow failed: {error_message}")
    
    async def _send_status_update(self, workflow: ROIWorkflow, message: str):
        """Send real-time status update via WebSocket"""
        if not self.websocket_callback:
            return
        
        try:
            update = WorkflowStatusUpdate(
                workflow_id=str(workflow.id),
                status=workflow.status,
                step_name=workflow.get_current_step().step_name if workflow.get_current_step() else None,
                progress_percentage=workflow.get_progress_percentage(),
                message=message,
                error=workflow.error_message
            )
            
            await self.websocket_callback(update.dict())
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket update: {e}")
    
    def get_workflow_status(self, db: Session, workflow_id: str) -> Optional[ROIWorkflow]:
        """Get current workflow status"""
        return db.query(ROIWorkflow).filter(ROIWorkflow.id == workflow_id).first()
    
    def list_workflows(
        self, 
        db: Session, 
        user_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ROIWorkflow]:
        """List workflows with optional filtering"""
        query = db.query(ROIWorkflow)
        
        if user_id:
            query = query.filter(ROIWorkflow.user_id == user_id)
        
        if status:
            query = query.filter(ROIWorkflow.status == status.value)
        
        return query.order_by(ROIWorkflow.created_at.desc()).offset(offset).limit(limit).all()
    
    async def delete_workflow(self, db: Session, workflow_id: str) -> bool:
        """Delete workflow and associated files"""
        workflow = db.query(ROIWorkflow).filter(ROIWorkflow.id == workflow_id).first()
        if not workflow:
            return False
        
        try:
            # Delete audio file
            if os.path.exists(workflow.audio_file_path):
                os.remove(workflow.audio_file_path)
            
            # Delete database record (cascade will handle steps)
            db.delete(workflow)
            db.commit()
            
            logger.info(f"Deleted workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete workflow {workflow_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all workflow components"""
        return {
            "transcription_agent": await self.transcription_agent.health_check(),
            "extraction_agent": await self.extraction_agent.health_check(),
            "storage_accessible": self.storage_path.exists() and self.storage_path.is_dir()
        }
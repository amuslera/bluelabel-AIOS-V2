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
from agents.translation_agent import TranslationAgent
from services.cache_service import cache_service
from services.performance_monitor import performance_monitor
from core.config import config

logger = logging.getLogger(__name__)


class ROIWorkflowService:
    """Service for orchestrating ROI workflow processing with optimization"""
    
    def __init__(self):
        self.transcription_agent = TranscriptionAgent()
        self.extraction_agent = ExtractionAgent()
        self.translation_agent = TranslationAgent()
        
        # Storage configuration
        self.storage_path = Path(config.local_storage_path) / "roi_workflows"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Supported audio formats
        self.supported_formats = {
            'mp3', 'mp4', 'm4a', 'wav', 'webm', 'flac', 'oga', 'ogg'
        }
        
        # WebSocket callback for real-time updates
        self.websocket_callback = None
        
        # Performance tracking
        self.performance_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "parallel_processing_enabled": True
        }
    
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
                    step_name="translation",
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
        Process a complete ROI workflow asynchronously with optimizations.
        
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
            logger.info(f"Starting optimized processing for workflow {workflow_id}")
            
            # Start performance monitoring
            timer_id = performance_monitor.start_workflow_timer(workflow_id)
            
            # Initialize cache connection if not already done
            if not hasattr(cache_service, 'redis_client') or cache_service.redis_client is None:
                await cache_service.connect()
            
            # Read audio file once for caching and memory optimization
            async with aiofiles.open(workflow.audio_file_path, 'rb') as f:
                audio_content = await f.read()
            
            # Record file size for memory tracking
            performance_monitor.record_metric(
                "workflow_file_size", 
                len(audio_content) / (1024*1024), 
                "MB", 
                {"workflow_id": workflow_id}
            )
            
            # Step 1: Transcription (with caching)
            transcription_result = await self._process_transcription_step_cached(db, workflow, audio_content)
            if not transcription_result["success"]:
                await self._fail_workflow(db, workflow, transcription_result["error"])
                return transcription_result
            
            # Determine if translation is needed
            needs_translation = (workflow.language_detected and 
                               workflow.language_detected.lower() in ['spanish', 'es'])
            
            if needs_translation:
                # Run translation and extraction in parallel for Spanish content
                translation_task = self._process_translation_step_cached(db, workflow)
                
                # Wait for translation to complete before extraction
                translation_result = await translation_task
                if not translation_result["success"]:
                    await self._fail_workflow(db, workflow, translation_result["error"])
                    return translation_result
                
                # Now run extraction on the translated text
                extraction_result = await self._process_extraction_step_cached(db, workflow)
            else:
                # For English content, proceed directly to extraction
                translation_result = await self._process_translation_step_cached(db, workflow)
                if not translation_result["success"]:
                    await self._fail_workflow(db, workflow, translation_result["error"])
                    return translation_result
                
                extraction_result = await self._process_extraction_step_cached(db, workflow)
            
            if not extraction_result["success"]:
                await self._fail_workflow(db, workflow, extraction_result["error"])
                return extraction_result
            
            # Mark workflow as completed
            await self._complete_workflow(db, workflow)
            
            # End performance monitoring
            total_duration = performance_monitor.end_workflow_timer(workflow_id, success=True)
            
            logger.info(f"Successfully completed optimized workflow {workflow_id} in {total_duration:.2f}s")
            
            # Clean up audio content from memory
            del audio_content
            
            return {
                "success": True,
                "workflow_id": str(workflow_id),
                "transcription": workflow.transcription,
                "extracted_data": workflow.extracted_data,
                "language": workflow.language_detected,
                "performance_stats": self.performance_stats,
                "processing_time_seconds": total_duration
            }
            
        except Exception as e:
            logger.error(f"Workflow processing failed for {workflow_id}: {e}")
            
            # End performance monitoring with failure
            performance_monitor.end_workflow_timer(workflow_id, success=False)
            
            await self._fail_workflow(db, workflow, str(e))
            return {
                "success": False,
                "error": str(e),
                "workflow_id": str(workflow_id)
            }
    
    async def _process_transcription_step_cached(
        self, 
        db: Session, 
        workflow: ROIWorkflow, 
        audio_content: bytes
    ) -> Dict[str, Any]:
        """Process transcription step with caching optimization"""
        step = next((s for s in workflow.steps if s.step_name == "transcription"), None)
        if not step:
            return {"success": False, "error": "Transcription step not found"}
        
        try:
            # Start step performance monitoring
            performance_monitor.start_step_timer(str(workflow.id), "transcription")
            
            # Update workflow and step status
            workflow.status = WorkflowStatus.TRANSCRIBING.value
            step.start()
            db.commit()
            
            await self._send_status_update(workflow, "Checking cache for transcription...")
            
            # Check cache first
            cached_result = await cache_service.get_transcription_cache(audio_content)
            
            if cached_result:
                logger.info(f"Using cached transcription for workflow {workflow.id}")
                self.performance_stats["cache_hits"] += 1
                
                # Use cached result
                workflow.transcription = cached_result["transcription"]
                workflow.language_detected = cached_result["language"]
                workflow.transcription_confidence = cached_result["confidence"]
                
                # Complete step
                step.complete({
                    "transcription_length": len(cached_result["transcription"]),
                    "language_detected": cached_result["language"],
                    "confidence": cached_result["confidence"],
                    "duration": cached_result.get("duration", 0),
                    "translated": cached_result["language"] == "spanish",
                    "cache_hit": True
                })
                
                db.commit()
                await self._send_status_update(workflow, "Transcription loaded from cache")
                
                # End step monitoring with cache hit
                performance_monitor.end_step_timer(str(workflow.id), "transcription", success=True, cache_hit=True)
                
                return {"success": True}
            
            # Cache miss - process normally
            self.performance_stats["cache_misses"] += 1
            await self._send_status_update(workflow, "Processing transcription...")
            
            # Process transcription
            result = await self.transcription_agent.process({
                "audio_file_path": workflow.audio_file_path,
                "language": None,  # Auto-detect
                "prompt": "This is a business meeting summary with client information."
            })
            
            if result["success"]:
                # Update workflow with results
                workflow.transcription = result["transcription"]
                workflow.language_detected = result["language"]
                workflow.transcription_confidence = result["confidence"]
                
                # Cache the result
                await cache_service.set_transcription_cache(audio_content, result)
                
                # Complete step
                step.complete({
                    "transcription_length": len(result["transcription"]),
                    "language_detected": result["language"],
                    "confidence": result["confidence"],
                    "duration": result["duration"],
                    "translated": result["language"] == "spanish",
                    "cache_hit": False
                })
                
                db.commit()
                await self._send_status_update(workflow, "Transcription completed and cached")
                
                logger.info(f"Transcription completed for workflow {workflow.id}: {len(result['transcription'])} chars, {result['language']}")
                
                # End step monitoring with cache miss
                performance_monitor.end_step_timer(str(workflow.id), "transcription", success=True, cache_hit=False)
                
                return {"success": True}
            else:
                step.fail(result["error"])
                db.commit()
                
                # End step monitoring with failure
                performance_monitor.end_step_timer(str(workflow.id), "transcription", success=False, cache_hit=False)
                
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            step.fail(str(e))
            db.commit()
            
            # End step monitoring with exception
            performance_monitor.end_step_timer(str(workflow.id), "transcription", success=False, cache_hit=False)
            
            logger.error(f"Transcription step failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_translation_step_cached(self, db: Session, workflow: ROIWorkflow) -> Dict[str, Any]:
        """Process translation step with caching optimization"""
        step = next((s for s in workflow.steps if s.step_name == "translation"), None)
        if not step:
            return {"success": False, "error": "Translation step not found"}
        
        try:
            # Update workflow status
            workflow.status = WorkflowStatus.TRANSLATING.value
            step.start()
            db.commit()
            
            # Check if translation is needed
            if workflow.language_detected and workflow.language_detected.lower() in ['spanish', 'es']:
                await self._send_status_update(workflow, "Checking cache for translation...")
                
                # Check cache first
                cached_result = await cache_service.get_translation_cache(
                    workflow.transcription, "es", "en"
                )
                
                if cached_result:
                    logger.info(f"Using cached translation for workflow {workflow.id}")
                    self.performance_stats["cache_hits"] += 1
                    
                    # Store English translation
                    if not workflow.extracted_data:
                        workflow.extracted_data = {}
                    workflow.extracted_data["transcription_english"] = cached_result["translation"]
                    
                    # Complete step
                    step.complete({
                        "translation_length": len(cached_result["translation"]),
                        "source_language": "es",
                        "target_language": "en",
                        "translated": True,
                        "cache_hit": True
                    })
                    
                    db.commit()
                    await self._send_status_update(workflow, "Translation loaded from cache")
                    
                    return {"success": True}
                
                # Cache miss - process normally
                self.performance_stats["cache_misses"] += 1
                await self._send_status_update(workflow, "Translating to English...")
                
                # Process translation
                result = await self.translation_agent.process({
                    "text": workflow.transcription,
                    "source_language": "es",
                    "target_language": "en"
                })
                
                if result["success"]:
                    # Store English translation
                    if not workflow.extracted_data:
                        workflow.extracted_data = {}
                    workflow.extracted_data["transcription_english"] = result["translation"]
                    
                    # Cache the result
                    await cache_service.set_translation_cache(
                        workflow.transcription, "es", "en", result
                    )
                    
                    # Complete step
                    step.complete({
                        "translation_length": len(result["translation"]),
                        "source_language": "es",
                        "target_language": "en",
                        "translated": True,
                        "cache_hit": False
                    })
                    
                    db.commit()
                    await self._send_status_update(workflow, "Translation completed and cached")
                    
                    logger.info(f"Translation completed for workflow {workflow.id}: {len(result['translation'])} chars")
                    
                    return {"success": True}
                else:
                    step.fail(result["error"])
                    db.commit()
                    return {"success": False, "error": result["error"]}
            else:
                # No translation needed - store original in extracted_data
                if not workflow.extracted_data:
                    workflow.extracted_data = {}
                workflow.extracted_data["transcription_english"] = workflow.transcription
                
                # Complete step
                step.complete({
                    "translation_length": len(workflow.transcription),
                    "source_language": workflow.language_detected or "en",
                    "target_language": "en",
                    "translated": False,
                    "cache_hit": False
                })
                
                db.commit()
                await self._send_status_update(workflow, "No translation needed - content already in English")
                
                logger.info(f"No translation needed for workflow {workflow.id}")
                
                return {"success": True}
                
        except Exception as e:
            step.fail(str(e))
            db.commit()
            logger.error(f"Translation step failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_extraction_step_cached(self, db: Session, workflow: ROIWorkflow) -> Dict[str, Any]:
        """Process data extraction step with caching optimization"""
        step = next((s for s in workflow.steps if s.step_name == "extraction"), None)
        if not step:
            return {"success": False, "error": "Extraction step not found"}
        
        try:
            # Update workflow status
            workflow.status = WorkflowStatus.EXTRACTING.value
            step.start()
            db.commit()
            
            await self._send_status_update(workflow, "Checking cache for data extraction...")
            
            # Use English text for extraction (either original or translated)
            extraction_text = workflow.extracted_data.get("transcription_english", workflow.transcription)
            context = f"Audio file: {workflow.audio_file_name}"
            
            # Check cache first
            cached_result = await cache_service.get_extraction_cache(
                extraction_text, workflow.language_detected or "en", context
            )
            
            if cached_result:
                logger.info(f"Using cached extraction for workflow {workflow.id}")
                self.performance_stats["cache_hits"] += 1
                
                # Merge with existing data (preserve translation)
                if workflow.extracted_data:
                    merged_data = workflow.extracted_data.copy()
                    merged_data.update(cached_result["extracted_data"])
                    workflow.extracted_data = merged_data
                else:
                    workflow.extracted_data = cached_result["extracted_data"]
                
                # Complete step
                step.complete({
                    "extraction_confidence": cached_result["confidence"],
                    "language_used": cached_result["language_used"],
                    "fields_extracted": len([k for k, v in cached_result["extracted_data"].items() if v]),
                    "cache_hit": True
                })
                
                db.commit()
                await self._send_status_update(workflow, "Data extraction loaded from cache")
                
                return {"success": True}
            
            # Cache miss - process normally
            self.performance_stats["cache_misses"] += 1
            await self._send_status_update(workflow, "Extracting structured data...")
            
            # Process extraction
            result = await self.extraction_agent.process({
                "transcription": workflow.transcription,
                "language": workflow.language_detected,
                "context": context
            })
            
            if result["success"]:
                # Update workflow with results - preserve existing data like translation
                if workflow.extracted_data:
                    merged_data = workflow.extracted_data.copy()
                    merged_data.update(result["extracted_data"])
                    workflow.extracted_data = merged_data
                else:
                    workflow.extracted_data = result["extracted_data"]
                
                # Cache the result
                await cache_service.set_extraction_cache(
                    extraction_text, workflow.language_detected or "en", context, result
                )
                
                # Complete step
                step.complete({
                    "extraction_confidence": result["confidence"],
                    "language_used": result["language_used"],
                    "fields_extracted": len([k for k, v in result["extracted_data"].items() if v]),
                    "cache_hit": False
                })
                
                db.commit()
                await self._send_status_update(workflow, "Data extraction completed and cached")
                
                logger.info(f"Data extraction completed for workflow {workflow.id}: confidence {result['confidence']:.2f}")
                
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
                
                # English translation will be set in translation step if needed
                
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
    
    async def _process_translation_step(self, db: Session, workflow: ROIWorkflow) -> Dict[str, Any]:
        """Process the translation step (if needed)"""
        step = next((s for s in workflow.steps if s.step_name == "translation"), None)
        if not step:
            return {"success": False, "error": "Translation step not found"}
        
        try:
            # Update workflow status
            workflow.status = WorkflowStatus.TRANSLATING.value
            step.start()
            db.commit()
            
            await self._send_status_update(workflow, "Translating to English...")
            
            # Check if translation is needed
            if workflow.language_detected and workflow.language_detected.lower() in ['spanish', 'es']:
                # Process translation
                result = await self.translation_agent.process({
                    "text": workflow.transcription,
                    "source_language": "es",
                    "target_language": "en"
                })
                
                if result["success"]:
                    # Store English translation in extracted_data for now
                    if not workflow.extracted_data:
                        workflow.extracted_data = {}
                    workflow.extracted_data["transcription_english"] = result["translation"]
                    
                    # Complete step
                    step.complete({
                        "translation_length": len(result["translation"]),
                        "source_language": "es",
                        "target_language": "en",
                        "translated": True
                    })
                    
                    db.commit()
                    
                    await self._send_status_update(workflow, "Translation to English completed")
                    
                    logger.info(
                        f"Translation completed for workflow {workflow.id}: "
                        f"{len(result['translation'])} chars"
                    )
                    
                    return {"success": True}
                else:
                    step.fail(result["error"])
                    db.commit()
                    return {"success": False, "error": result["error"]}
            else:
                # No translation needed - store original in extracted_data
                if not workflow.extracted_data:
                    workflow.extracted_data = {}
                workflow.extracted_data["transcription_english"] = workflow.transcription
                
                # Complete step
                step.complete({
                    "translation_length": len(workflow.transcription),
                    "source_language": workflow.language_detected or "en",
                    "target_language": "en",
                    "translated": False
                })
                
                db.commit()
                
                await self._send_status_update(workflow, "No translation needed - content already in English")
                
                logger.info(f"No translation needed for workflow {workflow.id}")
                
                return {"success": True}
                
        except Exception as e:
            step.fail(str(e))
            db.commit()
            logger.error(f"Translation step failed: {e}")
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
                # Update workflow with results - preserve existing data like translation
                if workflow.extracted_data:
                    # Merge with existing data (like transcription_english from translation step)
                    merged_data = workflow.extracted_data.copy()
                    merged_data.update(result["extracted_data"])
                    workflow.extracted_data = merged_data  # Reassign the whole object
                else:
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
    
    async def initialize_cache(self):
        """Initialize cache service connection"""
        await cache_service.connect()
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        cache_stats = await cache_service.get_cache_stats()
        
        return {
            "workflow_stats": self.performance_stats,
            "cache_stats": cache_stats,
            "cache_hit_rate": (
                self.performance_stats["cache_hits"] / 
                (self.performance_stats["cache_hits"] + self.performance_stats["cache_misses"])
                if (self.performance_stats["cache_hits"] + self.performance_stats["cache_misses"]) > 0
                else 0
            ) * 100
        }
    
    async def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache entries"""
        await cache_service.clear_cache(cache_type)
    
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
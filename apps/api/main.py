from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from datetime import datetime

# Import our custom logging
from core.logging import setup_logging, logger, LogContext
from core.config import config

# Import middleware
from apps.api.middleware.error_handler import register_error_handlers
from apps.api.middleware.request_id import request_id_middleware
from core.config_validator import validate_config_on_startup

# Import routers
from apps.api.routers import gateway, agents, knowledge, events, gmail_oauth, gmail_proxy, gmail_hybrid, gmail_complete, email, communication, workflows, files_simple, files_process, status, health, setup, digest, marketplace
from apps.api.routes import roi_workflow

# Load environment variables
load_dotenv()

# Set up logging
logger = setup_logging(
    service_name="bluelabel-api",
    log_level=config.logging.level,
    log_file=config.logging.file,
    json_format=not config.debug
)

# Create FastAPI app
app = FastAPI(
    title="Bluelabel AIOS v2",
    description="Agentic Intelligence Operating System API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    return await request_id_middleware(request, call_next)

# Register error handlers
register_error_handlers(app)

# Add request logging middleware
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Bluelabel AIOS v2 API")
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"Log level: {config.logging.level}")
    
    # Validate configuration
    # validate_config_on_startup()  # Temporarily disabled for ROI workflow testing

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Bluelabel AIOS v2 API")

# Root endpoint
@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {"message": "Welcome to Bluelabel AIOS v2"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "services": {
            "api": {
                "status": "ok",
                "lastCheck": datetime.utcnow().isoformat()
            },
            "database": {
                "status": "ok",
                "lastCheck": datetime.utcnow().isoformat()
            },
            "redis": {
                "status": "ok",
                "lastCheck": datetime.utcnow().isoformat()
            }
        }
    }


# Include routers
app.include_router(health.router)  # Health check at root level
app.include_router(files_simple.router)  # Files at /api/v1/files
app.include_router(files_process.router)  # File processing
app.include_router(status.router)  # Status at /api/v1/status
app.include_router(gateway.router, prefix="/api/v1/gateway", tags=["gateway"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(gmail_oauth.router, prefix="/api/v1/gmail", tags=["gmail"])
app.include_router(gmail_proxy.router, prefix="/api/v1/gmail-proxy", tags=["gmail-proxy"])
app.include_router(gmail_hybrid.router, prefix="/api/v1/gmail-hybrid", tags=["gmail-hybrid"])
app.include_router(gmail_complete.router, prefix="/api/v1/gmail-complete", tags=["gmail-complete"])
app.include_router(email.router, prefix="/api/v1/email", tags=["email"])
app.include_router(communication.router, prefix="/api/v1/communication", tags=["communication"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(digest.router)  # Digest at /api/v1/digest
app.include_router(marketplace.router, prefix="/api/v1", tags=["marketplace"])  # Marketplace at /api/v1/marketplace
app.include_router(setup.router, tags=["setup"])

# Register agent startup events
from apps.api.routers.agents import startup_event as agent_startup
app.add_event_handler("startup", agent_startup)

# Add ROI workflow endpoints directly to app
try:
    from fastapi import UploadFile, File, HTTPException, BackgroundTasks, Depends
    from sqlalchemy.orm import Session
    from apps.api.dependencies.database import get_db
    from services.roi_workflow_service import ROIWorkflowService
    from datetime import datetime

    # Initialize ROI workflow service
    roi_service = ROIWorkflowService()

    @app.post("/api/workflows/roi-report/")
    async def upload_roi_audio(
        background_tasks: BackgroundTasks,
        audio_file: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """Upload audio file for ROI analysis"""
        try:
            # Validate file
            if not audio_file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
            
            content = await audio_file.read()
            
            # Create workflow
            workflow = await roi_service.create_workflow(
                db=db,
                audio_file_name=audio_file.filename,
                audio_file_content=content,
                user_id=None
            )
            
            # Start background processing
            background_tasks.add_task(
                _process_workflow_async,
                workflow_id=str(workflow.id),
                db_session=db
            )
            
            return {
                "workflow_id": str(workflow.id),
                "status": workflow.status,
                "message": "Audio uploaded successfully. Processing started."
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    @app.post("/roi/upload-batch")
    async def upload_batch_roi_audio(
        background_tasks: BackgroundTasks,
        files: list[UploadFile] = File(...),
        db: Session = Depends(get_db)
    ):
        """Upload multiple audio files for ROI analysis"""
        try:
            if not files:
                raise HTTPException(status_code=400, detail="No files provided")
            
            if len(files) > 10:  # Limit batch size
                raise HTTPException(status_code=400, detail="Maximum 10 files per batch")
            
            results = []
            
            for i, audio_file in enumerate(files):
                try:
                    # Validate file
                    if not audio_file.filename:
                        results.append({
                            "index": i,
                            "filename": "unknown",
                            "success": False,
                            "error": "No filename provided"
                        })
                        continue
                    
                    content = await audio_file.read()
                    
                    # Create workflow
                    workflow = await roi_service.create_workflow(
                        db=db,
                        audio_file_name=audio_file.filename,
                        audio_file_content=content,
                        user_id=None
                    )
                    
                    # Start background processing
                    background_tasks.add_task(
                        _process_workflow_async,
                        workflow_id=str(workflow.id),
                        db_session=db
                    )
                    
                    results.append({
                        "index": i,
                        "filename": audio_file.filename,
                        "workflow_id": str(workflow.id),
                        "status": workflow.status,
                        "success": True
                    })
                    
                except Exception as e:
                    results.append({
                        "index": i,
                        "filename": audio_file.filename if audio_file.filename else "unknown",
                        "success": False,
                        "error": str(e)
                    })
            
            # Return batch results
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]
            
            return {
                "batch_id": f"batch_{len(successful)}_{len(failed)}",
                "total_files": len(files),
                "successful": len(successful),
                "failed": len(failed),
                "results": results,
                "message": f"Batch upload completed: {len(successful)} successful, {len(failed)} failed"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")

    @app.post("/roi/record")
    async def record_roi_audio(
        background_tasks: BackgroundTasks,
        audio_data: UploadFile = File(...),
        db: Session = Depends(get_db)
    ):
        """Accept audio recording from browser MediaRecorder API"""
        try:
            # Validate input
            if not audio_data.filename:
                # Generate filename for recording
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.webm"
            else:
                filename = audio_data.filename
            
            content = await audio_data.read()
            
            # Check if conversion is needed (WebM to MP3)
            if filename.endswith('.webm') or 'webm' in audio_data.content_type:
                # For now, accept WebM directly as OpenAI Whisper supports it
                # In production, you might want to convert to MP3
                pass
            
            # Create workflow
            workflow = await roi_service.create_workflow(
                db=db,
                audio_file_name=filename,
                audio_file_content=content,
                user_id=None
            )
            
            # Start background processing
            background_tasks.add_task(
                _process_workflow_async,
                workflow_id=str(workflow.id),
                db_session=db
            )
            
            return {
                "workflow_id": str(workflow.id),
                "status": workflow.status,
                "filename": filename,
                "message": "Recording uploaded successfully. Processing started."
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Recording upload failed: {str(e)}")

    @app.post("/roi/workflows/merge")
    async def merge_roi_workflows(
        workflow_ids: list[str],
        db: Session = Depends(get_db)
    ):
        """Merge results from multiple workflows"""
        try:
            if not workflow_ids:
                raise HTTPException(status_code=400, detail="No workflow IDs provided")
            
            if len(workflow_ids) > 20:  # Limit merge size
                raise HTTPException(status_code=400, detail="Maximum 20 workflows per merge")
            
            merged_results = {
                "merge_id": f"merge_{len(workflow_ids)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "total_workflows": len(workflow_ids),
                "workflows": [],
                "combined_data": {
                    "contacts": [],
                    "companies": set(),
                    "action_items": [],
                    "high_priority_contacts": [],
                    "languages_detected": set()
                }
            }
            
            for workflow_id in workflow_ids:
                try:
                    # Get workflow status
                    workflow = roi_service.get_workflow_status(db, workflow_id)
                    if not workflow:
                        merged_results["workflows"].append({
                            "workflow_id": workflow_id,
                            "status": "not_found",
                            "error": "Workflow not found"
                        })
                        continue
                    
                    workflow_data = {
                        "workflow_id": workflow_id,
                        "status": workflow.status,
                        "filename": workflow.audio_file_name,
                        "created_at": workflow.created_at.isoformat() if workflow.created_at else None
                    }
                    
                    if workflow.status == "completed" and workflow.extracted_data:
                        extracted = workflow.extracted_data
                        workflow_data["extracted_data"] = extracted
                        
                        # Add to combined data
                        if extracted.get("name") or extracted.get("company"):
                            contact = {
                                "name": extracted.get("name"),
                                "company": extracted.get("company"),
                                "position": extracted.get("position"),
                                "discussion": extracted.get("discussion"),
                                "contact_type": extracted.get("contact_type"),
                                "priority": extracted.get("priority"),
                                "source_workflow": workflow_id,
                                "source_file": workflow.audio_file_name
                            }
                            merged_results["combined_data"]["contacts"].append(contact)
                            
                            if extracted.get("company"):
                                merged_results["combined_data"]["companies"].add(extracted["company"])
                            
                            if extracted.get("priority") == "High":
                                merged_results["combined_data"]["high_priority_contacts"].append(contact)
                        
                        if extracted.get("action_items"):
                            for item in extracted["action_items"]:
                                merged_results["combined_data"]["action_items"].append({
                                    "action": item,
                                    "source_workflow": workflow_id,
                                    "source_contact": extracted.get("name", "Unknown")
                                })
                    
                    if workflow.language_detected:
                        merged_results["combined_data"]["languages_detected"].add(workflow.language_detected)
                    
                    merged_results["workflows"].append(workflow_data)
                    
                except Exception as e:
                    merged_results["workflows"].append({
                        "workflow_id": workflow_id,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Convert sets to lists for JSON serialization
            merged_results["combined_data"]["companies"] = list(merged_results["combined_data"]["companies"])
            merged_results["combined_data"]["languages_detected"] = list(merged_results["combined_data"]["languages_detected"])
            
            # Add summary statistics
            merged_results["summary"] = {
                "total_contacts": len(merged_results["combined_data"]["contacts"]),
                "unique_companies": len(merged_results["combined_data"]["companies"]),
                "total_action_items": len(merged_results["combined_data"]["action_items"]),
                "high_priority_contacts": len(merged_results["combined_data"]["high_priority_contacts"]),
                "languages_detected": merged_results["combined_data"]["languages_detected"]
            }
            
            return merged_results
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")

    @app.get("/roi/recording-template")
    async def get_recording_template():
        """Get voice recording template and prompts"""
        return {
            "template": {
                "greeting": "Please state the following information:",
                "fields": [
                    "Contact name and company",
                    "Their position or role", 
                    "Topics discussed in the meeting",
                    "Whether they are a new prospect or existing client",
                    "Priority level (high, medium, low)",
                    "Next steps or action items"
                ],
                "example": "Hi, I just met with John Smith from TechCorp, he's their CTO. We discussed their new AI project and potential partnership opportunities. This is a new prospect with high priority. Next steps are to send them a proposal by Friday and schedule a technical demo.",
                "tips": [
                    "Speak clearly and at a normal pace",
                    "Include as much detail as possible",
                    "Mention specific company names and contact details",
                    "State the priority level explicitly",
                    "Be specific about next steps and deadlines"
                ]
            },
            "recording_settings": {
                "suggested_format": "webm",
                "max_duration_minutes": 10,
                "sample_rate": 44100,
                "channels": 1
            }
        }

    @app.get("/roi/status/{workflow_id}")
    async def get_roi_workflow_status(
        workflow_id: str,
        db: Session = Depends(get_db)
    ):
        """Get status of a specific ROI workflow"""
        try:
            workflow = roi_service.get_workflow_status(db, workflow_id)
            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")
            
            return {
                "workflow_id": str(workflow.id),
                "status": workflow.status,
                "filename": workflow.audio_file_name,
                "progress_percentage": workflow.get_progress_percentage(),
                "language_detected": workflow.language_detected,
                "transcription": workflow.transcription,
                "extracted_data": workflow.extracted_data,
                "error_message": workflow.error_message,
                "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

    @app.get("/roi/list")
    async def list_roi_workflows(
        limit: int = 50,
        offset: int = 0,
        status: str = None,
        db: Session = Depends(get_db)
    ):
        """List ROI workflows with pagination"""
        try:
            from shared.models.roi_workflow import WorkflowStatus
            
            # Convert status string to enum if provided
            status_enum = None
            if status:
                try:
                    status_enum = WorkflowStatus(status)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
            
            workflows = roi_service.list_workflows(
                db=db,
                status=status_enum,
                limit=min(limit, 100),  # Cap at 100
                offset=offset
            )
            
            # Convert to simple format
            workflow_list = []
            for workflow in workflows:
                workflow_list.append({
                    "workflow_id": str(workflow.id),
                    "status": workflow.status,
                    "filename": workflow.audio_file_name,
                    "progress_percentage": workflow.get_progress_percentage(),
                    "language_detected": workflow.language_detected,
                    "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
                    "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                    "has_results": workflow.extracted_data is not None
                })
            
            return {
                "workflows": workflow_list,
                "count": len(workflow_list),
                "offset": offset,
                "limit": limit
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

    async def _process_workflow_async(workflow_id: str, db_session: Session):
        """Helper function for background workflow processing"""
        try:
            result = await roi_service.process_workflow(db_session, workflow_id)
            return result
        except Exception as e:
            logger.error(f"Background processing failed for workflow {workflow_id}: {e}")
            return {"success": False, "error": str(e)}

    @app.get("/api/workflows/roi-report/health/check")
    async def roi_health_check():
        """ROI workflow health check"""
        try:
            health_status = await roi_service.health_check()
            return {
                "status": "healthy" if all(health_status.values()) else "unhealthy",
                "components": health_status,
                "timestamp": "2025-05-31T03:00:00Z"
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    print("✅ ROI workflow endpoints registered successfully")
    
except Exception as e:
    print(f"❌ Failed to register ROI workflow endpoints: {e}")
    import traceback
    traceback.print_exc()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_DEBUG", "False").lower() == "true",
    )

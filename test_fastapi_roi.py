#!/usr/bin/env python3
"""
Standalone FastAPI server to test ROI workflow endpoints
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from services.roi_workflow_service import ROIWorkflowService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import get_settings

logger = logging.getLogger(__name__)

# Setup
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
workflow_service = ROIWorkflowService()

app = FastAPI(title="ROI Workflow Test API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "ROI workflow test API is running"}

@app.get("/roi/health")
async def roi_health():
    health_status = await workflow_service.health_check()
    return {
        "status": "healthy" if all(health_status.values()) else "unhealthy",
        "components": health_status
    }

@app.post("/roi/upload")
async def upload_audio(audio_file: UploadFile = File(...)):
    """Test audio upload endpoint"""
    print(f"🚀 UPLOAD STARTED: {audio_file.filename}")
    logger.info(f"=== UPLOAD STARTED: {audio_file.filename} ===")
    try:
        # Read file content
        content = await audio_file.read()
        
        # Create workflow
        db = SessionLocal()
        try:
            workflow = await workflow_service.create_workflow(
                db=db,
                audio_file_name=audio_file.filename,
                audio_file_content=content,
                user_id="test_user"
            )
            
            # Start processing the workflow asynchronously
            print(f"🚀 STARTING BACKGROUND TASK FOR: {workflow.id}")
            logger.info(f"Starting background processing for workflow {workflow.id}")
            task = asyncio.create_task(process_workflow_async(str(workflow.id)))
            print(f"🚀 BACKGROUND TASK CREATED: {task}")
            logger.info(f"Background task created: {task}")
            
            return {
                "id": str(workflow.id),
                "status": "uploaded",
                "message": "Audio uploaded successfully. Processing started.",
                "workflowId": str(workflow.id)
            }
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_workflow_async(workflow_id: str):
    """Process workflow asynchronously in background"""
    print(f"🔥 BACKGROUND TASK EXECUTING FOR: {workflow_id}")
    logger.info(f"=== STARTING BACKGROUND PROCESSING FOR {workflow_id} ===")
    try:
        # Create a NEW database session for the background task
        db = SessionLocal()
        try:
            logger.info(f"Created new DB session for workflow {workflow_id}")
            logger.info(f"Starting workflow processing...")
            result = await workflow_service.process_workflow(db, workflow_id)
            logger.info(f"=== WORKFLOW PROCESSING COMPLETED FOR {workflow_id} ===")
            logger.info(f"Result: {result}")
        except Exception as db_error:
            logger.error(f"Database error in workflow {workflow_id}: {db_error}")
            import traceback
            logger.error(f"DB error traceback: {traceback.format_exc()}")
        finally:
            try:
                db.close()
                logger.info(f"Database session closed for workflow {workflow_id}")
            except Exception as close_error:
                logger.error(f"Error closing DB session: {close_error}")
    except Exception as e:
        logger.error(f"=== BACKGROUND PROCESSING FAILED FOR {workflow_id} ===")
        logger.error(f"Error: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

@app.get("/roi/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of a specific workflow"""
    db = SessionLocal()
    try:
        workflow = workflow_service.get_workflow_status(db, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "id": str(workflow.id),
            "status": workflow.status,
            "filename": workflow.audio_file_name,
            "created_at": workflow.created_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "transcription": workflow.transcription,
            "transcription_english": getattr(workflow, 'transcription_english', None) or 
                                        (workflow.extracted_data and workflow.extracted_data.get('transcription_english')) or 
                                        workflow.transcription,
            "extracted_data": workflow.extracted_data,
            "language_detected": workflow.language_detected,
            "error_message": workflow.error_message
        }
    finally:
        db.close()

@app.get("/roi/list")
async def list_workflows():
    """List all workflows"""
    db = SessionLocal()
    try:
        workflows = workflow_service.list_workflows(db, limit=10)
        return {
            "count": len(workflows),
            "workflows": [
                {
                    "id": str(w.id),
                    "status": w.status,
                    "filename": w.audio_file_name,
                    "created_at": w.created_at.isoformat(),
                    "transcription": w.transcription,
                    "transcription_english": getattr(w, 'transcription_english', None) or 
                                            (w.extracted_data and w.extracted_data.get('transcription_english')) or 
                                            w.transcription,
                    "extracted_data": w.extracted_data,
                    "completed_at": w.completed_at.isoformat() if w.completed_at else None
                }
                for w in workflows
            ]
        }
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting ROI Workflow Test API on http://localhost:8001")
    print("📖 API docs available at http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
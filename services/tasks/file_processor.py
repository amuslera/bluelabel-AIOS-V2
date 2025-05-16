"""
Celery task for processing uploaded files.
Implements RULES.md #2: Traceability, #8: Resilience
"""
from celery import Task
import uuid
from datetime import datetime
from typing import Optional

from services.tasks.celery_app import celery_app
from services.storage.storage_factory import get_storage_service
from services.extractors.extractor_factory import get_extractor
from services.analytics import log_event, EventType
from agents.content_mind import ContentMindAgent
from services.knowledge.repository import get_knowledge_repository
from core.config import get_settings


class FileProcessorTask(Task):
    """Custom task class with retry logic"""
    name = "process_file"
    max_retries = 3
    default_retry_delay = 60  # seconds
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        file_id = kwargs.get("file_id")
        user_id = kwargs.get("user_id")
        
        log_event(
            EventType.FILE_FAILED.value,
            user_id=user_id,
            correlation_id=task_id,
            metadata={
                "file_id": file_id,
                "error": str(exc),
                "traceback": str(einfo)
            }
        )


@celery_app.task(
    bind=True,
    base=FileProcessorTask,
    name="process_file",
    max_retries=3,
    default_retry_delay=60
)
def process_file_task(
    self,
    file_id: str,
    user_id: str,
    tenant_id: str
) -> dict:
    """
    Process an uploaded file through the content pipeline.
    
    Steps:
    1. Download file from storage
    2. Extract content based on file type
    3. Process with ContentMind agent
    4. Store in knowledge repository
    5. Update file status
    """
    from core.database import get_database_sync
    
    task_id = self.request.id
    start_time = datetime.utcnow()
    
    try:
        # Log start
        log_event(
            EventType.AGENT_STARTED.value,
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=task_id,
            metadata={
                "file_id": file_id,
                "agent": "FileProcessor",
                "attempt": self.request.retries + 1
            }
        )
        
        # Get database connection
        db = get_database_sync()
        
        # Get file record
        file_record = db.fetch_one_sync(
            """
            SELECT * FROM files 
            WHERE id = %s AND user_id = %s
            """,
            (file_id, user_id)
        )
        
        if not file_record:
            raise ValueError(f"File not found: {file_id}")
        
        # Get storage service
        storage = get_storage_service()
        
        # Download file
        file_data = storage.download_file_sync(
            bucket="uploads",
            key=file_record["storage_path"]
        )
        
        # Get appropriate extractor
        extractor = get_extractor(file_record["content_type"])
        content = extractor.extract(
            file_data,
            filename=file_record["filename"]
        )
        
        # Process with ContentMind
        agent = ContentMindAgent()
        result = agent.process_sync({
            "content": content,
            "metadata": {
                "filename": file_record["filename"],
                "content_type": file_record["content_type"],
                "file_id": file_id,
                "user_id": user_id,
                "tenant_id": tenant_id
            }
        })
        
        # Store in knowledge repository
        knowledge_repo = get_knowledge_repository()
        knowledge_item = knowledge_repo.create_sync(
            user_id=user_id,
            tenant_id=tenant_id,
            title=result.get("title", file_record["filename"]),
            content=content,
            summary=result.get("summary"),
            source_file_id=file_id,
            metadata={
                "entities": result.get("entities", []),
                "topics": result.get("topics", []),
                "sentiment": result.get("sentiment"),
                "agent_output": result
            }
        )
        
        # Update file status
        db.execute_sync(
            """
            UPDATE files 
            SET status = %s, processed_at = %s, knowledge_id = %s
            WHERE id = %s
            """,
            ("completed", datetime.utcnow(), knowledge_item.id, file_id)
        )
        
        # Log success
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        log_event(
            EventType.FILE_PROCESSED.value,
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=task_id,
            metadata={
                "file_id": file_id,
                "knowledge_id": knowledge_item.id,
                "processing_time_ms": duration_ms,
                "content_length": len(content),
                "summary_length": len(result.get("summary", "")),
                "entity_count": len(result.get("entities", [])),
                "topic_count": len(result.get("topics", []))
            }
        )
        
        # Publish event for other services
        from core.event_bus import get_event_bus
        event_bus = get_event_bus()
        event_bus.publish(
            "file.processed",
            {
                "file_id": file_id,
                "knowledge_id": knowledge_item.id,
                "user_id": user_id,
                "tenant_id": tenant_id
            }
        )
        
        return {
            "status": "success",
            "file_id": file_id,
            "knowledge_id": knowledge_item.id,
            "processing_time_ms": duration_ms
        }
        
    except Exception as e:
        # Log error
        log_event(
            EventType.FILE_FAILED.value,
            user_id=user_id,
            tenant_id=tenant_id,
            correlation_id=task_id,
            metadata={
                "file_id": file_id,
                "error": str(e),
                "attempt": self.request.retries + 1
            }
        )
        
        # Update file status
        db = get_database_sync()
        db.execute_sync(
            """
            UPDATE files 
            SET status = %s, error_message = %s, processed_at = %s
            WHERE id = %s
            """,
            ("failed", str(e), datetime.utcnow(), file_id)
        )
        
        # Retry if transient error
        if self.request.retries < self.max_retries:
            if "timeout" in str(e).lower() or "connection" in str(e).lower():
                raise self.retry(
                    exc=e,
                    countdown=self.default_retry_delay * (self.request.retries + 1)
                )
        
        raise
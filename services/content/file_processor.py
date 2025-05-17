"""
File Processing Service
Processes uploaded files and extracts content
"""
from typing import Dict, Any
import os
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.content.pdf_extractor import get_pdf_extractor
from services.storage.storage_factory import get_storage
from services.knowledge.repository import get_knowledge_repository
from core.logging import setup_logging
from core.event_bus import EventBus, Event, EventMetadata

logger = setup_logging(service_name="file-processor")


class FileProcessor:
    """Process uploaded files and extract content"""
    
    def __init__(self, db: Session, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus
        self.pdf_extractor = get_pdf_extractor()
        self.storage = get_storage()
        self.knowledge_repo = get_knowledge_repository()
    
    async def process_file(self, file_id: str, user_id: str) -> Dict[str, Any]:
        """
        Process an uploaded file
        
        Args:
            file_id: ID of the file to process
            user_id: ID of the user who owns the file
            
        Returns:
            Processing result
        """
        result = {
            "success": False,
            "file_id": file_id,
            "knowledge_id": None,
            "error": None
        }
        
        try:
            # Get file record
            file_record = self.db.execute(
                text("""
                SELECT * FROM files 
                WHERE id = :file_id AND user_id = :user_id
                """),
                {"file_id": file_id, "user_id": user_id}
            ).first()
            
            if not file_record:
                result["error"] = "File not found"
                return result
            
            # Update status to processing
            self.db.execute(
                text("""
                UPDATE files 
                SET status = 'processing', processed_at = :processed_at
                WHERE id = :file_id
                """),
                {"file_id": file_id, "processed_at": datetime.utcnow()}
            )
            self.db.commit()
            
            # Emit processing started event
            await self.event_bus.emit(Event(
                metadata=EventMetadata(
                    event_type="file_processing_started",
                    correlation_id=file_id,
                    tenant_id=file_record.tenant_id
                ),
                payload={
                    "file_id": file_id,
                    "filename": file_record.filename,
                    "user_id": user_id
                }
            ))
            
            # Download file from storage
            local_path = f"/tmp/{file_id}_{file_record.filename}"
            
            await self.storage.download_file(
                bucket="uploads",
                key=file_record.storage_path,
                destination=local_path
            )
            
            # Process based on content type
            extracted_content = None
            
            if file_record.content_type == "application/pdf":
                extraction_result = self.pdf_extractor.extract_text(local_path)
                
                if extraction_result["success"]:
                    extracted_content = extraction_result["text"]
                else:
                    raise Exception(extraction_result["error"])
            
            elif file_record.content_type.startswith("text/"):
                # Handle text files
                with open(local_path, 'r', encoding='utf-8') as f:
                    extracted_content = f.read()
            
            else:
                raise Exception(f"Unsupported file type: {file_record.content_type}")
            
            # Store in knowledge repository
            if extracted_content:
                knowledge_item = await self.knowledge_repo.create_knowledge_item(
                    user_id=user_id,
                    tenant_id=file_record.tenant_id,
                    source_type="file",
                    source_id=file_id,
                    content=extracted_content,
                    metadata={
                        "filename": file_record.filename,
                        "content_type": file_record.content_type,
                        "file_size": file_record.size
                    }
                )
                
                result["knowledge_id"] = knowledge_item.id
                
                # Update file record with knowledge ID
                self.db.execute(
                    text("""
                    UPDATE files 
                    SET status = 'completed', knowledge_id = :knowledge_id
                    WHERE id = :file_id
                    """),
                    {"file_id": file_id, "knowledge_id": knowledge_item.id}
                )
                self.db.commit()
                
                result["success"] = True
                
                # Emit processing completed event
                await self.event_bus.emit(Event(
                    metadata=EventMetadata(
                        event_type="file_processing_completed",
                        correlation_id=file_id,
                        tenant_id=file_record.tenant_id
                    ),
                    payload={
                        "file_id": file_id,
                        "knowledge_id": knowledge_item.id,
                        "user_id": user_id
                    }
                ))
            
            # Clean up temporary file
            if os.path.exists(local_path):
                os.remove(local_path)
                
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {str(e)}")
            result["error"] = str(e)
            
            # Update file status to failed
            self.db.execute(
                text("""
                UPDATE files 
                SET status = 'failed', error_message = :error
                WHERE id = :file_id
                """),
                {"file_id": file_id, "error": str(e)}
            )
            self.db.commit()
            
            # Emit processing failed event
            await self.event_bus.emit(Event(
                metadata=EventMetadata(
                    event_type="file_processing_failed",
                    correlation_id=file_id,
                    tenant_id=file_record.tenant_id if file_record else None
                ),
                payload={
                    "file_id": file_id,
                    "error": str(e),
                    "user_id": user_id
                }
            ))
        
        return result
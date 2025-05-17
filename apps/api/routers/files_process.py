"""
File processing endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.schemas.base import User
from apps.api.dependencies.auth import get_current_user
from apps.api.dependencies.database import get_db
from services.content.pdf_extractor import get_pdf_extractor

router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post("/{file_id}/process")
async def process_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process a file and extract text - synchronous for MVP
    """
    try:
        # Get file record
        file_record = db.execute(
            text("""
            SELECT * FROM files 
            WHERE id = :file_id AND user_id = :user_id
            """),
            {"file_id": file_id, "user_id": current_user.id}
        ).first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # For MVP, we'll simulate processing
        # In production, this would download from storage and process
        
        # Update status to processing
        db.execute(
            text("""
            UPDATE files 
            SET status = 'processing'
            WHERE id = :file_id
            """),
            {"file_id": file_id}
        )
        db.commit()
        
        # Simulate text extraction
        extracted_text = f"""
        Simulated extraction from {file_record.filename}
        
        This is a placeholder for the actual content that would be extracted
        from the PDF file. In a real implementation, we would:
        
        1. Download the file from storage (MinIO/S3)
        2. Use the PDF extractor to get the text
        3. Store the text in the knowledge repository
        4. Update the file status
        
        File size: {file_record.size} bytes
        Content type: {file_record.content_type}
        """
        
        # Update status to completed
        db.execute(
            text("""
            UPDATE files 
            SET status = 'completed'
            WHERE id = :file_id
            """),
            {"file_id": file_id}
        )
        db.commit()
        
        return {
            "file_id": file_id,
            "status": "completed",
            "extracted_text": extracted_text,
            "text_length": len(extracted_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        
        # Update status to failed
        db.execute(
            text("""
            UPDATE files 
            SET status = 'failed', error_message = :error
            WHERE id = :file_id
            """),
            {"file_id": file_id, "error": str(e)}
        )
        db.commit()
        
        raise HTTPException(status_code=500, detail=str(e))
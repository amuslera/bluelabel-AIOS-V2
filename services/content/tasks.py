"""
Celery tasks for content processing
"""
from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.content.file_processor import FileProcessor
from core.event_bus import get_event_bus
from core.config import get_settings
from core.logging import setup_logging

logger = setup_logging(service_name="content-tasks")


@shared_task
def process_file_task(file_id: str, user_id: str):
    """
    Celery task to process a file asynchronously
    
    Args:
        file_id: ID of the file to process
        user_id: ID of the user who owns the file
    """
    settings = get_settings()
    
    # Create database session
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Get event bus
        event_bus = get_event_bus()
        
        # Create processor
        processor = FileProcessor(db, event_bus)
        
        # Process file
        logger.info(f"Processing file {file_id} for user {user_id}")
        result = processor.process_file(file_id, user_id)
        
        if result["success"]:
            logger.info(f"Successfully processed file {file_id}")
        else:
            logger.error(f"Failed to process file {file_id}: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in file processing task: {str(e)}")
        raise
    finally:
        db.close()
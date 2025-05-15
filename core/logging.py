"""
Centralized logging configuration for Bluelabel AIOS v2
"""
import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that adds extra fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['service'] = os.getenv('SERVICE_NAME', 'bluelabel-aios')
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['level'] = record.levelname
        
        # Add tenant_id if available in context
        if hasattr(record, 'tenant_id'):
            log_record['tenant_id'] = record.tenant_id

def setup_logging(
    service_name: str = "bluelabel-aios",
    log_level: str = None,
    log_file: str = None,
    json_format: bool = True
) -> logging.Logger:
    """
    Set up structured logging for the application
    
    Args:
        service_name: Name of the service for logging context
        log_level: Logging level (INFO, DEBUG, WARNING, ERROR)
        log_file: Path to log file (optional)
        json_format: Whether to use JSON format for logs
    
    Returns:
        Configured logger instance
    """
    # Get log level from env or parameter
    level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    if json_format:
        # JSON format for production
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

class LogContext:
    """Context manager for adding context to log records"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.context = kwargs
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwds):
            record = self.old_factory(*args, **kwds)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)

# Global logger instance
logger = setup_logging()
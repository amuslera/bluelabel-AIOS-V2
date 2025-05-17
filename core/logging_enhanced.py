"""
Enhanced logging system for Bluelabel AIOS
Provides structured logging with request tracking and error context
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
import uuid
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """Formats logs as structured JSON for better parsing"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
            
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_data, default=str)

class RequestContextFilter(logging.Filter):
    """Adds request context to all log records"""
    
    def filter(self, record):
        # Add request ID if available
        from contextvars import ContextVar
        request_id_var = ContextVar('request_id', default=None)
        
        request_id = request_id_var.get()
        if request_id:
            record.request_id = request_id
            
        return True

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = "logs/bluelabel_aios.log",
    json_logs: bool = True
) -> logging.Logger:
    """
    Set up the logging system
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for stdout only)
        json_logs: Whether to use JSON format for logs
        
    Returns:
        Configured logger instance
    """
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Create formatter
    if json_logs:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)
    
    # Return logger for the application
    return logging.getLogger("bluelabel-aios")

class LogContext:
    """Context manager for adding extra data to logs"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra_data = kwargs
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                f"Error in context: {exc_type.__name__}: {exc_val}",
                exc_info=True,
                extra={'extra_data': self.extra_data}
            )
            
    def log(self, level: str, message: str, **kwargs):
        """Log with context data"""
        extra_data = {**self.extra_data, **kwargs}
        log_func = getattr(self.logger, level.lower())
        log_func(message, extra={'extra_data': extra_data})

# Create application logger
logger = setup_logging()
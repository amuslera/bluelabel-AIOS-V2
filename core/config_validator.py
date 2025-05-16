"""
Configuration validation to ensure all required settings are present and valid.
Implements RULES.md #12: Resource Limits
"""
import os
import sys
from typing import List, Tuple
from pydantic import ValidationError

from core.config import Settings, get_settings


class ConfigValidator:
    """Validate configuration on startup"""
    
    @staticmethod
    def validate() -> Tuple[bool, List[str]]:
        """
        Validate all configuration settings.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            settings = get_settings()
        except ValidationError as e:
            return False, [f"Configuration validation failed: {str(e)}"]
        
        # Check required API keys
        if settings.LLM_ENABLED:
            if not any([
                settings.OPENAI_API_KEY,
                settings.ANTHROPIC_API_KEY,
                settings.GOOGLE_GENERATIVEAI_API_KEY
            ]):
                errors.append("LLM_ENABLED is True but no LLM API keys are configured")
        
        # Check database connection
        if not settings.DATABASE_URL:
            errors.append("DATABASE_URL is not configured")
        
        # Check Redis connection
        if not settings.REDIS_URL:
            errors.append("REDIS_URL is not configured")
        
        # Check file size limits
        if settings.MAX_FILE_SIZE_MB <= 0:
            errors.append("MAX_FILE_SIZE_MB must be greater than 0")
        
        # Check storage configuration
        storage_backend = os.getenv("STORAGE_BACKEND", "minio")
        if storage_backend == "s3":
            if not all([
                os.getenv("AWS_ACCESS_KEY_ID"),
                os.getenv("AWS_SECRET_ACCESS_KEY"),
                os.getenv("AWS_BUCKET_NAME")
            ]):
                errors.append("S3 storage configured but AWS credentials missing")
        elif storage_backend == "r2":
            if not all([
                os.getenv("R2_ACCOUNT_ID"),
                os.getenv("R2_ACCESS_KEY_ID"),
                os.getenv("R2_SECRET_ACCESS_KEY")
            ]):
                errors.append("R2 storage configured but Cloudflare credentials missing")
        
        # Check email configuration
        if os.getenv("EMAIL_BACKEND") == "resend":
            if not os.getenv("RESEND_API_KEY"):
                errors.append("Resend email backend configured but API key missing")
        
        # Check JWT secret
        if len(settings.JWT_SECRET_KEY) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters long")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def check_runtime_dependencies() -> Tuple[bool, List[str]]:
        """
        Check runtime dependencies like database connectivity.
        """
        errors = []
        
        # Check Redis connection
        try:
            import redis
            r = redis.from_url(get_settings().REDIS_URL)
            r.ping()
        except Exception as e:
            errors.append(f"Redis connection failed: {str(e)}")
        
        # Check database connection
        try:
            import databases
            database = databases.Database(get_settings().DATABASE_URL)
            # Note: Actual connection test would be async
        except Exception as e:
            errors.append(f"Database configuration error: {str(e)}")
        
        return len(errors) == 0, errors


def validate_config_on_startup():
    """
    Validate configuration when the application starts.
    Exit with error if configuration is invalid.
    """
    # Check static configuration
    is_valid, errors = ConfigValidator.validate()
    
    if not is_valid:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Check runtime dependencies
    is_valid, errors = ConfigValidator.check_runtime_dependencies()
    
    if not is_valid:
        print("Runtime dependency check failed:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease ensure all services are running and properly configured.")
        sys.exit(1)
    
    print("Configuration validation passed ✓")
"""
Health check endpoint and system monitoring
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import asyncio
import time
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import get_settings
from core.logging_enhanced import logger

router = APIRouter()
settings = get_settings()

# Global app start time for uptime calculation
APP_START_TIME = datetime.now(timezone.utc)
APP_VERSION = "0.1.0-mvp"

# Simple database session for health checks
def get_engine():
    try:
        return create_async_engine(settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        return None

engine = get_engine()
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) if engine else None

async def get_db():
    if async_session_maker:
        async with async_session_maker() as session:
            yield session
    else:
        yield None


class HealthChecker:
    """Service to check health of various system components"""
    
    async def check_database(self, db: Optional[AsyncSession]) -> Dict[str, Any]:
        """Check database connectivity"""
        if not db:
            return {
                "status": "unhealthy",
                "message": "Database session not available"
            }
        
        try:
            start = time.time()
            result = await db.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000  # ms
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity (simulated for MVP)"""
        # In MVP, Redis is simulated in-memory
        return {
            "status": "healthy",
            "message": "Redis simulation active",
            "mode": "in-memory"
        }
    
    async def check_storage(self) -> Dict[str, Any]:
        """Check storage service availability"""
        # For MVP, check local filesystem
        try:
            import os
            storage_path = settings.LOCAL_STORAGE_PATH
            if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
                return {
                    "status": "healthy",
                    "message": "Storage accessible",
                    "type": "local",
                    "path": storage_path
                }
            else:
                return {
                    "status": "degraded",
                    "message": "Storage path not fully accessible",
                    "path": storage_path
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Storage check failed: {str(e)}"
            }
    
    async def check_gmail(self) -> Dict[str, Any]:
        """Check Gmail OAuth status"""
        try:
            # Basic check - verify we have credentials configured
            if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET:
                return {
                    "status": "healthy",
                    "message": "Gmail credentials configured",
                    "oauth_configured": True
                }
            else:
                return {
                    "status": "degraded",
                    "message": "Gmail credentials not configured",
                    "oauth_configured": False
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Gmail check failed: {str(e)}"
            }
    
    async def check_llm_provider(self) -> Dict[str, Any]:
        """Check LLM provider availability"""
        try:
            # Check if API key is configured
            provider = settings.DEFAULT_LLM_PROVIDER
            
            if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
                return {
                    "status": "healthy",
                    "message": "LLM provider configured",
                    "provider": "anthropic",
                    "api_key_present": True
                }
            elif provider == "openai" and settings.OPENAI_API_KEY:
                return {
                    "status": "healthy",
                    "message": "LLM provider configured",
                    "provider": "openai",
                    "api_key_present": True
                }
            else:
                return {
                    "status": "degraded",
                    "message": "LLM provider not fully configured",
                    "provider": provider,
                    "api_key_present": False
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"LLM check failed: {str(e)}"
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system resource information"""
        try:
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory": {
                    "percent": memory.percent,
                    "available_mb": round(memory.available / 1024 / 1024),
                    "total_mb": round(memory.total / 1024 / 1024)
                },
                "disk": {
                    "percent": disk.percent,
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2)
                }
            }
        except Exception as e:
            logger.error(f"System info check failed: {str(e)}")
            return {}


health_checker = HealthChecker()


@router.get("/health", response_model=Dict[str, Any])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check endpoint
    
    Returns system status including:
    - Overall health status
    - Individual component status
    - System resources
    - Uptime and version info
    """
    
    # Calculate uptime
    uptime_seconds = (datetime.now(timezone.utc) - APP_START_TIME).total_seconds()
    
    # Run all health checks concurrently
    checks = await asyncio.gather(
        health_checker.check_database(db),
        health_checker.check_redis(),
        health_checker.check_storage(),
        health_checker.check_gmail(),
        health_checker.check_llm_provider(),
        return_exceptions=True
    )
    
    # Process results
    components = {
        "database": checks[0] if not isinstance(checks[0], Exception) else {"status": "error", "message": str(checks[0])},
        "redis": checks[1] if not isinstance(checks[1], Exception) else {"status": "error", "message": str(checks[1])},
        "storage": checks[2] if not isinstance(checks[2], Exception) else {"status": "error", "message": str(checks[2])},
        "gmail": checks[3] if not isinstance(checks[3], Exception) else {"status": "error", "message": str(checks[3])},
        "llm": checks[4] if not isinstance(checks[4], Exception) else {"status": "error", "message": str(checks[4])}
    }
    
    # Determine overall status
    statuses = [comp.get("status", "unknown") for comp in components.values()]
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
    elif any(s == "unhealthy" or s == "error" for s in statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    # Get system info
    system_info = health_checker.get_system_info()
    
    return {
        "status": overall_status,
        "version": APP_VERSION,
        "uptime_seconds": round(uptime_seconds),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": components,
        "system": system_info
    }


@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    return {"status": "ok", "version": APP_VERSION}
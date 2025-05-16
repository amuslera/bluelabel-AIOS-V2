"""
Health check endpoints for monitoring.
Implements RULES.md #5: Observability
"""
from fastapi import APIRouter, Depends
from datetime import datetime
import psutil
import os

from core.config import get_settings
from apps.api.dependencies.database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "unknown")
    }


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe(
    # redis=Depends(get_redis),  # TODO: Add when Redis is required
    db=Depends(get_db)
):
    """
    Kubernetes readiness probe.
    Checks if all dependencies are available.
    """
    checks = {
        "database": False,
        "redis": False,
        "storage": False
    }
    
    # Check database
    try:
        await db.fetch_one("SELECT 1")
        checks["database"] = True
    except:
        pass
    
    # Check Redis (simulation mode - always true)
    # TODO: Uncomment when Redis is required
    # try:
    #     await redis.ping()
    #     checks["redis"] = True
    # except:
    #     pass
    checks["redis"] = True  # Simulation mode
    
    # Check storage (MinIO/S3/R2)
    try:
        # Simple check - actual implementation would verify bucket access
        checks["storage"] = True
    except:
        pass
    
    all_ready = all(checks.values())
    
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks
    }


@router.get("/detailed")
async def detailed_health(
    settings=Depends(get_settings),
    # redis=Depends(get_redis),  # TODO: Add when Redis is required
    db=Depends(get_db)
):
    """
    Detailed health check with system metrics.
    """
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database check
    db_status = "unknown"
    try:
        result = await db.fetch_one("SELECT version()")
        db_status = "connected"
        db_version = result["version"]
    except Exception as e:
        db_status = f"error: {str(e)}"
        db_version = None
    
    # Redis check (simulation mode)
    # TODO: Uncomment when Redis is required
    # redis_status = "unknown"
    # try:
    #     await redis.ping()
    #     redis_status = "connected"
    #     redis_info = await redis.info()
    #     redis_version = redis_info.get("redis_version", "unknown")
    # except Exception as e:
    #     redis_status = f"error: {str(e)}"
    #     redis_version = None
    redis_status = "simulated"
    redis_version = "simulation"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "unknown"),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        },
        "dependencies": {
            "database": {
                "status": db_status,
                "version": db_version
            },
            "redis": {
                "status": redis_status,
                "version": redis_version
            }
        },
        "configuration": {
            "debug": settings.DEBUG,
            "environment": settings.ENVIRONMENT,
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "llm_enabled": settings.LLM_ENABLED
        }
    }
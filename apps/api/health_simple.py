"""
Simplified health check endpoint that works without database dependency
"""

from datetime import datetime, timezone
from typing import Dict, Any
import asyncio
import time
import psutil
from fastapi import APIRouter

from core.config import get_settings
from core.logging_enhanced import logger

router = APIRouter()
settings = get_settings()

# Global app start time for uptime calculation
APP_START_TIME = datetime.now(timezone.utc)
APP_VERSION = "0.1.0-mvp"


class SimpleHealthChecker:
    """Simple health checker without database dependency"""
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity (simulated)"""
        # For MVP, we'll just check if configuration exists
        if settings.DATABASE_URL:
            return {
                "status": "configured",
                "message": "Database URL configured (connection not tested)",
                "url_prefix": settings.DATABASE_URL[:20] + "..."
            }
        else:
            return {
                "status": "not_configured",
                "message": "Database URL not configured"
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity (simulated for MVP)"""
        return {
            "status": "healthy",
            "message": "Redis simulation active",
            "mode": "in-memory"
        }
    
    async def check_storage(self) -> Dict[str, Any]:
        """Check storage service availability"""
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
                # Try to create the directory
                os.makedirs(storage_path, exist_ok=True)
                return {
                    "status": "healthy",
                    "message": "Storage directory created",
                    "type": "local",
                    "path": storage_path
                }
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Storage check partial: {str(e)}",
                "type": "local"
            }
    
    async def check_gmail(self) -> Dict[str, Any]:
        """Check Gmail OAuth status"""
        if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET:
            return {
                "status": "healthy",
                "message": "Gmail credentials configured",
                "oauth_configured": True
            }
        else:
            return {
                "status": "not_configured",
                "message": "Gmail credentials not configured",
                "oauth_configured": False
            }
    
    async def check_llm_provider(self) -> Dict[str, Any]:
        """Check LLM provider availability"""
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
                "status": "not_configured",
                "message": "LLM provider not configured",
                "provider": provider,
                "api_key_present": False
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system resource information"""
        try:
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
            return {"error": str(e)}


health_checker = SimpleHealthChecker()


@router.get("/health")
async def health_check():
    """
    Health check endpoint without database dependency
    """
    
    # Calculate uptime
    uptime_seconds = (datetime.now(timezone.utc) - APP_START_TIME).total_seconds()
    
    # Run all health checks concurrently
    checks = await asyncio.gather(
        health_checker.check_database(),
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
    if any(s == "error" for s in statuses):
        overall_status = "unhealthy"
    elif any(s == "warning" or s == "not_configured" for s in statuses):
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
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
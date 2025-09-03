"""
Health check endpoints for monitoring and load balancing
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import time
import psutil
import asyncio

from ..core.config import settings
from ..core.database import get_db_health
from ..core.redis_client import get_redis_health
from ..models.common import HealthResponse
from ..core.logging_config import get_context_logger

router = APIRouter()
logger = get_context_logger(__name__)

# Track application startup time
startup_time = time.time()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    
    services = {}
    overall_status = "healthy"
    
    try:
        # Check database health
        db_healthy, db_status = await get_db_health()
        services["database"] = db_status
        
        if not db_healthy:
            overall_status = "degraded"
        
    except Exception as e:
        services["database"] = f"error: {str(e)}"
        overall_status = "unhealthy"
    
    try:
        # Check Redis health
        redis_healthy, redis_status = await get_redis_health()
        services["redis"] = redis_status
        
        if not redis_healthy:
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
    except Exception as e:
        services["redis"] = f"error: {str(e)}"
        overall_status = "unhealthy" if overall_status == "healthy" else overall_status
    
    # Calculate uptime
    uptime = time.time() - startup_time
    
    return HealthResponse(
        status=overall_status,
        services=services,
        uptime=uptime
    )


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics"""
    
    try:
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check services
        db_healthy, db_status = await get_db_health()
        redis_healthy, redis_status = await get_redis_health()
        
        # Test async operations
        start_time = time.time()
        await asyncio.sleep(0.001)  # Tiny async operation
        async_latency = (time.time() - start_time) * 1000
        
        uptime = time.time() - startup_time
        
        return {
            "status": "healthy" if db_healthy and redis_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime,
            "system": {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory.percent,
                "memory_available_mb": memory.available // 1024 // 1024,
                "disk_usage_percent": disk.percent,
                "disk_free_gb": disk.free // 1024 // 1024 // 1024
            },
            "services": {
                "database": {
                    "status": db_status,
                    "healthy": db_healthy
                },
                "redis": {
                    "status": redis_status,
                    "healthy": redis_healthy
                }
            },
            "performance": {
                "async_latency_ms": async_latency
            },
            "environment": {
                "app_name": settings.APP_NAME,
                "app_version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG
            }
        }
        
    except Exception as e:
        logger.error(
            "❌ Detailed health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=503,
            detail="Health check failed"
        )


@router.get("/ready")
async def readiness_probe():
    """Kubernetes readiness probe endpoint"""
    
    try:
        # Check critical services
        db_healthy, _ = await get_db_health()
        redis_healthy, _ = await get_redis_health()
        
        if db_healthy and redis_healthy:
            return {"status": "ready"}
        else:
            raise HTTPException(
                status_code=503,
                detail="Service not ready"
            )
            
    except Exception as e:
        logger.error(
            "❌ Readiness probe failed",
            extra={"error": str(e)}
        )
        
        raise HTTPException(
            status_code=503,
            detail="Service not ready"
        )


@router.get("/live")
async def liveness_probe():
    """Kubernetes liveness probe endpoint"""
    
    # Basic liveness check - just return 200 if the process is running
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
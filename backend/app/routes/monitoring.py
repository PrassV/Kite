"""
Monitoring and metrics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ..routes.auth import get_current_user
from ..utils.monitoring import performance_monitor
from ..core.config import settings
from ..core.logging_config import get_context_logger

router = APIRouter()
logger = get_context_logger(__name__)


@router.get("/metrics")
async def get_system_metrics(current_user: dict = Depends(get_current_user)):
    """Get comprehensive system metrics (requires authentication)"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        "📊 Metrics requested",
        extra={"user_id": user_id}
    )
    
    try:
        metrics = await performance_monitor.get_comprehensive_metrics()
        
        logger.info(
            "✅ Metrics collected successfully",
            extra={"user_id": user_id}
        )
        
        return metrics
        
    except Exception as e:
        logger.error(
            "❌ Failed to collect metrics",
            extra={
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect metrics"
        )


@router.get("/metrics/system")
async def get_system_only_metrics(current_user: dict = Depends(get_current_user)):
    """Get system metrics only"""
    
    user_id = current_user.get("user_id")
    
    try:
        metrics = performance_monitor.get_system_metrics()
        return {"system": metrics}
        
    except Exception as e:
        logger.error(
            "❌ Failed to collect system metrics",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect system metrics"
        )


@router.get("/metrics/requests")
async def get_request_metrics(current_user: dict = Depends(get_current_user)):
    """Get request performance metrics"""
    
    try:
        metrics = performance_monitor.get_request_metrics()
        return {"requests": metrics}
        
    except Exception as e:
        logger.error(
            "❌ Failed to collect request metrics",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect request metrics"
        )


@router.get("/metrics/analysis")
async def get_analysis_metrics(current_user: dict = Depends(get_current_user)):
    """Get analysis performance metrics"""
    
    try:
        metrics = performance_monitor.get_analysis_metrics()
        return {"analysis": metrics}
        
    except Exception as e:
        logger.error(
            "❌ Failed to collect analysis metrics",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect analysis metrics"
        )


@router.get("/metrics/redis")
async def get_redis_metrics(current_user: dict = Depends(get_current_user)):
    """Get Redis performance metrics"""
    
    try:
        metrics = await performance_monitor.get_redis_metrics()
        return {"redis": metrics}
        
    except Exception as e:
        logger.error(
            "❌ Failed to collect Redis metrics",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect Redis metrics"
        )


# Public endpoint for basic metrics (no authentication required)
@router.get("/public/stats")
async def get_public_stats():
    """Get public statistics (no sensitive information)"""
    
    try:
        uptime = performance_monitor.get_uptime()
        request_metrics = performance_monitor.get_request_metrics()
        analysis_metrics = performance_monitor.get_analysis_metrics()
        
        # Calculate aggregate stats without sensitive details
        total_requests = sum(m.get("total_requests", 0) for m in request_metrics.values())
        total_analyses = sum(m.get("total_analyses", 0) for m in analysis_metrics.values())
        
        successful_analyses = sum(m.get("successful_analyses", 0) for m in analysis_metrics.values())
        success_rate = (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
        
        # Count unique symbols analyzed across all analysis types
        all_symbols = set()
        for metrics in analysis_metrics.values():
            symbols = metrics.get("symbols_analyzed", [])
            if isinstance(symbols, list):
                all_symbols.update(symbols)
        
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime_hours": round(uptime / 3600, 2),
            "statistics": {
                "total_requests_processed": total_requests,
                "total_analyses_performed": total_analyses,
                "analysis_success_rate_percent": round(success_rate, 1),
                "unique_symbols_analyzed": len(all_symbols),
                "analysis_types_available": len(analysis_metrics)
            },
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(
            "❌ Failed to collect public stats",
            extra={"error": str(e)},
            exc_info=True
        )
        
        # Return basic info even if metrics collection fails
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "status": "operational",
            "metrics_error": "Could not collect detailed statistics"
        }
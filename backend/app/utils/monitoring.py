"""
Monitoring and metrics collection utilities
"""

import time
import psutil
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
from functools import wraps

from ..core.config import settings
from ..core.logging_config import get_context_logger
from ..core.redis_client import get_redis_client, set_cache, get_cache

logger = get_context_logger(__name__)


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_metrics = {}
        self.analysis_metrics = {}
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network I/O
            try:
                network = psutil.net_io_counters()
                network_metrics = {
                    "bytes_sent": network.bytes_sent,
                    "bytes_received": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_received": network.packets_recv
                }
            except Exception:
                network_metrics = {}
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": self.get_uptime(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "load_avg": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
                },
                "memory": {
                    "total_mb": memory.total // 1024 // 1024,
                    "available_mb": memory.available // 1024 // 1024,
                    "used_mb": memory.used // 1024 // 1024,
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total // 1024 // 1024 // 1024,
                    "free_gb": disk.free // 1024 // 1024 // 1024,
                    "used_gb": disk.used // 1024 // 1024 // 1024,
                    "usage_percent": round((disk.used / disk.total) * 100, 2)
                },
                "network": network_metrics
            }
            
        except Exception as e:
            logger.error(
                "❌ Failed to collect system metrics",
                extra={"error": str(e)},
                exc_info=True
            )
            return {"error": str(e)}
    
    async def get_redis_metrics(self) -> Dict[str, Any]:
        """Get Redis performance metrics"""
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return {"status": "disabled"}
            
            info = await redis_client.info()
            
            return {
                "status": "connected",
                "version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_mb": info.get("used_memory", 0) // 1024 // 1024,
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0)
            }
            
        except Exception as e:
            logger.error(
                "❌ Failed to collect Redis metrics",
                extra={"error": str(e)}
            )
            return {"status": "error", "error": str(e)}
    
    async def record_request_metric(
        self, 
        endpoint: str, 
        method: str, 
        status_code: int, 
        processing_time: float,
        user_id: Optional[str] = None
    ):
        """Record request performance metrics"""
        
        metric_key = f"{method}:{endpoint}"
        
        # Update in-memory metrics
        if metric_key not in self.request_metrics:
            self.request_metrics[metric_key] = {
                "total_requests": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0,
                "status_codes": {},
                "last_request": None
            }
        
        metrics = self.request_metrics[metric_key]
        metrics["total_requests"] += 1
        metrics["total_time"] += processing_time
        metrics["avg_time"] = metrics["total_time"] / metrics["total_requests"]
        metrics["min_time"] = min(metrics["min_time"], processing_time)
        metrics["max_time"] = max(metrics["max_time"], processing_time)
        metrics["last_request"] = datetime.utcnow().isoformat()
        
        # Track status codes
        status_key = str(status_code)
        metrics["status_codes"][status_key] = metrics["status_codes"].get(status_key, 0) + 1
        
        # Store in Redis for persistence (optional)
        try:
            redis_client = await get_redis_client()
            if redis_client:
                daily_key = f"metrics:requests:{datetime.now().strftime('%Y-%m-%d')}:{metric_key}"
                await redis_client.lpush(daily_key, f"{processing_time:.3f}:{status_code}")
                await redis_client.expire(daily_key, 86400 * 7)  # Keep for 7 days
        except Exception:
            pass  # Don't fail the request if metrics storage fails
    
    async def record_analysis_metric(
        self,
        symbol: str,
        analysis_type: str,
        processing_time: float,
        success: bool,
        cache_hit: bool = False,
        user_id: Optional[str] = None
    ):
        """Record analysis performance metrics"""
        
        metric_key = f"analysis:{analysis_type}"
        
        # Update in-memory metrics
        if metric_key not in self.analysis_metrics:
            self.analysis_metrics[metric_key] = {
                "total_analyses": 0,
                "successful_analyses": 0,
                "failed_analyses": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "cache_hits": 0,
                "cache_misses": 0,
                "symbols_analyzed": set(),
                "last_analysis": None
            }
        
        metrics = self.analysis_metrics[metric_key]
        metrics["total_analyses"] += 1
        
        if success:
            metrics["successful_analyses"] += 1
            metrics["total_time"] += processing_time
            metrics["avg_time"] = metrics["total_time"] / metrics["successful_analyses"]
        else:
            metrics["failed_analyses"] += 1
        
        if cache_hit:
            metrics["cache_hits"] += 1
        else:
            metrics["cache_misses"] += 1
        
        metrics["symbols_analyzed"].add(symbol)
        metrics["last_analysis"] = datetime.utcnow().isoformat()
        
        # Convert set to list for JSON serialization
        metrics_copy = metrics.copy()
        metrics_copy["symbols_analyzed"] = list(metrics["symbols_analyzed"])
        
        logger.info(
            "📊 Analysis metric recorded",
            extra={
                "symbol": symbol,
                "analysis_type": analysis_type,
                "processing_time": f"{processing_time:.3f}s",
                "success": success,
                "cache_hit": cache_hit,
                "user_id": user_id
            }
        )
    
    def get_request_metrics(self) -> Dict[str, Any]:
        """Get aggregated request metrics"""
        return dict(self.request_metrics)
    
    def get_analysis_metrics(self) -> Dict[str, Any]:
        """Get aggregated analysis metrics"""
        # Convert sets to lists for JSON serialization
        serializable_metrics = {}
        for key, metrics in self.analysis_metrics.items():
            metrics_copy = metrics.copy()
            metrics_copy["symbols_analyzed"] = list(metrics.get("symbols_analyzed", set()))
            metrics_copy["unique_symbols_count"] = len(metrics.get("symbols_analyzed", set()))
            serializable_metrics[key] = metrics_copy
        
        return serializable_metrics
    
    async def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get all metrics in one call"""
        
        system_metrics = self.get_system_metrics()
        redis_metrics = await self.get_redis_metrics()
        request_metrics = self.get_request_metrics()
        analysis_metrics = self.get_analysis_metrics()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "redis": redis_metrics,
            "requests": request_metrics,
            "analysis": analysis_metrics,
            "application": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "uptime_seconds": self.get_uptime()
            }
        }


# Global monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_type: str = "request"):
    """Decorator to monitor function performance"""
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                processing_time = time.time() - start_time
                
                logger.info(
                    f"📊 {operation_type.title()} performance",
                    extra={
                        "operation": func.__name__,
                        "processing_time": f"{processing_time:.3f}s",
                        "success": success,
                        "error": error
                    }
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                processing_time = time.time() - start_time
                
                logger.info(
                    f"📊 {operation_type.title()} performance",
                    extra={
                        "operation": func.__name__,
                        "processing_time": f"{processing_time:.3f}s",
                        "success": success,
                        "error": error
                    }
                )
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
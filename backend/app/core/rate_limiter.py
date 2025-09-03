"""
Rate limiting implementation using Redis
Provides configurable rate limits per endpoint and user
"""

from functools import wraps
from fastapi import HTTPException, Request, status
from typing import Dict, Optional
import time
import hashlib

from .config import settings
from .redis_client import get_redis_client, increment_cache, set_cache
from .logging_config import get_context_logger

logger = get_context_logger(__name__)


class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self):
        self.limits = {
            "analysis": settings.RATE_LIMIT_ANALYSIS,
            "auth": settings.RATE_LIMIT_AUTH, 
            "general": settings.RATE_LIMIT_GENERAL
        }
        self._parse_limits()
    
    def _parse_limits(self):
        """Parse rate limit strings to (count, window) tuples"""
        parsed_limits = {}
        
        for category, limit_str in self.limits.items():
            try:
                # Parse format like "20/minute" or "100/hour"
                count, period = limit_str.split('/')
                count = int(count)
                
                if period == "second":
                    window = 1
                elif period == "minute":
                    window = 60
                elif period == "hour":
                    window = 3600
                elif period == "day":
                    window = 86400
                else:
                    raise ValueError(f"Unknown period: {period}")
                
                parsed_limits[category] = (count, window)
                
            except Exception as e:
                logger.error(
                    f"❌ Failed to parse rate limit: {limit_str}",
                    extra={"error": str(e)}
                )
                # Default fallback
                parsed_limits[category] = (100, 60)
        
        self.parsed_limits = parsed_limits
        
        logger.info(
            "⚡ Rate limits configured",
            extra={"limits": parsed_limits}
        )
    
    async def is_allowed(
        self, 
        identifier: str, 
        category: str = "general"
    ) -> tuple[bool, Dict[str, int]]:
        """Check if request is allowed under rate limit"""
        
        if category not in self.parsed_limits:
            category = "general"
        
        max_requests, window = self.parsed_limits[category]
        
        # Create Redis key
        current_window = int(time.time()) // window
        key = f"rate_limit:{category}:{identifier}:{current_window}"
        
        redis_client = await get_redis_client()
        
        if not redis_client:
            # If Redis is not available, allow the request
            logger.warning("Redis not available - rate limiting disabled")
            return True, {
                "requests_made": 0,
                "requests_remaining": max_requests,
                "reset_time": (current_window + 1) * window
            }
        
        try:
            # Increment counter and get current count
            current_count = await increment_cache(key, 1)
            
            if current_count is None:
                # If increment failed, allow the request
                return True, {
                    "requests_made": 0,
                    "requests_remaining": max_requests,
                    "reset_time": (current_window + 1) * window
                }
            
            # Set expiration on first request in window
            if current_count == 1:
                await redis_client.expire(key, window + 1)  # Extra second for safety
            
            # Check if limit exceeded
            allowed = current_count <= max_requests
            
            rate_info = {
                "requests_made": current_count,
                "requests_remaining": max(0, max_requests - current_count),
                "reset_time": (current_window + 1) * window
            }
            
            if not allowed:
                logger.warning(
                    "🚫 Rate limit exceeded",
                    extra={
                        "identifier": identifier,
                        "category": category,
                        "current_count": current_count,
                        "limit": max_requests
                    }
                )
            
            return allowed, rate_info
            
        except Exception as e:
            logger.error(
                "❌ Rate limit check failed",
                extra={
                    "identifier": identifier,
                    "category": category,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # On error, allow the request
            return True, {
                "requests_made": 0,
                "requests_remaining": max_requests,
                "reset_time": (current_window + 1) * window
            }
    
    def get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        
        # Try to get user ID from request state (set by auth middleware)
        if hasattr(request.state, 'user_id') and request.state.user_id:
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        
        # Hash IP to avoid storing raw IPs in Redis
        return f"ip:{hashlib.sha256(client_ip.encode()).hexdigest()[:16]}"


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(category: str = "general"):
    """Rate limiting decorator for FastAPI endpoints"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look in kwargs
                request = kwargs.get('request')
            
            if not request:
                logger.warning("Request object not found - skipping rate limit")
                return await func(*args, **kwargs)
            
            # Get client identifier
            identifier = rate_limiter.get_client_identifier(request)
            
            # Check rate limit
            allowed, rate_info = await rate_limiter.is_allowed(identifier, category)
            
            if not allowed:
                # Add rate limit headers to response
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "X-RateLimit-Limit": str(rate_limiter.parsed_limits[category][0]),
                        "X-RateLimit-Remaining": str(rate_info["requests_remaining"]),
                        "X-RateLimit-Reset": str(rate_info["reset_time"]),
                        "Retry-After": str(rate_info["reset_time"] - int(time.time()))
                    }
                )
            
            # Add rate limit info to request state
            request.state.rate_limit_info = rate_info
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def setup_rate_limiting(app):
    """Setup rate limiting middleware for the FastAPI app"""
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """Add rate limit headers to all responses"""
        
        response = await call_next(request)
        
        # Add rate limit info to response headers if available
        if hasattr(request.state, 'rate_limit_info'):
            rate_info = request.state.rate_limit_info
            response.headers["X-RateLimit-Remaining"] = str(rate_info["requests_remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset_time"])
        
        return response
    
    logger.info("⚡ Rate limiting middleware setup complete")
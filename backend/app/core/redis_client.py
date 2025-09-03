"""
Redis client configuration and connection management
Supports caching with TTL and health checks
"""

import redis.asyncio as redis
import json
import pickle
from typing import Any, Optional, Union, Tuple
import logging
from datetime import timedelta

from .config import settings, get_redis_url
from .logging_config import get_context_logger

logger = get_context_logger(__name__)

# Global Redis connection pool
redis_pool = None
redis_client = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_pool, redis_client
    
    redis_url = get_redis_url()
    
    if not redis_url:
        logger.warning("⚠️  Redis URL not configured - caching will be disabled")
        return
    
    logger.info(
        "🔴 Initializing Redis connection",
        extra={
            "redis_url": redis_url.split('@')[1] if '@' in redis_url else redis_url,
            "max_connections": settings.REDIS_MAX_CONNECTIONS
        }
    )
    
    try:
        # Create connection pool
        redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=False,  # We'll handle encoding/decoding manually
            socket_keepalive=True,
            socket_keepalive_options={},
        )
        
        # Create Redis client
        redis_client = redis.Redis(connection_pool=redis_pool)
        
        # Test connection
        await redis_client.ping()
        
        logger.info("✅ Redis connection established successfully")
        
    except Exception as e:
        logger.error(
            "❌ Failed to initialize Redis",
            extra={"error": str(e)},
            exc_info=True
        )
        
        # Don't raise exception - allow app to run without Redis
        redis_client = None
        redis_pool = None


async def close_redis():
    """Close Redis connection"""
    global redis_client, redis_pool
    
    if redis_client:
        logger.info("🔄 Closing Redis connection")
        await redis_client.close()
        
    if redis_pool:
        await redis_pool.disconnect()
    
    redis_client = None
    redis_pool = None
    
    logger.info("✅ Redis connection closed")


async def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance"""
    return redis_client


async def get_redis_health() -> Tuple[bool, str]:
    """Check Redis health"""
    try:
        if not redis_client:
            return False, "Redis not configured"
        
        await redis_client.ping()
        return True, "healthy"
        
    except Exception as e:
        logger.warning(
            "⚠️  Redis health check failed",
            extra={"error": str(e)}
        )
        return False, f"error: {str(e)}"


def _serialize_value(value: Any) -> bytes:
    """Serialize value for Redis storage"""
    try:
        # Try JSON first for simple types
        if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
            return json.dumps(value, default=str).encode('utf-8')
        else:
            # Fall back to pickle for complex objects
            return pickle.dumps(value)
    except Exception as e:
        logger.warning(
            "⚠️  Failed to serialize value with JSON, using pickle",
            extra={"error": str(e), "type": type(value).__name__}
        )
        return pickle.dumps(value)


def _deserialize_value(data: bytes) -> Any:
    """Deserialize value from Redis storage"""
    try:
        # Try JSON first
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        try:
            # Fall back to pickle
            return pickle.loads(data)
        except Exception as e:
            logger.error(
                "❌ Failed to deserialize value",
                extra={"error": str(e)},
                exc_info=True
            )
            return None


async def set_cache(
    key: str, 
    value: Any, 
    ttl: Optional[Union[int, timedelta]] = None
) -> bool:
    """Set a value in cache with optional TTL"""
    
    if not redis_client:
        logger.debug("Redis not available - skipping cache set")
        return False
    
    try:
        serialized_value = _serialize_value(value)
        
        if ttl is not None:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            success = await redis_client.setex(key, ttl, serialized_value)
        else:
            success = await redis_client.set(key, serialized_value)
        
        if success:
            logger.debug(
                "✅ Cache set successfully",
                extra={
                    "key": key,
                    "ttl": ttl,
                    "size_bytes": len(serialized_value)
                }
            )
        
        return bool(success)
        
    except Exception as e:
        logger.error(
            "❌ Failed to set cache",
            extra={
                "key": key,
                "error": str(e)
            },
            exc_info=True
        )
        return False


async def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache"""
    
    if not redis_client:
        logger.debug("Redis not available - cache miss")
        return None
    
    try:
        data = await redis_client.get(key)
        
        if data is None:
            logger.debug(
                "🔍 Cache miss",
                extra={"key": key}
            )
            return None
        
        value = _deserialize_value(data)
        
        logger.debug(
            "✅ Cache hit",
            extra={
                "key": key,
                "size_bytes": len(data)
            }
        )
        
        return value
        
    except Exception as e:
        logger.error(
            "❌ Failed to get cache",
            extra={
                "key": key,
                "error": str(e)
            },
            exc_info=True
        )
        return None


async def delete_cache(key: str) -> bool:
    """Delete a key from cache"""
    
    if not redis_client:
        return False
    
    try:
        deleted_count = await redis_client.delete(key)
        
        logger.debug(
            "🗑️  Cache deleted",
            extra={
                "key": key,
                "existed": deleted_count > 0
            }
        )
        
        return deleted_count > 0
        
    except Exception as e:
        logger.error(
            "❌ Failed to delete cache",
            extra={
                "key": key,
                "error": str(e)
            },
            exc_info=True
        )
        return False


async def clear_cache_pattern(pattern: str) -> int:
    """Clear all keys matching a pattern"""
    
    if not redis_client:
        return 0
    
    try:
        keys = await redis_client.keys(pattern)
        
        if keys:
            deleted_count = await redis_client.delete(*keys)
            
            logger.info(
                "🗑️  Cache cleared by pattern",
                extra={
                    "pattern": pattern,
                    "deleted_count": deleted_count
                }
            )
            
            return deleted_count
        
        return 0
        
    except Exception as e:
        logger.error(
            "❌ Failed to clear cache pattern",
            extra={
                "pattern": pattern,
                "error": str(e)
            },
            exc_info=True
        )
        return 0


async def exists_cache(key: str) -> bool:
    """Check if a key exists in cache"""
    
    if not redis_client:
        return False
    
    try:
        exists = await redis_client.exists(key)
        return bool(exists)
        
    except Exception as e:
        logger.error(
            "❌ Failed to check cache existence",
            extra={
                "key": key,
                "error": str(e)
            }
        )
        return False


async def get_cache_ttl(key: str) -> Optional[int]:
    """Get TTL for a cache key"""
    
    if not redis_client:
        return None
    
    try:
        ttl = await redis_client.ttl(key)
        return ttl if ttl > 0 else None
        
    except Exception as e:
        logger.error(
            "❌ Failed to get cache TTL",
            extra={
                "key": key,
                "error": str(e)
            }
        )
        return None


async def increment_cache(key: str, amount: int = 1) -> Optional[int]:
    """Increment a numeric value in cache"""
    
    if not redis_client:
        return None
    
    try:
        new_value = await redis_client.incr(key, amount)
        
        logger.debug(
            "➕ Cache incremented",
            extra={
                "key": key,
                "amount": amount,
                "new_value": new_value
            }
        )
        
        return new_value
        
    except Exception as e:
        logger.error(
            "❌ Failed to increment cache",
            extra={
                "key": key,
                "error": str(e)
            },
            exc_info=True
        )
        return None


async def set_cache_hash(hash_key: str, field: str, value: Any) -> bool:
    """Set a field in a Redis hash"""
    
    if not redis_client:
        return False
    
    try:
        serialized_value = _serialize_value(value)
        success = await redis_client.hset(hash_key, field, serialized_value)
        
        logger.debug(
            "✅ Hash field set",
            extra={
                "hash_key": hash_key,
                "field": field
            }
        )
        
        return bool(success)
        
    except Exception as e:
        logger.error(
            "❌ Failed to set hash field",
            extra={
                "hash_key": hash_key,
                "field": field,
                "error": str(e)
            },
            exc_info=True
        )
        return False


async def get_cache_hash(hash_key: str, field: str) -> Optional[Any]:
    """Get a field from a Redis hash"""
    
    if not redis_client:
        return None
    
    try:
        data = await redis_client.hget(hash_key, field)
        
        if data is None:
            return None
        
        return _deserialize_value(data)
        
    except Exception as e:
        logger.error(
            "❌ Failed to get hash field",
            extra={
                "hash_key": hash_key,
                "field": field,
                "error": str(e)
            },
            exc_info=True
        )
        return None
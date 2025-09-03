"""
Analysis routes for comprehensive market analysis
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status, BackgroundTasks
from typing import Optional, Dict, Any
import time
import asyncio
from datetime import datetime

from ..routes.auth import get_current_user
from ..services.analysis_service import analysis_service
from ..auth.kite_client import AsyncKiteClient
from ..core.config import settings
from ..core.logging_config import get_context_logger
from ..core.rate_limiter import rate_limit
from ..core.redis_client import get_redis_client, set_cache, get_cache
from ..models.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ComprehensiveAnalysisResponse,
    QuickAnalysisResponse,
    AnalysisType,
    AnalysisHistoryResponse
)

router = APIRouter()
logger = get_context_logger(__name__)


async def get_kite_client(current_user: dict = Depends(get_current_user)) -> AsyncKiteClient:
    """Get authenticated Kite client for current user"""
    
    kite_client = AsyncKiteClient()
    
    # Get Kite access token from user data
    kite_access_token = current_user.get("kite_access_token")
    user_id = current_user.get("user_id")
    
    if not kite_access_token:
        logger.error(
            "❌ No Kite access token found for user",
            extra={"user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kite access token not found. Please re-authenticate."
        )
    
    # Set access token
    kite_client.set_access_token(kite_access_token, user_id)
    
    return kite_client


def generate_cache_key(symbol: str, request: AnalysisRequest, user_id: str) -> str:
    """Generate cache key for analysis results"""
    return f"analysis:{symbol}:{request.analysis_type.value}:{request.timeframe.value}:{request.analysis_window}:{user_id}"


@router.post("/{symbol}", response_model=AnalysisResponse)
@rate_limit("analysis")
async def analyze_symbol(
    symbol: str,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    kite_client: AsyncKiteClient = Depends(get_kite_client)
):
    """Perform comprehensive analysis on a stock symbol"""
    
    user_id = current_user.get("user_id")
    start_time = time.time()
    
    # Override symbol from path parameter
    request.symbol = symbol.upper()
    
    logger.info(
        f"🎯 Starting analysis",
        extra={
            "symbol": request.symbol,
            "analysis_type": request.analysis_type.value,
            "user_id": user_id,
            "timeframe": request.timeframe.value,
            "analysis_window": request.analysis_window
        }
    )
    
    try:
        # Check cache first
        cache_key = generate_cache_key(request.symbol, request, user_id)
        cached_result = await get_cache(cache_key)
        
        if cached_result:
            processing_time = time.time() - start_time
            
            logger.info(
                f"✅ Analysis served from cache",
                extra={
                    "symbol": request.symbol,
                    "user_id": user_id,
                    "processing_time": f"{processing_time:.3f}s",
                    "cache_hit": True
                }
            )
            
            # Parse cached result and add metadata
            cached_data = cached_result
            cached_data["cached"] = True
            cached_data["processing_time"] = processing_time
            
            return AnalysisResponse.parse_obj(cached_data)
        
        # Set Kite client in analysis service
        analysis_service.set_kite_client(kite_client)
        
        # Perform analysis based on type
        if request.analysis_type == AnalysisType.COMPREHENSIVE:
            analysis_result = await analysis_service.run_comprehensive_analysis(request, user_id)
            comprehensive_data = analysis_result
            quick_data = None
            
        elif request.analysis_type == AnalysisType.QUICK:
            analysis_result = await analysis_service.run_quick_analysis(request, user_id)
            comprehensive_data = None
            quick_data = analysis_result
            
        else:
            # For other analysis types, run comprehensive and extract specific components
            full_analysis = await analysis_service.run_comprehensive_analysis(request, user_id)
            comprehensive_data = full_analysis
            quick_data = None
        
        processing_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            "analysis_type": request.analysis_type,
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "analysis_window": request.analysis_window,
            "cached": False,
            "cache_expires_at": None,
            "processing_time": processing_time,
            "comprehensive_data": comprehensive_data.dict() if comprehensive_data else None,
            "quick_data": quick_data.dict() if quick_data else None
        }
        
        # Cache the result in background
        background_tasks.add_task(
            set_cache,
            cache_key,
            response_data,
            request.cache_duration
        )
        
        logger.info(
            f"✅ Analysis completed",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "processing_time": f"{processing_time:.3f}s",
                "analysis_type": request.analysis_type.value,
                "cache_hit": False
            }
        )
        
        return AnalysisResponse.parse_obj(response_data)
        
    except ValueError as ve:
        logger.warning(
            f"⚠️  Analysis validation error",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "error": str(ve)
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            f"❌ Analysis failed",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "error": str(e),
                "processing_time": f"{processing_time:.3f}s"
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed. Please try again."
        )


@router.get("/{symbol}/quick", response_model=QuickAnalysisResponse)
@rate_limit("analysis")
async def quick_analyze_symbol(
    symbol: str,
    timeframe: str = "day",
    analysis_window: int = 30,
    current_user: dict = Depends(get_current_user),
    kite_client: AsyncKiteClient = Depends(get_kite_client)
):
    """Quick analysis for faster responses"""
    
    user_id = current_user.get("user_id")
    
    # Create analysis request
    request = AnalysisRequest(
        symbol=symbol.upper(),
        analysis_type=AnalysisType.QUICK,
        timeframe=timeframe,
        analysis_window=min(analysis_window, 50),  # Limit for quick analysis
        cache_duration=60  # Shorter cache for quick analysis
    )
    
    logger.info(
        f"⚡ Starting quick analysis",
        extra={
            "symbol": request.symbol,
            "user_id": user_id
        }
    )
    
    try:
        # Set Kite client in analysis service
        analysis_service.set_kite_client(kite_client)
        
        # Perform quick analysis
        result = await analysis_service.run_quick_analysis(request, user_id)
        
        logger.info(
            f"✅ Quick analysis completed",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "recommendation": result.recommendation
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"❌ Quick analysis failed",
            extra={
                "symbol": request.symbol,
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quick analysis failed. Please try again."
        )


@router.get("/history", response_model=AnalysisHistoryResponse)
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get user's analysis history"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        f"📊 Fetching analysis history",
        extra={
            "user_id": user_id,
            "limit": limit,
            "offset": offset
        }
    )
    
    try:
        # TODO: Implement database query for analysis history
        # For now, return empty response
        
        return AnalysisHistoryResponse(
            analyses=[],
            total=0,
            symbols_analyzed=[],
            most_analyzed_symbol=None
        )
        
    except Exception as e:
        logger.error(
            f"❌ Failed to fetch analysis history",
            extra={
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analysis history"
        )


@router.delete("/{symbol}/cache")
async def clear_analysis_cache(
    symbol: str,
    current_user: dict = Depends(get_current_user)
):
    """Clear cached analysis for a symbol"""
    
    user_id = current_user.get("user_id")
    symbol = symbol.upper()
    
    logger.info(
        f"🗑️  Clearing analysis cache",
        extra={
            "symbol": symbol,
            "user_id": user_id
        }
    )
    
    try:
        redis_client = await get_redis_client()
        if redis_client:
            # Find and delete all cache keys for this symbol and user
            pattern = f"analysis:{symbol}:*:{user_id}"
            keys = await redis_client.keys(pattern)
            
            if keys:
                await redis_client.delete(*keys)
                deleted_count = len(keys)
            else:
                deleted_count = 0
            
            logger.info(
                f"✅ Cache cleared",
                extra={
                    "symbol": symbol,
                    "user_id": user_id,
                    "deleted_keys": deleted_count
                }
            )
            
            return {
                "message": f"Cache cleared for {symbol}",
                "deleted_keys": deleted_count
            }
        else:
            return {
                "message": "Cache not available",
                "deleted_keys": 0
            }
            
    except Exception as e:
        logger.error(
            f"❌ Failed to clear cache",
            extra={
                "symbol": symbol,
                "user_id": user_id,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


@router.get("/cache/stats")
async def get_cache_stats(current_user: dict = Depends(get_current_user)):
    """Get cache statistics for current user"""
    
    user_id = current_user.get("user_id")
    
    try:
        redis_client = await get_redis_client()
        if not redis_client:
            return {"cache_available": False}
        
        # Get cache keys for user
        pattern = f"analysis:*:*:{user_id}"
        keys = await redis_client.keys(pattern)
        
        # Get cache info
        info = await redis_client.info("memory")
        
        return {
            "cache_available": True,
            "user_cached_analyses": len(keys),
            "total_memory_usage_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
            "cache_hit_ratio": "N/A"  # Would need to track this separately
        }
        
    except Exception as e:
        logger.error(
            f"❌ Failed to get cache stats",
            extra={
                "user_id": user_id,
                "error": str(e)
            }
        )
        
        return {"cache_available": False, "error": str(e)}
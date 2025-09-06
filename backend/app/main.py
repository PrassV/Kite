"""
FastAPI Trading Analysis Platform - Main Application
Production-ready backend for comprehensive market analysis with Kite Connect integration
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid
import asyncio
from datetime import datetime

from .core.config import settings
from .core.database import init_db, close_db
from .core.redis_client import init_redis, close_redis
from .routes import auth, analysis, stocks, health, monitoring, agent
from .core.rate_limiter import setup_rate_limiting
from .core.logging_config import setup_logging
from .utils.monitoring import performance_monitor

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Startup
    logger.info("🚀 Starting FastAPI Trading Analysis Platform")
    
    # Initialize database connection
    await init_db()
    logger.info("✅ Database connection established")
    
    # Initialize Redis connection
    await init_redis()
    logger.info("✅ Redis connection established")
    
    # Setup rate limiting
    setup_rate_limiting(app)
    logger.info("✅ Rate limiting configured")
    
    # Initialize mathematical analysis components
    try:
        # Test import of mathematical components to ensure they're available
        import sys
        sys.path.append('/app')  # Add to Python path for Railway deployment
        from detector import DeterministicPatternDetector
        from comprehensive_market_analyzer import generate_comprehensive_market_analysis
        logger.info("✅ Mathematical analysis components loaded successfully")
        logger.info("🔬 Advanced pattern detection: ✅ ENABLED")
        logger.info("📊 Comprehensive market analysis: ✅ ENABLED") 
        logger.info("🧮 13+ Mathematical indicators: ✅ ENABLED")
    except ImportError as e:
        logger.warning(f"⚠️  Mathematical components not fully available: {e}")
        logger.info("📊 Falling back to simplified analysis")
    
    logger.info("🎯 Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("🔄 Starting application shutdown")
    
    # Close database connection
    await close_db()
    logger.info("✅ Database connection closed")
    
    # Close Redis connection
    await close_redis()
    logger.info("✅ Redis connection closed")
    
    logger.info("✅ Application shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="Trading Analysis Platform API",
    description="Production-ready FastAPI backend for comprehensive stock market analysis with Kite Connect integration",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None
)

# Security middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing and unique request IDs"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request start
    logger.info(
        f"🔄 REQUEST START",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log successful response
        logger.info(
            f"✅ REQUEST COMPLETE",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s"
            }
        )
        
        # Record performance metrics
        try:
            endpoint = request.url.path
            method = request.method
            user_id = getattr(request.state, 'user_id', None)
            
            asyncio.create_task(performance_monitor.record_request_metric(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                processing_time=process_time,
                user_id=user_id
            ))
        except Exception:
            pass  # Don't fail the request if metrics recording fails
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        logger.error(
            f"❌ REQUEST ERROR",
            extra={
                "request_id": request_id,
                "error": str(e),
                "process_time": f"{process_time:.3f}s"
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={"X-Request-ID": request_id}
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.error(
        f"❌ UNHANDLED EXCEPTION",
        extra={
            "request_id": request_id,
            "error": str(exc),
            "url": str(request.url),
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers={"X-Request-ID": request_id}
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler for HTTP exceptions with proper logging"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    logger.warning(
        f"⚠️  HTTP EXCEPTION",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "url": str(request.url)
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat()
        },
        headers={"X-Request-ID": request_id}
    )


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
app.include_router(agent.router, prefix="/agent", tags=["LivePositionalAgent"])
app.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Trading Analysis Platform API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "Documentation disabled in production",
        "health": "/health",
        "features": {
            "mathematical_analysis": "✅ Advanced Pattern Detection with 13+ Indicators",
            "real_time_integration": "✅ Kite Connect API",
            "comprehensive_analysis": "✅ Fibonacci, Volume, Trendlines",
            "ai_narratives": "✅ Gemini AI Integration",
            "pattern_detection": "✅ Head&Shoulders, Triangles, Flags, etc.",
            "mathematical_indicators": "✅ Hurst Exponent, Fractal Dimension, Shannon Entropy"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
"""
Database configuration and connection management
Supports PostgreSQL with SQLAlchemy async
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, MetaData
import asyncio
from typing import Tuple, Optional
import logging

from .config import settings, get_database_url
from .logging_config import get_context_logger

logger = get_context_logger(__name__)

# SQLAlchemy setup
Base = declarative_base()
metadata = MetaData()

# Global variables for connection management
engine = None
AsyncSessionLocal = None


async def init_db():
    """Initialize database connection"""
    global engine, AsyncSessionLocal
    
    database_url = get_database_url()
    
    # Convert PostgreSQL URL to async version
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    
    logger.info(
        "🗄️  Initializing database connection",
        extra={
            "database_type": "postgresql" if "postgresql" in database_url else "sqlite",
            "pool_size": settings.DB_POOL_SIZE
        }
    )
    
    try:
        # Create async engine
        engine = create_async_engine(
            database_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            echo=settings.DEBUG,  # Log SQL queries in debug mode
            future=True
        )
        
        # Create session factory
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Test connection
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        logger.info("✅ Database connection established successfully")
        
        # Create tables if they don't exist
        await create_tables()
        
    except Exception as e:
        logger.error(
            "❌ Failed to initialize database",
            extra={"error": str(e)},
            exc_info=True
        )
        raise


async def close_db():
    """Close database connection"""
    global engine
    
    if engine:
        logger.info("🔄 Closing database connection")
        await engine.dispose()
        logger.info("✅ Database connection closed")


async def create_tables():
    """Create database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created/verified")
        
    except Exception as e:
        logger.error(
            "❌ Failed to create database tables",
            extra={"error": str(e)},
            exc_info=True
        )
        raise


async def get_db_session() -> AsyncSession:
    """Get database session"""
    if not AsyncSessionLocal:
        raise RuntimeError("Database not initialized")
    
    return AsyncSessionLocal()


async def get_db_health() -> Tuple[bool, str]:
    """Check database health"""
    try:
        if not engine:
            return False, "Database not initialized"
        
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        return True, "healthy"
        
    except Exception as e:
        logger.warning(
            "⚠️  Database health check failed",
            extra={"error": str(e)}
        )
        return False, f"error: {str(e)}"


# Database models for the trading platform
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON
from datetime import datetime


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)  # Kite user ID
    user_name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=True)
    broker = Column(String(50), default="zerodha")
    kite_access_token = Column(String(500), nullable=True)  # Encrypted in production
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON, default=dict)


class UserSession(Base):
    """User session model"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), nullable=False)
    access_token = Column(String(1000), nullable=False)
    refresh_token_hash = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)


class AnalysisHistory(Base):
    """Analysis history model"""
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=False)
    analysis_window = Column(Integer, nullable=False)
    analysis_result = Column(JSON, nullable=True)  # Store full analysis result
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    cache_hit = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)


class Watchlist(Base):
    """User watchlist model"""
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(200), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    alerts_enabled = Column(Boolean, default=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)


class SystemMetrics(Base):
    """System metrics for monitoring"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# Dependency for getting database session in routes
async def get_db() -> AsyncSession:
    """FastAPI dependency for getting database session"""
    async with get_db_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
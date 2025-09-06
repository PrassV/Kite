"""
Application configuration using Pydantic Settings
Supports environment variables and Railway deployment
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    APP_NAME: str = "Trading Analysis Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # Security Settings
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_SECRET_KEY: str = "jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://*.vercel.app",
        "https://trading-platform-ui.vercel.app"
    ]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Kite Connect Settings
    KITE_API_KEY: str = "tlumgytiz5v5yeyg"
    KITE_API_SECRET: str = "gpjurebcvi62t4yrx4shyymcbiag16gd"
    KITE_REDIRECT_URL: str = "https://trading-platform-api.railway.app/auth/callback"
    
    # Database Settings (PostgreSQL on Railway)
    DATABASE_URL: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: int = 5432
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis Settings (Railway Redis)
    REDIS_URL: Optional[str] = None
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20
    
    # Cache Settings
    CACHE_TTL_ANALYSIS: int = 300  # 5 minutes
    CACHE_TTL_QUOTES: int = 60     # 1 minute
    CACHE_TTL_SEARCH: int = 3600   # 1 hour
    
    # Rate Limiting
    RATE_LIMIT_ANALYSIS: str = "20/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_GENERAL: str = "100/minute"
    
    # Analysis Settings
    DEFAULT_ANALYSIS_WINDOW: int = 60
    MAX_ANALYSIS_WINDOW: int = 365
    MAX_CONCURRENT_ANALYSIS: int = 50
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None
    
    # External API Settings
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 0.5
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def validate_database_url(cls, v, info):
        """Auto-construct DATABASE_URL if components are provided"""
        if v:
            return v
        
        # Try to construct from individual components
        values = info.data if info else {}
        host = values.get('DB_HOST')
        port = values.get('DB_PORT', 5432)
        name = values.get('DB_NAME')
        user = values.get('DB_USER')
        password = values.get('DB_PASSWORD')
        
        if all([host, name, user, password]):
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        
        return None
    
    @field_validator('REDIS_URL', mode='before')
    @classmethod
    def validate_redis_url(cls, v, info):
        """Auto-construct REDIS_URL if components are provided"""
        if v:
            return v
        
        # Try to construct from individual components
        values = info.data if info else {}
        host = values.get('REDIS_HOST')
        port = values.get('REDIS_PORT', 6379)
        password = values.get('REDIS_PASSWORD')
        db = values.get('REDIS_DB', 0)
        
        if host:
            if password:
                return f"redis://:{password}@{host}:{port}/{db}"
            else:
                return f"redis://{host}:{port}/{db}"
        
        return None
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() in ('production', 'prod')
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() in ('development', 'dev', 'local')
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL with fallback for Railway"""
    if settings.DATABASE_URL:
        return settings.DATABASE_URL
    
    # Railway provides DATABASE_URL automatically
    railway_db_url = os.getenv('DATABASE_URL')
    if railway_db_url:
        return railway_db_url
    
    # Fallback to SQLite for development
    if settings.is_development:
        return "sqlite:///./trading_platform.db"
    
    raise ValueError("No database configuration found")


def get_redis_url() -> Optional[str]:
    """Get Redis URL with fallback for Railway"""
    if settings.REDIS_URL:
        return settings.REDIS_URL
    
    # Railway provides REDIS_URL automatically
    railway_redis_url = os.getenv('REDIS_URL')
    if railway_redis_url:
        return railway_redis_url
    
    return None
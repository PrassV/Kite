"""
Common Pydantic models used across the application
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class APIResponse(BaseModel):
    """Base API response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, str] = Field(default_factory=dict)
    uptime: Optional[float] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number (starts from 1)")
    limit: int = Field(10, ge=1, le=100, description="Items per page (max 100)")


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: list
    page: int
    limit: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
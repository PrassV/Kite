"""
Authentication-related Pydantic models
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class KiteLoginRequest(BaseModel):
    """Request model for initiating Kite Connect login"""
    redirect_url: Optional[HttpUrl] = Field(
        None,
        description="Custom redirect URL after authentication (optional)"
    )


class KiteLoginResponse(BaseModel):
    """Response model for Kite Connect login initiation"""
    login_url: HttpUrl = Field(description="Kite Connect authentication URL")
    state: Optional[str] = Field(None, description="State parameter for OAuth flow")


class KiteCallbackRequest(BaseModel):
    """Request model for Kite Connect OAuth callback"""
    request_token: str = Field(description="Request token from Kite Connect")
    action: Optional[str] = Field(None, description="Action parameter from callback")
    status: Optional[str] = Field(None, description="Status parameter from callback")


class TokenResponse(BaseModel):
    """JWT token response model"""
    access_token: str = Field(description="JWT access token")
    refresh_token: str = Field(description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    expires_at: datetime = Field(description="Token expiration timestamp")


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str = Field(description="Valid refresh token")


class UserProfile(BaseModel):
    """User profile model"""
    user_id: str = Field(description="Kite Connect user ID")
    user_name: str = Field(description="User's name")
    email: Optional[str] = Field(None, description="User's email address")
    broker: str = Field(default="zerodha", description="Broker name")
    created_at: datetime = Field(description="Account creation timestamp")
    last_login: datetime = Field(description="Last login timestamp")


class UserSession(BaseModel):
    """User session model"""
    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="Kite Connect user ID")
    access_token: str = Field(description="Kite Connect access token")
    expires_at: datetime = Field(description="Session expiration timestamp")
    created_at: datetime = Field(description="Session creation timestamp")
    last_activity: datetime = Field(description="Last activity timestamp")


class AuthStatusResponse(BaseModel):
    """Authentication status response"""
    authenticated: bool = Field(description="Authentication status")
    user_profile: Optional[UserProfile] = Field(None, description="User profile if authenticated")
    session_expires_at: Optional[datetime] = Field(None, description="Session expiration time")
    permissions: list[str] = Field(default_factory=list, description="User permissions")


class LogoutResponse(BaseModel):
    """Logout response model"""
    message: str = Field(default="Successfully logged out")
    logged_out_at: datetime = Field(default_factory=datetime.utcnow)
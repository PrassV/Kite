"""
Authentication routes with Kite Connect OAuth integration
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from ..auth.kite_client import AsyncKiteClient
from ..auth.jwt_handler import jwt_handler
from ..core.config import settings
from ..core.logging_config import get_context_logger
from ..core.rate_limiter import rate_limit
from ..models.auth import (
    KiteLoginRequest,
    KiteLoginResponse,
    KiteCallbackRequest,
    TokenResponse,
    RefreshTokenRequest,
    AuthStatusResponse,
    UserProfile,
    LogoutResponse
)

router = APIRouter()
logger = get_context_logger(__name__)
security = HTTPBearer(auto_error=False)


# Dependency to get current user from JWT
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Extract and verify JWT token from request"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = jwt_handler.verify_token(token, "access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Add user info to request state
    request.state.user_id = payload.get("user_id")
    request.state.user_data = payload
    
    return payload


@router.post("/login", response_model=KiteLoginResponse)
@rate_limit("auth")
async def initiate_kite_login(request: KiteLoginRequest):
    """Initiate Kite Connect OAuth login flow"""
    
    logger.info(
        "🔐 Initiating Kite login",
        extra={"redirect_url": str(request.redirect_url) if request.redirect_url else None}
    )
    
    try:
        kite_client = AsyncKiteClient()
        
        # Use custom redirect URL if provided
        redirect_url = str(request.redirect_url) if request.redirect_url else settings.KITE_REDIRECT_URL
        login_url = kite_client.get_login_url(redirect_url)
        
        logger.info(
            "✅ Kite login URL generated",
            extra={"login_url": login_url}
        )
        
        return KiteLoginResponse(login_url=login_url)
        
    except Exception as e:
        logger.error(
            "❌ Failed to generate Kite login URL",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate login"
        )


@router.post("/callback", response_model=TokenResponse)
@rate_limit("auth")
async def handle_kite_callback(callback_data: KiteCallbackRequest):
    """Handle Kite Connect OAuth callback and generate JWT tokens"""
    
    logger.info(
        "🔄 Processing Kite callback",
        extra={
            "request_token": callback_data.request_token[:10] + "...",
            "status": callback_data.status,
            "action": callback_data.action
        }
    )
    
    try:
        # Initialize Kite client and generate session
        kite_client = AsyncKiteClient()
        session_data = await kite_client.generate_session(callback_data.request_token)
        
        # Get user profile
        profile = await kite_client.get_profile()
        
        # Prepare user data for JWT
        user_data = {
            "user_id": session_data["user_id"],
            "user_name": profile.get("user_name", ""),
            "email": profile.get("email", ""),
            "broker": profile.get("broker", "zerodha"),
            "kite_access_token": session_data["access_token"]
        }
        
        # Create JWT token pair
        token_data = jwt_handler.create_token_pair(user_data)
        
        # TODO: Store session in database
        # For now, we'll just log the session creation
        logger.info(
            "✅ User session created",
            extra={
                "user_id": user_data["user_id"],
                "user_name": user_data["user_name"]
            }
        )
        
        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type="bearer",
            expires_in=token_data["expires_in"],
            expires_at=token_data["expires_at"]
        )
        
    except Exception as e:
        logger.error(
            "❌ Kite callback processing failed",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
@rate_limit("auth")
async def refresh_access_token(refresh_request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    
    logger.info("🔄 Processing token refresh")
    
    try:
        # TODO: Implement proper refresh token validation with database
        # For now, we'll implement a simplified version
        
        refresh_payload = jwt_handler.verify_token(refresh_request.refresh_token, "refresh")
        if not refresh_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        user_id = refresh_payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
        
        # TODO: Get user data from database
        # For now, create minimal user data
        user_data = {
            "user_id": user_id,
            "user_name": "User",  # Would come from database
            "email": "",
            "broker": "zerodha"
        }
        
        # Create new access token
        access_token_data = jwt_handler.create_access_token(user_data)
        
        logger.info(
            "✅ Access token refreshed",
            extra={"user_id": user_id}
        )
        
        return TokenResponse(
            access_token=access_token_data["access_token"],
            refresh_token=refresh_request.refresh_token,  # Keep same refresh token
            token_type="bearer",
            expires_in=access_token_data["expires_in"],
            expires_at=access_token_data["expires_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "❌ Token refresh failed",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=AuthStatusResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        "👤 Fetching user info",
        extra={"user_id": user_id}
    )
    
    try:
        # TODO: Fetch complete user profile from database
        # For now, return data from JWT payload
        
        user_profile = UserProfile(
            user_id=current_user.get("user_id", ""),
            user_name=current_user.get("user_name", "User"),
            email=current_user.get("email"),
            broker=current_user.get("broker", "zerodha"),
            created_at=current_user.get("iat", 0),  # Would come from database
            last_login=current_user.get("iat", 0)   # Would come from database
        )
        
        return AuthStatusResponse(
            authenticated=True,
            user_profile=user_profile,
            session_expires_at=current_user.get("exp"),
            permissions=["analysis", "portfolio"]  # Would come from database
        )
        
    except Exception as e:
        logger.error(
            "❌ Failed to fetch user info",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(current_user: dict = Depends(get_current_user)):
    """Logout current user and invalidate tokens"""
    
    user_id = current_user.get("user_id")
    
    logger.info(
        "👋 User logout",
        extra={"user_id": user_id}
    )
    
    try:
        # TODO: Invalidate tokens in database/Redis
        # For now, just log the logout
        
        logger.info(
            "✅ User logged out successfully",
            extra={"user_id": user_id}
        )
        
        return LogoutResponse()
        
    except Exception as e:
        logger.error(
            "❌ Logout failed",
            extra={"user_id": user_id, "error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# Optional endpoint for checking authentication status without requiring auth
@router.get("/status")
async def check_auth_status(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Check authentication status without requiring valid token"""
    
    if not credentials:
        return {"authenticated": False}
    
    token = credentials.credentials
    payload = jwt_handler.verify_token(token, "access")
    
    if payload:
        return {
            "authenticated": True,
            "user_id": payload.get("user_id"),
            "expires_at": payload.get("exp")
        }
    else:
        return {"authenticated": False}